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
os.environ.update(SECRET_KEY="x", DATABASE_URL=f"sqlite:///{_TMP}/p84.db", MAIL_USERNAME="x@e.com", MAIL_PASSWORD="x")
if os.path.exists(f"{_TMP}/p84.db"): os.remove(f"{_TMP}/p84.db")
from unittest.mock import patch
from app import create_app
from app.extensions import db, mail
from app.models import (User, SchoolClass, Section, Subject, Student, Homework, HomeworkSubmission, AuditLog)
from app.models.enums import UserRole, RecordStatus, StudentStatus, HomeworkStatus, SubmissionStatus

app = create_app("development"); app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
with app.app_context(): db.create_all()
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

admin = app.test_client(); register(admin, "Homework School", "homework-school", "admin@hw.com")
admin.post("/academic/sessions/new", data={"name": "2026-27", "start_date": "2026-08-01", "end_date": "2027-06-30", "is_active": "y"}, **FR)
for n in ("Grade 8", "Grade 9"): admin.post("/academic/classes/new", data={"name": n, "capacity": "40", "class_teacher_id": "0"}, **FR)
with app.app_context():
    sid = User.query.filter_by(email="admin@hw.com").first().school_id
    c8 = SchoolClass.query.filter_by(name="Grade 8").first().id; c9 = SchoolClass.query.filter_by(name="Grade 9").first().id
for cid, name in ((c8, "A"), (c8, "B"), (c9, "A")):
    admin.post(f"/academic/classes/{cid}/sections/new", data={"name": name, "capacity": "40", "class_teacher_id": "0"}, **FR)
with app.app_context():
    s8a = Section.query.filter_by(class_id=c8, name="A").first().id; s8b = Section.query.filter_by(class_id=c8, name="B").first().id
    s9a = Section.query.filter_by(class_id=c9, name="A").first().id
    def mkuser(name, role):
        u = User(school_id=sid, name=name, email=f"{name.lower()}@hw.com", role=role, is_verified=True); u.set_password("StaffPass123!"); db.session.add(u); db.session.flush(); return u.id
    t1, t2, t3 = mkuser("Tea1", UserRole.TEACHER), mkuser("Tea2", UserRole.TEACHER), mkuser("Tea3", UserRole.TEACHER)
    acct, recep = mkuser("Acct", UserRole.ACCOUNTANT), mkuser("Recep", UserRole.RECEPTIONIST)
    def mksub(name, code, cid, teacher, status=RecordStatus.ACTIVE):
        s = Subject(school_id=sid, class_id=cid, name=name, code=code, teacher_id=teacher, status=status); db.session.add(s); db.session.flush(); return s.id
    math, sci = mksub("Math", "MTH", c8, t1), mksub("Science", "SCI", c8, t2)
    hist, dead, nobody = mksub("History", "HIS", c9, t1), mksub("Retired", "RET", c8, t1, RecordStatus.INACTIVE), mksub("Orphan", "ORP", c8, None)
    db.session.commit()
for name, (cid, sec, roll) in {"Stu One": (c8, s8a, "1"), "Stu Two": (c8, s8a, "2"), "Stu Three": (c8, s8b, "1"), "Stu Four": (c9, s9a, "1"), "Stu Five": (c8, s8a, "3")}.items():
    admin.post("/students/new", data={"admission_number": name.replace(" ", "-"), "admission_date": "2026-08-15", "name": name, "class_id": str(cid), "section_id": str(sec), "roll_number": roll}, **FR)
with app.app_context():
    stu = {s.name: s.id for s in Student.query.all()}
    Student.query.filter_by(name="Stu Five").first().status = StudentStatus.INACTIVE; db.session.commit()
def login(email):
    c = app.test_client(); c.post("/auth/login", data={"email": email, "password": "StaffPass123!"}, **FR); return c
T1, T2, T3, ACC, REC = login("tea1@hw.com"), login("tea2@hw.com"), login("tea3@hw.com"), login("acct@hw.com"), login("recep@hw.com")

def hw_data(**kw):
    d = dict(class_id=c8, section_id=0, subject_id=math, teacher_id=0, title="HW", description="Do it", assigned_date=D(0), due_date=D(3)); d.update(kw); return d
