"""
Every feature module from Phase 1 onward (students, attendance, fees, exams...)
must filter its queries by the current user's school. This is the single place
that resolves "which school" — so that logic never gets duplicated or,
worse, forgotten in some route.

A super_admin has no single school (see the CHECK constraint on User), and is
expected to explicitly choose which school's data to view via a school_id in
the URL/session rather than an implicit one — that selection mechanism is
added alongside the Super Admin views in a later phase.
"""
from flask_login import current_user
from app.models.enums import UserRole


def current_school_id():
    if not current_user.is_authenticated:
        return None
    if current_user.role == UserRole.SUPER_ADMIN:
        return None
    return current_user.school_id
