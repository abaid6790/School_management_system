import os
from datetime import date

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory, Response
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Student, StudentEnrollment, AcademicSession, SchoolClass, Section, Guardian, StudentGuardian, StudentDocument, Exam, FeeType, StudentFee, FeePayment, FeeDiscount
from app.models.enums import UserRole, StudentStatus, EnrollmentStatus, Gender, GuardianRelation, DocumentType, RecordStatus, PaymentMethod, DiscountType
from app.forms.student import StudentForm
from app.forms.fee import AssignFeeForm, PaymentForm, DiscountForm
from app.utils.decorators import role_required
from app.utils.tenant import current_school_id
from app.services.audit_service import log_action
from app.services.student_service import suggest_admission_number, is_roll_number_taken
from app.services.fee_service import compute_fee_totals, generate_receipt_number
from app.services.receipt_service import build_receipt_pdf, build_fee_statement_pdf
from app.utils.uploads import save_upload, UploadError

students_bp = Blueprint("students", __name__, url_prefix="/students")

PER_PAGE = 20


def _class_section_choices(school_id):
    """Returns (class_choices, sections_by_class) for the school's classes in
    the active session — used to populate the form and the client-side JS map
    that filters the section dropdown when a class is picked."""
    active_session = AcademicSession.query.filter_by(school_id=school_id, is_active=True).first()
    if not active_session:
        return [], {}

    classes = SchoolClass.query.filter_by(school_id=school_id, session_id=active_session.id).order_by(SchoolClass.name).all()
    class_choices = [(c.id, c.name) for c in classes]
    sections_by_class = {c.id: [[s.id, s.name] for s in c.sections] for c in classes}
    return class_choices, sections_by_class


@students_bp.route("/")
@login_required
@role_required(UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.TEACHER)
def list_students():
    school_id = current_school_id()
    q = request.args.get("q", "").strip()
    class_id = request.args.get("class_id", type=int)
    section_id = request.args.get("section_id", type=int)
    status = request.args.get("status", "").strip()
    page = request.args.get("page", 1, type=int)

    query = Student.query.filter_by(school_id=school_id)

    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(Student.name.ilike(like), Student.admission_number.ilike(like), Student.phone.ilike(like))
        )
    if class_id:
        query = query.filter(Student.current_class_id == class_id)
    if section_id:
        query = query.filter(Student.current_section_id == section_id)
    if status:
        query = query.filter(Student.status == StudentStatus(status))

    pagination = query.order_by(Student.name).paginate(page=page, per_page=PER_PAGE, error_out=False)

    classes = SchoolClass.query.filter_by(school_id=school_id).order_by(SchoolClass.name).all()

    return render_template(
        "students/list.html", pagination=pagination, students=pagination.items, classes=classes,
        q=q, class_id=class_id, section_id=section_id, status=status, statuses=list(StudentStatus),
    )


