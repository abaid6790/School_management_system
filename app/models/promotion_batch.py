"""
One promotion run from a source session to a target session. It starts as a DRAFT — the Admin reviews and
edits each student's decision, and nothing about any student changes — and is later APPLIED atomically.
A school has at most one open draft per (source, target) pair (partial unique index), so there is always
exactly one place to continue; applied batches stay as the permanent record of what was done.
"""
from sqlalchemy import CheckConstraint, Index, text

from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import PromotionBatchStatus

_DRAFT = text("status = 'DRAFT'")


class PromotionBatch(db.Model, TimestampMixin):
    __tablename__ = "promotion_batches"
    __table_args__ = (
        CheckConstraint("source_session_id <> target_session_id", name="ck_promotion_sessions_differ"),
        Index("uq_one_draft_promotion_per_pair", "school_id", "source_session_id", "target_session_id", unique=True,
              postgresql_where=_DRAFT, sqlite_where=_DRAFT),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    source_session_id = db.Column(db.Integer, db.ForeignKey("academic_sessions.id", ondelete="RESTRICT"), nullable=False)
    target_session_id = db.Column(db.Integer, db.ForeignKey("academic_sessions.id", ondelete="RESTRICT"), nullable=False)

    status = db.Column(db.Enum(PromotionBatchStatus, name="promotion_batch_status"),
                       default=PromotionBatchStatus.DRAFT, nullable=False)
    notes = db.Column(db.Text)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    applied_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    applied_at = db.Column(db.DateTime(timezone=True), nullable=True)

    school = db.relationship("School")
    source_session = db.relationship("AcademicSession", foreign_keys=[source_session_id])
    target_session = db.relationship("AcademicSession", foreign_keys=[target_session_id])
    created_by = db.relationship("User", foreign_keys=[created_by_id])
    applied_by = db.relationship("User", foreign_keys=[applied_by_id])
    items = db.relationship("PromotionItem", back_populates="batch", passive_deletes=True)

    def __repr__(self):
        return f"<PromotionBatch {self.source_session_id}->{self.target_session_id} {self.status.value}>"
