"""
Daily granularity (one row per student per calendar day), matching how the
spec's examples describe marking ("Grade 8 - Section A, Date: 10 September
2026 ... Present/Absent/Late") — not per-period, since periods don't exist
until the Timetable phase.

class_id/section_id/session_id are captured at the moment attendance is
marked, not read live off Student.current_class_id. If a student is later
promoted to a different class, their attendance history from the old class
must keep saying they were in the old class — exactly the same reasoning as
StudentEnrollment.
"""
from sqlalchemy import UniqueConstraint

from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import AttendanceStatus


class StudentAttendance(db.Model, TimestampMixin):
    __tablename__ = "student_attendance"
    __table_args__ = (
        UniqueConstraint("student_id", "date", name="uq_student_attendance_one_per_day"),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = db.Column(db.Integer, db.ForeignKey("academic_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id = db.Column(db.Integer, db.ForeignKey("sections.id", ondelete="CASCADE"), nullable=False, index=True)

    date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.Enum(AttendanceStatus, name="student_attendance_status"), nullable=False)
    remarks = db.Column(db.String(255))
    marked_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    student = db.relationship("Student")
    session = db.relationship("AcademicSession")
    school_class = db.relationship("SchoolClass")
    section = db.relationship("Section")
    marked_by = db.relationship("User")

    def __repr__(self):
        return f"<StudentAttendance student={self.student_id} date={self.date} status={self.status.value}>"
