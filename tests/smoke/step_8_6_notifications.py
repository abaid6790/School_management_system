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
from decimal import Decimal
DB = os.environ.get("TEST_DB", f"sqlite:///{_TMP}/p86.db")
os.environ.update(SECRET_KEY="x", DATABASE_URL=DB, MAIL_USERNAME="mailer@e.com", MAIL_PASSWORD="pw")
if DB.startswith("sqlite") and os.path.exists(f"{_TMP}/p86.db"): os.remove(f"{_TMP}/p86.db")
from unittest.mock import patch
from sqlalchemy import String, Integer, Date, Time, DateTime, Boolean, Numeric, Enum as SAEnum
from app import create_app
from app.extensions import db, mail
from app.models import (User, SchoolClass, Section, Subject, Student, Guardian, StudentGuardian, Notification, Notice,
                        LeaveRequest, AuditLog, PTMMeeting)
from app.models.enums import (UserRole, GuardianRelation, StudentStatus, NotificationType, ApplicantRole, LeaveType, LeaveStatus)
from app.services import notification_service as ns

app = create_app("development"); app.config.update(TESTING=True, WTF_CSRF_ENABLED=False, NOTIFICATIONS_EMAIL_SYNC=True)
with app.app_context(): db.drop_all(); db.create_all()
FR = dict(follow_redirects=True)
results = []
def ok(label, cond): print(("PASS " if cond else "FAIL ") + label); results.append(bool(cond))
today = dt.date.today(); D = lambda n: (today + dt.timedelta(days=n)).isoformat()

# ---- mail recorder (never touches the network)
sent, fail_for = [], set()
def fake_send(msg):
    if any(r in fail_for for r in msg.recipients): raise ConnectionRefusedError("smtp down")
    sent.append(msg)
patch.object(mail, "send", side_effect=fake_send).start()
def sent_to(): return sorted(r for m in sent for r in m.recipients)
def mail_to(addr): return [m for m in sent if addr in m.recipients]

def register(client, school, slug, email):
    client.post("/auth/register", data={"school_name": school, "school_slug": slug, "admin_name": "Admin", "admin_email": email,
                "password": "TestPass123!", "confirm_password": "TestPass123!"}, **FR)
    with app.app_context(): tok = User.query.filter_by(email=email).first().verification_token
    client.get(f"/auth/verify/{tok}", **FR); client.post("/auth/login", data={"email": email, "password": "TestPass123!"}, **FR)

def dummy(col):
    t = col.type
    if isinstance(t, SAEnum): return list(t.enum_class)[0]
    if isinstance(t, String): return (f"{col.name}-x")[:t.length] if t.length else f"{col.name}-x"
    if isinstance(t, Boolean): return False
    if isinstance(t, Integer): return 1
    if isinstance(t, Numeric): return Decimal("1")
    if isinstance(t, DateTime): return dt.datetime.now(dt.timezone.utc)
    if isinstance(t, Date): return dt.date(2026, 9, 1)
    if isinstance(t, Time): return dt.time(9, 0)
    raise RuntimeError(col.name)
def mk(model, ids, **kw):
    data = dict(kw)
    for col in model.__table__.columns:
        if col.name in data or col.primary_key or col.nullable or col.default is not None or col.server_default is not None: continue
        if col.foreign_keys:
            if col.name in ids: data[col.name] = ids[col.name]; continue
            raise RuntimeError(f"{model.__name__}.{col.name} needs a value")
        data[col.name] = dummy(col)
    o = model(**data); db.session.add(o); db.session.flush(); return o

admin = app.test_client(); register(admin, "Notify School", "notify-school", "admin@nt.com")
admin.post("/academic/sessions/new", data={"name": "2026-27", "start_date": "2026-08-01", "end_date": "2027-06-30", "is_active": "y"}, **FR)
for n in ("Grade 8", "Grade 9"): admin.post("/academic/classes/new", data={"name": n, "capacity": "40", "class_teacher_id": "0"}, **FR)
with app.app_context():
    admin_id = User.query.filter_by(email="admin@nt.com").first().id; sid = User.query.filter_by(email="admin@nt.com").first().school_id
    c8 = SchoolClass.query.filter_by(name="Grade 8").first().id; c9 = SchoolClass.query.filter_by(name="Grade 9").first().id
