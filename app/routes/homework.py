from datetime import date, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Homework, HomeworkSubmission, SchoolClass, Section, Subject, User, AcademicSession
from app.models.enums import UserRole, RecordStatus, HomeworkStatus, SubmissionStatus
from app.forms.homework import HomeworkForm, HomeworkEditForm
from app.utils.decorators import role_required
from app.utils.tenant import current_school_id
from app.services import notification_service as ns
from app.services.audit_service import log_action
from app.services.homework_service import (
    target_students, summarize, progress_for, due_state, can_manage, DONE,
)

homework_bp = Blueprint("homework", __name__, url_prefix="/homework")

STAFF = (UserRole.ADMIN, UserRole.TEACHER)
PER_PAGE = 20
MAX_WINDOW_DAYS = 365


def _active_session(school_id):
    return AcademicSession.query.filter_by(school_id=school_id, is_active=True).first()


def _teachers(school_id):
    return (User.query.filter_by(school_id=school_id, role=UserRole.TEACHER, is_active_account=True)
            .order_by(User.name).all())


def _prepare_choices(form, school_id):
    """Dropdowns for the create form. A teacher only gets subjects assigned to them.
    Returns (sections_by_class, subjects_by_class) for the page's cascading filters."""
    active = _active_session(school_id)
    classes = (SchoolClass.query.filter_by(school_id=school_id, session_id=active.id)
               .order_by(SchoolClass.name).all()) if active else []
    class_ids = [c.id for c in classes]
    subject_query = Subject.query.filter(
        Subject.school_id == school_id, Subject.status == RecordStatus.ACTIVE, Subject.class_id.in_(class_ids or [0]))
    if current_user.role == UserRole.TEACHER:
        subject_query = subject_query.filter(Subject.teacher_id == current_user.id)
    subjects = subject_query.order_by(Subject.name).all()

    form.class_id.choices = [(0, "— choose a class —")] + [(c.id, c.name) for c in classes]
    form.section_id.choices = [(0, "All sections")] + [(s.id, f"{c.name} – {s.name}") for c in classes for s in c.sections]
    form.subject_id.choices = [(0, "— choose a subject —")] + [(s.id, f"{s.name} ({s.code})") for s in subjects]
    sections_by_class = {c.id: [[s.id, s.name] for s in c.sections] for c in classes}
    subjects_by_class = {}
    for s in subjects:
        subjects_by_class.setdefault(s.class_id, []).append([s.id, f"{s.name} ({s.code})"])
    return sections_by_class, subjects_by_class, bool(subjects)


def _set_teacher_choices(form, school_id):
    if current_user.role == UserRole.ADMIN:
        form.teacher_id.choices = [(0, "The subject's own teacher")] + [(t.id, t.name) for t in _teachers(school_id)]
    else:
        del form.teacher_id            # a teacher always assigns homework to themselves


def _check_dates(form):
    good = True
    if form.due_date.data < form.assigned_date.data:
        form.due_date.errors.append("The due date can't be before the assigned date.")
        good = False
    elif (form.due_date.data - form.assigned_date.data).days > MAX_WINDOW_DAYS:
        form.due_date.errors.append("The due date can be at most a year after the assigned date.")
        good = False
    return good


def _resolve_teacher(form, subject_teacher_id, school_id):
    """Teacher responsible for this homework, or None (with an error on the form)."""
    if current_user.role == UserRole.TEACHER:
        return current_user.id
    chosen = form.teacher_id.data or None
    if chosen:
        if not User.query.filter_by(id=chosen, school_id=school_id, role=UserRole.TEACHER, is_active_account=True).first():
            form.teacher_id.errors.append("Choose an active teacher from this school.")
            return None
        return chosen
    if subject_teacher_id:
        return subject_teacher_id
    form.teacher_id.errors.append("This subject has no teacher assigned — choose a teacher.")
    return None


