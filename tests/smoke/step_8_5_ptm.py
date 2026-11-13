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
DB = os.environ.get("TEST_DB", f"sqlite:///{_TMP}/p85.db")
os.environ.update(SECRET_KEY="x", DATABASE_URL=DB, MAIL_USERNAME="x@e.com", MAIL_PASSWORD="x")
if DB.startswith("sqlite") and os.path.exists(f"{_TMP}/p85.db"): os.remove(f"{_TMP}/p85.db")
from unittest.mock import patch
from app import create_app
from app.extensions import db, mail
from app.models import (User, SchoolClass, Section, Student, Guardian, StudentGuardian, PTMMeeting, PTMAppointment,
                        AcademicSession, AuditLog)
from app.models.enums import UserRole, StudentStatus, MeetingStatus, AppointmentStatus, GuardianRelation

app = create_app("development"); app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
with app.app_context(): db.drop_all(); db.create_all()
FR = dict(follow_redirects=True)
results = []
def ok(label, cond): print(("PASS " if cond else "FAIL ") + label); results.append(bool(cond))
today = dt.date.today(); D = lambda n: (today + dt.timedelta(days=n)).isoformat()

def register(client, school, slug, email):
    with patch.object(mail, "send", return_value=None):
        client.post("/auth/register", data={"school_name": school, "school_slug": slug, "admin_name": "Admin",
            "admin_email": email, "password": "TestPass123!", "confirm_password": "TestPass123!"}, **FR)
    with app.app_context(): tok = User.query.filter_by(email=email).first().verification_token
    client.get(f"/auth/verify/{tok}", **FR); client.post("/auth/login", data={"email": email, "password": "TestPass123!"}, **FR)

admin = app.test_client(); register(admin, "Meeting School", "meeting-school", "admin@pm.com")
admin.post("/academic/sessions/new", data={"name": "2026-27", "start_date": "2026-08-01", "end_date": "2027-06-30", "is_active": "y"}, **FR)
for n in ("Grade 8", "Grade 9"): admin.post("/academic/classes/new", data={"name": n, "capacity": "40", "class_teacher_id": "0"}, **FR)
with app.app_context():
    sid = User.query.filter_by(email="admin@pm.com").first().school_id
    c8 = SchoolClass.query.filter_by(name="Grade 8").first().id; c9 = SchoolClass.query.filter_by(name="Grade 9").first().id
    session_id = AcademicSession.query.first().id
for cid, name in ((c8, "A"), (c8, "B"), (c9, "A")):
    admin.post(f"/academic/classes/{cid}/sections/new", data={"name": name, "capacity": "40", "class_teacher_id": "0"}, **FR)
with app.app_context():
    s8a = Section.query.filter_by(class_id=c8, name="A").first().id; s8b = Section.query.filter_by(class_id=c8, name="B").first().id
    s9a = Section.query.filter_by(class_id=c9, name="A").first().id
    def mkuser(name, role):
        u = User(school_id=sid, name=name, email=f"{name.lower()}@pm.com", role=role, is_verified=True); u.set_password("StaffPass123!"); db.session.add(u); db.session.flush(); return u.id
    t1, t2, t3 = mkuser("Tea1", UserRole.TEACHER), mkuser("Tea2", UserRole.TEACHER), mkuser("Tea3", UserRole.TEACHER)
    acct, recep = mkuser("Acct", UserRole.ACCOUNTANT), mkuser("Recep", UserRole.RECEPTIONIST)
    db.session.commit()
for name, (cid, sec, roll) in {"Stu One": (c8, s8a, "1"), "Stu Two": (c8, s8a, "2"), "Stu Three": (c8, s8b, "1"), "Stu Four": (c9, s9a, "1"), "Stu Five": (c8, s8a, "3")}.items():
    admin.post("/students/new", data={"admission_number": name.replace(" ", "-"), "admission_date": "2026-08-15", "name": name, "class_id": str(cid), "section_id": str(sec), "roll_number": roll}, **FR)
