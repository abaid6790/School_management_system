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
os.environ.setdefault("SECRET_KEY", "x"); os.environ.setdefault("MAIL_USERNAME", "x@e.com"); os.environ.setdefault("MAIL_PASSWORD", "x")
os.environ["DATABASE_URL"] = _url or f"sqlite:///{_TMP}/p81.db"
import sys, datetime as dt
from decimal import Decimal
from sqlalchemy import String, Integer, Date, Time, DateTime, Boolean, Numeric
from sqlalchemy import Enum as SAEnum
from sqlalchemy.exc import IntegrityError
from app import create_app
from app.extensions import db
from app.models import (School, AcademicSession, SchoolClass, Section, Subject, User, Student, Guardian,
                        Notice, Event, Homework, HomeworkSubmission, PTMMeeting, PTMAppointment, Notification)
from app.models.enums import *

app = create_app('development')
results = []
def ok(label, cond):
    print(("PASS " if cond else "FAIL ") + label); results.append(bool(cond))

def dummy(col):
    t = col.type
    if isinstance(t, SAEnum): return list(t.enum_class)[0]
    if isinstance(t, String):
        s = f"{col.name}-x"
        return s[:t.length] if t.length else s
    if isinstance(t, Boolean): return False
    if isinstance(t, Integer): return 1
    if isinstance(t, Numeric): return Decimal("1")
    if isinstance(t, DateTime): return dt.datetime.now(dt.timezone.utc)
    if isinstance(t, Date): return dt.date(2026, 9, 1)
    if isinstance(t, Time): return dt.time(9, 0)
    raise RuntimeError(f"no dummy for {col.name} {t}")

def mk(model, ids, **kw):
    data = dict(kw)
    for col in model.__table__.columns:
        if col.name in data or col.primary_key: continue
        if col.nullable or col.default is not None or col.server_default is not None: continue
        if col.foreign_keys:
            if col.name in ids: data[col.name] = ids[col.name]; continue
            raise RuntimeError(f"{model.__name__}.{col.name}: required FK not supplied")
        data[col.name] = dummy(col)
    obj = model(**data); db.session.add(obj); db.session.flush(); return obj

def must_commit(label, build):
    try:
        obj = build(); db.session.commit(); ok(label, True); return obj
    except Exception as e:
        db.session.rollback(); ok(f"{label}  [{type(e).__name__}: {str(e)[:140]}]", False)

def must_reject(label, build):
    try:
        build(); db.session.commit(); db.session.rollback(); ok(label, False)
    except IntegrityError:
        db.session.rollback(); ok(label, True)
    except Exception as e:
        db.session.rollback(); ok(f"{label}  [unexpected {type(e).__name__}: {str(e)[:120]}]", False)