@homework_bp.route("/")
@login_required
@role_required(*STAFF)
def list_homework():
    school_id = current_school_id()
    is_admin = current_user.role == UserRole.ADMIN
    scope = request.args.get("scope", "all" if is_admin else "mine")
    when = request.args.get("when", "upcoming")
    status = request.args.get("status", "active")
    class_id = request.args.get("class_id", type=int)
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    today = date.today()

    query = Homework.query.filter_by(school_id=school_id)
    if not is_admin and scope == "mine":
        query = query.filter(Homework.teacher_id == current_user.id)
    if class_id:
        query = query.filter(Homework.class_id == class_id)
    if status in {s.value for s in HomeworkStatus}:
        query = query.filter(Homework.status == HomeworkStatus(status))
    if when == "upcoming":
        query = query.filter(Homework.due_date >= today).order_by(Homework.due_date, Homework.id)
    else:
        if when == "past":
            query = query.filter(Homework.due_date < today)
        query = query.order_by(Homework.due_date.desc(), Homework.id.desc())
    if q:
        query = query.filter(Homework.title.ilike(f"%{q}%"))

    pagination = query.paginate(page=page, per_page=PER_PAGE, error_out=False)
    active = _active_session(school_id)
    classes = (SchoolClass.query.filter_by(school_id=school_id, session_id=active.id).order_by(SchoolClass.name).all()
               if active else [])
    return render_template(
        "homework/list.html", pagination=pagination, items=pagination.items, classes=classes, is_admin=is_admin,
        progress=progress_for(school_id, pagination.items), due_state=due_state, today=today,
        scope=scope, when=when, status=status, class_id=class_id, q=q,
    )


@homework_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(*STAFF)
def new_homework():
    school_id = current_school_id()
    active = _active_session(school_id)
    if not active:
        flash("Create and activate an academic session before assigning homework.", "warning")
        return redirect(url_for("homework.list_homework"))

    form = HomeworkForm()
    sections_by_class, subjects_by_class, has_subjects = _prepare_choices(form, school_id)
    _set_teacher_choices(form, school_id)
    if not has_subjects:
        flash("There are no subjects you can assign homework for yet. "
              "Subjects must be assigned to a teacher by an Admin.", "warning")
        return redirect(url_for("homework.list_homework"))

    if form.validate_on_submit():
        dates_ok = _check_dates(form)
        school_class = SchoolClass.query.filter_by(id=form.class_id.data, school_id=school_id, session_id=active.id).first()
        subject = None
        if not school_class:
            form.class_id.errors.append("Choose a class from the active session.")
        else:
            subject = Subject.query.filter_by(id=form.subject_id.data, school_id=school_id,
                                              class_id=school_class.id, status=RecordStatus.ACTIVE).first()
            if not subject:
                form.subject_id.errors.append("Choose a subject that belongs to that class.")
            elif current_user.role == UserRole.TEACHER and subject.teacher_id != current_user.id:
                form.subject_id.errors.append("You can only assign homework for subjects assigned to you.")
                subject = None
        section_id = form.section_id.data or None
        if school_class and section_id and not Section.query.filter_by(id=section_id, class_id=school_class.id).first():
            form.section_id.errors.append("That section doesn't belong to the chosen class.")
            section_id = -1
        teacher_id = _resolve_teacher(form, subject.teacher_id if subject else None, school_id) if subject else None

        if dates_ok and school_class and subject and section_id != -1 and teacher_id:
            homework = Homework(
                school_id=school_id, session_id=active.id, class_id=school_class.id, section_id=section_id,
                subject_id=subject.id, teacher_id=teacher_id, title=form.title.data.strip(),
                description=(form.description.data or "").strip() or None,
                assigned_date=form.assigned_date.data, due_date=form.due_date.data,
            )
            db.session.add(homework)
            db.session.flush()
            log_action("homework.created", "homework", homework.id,
                       new_value={"title": homework.title, "class_id": homework.class_id, "section_id": homework.section_id,
                                  "subject_id": homework.subject_id, "due": homework.due_date.isoformat()})
            db.session.commit()
            flash(f"Homework assigned. {ns.note(ns.notify_homework_assigned(homework, current_user.id))}".strip(), "success")
            return redirect(url_for("homework.view_homework", homework_id=homework.id))

    return render_template("homework/form.html", form=form, sections_by_class=sections_by_class,
                           subjects_by_class=subjects_by_class, today=date.today())


