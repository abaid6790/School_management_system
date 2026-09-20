"""
An Exam is scoped to a SchoolClass (e.g. "Midterm Exam - Grade 8"), not a
specific section — every section of that class sits the same exam on the
same schedule, matching how real school exams work. Subjects and their
per-subject schedule/marks live in ExamSubject, not here.
"""
from sqlalchemy import UniqueConstraint, CheckConstraint

from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import ExamType, ExamStatus


class Exam(db.Model, TimestampMixin):
    __tablename__ = "exams"
    __table_args__ = (
        UniqueConstraint("school_id", "session_id", "class_id", "name", name="uq_exam_school_session_class_name"),
        CheckConstraint("end_date >= start_date", name="ck_exam_end_after_start"),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = db.Column(db.Integer, db.ForeignKey("academic_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)

    name = db.Column(db.String(120), nullable=False)
    exam_type = db.Column(db.Enum(ExamType, name="exam_type"), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.Enum(ExamStatus, name="exam_status"), default=ExamStatus.SCHEDULED, nullable=False)

    school = db.relationship("School")
    session = db.relationship("AcademicSession")
    school_class = db.relationship("SchoolClass")
    exam_subjects = db.relationship("ExamSubject", back_populates="exam", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Exam {self.name} (class={self.class_id})>"
