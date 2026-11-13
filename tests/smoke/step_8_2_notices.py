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
import os, sys, datetime as dt
os.environ.update(SECRET_KEY="x", DATABASE_URL=f"sqlite:///{_TMP}/p82.db", MAIL_USERNAME="x@e.com", MAIL_PASSWORD="x")
if os.path.exists(f"{_TMP}/p82.db"): os.remove(f"{_TMP}/p82.db")
from unittest.mock import patch
from app import create_app
from app.extensions import db, mail
from app.models import User, SchoolClass, Section, Notice, AuditLog
from app.models.enums import UserRole, NoticeStatus

app = create_app("development"); app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
with app.app_context(): db.create_all()
FR = dict(follow_redirects=True)
results = []
def ok(label, cond): print(("PASS " if cond else "FAIL ") + label); results.append(bool(cond))

def register(client, school, slug, email):
    with patch.object(mail, "send", return_value=None):
        client.post("/auth/register", data={"school_name": school, "school_slug": slug, "admin_name": "Admin",
            "admin_email": email, "password": "TestPass123!", "confirm_password": "TestPass123!"}, **FR)
    with app.app_context():
        tok = User.query.filter_by(email=email).first().verification_token
    client.get(f"/auth/verify/{tok}", **FR)
    client.post("/auth/login", data={"email": email, "password": "TestPass123!"}, **FR)

admin = app.test_client(); register(admin, "Notice School", "notice-school", "admin@ns.com")
with app.app_context(): sid = User.query.filter_by(email="admin@ns.com").first().school_id
admin.post("/academic/sessions/new", data={"name": "2026-27", "start_date": "2026-08-01", "end_date": "2027-06-30", "is_active": "y"}, **FR)
admin.post("/academic/classes/new", data={"name": "Grade 8", "capacity": "40", "class_teacher_id": "0"}, **FR)
admin.post("/academic/classes/new", data={"name": "Grade 9", "capacity": "40", "class_teacher_id": "0"}, **FR)
with app.app_context():
    c8 = SchoolClass.query.filter_by(school_id=sid, name="Grade 8").first().id
    c9 = SchoolClass.query.filter_by(school_id=sid, name="Grade 9").first().id
admin.post(f"/academic/classes/{c8}/sections/new", data={"name": "A", "capacity": "40", "class_teacher_id": "0"}, **FR)
admin.post(f"/academic/classes/{c9}/sections/new", data={"name": "B", "capacity": "40", "class_teacher_id": "0"}, **FR)
with app.app_context():
    s8a = Section.query.filter_by(class_id=c8, name="A").first().id
    s9b = Section.query.filter_by(class_id=c9, name="B").first().id
    for name, role in [("teacher", UserRole.TEACHER), ("accountant", UserRole.ACCOUNTANT), ("reception", UserRole.RECEPTIONIST)]:
        u = User(school_id=sid, name=name.title(), email=f"{name}@ns.com", role=role, is_verified=True); u.set_password("StaffPass123!")
        db.session.add(u)
    db.session.commit()
clients = {}
for name in ("teacher", "accountant", "reception"):
    c = app.test_client(); c.post("/auth/login", data={"email": f"{name}@ns.com", "password": "StaffPass123!"}, **FR); clients[name] = c

def post_notice(title, audience="all", action="draft", **extra):
    data = {"title": title, "body": f"Body of {title}", "audience": audience, "class_id": "0", "section_id": "0", "action": action}
    data.update(extra)
    return admin.post("/notices/new", data=data, **FR)
def nid(title):
    with app.app_context(): return Notice.query.filter_by(title=title).first().id
def board(c): return c.get("/notices/", **FR).data.decode()
def status_of(title):
    with app.app_context(): return Notice.query.filter_by(title=title).first().status

# 1 -- draft lifecycle
post_notice("ZZ-draft1")
with app.app_context(): n = Notice.query.filter_by(title="ZZ-draft1").first()
ok("draft created with no published_at", n.status == NoticeStatus.DRAFT and n.published_at is None)
ok("admin list shows the draft", "ZZ-draft1" in admin.get("/notices/").data.decode())
ok("teacher board does not show a draft", "ZZ-draft1" not in board(clients["teacher"]))
ok("teacher opening a draft by id -> 404", clients["teacher"].get(f"/notices/{nid('ZZ-draft1')}").status_code == 404)
admin.post(f"/notices/{nid('ZZ-draft1')}/publish", **FR)
with app.app_context(): n = Notice.query.filter_by(title="ZZ-draft1").first()
ok("publish sets status + published_at", n.status == NoticeStatus.PUBLISHED and n.published_at is not None)
ok("teacher now sees it", "ZZ-draft1" in board(clients["teacher"]))
ok("teacher can open it by id", clients["teacher"].get(f"/notices/{nid('ZZ-draft1')}").status_code == 200)

