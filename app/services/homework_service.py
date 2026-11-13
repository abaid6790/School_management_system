"""
Homework helpers. Progress (how many students handed in) is always derived from the
submission rows and the class roster — never stored — and a student who is no longer
active or no longer in the class simply stops counting.

A homework's "target" is every ACTIVE student currently in its class (and in its
section, when one is set). Students have no logins, so submission status is recorded
by the teacher; no row for a student means "not recorded yet".
"""
from datetime import date

from sqlalchemy import func, or_

from app.extensions import db
from app.models import Homework, HomeworkSubmission, Student
from app.models.enums import StudentStatus, SubmissionStatus, UserRole, HomeworkStatus
from app.services.student_service import roll_sort_key

DONE = (SubmissionStatus.SUBMITTED, SubmissionStatus.LATE)


def target_query(school_id, class_id, section_id=None):
    query = Student.query.filter_by(school_id=school_id, current_class_id=class_id, status=StudentStatus.ACTIVE)
    if section_id:
        query = query.filter_by(current_section_id=section_id)
    return query


def target_students(homework):
    students = target_query(homework.school_id, homework.class_id, homework.section_id).all()
    students.sort(key=roll_sort_key)
    return students


def summarize(total, counts):
    """counts: {SubmissionStatus: n} for students currently in the target group."""
    submitted = counts.get(SubmissionStatus.SUBMITTED, 0)
    late = counts.get(SubmissionStatus.LATE, 0)
    missing = counts.get(SubmissionStatus.MISSING, 0)
    excused = counts.get(SubmissionStatus.EXCUSED, 0)
    recorded = submitted + late + missing + excused
    expected = max(total - excused, 0)          # excused students aren't expected to hand in
    done = submitted + late
    return {
        "total": total, "submitted": submitted, "late": late, "missing": missing, "excused": excused,
        "not_recorded": max(total - recorded, 0), "done": done, "expected": expected,
        "percent": round(100 * done / expected) if expected else None,
    }


def progress_for(school_id, homeworks):
    """{homework_id: summary} for a page of homework, using two small grouped queries."""
    if not homeworks:
        return {}
    ids = [h.id for h in homeworks]
    rows = (
        db.session.query(HomeworkSubmission.homework_id, HomeworkSubmission.status, func.count(HomeworkSubmission.id))
        .join(Homework, Homework.id == HomeworkSubmission.homework_id)
        .join(Student, Student.id == HomeworkSubmission.student_id)
        .filter(
            HomeworkSubmission.homework_id.in_(ids),
            Student.status == StudentStatus.ACTIVE,
            Student.current_class_id == Homework.class_id,
            or_(Homework.section_id.is_(None), Student.current_section_id == Homework.section_id),
        )
        .group_by(HomeworkSubmission.homework_id, HomeworkSubmission.status)
        .all()
    )
    counts = {}
    for homework_id, status, n in rows:
        counts.setdefault(homework_id, {})[status] = n
    totals = {}
    result = {}
    for h in homeworks:
        key = (h.class_id, h.section_id)
        if key not in totals:
            totals[key] = target_query(school_id, h.class_id, h.section_id).count()
        result[h.id] = summarize(totals[key], counts.get(h.id, {}))
    return result


def due_state(homework, today=None):
    """(label, bootstrap colour) — derived from the due date, never stored."""
    today = today or date.today()
    if homework.status == HomeworkStatus.CANCELLED:
        return "Cancelled", "secondary"
    days = (homework.due_date - today).days
    if days < 0:
        return "Past due", "secondary"
    if days == 0:
        return "Due today", "warning"
    return (f"Due in {days} day{'s' if days != 1 else ''}", "info")


def can_manage(user, homework) -> bool:
    return user.role == UserRole.ADMIN or (user.role == UserRole.TEACHER and homework.teacher_id == user.id)
