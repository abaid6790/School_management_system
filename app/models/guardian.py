"""
A Guardian represents a family's contact record, not one row per child. Multiple
students (siblings) link to the same Guardian through StudentGuardian instead of
duplicating father/mother/phone/address for every child — matching the spec's
"don't require duplicate parent information for every child" requirement.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin


class Guardian(db.Model, TimestampMixin):
    __tablename__ = "guardians"

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    father_name = db.Column(db.String(120))
    mother_name = db.Column(db.String(120))
    phone = db.Column(db.String(30), nullable=False)
    alternate_phone = db.Column(db.String(30))
    email = db.Column(db.String(150))
    occupation = db.Column(db.String(120))
    address = db.Column(db.String(255))

    emergency_contact_name = db.Column(db.String(120))
    emergency_contact_phone = db.Column(db.String(30))

    school = db.relationship("School")
    student_links = db.relationship("StudentGuardian", back_populates="guardian", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Guardian {self.father_name or self.mother_name or self.id} (school {self.school_id})>"
