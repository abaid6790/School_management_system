# Changelog

Work is delivered in phases; each phase was verified with scripted end-to-end checks (including real constraint-violation attempts), and from Phase 4 onward the database migrations were generated and tested against a real PostgreSQL instance.

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
