"""
Notifications. Two kinds of recipient:

* staff users  -> an in-app notification (bell + inbox);
* guardians    -> they have no logins, so the notification row is the *record of an email*:
                  sent (emailed_at), failed (email_error), or no address on file.

Rules this module keeps:
 - Nothing here may break the action that triggered it. Every public notify_* function
   builds its rows, commits them, and only then sends email; any exception is logged and
   swallowed (the caller gets None).
 - Email is sent AFTER the database commit (a failed save never emails anyone) and, unless
   NOTIFICATIONS_EMAIL_SYNC is on, in a background thread.
 - Outcomes are recorded honestly per recipient, so the Admin's delivery log shows exactly
   who was and wasn't reached.
"""
import threading
from datetime import datetime, timedelta, timezone

from flask import current_app, url_for
from flask_mail import Message

from app.extensions import db, mail
from app.models import Notification, User, Student, StudentGuardian, Guardian
from app.models.enums import NotificationType, NoticeAudience, UserRole, StudentStatus, ApplicantRole, LeaveStatus

STAFF_ROLES = (UserRole.ADMIN, UserRole.TEACHER, UserRole.ACCOUNTANT, UserRole.RECEPTIONIST)
NO_EMAIL_ERROR = "No email address on file"
NOT_CONFIGURED_ERROR = "Email is not configured on this server"
SWITCHED_OFF_ERROR = "Guardian emails are switched off (GUARDIAN_EMAILS_ENABLED)"
REMINDER_COOLDOWN = timedelta(hours=24)


# ------------------------------------------------------------------ recipients
def staff_recipients(school_id, roles=STAFF_ROLES, exclude_user_id=None):
    users = User.query.filter(
        User.school_id == school_id, User.role.in_(roles),
        User.is_active_account.is_(True), User.is_verified.is_(True),
    ).all()
    return [u.id for u in users if u.id != exclude_user_id]


def active_students(school_id, class_id=None, section_id=None):
    query = Student.query.filter_by(school_id=school_id, status=StudentStatus.ACTIVE)
    if class_id:
        query = query.filter_by(current_class_id=class_id)
    if section_id:
        query = query.filter_by(current_section_id=section_id)
    return query.all()


def guardians_for_students(students):
    """{guardian_id: [student names]} — a family linked to several students appears once."""
    by_id = {s.id: s for s in students}
    if not by_id:
        return {}
    result = {}
    for link in StudentGuardian.query.filter(StudentGuardian.student_id.in_(list(by_id))).order_by(StudentGuardian.id):
        names = result.setdefault(link.guardian_id, [])
        if by_id[link.student_id].name not in names:
            names.append(by_id[link.student_id].name)
    return result


def guardian_display_name(guardian):
    return guardian.father_name or guardian.mother_name or "Parent/Guardian"


# ------------------------------------------------------------------ creating rows
def create_user_notifications(school_id, user_ids, ntype, title, message, link_url=None):
    for user_id in dict.fromkeys(user_ids):
        db.session.add(Notification(school_id=school_id, recipient_user_id=user_id, notification_type=ntype,
                                    title=title[:200], message=message, link_url=link_url))
    return len(set(user_ids))


def create_guardian_notifications(school_id, per_guardian, ntype):
    """per_guardian: {guardian_id: (title, message)}. Returns (summary_counts, ids_to_email)."""
    if not per_guardian:
        return {"guardians": 0, "emailable": 0, "no_email": 0}, []
    guardians = {g.id: g for g in Guardian.query.filter(Guardian.id.in_(list(per_guardian)),
                                                        Guardian.school_id == school_id)}
    enabled = current_app.config.get("GUARDIAN_EMAILS_ENABLED", True)
    rows, no_email = [], 0
    for guardian_id, (title, message) in per_guardian.items():
        guardian = guardians.get(guardian_id)
        if guardian is None:
            continue
        row = Notification(school_id=school_id, recipient_guardian_id=guardian_id, notification_type=ntype,
                           title=title[:200], message=message)
        if not (guardian.email or "").strip():
            row.email_error, no_email = NO_EMAIL_ERROR, no_email + 1
        elif not enabled:
            row.email_error = SWITCHED_OFF_ERROR
        db.session.add(row)
        rows.append(row)
    db.session.flush()
    to_email = [r.id for r in rows if r.email_error is None]
    return {"guardians": len(rows), "emailable": len(to_email), "no_email": no_email}, to_email


