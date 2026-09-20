"""
computed_amount is snapshotted at the moment the discount is applied — for a
PERCENTAGE discount this means "X% of the fee's amount at that time", stored
as a concrete number so the discount doesn't silently change if the fee's
amount were ever edited later. A CHECK constraint keeps a single discount row
sane on its own; the "total discounts can't exceed the fee amount" rule is
enforced in fee_service.py since it spans multiple rows (a DB CHECK can't sum
sibling rows).
"""
from sqlalchemy import CheckConstraint

from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import DiscountType


class FeeDiscount(db.Model, TimestampMixin):
    __tablename__ = "fee_discounts"
    __table_args__ = (
        CheckConstraint("computed_amount >= 0", name="ck_fee_discount_non_negative"),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    student_fee_id = db.Column(db.Integer, db.ForeignKey("student_fees.id", ondelete="CASCADE"), nullable=False, index=True)

    discount_type = db.Column(db.Enum(DiscountType, name="discount_type"), nullable=False)
    value = db.Column(db.Numeric(10, 2), nullable=False)          # the raw input: a flat amount, or a percentage number
    computed_amount = db.Column(db.Numeric(10, 2), nullable=False)  # the actual amount deducted, snapshotted
    reason = db.Column(db.Text, nullable=False)
    applied_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    student_fee = db.relationship("StudentFee", back_populates="discounts")
    applied_by = db.relationship("User")

    def __repr__(self):
        return f"<FeeDiscount {self.discount_type.value} -{self.computed_amount} on fee {self.student_fee_id}>"
