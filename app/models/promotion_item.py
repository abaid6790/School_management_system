"""
One student's decision inside a promotion batch, with a snapshot of where they were (from_*) and where they
will go (to_*). PROMOTE/REPEAT need a target class AND section; GRADUATE/HOLD must have none — the CHECK uses
the enum NAMES ('PROMOTE', ...), as everywhere in this project. to_roll is assigned when the batch is applied.
"""
from sqlalchemy import CheckConstraint, UniqueConstraint

from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import PromotionDecision


class PromotionItem(db.Model, TimestampMixin):
    __tablename__ = "promotion_items"
    __table_args__ = (
        UniqueConstraint("batch_id", "student_id", name="uq_promotion_item_batch_student"),
        CheckConstraint(
            "(decision IN ('PROMOTE', 'REPEAT') AND to_class_id IS NOT NULL AND to_section_id IS NOT NULL) OR "
            "(decision IN ('GRADUATE', 'HOLD') AND to_class_id IS NULL AND to_section_id IS NULL)",
            name="ck_promotion_item_target",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id = db.Column(db.Integer, db.ForeignKey("promotion_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    from_enrollment_id = db.Column(db.Integer, db.ForeignKey("student_enrollments.id", ondelete="SET NULL"), nullable=True)

    from_class_id = db.Column(db.Integer, db.ForeignKey("classes.id", ondelete="RESTRICT"), nullable=False)
    from_section_id = db.Column(db.Integer, db.ForeignKey("sections.id", ondelete="RESTRICT"), nullable=False)
    from_roll = db.Column(db.String(20))

    decision = db.Column(db.Enum(PromotionDecision, name="promotion_decision"), nullable=False)
    to_class_id = db.Column(db.Integer, db.ForeignKey("classes.id", ondelete="RESTRICT"), nullable=True)
    to_section_id = db.Column(db.Integer, db.ForeignKey("sections.id", ondelete="RESTRICT"), nullable=True)
    to_roll = db.Column(db.String(20))

    batch = db.relationship("PromotionBatch", back_populates="items")
    student = db.relationship("Student")
    from_class = db.relationship("SchoolClass", foreign_keys=[from_class_id])
    from_section = db.relationship("Section", foreign_keys=[from_section_id])
    to_class = db.relationship("SchoolClass", foreign_keys=[to_class_id])
    to_section = db.relationship("Section", foreign_keys=[to_section_id])

    def __repr__(self):
        return f"<PromotionItem batch={self.batch_id} student={self.student_id} {self.decision.value}>"
