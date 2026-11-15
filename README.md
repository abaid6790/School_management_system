# 🏫 School Management System (SMS)

**A complete school operations platform — from student admissions to academic records, fees, payroll, and communication.**

School Management System (SMS) is a multi-tenant web application built with **Python, Flask, and PostgreSQL** to manage the day-to-day operations of multiple schools through one application.

It brings academic administration, student and staff records, attendance, examinations, fee collection, school finances, and communication into a unified system.

> **Data-driven by design:** Every number displayed is calculated from actual database records. There is no preloaded demo data — each newly registered school starts with a clean workspace.

<p align="center">
  <strong>Admissions</strong> • <strong>Academics</strong> • <strong>Attendance</strong> • <strong>Examinations</strong> • <strong>Fees</strong> • <strong>Payroll</strong> • <strong>Communication</strong>
</p>

---

## 🚧 Development Progress

<text-placeholder></text-placeholder>

**<span>8 of 12 phases completed</span>** — the core academic, financial, and communication workflows are implemented.

| Phase | Progress |
|---|---|
| Phase 0–8 | <badge>Complete</badge> |
| Phase 9–12 | <badge color="warning">In progress / Planned</badge> |

The following planned features are not yet implemented:

- Dashboard statistics and additional reporting
- Student promotion and transfer workflows
- Student and staff ID cards
- Data import and export
- In-app backup and restore
- Additional settings screens
- Parent and student portals

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the authoritative development status and known limitations.

---

## ✨ Features

### 🔐 Authentication & School Management
- School self-registration
- Email verification and password reset
- Login and logout
- Four staff roles with server-side permission enforcement
- Multi-tenant school data isolation
- Audit trail for important operations

### 🎓 Academic Administration
- Academic session management
- One active academic session at a time
- Class and section management
- Subject management
- School-wide period grid

### 👥 Student & Staff Records
- Student profiles with enrollment history
- Guardians shared across siblings
- Teacher management
- Non-teaching staff management
- Secure document uploads

### 📅 Attendance Management
- Daily student attendance
- Daily teacher attendance
- Attendance percentage calculations
- Low-attendance reports
- Leave requests synchronized with attendance after approval

### 🗓️ Timetable Management
- Weekly class and section timetables
- Teacher timetable views
- Daily timetable views
- Teacher, room, and class clash prevention

### 📝 Examination & Results
- Examination management
- Subject-wise examination papers
- Validated marks entry
- Configurable grade bands
- Pass/fail calculations and student rankings
- PDF report cards with remarks

### 💳 Student Fee Management
- Custom fee types
- Individual and bulk fee assignment
- Partial fee payments
- PDF payment receipts
- Discounts with recorded reasons
- Fee defaulter reports
- PDF student fee statements

### 💰 Finance & Payroll
- Expense categories and expense records
- Teacher and staff salary records
- PDF salary slips
- Teacher self-service salary history
- Cash-basis financial summaries

### 📢 School Communication
- Notices with draft, publish, archive, and expiry workflows
- Audience-based notices
- School calendar and holidays
- Homework assignments and teacher-recorded submissions
- Parent–teacher meeting scheduling
- Meeting slot booking
- In-app staff notifications
- Guardian emails with delivery logs and retry support
- Fee reminders

For complete role-level functionality, see [`docs/ROLES_AND_PERMISSIONS.md`](docs/ROLES_AND_PERMISSIONS.md) and [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md).

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python 3.10+ |
| Backend Framework | Flask 3 |
| ORM | SQLAlchemy 2.0 |
| Database | PostgreSQL 14+ |
| Database Migrations | Flask-Migrate / Alembic |
| Authentication | Flask-Login |
| Forms & CSRF | Flask-WTF |
| Password Hashing | Flask-Bcrypt |
| Email | Flask-Mail |
| PDF Generation | ReportLab |
| Templates | Jinja2 |
| UI Framework | Bootstrap 5 |
| Icons | Bootstrap Icons |
| Client-side Logic | Vanilla JavaScript |

<text>**Development environment:** Python 3.12 and PostgreSQL 16.</text>

Bootstrap and Bootstrap Icons are loaded from a CDN, so an internet connection is required for those browser assets.

---

## 🚀 Installation & Setup

### Prerequisites

Install the following before starting:

- Python 3.10 or newer
- PostgreSQL 14 or newer
- Git
- Gmail account with an App Password (if using Gmail for email delivery)

### 1. Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd SMS
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bat
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create your environment file:

```bat
copy .env.example .env
```

Open `.env` and configure the required values:

```env
SECRET_KEY=your-secret-key
DATABASE_URL=your-postgresql-database-url
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
```

Use the exact variable names and format specified in `.env.example`.

### 5. Create the PostgreSQL Database

Create the application database and configure its credentials.

Follow [`docs/INSTALLATION.md`](docs/INSTALLATION.md) for the complete PostgreSQL setup instructions.

### 6. Apply Database Migrations

For Windows Command Prompt:

```bat
set FLASK_APP=run.py
flask db upgrade
```

For PowerShell:

```powershell
$env:FLASK_APP = "run.py"
flask db upgrade
```

This applies the database migrations and creates the required tables.

### 7. Run the Application

```bash
python run.py
```

Open the registration page:

<http://127.0.0.1:5000/auth/register>

Register your school to create its initial workspace.