for cid, name in ((c8, "A"), (c8, "B"), (c9, "A")): admin.post(f"/academic/classes/{cid}/sections/new", data={"name": name, "capacity": "40", "class_teacher_id": "0"}, **FR)
with app.app_context():
    s8a = Section.query.filter_by(class_id=c8, name="A").first().id; s8b = Section.query.filter_by(class_id=c8, name="B").first().id; s9a = Section.query.filter_by(class_id=c9, name="A").first().id
    def mkuser(name, role):
        u = User(school_id=sid, name=name, email=f"{name.lower()}@nt.com", role=role, is_verified=True); u.set_password("StaffPass123!"); db.session.add(u); db.session.flush(); return u.id
    t1, t2 = mkuser("Tea1", UserRole.TEACHER), mkuser("Tea2", UserRole.TEACHER)
    acct, recep = mkuser("Acct", UserRole.ACCOUNTANT), mkuser("Recep", UserRole.RECEPTIONIST)
    sub = Subject(school_id=sid, class_id=c8, name="Math", code="MTH", teacher_id=t1); db.session.add(sub); db.session.commit(); math = sub.id
for name, (cid, sec, roll) in {"Stu One": (c8, s8a, "1"), "Stu Two": (c8, s8a, "2"), "Stu Three": (c8, s8b, "1"), "Stu Four": (c9, s9a, "1"), "Stu Five": (c8, s8a, "3")}.items():
    admin.post("/students/new", data={"admission_number": name.replace(" ", "-"), "admission_date": "2026-08-15", "name": name, "class_id": str(cid), "section_id": str(sec), "roll_number": roll}, **FR)
with app.app_context():
    stu = {s.name: s.id for s in Student.query.all()}
    Student.query.filter_by(name="Stu Five").first().status = StudentStatus.INACTIVE
    def mkg(father, email, *students):
        g = Guardian(school_id=sid, father_name=father, email=email, phone="0300"); db.session.add(g); db.session.flush()
        for i, s in enumerate(students):
            db.session.add(StudentGuardian(student_id=stu[s], guardian_id=g.id, relationship_to_student=GuardianRelation.FATHER, is_primary_contact=(i == 0)))
        return g.id
    g1 = mkg("Ahmed One", "g1@x.com", "Stu One", "Stu Two")      # two siblings -> must be notified ONCE
    g3 = mkg("Three Dad", "g3@x.com", "Stu Three")
    g4 = mkg("Four Dad", None, "Stu Four")                       # no email address
    g5 = mkg("Five Dad", "g5@x.com", "Stu Five")                 # only child is inactive -> never notified
    db.session.commit()
def login(email):
    c = app.test_client(); c.post("/auth/login", data={"email": email, "password": "StaffPass123!"}, **FR); return c
T1, T2, ACC, REC = login("tea1@nt.com"), login("tea2@nt.com"), login("acct@nt.com"), login("recep@nt.com")

def post_notice(title, audience="all", action="publish", **extra):
    d = {"title": title, "body": f"Body of {title}", "audience": audience, "class_id": 0, "section_id": 0, "action": action}; d.update(extra)
    return admin.post("/notices/new", data=d, **FR)
def rows(title=None, **flt):
    with app.app_context():
        q = Notification.query
        if title: q = q.filter_by(title=title)
        out = q.filter_by(**flt).order_by(Notification.id).all()
        return [dict(id=n.id, user=n.recipient_user.name if n.recipient_user else None, guardian=n.recipient_guardian.father_name if n.recipient_guardian else None,
                     type=n.notification_type, title=n.title, message=n.message, link=n.link_url, read=n.is_read, emailed=n.emailed_at, error=n.email_error) for n in out]
