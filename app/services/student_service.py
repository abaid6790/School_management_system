"""
Small helpers shared by the student create/edit routes. Kept out of the route
functions so the uniqueness check (used by both create and edit) can't drift
out of sync between the two.
"""
from datetime import date
from app.models import Student, StudentEnrollment


def roll_sort_key(student):
    roll = student.current_roll_number
    if roll and roll.isdigit():
        return (0, int(roll))
    return (1, roll or student.name)


def suggest_admission_number(school_id: int) -> str:
    """A starting suggestion only — the admin can change it, and the real
    uniqueness guarantee is the DB constraint on (school_id, admission_number),
    not this count (which two concurrent admissions could theoretically race)."""
    year = date.today().year
    count = Student.query.filter_by(school_id=school_id).count()
    return f"ADM-{year}-{count + 1:04d}"


def is_roll_number_taken(session_id: int, class_id: int, section_id: int, roll_number: str,
                          exclude_enrollment_id: int | None = None) -> bool:
    query = StudentEnrollment.query.filter_by(
        session_id=session_id, class_id=class_id, section_id=section_id, roll_number=roll_number.strip()
    )
    if exclude_enrollment_id:
        query = query.filter(StudentEnrollment.id != exclude_enrollment_id)
    return db_first_exists(query)


def db_first_exists(query) -> bool:
    return query.first() is not None
