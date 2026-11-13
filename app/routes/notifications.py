from datetime import datetime, timedelta, timezone

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func, and_, or_

from app.extensions import db
from app.models import Notification
from app.models.enums import UserRole, NotificationType
from app.utils.decorators import role_required
from app.utils.tenant import current_school_id
from app.services.audit_service import log_action
from app.services import notification_service as ns

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")
PER_PAGE = 25
LOG_PER_PAGE = 50
RETRY_LIMIT = 500
ICONS = {"general": "bell", "notice": "megaphone", "homework": "journal-text", "event": "calendar-event", "ptm": "people",
         "fee_due": "cash-coin", "leave": "calendar-check", "attendance": "clipboard-check", "result": "award"}


@notifications_bp.route("/")
@login_required
def inbox():
    only_unread = request.args.get("unread") == "1"
    page = request.args.get("page", 1, type=int)
    query = Notification.query.filter_by(recipient_user_id=current_user.id)
    if only_unread:
        query = query.filter_by(is_read=False)
    pagination = query.order_by(Notification.created_at.desc(), Notification.id.desc()).paginate(page=page, per_page=PER_PAGE, error_out=False)
    return render_template("notifications/inbox.html", pagination=pagination, items=pagination.items,
                           only_unread=only_unread, icons=ICONS)


@notifications_bp.route("/<int:notification_id>/go")
@login_required
def open_notification(notification_id):
    """Marks one of the signed-in user's own notifications read, then follows its (internal) link."""
    n = Notification.query.filter_by(id=notification_id, recipient_user_id=current_user.id).first_or_404()
    if not n.is_read:
        n.is_read, n.read_at = True, datetime.now(timezone.utc)
        db.session.commit()
    return redirect(ns.safe_internal_link(n.link_url) or url_for("notifications.inbox"))


@notifications_bp.route("/mark-all-read", methods=["POST"])
@login_required
def mark_all_read():
    updated = (Notification.query.filter_by(recipient_user_id=current_user.id, is_read=False)
               .update({"is_read": True, "read_at": datetime.now(timezone.utc)}))
    db.session.commit()
    flash(f"{updated} notification(s) marked as read." if updated else "Nothing to mark as read.", "info")
    return redirect(url_for("notifications.inbox"))


@notifications_bp.route("/delivery")
@login_required
@role_required(UserRole.ADMIN)
def delivery_log():
    school_id = current_school_id()
    status = request.args.get("status", "")
    ntype = request.args.get("type", "")
    page = request.args.get("page", 1, type=int)
    base = Notification.query.filter(Notification.school_id == school_id, Notification.recipient_guardian_id.isnot(None))

    def apply_status(query, s):
        if s == "sent":
            return query.filter(Notification.emailed_at.isnot(None))
        if s == "no_email":
            return query.filter(Notification.emailed_at.is_(None), Notification.email_error == ns.NO_EMAIL_ERROR)
        if s == "failed":
            return query.filter(Notification.emailed_at.is_(None), Notification.email_error.isnot(None), Notification.email_error != ns.NO_EMAIL_ERROR)
        if s == "pending":
            return query.filter(Notification.emailed_at.is_(None), Notification.email_error.is_(None))
        return query

    counts = {s: apply_status(base, s).count() for s in ("sent", "failed", "no_email", "pending")}
    query = apply_status(base, status)
    if ntype in {t.value for t in NotificationType}:
        query = query.filter(Notification.notification_type == NotificationType(ntype))
    pagination = query.order_by(Notification.created_at.desc(), Notification.id.desc()).paginate(page=page, per_page=LOG_PER_PAGE, error_out=False)
    return render_template("notifications/delivery.html", pagination=pagination, items=pagination.items, counts=counts,
                           status=status, ntype=ntype, types=list(NotificationType), delivery_status=ns.delivery_status,
                           guardian_name=ns.guardian_display_name)


@notifications_bp.route("/delivery/retry", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN)
def retry_failed():
    """Retries unsent guardian emails that can now go somewhere: ones that failed, ones whose guardian
    has since been given an address, and ones stuck 'pending' for over 10 minutes (e.g. the server
    restarted mid-mailing). Fresh pending ones are left alone — their worker may still be running.
    Already-sent emails are never resent, and 'switched off' rows are left as recorded."""
    school_id = current_school_id()
    stuck_before = datetime.now(timezone.utc) - timedelta(minutes=10)
    candidates = (Notification.query.filter(
        Notification.school_id == school_id, Notification.recipient_guardian_id.isnot(None), Notification.emailed_at.is_(None),
        or_(and_(Notification.email_error.isnot(None), Notification.email_error != ns.SWITCHED_OFF_ERROR),
            and_(Notification.email_error.is_(None), Notification.created_at <= stuck_before)))
        .order_by(Notification.id).limit(RETRY_LIMIT).all())
    ids = [n.id for n in candidates if n.recipient_guardian and (n.recipient_guardian.email or "").strip()]
    for n in candidates:
        if n.id in ids:
            n.email_error = None
    log_action("notification.retry", "notifications", None, new_value={"count": len(ids)})
    db.session.commit()
    ns.dispatch_emails(ids)
    flash(f"Retrying {len(ids)} email(s)." if ids else "Nothing to retry.", "info" if ids else "warning")
    return redirect(url_for("notifications.delivery_log"))