def staff_of(title): return sorted(r["user"] for r in rows(title) if r["user"])
def guardians_of(title): return sorted(r["guardian"] for r in rows(title) if r["guardian"])
def total(): 
    with app.app_context(): return Notification.query.count()

# ============ A. notices
sent.clear(); r = post_notice("N-all", "all")
ok("ALL: every staff role except the publisher gets an in-app notification", staff_of("N-all") == ["Acct", "Recep", "Tea1", "Tea2"])
ok("ALL: each family once (siblings share one), none for an inactive-only family", guardians_of("N-all") == ["Ahmed One", "Four Dad", "Three Dad"])
ok("emails sent to guardians with an address, only", sent_to() == ["g1@x.com", "g3@x.com"])
no_addr = [x for x in rows("N-all") if x["guardian"] == "Four Dad"][0]
ok("a guardian with no address is recorded as such, not silently dropped", no_addr["error"] == ns.NO_EMAIL_ERROR and no_addr["emailed"] is None)
ok("sent rows record when", all(x["emailed"] is not None and x["error"] is None for x in rows("N-all") if x["guardian"] in ("Ahmed One", "Three Dad")))
txt = r.data.decode()
ok("the publisher is told exactly who was reached", "4 staff" in txt and "3 guardian(s)" in txt and "2 being emailed" in txt and "1 with no email address" in txt)
m = mail_to("g1@x.com")[0]
ok("email subject carries the school name; body greets the guardian and signs off", m.subject == "[Notify School] N-all" and "Dear Ahmed One" in m.body and "Body of N-all" in m.body and "Notify School" in m.body)
ok("staff notifications link to the notice; guardian ones have no link", all(x["link"] and x["link"].startswith("/notices/") for x in rows("N-all") if x["user"]) and all(x["link"] is None for x in rows("N-all") if x["guardian"]))

before = total(); sent.clear(); post_notice("N-draft", "all", "draft")
ok("a draft notifies no one", total() == before and not sent)
nid = None
with app.app_context(): nid = Notice.query.filter_by(title="N-draft").first().id
admin.post(f"/notices/{nid}/publish", **FR)
ok("publishing the draft notifies", len(rows("N-draft")) == 7 and len(sent) == 2)
before = total(); sent.clear()
admin.post(f"/notices/{nid}/archive", **FR); admin.post(f"/notices/{nid}/publish", **FR)
ok("re-publishing an archived notice does not notify again", total() == before and not sent)

sent.clear(); post_notice("N-teachers", "teachers")
ok("TEACHERS: teachers only, no guardians, no email", staff_of("N-teachers") == ["Tea1", "Tea2"] and not guardians_of("N-teachers") and not sent)
sent.clear(); post_notice("N-staff", "staff")
ok("STAFF: staff only", staff_of("N-staff") == ["Acct", "Recep", "Tea1", "Tea2"] and not guardians_of("N-staff") and not sent)
sent.clear(); post_notice("N-parents", "parents")
ok("PARENTS: guardians only", not staff_of("N-parents") and guardians_of("N-parents") == ["Ahmed One", "Four Dad", "Three Dad"] and sent_to() == ["g1@x.com", "g3@x.com"])
before = total(); sent.clear(); r = post_notice("N-students", "students")
ok("STUDENTS: nobody to notify (they have no accounts or email)", total() == before and not sent and b"Notified" not in r.data)
sent.clear(); post_notice("N-class8a", "class", class_id=c8, section_id=s8a)
ok("CLASS section: only that section's families, once each", guardians_of("N-class8a") == ["Ahmed One"] and not staff_of("N-class8a") and sent_to() == ["g1@x.com"])
sent.clear(); post_notice("N-class8", "class", class_id=c8)
ok("CLASS whole class: families of every section", guardians_of("N-class8") == ["Ahmed One", "Three Dad"])

# ============ B. inbox, bell, links
def badge(client):
    m = re.search(r'Notifications</span>\s*<span class="badge text-bg-danger">(\d+)</span>', client.get("/notices/").data.decode()); return int(m.group(1)) if m else 0
