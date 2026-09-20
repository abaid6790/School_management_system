from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models import AcademicSession, SchoolClass, Section, Subject, User, Period
from app.models.enums import UserRole, SubjectType
from app.forms.academic import AcademicSessionForm, SchoolClassForm, SectionForm, SubjectForm, PeriodForm
from app.utils.decorators import role_required
from app.utils.tenant import current_school_id
from app.services.audit_service import log_action

academic_bp = Blueprint("academic", __name__, url_prefix="/academic")


def _teacher_choices():
    school_id = current_school_id()
    teachers = User.query.filter_by(school_id=school_id, role=UserRole.TEACHER).order_by(User.name).all()
    return [(0, "— None —")] + [(t.id, t.name) for t in teachers]


# ---------------------------------------------------------------- Sessions --

@academic_bp.route("/sessions")
@login_required
@role_required(UserRole.ADMIN)
def session_list():
    sessions = (
        AcademicSession.query.filter_by(school_id=current_school_id())
        .order_by(AcademicSession.start_date.desc())
        .all()
    )
    return render_template("academic/session_list.html", sessions=sessions)


@academic_bp.route("/sessions/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def session_new():
    form = AcademicSessionForm()
    if form.validate_on_submit():
        school_id = current_school_id()

        if form.is_active.data:
            AcademicSession.query.filter_by(school_id=school_id, is_active=True).update({"is_active": False})

        session_obj = AcademicSession(
            school_id=school_id,
            name=form.name.data.strip(),
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            is_active=form.is_active.data,
            description=form.description.data,
        )
        db.session.add(session_obj)
        db.session.flush()
        log_action("academic_session.created", "academic_sessions", session_obj.id,
                   new_value={"name": session_obj.name, "is_active": session_obj.is_active})
        db.session.commit()
        flash(f"Session '{session_obj.name}' created.", "success")
        return redirect(url_for("academic.session_list"))

    return render_template("academic/session_form.html", form=form, title="New Academic Session")


@academic_bp.route("/sessions/<int:session_id>/activate", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN)
def session_activate(session_id):
    school_id = current_school_id()
    session_obj = AcademicSession.query.filter_by(id=session_id, school_id=school_id).first_or_404()

    AcademicSession.query.filter_by(school_id=school_id, is_active=True).update({"is_active": False})
    session_obj.is_active = True
    log_action("academic_session.activated", "academic_sessions", session_obj.id)
    db.session.commit()

    flash(f"'{session_obj.name}' is now the active session.", "success")
    return redirect(url_for("academic.session_list"))


# ------------------------------------------------------------------ Classes --

@academic_bp.route("/classes")
@login_required
@role_required(UserRole.ADMIN)
def class_list():
    session_id = request.args.get("session_id", type=int)
    school_id = current_school_id()

    query = SchoolClass.query.filter_by(school_id=school_id)
    if session_id:
        query = query.filter_by(session_id=session_id)
    classes = query.order_by(SchoolClass.name).all()

    sessions = AcademicSession.query.filter_by(school_id=school_id).order_by(AcademicSession.start_date.desc()).all()
    active_session = AcademicSession.query.filter_by(school_id=school_id, is_active=True).first()

    return render_template(
        "academic/class_list.html", classes=classes, sessions=sessions,
        selected_session_id=session_id, active_session=active_session,
    )


@academic_bp.route("/classes/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def class_new():
    school_id = current_school_id()
    active_session = AcademicSession.query.filter_by(school_id=school_id, is_active=True).first()
    if not active_session:
        flash("Create and activate an academic session before adding classes.", "warning")
        return redirect(url_for("academic.session_new"))

    form = SchoolClassForm()
    form.class_teacher_id.choices = _teacher_choices()

    if form.validate_on_submit():
        class_obj = SchoolClass(
            school_id=school_id,
            session_id=active_session.id,
            name=form.name.data.strip(),
            code=form.code.data.strip() if form.code.data else None,
            capacity=form.capacity.data,
            class_teacher_id=form.class_teacher_id.data or None,
        )
        db.session.add(class_obj)
        db.session.flush()
        log_action("class.created", "classes", class_obj.id, new_value={"name": class_obj.name})
        db.session.commit()
        flash(f"Class '{class_obj.name}' created for {active_session.name}.", "success")
        return redirect(url_for("academic.class_list"))

    return render_template("academic/class_form.html", form=form, title="New Class", active_session=active_session)


@academic_bp.route("/classes/<int:class_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def class_edit(class_id):
    class_obj = SchoolClass.query.filter_by(id=class_id, school_id=current_school_id()).first_or_404()
    form = SchoolClassForm(obj=class_obj)
    form.class_teacher_id.choices = _teacher_choices()
    if request.method == "GET":
        form.class_teacher_id.data = class_obj.class_teacher_id or 0

    if form.validate_on_submit():
        old_value = {"name": class_obj.name, "capacity": class_obj.capacity}
        class_obj.name = form.name.data.strip()
        class_obj.code = form.code.data.strip() if form.code.data else None
        class_obj.capacity = form.capacity.data
        class_obj.class_teacher_id = form.class_teacher_id.data or None
        log_action("class.edited", "classes", class_obj.id, old_value=old_value,
                   new_value={"name": class_obj.name, "capacity": class_obj.capacity})
        db.session.commit()
        flash(f"Class '{class_obj.name}' updated.", "success")
        return redirect(url_for("academic.class_list"))

    return render_template("academic/class_form.html", form=form, title="Edit Class", active_session=class_obj.session)


# ----------------------------------------------------------------- Sections --

@academic_bp.route("/classes/<int:class_id>/sections")
@login_required
@role_required(UserRole.ADMIN)
def section_list(class_id):
    class_obj = SchoolClass.query.filter_by(id=class_id, school_id=current_school_id()).first_or_404()
    return render_template("academic/section_list.html", school_class=class_obj)


@academic_bp.route("/classes/<int:class_id>/sections/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def section_new(class_id):
    class_obj = SchoolClass.query.filter_by(id=class_id, school_id=current_school_id()).first_or_404()
    form = SectionForm()
    form.class_teacher_id.choices = _teacher_choices()

    if form.validate_on_submit():
        section_obj = Section(
            class_id=class_obj.id,
            name=form.name.data.strip(),
            room=form.room.data.strip() if form.room.data else None,
            capacity=form.capacity.data,
            class_teacher_id=form.class_teacher_id.data or None,
        )
        db.session.add(section_obj)
        db.session.flush()
        log_action("section.created", "sections", section_obj.id, new_value={"name": section_obj.name})
        db.session.commit()
        flash(f"Section '{section_obj.name}' added to {class_obj.name}.", "success")
        return redirect(url_for("academic.section_list", class_id=class_obj.id))

    return render_template("academic/section_form.html", form=form, title="New Section", school_class=class_obj)


@academic_bp.route("/sections/<int:section_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def section_edit(section_id):
    section_obj = (
        Section.query.join(SchoolClass)
        .filter(Section.id == section_id, SchoolClass.school_id == current_school_id())
        .first_or_404()
    )
    form = SectionForm(obj=section_obj)
    form.class_teacher_id.choices = _teacher_choices()
    if request.method == "GET":
        form.class_teacher_id.data = section_obj.class_teacher_id or 0

    if form.validate_on_submit():
        old_value = {"name": section_obj.name}
        section_obj.name = form.name.data.strip()
        section_obj.room = form.room.data.strip() if form.room.data else None
        section_obj.capacity = form.capacity.data
        section_obj.class_teacher_id = form.class_teacher_id.data or None
        log_action("section.edited", "sections", section_obj.id, old_value=old_value,
                   new_value={"name": section_obj.name})
        db.session.commit()
        flash(f"Section '{section_obj.name}' updated.", "success")
        return redirect(url_for("academic.section_list", class_id=section_obj.class_id))

    return render_template("academic/section_form.html", form=form, title="Edit Section",
                          school_class=section_obj.school_class)


# ----------------------------------------------------------------- Subjects --

@academic_bp.route("/subjects")
@login_required
@role_required(UserRole.ADMIN)
def subject_list():
    class_id = request.args.get("class_id", type=int)
    school_id = current_school_id()

    query = Subject.query.filter_by(school_id=school_id)
    if class_id:
        query = query.filter_by(class_id=class_id)
    subjects = query.order_by(Subject.name).all()
    classes = SchoolClass.query.filter_by(school_id=school_id).order_by(SchoolClass.name).all()

    return render_template("academic/subject_list.html", subjects=subjects, classes=classes, selected_class_id=class_id)


@academic_bp.route("/subjects/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def subject_new():
    school_id = current_school_id()
    form = SubjectForm()
    form.class_id.choices = [(c.id, c.name) for c in SchoolClass.query.filter_by(school_id=school_id).order_by(SchoolClass.name)]
    form.teacher_id.choices = _teacher_choices()

    if not form.class_id.choices:
        flash("Create a class before adding subjects.", "warning")
        return redirect(url_for("academic.class_new"))

    if form.validate_on_submit():
        subject_obj = Subject(
            school_id=school_id,
            class_id=form.class_id.data,
            teacher_id=form.teacher_id.data or None,
            name=form.name.data.strip(),
            code=form.code.data.strip(),
            max_marks=form.max_marks.data,
            passing_marks=form.passing_marks.data,
            subject_type=SubjectType(form.subject_type.data),
        )
        db.session.add(subject_obj)
        db.session.flush()
        log_action("subject.created", "subjects", subject_obj.id, new_value={"name": subject_obj.name})
        db.session.commit()
        flash(f"Subject '{subject_obj.name}' created.", "success")
        return redirect(url_for("academic.subject_list"))

    return render_template("academic/subject_form.html", form=form, title="New Subject")


@academic_bp.route("/subjects/<int:subject_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def subject_edit(subject_id):
    subject_obj = Subject.query.filter_by(id=subject_id, school_id=current_school_id()).first_or_404()
    form = SubjectForm()
    form.class_id.choices = [(c.id, c.name) for c in SchoolClass.query.filter_by(school_id=current_school_id()).order_by(SchoolClass.name)]
    form.teacher_id.choices = _teacher_choices()
    if request.method == "GET":
        form.name.data = subject_obj.name
        form.code.data = subject_obj.code
        form.class_id.data = subject_obj.class_id
        form.teacher_id.data = subject_obj.teacher_id or 0
        form.max_marks.data = subject_obj.max_marks
        form.passing_marks.data = subject_obj.passing_marks
        form.subject_type.data = subject_obj.subject_type.value

    if form.validate_on_submit():
        old_value = {"name": subject_obj.name, "max_marks": subject_obj.max_marks, "passing_marks": subject_obj.passing_marks}
        subject_obj.class_id = form.class_id.data
        subject_obj.teacher_id = form.teacher_id.data or None
        subject_obj.name = form.name.data.strip()
        subject_obj.code = form.code.data.strip()
        subject_obj.max_marks = form.max_marks.data
        subject_obj.passing_marks = form.passing_marks.data
        subject_obj.subject_type = SubjectType(form.subject_type.data)
        log_action("subject.edited", "subjects", subject_obj.id, old_value=old_value,
                   new_value={"name": subject_obj.name, "max_marks": subject_obj.max_marks, "passing_marks": subject_obj.passing_marks})
        db.session.commit()
        flash(f"Subject '{subject_obj.name}' updated.", "success")
        return redirect(url_for("academic.subject_list"))

    return render_template("academic/subject_form.html", form=form, title="Edit Subject")


# ------------------------------------------------------------------ Periods --

@academic_bp.route("/periods")
@login_required
@role_required(UserRole.ADMIN)
def period_list():
    periods = Period.query.filter_by(school_id=current_school_id()).order_by(Period.order_index).all()
    return render_template("academic/period_list.html", periods=periods)


@academic_bp.route("/periods/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def period_new():
    school_id = current_school_id()
    form = PeriodForm()
    if request.method == "GET":
        max_order = db.session.query(db.func.max(Period.order_index)).filter_by(school_id=school_id).scalar()
        form.order_index.data = (max_order or 0) + 1

    if form.validate_on_submit():
        name = form.name.data.strip()
        if Period.query.filter_by(school_id=school_id, name=name).first():
            form.name.errors.append("A period with this name already exists.")
        elif Period.query.filter_by(school_id=school_id, order_index=form.order_index.data).first():
            form.order_index.errors.append("This order number is already used by another period.")
        else:
            period = Period(
                school_id=school_id, name=name, order_index=form.order_index.data,
                start_time=form.start_time.data, end_time=form.end_time.data, is_break=form.is_break.data,
            )
            db.session.add(period)
            db.session.flush()
            log_action("period.created", "periods", period.id, new_value={"name": period.name})
            db.session.commit()
            flash(f"Period '{period.name}' created.", "success")
            return redirect(url_for("academic.period_list"))

    return render_template("academic/period_form.html", form=form, title="New Period")


@academic_bp.route("/periods/<int:period_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def period_edit(period_id):
    school_id = current_school_id()
    period = Period.query.filter_by(id=period_id, school_id=school_id).first_or_404()
    form = PeriodForm()

    if request.method == "GET":
        form.name.data = period.name
        form.order_index.data = period.order_index
        form.start_time.data = period.start_time
        form.end_time.data = period.end_time
        form.is_break.data = period.is_break

    if form.validate_on_submit():
        name = form.name.data.strip()
        name_conflict = Period.query.filter(
            Period.school_id == school_id, Period.name == name, Period.id != period.id
        ).first()
        order_conflict = Period.query.filter(
            Period.school_id == school_id, Period.order_index == form.order_index.data, Period.id != period.id
        ).first()
        if name_conflict:
            form.name.errors.append("A period with this name already exists.")
        elif order_conflict:
            form.order_index.errors.append("This order number is already used by another period.")
        else:
            period.name = name
            period.order_index = form.order_index.data
            period.start_time = form.start_time.data
            period.end_time = form.end_time.data
            period.is_break = form.is_break.data
            log_action("period.edited", "periods", period.id, new_value={"name": period.name})
            db.session.commit()
            flash(f"Period '{period.name}' updated.", "success")
            return redirect(url_for("academic.period_list"))

    return render_template("academic/period_form.html", form=form, title="Edit Period")
