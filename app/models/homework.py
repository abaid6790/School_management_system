from sqlalchemy import CheckConstraint, Index

from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import HomeworkStatus


class Homework(db.Model, TimestampMixin):
    """Homework set for a class (section_id NULL = every section of the class).
    Cancelled rather than deleted, because submission records depend on it."""
    __tablename__ = "homework"
    __table_args__ = (
        CheckConstraint("due_date >= assigned_date", name="ck_homework_due_after_assigned"),
        CheckConstraint("section_id IS NULL OR class_id IS NOT NULL", name="ck_homework_section_needs_class"),
        Index("ix_homework_class_due", "school_id", "class_id", "due_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = db.Column(db.Integer, db.ForeignKey("academic_sessions.id", ondelete="CASCADE"), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey("sections.id", ondelete="CASCADE"), nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    assigned_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum(HomeworkStatus, name="homework_status"), default=HomeworkStatus.ACTIVE, nullable=False)

    school = db.relationship("School")
    session = db.relationship("AcademicSession")
    school_class = db.relationship("SchoolClass")
    section = db.relationship("Section")
    subject = db.relationship("Subject")
    teacher = db.relationship("User")
    submissions = db.relationship("HomeworkSubmission", back_populates="homework", passive_deletes=True)

    def __repr__(self):
        return f"<Homework {self.title!r} due {self.due_date}>"
