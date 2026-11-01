"""
One booked slot between a teacher and a student's guardian. Double-booking is
prevented by two PARTIAL unique indexes that ignore cancelled appointments, so a
cancelled slot can be booked again but history is kept. (Same idea as the
timetable's clash constraints, with a status filter.)
"""
from sqlalchemy import Index, text

from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import AppointmentStatus

_ACTIVE = text("status <> 'CANCELLED'")


class PTMAppointment(db.Model, TimestampMixin):
    __tablename__ = "ptm_appointments"
    __table_args__ = (
        Index("uq_ptm_teacher_slot_active", "meeting_id", "teacher_id", "slot_start", unique=True,
              postgresql_where=_ACTIVE, sqlite_where=_ACTIVE),
        Index("uq_ptm_student_slot_active", "meeting_id", "student_id", "slot_start", unique=True,
              postgresql_where=_ACTIVE, sqlite_where=_ACTIVE),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey("ptm_meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    guardian_id = db.Column(db.Integer, db.ForeignKey("guardians.id", ondelete="SET NULL"), nullable=True)

    slot_start = db.Column(db.Time, nullable=False)
    status = db.Column(db.Enum(AppointmentStatus, name="appointment_status"),
                       default=AppointmentStatus.SCHEDULED, nullable=False)
    notes = db.Column(db.Text)

    meeting = db.relationship("PTMMeeting", back_populates="appointments")
    student = db.relationship("Student")
    teacher = db.relationship("User")
    guardian = db.relationship("Guardian")

    def __repr__(self):
        return f"<PTMAppointment meeting={self.meeting_id} student={self.student_id} {self.slot_start}>"
