"""
Shared mixins used by every model.

TenantMixin adds a `school_id` FK to any model representing tenant-owned data.
Every query against a tenant table must be scoped by school_id — the enforced
query helper for that lands in Step 0.3 (app/utils/tenant.py) alongside auth,
since it depends on the logged-in user's current school context.
"""
from datetime import datetime, timezone
from sqlalchemy.orm import declared_attr
from app.extensions import db


class TimestampMixin:
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class TenantMixin:
    @declared_attr
    def school_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey("schools.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
