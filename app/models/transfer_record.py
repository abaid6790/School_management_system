"""
A student leaving the school: transferred to another school, or withdrawn. The row snapshots where the
student was (last_*) and what they owed (dues_amount) at the moment of leaving, and carries the transfer
certificate number once one is issued. Exactly one ACTIVE record per student (partial unique index); a
reversed exit stays as history and the student may then be re-admitted and leave again later.
"""
from sqlalchemy import CheckConstraint, Index, UniqueConstraint, text

from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import TransferType, TransferStatus

_ACTIVE = text("status = 'ACTIVE'")


class TransferRecord(db.Model, TimestampMixin):
    __tablename__ = "transfer_records"
    __table_args__ = (
        UniqueConstraint("school_id", "certificate_number", name="uq_transfer_certificate_per_school"),
        CheckConstraint("dues_amount >= 0", name="ck_transfer_dues_non_negative"),
        CheckConstraint("certificate_number IS NULL OR certificate_issued_on IS NOT NULL", name="ck_transfer_certificate_has_date"),
        Index("uq_one_active_transfer_per_student", "student_id", unique=True,
              postgresql_where=_ACTIVE, sqlite_where=_ACTIVE),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="RESTRICT"), nullable=False, index=True)

    transfer_type = db.Column(db.Enum(TransferType, name="transfer_type"), nullable=False)
    status = db.Column(db.Enum(TransferStatus, name="transfer_status"), default=TransferStatus.ACTIVE, nullable=False)
    effective_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text)
    destination_school = db.Column(db.String(200))
    conduct = db.Column(db.String(100))
    remarks = db.Column(db.Text)

    # where the student was when they left (snapshots — they stay true even if the student record later changes)
    last_session_id = db.Column(db.Integer, db.ForeignKey("academic_sessions.id", ondelete="SET NULL"), nullable=True)
    last_class_id = db.Column(db.Integer, db.ForeignKey("classes.id", ondelete="SET NULL"), nullable=True)
    last_section_id = db.Column(db.Integer, db.ForeignKey("sections.id", ondelete="SET NULL"), nullable=True)
    last_roll_number = db.Column(db.String(20))

    dues_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)       # outstanding fees at the time of leaving
    dues_acknowledged = db.Column(db.Boolean, nullable=False, default=False)    # left with dues, knowingly

    certificate_number = db.Column(db.String(30), nullable=True)
    certificate_issued_on = db.Column(db.Date, nullable=True)

    processed_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reversed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    reversed_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    school = db.relationship("School")
    student = db.relationship("Student")
    last_session = db.relationship("AcademicSession")
    last_class = db.relationship("SchoolClass")
    last_section = db.relationship("Section")
    processed_by = db.relationship("User", foreign_keys=[processed_by_id])
    reversed_by = db.relationship("User", foreign_keys=[reversed_by_id])

    def __repr__(self):
        return f"<TransferRecord student={self.student_id} {self.transfer_type.value} {self.status.value}>"
