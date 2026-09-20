"""
Student holds identity/contact/demographic data that doesn't change with
promotion. Class, section, session, and roll number are NOT stored only here —
they're tracked per-session in StudentEnrollment (see enrollment.py), because a
promotion must never overwrite last year's placement.

current_class_id / current_section_id / current_session_id are a denormalized
cache of "wherever the active StudentEnrollment row currently points", kept in
sync by whatever writes enrollments (admission now, promotion later). They exist
purely so "list all students in Grade 8 - Section A" doesn't need a join through
enrollment history on every query — the history itself is never touched by this
cache being updated.
"""
from sqlalchemy import UniqueConstraint

from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import Gender, StudentStatus, EnrollmentStatus


class Student(db.Model, TimestampMixin):
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("school_id", "admission_number", name="uq_student_school_admission_no"),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    admission_number = db.Column(db.String(40), nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    father_name = db.Column(db.String(120))
    mother_name = db.Column(db.String(120))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.Enum(Gender, name="student_gender"))
    cnic_or_bform = db.Column(db.String(40))
    blood_group = db.Column(db.String(5))
    phone = db.Column(db.String(30))
    email = db.Column(db.String(150))
    address = db.Column(db.String(255))
    city = db.Column(db.String(100))
    previous_school = db.Column(db.String(150))
    admission_date = db.Column(db.Date, nullable=False)

    photo_path = db.Column(db.String(255))
    medical_info = db.Column(db.Text)
    notes = db.Column(db.Text)

    status = db.Column(
        db.Enum(StudentStatus, name="student_status"), default=StudentStatus.ACTIVE, nullable=False, index=True
    )

    current_session_id = db.Column(
        db.Integer, db.ForeignKey("academic_sessions.id", ondelete="SET NULL"), nullable=True
    )
    current_class_id = db.Column(db.Integer, db.ForeignKey("classes.id", ondelete="SET NULL"), nullable=True)
    current_section_id = db.Column(db.Integer, db.ForeignKey("sections.id", ondelete="SET NULL"), nullable=True)

    school = db.relationship("School")
    current_session = db.relationship("AcademicSession", foreign_keys=[current_session_id])
    current_class = db.relationship("SchoolClass", foreign_keys=[current_class_id])
    current_section = db.relationship("Section", foreign_keys=[current_section_id])

    enrollments = db.relationship(
        "StudentEnrollment", back_populates="student", cascade="all, delete-orphan",
        order_by="StudentEnrollment.id.desc()",
    )
    guardian_links = db.relationship("StudentGuardian", back_populates="student", cascade="all, delete-orphan")
    documents = db.relationship("StudentDocument", back_populates="student", cascade="all, delete-orphan")

    @property
    def current_enrollment(self):
        """The active enrollment row, if any — this is the source of truth for
        roll number; current_class_id/current_section_id are just a cache of it."""
        for enrollment in self.enrollments:
            if enrollment.status == EnrollmentStatus.ACTIVE:
                return enrollment
        return None

    @property
    def current_roll_number(self):
        enrollment = self.current_enrollment
        return enrollment.roll_number if enrollment else None

    def __repr__(self):
        return f"<Student {self.name} ({self.admission_number})>"