d = dt.date; t = dt.time
with app.app_context():
    db.drop_all(); db.create_all()
    ids = {}
    try:
        ids['school_id'] = mk(School, ids, name='S', slug='s').id
        ids['session_id'] = mk(AcademicSession, ids, name='2026', start_date=d(2026,8,1), end_date=d(2027,6,30)).id
        ids['class_id'] = mk(SchoolClass, ids, name='Grade 8').id
        ids['section_id'] = mk(Section, ids, name='A').id
        ids['subject_id'] = mk(Subject, ids, name='Math', code='MATH').id
        ids.update(current_class_id=ids['class_id'], current_section_id=ids['section_id'], academic_session_id=ids['session_id'])
        t1 = mk(User, ids, school_id=ids['school_id'], email='t1@x.com', name='T1', role=UserRole.TEACHER).id
        t2 = mk(User, ids, school_id=ids['school_id'], email='t2@x.com', name='T2', role=UserRole.TEACHER).id
        s1 = mk(Student, ids, admission_number='A1', name='Stu One').id
        s2 = mk(Student, ids, admission_number='A2', name='Stu Two').id
        g1 = mk(Guardian, ids).id
        db.session.commit()
    except Exception as e:
        print("FIXTURE SETUP FAILED:", type(e).__name__, str(e)[:300]); sys.exit(2)
    sch, cls, sec, sub, ses = ids['school_id'], ids['class_id'], ids['section_id'], ids['subject_id'], ids['session_id']
    print(f"fixtures ready on {db.engine.dialect.name}")

    # ---- Notice
    must_commit("notice: audience ALL, no class",            lambda: mk(Notice, ids, title='n1', body='b', audience=NoticeAudience.ALL))
    must_commit("notice: CLASS with class",                  lambda: mk(Notice, ids, title='n2', body='b', audience=NoticeAudience.CLASS, class_id=cls))
    must_commit("notice: CLASS with class + section",        lambda: mk(Notice, ids, title='n3', body='b', audience=NoticeAudience.CLASS, class_id=cls, section_id=sec))
    must_reject("notice: CLASS without a class rejected",    lambda: mk(Notice, ids, title='x', body='b', audience=NoticeAudience.CLASS))
    must_reject("notice: ALL carrying a class rejected",     lambda: mk(Notice, ids, title='x', body='b', audience=NoticeAudience.ALL, class_id=cls))
    must_reject("notice: section without class rejected",    lambda: mk(Notice, ids, title='x', body='b', audience=NoticeAudience.TEACHERS, section_id=sec))
    # ---- Event
    must_commit("event: multi-day with times",               lambda: mk(Event, ids, title='e1', start_date=d(2026,10,1), end_date=d(2026,10,3), start_time=t(9), end_time=t(15)))
    must_commit("event: multi-day, end time earlier is fine",lambda: mk(Event, ids, title='e2', start_date=d(2026,10,1), end_date=d(2026,10,2), start_time=t(15), end_time=t(9)))
    must_reject("event: end date before start rejected",     lambda: mk(Event, ids, title='x', start_date=d(2026,10,5), end_date=d(2026,10,4)))
    must_reject("event: same-day end time <= start rejected",lambda: mk(Event, ids, title='x', start_date=d(2026,10,5), end_date=d(2026,10,5), start_time=t(10), end_time=t(9)))
    # ---- Homework + submissions
    hw = must_commit("homework: whole class (no section)",   lambda: mk(Homework, ids, title='h1', assigned_date=d(2026,9,1), due_date=d(2026,9,5), teacher_id=t1))
    must_commit("homework: specific section",                lambda: mk(Homework, ids, title='h2', assigned_date=d(2026,9,1), due_date=d(2026,9,1), section_id=sec, teacher_id=t1))
    must_reject("homework: due before assigned rejected",    lambda: mk(Homework, ids, title='x', assigned_date=d(2026,9,5), due_date=d(2026,9,1)))
    hwid = hw.id
    must_commit("submission: first record",                  lambda: mk(HomeworkSubmission, ids, homework_id=hwid, student_id=s1, status=SubmissionStatus.SUBMITTED))
    must_reject("submission: duplicate per student rejected",lambda: mk(HomeworkSubmission, ids, homework_id=hwid, student_id=s1, status=SubmissionStatus.LATE))
    must_commit("submission: other student fine",            lambda: mk(HomeworkSubmission, ids, homework_id=hwid, student_id=s2, status=SubmissionStatus.MISSING))
    # ---- PTM
    m = must_commit("ptm meeting: valid",                    lambda: mk(PTMMeeting, ids, title='PTM', meeting_date=d(2026,11,1), start_time=t(9), end_time=t(12), slot_minutes=15))
    must_reject("ptm meeting: end <= start rejected",        lambda: mk(PTMMeeting, ids, title='x', meeting_date=d(2026,11,1), start_time=t(12), end_time=t(9)))
    must_reject("ptm meeting: slot of 3 min rejected",       lambda: mk(PTMMeeting, ids, title='x', meeting_date=d(2026,11,1), start_time=t(9), end_time=t(12), slot_minutes=3))
    must_reject("ptm meeting: slot of 200 min rejected",     lambda: mk(PTMMeeting, ids, title='x', meeting_date=d(2026,11,1), start_time=t(9), end_time=t(12), slot_minutes=200))
    mid = m.id
    a1 = must_commit("appointment: teacher1+student1 @09:00",lambda: mk(PTMAppointment, ids, meeting_id=mid, teacher_id=t1, student_id=s1, slot_start=t(9), guardian_id=g1))
    must_reject("appointment: teacher double-booked rejected",lambda: mk(PTMAppointment, ids, meeting_id=mid, teacher_id=t1, student_id=s2, slot_start=t(9)))
    must_reject("appointment: student double-booked rejected",lambda: mk(PTMAppointment, ids, meeting_id=mid, teacher_id=t2, student_id=s1, slot_start=t(9)))
    must_commit("appointment: different teacher+student ok", lambda: mk(PTMAppointment, ids, meeting_id=mid, teacher_id=t2, student_id=s2, slot_start=t(9)))
    a1id = a1.id
    def cancel():
        a = db.session.get(PTMAppointment, a1id); a.status = AppointmentStatus.CANCELLED; return a
    must_commit("appointment: cancel the first one",         cancel)
    must_commit("appointment: cancelled slot can be rebooked",lambda: mk(PTMAppointment, ids, meeting_id=mid, teacher_id=t1, student_id=s1, slot_start=t(9)))
    must_reject("appointment: rebooked slot is protected again", lambda: mk(PTMAppointment, ids, meeting_id=mid, teacher_id=t1, student_id=s2, slot_start=t(9)))
    # ---- Notification
    must_commit("notification: to a user",                   lambda: mk(Notification, ids, title='n', message='m', recipient_user_id=t1))
    must_commit("notification: to a guardian",               lambda: mk(Notification, ids, title='n', message='m', recipient_guardian_id=g1))
    must_reject("notification: both recipients rejected",    lambda: mk(Notification, ids, title='n', message='m', recipient_user_id=t1, recipient_guardian_id=g1))
    must_reject("notification: no recipient rejected",       lambda: mk(Notification, ids, title='n', message='m'))
    # ---- relationships
    ok("relationship: homework.submissions", len(db.session.get(Homework, hwid).submissions) == 2)
    ok("relationship: meeting.appointments (3 rows incl. cancelled)", len(db.session.get(PTMMeeting, mid).appointments) == 3)

print(f"\n{sum(results)}/{len(results)} passed on", create_app('development').config['SQLALCHEMY_DATABASE_URI'].split(':')[0])
sys.exit(0 if all(results) else 1)
