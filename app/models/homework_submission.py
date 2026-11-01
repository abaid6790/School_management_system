from sqlalchemy import UniqueConstraint

from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import SubmissionStatus


class HomeworkSubmission(db.Model, TimestampMixin):
    """Teacher-recorded submission status. A row exists only once a teacher has
    recorded something for that student; no row simply means 'not recorded yet'.
    (Students have no logins, so submission is tracked by the teacher.)"""
    __tablename__ = "homework_submissions"
    __table_args__ = (
        UniqueConstraint("homework_id", "student_id", name="uq_submission_homework_student"),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    homework_id = db.Column(db.Integer, db.ForeignKey("homework.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)

    status = db.Column(db.Enum(SubmissionStatus, name="submission_status"), nullable=False)
    submitted_on = db.Column(db.Date, nullable=True)
    remarks = db.Column(db.String(255))
    marked_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    homework = db.relationship("Homework", back_populates="submissions")
    student = db.relationship("Student")
    marked_by = db.relationship("User")

    def __repr__(self):
        return f"<HomeworkSubmission hw={self.homework_id} student={self.student_id} {self.status.value}>"