with app.app_context():
    stu = {s.name: s.id for s in Student.query.all()}
    Student.query.filter_by(name="Stu Five").first().status = StudentStatus.INACTIVE
    g_main = Guardian(school_id=sid, father_name="Ahmed One", mother_name="Sara One", phone="0300"); g_other = Guardian(school_id=sid, father_name="Other Dad", phone="0301")
    db.session.add_all([g_main, g_other]); db.session.flush()
    db.session.add(StudentGuardian(student_id=stu["Stu One"], guardian_id=g_main.id, relationship_to_student=GuardianRelation.FATHER, is_primary_contact=True))
    db.session.add(StudentGuardian(student_id=stu["Stu One"], guardian_id=g_other.id, relationship_to_student=GuardianRelation.MOTHER))
    db.session.add(StudentGuardian(student_id=stu["Stu Two"], guardian_id=g_other.id, relationship_to_student=GuardianRelation.FATHER, is_primary_contact=True))
    db.session.commit(); gA, gB = g_main.id, g_other.id
def login(email):
    c = app.test_client(); c.post("/auth/login", data={"email": email, "password": "StaffPass123!"}, **FR); return c
T1, T2, T3, ACC, REC = login("tea1@pm.com"), login("tea2@pm.com"), login("tea3@pm.com"), login("acct@pm.com"), login("recep@pm.com")

def mdata(**kw):
    d = dict(title="PTM", description="", meeting_date=D(7), start_time="09:00", end_time="10:00", slot_minutes=15, location="Hall", class_id=0, section_id=0); d.update(kw); return d
def make(client, **kw): return client.post("/ptm/new", data=mdata(**kw), **FR)
def meeting(title):
    with app.app_context(): return PTMMeeting.query.filter_by(title=title).first()
def mid(title): return meeting(title).id
def book(client, m, teacher, student, slot, guardian="", notes=""):
    return client.post(f"/ptm/{m}/book", data={"teacher_id": teacher, "student_id": stu.get(student, student), "slot": slot, "guardian_id": guardian, "notes": notes}, **FR)
def appts(m, include_cancelled=True):
    with app.app_context():
        q = PTMAppointment.query.filter_by(meeting_id=m).order_by(PTMAppointment.id).all()
        return [(a.teacher.name, a.student.name, a.slot_start.strftime("%H:%M"), a.status) for a in q if include_cancelled or a.status != AppointmentStatus.CANCELLED]
def aid(m, student, slot=None, status=None):
    with app.app_context():
        for a in PTMAppointment.query.filter_by(meeting_id=m, student_id=stu[student]).order_by(PTMAppointment.id).all():
            if (slot is None or a.slot_start.strftime("%H:%M") == slot) and (status is None or a.status == status): return a.id
def act(client, a, action, **extra): return client.post(f"/ptm/appointment/{a}/update", data={"action": action, **extra}, **FR)
def status_of(a):
    with app.app_context(): return db.session.get(PTMAppointment, a).status
import json
def slots_in_page(html):
    m = re.search(r"const SLOTS = (.*?);\n", html); return [label for _v, label in json.loads(m.group(1))] if m else []

