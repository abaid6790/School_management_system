"""
Core academic structure, all scoped to a school (tenant):

School -> AcademicSession -> SchoolClass -> Section
                                  \\-> Subject

Named SchoolClass (table "classes") instead of Class to avoid shadowing the
Python keyword and to keep the model name unambiguous once Student, etc. exist.
"""
from sqlalchemy import Index, CheckConstraint, UniqueConstraint

from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import SubjectType, RecordStatus


class AcademicSession(db.Model, TimestampMixin):
    __tablename__ = "academic_sessions"
    __table_args__ = (
        UniqueConstraint("school_id", "name", name="uq_session_school_name"),
        CheckConstraint("end_date > start_date", name="ck_session_end_after_start"),
        # Enforces "only one active session per school" at the database level,
        # not just in application code.
        Index(
            "uq_one_active_session_per_school",
            "school_id",
            unique=True,
            postgresql_where=db.text("is_active = true"),
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    name = db.Column(db.String(50), nullable=False)  # e.g. "2026-2027"
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    description = db.Column(db.Text)

    school = db.relationship("School", back_populates="sessions")
    classes = db.relationship("SchoolClass", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AcademicSession {self.name}>"


class SchoolClass(db.Model, TimestampMixin):
    __tablename__ = "classes"
    __table_args__ = (
        UniqueConstraint("school_id", "session_id", "name", name="uq_class_school_session_name"),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = db.Column(
        db.Integer, db.ForeignKey("academic_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name = db.Column(db.String(80), nullable=False)   # e.g. "Grade 8"
    code = db.Column(db.String(30))
    class_teacher_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    capacity = db.Column(db.Integer)
    status = db.Column(db.Enum(RecordStatus, name="class_status"), default=RecordStatus.ACTIVE, nullable=False)

    school = db.relationship("School")
    session = db.relationship("AcademicSession", back_populates="classes")
    class_teacher = db.relationship("User", foreign_keys=[class_teacher_id])
    sections = db.relationship("Section", back_populates="school_class", cascade="all, delete-orphan")
    subjects = db.relationship("Subject", back_populates="school_class", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SchoolClass {self.name}>"


class Section(db.Model, TimestampMixin):
    __tablename__ = "sections"
    __table_args__ = (
        UniqueConstraint("class_id", "name", name="uq_section_class_name"),
    )

    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)

    name = db.Column(db.String(30), nullable=False)  # e.g. "A"
    room = db.Column(db.String(30))
    class_teacher_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    capacity = db.Column(db.Integer)
    status = db.Column(db.Enum(RecordStatus, name="section_status"), default=RecordStatus.ACTIVE, nullable=False)

    school_class = db.relationship("SchoolClass", back_populates="sections")
    class_teacher = db.relationship("User", foreign_keys=[class_teacher_id])

    def __repr__(self):
        return f"<Section {self.name} of class {self.class_id}>"


class Subject(db.Model, TimestampMixin):
    __tablename__ = "subjects"
    __table_args__ = (
        UniqueConstraint("school_id", "class_id", "code", name="uq_subject_school_class_code"),
        CheckConstraint("passing_marks <= max_marks", name="ck_subject_passing_le_max"),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(30), nullable=False)
    max_marks = db.Column(db.Integer, default=100, nullable=False)
    passing_marks = db.Column(db.Integer, default=40, nullable=False)
    subject_type = db.Column(db.Enum(SubjectType, name="subject_type"), default=SubjectType.CORE, nullable=False)
    status = db.Column(db.Enum(RecordStatus, name="subject_status"), default=RecordStatus.ACTIVE, nullable=False)

    school = db.relationship("School")
    school_class = db.relationship("SchoolClass", back_populates="subjects")
    teacher = db.relationship("User", foreign_keys=[teacher_id])

    def __repr__(self):
        return f"<Subject {self.name} ({self.code})>"