# ------------------------------------------------------------------ sending
def _subject(school_name, title):
    clean = " ".join(title.split())              # no newlines: prevents header injection
    return f"[{school_name}] {clean}"[:150]


def deliver_emails(app, notification_ids):
    """Send (or retry) emails for guardian notifications; record the outcome of each."""
    with app.app_context():
        configured = bool(app.config.get("MAIL_USERNAME") and app.config.get("MAIL_PASSWORD"))
        for notification_id in notification_ids:
            n = db.session.get(Notification, notification_id)
            if n is None or n.emailed_at is not None or n.recipient_guardian_id is None:
                continue
            guardian = n.recipient_guardian
            address = (guardian.email or "").strip() if guardian else ""
            if not address:
                n.email_error = NO_EMAIL_ERROR
            elif not configured:
                n.email_error = NOT_CONFIGURED_ERROR
            else:
                try:
                    body = (f"Dear {guardian_display_name(guardian)},\n\n{n.message}\n\n— {n.school.name}")
                    mail.send(Message(subject=_subject(n.school.name, n.title), recipients=[address], body=body,
                                      sender=app.config["MAIL_DEFAULT_SENDER"]))
                    n.emailed_at, n.email_error = datetime.now(timezone.utc), None
                except Exception as exc:         # SMTP/auth/network problems are recorded, never raised
                    n.email_error = f"{type(exc).__name__}: {exc}"[:255]
                    app.logger.error("Notification email to %s failed: %s", address, exc)
            db.session.commit()


def dispatch_emails(notification_ids):
    if not notification_ids:
        return
    app = current_app._get_current_object()
    if app.config.get("NOTIFICATIONS_EMAIL_SYNC"):
        deliver_emails(app, notification_ids)
    else:
        threading.Thread(target=deliver_emails, args=(app, notification_ids), daemon=True).start()


def _finish(build):
    """Run build() -> (summary, ids_to_email); commit; then email. Never raises."""
    try:
        summary, to_email = build()
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Creating notifications failed (the action itself was not affected)")
        return None
    try:
        dispatch_emails(to_email)
    except Exception:
        current_app.logger.exception("Starting email delivery failed")
    return summary


def describe(summary) -> str:
    if summary is None:
        return "(Notifications could not be created — see the server log.)"
    parts = []
    if summary.get("staff"):
        parts.append(f"{summary['staff']} staff")
    if summary.get("guardians"):
        text = f"{summary['guardians']} guardian(s) — {summary['emailable']} being emailed"
        if summary["no_email"]:
            text += f", {summary['no_email']} with no email address on file"
        parts.append(text)
    return ("Notified " + "; ".join(parts) + ".") if parts else "No one needed to be notified."


def note(summary) -> str:
    """describe(), but empty when nobody needed telling (so flash messages stay clean)."""
    text = describe(summary)
    return "" if text == "No one needed to be notified." else text


def _summary(staff, guardian_counts):
    return {"staff": staff, **guardian_counts}


# ------------------------------------------------------------------ triggers
def notify_notice_published(notice, publisher_id):
    def build():
        sid = notice.school_id
        roles = {NoticeAudience.ALL: STAFF_ROLES, NoticeAudience.STAFF: STAFF_ROLES,
                 NoticeAudience.TEACHERS: (UserRole.TEACHER,)}.get(notice.audience, ())
        staff = staff_recipients(sid, roles, exclude_user_id=publisher_id) if roles else []
        link = url_for("notices.view_notice", notice_id=notice.id)
        create_user_notifications(sid, staff, NotificationType.NOTICE, notice.title, notice.body, link)
        if notice.audience in (NoticeAudience.ALL, NoticeAudience.PARENTS):
            students = active_students(sid)
        elif notice.audience == NoticeAudience.CLASS:
            students = active_students(sid, notice.class_id, notice.section_id)
        else:
            students = []
        per = {gid: (notice.title, notice.body) for gid in guardians_for_students(students)}
        counts, ids = create_guardian_notifications(sid, per, NotificationType.NOTICE)
        return _summary(len(set(staff)), counts), ids
    return _finish(build)