# ===== A. creating meetings and the slot grid
r = make(admin, title="PTM-main")
page = admin.get(f"/ptm/{mid('PTM-main')}").data.decode()
ok("meeting created; 4 slots derived from 09:00-10:00 / 15 min", b"4 appointment slots" in r.data and slots_in_page(page) == ["09:00–09:15", "09:15–09:30", "09:30–09:45", "09:45–10:00"])
make(admin, title="PTM-odd", end_time="10:10", slot_minutes=20)
odd = admin.get(f"/ptm/{mid('PTM-odd')}").data.decode()
ok("a window that doesn't divide evenly drops the partial slot", slots_in_page(odd) == ["09:00–09:20", "09:20–09:40", "09:40–10:00"])
n0 = len(db.session.query(PTMMeeting).all()) if False else 0
r = make(admin, title="PTM-bad1", start_time="10:00", end_time="09:00");   ok("end before start rejected", b"end time must be after" in r.data and meeting("PTM-bad1") is None)
r = make(admin, title="PTM-bad2", start_time="09:00", end_time="09:05", slot_minutes=10); ok("window shorter than one appointment rejected", b"shorter than one appointment" in r.data)
r = make(admin, title="PTM-bad3", meeting_date=D(-1));                      ok("past date rejected", b"can&#39;t be in the past" in r.data or b"be in the past" in r.data)
r = make(admin, title="PTM-bad4", slot_minutes=4);                          ok("4-minute appointments rejected", meeting("PTM-bad4") is None)
r = make(admin, title="PTM-bad5", slot_minutes=121);                        ok("121-minute appointments rejected", meeting("PTM-bad5") is None)
r = make(admin, title="");                                                  ok("missing title rejected", b"This field is required" in r.data)
r = make(admin, title="PTM-bad6", section_id=s8a);                          ok("section without a class rejected", b"Choose a class" in r.data and meeting("PTM-bad6") is None)
r = make(admin, title="PTM-bad7", class_id=c8, section_id=s9a);             ok("section of another class rejected", meeting("PTM-bad7") is None)
other = app.test_client(); register(other, "Other School", "other-school", "admin@other.com")
ok("no active session -> told to create one", b"activate an academic session" in other.get("/ptm/new", **FR).data)
for name, c in (("teacher", T1), ("receptionist", REC)):
    ok(f"{name}: can view list and meeting", c.get("/ptm/").status_code == 200 and c.get(f"/ptm/{mid('PTM-main')}").status_code == 200)
    ok(f"{name}: new/edit/complete/cancel are 403", [c.get("/ptm/new").status_code, c.get(f"/ptm/{mid('PTM-main')}/edit").status_code, c.post(f"/ptm/{mid('PTM-main')}/complete").status_code, c.post(f"/ptm/{mid('PTM-main')}/cancel").status_code] == [403] * 4)
ok("accountant: no access at all", [ACC.get("/ptm/").status_code, ACC.get(f"/ptm/{mid('PTM-main')}").status_code, ACC.get("/ptm/new").status_code] == [403] * 3)
with app.app_context():
    db.session.add(PTMMeeting(school_id=sid, session_id=session_id, title="PTM-past", meeting_date=today - dt.timedelta(days=10), start_time=dt.time(9), end_time=dt.time(10), slot_minutes=15)); db.session.commit()
lst = admin.get("/ptm/").data.decode()
ok("list defaults to upcoming", "PTM-main" in lst and "PTM-past" not in lst)
ok("past / all filters", "PTM-past" in admin.get("/ptm/?when=past").data.decode() and "PTM-main" not in admin.get("/ptm/?when=past").data.decode() and "PTM-past" in admin.get("/ptm/?when=all").data.decode())

