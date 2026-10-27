# School Management System (SMS)

A multi-tenant web application for running a school's day-to-day operations — admissions, attendance, timetables, exams and report cards, student fees, and the school's own payroll and expenses — built with **Flask** and **PostgreSQL**.

Every number on every screen is calculated from real database records. The application ships with **no demo data**: a newly registered school starts empty.

> **Status — Phases 0–7 of 12 complete.** The core academic and financial workflow works end to end. Several planned modules (dashboard statistics, homework, notices, events, promotion, ID cards, import/export, backups, settings screens, parent/student portals) are **not built yet** — see [docs/ROADMAP.md](docs/ROADMAP.md) for an honest list. There is currently **no automated test suite** (features were verified with scripted smoke tests; turning those into a pytest suite is on the roadmap).

## What works today

| Area | Highlights |
|---|---|
| **Accounts & access** | School self-registration, email verification, login/logout, password reset, four staff roles with server-side enforcement, per-school data isolation, audit trail |
| **Academic setup** | Academic sessions (one active at a time), classes, sections, subjects, school-wide period grid |
| **People** | Students (with enrollment history), guardians shared across siblings, teachers, non-teaching staff, secure document upload |
| **Attendance** | Daily student and teacher attendance, attendance %, low-attendance report, leave requests that sync into attendance on approval |
| **Timetable** | Weekly grid per class/section, teacher and daily views, teacher/room/class clash prevention |
| **Examinations** | Exams, per-subject papers, validated marks entry, configurable grade bands, results with pass/fail and ranking, report-card PDFs with remarks |
| **Student fees** | Fee types, individual and bulk assignment, partial payments, receipts (PDF), discounts with recorded reasons, defaulters report, fee statements (PDF) |
| **School finance** | Expense categories and expenses, teacher/staff salary records and salary slips (PDF), teacher self-service salary history, cash-basis financial summary |

Role-by-role details: [docs/ROLES_AND_PERMISSIONS.md](docs/ROLES_AND_PERMISSIONS.md). Step-by-step workflows: [docs/USER_GUIDE.md](docs/USER_GUIDE.md).

## Tech stack

- **Backend:** Python 3.10+ (developed on 3.12), Flask 3, SQLAlchemy 2.0, Flask-Migrate/Alembic, Flask-Login, Flask-WTF (CSRF), Flask-Bcrypt, Flask-Mail
- **Database:** PostgreSQL 14+ (tested on 16)
- **PDFs:** ReportLab (pure Python — no system libraries to install on Windows)
- **Frontend:** Server-rendered Jinja2 templates, Bootstrap 5 and Bootstrap Icons loaded from a CDN (internet access needed in the browser), a little vanilla JavaScript

## Quick start (Windows)

Full instructions, including PostgreSQL and Gmail setup, are in [docs/INSTALLATION.md](docs/INSTALLATION.md). In short:

```bat
cd D:\SMS
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
:: edit .env: SECRET_KEY, DATABASE_URL, MAIL_USERNAME, MAIL_PASSWORD
:: create the database first (see docs/INSTALLATION.md), then:
set FLASK_APP=run.py
flask db upgrade
python run.py
```

Then open <http://127.0.0.1:5000/auth/register> to register your school. (PowerShell: use `$env:FLASK_APP = "run.py"` instead of `set`.)

> **Important:** `flask db upgrade` creates all tables. If you skip it, logging in fails with `relation "users" does not exist` — see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## Documentation

| Document | What it covers |
|---|---|
| [docs/INSTALLATION.md](docs/INSTALLATION.md) | Prerequisites, PostgreSQL, `.env` settings, Gmail App Password, first run, production notes, backups |
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | First-time setup checklist and day-to-day workflows for every module |
| [docs/ROLES_AND_PERMISSIONS.md](docs/ROLES_AND_PERMISSIONS.md) | Who can do what, ownership rules, account creation flows |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | How the app is structured, multi-tenancy, security measures, design principles |
| [docs/DATABASE.md](docs/DATABASE.md) | Database conventions, migrations, backup/restore |
| [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) | Every table, column and constraint *(generated)* |
| [docs/ROUTES.md](docs/ROUTES.md) | Every URL and the roles allowed *(generated)* |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Conventions, adding a module, migrations workflow, testing notes, known gotchas |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Real errors and their fixes |
| [docs/ROADMAP.md](docs/ROADMAP.md) | What is not built yet, and known limitations |
| [CHANGELOG.md](CHANGELOG.md) | What each phase delivered |

## Project layout

```
run.py                  Development server entry point (binds 127.0.0.1 by default)
config.py               Settings read from environment / .env
requirements.txt        Pinned dependencies
.env.example            Template for your .env
migrations/versions/    Alembic migrations (apply with `flask db upgrade`)
tools/generate_docs.py  Regenerates the generated docs from the code
docs/                   Documentation
app/
  __init__.py           Application factory, blueprint registration, sidebar context
  extensions.py         db, login manager, mail, CSRF, bcrypt, migrate
  models/               SQLAlchemy models (one file per entity)
  forms/                Flask-WTF forms
  routes/               Blueprints — one per module
  services/             Business logic: calculations, PDFs, email, audit logging
  utils/                Decorators, tenant helper, tokens, uploads, navigation
  templates/            Jinja2 templates (shell.html is the sidebar layout)
```

## Design principles in one paragraph

Data that can be *derived* is never stored: attendance percentages, exam results, fee balances and net salaries are computed from the underlying records every time, so they cannot drift out of sync. History is preserved: a student's class per session lives in an enrollment record, and attendance records snapshot the class they were taken in. Rules are enforced twice where it matters — friendly checks in the application *and* constraints in the database as the safety net. Details in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Security at a glance

Bcrypt password hashing, CSRF protection on every form, HttpOnly/SameSite session cookies, signed expiring email tokens, upload validation by file *content* (not just extension), strict per-school data scoping, role checks on the server for every protected route, and an audit trail of important actions.

Known gaps you should be aware of before exposing it publicly: **there is no login rate-limiting/lockout, school registration is open to anyone who can reach the site, and password-reset links are valid until they expire rather than single-use.** See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#security-measures-and-known-gaps).

## License

No license has been chosen yet, so all rights are reserved by default. Add a `LICENSE` file before sharing the code publicly.