def create(client, **kw): return client.post("/homework/new", data=hw_data(**kw), **FR)
def row(title):
    with app.app_context(): return Homework.query.filter_by(title=title).first()
def hid(title): return row(title).id
def subs(h):
    with app.app_context(): return {s.student.name: s.status for s in HomeworkSubmission.query.filter_by(homework_id=h).all()}
def save(client, h, **statuses):
    data = {}
    for name, val in statuses.items():
        data[f"status_{stu[name.replace('_', ' ')]}"] = val
    return client.post(f"/homework/{h}/submissions", data=data, **FR)

# ===== A. creating
r = create(T1, title="HW-whole")
w = row("HW-whole")
ok("teacher creates homework for their own subject; assigned to themselves", w is not None and w.teacher_id == t1 and w.section_id is None and w.status == HomeworkStatus.ACTIVE)
form = T1.get("/homework/new").data.decode()
ok("a teacher's form only offers their own subjects", "Math (MTH)" in form and "Science (SCI)" not in form and "History (HIS)" in form)
ok("a teacher's form has no teacher dropdown", 'name="teacher_id"' not in form)
r = create(T1, title="HW-notmine", subject_id=sci)
ok("teacher can't assign homework for someone else's subject", (b"assigned to you" in r.data or b"Not a valid choice" in r.data) and row("HW-notmine") is None)
create(admin, title="HW-admin-default", subject_id=sci)
ok("admin: blank teacher -> the subject's own teacher", row("HW-admin-default").teacher_id == t2)
create(admin, title="HW-admin-explicit", subject_id=sci, teacher_id=t1)
ok("admin: explicit teacher respected", row("HW-admin-explicit").teacher_id == t1)
r = create(admin, title="HW-orphan", subject_id=nobody)
ok("subject with no teacher needs one chosen", b"no teacher assigned" in r.data and row("HW-orphan") is None)
create(admin, title="HW-orphan-ok", subject_id=nobody, teacher_id=t3)
ok("...and works once a teacher is chosen", row("HW-orphan-ok").teacher_id == t3)
r = create(admin, title="HW-badteacher", teacher_id=acct)
ok("a non-teacher can't be chosen as the teacher", (b"active teacher" in r.data or b"Not a valid choice" in r.data) and row("HW-badteacher") is None)
r = create(T1, title="HW-baddates", assigned_date=D(5), due_date=D(1)); ok("due before assigned rejected", b"before the assigned date" in r.data and row("HW-baddates") is None)
r = create(T1, title="HW-far", due_date=D(400)); ok("due more than a year out rejected", b"at most a year" in r.data and row("HW-far") is None)
r = create(T1, title=""); ok("missing title rejected", b"This field is required" in r.data)
r = create(T1, title="HW-wrongclass", subject_id=hist); ok("subject from a different class rejected", b"belongs to that class" in r.data and row("HW-wrongclass") is None)
r = create(T1, title="HW-wrongsec", section_id=s9a); ok("section from a different class rejected", b"doesn&#39;t belong" in r.data or b"belong to the chosen class" in r.data)
r = create(admin, title="HW-retired", subject_id=dead); ok("inactive subject rejected", row("HW-retired") is None)
r = create(T1, title="HW-nocls", class_id=99999); ok("unknown class rejected", row("HW-nocls") is None)
r = T3.get("/homework/new", **FR); ok("a teacher with no subjects is told why", b"no subjects you can assign" in r.data)
other = app.test_client(); register(other, "Other School", "other-school", "admin@other.com")
ok("no active session -> told to create one", b"activate an academic session" in other.get("/homework/new", **FR).data)

# ===== B. targets and the tracking table
create(T1, title="HW-8A", section_id=s8a)
h_whole, h_8a = hid("HW-whole"), hid("HW-8A")
page = T1.get(f"/homework/{h_whole}").data.decode()
ok("whole-class homework lists every ACTIVE student of the class", all(n in page for n in ("Stu One", "Stu Two", "Stu Three")))
ok("...but not other classes' students, nor inactive ones", "Stu Four" not in page and "Stu Five" not in page)
ok("students are in roll order", page.index("Stu One") < page.index("Stu Two"))
page8a = T1.get(f"/homework/{h_8a}").data.decode()
ok("section homework lists only that section", "Stu One" in page8a and "Stu Two" in page8a and "Stu Three" not in page8a)
ok("forms carry CSRF tokens", page.count('name="csrf_token"') >= 3)