# ===== B. booking
M = mid("PTM-main")
r = book(admin, M, t1, "Stu One", "09:00", guardian=gA, notes="wants to discuss maths")
ok("admin books teacher+student+slot with a guardian", appts(M) == [("Tea1", "Stu One", "09:00", AppointmentStatus.SCHEDULED)] and b"Appointment booked" in r.data)
page = admin.get(f"/ptm/{M}").data.decode()
ok("schedule shows the student under the teacher with the guardian's label", "Tea1" in page and "Stu One" in page and "Ahmed One (father)" in page)
r = book(admin, M, t1, "Stu Two", "09:00");   ok("teacher can't be double-booked (names who)", "Tea1 is already booked at 09:00–09:15" in r.data.decode() and "with Stu One" in r.data.decode())
r = book(admin, M, t2, "Stu One", "09:00");   ok("a student's family can't be in two places at once", "Stu One&#39;s family already has an appointment at 09:00–09:15" in r.data.decode() or "family already has an appointment" in r.data.decode())
r = book(admin, M, t1, "Stu One", "09:00");   t = r.data.decode(); ok("a double clash reports both reasons", "already booked" in t and "family already has" in t)
r = book(admin, M, t1, "Stu One", "09:15");   ok("same teacher+student twice is refused", "already has an appointment with Tea1" in r.data.decode())
ok("none of those created anything", len(appts(M)) == 1)
r = book(admin, M, t2, "Stu Two", "09:07");   ok("a time outside the grid is rejected", b"Not a valid choice" in r.data and len(appts(M)) == 1)
r = book(admin, M, t2, "Stu Two", "09:00", guardian=gA); ok("a guardian not linked to the student is rejected", "isn&#39;t linked" in r.data.decode() or "linked to this student" in r.data.decode())
r = book(admin, M, t2, "Stu Two", "09:00", guardian=gB); ok("a linked guardian is accepted", len(appts(M)) == 2)
r = book(admin, M, 99999, "Stu Three", "09:15");   ok("unknown teacher rejected", len(appts(M)) == 2)
r = book(admin, M, t2, 99999, "09:15");            ok("unknown student rejected", len(appts(M)) == 2)
with app.app_context(): User.query.filter_by(id=t3).first().is_active_account = False; db.session.commit()
r = book(admin, M, t3, "Stu Three", "09:15");      ok("a deactivated teacher can't be booked", len(appts(M)) == 2)
with app.app_context(): User.query.filter_by(id=t3).first().is_active_account = True; db.session.commit()
make(admin, title="PTM-8A", class_id=c8, section_id=s8a); M8 = mid("PTM-8A")
page = admin.get(f"/ptm/{M8}").data.decode()
ok("a section-scoped meeting offers only that section's active students", "Stu One" in page and "Stu Two" in page and "Stu Three" not in page and "Stu Four" not in page and "Stu Five" not in page)
for who in ("Stu Three", "Stu Four", "Stu Five"):
    book(admin, M8, t1, who, "09:00")
ok("students outside the scope (other section/class/inactive) can't be booked", appts(M8) == [])
book(admin, M8, t1, "Stu One", "09:00"); ok("a student inside the scope can", len(appts(M8)) == 1)
t1page = T1.get(f"/ptm/{M}").data.decode()
tsel = re.search(r'id="teacher_id"[^>]*>(.*?)</select>', t1page, re.S).group(1)
ok("a teacher's booking form offers only themselves", f'value="{t1}"' in tsel and f'value="{t2}"' not in tsel)
r = book(T1, M, t1, "Stu Three", "09:30"); ok("a teacher books their own slot", ("Tea1", "Stu Three", "09:30", AppointmentStatus.SCHEDULED) in appts(M))
codes = T1.post(f"/ptm/{M}/book", data={"teacher_id": t2, "student_id": stu["Stu Four"], "slot": "09:30"}).status_code
ok("a teacher can't book for another teacher (refused, nothing created)", codes in (302, 403) and len(appts(M)) == 3)
r = book(REC, M, t2, "Stu Four", "09:30"); ok("a receptionist books for any teacher", ("Tea2", "Stu Four", "09:30", AppointmentStatus.SCHEDULED) in appts(M))
ok("an accountant can't book (403)", ACC.post(f"/ptm/{M}/book", data={"teacher_id": t1, "student_id": stu["Stu One"], "slot": "09:45"}).status_code == 403)

