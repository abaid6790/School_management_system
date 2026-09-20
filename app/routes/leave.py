from datetime import datetime, timezone

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Student, User, Staff, LeaveRequest
from app.models.enums import UserRole, ApplicantRole, LeaveType, LeaveStatus
from app.forms.leave import LeaveRequestForm
from app.utils.decorators import role_required
from app.utils.tenant import current_school_id
from app.services.audit_service import log_action
from app.services.leave_service import sync_attendance_for_leave

leave_bp = Blueprint("leave", __name__, url_prefix="/leave")


@leave_bp.route("/")
@login_required
@role_required(UserRole.ADMIN, UserRole.TEACHER, UserRole.RECEPTIONIST)
def list_leave():
    school_id = current_school_id()
    status = request.args.get("status", "").strip()

    query = LeaveRequest.query.filter_by(school_id=school_id)
    if current_user.role == UserRole.TEACHER:
        query = query.filter_by(applicant_role=ApplicantRole.TEACHER, teacher_user_id=current_user.id)
    if status:
        query = query.filter_by(status=LeaveStatus(status))

    leave_requests = query.order_by(LeaveRequest.created_at.desc()).all()
    return render_template("leave/list.html", leave_requests=leave_requests, status=status, statuses=list(LeaveStatus))


@leave_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.TEACHER)
def new_leave():
    school_id = current_school_id()
    form = LeaveRequestForm()
    is_self_service = current_user.role == UserRole.TEACHER

    students = teachers = staff_members = []
    if not is_self_service:
        students = Student.query.filter_by(school_id=school_id).order_by(Student.name).all()
        teachers = User.query.filter_by(school_id=school_id, role=UserRole.TEACHER).order_by(User.name).all()
        staff_members = Staff.query.filter_by(school_id=school_id).order_by(Staff.name).all()

    if form.validate_on_submit():
        student_id = teacher_user_id = staff_id = None

        if is_self_service:
            applicant_role = ApplicantRole.TEACHER
            teacher_user_id = current_user.id
        else:
            try:
                applicant_role = ApplicantRole(request.form.get("applicant_role"))
            except (ValueError, TypeError):
                flash("Choose who this leave is for.", "danger")
                return redirect(url_for("leave.new_leave"))

            if applicant_role == ApplicantRole.STUDENT:
                student_id = request.form.get("student_id", type=int)
            elif applicant_role == ApplicantRole.TEACHER:
                teacher_user_id = request.form.get("teacher_user_id", type=int)
            else:
                staff_id = request.form.get("staff_id", type=int)

            if not (student_id or teacher_user_id or staff_id):
                flash("Choose a specific person for this leave request.", "danger")
                return redirect(url_for("leave.new_leave"))

        leave = LeaveRequest(
            school_id=school_id, applicant_role=applicant_role,
            student_id=student_id, teacher_user_id=teacher_user_id, staff_id=staff_id,
            leave_type=LeaveType(form.leave_type.data), start_date=form.start_date.data, end_date=form.end_date.data,
            reason=form.reason.data or None, applied_by_id=current_user.id,
        )
        db.session.add(leave)
        db.session.flush()
        log_action("leave.applied", "leave_requests", leave.id, new_value={
            "applicant_role": applicant_role.value,
            "start_date": leave.start_date.isoformat(), "end_date": leave.end_date.isoformat(),
        })
        db.session.commit()
        flash("Leave request submitted.", "success")
        return redirect(url_for("leave.view_leave", leave_id=leave.id))

    return render_template(
        "leave/form.html", form=form, is_self_service=is_self_service,
        students=students, teachers=teachers, staff_members=staff_members,
    )


@leave_bp.route("/<int:leave_id>")
@login_required
@role_required(UserRole.ADMIN, UserRole.TEACHER, UserRole.RECEPTIONIST)
def view_leave(leave_id):
    leave = LeaveRequest.query.filter_by(id=leave_id, school_id=current_school_id()).first_or_404()

    is_owner = leave.applicant_role == ApplicantRole.TEACHER and leave.teacher_user_id == current_user.id
    if current_user.role == UserRole.TEACHER and not is_owner:
        abort(403)

    return render_template("leave/view.html", leave=leave)


@leave_bp.route("/<int:leave_id>/decide", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN)
def decide_leave(leave_id):
    leave = LeaveRequest.query.filter_by(id=leave_id, school_id=current_school_id()).first_or_404()

    if leave.status != LeaveStatus.PENDING:
        flash("This leave request has already been decided.", "warning")
        return redirect(url_for("leave.view_leave", leave_id=leave.id))

    action = request.form.get("action")
    if action not in ("approve", "reject"):
        flash("Invalid action.", "danger")
        return redirect(url_for("leave.view_leave", leave_id=leave.id))

    leave.status = LeaveStatus.APPROVED if action == "approve" else LeaveStatus.REJECTED
    leave.approved_by_id = current_user.id
    leave.approved_on = datetime.now(timezone.utc)
    leave.decision_remarks = request.form.get("decision_remarks", "").strip() or None

    if leave.status == LeaveStatus.APPROVED:
        sync_attendance_for_leave(leave)

    log_action("leave.decided", "leave_requests", leave.id, new_value={"status": leave.status.value})
    db.session.commit()

    flash(f"Leave request {leave.status.value}.", "success")
    return redirect(url_for("leave.view_leave", leave_id=leave.id))


@leave_bp.route("/<int:leave_id>/cancel", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN, UserRole.TEACHER)
def cancel_leave(leave_id):
    leave = LeaveRequest.query.filter_by(id=leave_id, school_id=current_school_id()).first_or_404()

    is_owner = leave.applicant_role == ApplicantRole.TEACHER and leave.teacher_user_id == current_user.id
    if current_user.role == UserRole.TEACHER and not is_owner:
        abort(403)
    if leave.status != LeaveStatus.PENDING:
        flash("Only a pending request can be cancelled.", "warning")
        return redirect(url_for("leave.view_leave", leave_id=leave.id))

    leave.status = LeaveStatus.CANCELLED
    log_action("leave.cancelled", "leave_requests", leave.id)
    db.session.commit()

    flash("Leave request cancelled.", "info")
    return redirect(url_for("leave.view_leave", leave_id=leave.id))
