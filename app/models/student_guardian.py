from app.extensions import db
from app.models.enums import GuardianRelation


class StudentGuardian(db.Model):
    __tablename__ = "student_guardians"
    __table_args__ = (
        db.UniqueConstraint("student_id", "guardian_id", name="uq_student_guardian_pair"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    guardian_id = db.Column(db.Integer, db.ForeignKey("guardians.id", ondelete="CASCADE"), nullable=False, index=True)

    relationship_to_student = db.Column(db.Enum(GuardianRelation, name="guardian_relation"), nullable=False)
    is_primary_contact = db.Column(db.Boolean, default=True, nullable=False)
    is_emergency_contact = db.Column(db.Boolean, default=False, nullable=False)

    student = db.relationship("Student", back_populates="guardian_links")
    guardian = db.relationship("Guardian", back_populates="student_links")

    def __repr__(self):
        return f"<StudentGuardian student={self.student_id} guardian={self.guardian_id}>"
