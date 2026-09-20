from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required

from app.extensions import db
from app.models import User, Staff
from app.models.enums import UserRole, EmploymentStatus
from app.forms.staff import StaffForm
from app.forms.teacher import TeacherStatusForm
from app.utils.decorators import role_required
from app.utils.tenant import current_school_id
from app.services.audit_service import log_action
from app.services.account_service import create_staff_account
from app.services.email_service import send_account_setup_email

staff_bp = Blueprint("staff", __name__, url_prefix="/staff")

PER_PAGE = 20
ROLE_BY_NAME = {"accountant": UserRole.ACCOUNTANT, "receptionist": UserRole.RECEPTIONIST}


@staff_bp.route("/")
@login_required
@role_required(UserRole.ADMIN)
def list_staff():
    school_id = current_school_id()
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    page = request.args.get("page", 1, type=int)

    query = Staff.query.filter_by(school_id=school_id)
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(Staff.name.ilike(like), Staff.employee_id.ilike(like), Staff.position.ilike(like)))
    if status:
        query = query.filter(Staff.employment_status == EmploymentStatus(status))

    pagination = query.order_by(Staff.name).paginate(page=page, per_page=PER_PAGE, error_out=False)
    return render_template("staff/list.html", pagination=pagination, staff_members=pagination.items,
                          q=q, status=status, statuses=list(EmploymentStatus))


@staff_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def new_staff():
    school_id = current_school_id()
    form = StaffForm()

    if form.validate_on_submit():
        employee_id = form.employee_id.data.strip()
        if form.needs_login.data and not form.email.data:
            form.email.errors.append("Email is required to create a login for this staff member.")
        elif Staff.query.filter_by(school_id=school_id, employee_id=employee_id).first():
            form.employee_id.errors.append("This employee ID is already in use.")
        elif form.needs_login.data and User.query.filter_by(email=form.email.data.lower().strip()).first():
            form.email.errors.append("An account with this email already exists.")
        else:
            user = None
            if form.needs_login.data:
                role = ROLE_BY_NAME[form.system_role.data]
                user, token = create_staff_account(
                    school_id, form.name.data.strip(), form.email.data.lower().strip(), role, form.phone.data or None
                )

            staff_member = Staff(
                school_id=school_id,
                user_id=user.id if user else None,
                employee_id=employee_id,
                name=form.name.data.strip(),
                position=form.position.data.strip(),
                department=form.department.data or None,
                phone=form.phone.data or None,
                address=form.address.data or None,
                joining_date=form.joining_date.data,
                salary=form.salary.data,
            )
            db.session.add(staff_member)
            db.session.flush()

            log_action("staff.created", "staff", staff_member.id,
                       new_value={"name": staff_member.name, "position": staff_member.position})
            db.session.commit()

            if user:
                if send_account_setup_email(user, token):
                    flash(f"{staff_member.name} added. An email was sent for them to set their password.", "success")
                else:
                    flash(f"{staff_member.name} added, but the setup email couldn't be sent right now.", "warning")
            else:
                flash(f"{staff_member.name} added.", "success")

            return redirect(url_for("staff.view_staff", staff_id=staff_member.id))

    return render_template("staff/form.html", form=form, title="Add Staff Member")


@staff_bp.route("/<int:staff_id>")
@login_required
@role_required(UserRole.ADMIN)
def view_staff(staff_id):
    staff_member = Staff.query.filter_by(id=staff_id, school_id=current_school_id()).first_or_404()
    return render_template(
        "staff/profile.html", staff_member=staff_member,
        status_form=TeacherStatusForm(employment_status=staff_member.employment_status.value),
    )


@staff_bp.route("/<int:staff_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def edit_staff(staff_id):
    school_id = current_school_id()
    staff_member = Staff.query.filter_by(id=staff_id, school_id=school_id).first_or_404()

    form = StaffForm()
    if request.method == "GET":
        form.name.data = staff_member.name
        form.employee_id.data = staff_member.employee_id
        form.position.data = staff_member.position
        form.department.data = staff_member.department
        form.phone.data = staff_member.phone
        form.address.data = staff_member.address
        form.joining_date.data = staff_member.joining_date
        form.salary.data = staff_member.salary
        form.needs_login.data = staff_member.user_id is not None
        if staff_member.user:
            form.email.data = staff_member.user.email

    if form.validate_on_submit():
        employee_id = form.employee_id.data.strip()
        conflict = Staff.query.filter(
            Staff.school_id == school_id, Staff.employee_id == employee_id, Staff.id != staff_member.id
        ).first()
        if conflict:
            form.employee_id.errors.append("This employee ID is already in use.")
        else:
            old_value = {"name": staff_member.name, "position": staff_member.position}
            staff_member.name = form.name.data.strip()
            staff_member.employee_id = employee_id
            staff_member.position = form.position.data.strip()
            staff_member.department = form.department.data or None
            staff_member.phone = form.phone.data or None
            staff_member.address = form.address.data or None
            staff_member.joining_date = form.joining_date.data
            staff_member.salary = form.salary.data

            # Editing does NOT create or remove a login retroactively — that's a
            # bigger decision (deactivating/creating an account) than a plain
            # edit form should make implicitly. Existing linked accounts keep
            # their name/phone in sync since Staff.name is the source of truth
            # for display, but User.email/role changes aren't handled here.
            if staff_member.user:
                staff_member.user.name = staff_member.name
                staff_member.user.phone = staff_member.phone

            log_action("staff.edited", "staff", staff_member.id, old_value=old_value,
                       new_value={"name": staff_member.name, "position": staff_member.position})
            db.session.commit()
            flash(f"{staff_member.name}'s record has been updated.", "success")
            return redirect(url_for("staff.view_staff", staff_id=staff_member.id))

    return render_template("staff/form.html", form=form, title=f"Edit {staff_member.name}", staff_member=staff_member)


@staff_bp.route("/<int:staff_id>/status", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN)
def change_status(staff_id):
    staff_member = Staff.query.filter_by(id=staff_id, school_id=current_school_id()).first_or_404()
    form = TeacherStatusForm()

    if form.validate_on_submit():
        old_status = staff_member.employment_status.value
        staff_member.employment_status = EmploymentStatus(form.employment_status.data)
        if staff_member.user:
            staff_member.user.is_active_account = staff_member.employment_status == EmploymentStatus.ACTIVE

        log_action("staff.status_changed", "staff", staff_member.id,
                   old_value={"employment_status": old_status},
                   new_value={"employment_status": staff_member.employment_status.value})
        db.session.commit()
        flash(f"{staff_member.name}'s status changed to {staff_member.employment_status.value.replace('_', ' ').title()}.", "success")
    else:
        flash("Invalid status.", "danger")

    return redirect(url_for("staff.view_staff", staff_id=staff_member.id))