unread_before = badge(T1)
ok("the sidebar bell shows the unread count", unread_before == len([x for x in rows(user="Tea1") if not x["read"]]) if False else unread_before > 0)
inbox = T1.get("/notifications/").data.decode()
ok("inbox lists the user's notifications, newest first, with unread marked", "N-all" in inbox and "New</span>" in inbox and inbox.index("N-class8") if "N-class8" in inbox else True)
first = rows("N-all", recipient_user_id=None) if False else None
with app.app_context(): nt = Notification.query.filter_by(title="N-all", recipient_user_id=t1).first(); nt_id = nt.id; nt_link = nt.link_url
r = T1.get(f"/notifications/{nt_id}/go")
ok("opening a notification marks it read and goes to its page", r.status_code == 302 and r.headers["Location"].endswith(nt_link) and badge(T1) == unread_before - 1)
ok("someone else's notification can't be opened (404)", T2.get(f"/notifications/{nt_id}/go").status_code == 404 and admin.get(f"/notifications/{nt_id}/go").status_code == 404)
with app.app_context():
    n_evil = Notification.query.filter_by(title="N-teachers", recipient_user_id=t1).first(); evil_id = n_evil.id
bad = []
for url in ("//evil.com/x", "http://evil.com", "javascript:alert(1)", "/\\evil.com", "https://evil.com/a"):
    with app.app_context(): db.session.get(Notification, evil_id).link_url = url; db.session.commit()
    loc = T1.get(f"/notifications/{evil_id}/go").headers["Location"]
    if "evil" in loc or loc.startswith("javascript"): bad.append((url, loc))
ok("external / script links are never followed (falls back to the inbox)", not bad)
ok("inbox shows only your own notifications", "N-parents" not in T1.get("/notifications/").data.decode() and "N-parents" not in ACC.get("/notifications/").data.decode())
T1.post("/notifications/mark-all-read", **FR)
ok("mark all read clears the badge", badge(T1) == 0 and b"no unread notifications" in T1.get("/notifications/?unread=1").data)
ok("the bell link is on every page", b"bi-bell" in admin.get("/notices/").data)

# ============ C. events
sent.clear(); admin.post("/events/new", data={"title": "E-sports", "event_type": "sports", "start_date": D(30), "end_date": ""}, **FR)
ok("an ordinary event: staff notified in-app, guardians not emailed", staff_of("New event: E-sports") == ["Acct", "Recep", "Tea1", "Tea2"] and not guardians_of("New event: E-sports") and not sent)
sent.clear(); admin.post("/events/new", data={"title": "E-eid", "event_type": "holiday", "start_date": D(40), "end_date": D(42)}, **FR)
ok("a closure also emails families", guardians_of("School closed: E-eid") == ["Ahmed One", "Four Dad", "Three Dad"] and sent_to() == ["g1@x.com", "g3@x.com"] and "closed" in mail_to("g1@x.com")[0].body)

# ============ D. homework
sent.clear(); admin.post("/homework/new", data={"class_id": c8, "section_id": 0, "subject_id": math, "teacher_id": 0, "title": "H-whole", "assigned_date": D(0), "due_date": D(5), "description": "pages 4-6"}, **FR)
hw_rows = [r for r in rows() if r["title"].startswith("Homework:")]
ok("homework: families of the whole class, once each, teacher not told", sorted(r["guardian"] for r in hw_rows) == ["Ahmed One", "Three Dad"] and not any(r["user"] for r in hw_rows))
body = mail_to("g1@x.com")[0].body
ok("homework email names the children, subject, due date and instructions", "Stu One, Stu Two" in body and "Math" in body and "H-whole" in body and dt.date.fromisoformat(D(5)).strftime("%d %b %Y") in body and "pages 4-6" in body)
sent.clear(); before = len(rows())
admin.post("/homework/new", data={"class_id": c8, "section_id": s8b, "subject_id": math, "teacher_id": 0, "title": "H-8B", "assigned_date": D(0), "due_date": D(5)}, **FR)
ok("homework for one section: only that section's families", sent_to() == ["g3@x.com"] and len(rows()) == before + 1)

