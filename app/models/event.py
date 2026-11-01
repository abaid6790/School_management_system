from sqlalchemy import CheckConstraint, Index

from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import EventType


class Event(db.Model, TimestampMixin):
    """A school-wide calendar event. is_holiday marks days the school is closed
    (kept as data now so attendance screens can honour it later)."""
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_event_date_order"),
        CheckConstraint(
            "start_time IS NULL OR end_time IS NULL OR end_date > start_date OR end_time > start_time",
            name="ck_event_time_order",
        ),
        Index("ix_events_school_start", "school_id", "start_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_type = db.Column(db.Enum(EventType, name="event_type"), default=EventType.OTHER, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    location = db.Column(db.String(150))
    is_holiday = db.Column(db.Boolean, nullable=False, default=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    school = db.relationship("School")
    created_by = db.relationship("User")

    def __repr__(self):
        return f"<Event {self.title!r} {self.start_date}>"