# ===== C. cancel frees the slot; history is kept
first = aid(M, "Stu One", "09:00")
act(admin, first, "cancel")
ok("cancelling marks the appointment cancelled and keeps the row", status_of(first) == AppointmentStatus.CANCELLED)
book(admin, M, t1, "Stu Four", "09:00"); ok("a cancelled slot can be rebooked by someone else", ("Tea1", "Stu Four", "09:00", AppointmentStatus.SCHEDULED) in appts(M))
book(admin, M, t1, "Stu One", "09:45"); ok("the cancelled student can book again", ("Tea1", "Stu One", "09:45", AppointmentStatus.SCHEDULED) in appts(M))
ok("history intact: cancelled row still there", len([a for a in appts(M) if a[3] == AppointmentStatus.CANCELLED]) == 1)
ok("cancelled appointments shown separately", "Cancelled appointments (1)" in admin.get(f"/ptm/{M}").data.decode())
with patch("app.routes.ptm.find_conflicts", return_value=[]):
    r = book(admin, M, t1, "Stu Three", "09:00")      # Tea1 is genuinely booked at 09:00 -> only the DB index stops it
ok("RACE: with the app check bypassed, the database index still blocks it, politely", b"just taken" in r.data and not any(a[1] == "Stu Three" and a[2] == "09:00" for a in appts(M)))

# ===== D. outcomes, permissions, notes
a_t2 = aid(M, "Stu Two", "09:00")      # Tea2's appointment
a_t1 = aid(M, "Stu Four", "09:00")     # Tea1's appointment (the rebooked slot)
ok("a non-owner teacher can't complete/no-show/reopen/note/cancel (403)", [T1.post(f"/ptm/appointment/{a_t2}/update", data={"action": x}).status_code for x in ("complete", "no_show", "reopen", "notes", "cancel")] == [403] * 5)
act(T1, a_t1, "complete"); ok("the owner teacher marks it completed", status_of(a_t1) == AppointmentStatus.COMPLETED)
r = act(T1, a_t1, "cancel"); ok("a completed appointment can't be cancelled", b"Only a scheduled appointment" in r.data and status_of(a_t1) == AppointmentStatus.COMPLETED)
act(T1, a_t1, "reopen"); ok("reopen returns it to scheduled", status_of(a_t1) == AppointmentStatus.SCHEDULED)
act(admin, a_t1, "no_show"); ok("admin can mark a no-show", status_of(a_t1) == AppointmentStatus.NO_SHOW)
act(admin, a_t1, "reopen")
ok("a receptionist can't set outcomes or notes (403)", [REC.post(f"/ptm/appointment/{a_t1}/update", data={"action": x}).status_code for x in ("complete", "no_show", "reopen", "notes")] == [403] * 4)
a_rec = aid(M, "Stu Four", "09:30"); act(REC, a_rec, "cancel"); ok("...but a receptionist can cancel", status_of(a_rec) == AppointmentStatus.CANCELLED)
r = act(admin, a_rec, "complete"); ok("a cancelled appointment can't be changed", status_of(a_rec) == AppointmentStatus.CANCELLED and b"be changed" in r.data)
ok("unknown action -> 400", T1.post(f"/ptm/appointment/{a_t1}/update", data={"action": "explode"}).status_code == 400)
act(T1, a_t1, "notes", notes="Discussed reading level. Follow up in March.")
ok("owner teacher sees their notes", "Follow up in March" in T1.get(f"/ptm/{M}").data.decode())
ok("admin sees the notes", "Follow up in March" in admin.get(f"/ptm/{M}").data.decode())
ok("other teachers do not see the notes", "Follow up in March" not in T2.get(f"/ptm/{M}").data.decode())
ok("receptionists do not see the notes", "Follow up in March" not in REC.get(f"/ptm/{M}").data.decode())
with app.app_context(): first_note = db.session.get(PTMAppointment, first).notes
ok("booking-time notes were stored (on the since-cancelled booking)", first_note == "wants to discuss maths")
page = admin.get(f"/ptm/{M}?teacher_id={t1}").data.decode()
ok("teacher_id filter shows only that teacher's block", 'card-header">Tea1' in page and 'card-header">Tea2' not in page)

# ===== E. page data for the live filtering
page = admin.get(f"/ptm/{M}").data.decode()
ok("page carries busy-slot maps and guardian options for the JS", '"09:00"' in page and "Ahmed One (father)" in page and "Other Dad (mother)" in page)

