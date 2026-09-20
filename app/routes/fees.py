from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required

from app.extensions import db
from app.models import FeeType, StudentFee, Student, SchoolClass, Section, AcademicSession
from app.models.enums import UserRole, RecordStatus, StudentStatus
from app.forms.fee import FeeTypeForm, BulkAssignFeeForm
from app.utils.decorators import role_required
from app.utils.tenant import current_school_id
from app.services.audit_service import log_action
from app.services.fee_service import compute_defaulters

fees_bp = Blueprint("fees", __name__, url_prefix="/fees")


@fees_bp.route("/")
@login_required
@role_required(UserRole.ADMIN, UserRole.ACCOUNTANT, UserRole.RECEPTIONIST)
def index():
    return render_template("fees/index.html")


@fees_bp.route("/types")
@login_required
@role_required(UserRole.ADMIN, UserRole.ACCOUNTANT)
def fee_type_list():
    fee_types = FeeType.query.filter_by(school_id=current_school_id()).order_by(FeeType.name).all()
    return render_template("fees/type_list.html", fee_types=fee_types)


@fees_bp.route("/types/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def fee_type_new():
    school_id = current_school_id()
    form = FeeTypeForm()

    if form.validate_on_submit():
        name = form.name.data.strip()
        if FeeType.query.filter_by(school_id=school_id, name=name).first():
            form.name.errors.append("A fee type with this name already exists.")
        else:
            fee_type = FeeType(
                school_id=school_id, name=name, default_amount=form.default_amount.data,
                is_recurring=form.is_recurring.data,
            )
            db.session.add(fee_type)
            db.session.flush()
            log_action("fee_type.created", "fee_types", fee_type.id, new_value={"name": fee_type.name})
            db.session.commit()
            flash(f"Fee type '{fee_type.name}' created.", "success")
            return redirect(url_for("fees.fee_type_list"))

    return render_template("fees/type_form.html", form=form, title="New Fee Type")


@fees_bp.route("/types/<int:fee_type_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def fee_type_edit(fee_type_id):
    school_id = current_school_id()
    fee_type = FeeType.query.filter_by(id=fee_type_id, school_id=school_id).first_or_404()
    form = FeeTypeForm()

    if request.method == "GET":
        form.name.data = fee_type.name
        form.default_amount.data = fee_type.default_amount
        form.is_recurring.data = fee_type.is_recurring

    if form.validate_on_submit():
        name = form.name.data.strip()
        conflict = FeeType.query.filter(
            FeeType.school_id == school_id, FeeType.name == name, FeeType.id != fee_type.id
        ).first()
        if conflict:
            form.name.errors.append("A fee type with this name already exists.")
        else:
            fee_type.name = name
            fee_type.default_amount = form.default_amount.data
            fee_type.is_recurring = form.is_recurring.data
            log_action("fee_type.edited", "fee_types", fee_type.id, new_value={"name": fee_type.name})
            db.session.commit()
            flash(f"Fee type '{fee_type.name}' updated.", "success")
            return redirect(url_for("fees.fee_type_list"))

    return render_template("fees/type_form.html", form=form, title="Edit Fee Type")


@fees_bp.route("/types/<int:fee_type_id>/toggle-status", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN)
def fee_type_toggle_status(fee_type_id):
    fee_type = FeeType.query.filter_by(id=fee_type_id, school_id=current_school_id()).first_or_404()
    fee_type.status = RecordStatus.INACTIVE if fee_type.status == RecordStatus.ACTIVE else RecordStatus.ACTIVE
    log_action("fee_type.status_toggled", "fee_types", fee_type.id, new_value={"status": fee_type.status.value})
    db.session.commit()
    flash(f"'{fee_type.name}' is now {fee_type.status.value}.", "success")
    return redirect(url_for("fees.fee_type_list"))


@fees_bp.route("/assign-bulk", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN, UserRole.ACCOUNTANT)
def assign_bulk():
    school_id = current_school_id()
    active_session = AcademicSession.query.filter_by(school_id=school_id, is_active=True).first()
    if not active_session:
        flash("Activate an academic session before assigning fees.", "warning")
        return redirect(url_for("academic.session_list"))

    form = BulkAssignFeeForm()
    form.fee_type_id.choices = [
        (f.id, f.name) for f in FeeType.query.filter_by(school_id=school_id, status=RecordStatus.ACTIVE).order_by(FeeType.name)
    ]
    if not form.fee_type_id.choices:
        flash("Create a fee type before assigning fees.", "warning")
        return redirect(url_for("fees.fee_type_new"))

    classes = SchoolClass.query.filter_by(school_id=school_id, session_id=active_session.id).order_by(SchoolClass.name).all()
    form.class_id.choices = [(c.id, c.name) for c in classes]
    sections_by_class = {c.id: [[0, "All Sections"]] + [[s.id, s.name] for s in c.sections] for c in classes}

    if form.validate_on_submit():
        section_id = request.form.get("section_id", type=int) or 0
        query = Student.query.filter_by(school_id=school_id, current_class_id=form.class_id.data, status=StudentStatus.ACTIVE)
        if section_id:
            query = query.filter_by(current_section_id=section_id)
        students = query.all()

        created = 0
        skipped = 0
        for student in students:
            already_exists = StudentFee.query.filter_by(
                student_id=student.id, fee_type_id=form.fee_type_id.data,
                session_id=active_session.id, due_date=form.due_date.data,
            ).first()
            if already_exists:
                skipped += 1
                continue
            db.session.add(StudentFee(
                school_id=school_id, student_id=student.id, fee_type_id=form.fee_type_id.data,
                session_id=active_session.id, amount=form.amount.data, due_date=form.due_date.data,
                notes=form.notes.data or None,
            ))
            created += 1

        log_action("student_fee.bulk_assigned", "student_fees", None,
                   new_value={"fee_type_id": form.fee_type_id.data, "class_id": form.class_id.data, "count": created})
        db.session.commit()

        message = f"Fee assigned to {created} student(s)."
        if skipped:
            message += f" Skipped {skipped} who already had this exact fee for this due date."
        flash(message, "success")
        return redirect(url_for("fees.assign_bulk"))

    return render_template("fees/assign_bulk.html", form=form, sections_by_class=sections_by_class)


@fees_bp.route("/defaulters")
@login_required
@role_required(UserRole.ADMIN, UserRole.ACCOUNTANT, UserRole.RECEPTIONIST)
def defaulters():
    school_id = current_school_id()
    class_id = request.args.get("class_id", type=int)
    section_id = request.args.get("section_id", type=int)
    min_days_overdue = request.args.get("min_days_overdue", type=int)

    results = compute_defaulters(school_id, class_id=class_id, section_id=section_id)
    if min_days_overdue:
        results = [r for r in results if r["days_overdue"] >= min_days_overdue]

    classes = SchoolClass.query.filter_by(school_id=school_id).order_by(SchoolClass.name).all()
    sections_by_class = {c.id: [[s.id, s.name] for s in c.sections] for c in classes}

    return render_template(
        "fees/defaulters.html", results=results, classes=classes, sections_by_class=sections_by_class,
        class_id=class_id, section_id=section_id, min_days_overdue=min_days_overdue,
    )
