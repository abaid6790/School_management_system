"""
Three separate UniqueConstraints do the heavy lifting for conflict prevention,
each scoped to (session, day, period) so the same room/teacher/section slot
can never be double-booked within one academic session:

  - uq_timetable_section_slot: a section can't have two different subjects in
    the same period on the same day (SQL NULLs aren't at play here — section_id
    is always set).
  - uq_timetable_teacher_slot: a teacher can't be in two classes at once.
    teacher_id is nullable (free periods/breaks have no teacher) — standard
    SQL treats multiple NULLs as non-conflicting, so break periods never
    collide with each other under this constraint.
  - uq_timetable_room_slot: same idea for rooms; room is nullable and optional.

These are real database constraints, not just application-level checks, so a
race condition or a bug in the route code still can't create a double-booking.
"""
from sqlalchemy import UniqueConstraint

from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import DayOfWeek


class TimetableEntry(db.Model, TimestampMixin):
    __tablename__ = "timetable_entries"
    __table_args__ = (
        UniqueConstraint("session_id", "section_id", "day_of_week", "period_id", name="uq_timetable_section_slot"),
        UniqueConstraint("session_id", "teacher_id", "day_of_week", "period_id", name="uq_timetable_teacher_slot"),
        UniqueConstraint("session_id", "room", "day_of_week", "period_id", name="uq_timetable_room_slot"),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = db.Column(db.Integer, db.ForeignKey("academic_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id = db.Column(db.Integer, db.ForeignKey("sections.id", ondelete="CASCADE"), nullable=False, index=True)
    period_id = db.Column(db.Integer, db.ForeignKey("periods.id", ondelete="CASCADE"), nullable=False, index=True)

    day_of_week = db.Column(db.Enum(DayOfWeek, name="timetable_day_of_week"), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    room = db.Column(db.String(50), nullable=True)

    school = db.relationship("School")
    session = db.relationship("AcademicSession")
    school_class = db.relationship("SchoolClass")
    section = db.relationship("Section")
    period = db.relationship("Period")
    subject = db.relationship("Subject")
    teacher = db.relationship("User")

    def __repr__(self):
        return f"<TimetableEntry section={self.section_id} {self.day_of_week.value} period={self.period_id}>"