> **Important:** Always run `flask db upgrade` before using a fresh database. Skipping migrations can cause errors such as `relation "users" does not exist`. See [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) for solutions.

For complete installation instructions, including PostgreSQL and Gmail configuration, read [`docs/INSTALLATION.md`](docs/INSTALLATION.md).

---

## 🧪 Testing

The current project includes a smoke-test suite for Phase 8 modules and CSRF behavior.

Run the smoke tests:

```bash
python tests/smoke/run_all.py
```

Check POST forms for CSRF tokens:

```bash
python tools/check_csrf.py
```

**Current testing status:**
- Phase 8 smoke tests are maintained in `tests/smoke`.
- CSRF behavior is included in the smoke-test coverage.
- Earlier phases were verified using temporary scripts that were not retained.
- A comprehensive maintained `pytest` suite is planned.

See [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md#testing) for testing details.

---

## 🏗️ Project Structure

```text
SMS/
│
├── app/
│   ├── __init__.py          # Application factory and blueprint registration
│   ├── extensions.py        # Database, login, mail, CSRF, bcrypt, migrations
│   │
│   ├── models/              # SQLAlchemy models
│   ├── forms/               # Flask-WTF forms
│   ├── routes/              # Feature-specific blueprints
│   ├── services/            # Business logic, calculations, PDFs, email, audit
│   ├── utils/               # Decorators, tenant helpers, tokens, uploads
│   └── templates/           # Jinja2 templates and UI layouts
│
├── migrations/
│   └── versions/            # Alembic database migrations
│
├── tests/
│   └── smoke/               # Phase 8 and CSRF smoke tests
│
├── tools/
│   ├── generate_docs.py     # Regenerates generated documentation
│   └── check_csrf.py        # Checks POST forms for CSRF protection
│
├── docs/                    # Project documentation
│
├── config.py                # Environment-based configuration
├── run.py                   # Development server entry point
├── requirements.txt         # Pinned dependencies
├── .env.example             # Environment configuration template
└── README.md
```

---

## 🧠 Architecture & Design Principles

The system follows a data-driven architecture designed to keep records consistent and preserve historical information.

**1. Calculate derived data**

Attendance percentages, examination results, fee balances, and net salaries are calculated from underlying database records instead of being stored as independently editable totals.

**2. Preserve historical records**

Student class assignments are maintained through enrollment records, and attendance records retain the class information associated with the original attendance entry.

**3. Validate at multiple levels**

Important business rules are checked in the application, while database constraints provide an additional layer of protection.

**4. Maintain separation of responsibilities**

The application separates models, forms, routes, services, and utilities to keep business logic organized and maintainable.

**5. Enforce school-level isolation**

Each school's data is scoped to its own tenant, preventing unauthorized access to another school's records.

Read [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the detailed architecture and design decisions.

---

## 🔒 Security

Security mechanisms currently implemented include:

- Bcrypt password hashing
- CSRF protection on every form
- HttpOnly and SameSite session cookies
- Signed, expiring email tokens
- File upload validation based on file content
- Strict per-school data scoping
- Server-side role and permission enforcement
- Audit logging of important actions

### Known Security Limitations

The following gaps are important to understand before public deployment:

| Area | Current limitation |
|---|---|
| Login protection | No login rate-limiting or account lockout |
| School registration | Open to anyone who can access the application |
| Password reset | Reset links are not single-use and remain valid until expiration |

These protections are not implemented yet. Review [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md#security-measures-and-known-gaps) before exposing the application publicly.

---

## 📚 Documentation

Detailed documentation is available for installation, usage, development, and maintenance.

| Document | Description |
|---|---|
| [Installation](docs/INSTALLATION.md) | Prerequisites, PostgreSQL, environment variables, Gmail, first run, production notes, and backups |
| [User Guide](docs/USER_GUIDE.md) | First-time setup and day-to-day workflows |
| [Roles & Permissions](docs/ROLES_AND_PERMISSIONS.md) | Staff roles, access rules, and account ownership |
| [Architecture](docs/ARCHITECTURE.md) | Application structure, multi-tenancy, security, and design principles |
| [Database](docs/DATABASE.md) | Database conventions, migrations, backup, and restore |
| [Database Schema](docs/DATABASE_SCHEMA.md) | Generated tables, columns, and constraints |
| [Routes](docs/ROUTES.md) | Generated application routes and permitted roles |
| [Development](docs/DEVELOPMENT.md) | Coding conventions, module development, migrations, and testing |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Known errors and their solutions |
| [Roadmap](docs/ROADMAP.md) | Planned features and known limitations |
| [Changelog](CHANGELOG.md) | Phase-by-phase development history |

---

## 🗺️ Future Development

The remaining development work focuses on expanding the platform with:

- More comprehensive dashboards and statistics
- Student promotion and transfer management
- ID card generation
- Import and export functionality
- In-app backup and restore
- Additional school settings
- Parent and student portals
- Comprehensive automated testing

The complete and authoritative list is maintained in [`docs/ROADMAP.md`](docs/ROADMAP.md).

---

## 📄 License

**No license has been selected yet.**

Until a license is added, all rights are reserved by default. Add a `LICENSE` file before publicly distributing the source code or granting others permission to use, modify, or redistribute it.

---

<p align="center">
  <strong>School Management System</strong><br>
  Simplifying academic administration and everyday school operations.
</p>