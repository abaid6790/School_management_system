"""
An in-app notification for exactly one recipient: a logged-in user OR a guardian
(guardians have no login yet, so for them this row is mainly the record of an
email that was — or wasn't — sent). Exactly-one is a CHECK constraint.
"""
from sqlalchemy import CheckConstraint, Index

from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import NotificationType


class Notification(db.Model, TimestampMixin):
    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint(
            "(recipient_user_id IS NOT NULL AND recipient_guardian_id IS NULL) OR "
            "(recipient_user_id IS NULL AND recipient_guardian_id IS NOT NULL)",
            name="ck_notification_exactly_one_recipient",
        ),
        Index("ix_notifications_user_unread", "recipient_user_id", "is_read"),
        Index("ix_notifications_guardian_unread", "recipient_guardian_id", "is_read"),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    recipient_guardian_id = db.Column(db.Integer, db.ForeignKey("guardians.id", ondelete="CASCADE"), nullable=True)

    notification_type = db.Column(db.Enum(NotificationType, name="notification_type"),
                                  default=NotificationType.GENERAL, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link_url = db.Column(db.String(300))

    is_read = db.Column(db.Boolean, nullable=False, default=False)
    read_at = db.Column(db.DateTime(timezone=True), nullable=True)
    emailed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    email_error = db.Column(db.String(255), nullable=True)

    school = db.relationship("School")
    recipient_user = db.relationship("User")
    recipient_guardian = db.relationship("Guardian")

    def __repr__(self):
        return f"<Notification {self.notification_type.value} to user={self.recipient_user_id} guardian={self.recipient_guardian_id}>"
