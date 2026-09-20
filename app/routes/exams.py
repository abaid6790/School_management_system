from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, Response
from flask_login import login_required, current_user

from app.extensions import db
from app.models import AcademicSession, SchoolClass, Subject, Exam, ExamSubject, Mark, Student, GradeBand, ReportCardRemark
from app.models.enums import UserRole, ExamStatus, StudentStatus
from app.forms.exam import ExamForm, ExamSubjectForm, GradeBandForm
from app.utils.decorators import role_required
from app.utils.tenant import current_school_id
from app.services.audit_service import log_action
from app.services.student_service import roll_sort_key
from app.services.grading_service import find_overlapping_band
from app.services.result_service import compute_student_result, compute_class_ranking
from app.services.report_card_service import build_report_card_pdf

exams_bp = Blueprint("exams", __name__, url_prefix="/exams")


@exams_bp.route("/")
@login_required
@role_required(UserRole.ADMIN, UserRole.TEACHER)
def list_exams():
    school_id = current_school_id()
    class_id = request.args.get("class_id", type=int)

    query = Exam.query.filter_by(school_id=school_id)
    if class_id:
        query = query.filter_by(class_id=class_id)
    exam_list = query.order_by(Exam.start_date.desc()).all()

    classes = SchoolClass.query.filter_by(school_id=school_id).order_by(SchoolClass.name).all()
    return render_template("exams/list.html", exams=exam_list, classes=classes, class_id=class_id)


@exams_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def new_exam():
    school_id = current_school_id()
    active_session = AcademicSession.query.filter_by(school_id=school_id, is_active=True).first()
    if not active_session:
        flash("Activate an academic session before creating exams.", "warning")
        return redirect(url_for("academic.session_list"))

    form = ExamForm()
    form.class_id.choices = [
        (c.id, c.name) for c in SchoolClass.query.filter_by(school_id=school_id, session_id=active_session.id).order_by(SchoolClass.name)
    ]
    if not form.class_id.choices:
        flash("Create a class before scheduling exams.", "warning")
        return redirect(url_for("academic.class_new"))

    if form.validate_on_submit():
        name = form.name.data.strip()
        if Exam.query.filter_by(school_id=school_id, session_id=active_session.id, class_id=form.class_id.data, name=name).first():
            form.name.errors.append("An exam with this name already exists for that class this session.")
        else:
            exam = Exam(
                school_id=school_id, session_id=active_session.id, class_id=form.class_id.data,
                name=name, exam_type=form.exam_type.data, start_date=form.start_date.data,
                end_date=form.end_date.data, description=form.description.data or None,
            )
            db.session.add(exam)
            db.session.flush()
            log_action("exam.created", "exams", exam.id, new_value={"name": exam.name})
            db.session.commit()
            flash(f"Exam '{exam.name}' created.", "success")
            return redirect(url_for("exams.view_exam", exam_id=exam.id))

    return render_template("exams/form.html", form=form, title="New Exam")


@exams_bp.route("/<int:exam_id>")
@login_required
@role_required(UserRole.ADMIN, UserRole.TEACHER)
def view_exam(exam_id):
    exam = Exam.query.filter_by(id=exam_id, school_id=current_school_id()).first_or_404()
    return render_template("exams/view.html", exam=exam, statuses=list(ExamStatus))


