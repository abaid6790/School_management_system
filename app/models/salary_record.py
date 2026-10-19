"""
A salary record is for a teacher OR a staff member, never both. The CHECK
constraint uses the enum's stored NAME ('TEACHER'/'STAFF'), not .value — the
lesson from the earlier user/leave constraint bugs. Two separate unique
constraints stop double-processing a recipient for a month without colliding
via nullable columns. net_salary is never stored (see salary_service.py).
"""
from sqlalchemy import CheckConstraint, UniqueConstraint

from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import SalaryRecipientRole, SalaryPaymentStatus


class SalaryRecord(db.Model, TimestampMixin):
    __tablename__ = "salary_records"
    __table_args__ = (
        UniqueConstraint("teacher_user_id", "month", name="uq_salary_teacher_month"),
        UniqueConstraint("staff_id", "month", name="uq_salary_staff_month"),
        CheckConstraint("basic_salary >= 0 AND allowances >= 0 AND deductions >= 0 AND bonus >= 0",
                         name="ck_salary_amounts_non_negative"),
        CheckConstraint(
            "(recipient_role = 'TEACHER' AND teacher_user_id IS NOT NULL AND staff_id IS NULL) OR "
            "(recipient_role = 'STAFF' AND staff_id IS NOT NULL AND teacher_user_id IS NULL)",
            name="ck_salary_exactly_one_recipient",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    recipient_role = db.Column(db.Enum(SalaryRecipientRole, name="salary_recipient_role"), nullable=False, index=True)
    teacher_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    staff_id = db.Column(db.Integer, db.ForeignKey("staff.id", ondelete="CASCADE"), nullable=True)

    month = db.Column(db.Date, nullable=False, index=True)   # convention: the 1st of the month
    basic_salary = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    allowances = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    deductions = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    bonus = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    payment_status = db.Column(
        db.Enum(SalaryPaymentStatus, name="salary_payment_status"), default=SalaryPaymentStatus.PENDING, nullable=False
    )
    payment_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text)

    generated_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    paid_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    school = db.relationship("School")
    teacher = db.relationship("User", foreign_keys=[teacher_user_id])
    staff_member = db.relationship("Staff")
    generated_by = db.relationship("User", foreign_keys=[generated_by_id])
    paid_by = db.relationship("User", foreign_keys=[paid_by_id])

    @property
    def recipient_name(self):
        if self.recipient_role == SalaryRecipientRole.TEACHER:
            return self.teacher.name if self.teacher else "—"
        return self.staff_member.name if self.staff_member else "—"

    def __repr__(self):
        return f"<SalaryRecord {self.recipient_role.value}:{self.id} {self.month} {self.payment_status.value}>"
