from datetime import date, datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import (PTMMeeting, PTMAppointment, SchoolClass, Section, Student, StudentGuardian, User,
                        AcademicSession)
from app.models.enums import UserRole, MeetingStatus, AppointmentStatus
from app.forms.ptm import MeetingForm, BookingForm
from app.utils.decorators import role_required
from app.utils.tenant import current_school_id
from app.services import notification_service as ns
from app.services.audit_service import log_action
from app.services.ptm_service import (
    slots_for, slot_times, slot_label, scope_label, students_in_scope, guardians_by_student, guardian_label,
    find_conflicts, can_book_for, can_cancel, can_record_outcome, active_appointments, ACTIVE_STATUSES, STATUS_COLORS,
)

ptm_bp = Blueprint("ptm", __name__, url_prefix="/ptm")

VIEWERS = (UserRole.ADMIN, UserRole.TEACHER, UserRole.RECEPTIONIST)
PER_PAGE = 20


def _active_session(school_id):
    return AcademicSession.query.filter_by(school_id=school_id, is_active=True).first()


def _teachers(school_id):
    return User.query.filter_by(school_id=school_id, role=UserRole.TEACHER, is_active_account=True).order_by(User.name).all()


def _meeting_choices(form, school_id, meeting=None):
    active = _active_session(school_id)
    classes = (SchoolClass.query.filter_by(school_id=school_id, session_id=active.id).order_by(SchoolClass.name).all()
               if active else [])
    if meeting is not None and meeting.school_class is not None and meeting.school_class not in classes:
        classes.append(meeting.school_class)
    form.class_id.choices = [(0, "All classes")] + [(c.id, c.name) for c in classes]
    form.section_id.choices = [(0, "All sections")] + [(s.id, f"{c.name} – {s.name}") for c in classes for s in c.sections]
    return {c.id: [[s.id, s.name] for s in c.sections] for c in classes}


def _check_meeting(form, school_id, existing=None):
    """Cross-field rules. Returns (class_id, section_id, ok)."""
    good = True
    if form.end_time.data <= form.start_time.data:
        form.end_time.errors.append("The end time must be after the start time.")
        good = False
    elif not slot_times(form.meeting_date.data, form.start_time.data, form.end_time.data, form.slot_minutes.data):
        form.slot_minutes.errors.append("The meeting window is shorter than one appointment.")
        good = False
    unchanged_date = existing is not None and existing.meeting_date == form.meeting_date.data
    if form.meeting_date.data < date.today() and not unchanged_date:
        form.meeting_date.errors.append("The meeting date can't be in the past.")
        good = False
    class_id = form.class_id.data or None
    section_id = form.section_id.data or None
    if section_id and not class_id:
        form.section_id.errors.append("Choose a class to go with that section.")
        good = False
    elif class_id:
        if not SchoolClass.query.filter_by(id=class_id, school_id=school_id).first():
            form.class_id.errors.append("That class was not found.")
            good = False
        elif section_id and not Section.query.filter_by(id=section_id, class_id=class_id).first():
            form.section_id.errors.append("That section doesn't belong to the chosen class.")
            good = False
    return class_id, section_id, good


def _meeting_or_404(meeting_id):
    return PTMMeeting.query.filter_by(id=meeting_id, school_id=current_school_id()).first_or_404()


# ----------------------------------------------------------------- meetings
@ptm_bp.route("/")
@login_required
@role_required(*VIEWERS)
def list_meetings():
    school_id = current_school_id()
    when = request.args.get("when", "upcoming")
    page = request.args.get("page", 1, type=int)
    query = PTMMeeting.query.filter_by(school_id=school_id)
    if when == "upcoming":
        query = query.filter(PTMMeeting.meeting_date >= date.today()).order_by(PTMMeeting.meeting_date, PTMMeeting.start_time)
    else:
        if when == "past":
            query = query.filter(PTMMeeting.meeting_date < date.today())
        query = query.order_by(PTMMeeting.meeting_date.desc(), PTMMeeting.start_time)
    pagination = query.paginate(page=page, per_page=PER_PAGE, error_out=False)
    ids = [m.id for m in pagination.items]
    counts = dict(
        db.session.query(PTMAppointment.meeting_id, func.count(PTMAppointment.id))
        .filter(PTMAppointment.meeting_id.in_(ids or [0]), PTMAppointment.status.in_(ACTIVE_STATUSES))
        .group_by(PTMAppointment.meeting_id).all()
    )
    return render_template("ptm/list.html", pagination=pagination, meetings=pagination.items, counts=counts, when=when,
                           scope_label=scope_label, is_admin=current_user.role == UserRole.ADMIN)


