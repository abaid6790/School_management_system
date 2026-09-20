"""
The authoritative record of "which class/section a student was in, in which
session, with which roll number". Admission creates the first row. Promotion
(a later phase) never edits an existing row — it marks the old one PROMOTED/
REPEATED/etc. and inserts a new row for the new session. This is what makes
"historical academic data is preserved" (spec requirement) actually true at
the schema level, not just a promise in application code.
"""
from sqlalchemy import UniqueConstraint

from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import EnrollmentStatus


class StudentEnrollment(db.Model, TimestampMixin):
    __tablename__ = "student_enrollments"
    __table_args__ = (
        UniqueConstraint(
            "session_id", "class_id", "section_id", "roll_number",
            name="uq_enrollment_roll_per_section_session",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = db.Column(
        db.Integer, db.ForeignKey("academic_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id = db.Column(db.Integer, db.ForeignKey("sections.id", ondelete="CASCADE"), nullable=False, index=True)

    roll_number = db.Column(db.String(20), nullable=False)
    enrolled_on = db.Column(db.Date, nullable=False)
    status = db.Column(
        db.Enum(EnrollmentStatus, name="enrollment_status"), default=EnrollmentStatus.ACTIVE, nullable=False
    )
    remarks = db.Column(db.Text)

    student = db.relationship("Student", back_populates="enrollments")
    session = db.relationship("AcademicSession")
    school_class = db.relationship("SchoolClass")
    section = db.relationship("Section")

    def __repr__(self):
        return f"<StudentEnrollment student={self.student_id} class={self.class_id} roll={self.roll_number}>"
