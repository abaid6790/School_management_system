"""
A notice/announcement. Audience is one of a fixed set; CLASS targets one class
(optionally one section). The CHECK uses the enum NAME ('CLASS'), not its value —
see DATABASE.md. Notices are published/archived, never hard-deleted once published,
so what was communicated stays on record.
"""
from sqlalchemy import CheckConstraint, Index

from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import NoticeAudience, NoticeStatus


class Notice(db.Model, TimestampMixin):
    __tablename__ = "notices"
    __table_args__ = (
        CheckConstraint(
            "(audience = 'CLASS' AND class_id IS NOT NULL) OR "
            "(audience <> 'CLASS' AND class_id IS NULL AND section_id IS NULL)",
            name="ck_notice_class_target",
        ),
        CheckConstraint("section_id IS NULL OR class_id IS NOT NULL", name="ck_notice_section_needs_class"),
        Index("ix_notices_school_status", "school_id", "status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    audience = db.Column(db.Enum(NoticeAudience, name="notice_audience"), default=NoticeAudience.ALL, nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id", ondelete="CASCADE"), nullable=True)
    section_id = db.Column(db.Integer, db.ForeignKey("sections.id", ondelete="CASCADE"), nullable=True)

    status = db.Column(db.Enum(NoticeStatus, name="notice_status"), default=NoticeStatus.DRAFT, nullable=False)
    published_at = db.Column(db.DateTime(timezone=True), nullable=True)
    expires_on = db.Column(db.Date, nullable=True)
    is_pinned = db.Column(db.Boolean, nullable=False, default=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    school = db.relationship("School")
    school_class = db.relationship("SchoolClass")
    section = db.relationship("Section")
    created_by = db.relationship("User")

    def __repr__(self):
        return f"<Notice {self.title!r} {self.status.value}>"
