"""
Who can see which notice. Visibility is derived on demand, never stored.

Staff roles (everyone except the Admin, who manages all notices) see a PUBLISHED,
unexpired notice only when its audience concerns staff: ALL and STAFF for every
staff role, TEACHERS additionally for teachers. Notices for PARENTS, STUDENTS or a
CLASS are not shown on the staff board (they are for guardians/students, who have
no logins yet — delivery by email comes in a later step).
"""
from datetime import date

from sqlalchemy import or_

from app.models import Notice
from app.models.enums import NoticeAudience, NoticeStatus, UserRole

AUDIENCE_LABELS = {
    NoticeAudience.ALL: "Everyone in the school",
    NoticeAudience.STAFF: "All staff",
    NoticeAudience.TEACHERS: "Teachers only",
    NoticeAudience.PARENTS: "Parents / guardians",
    NoticeAudience.STUDENTS: "Students",
    NoticeAudience.CLASS: "A specific class",
}


def is_expired(notice, today=None) -> bool:
    today = today or date.today()
    return notice.expires_on is not None and notice.expires_on < today


def audience_label(notice) -> str:
    if notice.audience == NoticeAudience.CLASS and notice.school_class is not None:
        label = f"Class: {notice.school_class.name}"
        if notice.section is not None:
            label += f" – {notice.section.name}"
        return label
    return AUDIENCE_LABELS[notice.audience]


def staff_visible_audiences(role):
    audiences = [NoticeAudience.ALL, NoticeAudience.STAFF]
    if role == UserRole.TEACHER:
        audiences.append(NoticeAudience.TEACHERS)
    return audiences


def staff_board_query(school_id, role, today=None):
    today = today or date.today()
    return (
        Notice.query.filter(
            Notice.school_id == school_id,
            Notice.status == NoticeStatus.PUBLISHED,
            Notice.audience.in_(staff_visible_audiences(role)),
            or_(Notice.expires_on.is_(None), Notice.expires_on >= today),
        )
        .order_by(Notice.is_pinned.desc(), Notice.published_at.desc())
    )


def staff_can_view(notice, role, today=None) -> bool:
    today = today or date.today()
    return (
        notice.status == NoticeStatus.PUBLISHED
        and notice.audience in staff_visible_audiences(role)
        and not is_expired(notice, today)
    )
