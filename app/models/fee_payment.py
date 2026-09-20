from sqlalchemy import UniqueConstraint, CheckConstraint

from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import PaymentMethod


class FeePayment(db.Model, TimestampMixin):
    __tablename__ = "fee_payments"
    __table_args__ = (
        UniqueConstraint("school_id", "receipt_number", name="uq_fee_payment_school_receipt"),
        CheckConstraint("amount > 0", name="ck_fee_payment_amount_positive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    student_fee_id = db.Column(db.Integer, db.ForeignKey("student_fees.id", ondelete="CASCADE"), nullable=False, index=True)

    receipt_number = db.Column(db.String(40), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.Enum(PaymentMethod, name="payment_method"), nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    received_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    school = db.relationship("School")
    student_fee = db.relationship("StudentFee", back_populates="payments")
    received_by = db.relationship("User")

    def __repr__(self):
        return f"<FeePayment {self.receipt_number} amount={self.amount}>"
