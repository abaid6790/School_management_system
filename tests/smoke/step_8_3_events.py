# Smoke test (see tests/smoke/README.md). Safe by construction: it only ever uses a temporary SQLite file, or the
# database named in TEST_DB -- never DATABASE_URL from your environment or .env.
import os, sys, tempfile
_TMP = tempfile.gettempdir().replace(chr(92), "/")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault("NOTIFICATIONS_EMAIL_SYNC", "True")
_url = os.environ.get("TEST_DB")
if _url and not _url.startswith("sqlite") and "test" not in _url.rsplit("/", 1)[-1].lower():
    sys.exit("Refusing to run: these tests create and DROP tables. Point TEST_DB at a throwaway database whose name "
             "contains 'test' (for example postgresql+psycopg2://user:pw@localhost/sms_test).")
import os, re, sys, datetime as dt
os.environ.update(SECRET_KEY="x", DATABASE_URL=f"sqlite:///{_TMP}/p83.db", MAIL_USERNAME="x@e.com", MAIL_PASSWORD="x")
if os.path.exists(f"{_TMP}/p83.db"): os.remove(f"{_TMP}/p83.db")
from unittest.mock import patch
from app import create_app
from app.extensions import db, mail
from app.models import User, Event, AuditLog
from app.models.enums import UserRole, EventType

app = create_app("development"); app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
with app.app_context(): db.create_all()
FR = dict(follow_redirects=True)
results = []
def ok(label, cond): print(("PASS " if cond else "FAIL ") + label); results.append(bool(cond))

def register(client, school, slug, email):
    with patch.object(mail, "send", return_value=None):
        client.post("/auth/register", data={"school_name": school, "school_slug": slug, "admin_name": "Admin",
            "admin_email": email, "password": "TestPass123!", "confirm_password": "TestPass123!"}, **FR)
    with app.app_context(): tok = User.query.filter_by(email=email).first().verification_token
    client.get(f"/auth/verify/{tok}", **FR); client.post("/auth/login", data={"email": email, "password": "TestPass123!"}, **FR)

admin = app.test_client(); register(admin, "Event School", "event-school", "admin@es.com")
admin.post("/academic/sessions/new", data={"name": "2026-27", "start_date": "2026-08-01", "end_date": "2027-06-30", "is_active": "y"}, **FR)
with app.app_context():
    sid = User.query.filter_by(email="admin@es.com").first().school_id
    for name, role in [("teacher", UserRole.TEACHER), ("accountant", UserRole.ACCOUNTANT), ("reception", UserRole.RECEPTIONIST)]:
        u = User(school_id=sid, name=name.title(), email=f"{name}@es.com", role=role, is_verified=True); u.set_password("StaffPass123!"); db.session.add(u)
    db.session.commit()
staff = {}
for name in ("teacher", "accountant", "reception"):
    c = app.test_client(); c.post("/auth/login", data={"email": f"{name}@es.com", "password": "StaffPass123!"}, **FR); staff[name] = c

def add(title, start, end="", etype="other", **extra):
    d = {"title": title, "event_type": etype, "start_date": start, "end_date": end}; d.update(extra)
    return admin.post("/events/new", data=d, **FR)
def eid(title):
    with app.app_context(): return Event.query.filter_by(title=title).first().id
def get_event(title):
    with app.app_context():
        e = Event.query.filter_by(title=title).first(); return e
def month_html(c, y, m): return c.get(f"/events/?year={y}&month={m}").data.decode()
def cell(html, iso):
    m = re.search(rf'data-date="{iso}".*?</td>', html, re.S); return m.group(0) if m else ""
def count_events():
    with app.app_context(): return Event.query.count()

# 1 -- single-day
add("EV-single", "2026-11-05", etype="meeting")
e = get_event("EV-single")
ok("single-day event: blank end date defaults to start", e.end_date == e.start_date == dt.date(2026, 11, 5))
nov = month_html(admin, 2026, 11)
ok("shows in its own day cell only", "EV-single" in cell(nov, "2026-11-05") and "EV-single" not in cell(nov, "2026-11-06"))
ok("not in an unrelated month", "EV-single" not in month_html(admin, 2026, 9))

