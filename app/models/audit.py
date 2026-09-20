"""
Generic, append-only audit trail. Every module in later phases (students,
attendance, marks, fees, promotion, etc.) writes here through a shared helper
(app/services/audit_service.py, added in Step 0.4) instead of each module
rolling its own logging.

old_value/new_value are JSON so this one table can log any entity without a
schema change per module.
"""
from datetime import datetime, timezone
from app.extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    action = db.Column(db.String(80), nullable=False, index=True)   # e.g. "student.created", "marks.edited"
    table_name = db.Column(db.String(80), nullable=False)
    record_id = db.Column(db.Integer, nullable=True)

    old_value = db.Column(db.JSON, nullable=True)
    new_value = db.Column(db.JSON, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    school = db.relationship("School")
    user = db.relationship("User")

    def __repr__(self):
        return f"<AuditLog {self.action} on {self.table_name}#{self.record_id}>"