# ===== C. recording submissions
save(T1, h_whole, Stu_One="submitted", Stu_Two="late", Stu_Three="missing")
s = subs(h_whole)
ok("submissions recorded", s == {"Stu One": SubmissionStatus.SUBMITTED, "Stu Two": SubmissionStatus.LATE, "Stu Three": SubmissionStatus.MISSING})
with app.app_context(): rows = {r.student.name: r for r in HomeworkSubmission.query.filter_by(homework_id=h_whole)}
ok("date recorded for submitted/late only", rows["Stu One"].submitted_on == today and rows["Stu Two"].submitted_on == today and rows["Stu Three"].submitted_on is None)
ok("marked_by is the recording teacher", all(r.marked_by_id == t1 for r in rows.values()))
page = T1.get(f"/homework/{h_whole}").data.decode()
ok("summary tiles + 67% handed in (2 of 3)", "67%" in page)
r = save(T1, h_whole, Stu_One="submitted", Stu_Two="late", Stu_Three="missing")
ok("saving with no changes says so", b"No changes to save" in r.data)
r = T1.post(f"/homework/{h_whole}/submissions", data={f"status_{stu['Stu One']}": "submitted", f"status_{stu['Stu Two']}": "submitted", f"remarks_{stu['Stu Two']}": "brought it on Tuesday", f"status_{stu['Stu Three']}": ""}, **FR)
ok("changes + clearing are counted", b"0 added, 1 changed, 1 cleared" in r.data)
s = subs(h_whole)
ok("late->submitted kept; blank cleared the row", s == {"Stu One": SubmissionStatus.SUBMITTED, "Stu Two": SubmissionStatus.SUBMITTED})
ok("remarks saved and shown", "brought it on Tuesday" in T1.get(f"/homework/{h_whole}").data.decode())
save(T1, h_whole, Stu_One="submitted", Stu_Two="submitted", Stu_Three="excused")
page = T1.get(f"/homework/{h_whole}").data.decode()
ok("excused students leave the denominator (2 of 2 = 100%)", "100%" in page)
before = subs(h_whole)
r = T1.post(f"/homework/{h_whole}/submissions", data={f"status_{stu['Stu One']}": "bogus", f"status_{stu['Stu Two']}": "missing"}, **FR)
ok("an unknown status saves nothing at all", b"Nothing was saved" in r.data and subs(h_whole) == before)
snap = subs(h_whole)
T1.post(f"/homework/{h_whole}/submissions", data={f"status_{stu['Stu Four']}": "submitted"}, **FR)
ok("a student from another class can't be recorded, and nobody else is touched", "Stu Four" not in subs(h_whole) and subs(h_whole) == snap)
snap8 = subs(h_8a)
T1.post(f"/homework/{h_8a}/submissions", data={f"status_{stu['Stu Three']}": "submitted"}, **FR)
ok("a student outside the section can't be recorded", "Stu Three" not in subs(h_8a) and subs(h_8a) == snap8)
before_partial = subs(h_whole)
T1.post(f"/homework/{h_whole}/submissions", data={f"status_{stu['Stu Two']}": "late"}, **FR)
after_partial = subs(h_whole)
ok("REGRESSION: a partial POST changes only the students it names", after_partial["Stu Two"] == SubmissionStatus.LATE and all(after_partial[k] == v for k, v in before_partial.items() if k != "Stu Two") and len(after_partial) == len(before_partial))
T1.post(f"/homework/{h_whole}/submissions", data={f"status_{stu['Stu Two']}": "submitted"}, **FR)
T1.post(f"/homework/{h_whole}/submissions", data={}, **FR)
ok("REGRESSION: an empty POST changes nothing", subs(h_whole) == {**before_partial})
T1.post(f"/homework/{h_whole}/submissions", data={f"status_{stu['Stu Two']}": "submitted", f"remarks_{stu['Stu Two']}": "kept?"}, **FR)
T1.post(f"/homework/{h_whole}/submissions", data={f"status_{stu['Stu Two']}": "submitted"}, **FR)
with app.app_context(): rem = HomeworkSubmission.query.filter_by(homework_id=h_whole, student_id=stu["Stu Two"]).first().remarks
ok("REGRESSION: omitting the remarks field keeps the existing remarks", rem == "kept?")
T1.post(f"/homework/{h_whole}/submissions", data={f"status_{stu['Stu Two']}": "submitted", f"remarks_{stu['Stu Two']}": ""}, **FR)
with app.app_context(): rem = HomeworkSubmission.query.filter_by(homework_id=h_whole, student_id=stu["Stu Two"]).first().remarks
ok("an explicitly empty remarks field clears them", rem is None)
admin.post(f"/homework/{h_8a}/submissions", data={f"status_{stu['Stu One']}": "missing"}, **FR)
ok("admin can record on any homework", subs(h_8a).get("Stu One") == SubmissionStatus.MISSING)

