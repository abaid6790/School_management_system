from datetime import date, datetime, timezone

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Notice, SchoolClass, Section, AcademicSession
from app.models.enums import UserRole, NoticeAudience, NoticeStatus
from app.forms.notice import NoticeForm
from app.utils.decorators import role_required
from app.utils.tenant import current_school_id
from app.services.audit_service import log_action
from app.services.notice_service import is_expired, audience_label, staff_board_query, staff_can_view
from app.services import notification_service as ns

notices_bp = Blueprint("notices", __name__, url_prefix="/notices")

ALL_STAFF = (UserRole.ADMIN, UserRole.TEACHER, UserRole.ACCOUNTANT, UserRole.RECEPTIONIST)
PER_PAGE = 20


def _now():
    return datetime.now(timezone.utc)


def _prepare_choices(form, school_id, notice=None):
    """Class/section dropdowns for the active session (plus the notice's own class
    when editing, so an older notice stays editable). Returns {class_id: [[sec_id, name]]}
    for the page's section filter."""
    active = AcademicSession.query.filter_by(school_id=school_id, is_active=True).first()
    classes = []
    if active:
        classes = SchoolClass.query.filter_by(school_id=school_id, session_id=active.id).order_by(SchoolClass.name).all()
    if notice is not None and notice.school_class is not None and notice.school_class not in classes:
        classes.append(notice.school_class)
    form.class_id.choices = [(0, "— choose a class —")] + [(c.id, c.name) for c in classes]
    form.section_id.choices = [(0, "All sections")] + [(s.id, f"{c.name} – {s.name}") for c in classes for s in c.sections]
    return {c.id: [[s.id, s.name] for s in c.sections] for c in classes}


def _resolve_target(form, school_id, audience):
    """Returns (class_id, section_id, ok). Only a CLASS notice carries a class/section."""
    if audience != NoticeAudience.CLASS:
        return None, None, True
    class_id = form.class_id.data or None
    section_id = form.section_id.data or None
    if not class_id:
        form.class_id.errors.append("Choose the class this notice is for.")
        return None, None, False
    if not SchoolClass.query.filter_by(id=class_id, school_id=school_id).first():
        form.class_id.errors.append("That class was not found.")
        return None, None, False
    if section_id and not Section.query.filter_by(id=section_id, class_id=class_id).first():
        form.section_id.errors.append("That section doesn't belong to the chosen class.")
        return None, None, False
    return class_id, section_id, True


def _expiry_ok(form, notice=None):
    expires_on = form.expires_on.data
    unchanged = notice is not None and notice.expires_on == expires_on
    if expires_on and expires_on < date.today() and not unchanged:
        form.expires_on.errors.append("The expiry date can't be in the past.")
        return False
    return True


@notices_bp.route("/")
@login_required
@role_required(*ALL_STAFF)
def list_notices():
    school_id = current_school_id()
    if current_user.role != UserRole.ADMIN:
        notices = staff_board_query(school_id, current_user.role).all()
        return render_template("notices/list.html", is_admin=False, notices=notices, is_expired=is_expired,
                               audience_label=audience_label)

    q = request.args.get("q", "").strip()
    status = request.args.get("status", "")
    audience = request.args.get("audience", "")
    page = request.args.get("page", 1, type=int)

    query = Notice.query.filter_by(school_id=school_id)
    if q:
        query = query.filter(Notice.title.ilike(f"%{q}%"))
    if status in {s.value for s in NoticeStatus}:
        query = query.filter_by(status=NoticeStatus(status))
    if audience in {a.value for a in NoticeAudience}:
        query = query.filter_by(audience=NoticeAudience(audience))

    pagination = query.order_by(Notice.is_pinned.desc(), Notice.created_at.desc()).paginate(
        page=page, per_page=PER_PAGE, error_out=False)
    return render_template(
        "notices/list.html", is_admin=True, pagination=pagination, notices=pagination.items, q=q, status=status,
        audience=audience, statuses=list(NoticeStatus), audiences=list(NoticeAudience),
        is_expired=is_expired, audience_label=audience_label,
    )


@notices_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def new_notice():
    school_id = current_school_id()
    form = NoticeForm()
    sections_by_class = _prepare_choices(form, school_id)

    if form.validate_on_submit():
        audience = NoticeAudience(form.audience.data)
        class_id, section_id, target_ok = _resolve_target(form, school_id, audience)
        expiry_ok = _expiry_ok(form)
        if target_ok and expiry_ok:
            publish = request.form.get("action") == "publish"
            notice = Notice(
                school_id=school_id, title=form.title.data.strip(), body=form.body.data.strip(), audience=audience,
                class_id=class_id, section_id=section_id, expires_on=form.expires_on.data,
                is_pinned=form.is_pinned.data, created_by_id=current_user.id,
                status=NoticeStatus.PUBLISHED if publish else NoticeStatus.DRAFT,
                published_at=_now() if publish else None,
            )
            db.session.add(notice)
            db.session.flush()
            log_action("notice.created", "notices", notice.id,
                       new_value={"title": notice.title, "audience": audience.value, "status": notice.status.value})
            db.session.commit()
            if publish:
                flash(f"Notice published. {ns.note(ns.notify_notice_published(notice, current_user.id))}".strip(), "success")
            else:
                flash("Notice saved as a draft.", "success")
            return redirect(url_for("notices.view_notice", notice_id=notice.id))

    return render_template("notices/form.html", form=form, sections_by_class=sections_by_class,
                           title="New Notice", notice=None)


