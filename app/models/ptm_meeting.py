from sqlalchemy import CheckConstraint

from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import MeetingStatus


class PTMMeeting(db.Model, TimestampMixin):
    """A parent-teacher meeting day, divided into fixed-length slots. Optionally
    limited to a class/section."""
    __tablename__ = "ptm_meetings"
    __table_args__ = (
        CheckConstraint("end_time > start_time", name="ck_ptm_time_order"),
        CheckConstraint("slot_minutes BETWEEN 5 AND 120", name="ck_ptm_slot_minutes"),
        CheckConstraint("section_id IS NULL OR class_id IS NOT NULL", name="ck_ptm_section_needs_class"),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = db.Column(db.Integer, db.ForeignKey("academic_sessions.id", ondelete="CASCADE"), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id", ondelete="CASCADE"), nullable=True)
    section_id = db.Column(db.Integer, db.ForeignKey("sections.id", ondelete="CASCADE"), nullable=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    meeting_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    slot_minutes = db.Column(db.Integer, nullable=False, default=10)
    location = db.Column(db.String(150))
    status = db.Column(db.Enum(MeetingStatus, name="meeting_status"), default=MeetingStatus.SCHEDULED, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    school = db.relationship("School")
    session = db.relationship("AcademicSession")
    school_class = db.relationship("SchoolClass")
    section = db.relationship("Section")
    created_by = db.relationship("User", foreign_keys=[created_by_id])
    appointments = db.relationship("PTMAppointment", back_populates="meeting", passive_deletes=True)

    def __repr__(self):
        return f"<PTMMeeting {self.title!r} {self.meeting_date}>"