# 2 -- multi-day and month boundary
add("EV-multi", "2026-11-10", "2026-11-12", "sports")
nov = month_html(admin, 2026, 11)
ok("multi-day event appears on each of its days", all("EV-multi" in cell(nov, f"2026-11-{d}") for d in (10, 11, 12)))
ok("...and not the days around it", "EV-multi" not in cell(nov, "2026-11-09") and "EV-multi" not in cell(nov, "2026-11-13"))
add("EV-span", "2026-10-30", "2026-11-02", "trip")
oct_ = month_html(admin, 2026, 10); nov = month_html(admin, 2026, 11)
ok("boundary event in October grid: Oct 30, 31 and spill-over Nov 1, not Nov 2",
   all("EV-span" in cell(oct_, d) for d in ("2026-10-30", "2026-10-31", "2026-11-01")) and "EV-span" not in cell(oct_, "2026-11-02") if cell(oct_, "2026-11-02") else all("EV-span" in cell(oct_, d) for d in ("2026-10-30", "2026-10-31", "2026-11-01")))
ok("boundary event in November grid: Oct 30 .. Nov 2, not Nov 3",
   all("EV-span" in cell(nov, d) for d in ("2026-10-30", "2026-10-31", "2026-11-01", "2026-11-02")) and "EV-span" not in cell(nov, "2026-11-03"))

# 3 -- holidays
add("EV-holiday", "2026-11-20", etype="holiday")
ok("a HOLIDAY-type event is forced to 'school closed'", get_event("EV-holiday").is_holiday is True)
add("EV-examclosed", "2026-11-25", etype="exam", is_holiday="y")
ok("a non-holiday type can still mark the school closed", get_event("EV-examclosed").is_holiday is True)
add("EV-open", "2026-11-26", etype="cultural")
ok("an ordinary event does not close the school", get_event("EV-open").is_holiday is False)
nov = month_html(admin, 2026, 11)
ok("closed days are flagged in the grid", 'data-holiday="1"' in cell(nov, "2026-11-20") and 'data-holiday="1"' in cell(nov, "2026-11-25"))
ok("open days are not flagged", 'data-holiday' not in cell(nov, "2026-11-26") and 'data-holiday' not in cell(nov, "2026-11-05"))

# 4 -- times
add("EV-timed", "2026-11-15", etype="cultural", start_time="09:00", end_time="15:00")
add("EV-startonly", "2026-11-16", start_time="08:30")
ok("time range shown", "09:00–15:00" in admin.get(f"/events/{eid('EV-timed')}").data.decode())
ok("start-only shown as 'from'", "from 08:30" in admin.get(f"/events/{eid('EV-startonly')}").data.decode())
ok("no times -> All day", "All day" in admin.get(f"/events/{eid('EV-single')}").data.decode())

# 5 -- validation
n0 = count_events()
r = add("EV-bad1", "2026-11-10", "2026-11-09");            ok("end before start rejected", b"end date can" in r.data)
r = add("EV-bad2", "2026-11-10", start_time="10:00", end_time="09:00"); ok("same-day end time <= start rejected", b"end time must be after" in r.data)
r = add("EV-bad3", "2026-11-10", end_time="09:00");        ok("end time without start time rejected", b"Add a start time" in r.data)
r = add("EV-bad4", "2026-01-01", "2027-06-01");            ok("event longer than a year rejected", b"at most one year" in r.data)
r = admin.post("/events/new", data={"title": "", "event_type": "other", "start_date": "2026-11-10"}, **FR); ok("missing title rejected", b"This field is required" in r.data)
r = admin.post("/events/new", data={"title": "x", "event_type": "bogus", "start_date": "2026-11-10"}, **FR); ok("unknown event type rejected", b"Not a valid choice" in r.data)
r = admin.post("/events/new", data={"title": "x", "event_type": "other", "start_date": ""}, **FR); ok("missing start date rejected", b"This field is required" in r.data)
ok("none of the invalid events were saved", count_events() == n0)
add("EV-multiday-times", "2026-12-05", "2026-12-06", start_time="15:00", end_time="09:00")
ok("multi-day event may end earlier in the day than it starts", get_event("EV-multiday-times") is not None)

