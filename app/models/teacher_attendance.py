from sqlalchemy import UniqueConstraint

from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import AttendanceStatus


class TeacherAttendance(db.Model, TimestampMixin):
    __tablename__ = "teacher_attendance"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_teacher_attendance_one_per_day"),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.Enum(AttendanceStatus, name="teacher_attendance_status"), nullable=False)
    remarks = db.Column(db.String(255))
    marked_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    teacher = db.relationship("User", foreign_keys=[user_id])
    marked_by = db.relationship("User", foreign_keys=[marked_by_id])

    def __repr__(self):
        return f"<TeacherAttendance user={self.user_id} date={self.date} status={self.status.value}>"