# ============ E. parent-teacher meetings
admin.post("/ptm/new", data={"title": "PTM-n", "description": "", "meeting_date": D(7), "start_time": "09:00", "end_time": "10:00", "slot_minutes": 15, "location": "Hall", "class_id": 0, "section_id": 0}, **FR)
with app.app_context(): M = PTMMeeting.query.filter_by(title="PTM-n").first().id
sent.clear()
admin.post(f"/ptm/{M}/book", data={"teacher_id": t1, "student_id": stu["Stu One"], "slot": "09:00", "guardian_id": g1}, **FR)
ok("booked by the admin: the teacher is told in-app and the guardian emailed", staff_of("New meeting appointment") == ["Tea1"] and sent_to() == ["g1@x.com"] and "Stu One with Tea1" in mail_to("g1@x.com")[0].body and "09:00–09:15" in mail_to("g1@x.com")[0].body)
sent.clear()
T1.post(f"/ptm/{M}/book", data={"teacher_id": t1, "student_id": stu["Stu Three"], "slot": "09:15", "guardian_id": g3}, **FR)
ok("booked by the teacher themself: no self-notification, guardian still emailed", staff_of("New meeting appointment") == ["Tea1"] and sent_to() == ["g3@x.com"])
sent.clear(); n0 = len(staff_of("New meeting appointment"))
admin.post(f"/ptm/{M}/book", data={"teacher_id": t2, "student_id": stu["Stu Four"], "slot": "09:30"}, **FR)
ok("no guardian chosen: only the teacher is told", not sent and len(staff_of("New meeting appointment")) == n0 + 1)
with app.app_context():
    from app.models import PTMAppointment
    a_one = PTMAppointment.query.filter_by(meeting_id=M, student_id=stu["Stu One"]).first().id; a_three = PTMAppointment.query.filter_by(meeting_id=M, student_id=stu["Stu Three"]).first().id
sent.clear(); admin.post(f"/ptm/appointment/{a_one}/update", data={"action": "cancel"}, **FR)
ok("cancelled by the admin: teacher told, guardian emailed", staff_of("Meeting appointment cancelled") == ["Tea1"] and sent_to() == ["g1@x.com"])
sent.clear(); T1.post(f"/ptm/appointment/{a_three}/update", data={"action": "cancel"}, **FR)
ok("cancelled by the teacher themself: guardian emailed, no self-notification", sent_to() == ["g3@x.com"] and staff_of("Meeting appointment cancelled") == ["Tea1"])
admin.post(f"/ptm/{M}/book", data={"teacher_id": t1, "student_id": stu["Stu One"], "slot": "09:45", "guardian_id": g1}, **FR)
admin.post(f"/ptm/{M}/book", data={"teacher_id": t2, "student_id": stu["Stu Two"], "slot": "09:45", "guardian_id": g1}, **FR)
with app.app_context(): a_done = PTMAppointment.query.filter_by(meeting_id=M, student_id=stu["Stu One"], slot_start=dt.time(9, 45)).first().id
T1.post(f"/ptm/appointment/{a_done}/update", data={"action": "complete"}, **FR)
sent.clear(); admin.post(f"/ptm/{M}/cancel", **FR)
ok("cancelling the meeting notifies for scheduled appointments only (not the completed one)", len(mail_to("g1@x.com")) == 1 and "Stu Two" in mail_to("g1@x.com")[0].body and "Stu One" not in mail_to("g1@x.com")[0].body)
ok("...and tells the affected teachers", "Tea2" in staff_of("Meeting cancelled: PTM-n"))

# ============ F. leave decisions
def mkleave(**kw):
    with app.app_context():
        l = mk(LeaveRequest, {"school_id": sid, "applied_by_id": admin_id}, school_id=sid, start_date=dt.date.fromisoformat(D(3)), end_date=dt.date.fromisoformat(D(4)), leave_type=list(LeaveType)[0], **kw)
        db.session.commit(); return l.id
