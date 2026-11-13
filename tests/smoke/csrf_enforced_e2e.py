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
import os, re, sys
os.environ.update(SECRET_KEY="x", DATABASE_URL=f"sqlite:///{_TMP}/csrf.db", MAIL_USERNAME="x@e.com", MAIL_PASSWORD="x")
if os.path.exists(f"{_TMP}/csrf.db"): os.remove(f"{_TMP}/csrf.db")
from unittest.mock import patch
from app import create_app
from app.extensions import db, mail
from app.models import User, SchoolClass, Section, Subject, Notice, Event, Homework, Expense, ExpenseCategory
from app.models.enums import UserRole

app = create_app("development"); app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
with app.app_context(): db.create_all()
c = app.test_client(); FR = dict(follow_redirects=True)
with patch.object(mail, "send", return_value=None):
    c.post("/auth/register", data={"school_name": "Csrf Test School", "school_slug": "csrf-test", "admin_name": "A", "admin_email": "a@s.com", "password": "TestPass123!", "confirm_password": "TestPass123!"}, **FR)
with app.app_context(): tok = User.query.filter_by(email="a@s.com").first().verification_token; sid = User.query.filter_by(email="a@s.com").first().school_id
c.get(f"/auth/verify/{tok}", **FR); c.post("/auth/login", data={"email": "a@s.com", "password": "TestPass123!"}, **FR)
c.post("/academic/sessions/new", data={"name": "2026", "start_date": "2026-08-01", "end_date": "2027-06-30", "is_active": "y"}, **FR)
c.post("/academic/classes/new", data={"name": "G8", "capacity": "40", "class_teacher_id": "0"}, **FR)
with app.app_context(): cid = SchoolClass.query.first().id
c.post(f"/academic/classes/{cid}/sections/new", data={"name": "A", "capacity": "40", "class_teacher_id": "0"}, **FR)
with app.app_context():
    sec = Section.query.first().id
    t = User(school_id=sid, name="Tea", email="t@s.com", role=UserRole.TEACHER, is_verified=True); t.set_password("x"); db.session.add(t); db.session.flush()
    db.session.add(Subject(school_id=sid, class_id=cid, name="Math", code="M", teacher_id=t.id)); db.session.commit()
    sub = Subject.query.first().id
c.post("/students/new", data={"admission_number": "A1", "admission_date": "2026-08-15", "name": "Stu", "class_id": str(cid), "section_id": str(sec), "roll_number": "1"}, **FR)
c.post("/notices/new", data={"title": "N", "body": "b", "audience": "all", "class_id": "0", "section_id": "0", "action": "publish"}, **FR)
c.post("/events/new", data={"title": "E", "event_type": "other", "start_date": "2026-11-05", "end_date": ""}, **FR)
c.post("/homework/new", data={"class_id": str(cid), "section_id": "0", "subject_id": str(sub), "teacher_id": "0", "title": "H", "assigned_date": "2026-11-01", "due_date": "2026-11-09"}, **FR)
c.post("/expenses/categories/new", data={"name": "Cat"}, **FR)
with app.app_context():
    nid, eid, hid = Notice.query.first().id, Event.query.first().id, Homework.query.first().id
    cat = ExpenseCategory.query.first().id
c.post("/expenses/new", data={"category_id": str(cat), "description": "x", "amount": "5", "expense_date": "2026-11-01", "payment_method": "cash"}, **FR)
with app.app_context(): xid = Expense.query.first().id

app.config["WTF_CSRF_ENABLED"] = True          # from here on, CSRF is enforced like in a real browser
def post_form(page, action_part):
    html = c.get(page).data.decode()
    for m in re.finditer(r"<form\b([^>]*)>(.*?)</form>", html, re.S):
        attrs, body = m.group(1), m.group(2)
        act = re.search(r'action="([^"]+)"', attrs)
        if act and action_part in act.group(1) and re.search(r'method="POST"', attrs, re.I):
            tk = re.search(r'name="csrf_token"[^>]*?value="([^"]+)"', body)
            data = {"csrf_token": tk.group(1)} if tk else {}
            return c.post(act.group(1), data=data).status_code, bool(tk)
    return None, None

checks = [
  ("notice: archive button",          f"/notices/{nid}", "/archive"),
  ("event: delete button",            f"/events/{eid}", "/delete"),
  ("homework: cancel button",         f"/homework/{hid}", "/cancel"),
  ("homework: save-submissions form", f"/homework/{hid}", "/submissions"),
  ("expense: delete button",          "/expenses/", "/delete"),
]
bad = 0
for label, page, part in checks:
    code, had = post_form(page, part)
    verdict = "OK " if code in (200, 302) else "REJECTED"
    if verdict != "OK ": bad += 1
    print(f"{verdict:9s} {label:34s} token in form: {had}   POST -> {code}")
print(f"\n{len(checks) - bad}/{len(checks)} accepted with CSRF enforced")
sys.exit(1 if bad else 0)
