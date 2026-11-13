# Development Guide

## Setup

Follow [INSTALLATION.md](INSTALLATION.md), but point `DATABASE_URL` at a **throwaway development database** — scripted tests and experiments write real rows.

## Where things live

| Folder | Put here |
|---|---|
| `app/models/` | One SQLAlchemy model per file; import it in `app/models/__init__.py` so migrations see it |
| `app/forms/` | Flask-WTF form classes |
| `app/routes/` | One blueprint per module; registered in `app/__init__.py` |
| `app/services/` | Anything calculated or reused: totals, statuses, PDFs, email, audit logging |
| `app/utils/` | Decorators, tenant helper, tokens, uploads, navigation list |
| `app/templates/<module>/` | Templates extending `shell.html` (logged-in pages) or `base.html` (public auth pages) |

## Conventions that matter

1. **Scope every query by school.** Use `current_school_id()` from `app/utils/tenant.py`. Look up single records with `filter_by(id=..., school_id=current_school_id()).first_or_404()`. Forgetting this is a cross-tenant data leak.
2. **Protect every route:** `@login_required` then `@role_required(UserRole.…)`. Add an explicit ownership check if a role should only reach its own records.
3. **Don't store what you can derive.** Add a function in `app/services/` that computes it from the source rows (see `fee_service.compute_fee_totals`, `result_service.compute_student_result`, `attendance_service`).
4. **Audit important writes:** call `log_action(...)` *before* `db.session.commit()`. `log_action` only adds the row to the session, so the change and its audit entry commit together.
5. **Validate twice:** friendly checks in the route/service, hard constraints in the model. Cross-row rules (sums, ranges) can only live in the application.
6. **Prefer deactivating to deleting** anything other records point to.
7. **Business-rule errors** go back to the user as flash messages or field errors — never a bare exception.
8. **Every POST form needs a CSRF token** — `{{ form.hidden_tag() }}` for WTForms forms, or `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` for plain buttons. Tests that switch CSRF off cannot catch a missing token, so run `python tools/check_csrf.py` (fails on any form without one) and exercise new buttons with CSRF enforced (see `tests/smoke/csrf_enforced_e2e.py`).
9. **Notifications are best-effort side effects.** Call a `notify_*` function from `app/services/notification_service.py` *after* `db.session.commit()`, never inside the transaction. They swallow their own errors and return a summary that you can show in the flash message.
10. **Bulk forms: an absent field means "unchanged"; only an explicitly empty value clears.** Otherwise a partial or stale request can wipe records.

## Adding a new module — checklist

1. Model (+ enum members if needed) → export in `models/__init__.py`.
2. `flask db migrate -m "…"`, **read the generated file**, then `flask db upgrade`.
3. Form, routes (blueprint with `url_prefix`), service functions, templates.
4. Register the blueprint in `app/__init__.py`.
5. Point the sidebar entry's `endpoint` in `app/utils/navigation.py` at the new page (entries with `endpoint: None` render as "soon").
6. Update [ROLES_AND_PERMISSIONS.md](ROLES_AND_PERMISSIONS.md) and [CHANGELOG.md](../CHANGELOG.md).
7. Run `python tools/generate_docs.py` to refresh the schema, route and sidebar references. (New tables must be added to the `GROUPS` list at the top of that script, otherwise they appear under "Other".)

## Migrations

See [DATABASE.md](DATABASE.md#migrations). Two gotchas:

- Alembic **does not detect new enum values**. Adding a member to a Python enum requires a hand-written `op.execute("ALTER TYPE <enum_name> ADD VALUE '<NAME>'")` migration — remember the stored value is the member **name**, upper-case.
- `flask db migrate` needs the database at `head` first; run `flask db upgrade` before generating a new revision.

## Testing

`tests/smoke/` holds standalone scripts for each Phase 8 module (models, notices, events, homework, parent–teacher meetings, notifications) and an end-to-end check that presses real buttons **with CSRF enforced**. Run them all with `python tests/smoke/run_all.py` (SQLite in a temporary file by default); `step_8_5_ptm.py` and `step_8_6_notifications.py` also run on PostgreSQL by setting `TEST_DB=postgresql+psycopg2://user:password@localhost/dbname`. They create real rows in whichever database they point at, so use a throwaway one. Earlier phases (0–7) were verified with scripts that were not kept, and converting this suite into `pytest`, plus covering those phases, is the top testing item on the [roadmap](ROADMAP.md). If you write such a script, this is the pattern that worked:

```python
from unittest.mock import patch
from app import create_app
from app.extensions import db, mail

app = create_app("development")
app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)   # CSRF off for the test client only
with app.app_context():
    db.create_all()                      # or `flask db upgrade` on a scratch database
client = app.test_client()

with patch.object(mail, "send", return_value=None):      # never send real email
    client.post("/auth/register", data={...}, follow_redirects=True)
```

Pitfalls that produced false failures during development:

- **Always pass `follow_redirects=True`.** Flash messages queue up across redirects and are dumped onto the next page that renders, so an old message such as "Bilal admitted" can make a text search on a later page match by accident.
- **Jinja escapes apostrophes** (`can't` becomes `can&#39;t`), so search for text without apostrophes.
- A test user who is still logged in is redirected away from `/auth/login` — log out first.
- Use a throwaway database; tests create schools, users and money records.
- Run against PostgreSQL, not only SQLite: native enums, partial indexes and `CHECK` constraints behave differently.

## Known gotchas (each cost real debugging time)

| Gotcha | What to do |
|---|---|
| `db.Enum(PyEnum)` stores the member **name** (`'SUPER_ADMIN'`), not the value | Write `CHECK` constraints and raw SQL with the upper-case names |
| `SelectField` coerces with `str` when populated from an object (`obj=`), mangling enums | Set enum-backed form fields explicitly instead of `Form(obj=model)` |
| `Optional()` on an empty field skips *all* validators, including `validate_<field>` methods | Put conditional-required checks in the route |
| A validation error that is never rendered looks like "the form does nothing" | Always render `field.errors` in the template |
| Unpinned `SQLAlchemy`/`alembic` drifted to versions that switched the default Postgres driver | Keep the pins in `requirements.txt`; keep `+psycopg2` in `DATABASE_URL` |
| Editing a file mid-`str_replace` can clobber an adjacent `def` line | Run `python -m compileall app` after bulk edits |
| `del form.field` leaves the attribute set to `None` (it isn't removed) | Test `"field" in form`, not `hasattr` |
| A bulk form that treats a *missing* field as "blank" wipes data on a partial or stale POST | Absent = unchanged; only an explicitly empty value clears |
| `{{ value \| tojson }}` escapes non-ASCII (an en dash becomes `\u2013`), so tests searching the HTML for it fail | Decode the JSON instead |
| Alembic's autogenerated downgrade drops tables but not PostgreSQL enum types | Drop them in `downgrade()` (done for every migration; copy the pattern) |
| Flask-WTF only enforces CSRF when it is enabled, so tests with it off miss forms lacking tokens | `python tools/check_csrf.py` plus enforced-CSRF tests |
| Inserting a new import next to a multi-line `from x import (...)` can land inside the parentheses | Add it after a known single-line import and run `python -m compileall app` |

## Code style

Plain, explicit Python; short docstrings that explain **why** a rule exists (the models carry the reasoning for each constraint); type hints on service functions. Templates use Bootstrap 5 utility classes; keep forms rendering their own errors.
