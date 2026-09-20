"""
Attendance percentage convention, used everywhere attendance % is shown:

    percentage = (PRESENT + LATE) / (PRESENT + LATE + ABSENT) * 100

EXCUSED and LEAVE days are deliberately excluded from both sides of the
ratio — an excused absence shouldn't count against a student the way an
unexplained one does. LATE counts as attended (they were there, just late),
matching how the spec's own worked example treats attendance percentage.
"""
from sqlalchemy import func, case

from app.extensions import db
from app.models import StudentAttendance, TeacherAttendance
from app.models.enums import AttendanceStatus

COUNTED_STATUSES = (AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.ABSENT)
ATTENDED_STATUSES = (AttendanceStatus.PRESENT, AttendanceStatus.LATE)


def compute_teacher_attendance_stats(user_id: int, start_date=None, end_date=None) -> dict:
    """Same present+late-counted / excused-or-leave-excluded convention as
    compute_attendance_stats below, applied to a teacher's own record."""
    query = TeacherAttendance.query.filter_by(user_id=user_id)
    if start_date:
        query = query.filter(TeacherAttendance.date >= start_date)
    if end_date:
        query = query.filter(TeacherAttendance.date <= end_date)

    records = query.all()
    present = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
    late = sum(1 for r in records if r.status == AttendanceStatus.LATE)
    absent = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)
    leave = sum(1 for r in records if r.status == AttendanceStatus.LEAVE)
    denominator = present + late + absent
    percentage = round((present + late) / denominator * 100, 1) if denominator else None

    return {
        "present": present, "late": late, "absent": absent, "leave": leave,
        "denominator": denominator, "percentage": percentage,
    }


def compute_attendance_stats(student_id: int, session_id: int | None = None,
                              start_date=None, end_date=None) -> dict:
    query = StudentAttendance.query.filter_by(student_id=student_id)
    if session_id:
        query = query.filter_by(session_id=session_id)
    if start_date:
        query = query.filter(StudentAttendance.date >= start_date)
    if end_date:
        query = query.filter(StudentAttendance.date <= end_date)

    records = query.all()
    present = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
    late = sum(1 for r in records if r.status == AttendanceStatus.LATE)
    absent = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)
    excused = sum(1 for r in records if r.status == AttendanceStatus.EXCUSED)
    denominator = present + late + absent

    percentage = round((present + late) / denominator * 100, 1) if denominator else None

    return {
        "present": present, "late": late, "absent": absent, "excused": excused,
        "denominator": denominator, "percentage": percentage,
    }


def low_attendance_query(school_id: int, session_id: int, start_date, end_date, min_marked_days: int = 5):
    """A single grouped SQL query (not one query per student) for the
    low-attendance report — this needs to stay cheap even with thousands of
    students and years of attendance history."""
    attended_expr = func.sum(case((StudentAttendance.status.in_(ATTENDED_STATUSES), 1), else_=0))
    denominator_expr = func.sum(case((StudentAttendance.status.in_(COUNTED_STATUSES), 1), else_=0))

    rows = (
        db.session.query(
            StudentAttendance.student_id,
            attended_expr.label("attended"),
            denominator_expr.label("denominator"),
        )
        .filter(
            StudentAttendance.school_id == school_id,
            StudentAttendance.session_id == session_id,
            StudentAttendance.date >= start_date,
            StudentAttendance.date <= end_date,
        )
        .group_by(StudentAttendance.student_id)
        .having(denominator_expr >= min_marked_days)
        .all()
    )
    return [
        {"student_id": r.student_id, "attended": r.attended, "denominator": r.denominator,
         "percentage": round(r.attended / r.denominator * 100, 1)}
        for r in rows
    ]
