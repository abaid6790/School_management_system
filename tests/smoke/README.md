# Smoke tests

Standalone scripts (not `pytest` yet) that drive the real application through Flask's test client and assert on what comes back
and on what lands in the database. They cover the Phase 8 modules and the CSRF behaviour:

| Script | Covers |
|---|---|
| `step_8_1_models.py` | The seven Phase 8 tables and their database constraints (incl. the PTM partial unique indexes) |
| `step_8_2_notices.py` | Notices: audiences, drafts/publish/archive, expiry, who sees what, escaping, tenant isolation |
| `step_8_3_events.py` | Calendar grid, holidays, validation, month navigation, attendance "closed" banner |
| `step_8_4_homework.py` | Homework, teacher-recorded submissions, progress, permissions, partial-POST safety |
| `step_8_5_ptm.py` | Parent–teacher meetings: slot grid, clashes, cancel/rebook, a database-level race test, note privacy |
| `step_8_6_notifications.py` | In-app notifications, guardian email + delivery log/retry, fee reminders, failure isolation |
| `csrf_enforced_e2e.py` | Presses real buttons with CSRF **enforced** (the other scripts switch it off) |

```
python tests/smoke/run_all.py            # everything, on temporary SQLite files
python tests/smoke/run_all.py homework   # just scripts with "homework" in the name
```

**Safety.** The scripts create real rows and some call `drop_all()`. They only ever use a temporary SQLite file, or the database named in
`TEST_DB` — never `DATABASE_URL` from your environment or `.env` — and they refuse any non-SQLite `TEST_DB` whose database name doesn't
contain `test`. To run on PostgreSQL, create a throwaway database (for example `sms_test`) and set
`TEST_DB=postgresql+psycopg2://user:password@localhost/sms_test` (`step_8_1`, `step_8_5` and `step_8_6` use it; the others use SQLite).

Mail is never sent: the notification tests replace the mail transport with an in-memory recorder.

Earlier phases (0–7) were verified with scripts that were not kept. Turning this suite into `pytest` and extending it to those phases is
planned for Phase 12.
