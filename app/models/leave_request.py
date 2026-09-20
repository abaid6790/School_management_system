"""
One leave table for all three applicant kinds rather than three near-identical
tables, since the workflow (apply -> pending -> approve/reject) is identical.
Exactly one of student_id / teacher_user_id / staff_id is populated, matching
applicant_role — enforced by a CHECK constraint, not just application code, so
a bug elsewhere can't silently create a leave request that points at nothing
or at the wrong kind of applicant.
"""
from sqlalchemy import CheckConstraint

from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import ApplicantRole, LeaveType, LeaveStatus


class LeaveRequest(db.Model, TimestampMixin):
    __tablename__ = "leave_requests"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_leave_end_after_start"),
        # NOTE: db.Enum(PyEnum) stores the member's NAME by default (e.g. "STUDENT"),
        # not its .value ("student") — this constraint must match that, not the
        # lowercase values used everywhere in Python/forms/URLs.
        CheckConstraint(
            "(applicant_role = 'STUDENT' AND student_id IS NOT NULL AND teacher_user_id IS NULL AND staff_id IS NULL) OR "
            "(applicant_role = 'TEACHER' AND teacher_user_id IS NOT NULL AND student_id IS NULL AND staff_id IS NULL) OR "
            "(applicant_role = 'STAFF' AND staff_id IS NOT NULL AND student_id IS NULL AND teacher_user_id IS NULL)",
            name="ck_leave_exactly_one_applicant",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    applicant_role = db.Column(db.Enum(ApplicantRole, name="leave_applicant_role"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=True)
    teacher_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    staff_id = db.Column(db.Integer, db.ForeignKey("staff.id", ondelete="CASCADE"), nullable=True)

    leave_type = db.Column(db.Enum(LeaveType, name="leave_type"), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text)

    status = db.Column(db.Enum(LeaveStatus, name="leave_status"), default=LeaveStatus.PENDING, nullable=False, index=True)
    applied_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_on = db.Column(db.DateTime(timezone=True), nullable=True)
    decision_remarks = db.Column(db.Text)

    school = db.relationship("School")
    student = db.relationship("Student")
    teacher = db.relationship("User", foreign_keys=[teacher_user_id])
    staff_member = db.relationship("Staff")
    applied_by = db.relationship("User", foreign_keys=[applied_by_id])
    approved_by = db.relationship("User", foreign_keys=[approved_by_id])

    @property
    def applicant_name(self):
        if self.applicant_role == ApplicantRole.STUDENT:
            return self.student.name if self.student else "—"
        if self.applicant_role == ApplicantRole.TEACHER:
            return self.teacher.name if self.teacher else "—"
        return self.staff_member.name if self.staff_member else "—"

    def __repr__(self):
        return f"<LeaveRequest {self.applicant_role.value}:{self.id} {self.start_date}..{self.end_date} {self.status.value}>"
