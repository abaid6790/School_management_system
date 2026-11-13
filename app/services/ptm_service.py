"""
Parent-teacher meeting helpers. A meeting day is divided into equal slots; the slot grid
is DERIVED from (start, end, slot length) — never stored — and a booking is just
(teacher, student, slot start). Double-booking is checked here with friendly messages and
backed by partial unique indexes in the database (cancelled appointments don't hold a slot).

Parents have no logins: staff book appointments on their behalf.
"""
from datetime import datetime, timedelta

from sqlalchemy.orm import joinedload

from app.models import PTMAppointment, Student, StudentGuardian
from app.models.enums import AppointmentStatus, StudentStatus, UserRole, GuardianRelation

ACTIVE_STATUSES = (AppointmentStatus.SCHEDULED, AppointmentStatus.COMPLETED, AppointmentStatus.NO_SHOW)
STATUS_COLORS = {
    AppointmentStatus.SCHEDULED: "primary", AppointmentStatus.COMPLETED: "success",
    AppointmentStatus.CANCELLED: "secondary", AppointmentStatus.NO_SHOW: "danger",
}


def slot_times(date_value, start_time, end_time, minutes):
    """Start times of every whole slot that fits in [start_time, end_time]."""
    cursor = datetime.combine(date_value, start_time)
    end = datetime.combine(date_value, end_time)
    step = timedelta(minutes=minutes)
    slots = []
    while cursor + step <= end:
        slots.append(cursor.time())
        cursor += step
    return slots


def slots_for(meeting):
    return slot_times(meeting.meeting_date, meeting.start_time, meeting.end_time, meeting.slot_minutes)


def slot_label(meeting, slot) -> str:
    end = (datetime.combine(meeting.meeting_date, slot) + timedelta(minutes=meeting.slot_minutes)).time()
    return f"{slot.strftime('%H:%M')}–{end.strftime('%H:%M')}"


def guardian_label(guardian, relation=None) -> str:
    if guardian is None:
        return "—"
    if relation == GuardianRelation.FATHER and guardian.father_name:
        name = guardian.father_name
    elif relation == GuardianRelation.MOTHER and guardian.mother_name:
        name = guardian.mother_name
    else:
        name = guardian.father_name or guardian.mother_name or "Guardian"
    return f"{name} ({relation.value})" if relation else name


def scope_label(meeting) -> str:
    if meeting.school_class is None:
        return "All classes"
    label = meeting.school_class.name
    return f"{label} – {meeting.section.name}" if meeting.section is not None else label


def students_in_scope(school_id, meeting):
    query = (Student.query.filter_by(school_id=school_id, status=StudentStatus.ACTIVE)
             .options(joinedload(Student.current_class), joinedload(Student.current_section)))
    if meeting.class_id:
        query = query.filter(Student.current_class_id == meeting.class_id)
    if meeting.section_id:
        query = query.filter(Student.current_section_id == meeting.section_id)
    students = query.all()
    students.sort(key=lambda s: ((s.current_class.name if s.current_class else ""),
                                 (s.current_section.name if s.current_section else ""), s.name.lower()))
    return students


def guardians_by_student(student_ids):
    """{student_id: [[guardian_id, label], ...]} from the guardian links."""
    if not student_ids:
        return {}
    links = (StudentGuardian.query.filter(StudentGuardian.student_id.in_(student_ids))
             .options(joinedload(StudentGuardian.guardian)).all())
    result = {}
    for link in sorted(links, key=lambda l: (not l.is_primary_contact, l.id)):
        result.setdefault(link.student_id, []).append(
            [link.guardian_id, guardian_label(link.guardian, link.relationship_to_student)])
    return result


def active_appointments(meeting_id):
    return PTMAppointment.query.filter(PTMAppointment.meeting_id == meeting_id,
                                       PTMAppointment.status.in_(ACTIVE_STATUSES))


def find_conflicts(meeting, teacher, student, slot):
    """Human-readable reasons this booking can't happen (empty list = free)."""
    when = slot_label(meeting, slot)
    reasons = []
    active = active_appointments(meeting.id)
    clash = active.filter_by(teacher_id=teacher.id, slot_start=slot).first()
    if clash:
        reasons.append(f"{teacher.name} is already booked at {when} (with {clash.student.name}).")
    clash = active.filter_by(student_id=student.id, slot_start=slot).first()
    if clash:
        reasons.append(f"{student.name}'s family already has an appointment at {when} (with {clash.teacher.name}).")
    pair = active.filter_by(teacher_id=teacher.id, student_id=student.id).first()
    if pair and pair.slot_start != slot:
        reasons.append(f"{student.name} already has an appointment with {teacher.name} in this meeting "
                       f"({slot_label(meeting, pair.slot_start)}).")
    return reasons


# ---- who may do what -------------------------------------------------------
def can_book_for(user, teacher_id) -> bool:
    if user.role in (UserRole.ADMIN, UserRole.RECEPTIONIST):
        return True
    return user.role == UserRole.TEACHER and teacher_id == user.id


def can_cancel(user, appointment) -> bool:
    return can_book_for(user, appointment.teacher_id)


def can_record_outcome(user, appointment) -> bool:
    """Outcome (completed / no-show / notes) is for the teacher concerned and the Admin.
    Notes are visible to the same people — a receptionist books slots but doesn't see them."""
    return user.role == UserRole.ADMIN or (user.role == UserRole.TEACHER and appointment.teacher_id == user.id)
