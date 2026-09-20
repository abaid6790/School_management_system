from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models import AcademicSession, SchoolClass, Section, Subject, Period, TimetableEntry, User
from app.models.enums import UserRole, DayOfWeek
from app.utils.decorators import role_required
from app.utils.tenant import current_school_id
from app.services.audit_service import log_action
from app.services.timetable_service import find_conflicts

timetable_bp = Blueprint("timetable", __name__, url_prefix="/timetable")

DAYS_ORDER = list(DayOfWeek)


@timetable_bp.route("/")
@login_required
@role_required(UserRole.ADMIN, UserRole.TEACHER)
def index():
    school_id = current_school_id()
    active_session = AcademicSession.query.filter_by(school_id=school_id, is_active=True).first()
    if not active_session:
        flash("No active academic session — activate one before building a timetable.", "warning")
        return redirect(url_for("academic.session_list"))

    classes = SchoolClass.query.filter_by(school_id=school_id, session_id=active_session.id).order_by(SchoolClass.name).all()
    sections_by_class = {c.id: [[s.id, s.name] for s in c.sections] for c in classes}
    periods = Period.query.filter_by(school_id=school_id).order_by(Period.order_index).all()

    class_id = request.args.get("class_id", type=int)
    section_id = request.args.get("section_id", type=int)

    section = None
    grid = {}
    if class_id and section_id:
        section = Section.query.filter_by(id=section_id, class_id=class_id).first()
        if section and not periods:
            flash("Define at least one period before building a timetable.", "warning")
            return redirect(url_for("academic.period_new"))
        if section:
            for p in periods:
                grid[p.id] = {d.value: None for d in DAYS_ORDER}
            entries = TimetableEntry.query.filter_by(session_id=active_session.id, section_id=section_id).all()
            for e in entries:
                grid[e.period_id][e.day_of_week.value] = e

    return render_template(
        "timetable/index.html", classes=classes, sections_by_class=sections_by_class,
        class_id=class_id, section_id=section_id, section=section, periods=periods,
        grid=grid, days=DAYS_ORDER,
    )


def _entry_context():
    """Shared lookup for the class/section/period/day a new entry is being added to."""
    class_id = request.values.get("class_id", type=int)
    section_id = request.values.get("section_id", type=int)
    period_id = request.values.get("period_id", type=int)
    day_raw = request.values.get("day")

    section = Section.query.filter_by(id=section_id, class_id=class_id).first_or_404()
    period = Period.query.filter_by(id=period_id, school_id=current_school_id()).first_or_404()
    day_enum = DayOfWeek(day_raw)  # raises ValueError on bad input; caller handles it
    return class_id, section, period, day_enum