# ===== D. permissions
page = T2.get(f"/homework/{h_whole}").data.decode()
ok("another teacher can view, read-only", "Save submissions" not in page and "Only the assigned teacher" in page and "Stu One" in page)
codes = [T2.post(f"/homework/{h_whole}/submissions", data={}).status_code, T2.get(f"/homework/{h_whole}/edit").status_code,
         T2.post(f"/homework/{h_whole}/cancel").status_code, T2.post(f"/homework/{h_whole}/delete").status_code, T2.post(f"/homework/{h_whole}/reinstate").status_code]
ok("...and can't save, edit, cancel, delete or reinstate", codes == [403] * 5)
for name, c in (("accountant", ACC), ("receptionist", REC)):
    ok(f"{name}: no access to list/new/view/save", [c.get("/homework/").status_code, c.get("/homework/new").status_code, c.get(f"/homework/{h_whole}").status_code, c.post(f"/homework/{h_whole}/submissions").status_code] == [403] * 4)

# ===== E. list
create(T1, title="HW-past", assigned_date=D(-10), due_date=D(-5)); create(T1, title="HW-today", due_date=D(0)); create(T2, title="HW-T2", subject_id=sci)
lst = T1.get("/homework/").data.decode()
ok("teacher default = my upcoming homework only", "HW-whole" in lst and "HW-today" in lst and "HW-past" not in lst and "HW-T2" not in lst)
ok("scope=all shows other teachers' homework", "HW-T2" in T1.get("/homework/?scope=all").data.decode())
lst = admin.get("/homework/?when=all").data.decode()
ok("admin sees everyone's, any date", all(t in lst for t in ("HW-whole", "HW-past", "HW-T2", "HW-today")))
ok("when=past shows only past due", "HW-past" in admin.get("/homework/?when=past").data.decode() and "HW-whole" not in admin.get("/homework/?when=past").data.decode())
lst = T1.get("/homework/?when=all").data.decode()
ok("due-state badges", "Past due" in lst and "Due today" in lst and "Due in 3 days" in lst)
ok("class filter", "HW-whole" not in admin.get(f"/homework/?class_id={c9}&when=all").data.decode())
ok("title search", "HW-today" in admin.get("/homework/?q=today&when=all").data.decode() and "HW-whole" not in admin.get("/homework/?q=today&when=all").data.decode())
ok("progress column: whole class 2 of 2 (one excused)", "2 of 2" in T1.get("/homework/").data.decode())
ok("progress column: section homework counts only its 2 students", "0 of 2" in T1.get("/homework/?q=8A").data.decode() or "of 2" in T1.get("/homework/?q=8A").data.decode())

# ===== F. cancel / reinstate / delete / edit
T1.post(f"/homework/{h_whole}/cancel", **FR)
ok("cancel keeps the record, hides it from the default list", row("HW-whole").status == HomeworkStatus.CANCELLED and "HW-whole" not in T1.get("/homework/").data.decode())
ok("...and it appears under status=cancelled", "HW-whole" in T1.get("/homework/?status=cancelled&when=all").data.decode())
r = save(T1, h_whole, Stu_One="missing")
ok("a cancelled homework refuses new submissions", b"cancelled" in r.data and subs(h_whole)["Stu One"] == SubmissionStatus.SUBMITTED)
T1.post(f"/homework/{h_whole}/reinstate", **FR); ok("reinstate restores it", row("HW-whole").status == HomeworkStatus.ACTIVE)
r = T1.post(f"/homework/{h_whole}/delete", **FR)
ok("homework with submissions can't be deleted", b"can&#39;t be deleted" in r.data or b"be deleted" in r.data and row("HW-whole") is not None)
h_today = hid("HW-today"); T1.post(f"/homework/{h_today}/delete", **FR)
ok("homework without submissions can be deleted", row("HW-today") is None)