# 2 -- audience visibility per role
for title, aud in [("ZZ-all", "all"), ("ZZ-staff", "staff"), ("ZZ-teachers", "teachers"), ("ZZ-parents", "parents"), ("ZZ-students", "students")]:
    post_notice(title, aud, "publish")
post_notice("ZZ-class", "class", "publish", class_id=str(c8), section_id=str(s8a))
tb, ab, rb = board(clients["teacher"]), board(clients["accountant"]), board(clients["reception"])
ok("teacher sees ALL, STAFF, TEACHERS", all(t in tb for t in ("ZZ-all", "ZZ-staff", "ZZ-teachers")))
ok("teacher does not see PARENTS/STUDENTS/CLASS", not any(t in tb for t in ("ZZ-parents", "ZZ-students", "ZZ-class")))
ok("accountant sees ALL, STAFF only", "ZZ-all" in ab and "ZZ-staff" in ab and "ZZ-teachers" not in ab and "ZZ-parents" not in ab)
ok("receptionist sees ALL, STAFF only", "ZZ-all" in rb and "ZZ-staff" in rb and "ZZ-teachers" not in rb)
ok("teacher opening a PARENTS notice by id -> 404", clients["teacher"].get(f"/notices/{nid('ZZ-parents')}").status_code == 404)
ok("accountant opening a TEACHERS notice by id -> 404", clients["accountant"].get(f"/notices/{nid('ZZ-teachers')}").status_code == 404)
adm = admin.get("/notices/").data.decode()
ok("admin sees every audience incl. class label", all(t in adm for t in ("ZZ-parents", "ZZ-students", "ZZ-class")) and "Class: Grade 8 – A" in adm)

# 3 -- target rules
before = 0
with app.app_context(): before = Notice.query.count()
r = post_notice("ZZ-bad1", "class")
ok("CLASS without a class is rejected with a message", b"Choose the class" in r.data)
r = post_notice("ZZ-bad2", "class", class_id=str(c8), section_id=str(s9b))
ok("section from another class is rejected", b"doesn&#39;t belong" in r.data or b"belong to the chosen class" in r.data)
with app.app_context(): ok("rejected notices were not saved", Notice.query.count() == before)
post_notice("ZZ-ignored", "all", class_id=str(c8))
with app.app_context(): n = Notice.query.filter_by(title="ZZ-ignored").first()
ok("a class posted with a non-CLASS audience is ignored", n.class_id is None and n.section_id is None)

# 4 -- expiry
r = post_notice("ZZ-pastexp", "all", "publish", expires_on="2020-01-01")
ok("expiry in the past is rejected", b"can&#39;t be in the past" in r.data or b"be in the past" in r.data)
with app.app_context(): ok("past-expiry notice not saved", Notice.query.filter_by(title="ZZ-pastexp").first() is None)
post_notice("ZZ-willexpire", "staff", "publish", expires_on=(dt.date.today() + dt.timedelta(days=5)).isoformat())
ok("future expiry shows on the board", "ZZ-willexpire" in board(clients["teacher"]))
with app.app_context():
    n = Notice.query.filter_by(title="ZZ-willexpire").first(); n.expires_on = dt.date.today() - dt.timedelta(days=1); db.session.commit()
ok("expired notice leaves the staff board", "ZZ-willexpire" not in board(clients["teacher"]))
ok("expired notice 404s for staff", clients["teacher"].get(f"/notices/{nid('ZZ-willexpire')}").status_code == 404)
ok("admin list flags it Expired", "Expired" in admin.get("/notices/?q=ZZ-willexpire").data.decode())
post_notice("ZZ-expdraft", "all", "draft", expires_on=(dt.date.today() + dt.timedelta(days=1)).isoformat())
with app.app_context():
    n = Notice.query.filter_by(title="ZZ-expdraft").first(); n.expires_on = dt.date.today() - dt.timedelta(days=2); db.session.commit()
r = admin.post(f"/notices/{nid('ZZ-expdraft')}/publish", **FR)
ok("publishing an already-expired notice is refused", b"expiry date has already passed" in r.data and status_of("ZZ-expdraft") == NoticeStatus.DRAFT)

# 5 -- pinning
post_notice("ZZ-plain", "all", "publish")
post_notice("ZZ-pinned", "all", "publish", is_pinned="y")
tb = board(clients["teacher"])
ok("pinned notice listed before older plain ones", tb.find("ZZ-pinned") < tb.find("ZZ-plain") < tb.find("ZZ-all"))