# 6 -- overflow
for i in range(1, 6): add(f"EV-ov{i}", "2026-11-28")
nov = month_html(admin, 2026, 11); c28 = cell(nov, "2026-11-28")
ok("busy day shows exactly 3 events AND '+2 more'", "+2 more" in c28 and sum(1 for i in range(1, 6) if f">EV-ov{i}<" in c28) == 3)
ok("'+N more' links to that day's list", "start=2026-11-28" in c28 and "end=2026-11-28" in c28)
lst = admin.get("/events/list?start=2026-11-28&end=2026-11-28").data.decode()
ok("that list shows all five", all(f"EV-ov{i}" in lst for i in range(1, 6)))

# 7 -- admin-only affordances and prefill
ok("new-event form can be prefilled from a day", 'value="2026-11-05"' in admin.get("/events/new?date=2026-11-05").data.decode())
ok("admin calendar has '+' add links", "Add an event on this day" in month_html(admin, 2026, 11))
ok("staff calendar has none", "Add an event on this day" not in month_html(staff["teacher"], 2026, 11))

# 8 -- roles
for name, c in staff.items():
    ok(f"{name}: can view calendar, list and detail",
       "EV-single" in month_html(c, 2026, 11) and c.get("/events/list?start=2026-11-01").status_code == 200 and c.get(f"/events/{eid('EV-single')}").status_code == 200)
    codes = [c.get("/events/new").status_code, c.post("/events/new", data={"title": "x"}).status_code,
             c.get(f"/events/{eid('EV-single')}/edit").status_code, c.post(f"/events/{eid('EV-single')}/delete").status_code]
    ok(f"{name}: new/edit/delete all 403", codes == [403] * 4)

# 9 -- month navigation
ok("explicit month works", "December 2026" in month_html(admin, 2026, 12))
today = dt.date.today(); cur = today.strftime("%B %Y")
ok("month=13 falls back to the current month", cur in admin.get("/events/?year=2026&month=13").data.decode())
ok("non-numeric month falls back", cur in admin.get("/events/?month=abc").data.decode())
ok("year out of range falls back", cur in admin.get("/events/?year=1999&month=5").data.decode())
ok("no 'previous' button before the supported range", "chevron-left" not in admin.get("/events/?year=2000&month=1").data.decode())
ok("no 'next' button after the supported range", "chevron-right" not in admin.get("/events/?year=2100&month=12").data.decode())

# 10 -- list view
past = (today - dt.timedelta(days=30)).isoformat(); fut = (today + dt.timedelta(days=10)).isoformat()
add("EV-pastlist", past); add("EV-futlist", fut, etype="exam")
dl = admin.get("/events/list").data.decode()
ok("default list = upcoming only", "EV-futlist" in dl and "EV-pastlist" not in dl)
ok("earlier 'from' includes past events", "EV-pastlist" in admin.get(f"/events/list?start={past}").data.decode())
tl = admin.get(f"/events/list?start={past}&type=exam").data.decode()
ok("type filter", "EV-futlist" in tl and "EV-pastlist" not in tl)
ok("'to' filter", "EV-futlist" not in admin.get(f"/events/list?start={past}&end={(today).isoformat()}").data.decode())
ok("garbage dates don't crash", admin.get("/events/list?start=nope&end=also-nope").status_code == 200)