@timetable_bp.route("/entry/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def entry_new():
    school_id = current_school_id()
    active_session = AcademicSession.query.filter_by(school_id=school_id, is_active=True).first()

    try:
        class_id, section, period, day_enum = _entry_context()
    except ValueError:
        flash("Invalid day.", "danger")
        return redirect(url_for("timetable.index"))

    subjects = Subject.query.filter_by(school_id=school_id, class_id=class_id).order_by(Subject.name).all()
    teachers = User.query.filter_by(school_id=school_id, role=UserRole.TEACHER).order_by(User.name).all()

    if request.method == "POST":
        subject_id = request.form.get("subject_id", type=int) or None
        teacher_id = request.form.get("teacher_id", type=int) or None
        room = request.form.get("room", "").strip() or None

        conflicts = find_conflicts(active_session.id, day_enum, period.id, section.id, teacher_id, room)
        if conflicts:
            for c in conflicts:
                flash(c, "danger")
        else:
            entry = TimetableEntry(
                school_id=school_id, session_id=active_session.id, class_id=class_id, section_id=section.id,
                period_id=period.id, day_of_week=day_enum, subject_id=subject_id, teacher_id=teacher_id, room=room,
            )
            db.session.add(entry)
            db.session.flush()
            log_action("timetable.created", "timetable_entries", entry.id,
                       new_value={"section_id": section.id, "day": day_enum.value, "period_id": period.id})
            db.session.commit()
            flash("Timetable entry saved.", "success")
            return redirect(url_for("timetable.index", class_id=class_id, section_id=section.id))

    return render_template(
        "timetable/entry_form.html", section=section, period=period, day=day_enum,
        subjects=subjects, teachers=teachers, title="New Timetable Entry", entry=None,
    )


@timetable_bp.route("/entry/<int:entry_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def entry_edit(entry_id):
    school_id = current_school_id()
    entry = TimetableEntry.query.filter_by(id=entry_id, school_id=school_id).first_or_404()

    subjects = Subject.query.filter_by(school_id=school_id, class_id=entry.class_id).order_by(Subject.name).all()
    teachers = User.query.filter_by(school_id=school_id, role=UserRole.TEACHER).order_by(User.name).all()

    if request.method == "POST":
        subject_id = request.form.get("subject_id", type=int) or None
        teacher_id = request.form.get("teacher_id", type=int) or None
        room = request.form.get("room", "").strip() or None

        conflicts = find_conflicts(
            entry.session_id, entry.day_of_week, entry.period_id, entry.section_id,
            teacher_id, room, exclude_entry_id=entry.id,
        )
        if conflicts:
            for c in conflicts:
                flash(c, "danger")
        else:
            old_value = {"subject_id": entry.subject_id, "teacher_id": entry.teacher_id, "room": entry.room}
            entry.subject_id = subject_id
            entry.teacher_id = teacher_id
            entry.room = room
            log_action("timetable.edited", "timetable_entries", entry.id, old_value=old_value,
                       new_value={"subject_id": subject_id, "teacher_id": teacher_id, "room": room})
            db.session.commit()
            flash("Timetable entry updated.", "success")
            return redirect(url_for("timetable.index", class_id=entry.class_id, section_id=entry.section_id))

    return render_template(
        "timetable/entry_form.html", section=entry.section, period=entry.period, day=entry.day_of_week,
        subjects=subjects, teachers=teachers, title="Edit Timetable Entry", entry=entry,
    )


@timetable_bp.route("/entry/<int:entry_id>/delete", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN)
def entry_delete(entry_id):
    entry = TimetableEntry.query.filter_by(id=entry_id, school_id=current_school_id()).first_or_404()
    class_id, section_id = entry.class_id, entry.section_id

    log_action("timetable.deleted", "timetable_entries", entry.id,
               old_value={"subject_id": entry.subject_id, "teacher_id": entry.teacher_id})
    db.session.delete(entry)
    db.session.commit()

    flash("Timetable entry removed.", "info")
    return redirect(url_for("timetable.index", class_id=class_id, section_id=section_id))


@timetable_bp.route("/teacher/<int:user_id>")
@login_required
@role_required(UserRole.ADMIN, UserRole.TEACHER)
def teacher_timetable(user_id):
    school_id = current_school_id()
    if current_user.role == UserRole.TEACHER and current_user.id != user_id:
        abort(403)

    teacher = User.query.filter_by(id=user_id, school_id=school_id, role=UserRole.TEACHER).first_or_404()
    active_session = AcademicSession.query.filter_by(school_id=school_id, is_active=True).first()
    periods = Period.query.filter_by(school_id=school_id).order_by(Period.order_index).all()

    grid = {p.id: {d.value: None for d in DAYS_ORDER} for p in periods}
    if active_session:
        entries = TimetableEntry.query.filter_by(session_id=active_session.id, teacher_id=user_id).all()
        for e in entries:
            grid[e.period_id][e.day_of_week.value] = e

    return render_template(
        "timetable/teacher_view.html", teacher=teacher, periods=periods, grid=grid, days=DAYS_ORDER,
    )


@timetable_bp.route("/daily")
@login_required
@role_required(UserRole.ADMIN, UserRole.TEACHER)
def daily_view():
    school_id = current_school_id()
    active_session = AcademicSession.query.filter_by(school_id=school_id, is_active=True).first()
    if not active_session:
        flash("No active academic session.", "warning")
        return redirect(url_for("timetable.index"))

    try:
        day_enum = DayOfWeek(request.args.get("day") or DAYS_ORDER[0].value)
    except ValueError:
        day_enum = DAYS_ORDER[0]

    class_id = request.args.get("class_id", type=int)

    query = TimetableEntry.query.filter_by(session_id=active_session.id, day_of_week=day_enum)
    if class_id:
        query = query.filter_by(class_id=class_id)
    entries = query.join(Period, TimetableEntry.period_id == Period.id).order_by(Period.order_index).all()

    classes = SchoolClass.query.filter_by(school_id=school_id, session_id=active_session.id).order_by(SchoolClass.name).all()

    return render_template(
        "timetable/daily_view.html", entries=entries, day=day_enum, days=DAYS_ORDER,
        classes=classes, class_id=class_id,
    )
