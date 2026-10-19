from datetime import date

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, Response
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User, Staff, SalaryRecord
from app.models.enums import UserRole, SalaryRecipientRole, SalaryPaymentStatus
from app.forms.salary import SalaryForm
from app.utils.decorators import role_required
from app.utils.tenant import current_school_id
from app.services.audit_service import log_action
from app.services.salary_service import compute_net_salary
from app.services.salary_slip_service import build_salary_slip_pdf

salaries_bp = Blueprint("salaries", __name__, url_prefix="/salaries")


@salaries_bp.route("/")
@login_required
@role_required(UserRole.ADMIN, UserRole.ACCOUNTANT)
def list_salaries():
    school_id = current_school_id()
    status = request.args.get("status", "")
    query = SalaryRecord.query.filter_by(school_id=school_id)
    if status:
        query = query.filter_by(payment_status=SalaryPaymentStatus(status))
    records = query.order_by(SalaryRecord.month.desc()).all()
    return render_template("salaries/list.html", records=records, status=status,
                           statuses=list(SalaryPaymentStatus), compute_net_salary=compute_net_salary)


@salaries_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN, UserRole.ACCOUNTANT)
def new_salary():
    school_id = current_school_id()
    teachers = User.query.filter_by(school_id=school_id, role=UserRole.TEACHER).order_by(User.name).all()
    staff_members = Staff.query.filter_by(school_id=school_id).order_by(Staff.name).all()

    form = SalaryForm()
    if form.validate_on_submit():
        try:
            recipient_role = SalaryRecipientRole(request.form.get("recipient_role"))
        except (ValueError, TypeError):
            flash("Choose who this salary is for.", "danger")
            return redirect(url_for("salaries.new_salary"))

        teacher_user_id = staff_id = None
        if recipient_role == SalaryRecipientRole.TEACHER:
            teacher_user_id = request.form.get("teacher_user_id", type=int)
        else:
            staff_id = request.form.get("staff_id", type=int)

        if not (teacher_user_id or staff_id):
            flash("Choose a specific person for this salary record.", "danger")
            return redirect(url_for("salaries.new_salary"))

        month_normalized = form.month.data.replace(day=1)
        existing = SalaryRecord.query.filter_by(school_id=school_id, month=month_normalized)
        existing = existing.filter_by(teacher_user_id=teacher_user_id) if teacher_user_id else existing.filter_by(staff_id=staff_id)
        if existing.first():
            flash("A salary record already exists for this person for this month.", "danger")
            return redirect(url_for("salaries.new_salary"))

        record = SalaryRecord(
            school_id=school_id, recipient_role=recipient_role, teacher_user_id=teacher_user_id, staff_id=staff_id,
            month=month_normalized, basic_salary=form.basic_salary.data, allowances=form.allowances.data or 0,
            deductions=form.deductions.data or 0, bonus=form.bonus.data or 0, notes=form.notes.data or None,
            generated_by_id=current_user.id,
        )
        db.session.add(record)
        db.session.flush()
        log_action("salary.generated", "salary_records", record.id,
                   new_value={"recipient_role": recipient_role.value, "month": month_normalized.isoformat()})
        db.session.commit()
        flash("Salary record generated.", "success")
        return redirect(url_for("salaries.view_salary", salary_id=record.id))

    return render_template("salaries/form.html", form=form, teachers=teachers, staff_members=staff_members)


@salaries_bp.route("/<int:salary_id>")
@login_required
@role_required(UserRole.ADMIN, UserRole.ACCOUNTANT, UserRole.TEACHER)
def view_salary(salary_id):
    record = SalaryRecord.query.filter_by(id=salary_id, school_id=current_school_id()).first_or_404()
    if current_user.role == UserRole.TEACHER and record.teacher_user_id != current_user.id:
        abort(403)
    return render_template("salaries/view.html", record=record, net_salary=compute_net_salary(record))


@salaries_bp.route("/<int:salary_id>/mark-paid", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN, UserRole.ACCOUNTANT)
def mark_paid(salary_id):
    record = SalaryRecord.query.filter_by(id=salary_id, school_id=current_school_id()).first_or_404()
    if record.payment_status == SalaryPaymentStatus.PAID:
        flash("This salary has already been marked paid.", "info")
        return redirect(url_for("salaries.view_salary", salary_id=record.id))
    record.payment_status = SalaryPaymentStatus.PAID
    record.payment_date = date.today()
    record.paid_by_id = current_user.id
    log_action("salary.paid", "salary_records", record.id, new_value={"payment_date": record.payment_date.isoformat()})
    db.session.commit()
    flash(f"Salary marked as paid for {record.recipient_name}.", "success")
    return redirect(url_for("salaries.view_salary", salary_id=record.id))


@salaries_bp.route("/<int:salary_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN, UserRole.ACCOUNTANT)
def edit_salary(salary_id):
    record = SalaryRecord.query.filter_by(id=salary_id, school_id=current_school_id()).first_or_404()
    if record.payment_status == SalaryPaymentStatus.PAID:
        flash("A paid salary record can't be edited.", "warning")
        return redirect(url_for("salaries.view_salary", salary_id=record.id))

    form = SalaryForm()
    if request.method == "GET":
        form.month.data = record.month
        form.basic_salary.data = record.basic_salary
        form.allowances.data = record.allowances
        form.deductions.data = record.deductions
        form.bonus.data = record.bonus
        form.notes.data = record.notes

    if form.validate_on_submit():
        record.month = form.month.data.replace(day=1)
        record.basic_salary = form.basic_salary.data
        record.allowances = form.allowances.data or 0
        record.deductions = form.deductions.data or 0
        record.bonus = form.bonus.data or 0
        record.notes = form.notes.data or None
        log_action("salary.edited", "salary_records", record.id, new_value={"basic_salary": str(record.basic_salary)})
        db.session.commit()
        flash("Salary record updated.", "success")
        return redirect(url_for("salaries.view_salary", salary_id=record.id))

    return render_template("salaries/edit_form.html", form=form, record=record)


@salaries_bp.route("/<int:salary_id>/slip/pdf")
@login_required
@role_required(UserRole.ADMIN, UserRole.ACCOUNTANT, UserRole.TEACHER)
def salary_slip_pdf(salary_id):
    record = SalaryRecord.query.filter_by(id=salary_id, school_id=current_school_id()).first_or_404()
    if current_user.role == UserRole.TEACHER and record.teacher_user_id != current_user.id:
        abort(403)
    pdf_bytes = build_salary_slip_pdf(record)
    filename = f"salary_slip_{record.recipient_name.replace(' ', '_')}_{record.month.strftime('%Y-%m')}.pdf"
    return Response(pdf_bytes, mimetype="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"})


@salaries_bp.route("/my")
@login_required
@role_required(UserRole.TEACHER)
def my_salaries():
    records = (SalaryRecord.query.filter_by(school_id=current_school_id(), teacher_user_id=current_user.id)
               .order_by(SalaryRecord.month.desc()).all())
    return render_template("salaries/my_list.html", records=records, compute_net_salary=compute_net_salary)