# ===== F. meeting lifecycle
make(admin, title="PTM-edit"); ME = mid("PTM-edit")
admin.post(f"/ptm/{ME}/edit", data=mdata(title="PTM-edit", end_time="09:40", slot_minutes=20), **FR)
page = admin.get(f"/ptm/{ME}").data.decode()
ok("with no appointments, times and slot length can change (grid updates)", slots_in_page(page) == ["09:00–09:20", "09:20–09:40"])
book(admin, ME, t1, "Stu One", "09:00")
r = admin.post(f"/ptm/{ME}/edit", data=mdata(title="PTM-edit", end_time="10:00", slot_minutes=20), **FR)
ok("once booked, times/length are locked", b"cancel those appointments first" in r.data and meeting("PTM-edit").end_time == dt.time(9, 40))
r = admin.post(f"/ptm/{ME}/edit", data=mdata(title="PTM-edit", end_time="09:40", slot_minutes=20, class_id=c8), **FR)
ok("...and so is the class", b"cancel those appointments first" in r.data)
admin.post(f"/ptm/{ME}/edit", data=mdata(title="PTM-edit-renamed", end_time="09:40", slot_minutes=20, location="Library", meeting_date=D(9)), **FR)
mm = meeting("PTM-edit-renamed")
ok("title, date and location can still change", mm is not None and mm.location == "Library" and mm.meeting_date == today + dt.timedelta(days=9))
r = admin.post(f"/ptm/{ME}/edit", data=mdata(title="PTM-edit-renamed", end_time="09:40", slot_minutes=20, meeting_date=D(-3)), **FR)
ok("moving the date into the past is rejected", b"be in the past" in r.data)
with app.app_context(): pid = PTMMeeting.query.filter_by(title="PTM-past").first().id
admin.post(f"/ptm/{pid}/edit", data=mdata(title="PTM-past-renamed", meeting_date=(today - dt.timedelta(days=10)).isoformat()), **FR)
ok("a past meeting can be edited as long as its date is unchanged", meeting("PTM-past-renamed") is not None)

make(admin, title="PTM-done"); MD = mid("PTM-done"); book(admin, MD, t1, "Stu One", "09:00"); book(admin, MD, t2, "Stu Two", "09:15")
act(T1, aid(MD, "Stu One"), "complete")
r = admin.post(f"/ptm/{MD}/complete", **FR)
ok("completing reports appointments still marked scheduled", b"1 appointment(s) are still marked scheduled" in r.data and meeting("PTM-done").status == MeetingStatus.COMPLETED)
r = book(admin, MD, t3, "Stu Three", "09:30"); ok("a completed meeting takes no more bookings", b"no longer taking bookings" in r.data and len(appts(MD)) == 2)
ok("...can't be edited, completed again or cancelled", b"Only a scheduled meeting can be edited" in admin.get(f"/ptm/{MD}/edit", **FR).data and b"Only a scheduled meeting can be marked" in admin.post(f"/ptm/{MD}/complete", **FR).data and b"Only a scheduled meeting can be cancelled" in admin.post(f"/ptm/{MD}/cancel", **FR).data)
act(T2, aid(MD, "Stu Two"), "no_show"); ok("outcomes can still be recorded after the meeting is completed", status_of(aid(MD, "Stu Two")) == AppointmentStatus.NO_SHOW)

make(admin, title="PTM-cancel"); MC = mid("PTM-cancel")
book(admin, MC, t1, "Stu One", "09:00"); book(admin, MC, t2, "Stu Two", "09:15"); book(admin, MC, t1, "Stu Three", "09:30")
act(T1, aid(MC, "Stu Three"), "complete")
r = admin.post(f"/ptm/{MC}/cancel", **FR)
ok("cancelling a meeting cancels its scheduled appointments", b"2 appointment(s) cancelled" in r.data and status_of(aid(MC, "Stu One")) == AppointmentStatus.CANCELLED and status_of(aid(MC, "Stu Two")) == AppointmentStatus.CANCELLED)
ok("...but keeps ones that already happened", status_of(aid(MC, "Stu Three")) == AppointmentStatus.COMPLETED)
ok("...and a cancelled meeting takes no bookings", b"no longer taking bookings" in book(admin, MC, t3, "Stu One", "09:45").data)