edit = T1.get(f"/homework/{h_whole}/edit").data.decode()
ok("edit form is pre-filled and has no class/subject/teacher controls", "HW-whole" in edit and 'name="class_id"' not in edit and 'name="subject_id"' not in edit and 'name="teacher_id"' not in edit)
T1.post(f"/homework/{h_whole}/edit", data={"title": "HW-whole-2", "description": "new", "assigned_date": D(0), "due_date": D(6), "class_id": c9, "subject_id": hist, "section_id": s9a}, **FR)
w = row("HW-whole-2")
ok("owner edits title/dates; tampered class/subject/section ignored", w.due_date == today + dt.timedelta(days=6) and w.class_id == c8 and w.subject_id == math and w.section_id is None)
r = T1.post(f"/homework/{h_whole}/edit", data={"title": "x", "assigned_date": D(5), "due_date": D(1)}, **FR)
ok("edit validates dates", b"before the assigned date" in r.data)
ok("admin's edit form has a teacher dropdown", 'name="teacher_id"' in admin.get(f"/homework/{h_whole}/edit").data.decode())
admin.post(f"/homework/{h_whole}/edit", data={"title": "HW-whole-2", "assigned_date": D(0), "due_date": D(6), "teacher_id": t2}, **FR)
ok("admin can reassign the teacher", row("HW-whole-2").teacher_id == t2)
ok("...after which the old teacher loses write access and the new one gains it", T1.get(f"/homework/{h_whole}/edit").status_code == 403 and T2.get(f"/homework/{h_whole}/edit").status_code == 200)
r = admin.post(f"/homework/{h_whole}/edit", data={"title": "x", "assigned_date": D(0), "due_date": D(6), "teacher_id": acct}, **FR)
ok("reassigning to a non-teacher is rejected", (b"active teacher" in r.data or b"Not a valid choice" in r.data) and row("HW-whole-2").teacher_id == t2)

# ===== G. roster changes + escaping
before = T2.get("/homework/").data.decode()
with app.app_context(): Student.query.filter_by(name="Stu One").first().status = StudentStatus.INACTIVE; db.session.commit()
page = T2.get(f"/homework/{h_whole}").data.decode()
ok("a student who becomes inactive drops out of the table", "Stu One" not in page)
ok("...and out of the progress numbers (1 of 1)", "1 of 1" in T2.get("/homework/?scope=all").data.decode())
create(T1, title="HW-<script>alert(1)</script>", description="<img src=x onerror=alert(1)>")
xid = hid("HW-<script>alert(1)</script>")
T1.post(f"/homework/{xid}/submissions", data={f"status_{stu['Stu Two']}": "late", f"status_{stu['Stu Two']}": "late", f"remarks_{stu['Stu Two']}": "<b onmouseover=alert(2)>"}, **FR)
page = admin.get(f"/homework/{xid}").data.decode()
ok("title, instructions and remarks are escaped", "<script>alert(1)" not in page and "<img src=x" not in page and "<b onmouseover" not in page and "&lt;" in page)

# ===== H. tenant isolation + audit
ok("other school can't open our homework", other.get(f"/homework/{h_whole}").status_code == 404)
ok("other school's list is empty", "HW-" not in other.get("/homework/?when=all").data.decode())
ok("other school can't save/cancel/delete ours", [other.post(f"/homework/{h_whole}/submissions").status_code, other.post(f"/homework/{h_whole}/cancel").status_code, other.post(f"/homework/{h_whole}/delete").status_code] == [404] * 3)
with app.app_context(): acts = {a.action for a in AuditLog.query.filter(AuditLog.action.like("homework.%")).all()}
ok("audit trail", {"homework.created", "homework.edited", "homework.cancelled", "homework.reinstated", "homework.deleted", "homework.submissions_saved"} <= acts)

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
