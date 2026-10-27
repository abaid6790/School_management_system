# Architecture

## Overview

A server-rendered Flask application using the **application-factory** pattern. There is no separate API or JavaScript frontend: each request is handled by a blueprint view that reads/writes PostgreSQL through SQLAlchemy and renders a Jinja2 template.

```
Browser ──HTTP──▶ Flask (create_app)
                    │  Flask-Login (session) → CSRF check → blueprint view
                    │
                    ├─ forms/      validate input (Flask-WTF)
                    ├─ services/   calculations, PDFs, email, audit logging
                    ├─ models/     SQLAlchemy entities + DB constraints
                    └─ templates/  Jinja2 (shell.html = sidebar layout)
                                  │
                                  ▼
                              PostgreSQL
```

Layering convention: **routes** handle HTTP and permissions and call into **services** for anything calculated (attendance %, results, fee balances, net salary, PDFs). **Models** hold structure and database-level rules. Forms are plain Flask-WTF classes.

## Application startup (`app/__init__.py`)

`create_app()` loads the config class chosen by `FLASK_ENV`, initialises the extensions (`db`, `migrate`, `login_manager`, `bcrypt`, `mail`, `csrf`), imports all models so migrations can see them, registers every blueprint, adds the `/health` check, and installs a context processor that gives every template the role-filtered sidebar (`nav_sections`).

## Multi-tenancy

One database, many schools. The **school is the tenant**.

- Every tenant-owned table has an indexed `school_id` foreign key (some child tables, such as `sections` or `exam_subjects`, inherit scope through their parent).
- `app/utils/tenant.py::current_school_id()` returns the logged-in user's school. **Every query in a route filters by it**, and single-record lookups use `filter_by(id=..., school_id=current_school_id()).first_or_404()` so another school's record id simply returns 404.
- Registration (`/auth/register`) creates a school and its first Admin in one transaction.
- A **Super Admin** (`role = SUPER_ADMIN`) has no school (`school_id` is NULL, enforced by a CHECK constraint) and currently can only use the dashboard and the audit log.

Isolation is enforced by application code, not by PostgreSQL row-level security. A route that forgets the `school_id` filter would leak data, which is why the filter is a firm convention (see [DEVELOPMENT.md](DEVELOPMENT.md)).

## Authentication and sessions

- Passwords are hashed with **bcrypt** (Flask-Bcrypt); minimum length 8.
- Login requires a **verified email** and an **active account**. `User.is_active` is `is_active_account AND is_verified`, so deactivating a teacher/staff member (employment status ≠ Active) immediately blocks login.
- Email links use `itsdangerous` signed, time-limited tokens with **separate salts per purpose**: email verification (24 h), password reset (1 h), account setup (24 h). A token for one purpose cannot be replayed for another.
- Admin-created accounts (teachers, login-enabled staff) never have a password chosen or seen by the Admin: a random unusable password is stored and the person sets their own through the emailed setup link.
- The `next` parameter after login is checked to stay on the same host (open-redirect protection).
- "Forgot password" and "resend verification" always give the same response whether or not the email exists.

## Authorization

`@login_required` + `@role_required(UserRole.X, ...)` on every protected view; the sidebar is filtered by role from one list (`app/utils/navigation.py`) but **hiding a link is cosmetic — the route check is the real control**. Some views add an **ownership rule**: a teacher may view only their own profile, attendance history, timetable, and salary records; marks for a subject may be entered only by that subject's assigned teacher (or an Admin). Full matrix: [ROLES_AND_PERMISSIONS.md](ROLES_AND_PERMISSIONS.md).

## Design principles

1. **Derive, don't store.** Attendance percentages, exam results/grades/ranks, fee discount/paid/remaining/status, and net salary are computed from the underlying rows on demand (`app/services/`). There is no `paid_amount` or `result` column that could disagree with the records it summarises.
2. **Preserve history.** A student's class/section/roll number per session lives in `student_enrollments`; attendance rows snapshot the class, section and session they were recorded in; discounts snapshot their computed amount; records that others depend on are deactivated rather than deleted (students, fee types, expense categories, grade bands can be removed only when unused).
3. **Two layers of rule enforcement.** The application checks first and gives a specific message ("Ms. Khan is already teaching Grade 8-B at this time"); the database constraint remains the safety net against races and bugs (unique timetable slots, positive payment amounts, one active session per school, "exactly one applicant/recipient" checks).
4. **Audit important actions.** `services/audit_service.log_action()` adds an `audit_logs` row **in the same transaction** as the change (it deliberately does not commit by itself), so an action and its audit entry succeed or fail together. It records action, table, record id, optional old/new values (JSON), user, school and IP.
5. **No fake data.** Nothing is seeded. Empty states are real empty states.

## Files and uploads

Student documents (PDF, JPG, JPEG, PNG; 8 MB request cap) are validated by **extension and by content** (PDF magic bytes; images must open and verify in Pillow). Files are stored under `instance/uploads/students/<school_id>/<student_id>/` with a random UUID filename (the original name is kept only as display text), outside any publicly served folder, and downloads go through a route that checks role and school.

## PDF generation

Report cards, fee receipts, fee statements and salary slips are built with **ReportLab** (pure Python). It was chosen over HTML-to-PDF tools such as WeasyPrint, which need system libraries (Cairo/Pango) that are a frequent source of Windows installation failures. All PDFs are A4.

## Security measures and known gaps

**In place:** bcrypt hashing; CSRF protection on all forms (Flask-WTF `CSRFProtect`); HttpOnly + SameSite=Lax session cookies (`Secure` in production); signed, expiring, purpose-specific email tokens; open-redirect check; upload content validation; per-school query scoping; server-side role and ownership checks; audit trail; SQL injection avoided by using the ORM throughout; Jinja2 auto-escaping.

**Known gaps — fix before exposing the app publicly:**

- **No login rate-limiting or account lockout** — passwords can be guessed without throttling.
- **Registration is open** — anyone who can reach the site can create a school.
- **Password-reset and account-setup links are stateless** signed tokens: valid until they expire, not single-use. (Email-verification tokens *are* cleared once used.)
- **Teachers have broad read access** — any teacher can see all students, exams and results in the school, and mark attendance for any class (not only their own).
- No custom error pages (default 403/404 pages), no password-strength rules beyond length, no two-factor authentication.
- Audit entries store old/new values, but the audit-log screen does not display them yet.

## Time and money

Timestamps are stored timezone-aware in UTC; plain dates (due dates, attendance dates, etc.) are `DATE`s. "Today" in the app means the server's local date. Money is `NUMERIC(10,2)` with no currency stored or shown — amounts are displayed as plain numbers.