@ptm_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def new_meeting():
    school_id = current_school_id()
    active = _active_session(school_id)
    if not active:
        flash("Create and activate an academic session before scheduling a meeting.", "warning")
        return redirect(url_for("ptm.list_meetings"))
    form = MeetingForm()
    sections_by_class = _meeting_choices(form, school_id)
    if form.validate_on_submit():
        class_id, section_id, ok = _check_meeting(form, school_id)
        if ok:
            meeting = PTMMeeting(
                school_id=school_id, session_id=active.id, class_id=class_id, section_id=section_id,
                title=form.title.data.strip(), description=(form.description.data or "").strip() or None,
                meeting_date=form.meeting_date.data, start_time=form.start_time.data, end_time=form.end_time.data,
                slot_minutes=form.slot_minutes.data, location=(form.location.data or "").strip() or None,
                created_by_id=current_user.id,
            )
            db.session.add(meeting)
            db.session.flush()
            log_action("ptm.created", "ptm_meetings", meeting.id,
                       new_value={"title": meeting.title, "date": meeting.meeting_date.isoformat(),
                                  "slots": len(slots_for(meeting))})
            db.session.commit()
            flash(f"Meeting scheduled with {len(slots_for(meeting))} appointment slots per teacher.", "success")
            return redirect(url_for("ptm.view_meeting", meeting_id=meeting.id))
    return render_template("ptm/form.html", form=form, sections_by_class=sections_by_class, title="Schedule a Meeting",
                           meeting=None, locked=False)


