import calendar
from datetime import date, datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User, TeacherAttendance
from app.models.enums import UserRole, AttendanceStatus
from app.utils.decorators import role_required
from app.utils.tenant import current_school_id
from app.services.audit_service import log_action
from app.services.attendance_service import compute_teacher_attendance_stats

teacher_attendance_bp = Blueprint("teacher_attendance", __name__, url_prefix="/teacher-attendance")


@teacher_attendance_bp.route("/mark", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def mark():
    school_id = current_school_id()
    date_str = request.values.get("date") or date.today().isoformat()
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        selected_date = date.today()

    teachers = User.query.filter_by(school_id=school_id, role=UserRole.TEACHER).order_by(User.name).all()
    existing = TeacherAttendance.query.filter(
        TeacherAttendance.date == selected_date, TeacherAttendance.user_id.in_([t.id for t in teachers])
    ).all()
    existing_by_user = {a.user_id: a for a in existing}

    if request.method == "POST":
        counts = {s.value: 0 for s in AttendanceStatus}
        for teacher in teachers:
            raw_status = request.form.get(f"status_{teacher.id}")
            if not raw_status:
                continue
            try:
                status = AttendanceStatus(raw_status)
            except ValueError:
                continue

            record = existing_by_user.get(teacher.id)
            if record:
                record.status = status
                record.marked_by_id = current_user.id
            else:
                record = TeacherAttendance(
                    school_id=school_id, user_id=teacher.id, date=selected_date,
                    status=status, marked_by_id=current_user.id,
                )
                db.session.add(record)
            counts[status.value] += 1

        log_action("teacher_attendance.marked", "teacher_attendance", None,
                   new_value={"date": selected_date.isoformat(), "counts": counts})
        db.session.commit()
        flash(f"Teacher attendance saved for {selected_date.isoformat()}.", "success")
        return redirect(url_for("teacher_attendance.mark", date=selected_date.isoformat()))

    return render_template(
        "teacher_attendance/mark.html", teachers=teachers, selected_date=selected_date,
        existing_by_user=existing_by_user, statuses=list(AttendanceStatus),
    )


@teacher_attendance_bp.route("/reports/daily")
@login_required
@role_required(UserRole.ADMIN)
def daily_report():
    school_id = current_school_id()
    date_str = request.args.get("date") or date.today().isoformat()
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        selected_date = date.today()

    records = (
        TeacherAttendance.query.filter_by(school_id=school_id, date=selected_date)
        .join(User, TeacherAttendance.user_id == User.id).order_by(User.name).all()
    )
    counts = {s.value: 0 for s in AttendanceStatus}
    for r in records:
        counts[r.status.value] += 1

    return render_template("teacher_attendance/daily_report.html", selected_date=selected_date, records=records, counts=counts)


@teacher_attendance_bp.route("/history/<int:user_id>")
@login_required
@role_required(UserRole.ADMIN, UserRole.TEACHER)
def history(user_id):
    school_id = current_school_id()
    if current_user.role == UserRole.TEACHER and current_user.id != user_id:
        abort(403)

    teacher = User.query.filter_by(id=user_id, school_id=school_id, role=UserRole.TEACHER).first_or_404()

    month_str = request.args.get("month") or date.today().strftime("%Y-%m")
    try:
        year, month = (int(x) for x in month_str.split("-"))
    except ValueError:
        year, month = date.today().year, date.today().month

    days_in_month = calendar.monthrange(year, month)[1]
    month_start = date(year, month, 1)
    month_end = date(year, month, days_in_month)

    records = TeacherAttendance.query.filter(
        TeacherAttendance.user_id == user_id,
        TeacherAttendance.date >= month_start, TeacherAttendance.date <= month_end,
    ).all()
    by_day = {r.date.day: r for r in records}

    stats = compute_teacher_attendance_stats(user_id, start_date=month_start, end_date=month_end)

    return render_template(
        "teacher_attendance/history.html", teacher=teacher, year=year, month=month,
        days_in_month=days_in_month, by_day=by_day, stats=stats, month_str=month_str,
    )