@homework_bp.route("/<int:homework_id>")
@login_required
@role_required(*STAFF)
def view_homework(homework_id):
    homework = Homework.query.filter_by(id=homework_id, school_id=current_school_id()).first_or_404()
    students = target_students(homework)
    rows = {s.student_id: s for s in HomeworkSubmission.query.filter_by(homework_id=homework.id).all()}
    counts = {}
    for student in students:
        row = rows.get(student.id)
        if row:
            counts[row.status] = counts.get(row.status, 0) + 1
    return render_template(
        "homework/view.html", homework=homework, students=students, rows=rows, summary=summarize(len(students), counts),
        manage=can_manage(current_user, homework), statuses=list(SubmissionStatus),
        state=due_state(homework),
    )


@homework_bp.route("/<int:homework_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(*STAFF)
def edit_homework(homework_id):
    school_id = current_school_id()
    homework = Homework.query.filter_by(id=homework_id, school_id=school_id).first_or_404()
    if not can_manage(current_user, homework):
        abort(403)
    form = HomeworkEditForm()
    _set_teacher_choices(form, school_id)
    if request.method == "GET":
        form.title.data = homework.title
        form.description.data = homework.description
        form.assigned_date.data = homework.assigned_date
        form.due_date.data = homework.due_date
        if "teacher_id" in form:            # absent for teachers (deleted from the form)
            form.teacher_id.data = homework.teacher_id or 0
    if form.validate_on_submit() and _check_dates(form):
        teacher_ok = True
        if current_user.role == UserRole.ADMIN:
            chosen = form.teacher_id.data or None
            if chosen:
                if User.query.filter_by(id=chosen, school_id=school_id, role=UserRole.TEACHER, is_active_account=True).first():
                    homework.teacher_id = chosen
                else:
                    form.teacher_id.errors.append("Choose an active teacher from this school.")
                    teacher_ok = False
        if teacher_ok:
            homework.title = form.title.data.strip()
            homework.description = (form.description.data or "").strip() or None
            homework.assigned_date = form.assigned_date.data
            homework.due_date = form.due_date.data
            log_action("homework.edited", "homework", homework.id,
                       new_value={"title": homework.title, "due": homework.due_date.isoformat()})
            db.session.commit()
            flash("Homework updated.", "success")
            return redirect(url_for("homework.view_homework", homework_id=homework.id))
        db.session.rollback()
    return render_template("homework/edit_form.html", form=form, homework=homework)


@homework_bp.route("/<int:homework_id>/submissions", methods=["POST"])
@login_required
@role_required(*STAFF)
def save_submissions(homework_id):
    homework = Homework.query.filter_by(id=homework_id, school_id=current_school_id()).first_or_404()
    if not can_manage(current_user, homework):
        abort(403)
    if homework.status != HomeworkStatus.ACTIVE:
        flash("This homework is cancelled. Reinstate it before recording submissions.", "warning")
        return redirect(url_for("homework.view_homework", homework_id=homework.id))

    students = target_students(homework)            # only these students can be recorded; anything else posted is ignored
    existing = {s.student_id: s for s in HomeworkSubmission.query.filter_by(homework_id=homework.id).all()}

    # A student whose field is ABSENT from the request is left untouched (a partial or stale
    # request must never erase records). Only an explicitly empty value clears the entry.
    plan, invalid = [], []
    for student in students:
        status_key = f"status_{student.id}"
        if status_key not in request.form:
            continue
        raw = request.form.get(status_key, "")
        remarks_raw = request.form.get(f"remarks_{student.id}")
        if remarks_raw is None:
            current = existing.get(student.id)
            remarks = current.remarks if current else None
        else:
            remarks = remarks_raw.strip()[:255] or None
        if raw == "":
            plan.append((student, None, None))
            continue
        try:
            plan.append((student, SubmissionStatus(raw), remarks))
        except ValueError:
            invalid.append(student.name)
    if invalid:
        flash("Unrecognised status for: " + ", ".join(invalid) + ". Nothing was saved.", "danger")
        return redirect(url_for("homework.view_homework", homework_id=homework.id))

    created = updated = cleared = 0
    today = date.today()
    for student, status, remarks in plan:
        row = existing.get(student.id)
        if status is None:                       # "not recorded" clears any earlier entry
            if row:
                db.session.delete(row)
                cleared += 1
            continue
        if row is None:
            db.session.add(HomeworkSubmission(
                school_id=homework.school_id, homework_id=homework.id, student_id=student.id, status=status,
                submitted_on=today if status in DONE else None, remarks=remarks, marked_by_id=current_user.id))
            created += 1
        elif row.status != status or (row.remarks or None) != remarks:
            if status in DONE and row.submitted_on is None:
                row.submitted_on = today
            elif status not in DONE:
                row.submitted_on = None
            row.status, row.remarks, row.marked_by_id = status, remarks, current_user.id
            updated += 1
    if created or updated or cleared:
        log_action("homework.submissions_saved", "homework", homework.id,
                   new_value={"created": created, "updated": updated, "cleared": cleared})
    db.session.commit()
    flash(f"Submissions saved ({created} added, {updated} changed, {cleared} cleared)." if (created or updated or cleared)
          else "No changes to save.", "success" if (created or updated or cleared) else "info")
    return redirect(url_for("homework.view_homework", homework_id=homework.id))


@homework_bp.route("/<int:homework_id>/cancel", methods=["POST"])
@login_required
@role_required(*STAFF)
def cancel_homework(homework_id):
    homework = Homework.query.filter_by(id=homework_id, school_id=current_school_id()).first_or_404()
    if not can_manage(current_user, homework):
        abort(403)
    if homework.status == HomeworkStatus.ACTIVE:
        homework.status = HomeworkStatus.CANCELLED
        log_action("homework.cancelled", "homework", homework.id, new_value={"title": homework.title})
        db.session.commit()
        flash("Homework cancelled. Its records are kept.", "success")
    return redirect(url_for("homework.view_homework", homework_id=homework.id))


@homework_bp.route("/<int:homework_id>/reinstate", methods=["POST"])
@login_required
@role_required(*STAFF)
def reinstate_homework(homework_id):
    homework = Homework.query.filter_by(id=homework_id, school_id=current_school_id()).first_or_404()
    if not can_manage(current_user, homework):
        abort(403)
    if homework.status == HomeworkStatus.CANCELLED:
        homework.status = HomeworkStatus.ACTIVE
        log_action("homework.reinstated", "homework", homework.id, new_value={"title": homework.title})
        db.session.commit()
        flash("Homework reinstated.", "success")
    return redirect(url_for("homework.view_homework", homework_id=homework.id))


@homework_bp.route("/<int:homework_id>/delete", methods=["POST"])
@login_required
@role_required(*STAFF)
def delete_homework(homework_id):
    homework = Homework.query.filter_by(id=homework_id, school_id=current_school_id()).first_or_404()
    if not can_manage(current_user, homework):
        abort(403)
    if HomeworkSubmission.query.filter_by(homework_id=homework.id).count():
        flash("Submissions have been recorded for this homework, so it can't be deleted. Cancel it instead.", "warning")
        return redirect(url_for("homework.view_homework", homework_id=homework.id))
    log_action("homework.deleted", "homework", homework.id, old_value={"title": homework.title})
    db.session.delete(homework)
    db.session.commit()
    flash("Homework deleted.", "info")
    return redirect(url_for("homework.list_homework"))