@exams_bp.route("/<int:exam_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def edit_exam(exam_id):
    school_id = current_school_id()
    exam = Exam.query.filter_by(id=exam_id, school_id=school_id).first_or_404()

    form = ExamForm()
    form.class_id.choices = [(exam.class_id, exam.school_class.name)]  # class isn't changeable after creation
    form.class_id.render_kw = {"disabled": True}

    if request.method == "GET":
        form.name.data = exam.name
        form.exam_type.data = exam.exam_type.value
        form.class_id.data = exam.class_id
        form.start_date.data = exam.start_date
        form.end_date.data = exam.end_date
        form.description.data = exam.description

    if form.validate_on_submit():
        name = form.name.data.strip()
        conflict = Exam.query.filter(
            Exam.school_id == school_id, Exam.session_id == exam.session_id, Exam.class_id == exam.class_id,
            Exam.name == name, Exam.id != exam.id,
        ).first()
        if conflict:
            form.name.errors.append("An exam with this name already exists for that class this session.")
        else:
            exam.name = name
            exam.exam_type = form.exam_type.data
            exam.start_date = form.start_date.data
            exam.end_date = form.end_date.data
            exam.description = form.description.data or None
            log_action("exam.edited", "exams", exam.id, new_value={"name": exam.name})
            db.session.commit()
            flash(f"Exam '{exam.name}' updated.", "success")
            return redirect(url_for("exams.view_exam", exam_id=exam.id))

    return render_template("exams/form.html", form=form, title=f"Edit {exam.name}", exam=exam)


@exams_bp.route("/<int:exam_id>/status", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN)
def change_status(exam_id):
    exam = Exam.query.filter_by(id=exam_id, school_id=current_school_id()).first_or_404()
    try:
        new_status = ExamStatus(request.form.get("status"))
    except ValueError:
        flash("Invalid status.", "danger")
        return redirect(url_for("exams.view_exam", exam_id=exam.id))

    old_status = exam.status.value
    exam.status = new_status
    log_action("exam.status_changed", "exams", exam.id, old_value={"status": old_status}, new_value={"status": new_status.value})
    db.session.commit()
    flash(f"Exam status changed to {new_status.value.title()}.", "success")
    return redirect(url_for("exams.view_exam", exam_id=exam.id))


# ------------------------------------------------------------- Exam Subjects --

@exams_bp.route("/<int:exam_id>/subjects/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def new_exam_subject(exam_id):
    school_id = current_school_id()
    exam = Exam.query.filter_by(id=exam_id, school_id=school_id).first_or_404()

    already_added = {es.subject_id for es in exam.exam_subjects}
    available_subjects = [s for s in Subject.query.filter_by(school_id=school_id, class_id=exam.class_id).order_by(Subject.name) if s.id not in already_added]

    form = ExamSubjectForm()
    form.subject_id.choices = [(s.id, s.name) for s in available_subjects]
    if not form.subject_id.choices:
        flash("All of this class's subjects are already added to this exam.", "info")
        return redirect(url_for("exams.view_exam", exam_id=exam.id))

    if request.method == "GET":
        # Pre-fill from the subject's own defaults once one is chosen client-side isn't
        # wired here (kept simple) — default to the first subject's max/passing marks.
        first_subject = available_subjects[0]
        form.max_marks.data = first_subject.max_marks
        form.passing_marks.data = first_subject.passing_marks

    if form.validate_on_submit():
        exam_subject = ExamSubject(
            school_id=school_id, exam_id=exam.id, subject_id=form.subject_id.data,
            max_marks=form.max_marks.data, passing_marks=form.passing_marks.data,
            exam_date=form.exam_date.data, start_time=form.start_time.data,
            end_time=form.end_time.data, room=form.room.data or None,
        )
        db.session.add(exam_subject)
        db.session.flush()
        log_action("exam_subject.created", "exam_subjects", exam_subject.id,
                   new_value={"exam_id": exam.id, "subject_id": form.subject_id.data})
        db.session.commit()
        flash("Subject added to exam.", "success")
        return redirect(url_for("exams.view_exam", exam_id=exam.id))

    return render_template("exams/subject_form.html", form=form, exam=exam, title="Add Subject to Exam")


@exams_bp.route("/<int:exam_id>/subjects/<int:exam_subject_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def edit_exam_subject(exam_id, exam_subject_id):
    school_id = current_school_id()
    exam = Exam.query.filter_by(id=exam_id, school_id=school_id).first_or_404()
    exam_subject = ExamSubject.query.filter_by(id=exam_subject_id, exam_id=exam.id).first_or_404()

    form = ExamSubjectForm()
    form.subject_id.choices = [(exam_subject.subject_id, exam_subject.subject.name)]
    form.subject_id.render_kw = {"disabled": True}

    if request.method == "GET":
        form.subject_id.data = exam_subject.subject_id
        form.max_marks.data = exam_subject.max_marks
        form.passing_marks.data = exam_subject.passing_marks
        form.exam_date.data = exam_subject.exam_date
        form.start_time.data = exam_subject.start_time
        form.end_time.data = exam_subject.end_time
        form.room.data = exam_subject.room

    has_marks = Mark.query.filter_by(exam_subject_id=exam_subject.id).count() > 0

    if form.validate_on_submit():
        if has_marks and form.max_marks.data != exam_subject.max_marks:
            existing_max = Mark.query.filter_by(exam_subject_id=exam_subject.id).with_entities(
                db.func.max(Mark.obtained_marks)
            ).scalar()
            if existing_max is not None and float(existing_max) > form.max_marks.data:
                form.max_marks.errors.append(
                    f"Can't lower maximum marks below {existing_max} — a recorded mark already exceeds that."
                )
                return render_template("exams/subject_form.html", form=form, exam=exam, title="Edit Exam Subject", has_marks=has_marks)

        exam_subject.max_marks = form.max_marks.data
        exam_subject.passing_marks = form.passing_marks.data
        exam_subject.exam_date = form.exam_date.data
        exam_subject.start_time = form.start_time.data
        exam_subject.end_time = form.end_time.data
        exam_subject.room = form.room.data or None
        log_action("exam_subject.edited", "exam_subjects", exam_subject.id,
                   new_value={"max_marks": exam_subject.max_marks, "passing_marks": exam_subject.passing_marks})
        db.session.commit()
        flash("Exam subject updated.", "success")
        return redirect(url_for("exams.view_exam", exam_id=exam.id))

    return render_template("exams/subject_form.html", form=form, exam=exam, title="Edit Exam Subject", has_marks=has_marks)


@exams_bp.route("/<int:exam_id>/subjects/<int:exam_subject_id>/delete", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN)
def delete_exam_subject(exam_id, exam_subject_id):
    school_id = current_school_id()
    exam = Exam.query.filter_by(id=exam_id, school_id=school_id).first_or_404()
    exam_subject = ExamSubject.query.filter_by(id=exam_subject_id, exam_id=exam.id).first_or_404()

    if Mark.query.filter_by(exam_subject_id=exam_subject.id).count() > 0:
        flash("Can't remove this subject — marks have already been recorded for it.", "danger")
        return redirect(url_for("exams.view_exam", exam_id=exam.id))

    log_action("exam_subject.deleted", "exam_subjects", exam_subject.id, old_value={"subject_id": exam_subject.subject_id})
    db.session.delete(exam_subject)
    db.session.commit()
    flash("Subject removed from exam.", "info")
    return redirect(url_for("exams.view_exam", exam_id=exam.id))


# --------------------------------------------------------------- Marks Entry --

@exams_bp.route("/<int:exam_id>/subjects/<int:exam_subject_id>/marks", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN, UserRole.TEACHER)
def enter_marks(exam_id, exam_subject_id):
    school_id = current_school_id()
    exam = Exam.query.filter_by(id=exam_id, school_id=school_id).first_or_404()
    exam_subject = ExamSubject.query.filter_by(id=exam_subject_id, exam_id=exam.id).first_or_404()

    # Only the subject's own assigned teacher (or an Admin) can enter its marks —
    # not just any teacher in the school.
    if current_user.role == UserRole.TEACHER and exam_subject.subject.teacher_id != current_user.id:
        abort(403)

    students = Student.query.filter_by(school_id=school_id, current_class_id=exam.class_id, status=StudentStatus.ACTIVE).all()
    students.sort(key=roll_sort_key)

    existing_marks = {m.student_id: m for m in Mark.query.filter_by(exam_subject_id=exam_subject.id).all()}

    if request.method == "POST":
        errors = []
        to_save = {}
        for student in students:
            raw = request.form.get(f"marks_{student.id}", "").strip()
            if raw == "":
                continue
            try:
                value = float(raw)
            except ValueError:
                errors.append(f"{student.name}: '{raw}' is not a valid number.")
                continue
            if value < 0 or value > exam_subject.max_marks:
                errors.append(f"{student.name}: marks must be between 0 and {exam_subject.max_marks}.")
                continue
            to_save[student.id] = value

        if errors:
            for e in errors[:10]:
                flash(e, "danger")
            if len(errors) > 10:
                flash(f"...and {len(errors) - 10} more error(s).", "danger")
        else:
            for student_id, value in to_save.items():
                record = existing_marks.get(student_id)
                if record:
                    record.obtained_marks = value
                    record.entered_by_id = current_user.id
                else:
                    db.session.add(Mark(
                        school_id=school_id, exam_subject_id=exam_subject.id, student_id=student_id,
                        obtained_marks=value, entered_by_id=current_user.id,
                    ))
            log_action("marks.entered", "marks", None,
                       new_value={"exam_subject_id": exam_subject.id, "count": len(to_save)})
            db.session.commit()
            flash(f"Marks saved for {len(to_save)} student(s).", "success")
            return redirect(url_for("exams.enter_marks", exam_id=exam.id, exam_subject_id=exam_subject.id))

    return render_template(
        "exams/marks_entry.html", exam=exam, exam_subject=exam_subject,
        students=students, existing_marks=existing_marks,
    )


# --------------------------------------------------------------- Grade Bands --

@exams_bp.route("/grade-bands")
@login_required
@role_required(UserRole.ADMIN)
def grade_band_list():
    bands = GradeBand.query.filter_by(school_id=current_school_id()).order_by(GradeBand.order_index).all()
    return render_template("exams/grade_band_list.html", bands=bands)


@exams_bp.route("/grade-bands/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def grade_band_new():
    school_id = current_school_id()
    form = GradeBandForm()
    if request.method == "GET":
        max_order = db.session.query(db.func.max(GradeBand.order_index)).filter_by(school_id=school_id).scalar()
        form.order_index.data = (max_order or 0) + 1

    if form.validate_on_submit():
        overlap = find_overlapping_band(school_id, form.min_percentage.data, form.max_percentage.data)
        if overlap:
            form.min_percentage.errors.append(
                f"Overlaps with existing band {overlap.grade} ({overlap.min_percentage}-{overlap.max_percentage})."
            )
        else:
            band = GradeBand(
                school_id=school_id, grade=form.grade.data.strip(), min_percentage=form.min_percentage.data,
                max_percentage=form.max_percentage.data, order_index=form.order_index.data,
            )
            db.session.add(band)
            db.session.flush()
            log_action("grade_band.created", "grade_bands", band.id, new_value={"grade": band.grade})
            db.session.commit()
            flash(f"Grade band '{band.grade}' created.", "success")
            return redirect(url_for("exams.grade_band_list"))

    return render_template("exams/grade_band_form.html", form=form, title="New Grade Band")


@exams_bp.route("/grade-bands/<int:band_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def grade_band_edit(band_id):
    school_id = current_school_id()
    band = GradeBand.query.filter_by(id=band_id, school_id=school_id).first_or_404()
    form = GradeBandForm()

    if request.method == "GET":
        form.grade.data = band.grade
        form.min_percentage.data = band.min_percentage
        form.max_percentage.data = band.max_percentage
        form.order_index.data = band.order_index

    if form.validate_on_submit():
        overlap = find_overlapping_band(school_id, form.min_percentage.data, form.max_percentage.data, exclude_id=band.id)
        if overlap:
            form.min_percentage.errors.append(
                f"Overlaps with existing band {overlap.grade} ({overlap.min_percentage}-{overlap.max_percentage})."
            )
        else:
            band.grade = form.grade.data.strip()
            band.min_percentage = form.min_percentage.data
            band.max_percentage = form.max_percentage.data
            band.order_index = form.order_index.data
            log_action("grade_band.edited", "grade_bands", band.id, new_value={"grade": band.grade})
            db.session.commit()
            flash(f"Grade band '{band.grade}' updated.", "success")
            return redirect(url_for("exams.grade_band_list"))

    return render_template("exams/grade_band_form.html", form=form, title="Edit Grade Band")


@exams_bp.route("/grade-bands/<int:band_id>/delete", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN)
def grade_band_delete(band_id):
    band = GradeBand.query.filter_by(id=band_id, school_id=current_school_id()).first_or_404()
    log_action("grade_band.deleted", "grade_bands", band.id, old_value={"grade": band.grade})
    db.session.delete(band)
    db.session.commit()
    flash("Grade band deleted.", "info")
    return redirect(url_for("exams.grade_band_list"))


# ------------------------------------------------------------------ Results --

@exams_bp.route("/<int:exam_id>/results")
@login_required
@role_required(UserRole.ADMIN, UserRole.TEACHER)
def exam_results(exam_id):
    exam = Exam.query.filter_by(id=exam_id, school_id=current_school_id()).first_or_404()
    ranking = compute_class_ranking(exam)
    return render_template("exams/results.html", exam=exam, ranking=ranking)


@exams_bp.route("/<int:exam_id>/results/<int:student_id>")
@login_required
@role_required(UserRole.ADMIN, UserRole.TEACHER)
def student_result(exam_id, student_id):
    school_id = current_school_id()
    exam = Exam.query.filter_by(id=exam_id, school_id=school_id).first_or_404()
    student = Student.query.filter_by(id=student_id, school_id=school_id).first_or_404()
    result = compute_student_result(exam, student.id)
    return render_template("exams/student_result.html", exam=exam, student=student, result=result)


# --------------------------------------------------------------- Report Card --

@exams_bp.route("/<int:exam_id>/report-card/<int:student_id>")
@login_required
@role_required(UserRole.ADMIN, UserRole.TEACHER)
def report_card(exam_id, student_id):
    school_id = current_school_id()
    exam = Exam.query.filter_by(id=exam_id, school_id=school_id).first_or_404()
    student = Student.query.filter_by(id=student_id, school_id=school_id).first_or_404()
    result = compute_student_result(exam, student.id)
    ranking = compute_class_ranking(exam)
    rank_entry = next((r for r in ranking if r["student"].id == student.id), None)
    remark = ReportCardRemark.query.filter_by(exam_id=exam.id, student_id=student.id).first()

    return render_template(
        "exams/report_card.html", exam=exam, student=student, result=result,
        rank_entry=rank_entry, total_in_class=len(ranking), remark=remark,
    )


@exams_bp.route("/<int:exam_id>/report-card/<int:student_id>/remarks", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN, UserRole.TEACHER)
def save_remarks(exam_id, student_id):
    school_id = current_school_id()
    exam = Exam.query.filter_by(id=exam_id, school_id=school_id).first_or_404()
    student = Student.query.filter_by(id=student_id, school_id=school_id).first_or_404()

    remark = ReportCardRemark.query.filter_by(exam_id=exam.id, student_id=student.id).first()
    teacher_remarks = request.form.get("teacher_remarks", "").strip() or None
    principal_remarks = request.form.get("principal_remarks", "").strip() or None

    if remark:
        remark.teacher_remarks = teacher_remarks
        remark.principal_remarks = principal_remarks
    else:
        remark = ReportCardRemark(
            school_id=school_id, exam_id=exam.id, student_id=student.id,
            teacher_remarks=teacher_remarks, principal_remarks=principal_remarks,
        )
        db.session.add(remark)

    log_action("report_card_remark.saved", "report_card_remarks", remark.id if remark.id else None,
               new_value={"exam_id": exam.id, "student_id": student.id})
    db.session.commit()
    flash("Remarks saved.", "success")
    return redirect(url_for("exams.report_card", exam_id=exam.id, student_id=student.id))


@exams_bp.route("/<int:exam_id>/report-card/<int:student_id>/pdf")
@login_required
@role_required(UserRole.ADMIN, UserRole.TEACHER)
def report_card_pdf(exam_id, student_id):
    school_id = current_school_id()
    exam = Exam.query.filter_by(id=exam_id, school_id=school_id).first_or_404()
    student = Student.query.filter_by(id=student_id, school_id=school_id).first_or_404()
    remark = ReportCardRemark.query.filter_by(exam_id=exam.id, student_id=student.id).first()

    pdf_bytes = build_report_card_pdf(exam, student, remark=remark)
    log_action("report_card.downloaded", "students", student.id, new_value={"exam_id": exam.id})
    db.session.commit()

    filename = f"report_card_{student.admission_number}_{exam.name.replace(' ', '_')}.pdf"
    return Response(
        pdf_bytes, mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
