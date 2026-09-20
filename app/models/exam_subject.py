"""
max_marks/passing_marks are captured HERE, not read from Subject, because an
exam can legitimately use different marks than the subject's usual default
(e.g. a quiz worth 20 marks for a subject whose normal max is 100) — this is
exactly why the spec lists max/passing marks as Exam Subject fields, separate
from Subject's own.
"""
from sqlalchemy import UniqueConstraint, CheckConstraint

from app.extensions import db
from app.models.mixins import TimestampMixin


class ExamSubject(db.Model, TimestampMixin):
    __tablename__ = "exam_subjects"
    __table_args__ = (
        UniqueConstraint("exam_id", "subject_id", name="uq_exam_subject_pair"),
        CheckConstraint("passing_marks <= max_marks", name="ck_exam_subject_passing_le_max"),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)

    max_marks = db.Column(db.Integer, nullable=False)
    passing_marks = db.Column(db.Integer, nullable=False)
    exam_date = db.Column(db.Date)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    room = db.Column(db.String(50))

    exam = db.relationship("Exam", back_populates="exam_subjects")
    subject = db.relationship("Subject")
    marks = db.relationship("Mark", back_populates="exam_subject", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ExamSubject exam={self.exam_id} subject={self.subject_id}>"
