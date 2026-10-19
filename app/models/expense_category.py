from sqlalchemy import UniqueConstraint

from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import RecordStatus


class ExpenseCategory(db.Model, TimestampMixin):
    __tablename__ = "expense_categories"
    __table_args__ = (
        UniqueConstraint("school_id", "name", name="uq_expense_category_school_name"),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.Enum(RecordStatus, name="expense_category_status"), default=RecordStatus.ACTIVE, nullable=False)

    school = db.relationship("School")

    def __repr__(self):
        return f"<ExpenseCategory {self.name}>"