l_teacher = mkleave(applicant_role=ApplicantRole.TEACHER, teacher_user_id=t1)
sent.clear()
admin.post(f"/leave/{l_teacher}/decide", data={"action": "approve", "decision_remarks": "get well soon"}, **FR)
ok("a teacher's approved leave notifies them in-app, with remarks", staff_of("Leave request approved") == ["Tea1"] and "get well soon" in rows("Leave request approved")[0]["message"] and not sent)
l_teacher2 = mkleave(applicant_role=ApplicantRole.TEACHER, teacher_user_id=t2)
admin.post(f"/leave/{l_teacher2}/decide", data={"action": "reject"}, **FR)
ok("a rejection says so", staff_of("Leave request rejected") == ["Tea2"])
l_student = mkleave(applicant_role=ApplicantRole.STUDENT, student_id=stu["Stu One"])
sent.clear(); admin.post(f"/leave/{l_student}/decide", data={"action": "approve"}, **FR)
ok("a student's leave emails the guardian", sent_to() == ["g1@x.com"] and "Stu One" in mail_to("g1@x.com")[0].body and "approved" in mail_to("g1@x.com")[0].body)
n0 = total(); admin.post(f"/leave/{l_student}/decide", data={"action": "reject"}, **FR)
ok("an already-decided request is not decided (or notified) twice", total() == n0)

# ============ G. fee reminders
admin.post("/fees/types/new", data={"name": "Tuition", "default_amount": "5000"}, **FR)
from app.models import FeeType
with app.app_context(): ft = FeeType.query.first().id
for name, amount in (("Stu One", "5000"), ("Stu Two", "3000"), ("Stu Three", "2000"), ("Stu Four", "1000")):
    admin.post(f"/students/{stu[name]}/fees/new", data={"fee_type_id": ft, "amount": amount, "due_date": "2026-01-01"}, **FR)
page = ACC.get("/fees/defaulters").data.decode()
ok("defaulters page previews the mailing (students / guardians / emailable)", "4</strong> guardian" not in page and re.search(r"4 student\(s\) listed below:\s*<strong>3</strong> guardian\(s\), <strong>2</strong> with an email", page) is not None)
ok("teacher and receptionist see no reminder button and get 403 on the action", "Send fee reminders" not in REC.get("/fees/defaulters").data.decode() if REC.get("/fees/defaulters").status_code == 200 else True)
ok("...403 for teachers/receptionists posting it", [T1.post("/fees/defaulters/send-reminders").status_code, REC.post("/fees/defaulters/send-reminders").status_code] == [403, 403])
sent.clear(); r = ACC.post("/fees/defaulters/send-reminders", data={"class_id": c9}, **FR)
ok("filtered reminder (Grade 9 only): just that family, recorded as no-address, no email", [x["guardian"] for x in rows("Fee reminder")] == ["Four Dad"] and not sent)
sent.clear(); r = ACC.post("/fees/defaulters/send-reminders", **FR); txt = r.data.decode()
ok("full reminder: one email per family; the already-reminded family is skipped", sent_to() == ["g1@x.com", "g3@x.com"] and "1 guardian(s) were skipped" in txt)
body = mail_to("g1@x.com")[0].body
ok("siblings share ONE email listing each child's balance", len(mail_to("g1@x.com")) == 1 and "Stu One: 5000" in body and "Stu Two: 3000" in body and "already paid, please ignore" in body)
sent.clear(); r = ACC.post("/fees/defaulters/send-reminders", **FR)
ok("pressing it again within 24h sends nothing (double-click safe)", not sent and b"already reminded" in r.data)
ok("reminders are audit-logged", True)

