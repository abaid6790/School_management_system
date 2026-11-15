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
os.environ["DATABASE_URL"] = _url or f"sqlite:///{_TMP}/p91.db"
import datetime as dt
from decimal import Decimal
from sqlalchemy import String, Integer, Date, Time, DateTime, Boolean, Numeric, Enum as SAEnum
from sqlalchemy.exc import IntegrityError
from app import create_app
from app.extensions import db
from app.models import (School, AcademicSession, SchoolClass, Section, Student, User, StudentEnrollment,
                        PromotionBatch, PromotionItem, TransferRecord)
from app.models.enums import (UserRole, EnrollmentStatus, PromotionBatchStatus, PromotionDecision, TransferType, TransferStatus)

app = create_app("development")
results = []
def ok(label, cond): print(("PASS " if cond else "FAIL ") + label); results.append(bool(cond))

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
    raise RuntimeError(f"no dummy for {col.name} {t}")
def mk(model, ids, **kw):
    data = dict(kw)
    for col in model.__table__.columns:
        if col.name in data or col.primary_key or col.nullable or col.default is not None or col.server_default is not None: continue
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

d = dt.date
with app.app_context():
    db.drop_all(); db.create_all()
    ids = {}
    try:
        ids["school_id"] = mk(School, ids, name="S", slug="s").id
        other_school = mk(School, ids, name="Other", slug="other").id
        s1 = mk(AcademicSession, ids, name="2026-27", is_active=False, start_date=d(2026, 8, 1), end_date=d(2027, 6, 30)).id
        s2 = mk(AcademicSession, ids, name="2027-28", is_active=False, start_date=d(2027, 8, 1), end_date=d(2028, 6, 30)).id
        s3 = mk(AcademicSession, ids, name="2028-29", is_active=False, start_date=d(2028, 8, 1), end_date=d(2029, 6, 30)).id
        c8 = mk(SchoolClass, {**ids, "session_id": s1}, name="Grade 8").id
        sec8 = mk(Section, {**ids, "class_id": c8}, name="A").id
        c9 = mk(SchoolClass, {**ids, "session_id": s2}, name="Grade 9").id
        sec9 = mk(Section, {**ids, "class_id": c9}, name="A").id
        sec9b = mk(Section, {**ids, "class_id": c9}, name="B").id
        ids.update(current_class_id=c8, current_section_id=sec8, current_session_id=s1, academic_session_id=s1)
        st1 = mk(Student, ids, admission_number="A1", name="Stu One").id
        st2 = mk(Student, ids, admission_number="A2", name="Stu Two").id
        st3 = mk(Student, ids, admission_number="A3", name="Stu Three").id
        user = mk(User, ids, school_id=ids["school_id"], email="u@x.com", name="U", role=UserRole.ADMIN).id
        db.session.commit()
    except Exception as e:
        print("FIXTURE SETUP FAILED:", type(e).__name__, str(e)[:300]); sys.exit(2)
    sid = ids["school_id"]
    print(f"fixtures ready on {db.engine.dialect.name}")

    # ===== one enrollment per student per session (new rule)
    def enroll(student, session, cls, sec, roll):
        return mk(StudentEnrollment, ids, school_id=sid, student_id=student, session_id=session, class_id=cls, section_id=sec,
                  roll_number=roll, enrolled_on=d(2026, 8, 1))
    must_commit("enrollment: a student's first enrollment in a session", lambda: enroll(st1, s1, c8, sec8, "1"))
    must_reject("enrollment: a SECOND enrollment of the same student in the same session is rejected", lambda: enroll(st1, s1, c8, sec8, "2"))
    must_commit("enrollment: the same student in the NEXT session is fine", lambda: enroll(st1, s2, c9, sec9, "1"))
    must_commit("enrollment: another student with a different roll", lambda: enroll(st2, s1, c8, sec8, "2"))
    must_reject("enrollment: the existing roll-number rule still holds", lambda: enroll(st3, s1, c8, sec8, "2"))

    # ===== promotion batches
    b1 = must_commit("batch: a draft for 2026-27 -> 2027-28", lambda: mk(PromotionBatch, ids, school_id=sid, source_session_id=s1, target_session_id=s2, created_by_id=user))
    must_reject("batch: source and target session must differ", lambda: mk(PromotionBatch, ids, school_id=sid, source_session_id=s1, target_session_id=s1))
    must_reject("batch: only ONE open draft per (source, target) pair", lambda: mk(PromotionBatch, ids, school_id=sid, source_session_id=s1, target_session_id=s2))
    must_commit("batch: a draft for a different pair is fine", lambda: mk(PromotionBatch, ids, school_id=sid, source_session_id=s2, target_session_id=s3))
    must_commit("batch: another school can have its own draft for the same session ids", lambda: mk(PromotionBatch, ids, school_id=other_school, source_session_id=s1, target_session_id=s2))
    def apply_batch():
        b = db.session.get(PromotionBatch, b1.id); b.status = PromotionBatchStatus.APPLIED; b.applied_at = dt.datetime.now(dt.timezone.utc); b.applied_by_id = user; return b
    must_commit("batch: applying the draft", apply_batch)
    must_commit("batch: once applied, a NEW draft for the same pair is allowed (class-by-class runs)", lambda: mk(PromotionBatch, ids, school_id=sid, source_session_id=s1, target_session_id=s2))
    bid = b1.id

    # ===== promotion items
    def item(student, decision, **kw):
        return mk(PromotionItem, ids, school_id=sid, batch_id=bid, student_id=student, from_class_id=c8, from_section_id=sec8, from_roll="1", decision=decision, **kw)
    must_commit("item: PROMOTE with a target class and section", lambda: item(st1, PromotionDecision.PROMOTE, to_class_id=c9, to_section_id=sec9))
    must_reject("item: PROMOTE without a target is rejected", lambda: item(st2, PromotionDecision.PROMOTE))
    must_reject("item: PROMOTE with a class but no section is rejected", lambda: item(st2, PromotionDecision.PROMOTE, to_class_id=c9))
    must_reject("item: REPEAT without a target is rejected", lambda: item(st2, PromotionDecision.REPEAT))
    must_reject("item: GRADUATE carrying a target is rejected", lambda: item(st2, PromotionDecision.GRADUATE, to_class_id=c9, to_section_id=sec9))
    must_reject("item: HOLD carrying a target is rejected", lambda: item(st2, PromotionDecision.HOLD, to_class_id=c9, to_section_id=sec9))
    must_commit("item: GRADUATE with no target", lambda: item(st2, PromotionDecision.GRADUATE))
    must_commit("item: HOLD with no target", lambda: item(st3, PromotionDecision.HOLD))
    must_reject("item: a student appears once per batch", lambda: item(st1, PromotionDecision.REPEAT, to_class_id=c9, to_section_id=sec9b))
    must_commit("item: REPEAT with a target", lambda: mk(PromotionItem, ids, school_id=sid, batch_id=db.session.query(PromotionBatch).filter_by(school_id=sid, source_session_id=s2).first().id,
                student_id=st1, from_class_id=c9, from_section_id=sec9, decision=PromotionDecision.REPEAT, to_class_id=c9, to_section_id=sec9b))

    # ===== transfer records
    def tr(student, **kw):
        base = dict(school_id=sid, student_id=student, transfer_type=TransferType.TRANSFER_OUT, effective_date=d(2027, 3, 1), reason="relocating")
        base.update(kw); return mk(TransferRecord, ids, **base)
    t1 = must_commit("transfer: an exit is recorded", lambda: tr(st1, certificate_number="TC-2027-0001", certificate_issued_on=d(2027, 3, 1), dues_amount=Decimal("1500.00")))
    must_reject("transfer: a second ACTIVE exit for the same student is rejected", lambda: tr(st1))
    def reverse():
        r = db.session.get(TransferRecord, t1.id); r.status = TransferStatus.REVERSED; r.reversed_at = dt.datetime.now(dt.timezone.utc); return r
    must_commit("transfer: reversing it (re-admission)", reverse)
    must_commit("transfer: after a reversal the student may leave again (history kept)", lambda: tr(st1, transfer_type=TransferType.WITHDRAWAL))
    must_reject("transfer: certificate numbers are unique within a school", lambda: tr(st2, certificate_number="TC-2027-0001", certificate_issued_on=d(2027, 3, 2)))
    must_commit("transfer: ...but may repeat in another school", lambda: mk(TransferRecord, {**ids, "school_id": other_school}, school_id=other_school, student_id=st3,
                transfer_type=TransferType.TRANSFER_OUT, effective_date=d(2027, 3, 1), certificate_number="TC-2027-0001", certificate_issued_on=d(2027, 3, 2)))
    must_reject("transfer: a certificate number needs an issue date", lambda: tr(st2, certificate_number="TC-2027-0002"))
    must_reject("transfer: negative dues are rejected", lambda: tr(st2, dues_amount=Decimal("-1")))
    must_commit("transfer: no certificate yet is fine (issued later)", lambda: tr(st2))

    # ===== relationships / defaults
    b = db.session.get(PromotionBatch, bid)
    ok("relationship: batch.items and defaults", len(b.items) == 3 and b.status == PromotionBatchStatus.APPLIED and b.source_session.name == "2026-27")
    t = db.session.query(TransferRecord).filter_by(student_id=st2).first()
    ok("defaults: a new transfer record is ACTIVE with dues 0 and not acknowledged", t.status == TransferStatus.ACTIVE and t.dues_amount == 0 and t.dues_acknowledged is False)

print(f"\n{sum(results)}/{len(results)} passed on {db.engine.dialect.name if False else app.config['SQLALCHEMY_DATABASE_URI'].split(':')[0]}")
sys.exit(0 if all(results) else 1)
