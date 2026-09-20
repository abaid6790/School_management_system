"""
Route-level access control. Usage:

    from app.utils.decorators import role_required
    from app.models.enums import UserRole

    @app_bp.route("/students")
    @login_required
    @role_required(UserRole.ADMIN, UserRole.RECEPTIONIST)
    def student_list():
        ...

Kept deliberately simple in Phase 0 — tenant-data-level filtering (which school's
students a request can see) is a separate concern handled by app/utils/tenant.py,
not by this decorator.
"""
from functools import wraps
from flask import abort
from flask_login import current_user


def role_required(*roles):
    allowed = {r.value if hasattr(r, "value") else r for r in roles}

    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role.value not in allowed:
                abort(403)
            return view_func(*args, **kwargs)
        return wrapped_view
    return decorator
