from sqlalchemy import UniqueConstraint

from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import RecordStatus


class FeeType(db.Model, TimestampMixin):
    __tablename__ = "fee_types"
    __table_args__ = (
        UniqueConstraint("school_id", "name", name="uq_fee_type_school_name"),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    name = db.Column(db.String(100), nullable=False)          # e.g. "Tuition Fee", "Admission Fee", "Transport Fee"
    default_amount = db.Column(db.Numeric(10, 2))               # suggested amount, editable per assignment
    is_recurring = db.Column(db.Boolean, default=False, nullable=False)  # e.g. monthly tuition vs. one-time admission
    status = db.Column(db.Enum(RecordStatus, name="fee_type_status"), default=RecordStatus.ACTIVE, nullable=False)

    school = db.relationship("School")

    def __repr__(self):
        return f"<FeeType {self.name}>"