# ===== G. escaping, isolation, audit
make(admin, title="PTM-<script>alert(1)</script>", description="<img src=x onerror=alert(1)>", location="<b>room</b>"); MX = mid("PTM-<script>alert(1)</script>")
book(admin, MX, t1, "Stu One", "09:00", notes="<script>alert(2)</script>"); act(admin, aid(MX, "Stu One"), "notes", notes="<script>alert(3)</script>")
page = admin.get(f"/ptm/{MX}").data.decode() + admin.get("/ptm/").data.decode()
ok("titles, details, location and notes are escaped", "<script>alert" not in page and "<img src=x" not in page and "<b>room</b>" not in page and "&lt;script&gt;" in page)
ok("other school can't open our meeting or its appointments", [other.get(f"/ptm/{M}").status_code, other.post(f"/ptm/appointment/{aid(M, 'Stu Two', '09:00')}/update", data={"action": "cancel"}).status_code, other.post(f"/ptm/{M}/cancel").status_code] == [404] * 3)
ok("other school's list is empty", "PTM" not in other.get("/ptm/?when=all").data.decode())
r = other.post(f"/ptm/{M}/book", data={"teacher_id": t1, "student_id": stu["Stu One"], "slot": "09:45"})
ok("other school can't book into our meeting", r.status_code == 404)
with app.app_context(): acts = {a.action for a in AuditLog.query.filter(AuditLog.action.like("ptm.%")).all()}
need = {"ptm.created", "ptm.edited", "ptm.completed", "ptm.cancelled", "ptm.appointment_booked", "ptm.appointment_cancelled", "ptm.appointment_complete", "ptm.appointment_no_show", "ptm.appointment_reopened", "ptm.appointment_notes"}
ok("audit trail covers every action", need <= acts)

# ===== H. CSRF enforced, pressing the real buttons
app.config["WTF_CSRF_ENABLED"] = True
make_csrf = lambda: None
def press(client, page_url, action_part, extra=None, require=None):
    html = client.get(page_url).data.decode()
    for m in re.finditer(r"<form\b([^>]*)>(.*?)</form>", html, re.S):
        attrs, body = m.group(1), m.group(2)
        act_ = re.search(r'action="([^"]+)"', attrs)
        if act_ and action_part in act_.group(1) and (require is None or require in body):
            tk = re.search(r'name="csrf_token"[^>]*?value="([^"]+)"', body)
            data = dict(extra or {});
            if tk: data["csrf_token"] = tk.group(1)
            return client.post(act_.group(1), data=data).status_code, bool(tk)
    return None, None
MCS = mid("PTM-main")
code, had = press(admin, f"/ptm/{MCS}", f"/ptm/{MCS}/book", {"teacher_id": t2, "student_id": stu["Stu Three"], "slot": "09:45"})
ok(f"CSRF enforced: booking form works (token={had}, POST->{code})", code in (200, 302))
code, had = press(admin, f"/ptm/{MCS}", "/update", {"action": "cancel"}, require='value="cancel"')
ok(f"CSRF enforced: appointment Cancel button works (token={had}, POST->{code})", code in (200, 302))
code, had = press(admin, f"/ptm/{MCS}", "/complete")
ok(f"CSRF enforced: meeting 'Mark completed' button works (token={had}, POST->{code})", code in (200, 302))
code = admin.post(f"/ptm/{mid('PTM-8A')}/cancel").status_code
ok("CSRF enforced: a POST with no token is rejected (400)", code == 400)

print(f"\n{sum(results)}/{len(results)} passed on {db.engine.dialect.name if False else DB.split(':')[0]}")
sys.exit(0 if all(results) else 1)
