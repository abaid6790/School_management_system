"""
obtained_marks <= exam_subject.max_marks cannot be a database CHECK constraint
(Postgres CHECK constraints can't reference another table's column) — that
validation is enforced in the marks-entry route/form instead. What the
database CAN and does enforce here: obtained_marks can't be negative, and a
student can't have two mark rows for the same exam subject.
"""
from sqlalchemy import UniqueConstraint, CheckConstraint

from app.extensions import db
from app.models.mixins import TimestampMixin


class Mark(db.Model, TimestampMixin):
    __tablename__ = "marks"
    __table_args__ = (
        UniqueConstraint("exam_subject_id", "student_id", name="uq_mark_exam_subject_student"),
        CheckConstraint("obtained_marks >= 0", name="ck_mark_obtained_non_negative"),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    exam_subject_id = db.Column(db.Integer, db.ForeignKey("exam_subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)

    obtained_marks = db.Column(db.Numeric(6, 2), nullable=False)
    remarks = db.Column(db.String(255))
    entered_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    exam_subject = db.relationship("ExamSubject", back_populates="marks")
    student = db.relationship("Student")
    entered_by = db.relationship("User")

    def __repr__(self):
        return f"<Mark exam_subject={self.exam_subject_id} student={self.student_id} marks={self.obtained_marks}>"
