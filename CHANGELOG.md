# Changelog

Work is delivered in phases; each phase was verified with scripted end-to-end checks (including real constraint-violation attempts), and from Phase 4 onward the database migrations were generated and tested against a real PostgreSQL instance.

## Phase 8 — Communication and engagement
- **Notices:** Admin drafts, publishes, pins, expires and archives notices addressed to everyone, all staff, teachers, parents, students or one class/section. Staff see a read-only board of what is addressed to them; published notices are never deleted, only archived.
- **Events and calendar:** Monday-first month grid (multi-day events fill every day), upcoming list with filters, holidays that mark the school as closed, and a "school is closed" warning on the student and teacher attendance pages.
- **Homework:** teachers assign homework for their own subjects (Admin for any) to a class or section; the teacher records Submitted / Late / Missing / Excused per student; progress is calculated, with excused students left out of the denominator. Cancel rather than delete once submissions exist.
- **Parent–teacher meetings:** a meeting day is divided into equal slots; staff book appointments on parents' behalf with friendly double-booking messages (database partial unique indexes back them up, and a cancelled slot can be rebooked while history is kept); outcome and notes are private to the teacher and Admin.
- **Notifications:** sidebar bell and inbox for staff; email to guardians (who have no logins) after the database commit, in a background thread, with a per-recipient record of sent / failed / no address; Admin delivery log with retry (also recovers emails stuck pending after a restart); manual "Send fee reminders" on the defaulters report with a 24-hour guard against double sends. Triggers: first publication of a notice, new events (families only for closures), homework assigned, meeting appointments booked/cancelled, leave decisions.
- **Database:** migration `7cd218daa2d4` adds 7 tables (notices, events, homework, homework_submissions, ptm_meetings, ptm_appointments, notifications). Verified on PostgreSQL: applies cleanly, matches the models (`flask db check`), and the whole chain now round-trips down to an empty database and back up.
- **Fixed — missing CSRF tokens (affected phases 0–7):** CSRF protection is on app-wide, but 23 POST-only forms (delete, archive, mark paid, change status, activate session, cancel leave, …) had no token, so in a real browser they failed with "400 Bad Request: The CSRF token is missing". Every earlier test ran with CSRF switched off, so it was never seen. All forms now carry a token, `tools/check_csrf.py` guards against regressions, and a standalone `csrf_hotfix.py` was provided for existing Phase 7 installs.
- **Fixed — migration downgrades** left PostgreSQL enum types behind, so rolling a migration back and re-applying it failed ("type already exists"). Every migration's `downgrade()` now drops its enum types. (Only downgrade code changed; upgrades are untouched.)
- **Tests:** smoke-test scripts for each Phase 8 module plus an end-to-end check with CSRF enforced now ship in `tests/smoke`.

## Documentation and hardening (after Phase 7)
- Added this documentation set (`README.md`, `docs/`) and `tools/generate_docs.py`, which regenerates the schema, route and sidebar references from the code.
- **Pinned `SQLAlchemy==2.0.36` and `alembic==1.13.3`.** They had been unpinned transitive dependencies; a fresh install pulled SQLAlchemy 2.1, whose default Postgres driver changed and broke connections (`No module named 'psycopg'`). `.env.example` now uses the explicit `postgresql+psycopg2://` URL.
- `run.py` now binds to `127.0.0.1` by default (was `0.0.0.0` with the debugger on); override with `APP_HOST`/`APP_PORT`.
- Route reference marks public routes (login, register, …) as public rather than "any logged-in user".

## Phase 7 — School finance
Expense categories and expenses (filters, totals); salary records for teachers and staff (generate, edit while pending, mark paid, slip PDF, one per person per month); teacher self-service salary history; cash-basis financial summary (income, expenses, salaries paid, net balance, expenses by category). Migration `bfb00a01e2b8`. Fixed: a validation error on the expense form was rejected correctly but never displayed.

## Phase 6 — Student fees
Fee types; individual and bulk fee assignment (re-running skips students already charged); partial payments with receipt numbers and receipt PDFs; discounts with required reasons (cannot exceed the fee or drop net below what's been paid); calculated Paid/Partially Paid/Unpaid/Overdue status; defaulters report; fee statement (view and PDF). Migration `a5fb460d2ad5`.

## Phase 5 — Examinations
Exams per class, per-subject papers with their own marks, validated bulk marks entry (only the assigned teacher or an Admin), configurable grade bands, on-demand results (a student passes only if every marked subject passes), competition-style ranking, report cards with persisted remarks and PDF. Migration `3ccb96b401d8`.

## Phase 4 — Timetable
School-wide periods; weekly grid per class/section; teacher, section and room clash prevention (friendly message plus database constraints); teacher's own weekly view; whole-school daily view. Switched the project's database from Supabase to **local PostgreSQL** and verified the whole schema against a real server for the first time. Migration `eae5901e25c4` (initial schema).

## Phase 3 — Attendance
Daily student and teacher attendance (re-marking updates, never duplicates), attendance % and low-attendance report, leave requests for students/teachers/staff, and approval that syncs into attendance. Fixed a latent bug where hand-written `CHECK` constraints compared against enum *values* while PostgreSQL stores enum *names* (affected the super-admin and leave constraints).

## Phases 1–2 — People
Students with history-preserving enrollments, guardians shared across siblings, teachers and staff (Admin-created accounts get an emailed setup link instead of an assigned password), secure document upload with content validation. Admissions were absorbed into the student-creation flow (hence no separate Phase 2). Academic setup screens (sessions, classes, sections, subjects) were added here after being missed in Phase 0.

## Phase 0 — Foundation
Application factory, configuration, multi-tenant schema, registration with email verification, login/logout, password reset, role-based access, sidebar shell, audit log.