@students_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN, UserRole.RECEPTIONIST)
def new_student():
    school_id = current_school_id()
    active_session = AcademicSession.query.filter_by(school_id=school_id, is_active=True).first()
    if not active_session:
        flash("Create and activate an academic session before admitting students.", "warning")
        return redirect(url_for("academic.session_list"))

    class_choices, sections_by_class = _class_section_choices(school_id)
    if not class_choices:
        flash("Create at least one class (with a section) before admitting students.", "warning")
        return redirect(url_for("academic.class_new"))

    form = StudentForm()
    form.class_id.choices = class_choices
    all_sections = [(sid, sname) for secs in sections_by_class.values() for sid, sname in secs]
    form.section_id.choices = all_sections or [(0, "— add a section first —")]

    if request.method == "GET":
        form.admission_number.data = suggest_admission_number(school_id)
        form.admission_date.data = date.today()

    if form.validate_on_submit():
        chosen_section = Section.query.filter_by(id=form.section_id.data, class_id=form.class_id.data).first()
        if not chosen_section:
            form.section_id.errors.append("That section doesn't belong to the selected class.")
        elif is_roll_number_taken(active_session.id, form.class_id.data, form.section_id.data, form.roll_number.data):
            form.roll_number.errors.append("This roll number is already used in that class/section.")
        else:
            student = Student(
                school_id=school_id,
                admission_number=form.admission_number.data.strip(),
                admission_date=form.admission_date.data,
                name=form.name.data.strip(),
                father_name=form.father_name.data.strip() if form.father_name.data else None,
                mother_name=form.mother_name.data.strip() if form.mother_name.data else None,
                date_of_birth=form.date_of_birth.data,
                gender=Gender(form.gender.data) if form.gender.data else None,
                cnic_or_bform=form.cnic_or_bform.data or None,
                blood_group=form.blood_group.data or None,
                phone=form.phone.data or None,
                email=form.email.data or None,
                address=form.address.data or None,
                city=form.city.data or None,
                previous_school=form.previous_school.data or None,
                medical_info=form.medical_info.data or None,
                notes=form.notes.data or None,
                current_session_id=active_session.id,
                current_class_id=form.class_id.data,
                current_section_id=form.section_id.data,
            )
            db.session.add(student)
            try:
                db.session.flush()
            except Exception:
                db.session.rollback()
                form.admission_number.errors.append("This admission number is already in use.")
                return render_template(
                    "students/form.html", form=form, title="Admit New Student",
                    sections_by_class=sections_by_class,
                )

            enrollment = StudentEnrollment(
                school_id=school_id, student_id=student.id, session_id=active_session.id,
                class_id=form.class_id.data, section_id=form.section_id.data,
                roll_number=form.roll_number.data.strip(), enrolled_on=form.admission_date.data,
            )
            db.session.add(enrollment)
            db.session.flush()

            log_action("student.created", "students", student.id,
                       new_value={"name": student.name, "admission_number": student.admission_number})
            db.session.commit()

            flash(f"{student.name} admitted successfully (Admission No. {student.admission_number}).", "success")
            return redirect(url_for("students.view_student", student_id=student.id))

    return render_template(
        "students/form.html", form=form, title="Admit New Student", sections_by_class=sections_by_class,
    )


from app.services.attendance_service import compute_attendance_stats
from app.services.result_service import compute_student_result


@students_bp.route("/<int:student_id>")
@login_required
@role_required(UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.TEACHER)
def view_student(student_id):
    student = Student.query.filter_by(id=student_id, school_id=current_school_id()).first_or_404()
    attendance_stats = compute_attendance_stats(student.id, session_id=student.current_session_id)
    return render_template(
        "students/profile.html", student=student, statuses=list(StudentStatus),
        doc_types=list(DocumentType), attendance_stats=attendance_stats,
    )


@students_bp.route("/<int:student_id>/results")
@login_required
@role_required(UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.TEACHER)
def student_results(student_id):
    student = Student.query.filter_by(id=student_id, school_id=current_school_id()).first_or_404()
    exams = Exam.query.filter_by(school_id=student.school_id, class_id=student.current_class_id).order_by(Exam.start_date.desc()).all()

    summaries = []
    for exam in exams:
        result = compute_student_result(exam, student.id)
        if result["has_any_marks"]:
            summaries.append({"exam": exam, **result})

    return render_template("students/results.html", student=student, summaries=summaries)


@students_bp.route("/<int:student_id>/fees")
@login_required
@role_required(UserRole.ADMIN, UserRole.ACCOUNTANT, UserRole.RECEPTIONIST)
def student_fees(student_id):
    student = Student.query.filter_by(id=student_id, school_id=current_school_id()).first_or_404()
    fees = StudentFee.query.filter_by(student_id=student.id).order_by(StudentFee.due_date.desc()).all()
    fee_rows = [{"fee": fee, "totals": compute_fee_totals(fee)} for fee in fees]
    return render_template("students/fees.html", student=student, fee_rows=fee_rows)


