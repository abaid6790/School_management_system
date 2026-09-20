"""
The three DB UniqueConstraints on TimetableEntry are the hard guarantee against
double-booking (see models/timetable.py), but a raw IntegrityError makes for a
poor form experience. This runs the same three checks proactively, so the user
sees "Ms. Khan is already teaching Grade 8-B at this time" instead of a
constraint-name-mangled database error — the DB constraint stays as the actual
safety net (e.g. against a race condition), this is purely for UX.
"""
from app.models import TimetableEntry


def find_conflicts(session_id, day_of_week, period_id, section_id, teacher_id, room, exclude_entry_id=None):
    conflicts = []

    section_q = TimetableEntry.query.filter_by(
        session_id=session_id, section_id=section_id, day_of_week=day_of_week, period_id=period_id
    )
    if exclude_entry_id:
        section_q = section_q.filter(TimetableEntry.id != exclude_entry_id)
    existing_section = section_q.first()
    if existing_section:
        subject_name = existing_section.subject.name if existing_section.subject else "another subject"
        conflicts.append(f"This class already has {subject_name} scheduled in this period.")

    if teacher_id:
        teacher_q = TimetableEntry.query.filter_by(
            session_id=session_id, teacher_id=teacher_id, day_of_week=day_of_week, period_id=period_id
        )
        if exclude_entry_id:
            teacher_q = teacher_q.filter(TimetableEntry.id != exclude_entry_id)
        existing_teacher = teacher_q.first()
        if existing_teacher:
            conflicts.append(
                f"{existing_teacher.teacher.name} is already teaching "
                f"{existing_teacher.school_class.name} - {existing_teacher.section.name} at this time."
            )

    if room:
        room_q = TimetableEntry.query.filter_by(
            session_id=session_id, room=room, day_of_week=day_of_week, period_id=period_id
        )
        if exclude_entry_id:
            room_q = room_q.filter(TimetableEntry.id != exclude_entry_id)
        existing_room = room_q.first()
        if existing_room:
            conflicts.append(
                f"Room {room} is already booked by "
                f"{existing_room.school_class.name} - {existing_room.section.name} at this time."
            )

    return conflicts