@ptm_bp.route("/<int:meeting_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def edit_meeting(meeting_id):
    school_id = current_school_id()
    meeting = _meeting_or_404(meeting_id)
    if meeting.status != MeetingStatus.SCHEDULED:
        flash("Only a scheduled meeting can be edited.", "warning")
        return redirect(url_for("ptm.view_meeting", meeting_id=meeting.id))
    booked = active_appointments(meeting.id).count() > 0
    form = MeetingForm()
    sections_by_class = _meeting_choices(form, school_id, meeting)
    if request.method == "GET":
        form.title.data, form.description.data = meeting.title, meeting.description
        form.meeting_date.data, form.start_time.data, form.end_time.data = meeting.meeting_date, meeting.start_time, meeting.end_time
        form.slot_minutes.data, form.location.data = meeting.slot_minutes, meeting.location
        form.class_id.data, form.section_id.data = meeting.class_id or 0, meeting.section_id or 0
    if form.validate_on_submit():
        class_id, section_id, ok = _check_meeting(form, school_id, meeting)
        if ok and booked:
            changed = (form.start_time.data != meeting.start_time or form.end_time.data != meeting.end_time
                       or form.slot_minutes.data != meeting.slot_minutes or class_id != meeting.class_id
                       or section_id != meeting.section_id)
            if changed:
                form.slot_minutes.errors.append(
                    "Times, appointment length and class can't change while appointments are booked — "
                    "cancel those appointments first.")
                ok = False
        if ok:
            meeting.title, meeting.description = form.title.data.strip(), (form.description.data or "").strip() or None
            meeting.meeting_date, meeting.location = form.meeting_date.data, (form.location.data or "").strip() or None
            if not booked:
                meeting.start_time, meeting.end_time, meeting.slot_minutes = form.start_time.data, form.end_time.data, form.slot_minutes.data
                meeting.class_id, meeting.section_id = class_id, section_id
            log_action("ptm.edited", "ptm_meetings", meeting.id,
                       new_value={"title": meeting.title, "date": meeting.meeting_date.isoformat()})
            db.session.commit()
            flash("Meeting updated.", "success")
            return redirect(url_for("ptm.view_meeting", meeting_id=meeting.id))
    return render_template("ptm/form.html", form=form, sections_by_class=sections_by_class, title="Edit Meeting",
                           meeting=meeting, locked=booked)


@ptm_bp.route("/<int:meeting_id>/complete", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN)
def complete_meeting(meeting_id):
    meeting = _meeting_or_404(meeting_id)
    if meeting.status != MeetingStatus.SCHEDULED:
        flash("Only a scheduled meeting can be marked completed.", "warning")
    else:
        meeting.status = MeetingStatus.COMPLETED
        pending = active_appointments(meeting.id).filter(PTMAppointment.status == AppointmentStatus.SCHEDULED).count()
        log_action("ptm.completed", "ptm_meetings", meeting.id, new_value={"still_scheduled": pending})
        db.session.commit()
        flash("Meeting marked completed." + (f" {pending} appointment(s) are still marked scheduled — "
              "record whether they took place." if pending else ""), "success")
    return redirect(url_for("ptm.view_meeting", meeting_id=meeting.id))


@ptm_bp.route("/<int:meeting_id>/cancel", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN)
def cancel_meeting(meeting_id):
    meeting = _meeting_or_404(meeting_id)
    if meeting.status != MeetingStatus.SCHEDULED:
        flash("Only a scheduled meeting can be cancelled.", "warning")
        return redirect(url_for("ptm.view_meeting", meeting_id=meeting.id))
    pending = PTMAppointment.query.filter_by(meeting_id=meeting.id, status=AppointmentStatus.SCHEDULED).all()
    for appointment in pending:
        appointment.status = AppointmentStatus.CANCELLED
    meeting.status = MeetingStatus.CANCELLED
    log_action("ptm.cancelled", "ptm_meetings", meeting.id, new_value={"appointments_cancelled": len(pending)})
    db.session.commit()
    flash(f"Meeting cancelled ({len(pending)} appointment(s) cancelled with it). {ns.note(ns.notify_ptm_meeting_cancelled(meeting, pending, current_user.id))}".strip(), "success")
    return redirect(url_for("ptm.view_meeting", meeting_id=meeting.id))


# ----------------------------------------------------------------- the meeting page + booking
def _booking_form_setup(form, school_id, meeting, students):
    teachers = [current_user] if current_user.role == UserRole.TEACHER else _teachers(school_id)
    form.teacher_id.choices = [(t.id, t.name) for t in teachers]
    form.student_id.choices = [(s.id, f"{s.name} — {s.current_class.name if s.current_class else ''}"
                                      f"{' ' + s.current_section.name if s.current_section else ''}") for s in students]
    form.slot.choices = [(t.strftime("%H:%M"), slot_label(meeting, t)) for t in slots_for(meeting)]


@ptm_bp.route("/<int:meeting_id>")
@login_required
@role_required(*VIEWERS)
def view_meeting(meeting_id):
    school_id = current_school_id()
    meeting = _meeting_or_404(meeting_id)
    teacher_filter = request.args.get("teacher_id", type=int)
    appointments = (PTMAppointment.query.filter_by(meeting_id=meeting.id)
                    .order_by(PTMAppointment.slot_start, PTMAppointment.id).all())
    by_teacher, cancelled, busy_teacher, busy_student = {}, [], {}, {}
    for a in appointments:
        if a.status == AppointmentStatus.CANCELLED:
            cancelled.append(a)
            continue
        by_teacher.setdefault(a.teacher_id, []).append(a)
        busy_teacher.setdefault(a.teacher_id, []).append(a.slot_start.strftime("%H:%M"))
        busy_student.setdefault(a.student_id, []).append(a.slot_start.strftime("%H:%M"))
    teacher_names = {t.id: t.name for t in _teachers(school_id)}
    for a in appointments:
        teacher_names.setdefault(a.teacher_id, a.teacher.name if a.teacher else "Teacher")
    if teacher_filter:
        by_teacher = {k: v for k, v in by_teacher.items() if k == teacher_filter}

    can_book = meeting.status == MeetingStatus.SCHEDULED
    form, students, guardians = None, [], {}
    if can_book:
        students = students_in_scope(school_id, meeting)
        form = BookingForm()
        _booking_form_setup(form, school_id, meeting, students)
        guardians = guardians_by_student([s.id for s in students])
    return render_template(
        "ptm/view.html", meeting=meeting, form=form, by_teacher=by_teacher, cancelled=cancelled,
        teacher_names=teacher_names, teacher_filter=teacher_filter, slots=[(t.strftime("%H:%M"), slot_label(meeting, t)) for t in slots_for(meeting)],
        busy_teacher=busy_teacher, busy_student=busy_student, guardians=guardians, scope=scope_label(meeting),
        is_admin=current_user.role == UserRole.ADMIN, can_book=can_book, status_colors=STATUS_COLORS,
        can_cancel=can_cancel, can_record=can_record_outcome, guardian_label=guardian_label, slot_label=slot_label,
        student_count=len(students),
    )


@ptm_bp.route("/<int:meeting_id>/book", methods=["POST"])
@login_required
@role_required(*VIEWERS)
def book(meeting_id):
    school_id = current_school_id()
    meeting = _meeting_or_404(meeting_id)
    if meeting.status != MeetingStatus.SCHEDULED:
        flash("This meeting is no longer taking bookings.", "warning")
        return redirect(url_for("ptm.view_meeting", meeting_id=meeting.id))
    students = students_in_scope(school_id, meeting)
    form = BookingForm()
    _booking_form_setup(form, school_id, meeting, students)
    problems = []
    if form.validate_on_submit():
        if not can_book_for(current_user, form.teacher_id.data):
            abort(403)
        teacher = User.query.filter_by(id=form.teacher_id.data, school_id=school_id, role=UserRole.TEACHER,
                                       is_active_account=True).first()
        student = next((s for s in students if s.id == form.student_id.data), None)
        slot = datetime.strptime(form.slot.data, "%H:%M").time()
        guardian_id = form.guardian_id.data or None
        if not teacher or not student:
            problems.append("Choose a teacher and a student from the lists.")
        else:
            if guardian_id and not StudentGuardian.query.filter_by(student_id=student.id, guardian_id=guardian_id).first():
                problems.append("That person isn't linked to this student as a guardian.")
            problems += find_conflicts(meeting, teacher, student, slot)
        if not problems:
            appointment = PTMAppointment(
                school_id=school_id, meeting_id=meeting.id, student_id=student.id, teacher_id=teacher.id,
                guardian_id=guardian_id, slot_start=slot, notes=(form.notes.data or "").strip() or None)
            db.session.add(appointment)
            try:
                db.session.flush()
                log_action("ptm.appointment_booked", "ptm_appointments", appointment.id,
                           new_value={"meeting_id": meeting.id, "teacher_id": teacher.id, "student_id": student.id,
                                      "slot": slot.strftime("%H:%M")})
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("That slot was just taken by someone else. Please choose another.", "danger")
                return redirect(url_for("ptm.view_meeting", meeting_id=meeting.id))
            flash(f"Appointment booked. {ns.note(ns.notify_ptm_booked(appointment, current_user.id))}".strip(), "success")
            return redirect(url_for("ptm.view_meeting", meeting_id=meeting.id))
    else:
        for field_errors in form.errors.values():
            problems += field_errors
    for p in problems:
        flash(p, "danger")
    return redirect(url_for("ptm.view_meeting", meeting_id=meeting.id))


@ptm_bp.route("/appointment/<int:appointment_id>/update", methods=["POST"])
@login_required
@role_required(*VIEWERS)
def update_appointment(appointment_id):
    school_id = current_school_id()
    appointment = PTMAppointment.query.filter_by(id=appointment_id, school_id=school_id).first_or_404()
    meeting = appointment.meeting
    action = request.form.get("action", "")
    back = redirect(url_for("ptm.view_meeting", meeting_id=meeting.id))

    if action == "cancel":
        if not can_cancel(current_user, appointment):
            abort(403)
        if appointment.status != AppointmentStatus.SCHEDULED:
            flash("Only a scheduled appointment can be cancelled.", "warning")
            return back
        appointment.status = AppointmentStatus.CANCELLED
        log_action("ptm.appointment_cancelled", "ptm_appointments", appointment.id, new_value={"meeting_id": meeting.id})
        db.session.commit()
        flash(f"Appointment cancelled. The slot is free again. {ns.note(ns.notify_ptm_cancelled(appointment, current_user.id))}".strip(), "success")
        return back

    if not can_record_outcome(current_user, appointment):
        abort(403)
    if appointment.status == AppointmentStatus.CANCELLED:
        flash("A cancelled appointment can't be changed — book a new one.", "warning")
        return back

    if action in ("complete", "no_show"):
        if appointment.status != AppointmentStatus.SCHEDULED:
            flash("Only a scheduled appointment can be marked.", "warning")
            return back
        appointment.status = AppointmentStatus.COMPLETED if action == "complete" else AppointmentStatus.NO_SHOW
        log_action(f"ptm.appointment_{action}", "ptm_appointments", appointment.id, new_value={"meeting_id": meeting.id})
        db.session.commit()
        flash("Marked as " + ("completed." if action == "complete" else "a no-show."), "success")
    elif action == "reopen":
        if appointment.status not in (AppointmentStatus.COMPLETED, AppointmentStatus.NO_SHOW):
            flash("Nothing to reopen.", "info")
            return back
        appointment.status = AppointmentStatus.SCHEDULED
        log_action("ptm.appointment_reopened", "ptm_appointments", appointment.id, new_value={"meeting_id": meeting.id})
        db.session.commit()
        flash("Appointment set back to scheduled.", "success")
    elif action == "notes":
        appointment.notes = (request.form.get("notes", "").strip()[:1000]) or None
        log_action("ptm.appointment_notes", "ptm_appointments", appointment.id, new_value={"meeting_id": meeting.id})
        db.session.commit()
        flash("Notes saved.", "success")
    else:
        abort(400)
    return back
