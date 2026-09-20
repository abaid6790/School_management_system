from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User, TeacherProfile, Subject, SchoolClass, Section
from app.models.enums import UserRole, Gender, EmploymentStatus
from app.forms.teacher import TeacherForm, TeacherStatusForm
from app.utils.decorators import role_required
from app.utils.tenant import current_school_id
from app.services.audit_service import log_action
from app.services.account_service import create_staff_account
from app.services.email_service import send_account_setup_email

teachers_bp = Blueprint("teachers", __name__, url_prefix="/teachers")

PER_PAGE = 20


@teachers_bp.route("/")
@login_required
@role_required(UserRole.ADMIN)
def list_teachers():
    school_id = current_school_id()
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    page = request.args.get("page", 1, type=int)

    query = (
        TeacherProfile.query.join(User)
        .filter(TeacherProfile.school_id == school_id)
    )
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(User.name.ilike(like), TeacherProfile.employee_id.ilike(like)))
    if status:
        query = query.filter(TeacherProfile.employment_status == EmploymentStatus(status))

    pagination = query.order_by(User.name).paginate(page=page, per_page=PER_PAGE, error_out=False)
    return render_template(
        "teachers/list.html", pagination=pagination, profiles=pagination.items,
        q=q, status=status, statuses=list(EmploymentStatus),
    )


@teachers_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def new_teacher():
    school_id = current_school_id()
    form = TeacherForm()

    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        employee_id = form.employee_id.data.strip()

        if User.query.filter_by(email=email).first():
            form.email.errors.append("An account with this email already exists.")
        elif TeacherProfile.query.filter_by(school_id=school_id, employee_id=employee_id).first():
            form.employee_id.errors.append("This employee ID is already in use.")
        else:
            user, token = create_staff_account(school_id, form.name.data.strip(), email, UserRole.TEACHER, form.phone.data or None)

            profile = TeacherProfile(
                school_id=school_id,
                user_id=user.id,
                employee_id=employee_id,
                father_or_spouse_name=form.father_or_spouse_name.data or None,
                date_of_birth=form.date_of_birth.data,
                gender=Gender(form.gender.data) if form.gender.data else None,
                address=form.address.data or None,
                qualification=form.qualification.data or None,
                specialization=form.specialization.data or None,
                joining_date=form.joining_date.data,
                salary=form.salary.data,
            )
            db.session.add(profile)
            db.session.flush()

            log_action("teacher.created", "users", user.id, new_value={"name": user.name, "employee_id": employee_id})
            db.session.commit()

            if send_account_setup_email(user, token):
                flash(f"{user.name} added. An email was sent for them to set their password.", "success")
            else:
                flash(
                    f"{user.name} added, but the setup email couldn't be sent right now. "
                    f"They can use 'Forgot password' on the login page once email delivery is working.",
                    "warning",
                )
            return redirect(url_for("teachers.view_teacher", user_id=user.id))

    return render_template("teachers/form.html", form=form, title="Add Teacher")


@teachers_bp.route("/<int:user_id>")
@login_required
@role_required(UserRole.ADMIN, UserRole.TEACHER)
def view_teacher(user_id):
    school_id = current_school_id()
    if current_user.role == UserRole.TEACHER and current_user.id != user_id:
        # Teachers may view their own profile only, not each other's.
        from flask import abort
        abort(403)

    user = User.query.filter_by(id=user_id, school_id=school_id, role=UserRole.TEACHER).first_or_404()
    profile = TeacherProfile.query.filter_by(user_id=user.id).first_or_404()

    subjects = Subject.query.filter_by(school_id=school_id, teacher_id=user.id).order_by(Subject.name).all()
    homeroom_classes = SchoolClass.query.filter_by(school_id=school_id, class_teacher_id=user.id).all()
    homeroom_sections = (
        Section.query.join(SchoolClass).filter(SchoolClass.school_id == school_id, Section.class_teacher_id == user.id).all()
    )

    return render_template(
        "teachers/profile.html", teacher=user, profile=profile, subjects=subjects,
        homeroom_classes=homeroom_classes, homeroom_sections=homeroom_sections,
        status_form=TeacherStatusForm(employment_status=profile.employment_status.value),
    )


@teachers_bp.route("/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def edit_teacher(user_id):
    school_id = current_school_id()
    user = User.query.filter_by(id=user_id, school_id=school_id, role=UserRole.TEACHER).first_or_404()
    profile = TeacherProfile.query.filter_by(user_id=user.id).first_or_404()

    form = TeacherForm()
    if request.method == "GET":
        form.name.data = user.name
        form.email.data = user.email
        form.phone.data = user.phone
        form.employee_id.data = profile.employee_id
        form.father_or_spouse_name.data = profile.father_or_spouse_name
        form.date_of_birth.data = profile.date_of_birth
        form.gender.data = profile.gender.value if profile.gender else ""
        form.address.data = profile.address
        form.qualification.data = profile.qualification
        form.specialization.data = profile.specialization
        form.joining_date.data = profile.joining_date
        form.salary.data = profile.salary

    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        employee_id = form.employee_id.data.strip()

        email_taken = User.query.filter(User.email == email, User.id != user.id).first()
        employee_id_taken = TeacherProfile.query.filter(
            TeacherProfile.school_id == school_id, TeacherProfile.employee_id == employee_id,
            TeacherProfile.user_id != user.id,
        ).first()

        if email_taken:
            form.email.errors.append("An account with this email already exists.")
        elif employee_id_taken:
            form.employee_id.errors.append("This employee ID is already in use.")
        else:
            old_value = {"name": user.name, "employee_id": profile.employee_id}
            user.name = form.name.data.strip()
            user.email = email
            user.phone = form.phone.data or None

            profile.employee_id = employee_id
            profile.father_or_spouse_name = form.father_or_spouse_name.data or None
            profile.date_of_birth = form.date_of_birth.data
            profile.gender = Gender(form.gender.data) if form.gender.data else None
            profile.address = form.address.data or None
            profile.qualification = form.qualification.data or None
            profile.specialization = form.specialization.data or None
            profile.joining_date = form.joining_date.data
            profile.salary = form.salary.data

            log_action("teacher.edited", "users", user.id, old_value=old_value,
                       new_value={"name": user.name, "employee_id": profile.employee_id})
            db.session.commit()
            flash(f"{user.name}'s record has been updated.", "success")
            return redirect(url_for("teachers.view_teacher", user_id=user.id))

    return render_template("teachers/form.html", form=form, title=f"Edit {user.name}", teacher=user)


@teachers_bp.route("/<int:user_id>/status", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN)
def change_status(user_id):
    school_id = current_school_id()
    user = User.query.filter_by(id=user_id, school_id=school_id, role=UserRole.TEACHER).first_or_404()
    profile = TeacherProfile.query.filter_by(user_id=user.id).first_or_404()

    form = TeacherStatusForm()
    if form.validate_on_submit():
        old_status = profile.employment_status.value
        profile.employment_status = EmploymentStatus(form.employment_status.data)
        # An inactive employment status also blocks login — mirrors the real-world
        # expectation that a resigned/terminated teacher can't still sign in.
        user.is_active_account = profile.employment_status == EmploymentStatus.ACTIVE

        log_action("teacher.status_changed", "users", user.id,
                   old_value={"employment_status": old_status},
                   new_value={"employment_status": profile.employment_status.value})
        db.session.commit()
        flash(f"{user.name}'s employment status changed to {profile.employment_status.value.replace('_', ' ').title()}.", "success")
    else:
        flash("Invalid status.", "danger")

    return redirect(url_for("teachers.view_teacher", user_id=user.id))
