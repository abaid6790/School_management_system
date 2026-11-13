"""
Calendar helpers. Everything is derived from the events table on demand — the month
grid, which days are closed, how many events fall on a day — nothing is stored.
"""
import calendar
from datetime import date, time, timedelta

from app.models import Event
from app.models.enums import EventType

TYPE_COLORS = {
    EventType.HOLIDAY: "danger", EventType.EXAM: "warning", EventType.SPORTS: "success",
    EventType.CULTURAL: "info", EventType.MEETING: "primary", EventType.TRIP: "secondary", EventType.OTHER: "dark",
}
MAX_SPAN_DAYS = 365          # keeps per-day calendar expansion bounded
MIN_YEAR, MAX_YEAR = 2000, 2100


def clamp_month(year, month, today=None):
    """Validated (year, month) from query-string input; falls back to the current month."""
    today = today or date.today()
    try:
        y, m = int(year), int(month)
    except (TypeError, ValueError):
        return today.year, today.month
    if not (MIN_YEAR <= y <= MAX_YEAR and 1 <= m <= 12):
        return today.year, today.month
    return y, m


def shift_month(year, month, delta):
    """(year, month) moved by delta months, or None if outside the supported range."""
    index = year * 12 + (month - 1) + delta
    y, m = divmod(index, 12)
    m += 1
    return (y, m) if MIN_YEAR <= y <= MAX_YEAR else None


def month_weeks(year, month):
    """Monday-first weeks, each a list of 7 dates (including spill-over days)."""
    return calendar.Calendar(firstweekday=0).monthdatescalendar(year, month)


def _sort_key(event):
    return (event.start_date, event.start_time or time.min, event.title.lower())


def events_overlapping(school_id, start, end):
    events = Event.query.filter(
        Event.school_id == school_id, Event.start_date <= end, Event.end_date >= start,
    ).all()
    return sorted(events, key=_sort_key)


def events_by_day(events, first, last):
    """{date: [events]} for every day of [first, last] that each (multi-day) event covers."""
    by_day = {}
    for event in events:
        day, stop = max(event.start_date, first), min(event.end_date, last)
        while day <= stop:
            by_day.setdefault(day, []).append(event)
            day += timedelta(days=1)
    for day_events in by_day.values():
        day_events.sort(key=_sort_key)
    return by_day


def holidays_on(school_id, day):
    return Event.query.filter(
        Event.school_id == school_id, Event.is_holiday.is_(True), Event.start_date <= day, Event.end_date >= day,
    ).order_by(Event.start_date).all()


def time_label(event) -> str:
    if event.start_time and event.end_time:
        return f"{event.start_time.strftime('%H:%M')}–{event.end_time.strftime('%H:%M')}"
    if event.start_time:
        return f"from {event.start_time.strftime('%H:%M')}"
    return "All day"


def date_label(event) -> str:
    if event.start_date == event.end_date:
        return event.start_date.strftime("%d %b %Y")
    if event.start_date.year == event.end_date.year:
        return f"{event.start_date.strftime('%d %b')} – {event.end_date.strftime('%d %b %Y')}"
    return f"{event.start_date.strftime('%d %b %Y')} – {event.end_date.strftime('%d %b %Y')}"