# 11 -- edit
eid_t = eid("EV-timed")
form = admin.get(f"/events/{eid_t}/edit").data.decode()
ok("edit form is pre-filled (title, dates, times, type)", all(s in form for s in ("EV-timed", 'value="2026-11-15"', 'value="09:00"', 'value="15:00"')) and re.search(r'<option[^>]*selected[^>]*>Cultural', form) is not None)
admin.post(f"/events/{eid_t}/edit", data={"title": "EV-timed2", "event_type": "cultural", "start_date": "2026-11-15", "end_date": "2026-11-17", "start_time": "10:00", "end_time": "11:00", "location": "Hall"}, **FR)
e = get_event("EV-timed2")
ok("edit saves changes", e is not None and e.end_date == dt.date(2026, 11, 17) and e.start_time == dt.time(10, 0) and e.location == "Hall")
single = admin.get(f"/events/{eid('EV-single')}/edit").data.decode()
end_tag = re.search(r'<input[^>]*name="end_date"[^>]*>', single).group(0)
ok("a one-day event's end-date box edits back as blank", not re.search(r'value="\d', end_tag))
r = admin.post(f"/events/{eid_t}/edit", data={"title": "EV-timed2", "event_type": "cultural", "start_date": "2026-11-15", "end_date": "2026-11-10"}, **FR)
ok("edit is validated too", b"end date can" in r.data)

# 12 -- escaping
add("EV-<script>alert(1)</script>", "2026-11-03", description="<img src=x onerror=alert(1)> hi")
nov = month_html(admin, 2026, 11)
ok("calendar escapes titles", "<script>alert(1)" not in nov and "&lt;script&gt;" in nov)
xid = eid("EV-<script>alert(1)</script>")
det = admin.get(f"/events/{xid}").data.decode()
ok("detail escapes description and title", "<img src=x" not in det and "&lt;img" in det and "<script>alert(1)" not in det)

# 13 -- attendance banner
add("EV-closure", "2026-12-01", "2026-12-03", "holiday")
sa = lambda c, d: c.get(f"/attendance/mark?date={d}", **FR).data.decode()
ok("student attendance page warns on a closed day", "marks this date as closed" in sa(admin, "2026-11-20") and "EV-holiday" in sa(admin, "2026-11-20"))
ok("...on every day of a multi-day closure", all("EV-closure" in sa(admin, f"2026-12-0{d}") for d in (1, 2, 3)))
ok("...but not the day after, nor on an ordinary event day", "marks this date as closed" not in sa(admin, "2026-12-04") and "marks this date as closed" not in sa(admin, "2026-11-05"))
ok("a teacher marking attendance sees the warning too", "marks this date as closed" in sa(staff["teacher"], "2026-11-20"))
ok("teacher-attendance page warns as well", "marks this date as closed" in admin.get("/teacher-attendance/mark?date=2026-11-20", **FR).data.decode())

# 14 -- delete + audit
did = eid("EV-open")
admin.post(f"/events/{did}/delete", **FR)
ok("delete removes the event", get_event("EV-open") is None and "EV-open" not in month_html(admin, 2026, 11))
with app.app_context(): acts = {a.action for a in AuditLog.query.filter(AuditLog.action.like("event.%")).all()}
ok("audit trail has created/edited/deleted", {"event.created", "event.edited", "event.deleted"} <= acts)

# 15 -- tenant isolation
other = app.test_client(); register(other, "Other School", "other-school", "admin@other.com")
ok("other school can't open our event", other.get(f"/events/{eid('EV-single')}").status_code == 404)
ok("other school's calendar is empty", "EV-" not in month_html(other, 2026, 11))
ok("other school can't delete or edit ours", other.post(f"/events/{eid('EV-single')}/delete").status_code == 404 and other.get(f"/events/{eid('EV-single')}/edit").status_code == 404)
ok("other school's attendance page doesn't inherit our holidays", "EV-holiday" not in other.get("/attendance/mark?date=2026-11-20", **FR).data.decode())
ok("our event survived the attempts", get_event("EV-single") is not None)

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