@students_bp.route("/<int:student_id>/fees/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN, UserRole.ACCOUNTANT, UserRole.RECEPTIONIST)
def add_student_fee(student_id):
    school_id = current_school_id()
    student = Student.query.filter_by(id=student_id, school_id=school_id).first_or_404()

    form = AssignFeeForm()
    fee_types = FeeType.query.filter_by(school_id=school_id, status=RecordStatus.ACTIVE).order_by(FeeType.name).all()
    form.fee_type_id.choices = [(f.id, f.name) for f in fee_types]
    if not form.fee_type_id.choices:
        flash("Create a fee type before assigning fees.", "warning")
        return redirect(url_for("fees.fee_type_new"))

    if form.validate_on_submit():
        fee = StudentFee(
            school_id=school_id, student_id=student.id, fee_type_id=form.fee_type_id.data,
            session_id=student.current_session_id, amount=form.amount.data, due_date=form.due_date.data,
            notes=form.notes.data or None,
        )
        db.session.add(fee)
        db.session.flush()
        log_action("student_fee.assigned", "student_fees", fee.id,
                   new_value={"fee_type_id": form.fee_type_id.data, "amount": str(form.amount.data)})
        db.session.commit()
        flash("Fee assigned.", "success")
        return redirect(url_for("students.student_fees", student_id=student.id))

    return render_template(
        "students/fee_form.html", form=form, student=student,
        fee_type_defaults={f.id: str(f.default_amount) if f.default_amount is not None else "" for f in fee_types},
    )


@students_bp.route("/<int:student_id>/fees/<int:fee_id>/pay", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN, UserRole.ACCOUNTANT, UserRole.RECEPTIONIST)
def pay_student_fee(student_id, fee_id):
    school_id = current_school_id()
    student = Student.query.filter_by(id=student_id, school_id=school_id).first_or_404()
    fee = StudentFee.query.filter_by(id=fee_id, student_id=student.id).first_or_404()
    totals = compute_fee_totals(fee)

    if totals["remaining"] <= 0:
        flash("This fee is already fully paid.", "info")
        return redirect(url_for("students.student_fees", student_id=student.id))

    form = PaymentForm()
    if request.method == "GET":
        form.amount.data = totals["remaining"]
        form.payment_date.data = date.today()

    if form.validate_on_submit():
        if form.amount.data > totals["remaining"]:
            form.amount.errors.append(f"Amount can't exceed the remaining balance of {totals['remaining']}.")
        else:
            receipt_number = generate_receipt_number(school_id)
            payment = FeePayment(
                school_id=school_id, student_fee_id=fee.id, receipt_number=receipt_number,
                amount=form.amount.data, payment_method=PaymentMethod(form.payment_method.data),
                payment_date=form.payment_date.data, notes=form.notes.data or None, received_by_id=current_user.id,
            )
            db.session.add(payment)
            db.session.flush()
            log_action("fee_payment.recorded", "fee_payments", payment.id,
                       new_value={"student_fee_id": fee.id, "amount": str(form.amount.data), "receipt_number": receipt_number})
            db.session.commit()
            flash(f"Payment recorded. Receipt {receipt_number}.", "success")
            return redirect(url_for("students.fee_receipt", student_id=student.id, fee_id=fee.id, payment_id=payment.id))

    return render_template("students/fee_pay.html", form=form, student=student, fee=fee, totals=totals)


@students_bp.route("/<int:student_id>/fees/<int:fee_id>/receipts/<int:payment_id>")
@login_required
@role_required(UserRole.ADMIN, UserRole.ACCOUNTANT, UserRole.RECEPTIONIST)
def fee_receipt(student_id, fee_id, payment_id):
    school_id = current_school_id()
    student = Student.query.filter_by(id=student_id, school_id=school_id).first_or_404()
    fee = StudentFee.query.filter_by(id=fee_id, student_id=student.id).first_or_404()
    payment = FeePayment.query.filter_by(id=payment_id, student_fee_id=fee.id).first_or_404()
    totals = compute_fee_totals(fee)
    return render_template("students/fee_receipt.html", student=student, fee=fee, payment=payment, totals=totals)


@students_bp.route("/<int:student_id>/fees/<int:fee_id>/receipts/<int:payment_id>/pdf")
@login_required
@role_required(UserRole.ADMIN, UserRole.ACCOUNTANT, UserRole.RECEPTIONIST)
def fee_receipt_pdf(student_id, fee_id, payment_id):
    school_id = current_school_id()
    student = Student.query.filter_by(id=student_id, school_id=school_id).first_or_404()
    fee = StudentFee.query.filter_by(id=fee_id, student_id=student.id).first_or_404()
    payment = FeePayment.query.filter_by(id=payment_id, student_fee_id=fee.id).first_or_404()

    pdf_bytes = build_receipt_pdf(payment)
    filename = f"receipt_{payment.receipt_number}.pdf"
    return Response(pdf_bytes, mimetype="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"})