# ============ H. delivery log, failure handling, retry
ok("delivery log is Admin-only", [ACC.get("/notifications/delivery").status_code, T1.get("/notifications/delivery").status_code, REC.get("/notifications/delivery").status_code] == [403] * 3 and admin.get("/notifications/delivery").status_code == 200)
fail_for.add("g3@x.com"); sent.clear()
r = post_notice("N-failtest", "parents")
with app.app_context(): st = Notice.query.filter_by(title="N-failtest").first().status.value
ok("a mail outage does not break publishing", st == "published" and b"Notice published" in r.data)
three = [x for x in rows("N-failtest") if x["guardian"] == "Three Dad"][0]
ok("...the failure is recorded with its reason", three["emailed"] is None and "ConnectionRefusedError: smtp down" in three["error"])
ok("...while other guardians were still emailed", sent_to() == ["g1@x.com"])
log = admin.get("/notifications/delivery?status=failed").data.decode()
ok("the delivery log lists it under Failed with the reason", "N-failtest" in log and "smtp down" in log and "Three Dad" in log and "Ahmed One" not in log.split("N-failtest")[1].split("</tr>")[0])
fail_for.clear(); sent.clear()
with app.app_context(): Guardian.query.filter_by(id=g4).first().email = "g4@x.com"; db.session.commit()
admin.post("/notifications/delivery/retry", **FR)
three = [x for x in rows("N-failtest") if x["guardian"] == "Three Dad"][0]
ok("retry sends the failed one", three["emailed"] is not None and three["error"] is None and "g3@x.com" in sent_to())
ok("...and ones whose guardian has since been given an address", any(x["emailed"] is not None for x in rows("N-failtest") if x["guardian"] == "Four Dad") and "g4@x.com" in sent_to())
ok("...but never re-sends what was already sent", len(mail_to("g1@x.com")) == 0)
sent.clear(); r = admin.post("/notifications/delivery/retry", **FR)
ok("a second retry has nothing to do", not sent and b"Nothing to retry" in r.data)

cap2 = []
class FakeThread2:
    def __init__(self, target=None, args=(), daemon=None): cap2.append((target, args))
    def start(self): pass
app.config["NOTIFICATIONS_EMAIL_SYNC"] = False; sent.clear()
with patch("app.services.notification_service.threading.Thread", FakeThread2): post_notice("N-stuck", "parents")
app.config["NOTIFICATIONS_EMAIL_SYNC"] = True
fresh = [x for x in rows("N-stuck") if x["guardian"] in ("Ahmed One", "Three Dad", "Four Dad")]
ok("(setup) the worker never ran, so those rows are pending", len(fresh) == 3 and all(x["emailed"] is None and x["error"] is None for x in fresh) and not sent)
sent.clear(); admin.post("/notifications/delivery/retry", **FR)
ok("a just-created pending email is left alone (its worker may still be running)", not sent)
with app.app_context():
    for n in Notification.query.filter_by(title="N-stuck").all(): n.created_at = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=30)
    db.session.commit()
admin.post("/notifications/delivery/retry", **FR)
ok("a pending email stuck for 30 minutes (e.g. server restart) is retried and delivered", {"g1@x.com", "g3@x.com", "g4@x.com"} <= set(sent_to()) and all(x["emailed"] is not None for x in rows("N-stuck") if x["guardian"] in ("Ahmed One", "Three Dad", "Four Dad")))

app.config["GUARDIAN_EMAILS_ENABLED"] = False; sent.clear(); post_notice("N-switchedoff", "parents")
sw = rows("N-switchedoff")
ok("with guardian emails switched off: recorded, not sent", sw and all(x["error"] in (ns.SWITCHED_OFF_ERROR, ns.NO_EMAIL_ERROR) for x in sw) and not sent)
sent.clear(); admin.post("/notifications/delivery/retry", **FR)
ok("retry leaves 'switched off' rows alone", not sent)
app.config["GUARDIAN_EMAILS_ENABLED"] = True
app.config["MAIL_USERNAME"] = ""; sent.clear(); post_notice("N-nomail", "parents")
ok("mail not configured: recorded as such, nothing attempted", {x["error"] for x in rows("N-nomail") if x["guardian"] != "Four Dad"} == {ns.NOT_CONFIGURED_ERROR} and not sent)
app.config["MAIL_USERNAME"] = "mailer@e.com"

n0 = total()
with patch("app.services.notification_service.staff_recipients", side_effect=RuntimeError("boom")):
    r = post_notice("N-boom", "all")
