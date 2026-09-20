"""
Single entry point for writing to AuditLog, so every module logs the same way
instead of each rolling its own. Deliberately does NOT call db.session.commit()
itself — it adds the row to the current session so it commits atomically together
with whatever change it's logging (e.g. a marks edit and its audit row either
both save or both roll back, never one without the other).
"""
from flask import request, has_request_context
from flask_login import current_user
from app.extensions import db
from app.models.audit import AuditLog


def log_action(action: str, table_name: str, record_id=None, old_value=None, new_value=None, school_id=None):
    resolved_school_id = school_id
    if resolved_school_id is None and getattr(current_user, "is_authenticated", False):
        resolved_school_id = current_user.school_id

    entry = AuditLog(
        school_id=resolved_school_id,
        user_id=current_user.id if getattr(current_user, "is_authenticated", False) else None,
        action=action,
        table_name=table_name,
        record_id=record_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=request.remote_addr if has_request_context() else None,
    )
    db.session.add(entry)