@students_bp.route("/<int:student_id>/fees/<int:fee_id>/discounts/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN, UserRole.ACCOUNTANT)
def add_fee_discount(student_id, fee_id):
    school_id = current_school_id()
    student = Student.query.filter_by(id=student_id, school_id=school_id).first_or_404()
    fee = StudentFee.query.filter_by(id=fee_id, student_id=student.id).first_or_404()
    totals = compute_fee_totals(fee)

    form = DiscountForm()
    if form.validate_on_submit():
        discount_type = DiscountType(form.discount_type.data)
        if discount_type == DiscountType.PERCENTAGE:
            computed_amount = round(fee.amount * form.value.data / 100, 2)
        else:
            computed_amount = form.value.data

        max_allowable = fee.amount - totals["discount_total"]
        if computed_amount > max_allowable:
            form.value.errors.append(
                f"This discount would exceed the fee amount. Maximum allowable discount right now: {max_allowable}."
            )
        elif (totals["net_amount"] - computed_amount) < totals["paid_total"]:
            form.value.errors.append(
                f"This discount would reduce the net amount below what's already been paid "
                f"({totals['paid_total']}) — that would need a refund process instead."
            )
        else:
            discount = FeeDiscount(
                school_id=school_id, student_fee_id=fee.id, discount_type=discount_type,
                value=form.value.data, computed_amount=computed_amount, reason=form.reason.data.strip(),
                applied_by_id=current_user.id,
            )
            db.session.add(discount)
            db.session.flush()
            log_action("fee_discount.applied", "fee_discounts", discount.id,
                       new_value={"student_fee_id": fee.id, "type": discount_type.value, "amount": str(computed_amount)})
            db.session.commit()
            flash(f"Discount of {computed_amount} applied.", "success")
            return redirect(url_for("students.student_fees", student_id=student.id))

    return render_template("students/discount_form.html", form=form, student=student, fee=fee, totals=totals)


@students_bp.route("/<int:student_id>/fees/<int:fee_id>/discounts/<int:discount_id>/delete", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN, UserRole.ACCOUNTANT)
def delete_fee_discount(student_id, fee_id, discount_id):
    school_id = current_school_id()
    student = Student.query.filter_by(id=student_id, school_id=school_id).first_or_404()
    fee = StudentFee.query.filter_by(id=fee_id, student_id=student.id).first_or_404()
    discount = FeeDiscount.query.filter_by(id=discount_id, student_fee_id=fee.id).first_or_404()

    log_action("fee_discount.removed", "fee_discounts", discount.id,
               old_value={"type": discount.discount_type.value, "amount": str(discount.computed_amount), "reason": discount.reason})
    db.session.delete(discount)
    db.session.commit()
    flash("Discount removed.", "info")
    return redirect(url_for("students.student_fees", student_id=student.id))


@students_bp.route("/<int:student_id>/fees/statement")
@login_required
@role_required(UserRole.ADMIN, UserRole.ACCOUNTANT, UserRole.RECEPTIONIST)
def fee_statement(student_id):
    student = Student.query.filter_by(id=student_id, school_id=current_school_id()).first_or_404()
    fees = StudentFee.query.filter_by(student_id=student.id).order_by(StudentFee.due_date).all()
    fee_rows = [{"fee": fee, "totals": compute_fee_totals(fee)} for fee in fees]
    return render_template("students/fee_statement.html", student=student, fee_rows=fee_rows)


@students_bp.route("/<int:student_id>/fees/statement/pdf")
@login_required
@role_required(UserRole.ADMIN, UserRole.ACCOUNTANT, UserRole.RECEPTIONIST)
def fee_statement_pdf(student_id):
    student = Student.query.filter_by(id=student_id, school_id=current_school_id()).first_or_404()
    fees = StudentFee.query.filter_by(student_id=student.id).order_by(StudentFee.due_date).all()
    fee_rows = [{"fee": fee, "totals": compute_fee_totals(fee)} for fee in fees]

    pdf_bytes = build_fee_statement_pdf(student, fee_rows)
    filename = f"fee_statement_{student.admission_number}.pdf"
    return Response(pdf_bytes, mimetype="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"})


