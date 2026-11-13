from datetime import date, datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Event
from app.models.enums import UserRole, EventType
from app.forms.event import EventForm
from app.utils.decorators import role_required
from app.utils.tenant import current_school_id
from app.services import notification_service as ns
from app.services.audit_service import log_action
from app.services.event_service import (
    TYPE_COLORS, MAX_SPAN_DAYS, clamp_month, shift_month, month_weeks, events_overlapping, events_by_day,
    time_label, date_label,
)

events_bp = Blueprint("events", __name__, url_prefix="/events")

ALL_STAFF = (UserRole.ADMIN, UserRole.TEACHER, UserRole.ACCOUNTANT, UserRole.RECEPTIONIST)
LIST_LIMIT = 200


def _parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date() if value else None
    except ValueError:
        return None


def _valid(form):
    """Cross-field rules the single-field validators can't express. Returns True when fine."""
    start = form.start_date.data
    end = form.end_date.data or start
    good = True
    if end < start:
        form.end_date.errors.append("The end date can't be before the start date.")
        good = False
    elif (end - start).days > MAX_SPAN_DAYS:
        form.end_date.errors.append("An event can span at most one year.")
        good = False
    if form.end_time.data and not form.start_time.data:
        form.start_time.errors.append("Add a start time before setting an end time.")
        good = False
    elif form.start_time.data and form.end_time.data and end == start and form.end_time.data <= form.start_time.data:
        form.end_time.errors.append("The end time must be after the start time.")
        good = False
    return good


def _apply(form, event):
    event_type = EventType(form.event_type.data)
    event.title = form.title.data.strip()
    event.event_type = event_type
    event.start_date = form.start_date.data
    event.end_date = form.end_date.data or form.start_date.data
    event.start_time = form.start_time.data
    event.end_time = form.end_time.data
    event.location = (form.location.data or "").strip() or None
    event.description = (form.description.data or "").strip() or None
    event.is_holiday = bool(form.is_holiday.data) or event_type == EventType.HOLIDAY


@events_bp.route("/")
@login_required
@role_required(*ALL_STAFF)
def calendar_view():
    school_id = current_school_id()
    today = date.today()
    year, month = clamp_month(request.args.get("year"), request.args.get("month"), today)
    weeks = month_weeks(year, month)
    first, last = weeks[0][0], weeks[-1][-1]
    by_day = events_by_day(events_overlapping(school_id, first, last), first, last)
    holiday_days = {d for d, evs in by_day.items() if any(e.is_holiday for e in evs)}
    return render_template(
        "events/calendar.html", year=year, month=month, weeks=weeks, by_day=by_day, holiday_days=holiday_days,
        today=today, month_name=date(year, month, 1).strftime("%B %Y"),
        prev_ym=shift_month(year, month, -1), next_ym=shift_month(year, month, 1),
        colors=TYPE_COLORS, is_admin=current_user.role == UserRole.ADMIN,
        legend=[(t, TYPE_COLORS[t]) for t in EventType],
    )


@events_bp.route("/list")
@login_required
@role_required(*ALL_STAFF)
def list_events():
    school_id = current_school_id()
    start = _parse_date(request.args.get("start")) or date.today()
    end = _parse_date(request.args.get("end"))
    type_value = request.args.get("type", "")

    query = Event.query.filter(Event.school_id == school_id, Event.end_date >= start)
    if end:
        query = query.filter(Event.start_date <= end)
    if type_value in {t.value for t in EventType}:
        query = query.filter(Event.event_type == EventType(type_value))
    events = query.order_by(Event.start_date, Event.start_time, Event.title).limit(LIST_LIMIT).all()
    return render_template(
        "events/list.html", events=events, start=start, end=end, type_value=type_value, types=list(EventType),
        colors=TYPE_COLORS, time_label=time_label, date_label=date_label,
        is_admin=current_user.role == UserRole.ADMIN, limit=LIST_LIMIT,
    )


@events_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def new_event():
    form = EventForm()
    if request.method == "GET":
        prefill = _parse_date(request.args.get("date"))
        if prefill:
            form.start_date.data = prefill
    if form.validate_on_submit() and _valid(form):
        event = Event(school_id=current_school_id(), created_by_id=current_user.id)
        _apply(form, event)
        db.session.add(event)
        db.session.flush()
        log_action("event.created", "events", event.id,
                   new_value={"title": event.title, "type": event.event_type.value, "start": event.start_date.isoformat()})
        db.session.commit()
        flash(f"Event added to the calendar. {ns.note(ns.notify_event_created(event, current_user.id))}".strip(), "success")
        return redirect(url_for("events.view_event", event_id=event.id))
    return render_template("events/form.html", form=form, title="New Event", event=None)


@events_bp.route("/<int:event_id>")
@login_required
@role_required(*ALL_STAFF)
def view_event(event_id):
    event = Event.query.filter_by(id=event_id, school_id=current_school_id()).first_or_404()
    return render_template(
        "events/view.html", event=event, color=TYPE_COLORS[event.event_type], when=date_label(event),
        at=time_label(event), is_admin=current_user.role == UserRole.ADMIN,
    )


@events_bp.route("/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def edit_event(event_id):
    event = Event.query.filter_by(id=event_id, school_id=current_school_id()).first_or_404()
    form = EventForm()
    if request.method == "GET":
        form.title.data = event.title
        form.event_type.data = event.event_type.value
        form.start_date.data = event.start_date
        form.end_date.data = event.end_date if event.end_date != event.start_date else None
        form.start_time.data = event.start_time
        form.end_time.data = event.end_time
        form.location.data = event.location
        form.description.data = event.description
        form.is_holiday.data = event.is_holiday
    if form.validate_on_submit() and _valid(form):
        _apply(form, event)
        log_action("event.edited", "events", event.id,
                   new_value={"title": event.title, "type": event.event_type.value, "start": event.start_date.isoformat()})
        db.session.commit()
        flash("Event updated.", "success")
        return redirect(url_for("events.view_event", event_id=event.id))
    return render_template("events/form.html", form=form, title="Edit Event", event=event)


@events_bp.route("/<int:event_id>/delete", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN)
def delete_event(event_id):
    event = Event.query.filter_by(id=event_id, school_id=current_school_id()).first_or_404()
    log_action("event.deleted", "events", event.id, old_value={"title": event.title, "start": event.start_date.isoformat()})
    db.session.delete(event)
    db.session.commit()
    flash("Event deleted.", "info")
    return redirect(url_for("events.calendar_view"))