@notices_bp.route("/<int:notice_id>")
@login_required
@role_required(*ALL_STAFF)
def view_notice(notice_id):
    notice = Notice.query.filter_by(id=notice_id, school_id=current_school_id()).first_or_404()
    is_admin = current_user.role == UserRole.ADMIN
    if not is_admin and not staff_can_view(notice, current_user.role):
        abort(404)   # not revealed to people it isn't addressed to
    return render_template("notices/view.html", notice=notice, is_admin=is_admin,
                           expired=is_expired(notice), audience_text=audience_label(notice))


@notices_bp.route("/<int:notice_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def edit_notice(notice_id):
    school_id = current_school_id()
    notice = Notice.query.filter_by(id=notice_id, school_id=school_id).first_or_404()
    form = NoticeForm()
    sections_by_class = _prepare_choices(form, school_id, notice)

    if request.method == "GET":
        form.title.data = notice.title
        form.body.data = notice.body
        form.audience.data = notice.audience.value
        form.class_id.data = notice.class_id or 0
        form.section_id.data = notice.section_id or 0
        form.expires_on.data = notice.expires_on
        form.is_pinned.data = notice.is_pinned

    if form.validate_on_submit():
        audience = NoticeAudience(form.audience.data)
        class_id, section_id, target_ok = _resolve_target(form, school_id, audience)
        expiry_ok = _expiry_ok(form, notice)
        if target_ok and expiry_ok:
            notice.title = form.title.data.strip()
            notice.body = form.body.data.strip()
            notice.audience = audience
            notice.class_id, notice.section_id = class_id, section_id
            notice.expires_on = form.expires_on.data
            notice.is_pinned = form.is_pinned.data
            publish_now = request.form.get("action") == "publish" and notice.status == NoticeStatus.DRAFT
            first_publication = publish_now and notice.published_at is None
            if publish_now:
                notice.status = NoticeStatus.PUBLISHED
                notice.published_at = notice.published_at or _now()
            log_action("notice.edited", "notices", notice.id,
                       new_value={"title": notice.title, "audience": audience.value, "status": notice.status.value})
            db.session.commit()
            if first_publication:
                flash(f"Notice published. {ns.note(ns.notify_notice_published(notice, current_user.id))}".strip(), "success")
            else:
                flash("Notice published." if publish_now else "Notice updated.", "success")
            return redirect(url_for("notices.view_notice", notice_id=notice.id))

    return render_template("notices/form.html", form=form, sections_by_class=sections_by_class,
                           title="Edit Notice", notice=notice)


@notices_bp.route("/<int:notice_id>/publish", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN)
def publish_notice(notice_id):
    notice = Notice.query.filter_by(id=notice_id, school_id=current_school_id()).first_or_404()
    if notice.status == NoticeStatus.PUBLISHED:
        flash("This notice is already published.", "info")
    elif is_expired(notice):
        flash("This notice's expiry date has already passed. Edit it to set a new date first.", "warning")
    else:
        first_publication = notice.published_at is None        # re-publishing an archived notice does not re-notify anyone
        notice.status = NoticeStatus.PUBLISHED
        notice.published_at = notice.published_at or _now()
        log_action("notice.published", "notices", notice.id, new_value={"title": notice.title})
        db.session.commit()
        if first_publication:
            flash(f"Notice published. {ns.note(ns.notify_notice_published(notice, current_user.id))}".strip(), "success")
        else:
            flash("Notice published.", "success")
    return redirect(url_for("notices.view_notice", notice_id=notice.id))


@notices_bp.route("/<int:notice_id>/archive", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN)
def archive_notice(notice_id):
    notice = Notice.query.filter_by(id=notice_id, school_id=current_school_id()).first_or_404()
    if notice.status != NoticeStatus.PUBLISHED:
        flash("Only a published notice can be archived.", "warning")
    else:
        notice.status = NoticeStatus.ARCHIVED
        log_action("notice.archived", "notices", notice.id, new_value={"title": notice.title})
        db.session.commit()
        flash("Notice archived. It is no longer shown on the board.", "success")
    return redirect(url_for("notices.view_notice", notice_id=notice.id))


@notices_bp.route("/<int:notice_id>/delete", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN)
def delete_notice(notice_id):
    notice = Notice.query.filter_by(id=notice_id, school_id=current_school_id()).first_or_404()
    if notice.status != NoticeStatus.DRAFT:
        flash("Only drafts can be deleted. Published notices are kept on record — archive it instead.", "warning")
        return redirect(url_for("notices.view_notice", notice_id=notice.id))
    log_action("notice.deleted", "notices", notice.id, old_value={"title": notice.title})
    db.session.delete(notice)
    db.session.commit()
    flash("Draft deleted.", "info")
    return redirect(url_for("notices.list_notices"))