@students_bp.route("/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN, UserRole.RECEPTIONIST)
def edit_student(student_id):
    school_id = current_school_id()
    student = Student.query.filter_by(id=student_id, school_id=school_id).first_or_404()
    enrollment = student.current_enrollment

    class_choices, sections_by_class = _class_section_choices(school_id)
    all_sections = [(sid, sname) for secs in sections_by_class.values() for sid, sname in secs]

    form = StudentForm()
    form.class_id.choices = class_choices or [(student.current_class_id, student.current_class.name)]
    form.section_id.choices = all_sections or [(student.current_section_id, student.current_section.name)]

    if request.method == "GET":
        form.admission_number.data = student.admission_number
        form.admission_date.data = student.admission_date
        form.name.data = student.name
        form.father_name.data = student.father_name
        form.mother_name.data = student.mother_name
        form.date_of_birth.data = student.date_of_birth
        form.gender.data = student.gender.value if student.gender else ""
        form.cnic_or_bform.data = student.cnic_or_bform
        form.blood_group.data = student.blood_group or ""
        form.phone.data = student.phone
        form.email.data = student.email
        form.address.data = student.address
        form.city.data = student.city
        form.previous_school.data = student.previous_school
        form.medical_info.data = student.medical_info
        form.notes.data = student.notes
        form.class_id.data = student.current_class_id
        form.section_id.data = student.current_section_id
        form.roll_number.data = enrollment.roll_number if enrollment else ""

    if form.validate_on_submit():
        chosen_section = Section.query.filter_by(id=form.section_id.data, class_id=form.class_id.data).first()
        if not chosen_section:
            form.section_id.errors.append("That section doesn't belong to the selected class.")
        elif enrollment and is_roll_number_taken(
            enrollment.session_id, form.class_id.data, form.section_id.data, form.roll_number.data,
            exclude_enrollment_id=enrollment.id,
        ):
            form.roll_number.errors.append("This roll number is already used in that class/section.")
        else:
            old_value = {"name": student.name, "class_id": student.current_class_id, "section_id": student.current_section_id}

            student.admission_number = form.admission_number.data.strip()
            student.admission_date = form.admission_date.data
            student.name = form.name.data.strip()
            student.father_name = form.father_name.data.strip() if form.father_name.data else None
            student.mother_name = form.mother_name.data.strip() if form.mother_name.data else None
            student.date_of_birth = form.date_of_birth.data
            student.gender = Gender(form.gender.data) if form.gender.data else None
            student.cnic_or_bform = form.cnic_or_bform.data or None
            student.blood_group = form.blood_group.data or None
            student.phone = form.phone.data or None
            student.email = form.email.data or None
            student.address = form.address.data or None
            student.city = form.city.data or None
            student.previous_school = form.previous_school.data or None
            student.medical_info = form.medical_info.data or None
            student.notes = form.notes.data or None
            student.current_class_id = form.class_id.data
            student.current_section_id = form.section_id.data

            if enrollment:
                enrollment.class_id = form.class_id.data
                enrollment.section_id = form.section_id.data
                enrollment.roll_number = form.roll_number.data.strip()

            log_action("student.edited", "students", student.id, old_value=old_value,
                       new_value={"name": student.name, "class_id": student.current_class_id, "section_id": student.current_section_id})
            db.session.commit()

            flash(f"{student.name}'s record has been updated.", "success")
            return redirect(url_for("students.view_student", student_id=student.id))

    return render_template(
        "students/form.html", form=form, title=f"Edit {student.name}", sections_by_class=sections_by_class,
        student=student,
    )


@students_bp.route("/<int:student_id>/status", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN)
def change_status(student_id):
    student = Student.query.filter_by(id=student_id, school_id=current_school_id()).first_or_404()
    new_status_raw = request.form.get("status")
    reason = request.form.get("reason", "").strip()

    try:
        new_status = StudentStatus(new_status_raw)
    except ValueError:
        flash("Invalid status.", "danger")
        return redirect(url_for("students.view_student", student_id=student.id))

    old_status = student.status.value
    student.status = new_status
    if reason:
        note = f"[{date.today().isoformat()}] Status changed to {new_status.value}: {reason}"
        student.notes = f"{student.notes}\n{note}" if student.notes else note

    log_action("student.status_changed", "students", student.id,
               old_value={"status": old_status}, new_value={"status": new_status.value, "reason": reason or None})
    db.session.commit()

    flash(f"{student.name}'s status changed to {new_status.value.title()}.", "success")
    return redirect(url_for("students.view_student", student_id=student.id))


@students_bp.route("/<int:student_id>/guardians/add", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN, UserRole.RECEPTIONIST)
def add_guardian(student_id):
    school_id = current_school_id()
    student = Student.query.filter_by(id=student_id, school_id=school_id).first_or_404()

    search_q = request.args.get("q", "").strip()
    search_results = []
    if search_q:
        like = f"%{search_q}%"
        search_results = (
            Guardian.query.filter_by(school_id=school_id)
            .filter(db.or_(Guardian.phone.ilike(like), Guardian.father_name.ilike(like), Guardian.mother_name.ilike(like)))
            .limit(10).all()
        )

    if request.method == "POST":
        action = request.form.get("action")
        try:
            relationship = GuardianRelation(request.form.get("relationship_to_student"))
        except (ValueError, TypeError):
            flash("Please choose how this guardian is related to the student.", "danger")
            return redirect(url_for("students.add_guardian", student_id=student.id, q=search_q))

        is_primary = request.form.get("is_primary_contact") == "on"
        is_emergency = request.form.get("is_emergency_contact") == "on"

        if action == "link_existing":
            guardian_id = request.form.get("guardian_id", type=int)
            guardian = Guardian.query.filter_by(id=guardian_id, school_id=school_id).first()
            if not guardian:
                flash("Guardian not found.", "danger")
                return redirect(url_for("students.add_guardian", student_id=student.id))

            if StudentGuardian.query.filter_by(student_id=student.id, guardian_id=guardian.id).first():
                flash("This guardian is already linked to this student.", "warning")
                return redirect(url_for("students.view_student", student_id=student.id))

            link = StudentGuardian(
                student_id=student.id, guardian_id=guardian.id, relationship_to_student=relationship,
                is_primary_contact=is_primary, is_emergency_contact=is_emergency,
            )
            db.session.add(link)
            db.session.flush()
            log_action("student_guardian.linked", "student_guardians", link.id,
                       new_value={"student_id": student.id, "guardian_id": guardian.id})
            db.session.commit()
            flash(f"Linked {guardian.father_name or guardian.mother_name} to {student.name}.", "success")
            return redirect(url_for("students.view_student", student_id=student.id))

        elif action == "create_new":
            phone = request.form.get("phone", "").strip()
            father_name = request.form.get("father_name", "").strip()
            mother_name = request.form.get("mother_name", "").strip()
            if not phone:
                flash("Phone number is required to add a new guardian.", "danger")
                return redirect(url_for("students.add_guardian", student_id=student.id))
            if not father_name and not mother_name:
                flash("Provide at least a father's or mother's name.", "danger")
                return redirect(url_for("students.add_guardian", student_id=student.id))

            guardian = Guardian(
                school_id=school_id,
                father_name=father_name or None,
                mother_name=mother_name or None,
                phone=phone,
                alternate_phone=request.form.get("alternate_phone") or None,
                email=request.form.get("email") or None,
                occupation=request.form.get("occupation") or None,
                address=request.form.get("address") or None,
                emergency_contact_name=request.form.get("emergency_contact_name") or None,
                emergency_contact_phone=request.form.get("emergency_contact_phone") or None,
            )
            db.session.add(guardian)
            db.session.flush()

            link = StudentGuardian(
                student_id=student.id, guardian_id=guardian.id, relationship_to_student=relationship,
                is_primary_contact=is_primary, is_emergency_contact=is_emergency,
            )
            db.session.add(link)
            db.session.flush()

            log_action("guardian.created", "guardians", guardian.id, new_value={"phone": guardian.phone})
            log_action("student_guardian.linked", "student_guardians", link.id,
                       new_value={"student_id": student.id, "guardian_id": guardian.id})
            db.session.commit()
            flash(f"Added and linked a new guardian to {student.name}.", "success")
            return redirect(url_for("students.view_student", student_id=student.id))

    return render_template(
        "students/add_guardian.html", student=student, search_q=search_q,
        search_results=search_results, relations=list(GuardianRelation),
    )


@students_bp.route("/<int:student_id>/guardians/<int:link_id>/unlink", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN, UserRole.RECEPTIONIST)
def unlink_guardian(student_id, link_id):
    student = Student.query.filter_by(id=student_id, school_id=current_school_id()).first_or_404()
    link = StudentGuardian.query.filter_by(id=link_id, student_id=student.id).first_or_404()

    guardian_name = link.guardian.father_name or link.guardian.mother_name
    log_action("student_guardian.unlinked", "student_guardians", link.id,
               old_value={"student_id": student.id, "guardian_id": link.guardian_id})
    db.session.delete(link)
    db.session.commit()

    flash(f"Removed {guardian_name} from {student.name}'s guardians.", "info")
    return redirect(url_for("students.view_student", student_id=student.id))


@students_bp.route("/<int:student_id>/documents/upload", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN, UserRole.RECEPTIONIST)
def upload_document(student_id):
    student = Student.query.filter_by(id=student_id, school_id=current_school_id()).first_or_404()

    try:
        document_type = DocumentType(request.form.get("document_type"))
    except (ValueError, TypeError):
        flash("Please choose a document type.", "danger")
        return redirect(url_for("students.view_student", student_id=student.id))

    try:
        relative_path, original_filename = save_upload(
            request.files.get("file"),
            subfolder=f"students/{student.school_id}/{student.id}",
            allowed_extensions=current_app.config["ALLOWED_DOCUMENT_EXTENSIONS"],
        )
    except UploadError as e:
        flash(str(e), "danger")
        return redirect(url_for("students.view_student", student_id=student.id))

    doc = StudentDocument(
        school_id=student.school_id, student_id=student.id, document_type=document_type,
        file_path=relative_path, original_filename=original_filename, uploaded_by_id=current_user.id,
    )
    db.session.add(doc)
    db.session.flush()
    log_action("student_document.uploaded", "student_documents", doc.id,
               new_value={"document_type": document_type.value, "filename": original_filename})
    db.session.commit()

    flash(f"Uploaded {original_filename}.", "success")
    return redirect(url_for("students.view_student", student_id=student.id))


@students_bp.route("/<int:student_id>/documents/<int:doc_id>/download")
@login_required
@role_required(UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.TEACHER)
def download_document(student_id, doc_id):
    student = Student.query.filter_by(id=student_id, school_id=current_school_id()).first_or_404()
    doc = StudentDocument.query.filter_by(id=doc_id, student_id=student.id).first_or_404()

    directory, filename = os.path.split(doc.file_path)
    return send_from_directory(
        os.path.join(current_app.config["UPLOAD_FOLDER"], directory), filename,
        as_attachment=True, download_name=doc.original_filename,
    )


@students_bp.route("/<int:student_id>/documents/<int:doc_id>/delete", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN)
def delete_document(student_id, doc_id):
    student = Student.query.filter_by(id=student_id, school_id=current_school_id()).first_or_404()
    doc = StudentDocument.query.filter_by(id=doc_id, student_id=student.id).first_or_404()

    full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], doc.file_path)
    log_action("student_document.deleted", "student_documents", doc.id,
               old_value={"document_type": doc.document_type.value, "filename": doc.original_filename})
    db.session.delete(doc)
    db.session.commit()

    if os.path.exists(full_path):
        try:
            os.remove(full_path)
        except OSError:
            current_app.logger.warning("Could not remove uploaded file %s", full_path)

    flash("Document deleted.", "info")
    return redirect(url_for("students.view_student", student_id=student.id))