def notify_event_created(event, creator_id):
    def build():
        sid = event.school_id
        when = event.start_date.strftime("%d %b %Y") + (f" – {event.end_date.strftime('%d %b %Y')}" if event.end_date != event.start_date else "")
        message = f"{event.title} — {when}" + (f", {event.location}" if event.location else "")
        if event.description:
            message += f"\n\n{event.description}"
        staff = staff_recipients(sid, STAFF_ROLES, exclude_user_id=creator_id)
        create_user_notifications(sid, staff, NotificationType.EVENT, f"New event: {event.title}", message,
                                  url_for("events.view_event", event_id=event.id))
        counts, ids = {"guardians": 0, "emailable": 0, "no_email": 0}, []
        if event.is_holiday:                         # families are emailed only about closures
            per = {gid: (f"School closed: {event.title}", f"The school will be closed: {message}")
                   for gid in guardians_for_students(active_students(sid))}
            counts, ids = create_guardian_notifications(sid, per, NotificationType.EVENT)
        return _summary(len(set(staff)), counts), ids
    return _finish(build)


def notify_homework_assigned(homework, creator_id):
    from app.services.homework_service import target_students
    def build():
        sid = homework.school_id
        students = target_students(homework)
        where = homework.school_class.name + (f" – {homework.section.name}" if homework.section else "")
        per = {}
        for gid, names in guardians_for_students(students).items():
            message = (f"{homework.subject.name} homework has been assigned to {where}.\n\n"
                       f"{homework.title}\nDue: {homework.due_date.strftime('%d %b %Y')}\nFor: {', '.join(names)}")
            if homework.description:
                message += f"\n\n{homework.description}"
            per[gid] = (f"Homework: {homework.subject.name} — {homework.title}", message)
        counts, ids = create_guardian_notifications(sid, per, NotificationType.HOMEWORK)
        return _summary(0, counts), ids
    return _finish(build)


def _ptm_text(appointment):
    from app.services.ptm_service import slot_label
    meeting = appointment.meeting
    text = (f"{appointment.student.name} with {appointment.teacher.name}\n"
            f"{meeting.title} — {meeting.meeting_date.strftime('%A, %d %b %Y')}, {slot_label(meeting, appointment.slot_start)}")
    return text + (f"\nLocation: {meeting.location}" if meeting.location else "")


def notify_ptm_booked(appointment, actor_id):
    def build():
        sid, staff, counts, ids = appointment.school_id, 0, {"guardians": 0, "emailable": 0, "no_email": 0}, []
        text = _ptm_text(appointment)
        if appointment.teacher_id != actor_id:
            create_user_notifications(sid, [appointment.teacher_id], NotificationType.PTM, "New meeting appointment", text,
                                      url_for("ptm.view_meeting", meeting_id=appointment.meeting_id))
            staff = 1
        if appointment.guardian_id:
            counts, ids = create_guardian_notifications(
                sid, {appointment.guardian_id: ("Parent–teacher meeting appointment", "An appointment has been booked:\n\n" + text)},
                NotificationType.PTM)
        return _summary(staff, counts), ids
    return _finish(build)


def notify_ptm_cancelled(appointment, actor_id):
    def build():
        sid, staff, counts, ids = appointment.school_id, 0, {"guardians": 0, "emailable": 0, "no_email": 0}, []
        text = _ptm_text(appointment)
        if appointment.teacher_id != actor_id:
            create_user_notifications(sid, [appointment.teacher_id], NotificationType.PTM, "Meeting appointment cancelled", text,
                                      url_for("ptm.view_meeting", meeting_id=appointment.meeting_id))
            staff = 1
        if appointment.guardian_id:
            counts, ids = create_guardian_notifications(
                sid, {appointment.guardian_id: ("Parent–teacher meeting appointment cancelled", "This appointment has been cancelled:\n\n" + text)},
                NotificationType.PTM)
        return _summary(staff, counts), ids
    return _finish(build)


def notify_ptm_meeting_cancelled(meeting, cancelled_appointments, actor_id):
    def build():
        sid = meeting.school_id
        teachers = [a.teacher_id for a in cancelled_appointments if a.teacher_id != actor_id]
        create_user_notifications(sid, teachers, NotificationType.PTM, f"Meeting cancelled: {meeting.title}",
                                  f"{meeting.title} on {meeting.meeting_date.strftime('%d %b %Y')} has been cancelled.",
                                  url_for("ptm.view_meeting", meeting_id=meeting.id))
        per = {}
        for a in cancelled_appointments:
            if a.guardian_id:
                per[a.guardian_id] = ("Parent–teacher meeting cancelled",
                                      "The meeting has been cancelled, so this appointment will not take place:\n\n" + _ptm_text(a))
        counts, ids = create_guardian_notifications(sid, per, NotificationType.PTM)
        return _summary(len(set(teachers)), counts), ids
    return _finish(build)