# 6 -- archive / republish / delete rules
tid = nid("ZZ-all")
admin.post(f"/notices/{tid}/archive", **FR)
ok("archived notice leaves the board", status_of("ZZ-all") == NoticeStatus.ARCHIVED and "ZZ-all" not in board(clients["teacher"]))
with app.app_context(): first_pub = Notice.query.filter_by(title="ZZ-all").first().published_at
admin.post(f"/notices/{tid}/publish", **FR)
with app.app_context(): n = Notice.query.filter_by(title="ZZ-all").first()
ok("re-publish restores it and keeps the original published_at", n.status == NoticeStatus.PUBLISHED and n.published_at == first_pub)
r = admin.post(f"/notices/{nid('ZZ-staff')}/delete", **FR)
ok("a published notice cannot be deleted", b"Only drafts can be deleted" in r.data and status_of("ZZ-staff") == NoticeStatus.PUBLISHED)
did = nid("ZZ-expdraft")
admin.post(f"/notices/{did}/delete", **FR)
with app.app_context(): ok("a draft can be deleted", Notice.query.filter_by(id=did).first() is None)
r = admin.post(f"/notices/{nid('ZZ-staff')}/archive", **FR)
r2 = admin.post(f"/notices/{nid('ZZ-staff')}/archive", **FR)
ok("archiving twice is refused politely", b"Only a published notice can be archived" in r2.data)
r3 = admin.post(f"/notices/{nid('ZZ-staff')}/delete", **FR)
ok("an archived notice cannot be deleted either", b"Only drafts can be deleted" in r3.data)

# 7 -- editing
eid = nid("ZZ-teachers")
admin.post(f"/notices/{eid}/edit", data={"title": "ZZ-teachers-edited", "body": "new body", "audience": "teachers", "class_id": "0", "section_id": "0"}, **FR)
with app.app_context(): n = Notice.query.filter_by(id=eid).first()
ok("editing a published notice keeps it published", n.title == "ZZ-teachers-edited" and n.status == NoticeStatus.PUBLISHED)
r = admin.get(f"/notices/{eid}/edit")
ok("edit form is pre-filled", b"ZZ-teachers-edited" in r.data and b'value="teachers"' in r.data and b"selected" in r.data)
post_notice("ZZ-editdraft", "all", "draft")
did2 = nid("ZZ-editdraft")
admin.post(f"/notices/{did2}/edit", data={"title": "ZZ-editdraft", "body": "b", "audience": "all", "class_id": "0", "section_id": "0", "action": "publish"}, **FR)
ok("'Save & publish' on a draft publishes it", status_of("ZZ-editdraft") == NoticeStatus.PUBLISHED)
cid = nid("ZZ-class")
admin.post(f"/notices/{cid}/edit", data={"title": "ZZ-class", "body": "b", "audience": "class", "class_id": str(c8), "section_id": "0", "action": "x"}, **FR)
with app.app_context(): n = Notice.query.filter_by(id=cid).first()
ok("editing a class notice can widen it to all sections", n.class_id == c8 and n.section_id is None)

# 8 -- roles
for name, c in clients.items():
    codes = [c.get("/notices/new").status_code, c.post("/notices/new", data={"title": "x"}).status_code,
             c.get(f"/notices/{eid}/edit").status_code, c.post(f"/notices/{eid}/publish").status_code,
             c.post(f"/notices/{eid}/archive").status_code, c.post(f"/notices/{eid}/delete").status_code]
    ok(f"{name}: new/edit/publish/archive/delete all 403", codes == [403] * 6)

# 9 -- escaping
post_notice("ZZ-xss", "all", "publish", body="<script>alert(1)</script> hello")
html = clients["teacher"].get(f"/notices/{nid('ZZ-xss')}").data.decode()
ok("notice body is HTML-escaped", "&lt;script&gt;alert(1)&lt;/script&gt;" in html and "<script>alert(1)" not in html)

# 10 -- list filters
ok("search by title", "ZZ-xss" in admin.get("/notices/?q=xss").data.decode() and "ZZ-pinned" not in admin.get("/notices/?q=xss").data.decode())
ok("filter by status=draft", "ZZ-draft1" not in admin.get("/notices/?status=draft").data.decode())

# 11 -- tenant isolation
other = app.test_client(); register(other, "Other School", "other-school", "admin@other.com")
ok("other school's admin cannot open our notice", other.get(f"/notices/{eid}").status_code == 404)
ok("other school's list is empty", "ZZ-" not in other.get("/notices/").data.decode())
ok("other school's admin cannot publish/delete ours", other.post(f"/notices/{nid('ZZ-xss')}/archive").status_code == 404 and other.post(f"/notices/{nid('ZZ-xss')}/delete").status_code == 404)

# 12 -- audit
with app.app_context(): acts = {a.action for a in AuditLog.query.filter(AuditLog.action.like("notice.%")).all()}
ok("audit trail has created/edited/published/archived/deleted", {"notice.created", "notice.edited", "notice.published", "notice.archived", "notice.deleted"} <= acts)

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
