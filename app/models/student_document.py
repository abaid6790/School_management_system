from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import DocumentType


class StudentDocument(db.Model, TimestampMixin):
    __tablename__ = "student_documents"

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)

    document_type = db.Column(db.Enum(DocumentType, name="student_document_type"), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    student = db.relationship("Student", back_populates="documents")
    uploaded_by = db.relationship("User")

    def __repr__(self):
        return f"<StudentDocument {self.document_type.value} for student {self.student_id}>"
