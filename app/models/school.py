"""
School is the tenant root. Every other tenant-scoped table (users, sessions,
classes, sections, subjects, and everything added in later phases — students,
fees, exams, etc.) hangs off school_id, either directly or transitively.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin


class School(db.Model, TimestampMixin):
    __tablename__ = "schools"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False, index=True)  # URL-safe identifier
    logo_path = db.Column(db.String(255))
    address = db.Column(db.String(255))
    phone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    website = db.Column(db.String(150))
    registration_number = db.Column(db.String(80))

    is_active = db.Column(db.Boolean, default=True, nullable=False)  # Super Admin can suspend a school

    # --- Relationships ---
    users = db.relationship("User", back_populates="school", cascade="all, delete-orphan")
    sessions = db.relationship("AcademicSession", back_populates="school", cascade="all, delete-orphan")
    settings = db.relationship(
        "SchoolSettings", back_populates="school", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<School {self.name!r} ({self.slug})>"