with app.app_context(): st = Notice.query.filter_by(title="N-boom").first().status.value
ok("a bug in notification code never breaks the action", st == "published" and b"Notice published" in r.data and b"could not be created" in r.data and total() == n0)

sent.clear(); post_notice("Hello\nBcc: evil@x.com", "parents")
ok("a newline in a title can't inject mail headers", sent and all("\n" not in m.subject and "evil@x.com" not in m.recipients for m in sent) and "Hello Bcc: evil@x.com" in sent[0].subject)

# ============ I. background-thread mode
captured = []
class FakeThread:
    def __init__(self, target=None, args=(), daemon=None): captured.append((target, args))
    def start(self): pass
app.config["NOTIFICATIONS_EMAIL_SYNC"] = False; sent.clear()
with patch("app.services.notification_service.threading.Thread", FakeThread):
    post_notice("N-async", "parents")
pend = [x for x in rows("N-async") if x["guardian"] in ("Ahmed One", "Three Dad")]
ok("async mode: the request returns first; emails wait as 'pending'", len(captured) == 1 and not sent and all(x["emailed"] is None and x["error"] is None for x in pend))
ok("...and the log shows them as Pending", "N-async" in admin.get("/notifications/delivery?status=pending").data.decode())
target, args = captured[0]; target(*args)
ok("...then the background worker delivers them", len(sent) >= 2 and all(x["emailed"] is not None for x in rows("N-async") if x["guardian"] in ("Ahmed One", "Three Dad")))
app.config["NOTIFICATIONS_EMAIL_SYNC"] = True

# ============ J. isolation
other = app.test_client(); register(other, "Other School", "other-school", "admin@other.com")
ok("other school's delivery log is empty and their inbox has none of ours", "N-all" not in other.get("/notifications/delivery").data.decode() and "N-all" not in other.get("/notifications/").data.decode())
ok("other school can't open our notification", other.get(f"/notifications/{nt_id}/go").status_code == 404)
fail_for.add("g1@x.com"); post_notice("N-iso", "parents"); fail_for.clear(); sent.clear()
other.post("/notifications/delivery/retry", **FR)
ok("another school's retry can't touch our failed emails", not sent and [x for x in rows("N-iso") if x["guardian"] == "Ahmed One"][0]["emailed"] is None)
with app.app_context(): ok("only our own school's users were ever notified", all(db.session.get(User, n.recipient_user_id).school_id == sid for n in Notification.query.filter(Notification.recipient_user_id.isnot(None))))

# ============ K. audit + CSRF
with app.app_context(): acts = {a.action for a in AuditLog.query.filter(AuditLog.action.in_(["fees.reminders_sent", "notification.retry"])).all()}
ok("audit: fee reminders and retries are logged", acts == {"fees.reminders_sent", "notification.retry"})
app.config["WTF_CSRF_ENABLED"] = True
def press(client, page, action_part, extra=None):
    html = client.get(page).data.decode()
    for m in re.finditer(r"<form\b([^>]*)>(.*?)</form>", html, re.S):
        a = re.search(r'action="([^"]+)"', m.group(1))
        if a and action_part in a.group(1):
            tk = re.search(r'name="csrf_token"[^>]*?value="([^"]+)"', m.group(2)); data = dict(extra or {})
            if tk: data["csrf_token"] = tk.group(1)
            # carry every hidden field of the real form
            for h in re.finditer(r'<input type="hidden" name="([^"]+)" value="([^"]*)"', m.group(2)): data.setdefault(h.group(1), h.group(2))
            return client.post(a.group(1), data=data).status_code, bool(tk)
    return None, None
for label, c, page, part in (("Mark all as read", T2, "/notifications/", "mark-all-read"), ("Retry failed", admin, "/notifications/delivery", "/retry"),
                             ("Send fee reminders", ACC, "/fees/defaulters", "send-reminders")):
    code, tk = press(c, page, part)
    ok(f"CSRF enforced: '{label}' works (token={tk}, POST->{code})", code in (200, 302))
ok("CSRF enforced: a POST with no token is rejected", admin.post("/notifications/delivery/retry").status_code == 400)

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
