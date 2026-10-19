from sqlalchemy import CheckConstraint

from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import PaymentMethod


class Expense(db.Model, TimestampMixin):
    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_expense_amount_positive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("expense_categories.id", ondelete="RESTRICT"), nullable=False, index=True)

    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    expense_date = db.Column(db.Date, nullable=False, index=True)
    payment_method = db.Column(db.Enum(PaymentMethod, name="expense_payment_method"), nullable=False)
    vendor = db.Column(db.String(150))
    notes = db.Column(db.Text)
    recorded_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    school = db.relationship("School")
    category = db.relationship("ExpenseCategory")
    recorded_by = db.relationship("User")

    def __repr__(self):
        return f"<Expense {self.description} amount={self.amount}>"
