from sqlalchemy import UniqueConstraint

from app.extensions import db
from app.models.mixins import TimestampMixin


class ReportCardRemark(db.Model, TimestampMixin):
    __tablename__ = "report_card_remarks"
    __table_args__ = (
        UniqueConstraint("exam_id", "student_id", name="uq_report_card_remark_exam_student"),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)

    teacher_remarks = db.Column(db.Text)
    principal_remarks = db.Column(db.Text)

    exam = db.relationship("Exam")
    student = db.relationship("Student")

    def __repr__(self):
        return f"<ReportCardRemark exam={self.exam_id} student={self.student_id}>"
