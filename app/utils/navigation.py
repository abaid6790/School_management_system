"""
Single source of truth for the sidebar. Every item declares which roles can see
it. Items whose `endpoint` is still None don't have a route yet (their module
lands in a later phase) — the sidebar renders them as a disabled "soon" entry
instead of a broken or absent link, so the full information architecture is
visible from Phase 0 onward. As each phase adds a blueprint, flip that item's
endpoint from None to the real one and it becomes a live link automatically.
"""
from app.models.enums import UserRole

ALL_STAFF = [UserRole.ADMIN, UserRole.TEACHER, UserRole.ACCOUNTANT, UserRole.RECEPTIONIST]

NAV_SECTIONS = [
    {
        "heading": None,
        "items": [
            {"label": "Dashboard", "endpoint": "dashboard.index", "icon": "speedometer2",
             "roles": ALL_STAFF + [UserRole.SUPER_ADMIN]},
        ],
    },
    {
        "heading": "Academics",
        "items": [
            {"label": "Students", "endpoint": "students.list_students", "icon": "people",
             "roles": [UserRole.ADMIN, UserRole.RECEPTIONIST, UserRole.TEACHER]},
            {"label": "Admissions", "endpoint": "students.new_student", "icon": "person-plus",
             "roles": [UserRole.ADMIN, UserRole.RECEPTIONIST]},
            {"label": "Parents", "endpoint": "guardians.list_guardians", "icon": "person-hearts",
             "roles": [UserRole.ADMIN, UserRole.RECEPTIONIST]},
            {"label": "Teachers", "endpoint": "teachers.list_teachers", "icon": "person-workspace", "roles": [UserRole.ADMIN]},
            {"label": "Staff", "endpoint": "staff.list_staff", "icon": "briefcase", "roles": [UserRole.ADMIN]},
            {"label": "Classes", "endpoint": "academic.class_list", "icon": "diagram-3", "roles": [UserRole.ADMIN]},
            {"label": "Sections", "endpoint": "academic.class_list", "icon": "grid", "roles": [UserRole.ADMIN]},
            {"label": "Subjects", "endpoint": "academic.subject_list", "icon": "book",
             "roles": [UserRole.ADMIN, UserRole.TEACHER]},
        ],
    },
    {
        "heading": "Attendance & Schedule",
        "items": [
            {"label": "Attendance", "endpoint": "attendance.index", "icon": "calendar-check",
             "roles": [UserRole.ADMIN, UserRole.TEACHER]},
            {"label": "Timetable", "endpoint": "timetable.index", "icon": "calendar3",
             "roles": [UserRole.ADMIN, UserRole.TEACHER]},
            {"label": "Leave", "endpoint": "leave.list_leave", "icon": "calendar-x",
             "roles": [UserRole.ADMIN, UserRole.TEACHER, UserRole.RECEPTIONIST]},
        ],
    },
    {
        "heading": "Examinations",
        "items": [
            {"label": "Exams", "endpoint": "exams.list_exams", "icon": "pencil-square",
             "roles": [UserRole.ADMIN, UserRole.TEACHER]},
            {"label": "Results", "endpoint": None, "icon": "clipboard-data",
             "roles": [UserRole.ADMIN, UserRole.TEACHER]},
        ],
    },
    {
        "heading": "Finance",
        "items": [
            {"label": "Fees", "endpoint": "fees.index", "icon": "cash-coin",
             "roles": [UserRole.ADMIN, UserRole.ACCOUNTANT, UserRole.RECEPTIONIST]},
            {"label": "Expenses", "endpoint": None, "icon": "receipt",
             "roles": [UserRole.ADMIN, UserRole.ACCOUNTANT]},
            {"label": "Salaries", "endpoint": None, "icon": "wallet2",
             "roles": [UserRole.ADMIN, UserRole.ACCOUNTANT]},
        ],
    },
    {
        "heading": "Communication",
        "items": [
            {"label": "Homework", "endpoint": None, "icon": "journal-text",
             "roles": [UserRole.ADMIN, UserRole.TEACHER]},
            {"label": "Notices", "endpoint": None, "icon": "megaphone", "roles": ALL_STAFF},
            {"label": "Events", "endpoint": None, "icon": "calendar-event", "roles": ALL_STAFF},
        ],
    },
    {
        "heading": "System",
        "items": [
            {"label": "Reports", "endpoint": None, "icon": "bar-chart",
             "roles": [UserRole.ADMIN, UserRole.ACCOUNTANT]},
            {"label": "Audit Log", "endpoint": "audit.list_logs", "icon": "shield-check",
             "roles": [UserRole.ADMIN, UserRole.SUPER_ADMIN]},
            {"label": "Academic Sessions", "endpoint": "academic.session_list", "icon": "calendar-range",
             "roles": [UserRole.ADMIN]},
            {"label": "Settings", "endpoint": None, "icon": "gear", "roles": [UserRole.ADMIN]},
        ],
    },
]


def visible_sections(role: UserRole):
    """NAV_SECTIONS filtered to what `role` can see; sections left with zero
    visible items are dropped entirely rather than shown empty."""
    result = []
    for section in NAV_SECTIONS:
        items = [item for item in section["items"] if role in item["roles"]]
        if items:
            result.append({**section, "items": items})
    return result
