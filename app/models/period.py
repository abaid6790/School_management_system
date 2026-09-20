"""
Periods are defined once per school (not per class) — every class follows the
same period grid (Period 1 is always 8:00-8:45 for the whole school), which is
how real timetables work and is what makes "same teacher, same period, two
different classes" a meaningful conflict to detect in TimetableEntry.
"""
from sqlalchemy import UniqueConstraint, CheckConstraint

from app.extensions import db
from app.models.mixins import TimestampMixin


class Period(db.Model, TimestampMixin):
    __tablename__ = "periods"
    __table_args__ = (
        UniqueConstraint("school_id", "order_index", name="uq_period_school_order"),
        UniqueConstraint("school_id", "name", name="uq_period_school_name"),
        CheckConstraint("end_time > start_time", name="ck_period_end_after_start"),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    name = db.Column(db.String(50), nullable=False)          # e.g. "Period 1", "Lunch Break"
    order_index = db.Column(db.Integer, nullable=False)       # display/sort order through the day
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_break = db.Column(db.Boolean, default=False, nullable=False)  # break periods don't need a subject/teacher

    school = db.relationship("School")

    def __repr__(self):
        return f"<Period {self.name} {self.start_time}-{self.end_time}>"
