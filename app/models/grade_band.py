"""
SchoolSettings has a grading_system JSON column from Phase 0, but a dedicated
table is easier to query (a single indexed lookup: "which band does this
percentage fall into") and easier to validate (no min/max overlap) than a
JSON blob would be — that JSON field is left in place but unused going
forward in favor of this.
"""
from sqlalchemy import CheckConstraint

from app.extensions import db
from app.models.mixins import TimestampMixin


class GradeBand(db.Model, TimestampMixin):
    __tablename__ = "grade_bands"
    __table_args__ = (
        CheckConstraint("max_percentage >= min_percentage", name="ck_grade_band_max_ge_min"),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    grade = db.Column(db.String(5), nullable=False)          # e.g. "A+", "A", "B", "F"
    min_percentage = db.Column(db.Float, nullable=False)
    max_percentage = db.Column(db.Float, nullable=False)
    order_index = db.Column(db.Integer, nullable=False)       # display order, highest grade first

    school = db.relationship("School")

    def __repr__(self):
        return f"<GradeBand {self.grade} {self.min_percentage}-{self.max_percentage}>"
