from datetime import date, datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import (
    Student, StudentAttendance, AcademicSession, SchoolClass, Section, SchoolSettings,
)
from app.models.enums import UserRole, AttendanceStatus, StudentStatus
from app.utils.decorators import role_required
from app.utils.tenant import current_school_id
from app.services.audit_service import log_action
from app.services.attendance_service import compute_attendance_stats, low_attendance_query
from app.services.student_service import roll_sort_key

attendance_bp = Blueprint("attendance", __name__, url_prefix="/attendance")


@attendance_bp.route("/")
@login_required
@role_required(UserRole.ADMIN, UserRole.TEACHER)
def index():
    return render_template("attendance/index.html")


@attendance_bp.route("/mark", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN, UserRole.TEACHER)
def mark():
    school_id = current_school_id()
    active_session = AcademicSession.query.filter_by(school_id=school_id, is_active=True).first()
    if not active_session:
        flash("No active academic session — activate one before marking attendance.", "warning")
        return redirect(url_for("academic.session_list"))

    classes = SchoolClass.query.filter_by(school_id=school_id, session_id=active_session.id).order_by(SchoolClass.name).all()
    sections_by_class = {c.id: [[s.id, s.name] for s in c.sections] for c in classes}

    class_id = request.values.get("class_id", type=int)
    section_id = request.values.get("section_id", type=int)
    date_str = request.values.get("date") or date.today().isoformat()
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        selected_date = date.today()

    students = []
    existing_by_student = {}
    if class_id and section_id:
        students = (
            Student.query.filter_by(
                school_id=school_id, current_class_id=class_id, current_section_id=section_id,
                status=StudentStatus.ACTIVE,
            ).all()
        )
        students.sort(key=roll_sort_key)

        existing = StudentAttendance.query.filter(
            StudentAttendance.date == selected_date,
            StudentAttendance.student_id.in_([s.id for s in students]),
        ).all()
        existing_by_student = {a.student_id: a for a in existing}

    if request.method == "POST":
        if not (class_id and section_id):
            flash("Choose a class and section first.", "danger")
            return redirect(url_for("attendance.mark"))

        counts = {s.value: 0 for s in AttendanceStatus}
        for student in students:
            raw_status = request.form.get(f"status_{student.id}")
            if not raw_status:
                continue
            try:
                status = AttendanceStatus(raw_status)
            except ValueError:
                continue

            record = existing_by_student.get(student.id)
            if record:
                record.status = status
                record.marked_by_id = current_user.id
            else:
                record = StudentAttendance(
                    school_id=school_id, student_id=student.id, session_id=active_session.id,
                    class_id=class_id, section_id=section_id, date=selected_date,
                    status=status, marked_by_id=current_user.id,
                )
                db.session.add(record)
            counts[status.value] += 1

        log_action(
            "attendance.marked", "student_attendance", None,
            new_value={"class_id": class_id, "section_id": section_id, "date": selected_date.isoformat(), "counts": counts},
        )
        db.session.commit()
        flash(f"Attendance saved for {selected_date.isoformat()} — {sum(counts.values())} students marked.", "success")
        return redirect(url_for("attendance.mark", class_id=class_id, section_id=section_id, date=selected_date.isoformat()))

    return render_template(
        "attendance/mark.html", classes=classes, sections_by_class=sections_by_class,
        class_id=class_id, section_id=section_id,
        selected_date=selected_date, students=students, existing_by_student=existing_by_student,
        statuses=list(AttendanceStatus),
    )


@attendance_bp.route("/reports/daily")
@login_required
@role_required(UserRole.ADMIN, UserRole.TEACHER)
def daily_report():
    school_id = current_school_id()
    date_str = request.args.get("date") or date.today().isoformat()
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        selected_date = date.today()

    class_id = request.args.get("class_id", type=int)

    query = StudentAttendance.query.filter_by(school_id=school_id, date=selected_date)
    if class_id:
        query = query.filter_by(class_id=class_id)
    records = query.join(Student).order_by(Student.name).all()

    counts = {s.value: 0 for s in AttendanceStatus}
    for r in records:
        counts[r.status.value] += 1

    classes = SchoolClass.query.filter_by(school_id=school_id).order_by(SchoolClass.name).all()

    return render_template(
        "attendance/daily_report.html", selected_date=selected_date, records=records,
        counts=counts, classes=classes, class_id=class_id,
    )


@attendance_bp.route("/reports/low-attendance")
@login_required
@role_required(UserRole.ADMIN, UserRole.TEACHER)
def low_attendance_report():
    school_id = current_school_id()
    active_session = AcademicSession.query.filter_by(school_id=school_id, is_active=True).first()
    if not active_session:
        flash("No active academic session.", "warning")
        return redirect(url_for("attendance.index"))

    settings = SchoolSettings.query.filter_by(school_id=school_id).first()
    threshold = settings.minimum_attendance_percentage if settings else 75.0

    start_str = request.args.get("start_date") or active_session.start_date.isoformat()
    end_str = request.args.get("end_date") or date.today().isoformat()
    start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_str, "%Y-%m-%d").date()

    rows = low_attendance_query(school_id, active_session.id, start_date, end_date)
    below_threshold = [r for r in rows if r["percentage"] < threshold]

    student_ids = [r["student_id"] for r in below_threshold]
    students_by_id = {s.id: s for s in Student.query.filter(Student.id.in_(student_ids)).all()} if student_ids else {}

    results = []
    for r in below_threshold:
        student = students_by_id.get(r["student_id"])
        if student:
            results.append({**r, "student": student})
    results.sort(key=lambda r: r["percentage"])

    return render_template(
        "attendance/low_attendance.html", results=results, threshold=threshold,
        start_date=start_date, end_date=end_date,
    )