def notify_leave_decided(leave):
    def build():
        sid = leave.school_id
        verdict = "approved" if leave.status == LeaveStatus.APPROVED else "rejected"
        dates = leave.start_date.strftime("%d %b %Y") + (f" – {leave.end_date.strftime('%d %b %Y')}" if leave.end_date != leave.start_date else "")
        staff, counts, ids = 0, {"guardians": 0, "emailable": 0, "no_email": 0}, []
        if leave.applicant_role == ApplicantRole.TEACHER and leave.teacher_user_id and leave.teacher_user_id != leave.approved_by_id:
            message = f"Your leave request for {dates} was {verdict}." + (f"\nRemarks: {leave.decision_remarks}" if leave.decision_remarks else "")
            create_user_notifications(sid, [leave.teacher_user_id], NotificationType.LEAVE, f"Leave request {verdict}", message,
                                      url_for("leave.view_leave", leave_id=leave.id))
            staff = 1
        elif leave.applicant_role == ApplicantRole.STUDENT and leave.student is not None:
            message = (f"The leave request for {leave.student.name} ({dates}) was {verdict}."
                       + (f"\nRemarks: {leave.decision_remarks}" if leave.decision_remarks else ""))
            per = {gid: (f"Leave request {verdict}", message) for gid in guardians_for_students([leave.student])}
            counts, ids = create_guardian_notifications(sid, per, NotificationType.LEAVE)
        return _summary(staff, counts), ids
    return _finish(build)


def fee_reminder_preview(results):
    """How many guardians a reminder mailing for these defaulters would reach."""
    students = [r["student"] for r in results]
    guardians = guardians_for_students(students)
    emailable = Guardian.query.filter(Guardian.id.in_(list(guardians) or [0]), Guardian.email.isnot(None), Guardian.email != "").count()
    return {"students": len(students), "guardians": len(guardians), "emailable": emailable}


def notify_fee_reminders(school_id, results):
    """One email per guardian listing every child of theirs with an outstanding balance.
    Guardians already reminded in the last 24 hours are skipped (protects against double-clicks)."""
    def build():
        by_guardian = {}
        mapping = guardians_for_students([r["student"] for r in results])
        for r in results:
            for gid, names in mapping.items():
                if r["student"].name in names:
                    by_guardian.setdefault(gid, [])
        for gid in by_guardian:
            for r in results:
                if r["student"].name in mapping[gid]:
                    by_guardian[gid].append(r)
        cutoff = datetime.now(timezone.utc) - REMINDER_COOLDOWN
        recent = {gid for (gid,) in db.session.query(Notification.recipient_guardian_id).filter(
            Notification.school_id == school_id, Notification.notification_type == NotificationType.FEE_DUE,
            Notification.recipient_guardian_id.in_(list(by_guardian) or [0]), Notification.created_at >= cutoff)}
        per = {}
        for gid, items in by_guardian.items():
            if gid in recent:
                continue
            lines = [f"- {r['student'].name}: {r['total_remaining']} outstanding (oldest due date "
                     f"{r['earliest_due_date'].strftime('%d %b %Y')})" for r in items]
            per[gid] = ("Fee reminder", "This is a reminder that the following fees are outstanding:\n\n" + "\n".join(lines)
                        + "\n\nIf you have already paid, please ignore this message.")
        counts, ids = create_guardian_notifications(school_id, per, NotificationType.FEE_DUE)
        counts["skipped_recent"] = len([g for g in by_guardian if g in recent])
        return _summary(0, counts), ids
    return _finish(build)


# ------------------------------------------------------------------ delivery status (derived, never stored)
def delivery_status(notification):
    if notification.emailed_at is not None:
        return "sent"
    if notification.email_error == NO_EMAIL_ERROR:
        return "no_email"
    if notification.email_error:
        return "failed"
    return "pending"


def safe_internal_link(url):
    """Only same-site relative paths are followed after opening a notification."""
    if url and url.startswith("/") and not url.startswith("//") and "\\" not in url:
        return url
    return None
