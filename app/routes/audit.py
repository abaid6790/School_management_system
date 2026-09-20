from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

from app.models import AuditLog
from app.models.enums import UserRole
from app.utils.decorators import role_required
from app.utils.tenant import current_school_id

audit_bp = Blueprint("audit", __name__)

PER_PAGE = 25


@audit_bp.route("/audit-logs")
@login_required
@role_required(UserRole.ADMIN, UserRole.SUPER_ADMIN)
def list_logs():
    page = request.args.get("page", 1, type=int)
    query = AuditLog.query.order_by(AuditLog.created_at.desc())

    # A school Admin only ever sees their own school's trail. A Super Admin has
    # no single school (current_school_id() returns None for that role), so
    # they see everything — tenant scoping doesn't apply to them by design.
    if current_user.role != UserRole.SUPER_ADMIN:
        query = query.filter_by(school_id=current_school_id())

    pagination = query.paginate(page=page, per_page=PER_PAGE, error_out=False)
    return render_template("audit/list.html", pagination=pagination, logs=pagination.items)
