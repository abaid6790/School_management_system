"""
One settings row per school. Holds the configurable rules referenced throughout
later phases: grading scale, passing criteria, attendance policy, default fee
payment methods. Kept as one row (not scattered flags) so Settings UI in a later
phase is a single form.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin


class SchoolSettings(db.Model, TimestampMixin):
    __tablename__ = "school_settings"

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(
        db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # Grading scale, e.g. [{"min": 90, "max": 100, "grade": "A+"}, {"min": 80, "max": 89, "grade": "A"}, ...]
    grading_system = db.Column(db.JSON, default=list, nullable=False)
    passing_percentage = db.Column(db.Float, default=40.0, nullable=False)

    attendance_late_threshold_minutes = db.Column(db.Integer, default=15, nullable=False)
    minimum_attendance_percentage = db.Column(db.Float, default=75.0, nullable=False)

    fee_fine_per_day = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    default_payment_methods = db.Column(
        db.JSON,
        default=lambda: ["cash", "bank_transfer", "card", "cheque", "mobile_wallet"],
        nullable=False,
    )

    school = db.relationship("School", back_populates="settings")

    def __repr__(self):
        return f"<SchoolSettings for school {self.school_id}>"
