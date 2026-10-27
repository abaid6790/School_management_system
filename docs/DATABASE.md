# Database Guide

PostgreSQL, accessed through SQLAlchemy 2.0, with schema changes managed by Alembic via Flask-Migrate. The full table/column/constraint listing is in [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) (generated from the models).

## Conventions

- **Tenancy:** tenant-owned tables have an indexed `school_id` (FK to `schools`, `ON DELETE CASCADE`). See [ARCHITECTURE.md](ARCHITECTURE.md#multi-tenancy).
- **Timestamps:** most tables have `created_at` / `updated_at` (timezone-aware, UTC) via `TimestampMixin`.
- **Money:** `NUMERIC(10,2)`; marks are `NUMERIC(6,2)`. No currency is stored.
- **Enums:** native PostgreSQL `ENUM` types. ⚠️ SQLAlchemy stores the Python member **name** (`'ADMIN'`, `'SUPER_ADMIN'`, `'TEACHER'`), *not* its lowercase `.value`. This matters in two places: hand-written `CHECK` constraints and raw SQL must use the upper-case names; and **adding a new enum member needs a hand-written migration** (`ALTER TYPE ... ADD VALUE`) because Alembic's autogenerate does not detect enum value changes.
- **Foreign keys:** child rows cascade from their parent school; `fee_types` and `expense_categories` are referenced with `ON DELETE RESTRICT` so a category with history cannot be deleted; "who did this" user links use `SET NULL`.
- **Deactivate, don't delete:** students, fee types, expense categories and similar records have a status instead of a delete action.
- **Derived values are not columns:** there is no stored attendance %, result, fee balance, fee status or net salary.

## Rules enforced by the database

These are constraints, not just application checks (names appear in [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)):

- One **active academic session** per school (partial unique index `uq_one_active_session_per_school`); session end after start.
- Unique **admission number** per school; unique **roll number** per (session, class, section).
- Unique **employee ID** per school (teachers and staff); unique **receipt number** per school.
- **Timetable clashes:** a section, a teacher, or a room cannot be booked twice in the same (session, day, period).
- One **attendance** row per student per day and per teacher per day.
- A **leave request** has exactly one applicant (student, teacher, or staff) matching its role; end date not before start date.
- A **salary record** has exactly one recipient (teacher or staff) matching its role; one record per recipient per month; no negative components.
- **Payments** and **expenses** must be greater than zero; **marks** cannot be negative; **discounts** cannot be negative; passing marks cannot exceed maximum marks.
- A **super admin** has no school; every other role must have one.

Rules that span several rows are enforced in the application only (a database `CHECK` cannot sum other rows): obtained marks ≤ the paper's maximum, total discounts ≤ the fee amount, a payment ≤ the remaining balance, no overlapping grade bands.

## Migrations

| Revision | Contents |
|---|---|
| `eae5901e25c4` | Initial schema: foundation, people, attendance & leave, periods and timetable |
| `3ccb96b401d8` | Phase 5: exams, exam subjects, marks, grade bands, report-card remarks |
| `a5fb460d2ad5` | Phase 6: fee types, student fees, discounts, payments |
| `bfb00a01e2b8` | Phase 7: expense categories, expenses, salary records |

```bat
flask db upgrade                         :: apply all pending migrations
flask db current                         :: show the revision the database is at
flask db history                         :: list revisions
flask db migrate -m "describe change"    :: generate a new migration after editing models
flask db downgrade                       :: step back one revision (destructive)
```

Always **read the generated migration file** before applying it, and run `flask db upgrade` on a copy of real data first. `flask db migrate` requires the database to already be at `head`.

## Resetting a development database

This **destroys all data**:

```bat
psql -U postgres -c "DROP DATABASE school_management_db;"
psql -U postgres -c "CREATE DATABASE school_management_db;"
flask db upgrade
```

## Backup and restore

See [INSTALLATION.md](INSTALLATION.md#11-backups). The uploads folder must be backed up alongside the database.
