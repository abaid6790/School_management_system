"""
Approving a leave request writes into StudentAttendance or TeacherAttendance
for every day it covers, upserting exactly like the manual marking routes do
(same "find existing row for this day, update it; else create" pattern) — so
attendance and an approved leave can never quietly contradict each other.

Staff (non-teaching) have no attendance module yet, so a Staff leave request
stands alone — nothing to sync it into.
"""
from datetime import timedelta

from app.extensions import db
from app.models import StudentAttendance, TeacherAttendance
from app.models.enums import ApplicantRole, AttendanceStatus


def _date_range(start_date, end_date):
    for offset in range((end_date - start_date).days + 1):
        yield start_date + timedelta(days=offset)


def sync_attendance_for_leave(leave) -> None:
    if leave.applicant_role == ApplicantRole.TEACHER:
        for d in _date_range(leave.start_date, leave.end_date):
            record = TeacherAttendance.query.filter_by(user_id=leave.teacher_user_id, date=d).first()
            if record:
                record.status = AttendanceStatus.LEAVE
                record.marked_by_id = leave.approved_by_id
            else:
                db.session.add(TeacherAttendance(
                    school_id=leave.school_id, user_id=leave.teacher_user_id, date=d,
                    status=AttendanceStatus.LEAVE, marked_by_id=leave.approved_by_id,
                ))

    elif leave.applicant_role == ApplicantRole.STUDENT:
        student = leave.student
        if not student or not student.current_session_id:
            return
        for d in _date_range(leave.start_date, leave.end_date):
            record = StudentAttendance.query.filter_by(student_id=student.id, date=d).first()
            if record:
                record.status = AttendanceStatus.EXCUSED
                record.marked_by_id = leave.approved_by_id
            else:
                db.session.add(StudentAttendance(
                    school_id=leave.school_id, student_id=student.id, session_id=student.current_session_id,
                    class_id=student.current_class_id, section_id=student.current_section_id,
                    date=d, status=AttendanceStatus.EXCUSED, marked_by_id=leave.approved_by_id,
                ))
