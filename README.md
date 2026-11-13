# 🏫 School Management System (SMS)

**A multi-tenant platform for managing the complete day-to-day operations of a school.**

Built with **Python, Flask, and PostgreSQL**, the School Management System brings academic administration, student records, attendance, examinations, fees, payroll, and communication together in one application.

Every figure displayed is calculated from actual database records. **No demo data is included** — every newly registered school starts with a clean, empty workspace.

<p align="center">
  <strong>Academic Management</strong> • <strong>Student Information</strong> • <strong>Attendance</strong> • <strong>Examinations</strong> • <strong>Finance</strong> • <strong>Communication</strong>
</p>

---

## 🚧 Development Status

**Phases 0–8 of 12 completed**

The core academic, financial, and communication workflows are implemented. Development is ongoing, and some planned modules have not been built yet.

| Phase | Scope | Status |
|---|---|---|
| 0 | Project foundation and configuration | ✅ Complete |
| 1 | Authentication, roles, permissions, and school setup | ✅ Complete |
| 2 | Academic structure and student records | ✅ Complete |
| 3 | Attendance and leave management | ✅ Complete |
| 4 | Timetables and scheduling | ✅ Complete |
| 5 | Examinations and report cards | ✅ Complete |
| 6 | Student fees and payment management | ✅ Complete |
| 7 | School finance and payroll | ✅ Complete |
| 8 | Notices, calendar, homework, and communication | ✅ Complete |
| 9 | Dashboard statistics, promotion, and transfers | ⏳ Planned |
| 10 | ID cards and import/export | ⏳ Planned |
| 11 | Backups, settings screens, and parent/student portals | ⏳ Planned |

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the complete development plan and known limitations.

---

## ✨ Features

### 🔐 Accounts & Access Control
- School self-registration and email verification
- Secure login, logout, and password reset
- Four staff roles with server-side permission enforcement
- Multi-tenant architecture with strict per-school data isolation
- Audit trail for important operations

### 🎓 Academic Management
- Academic sessions with one active session at a time
- Class, section, and subject management
- School-wide period and timetable configuration
- Student enrollment history across academic sessions

### 👥 Student & Staff Management
- Student profiles and enrollment records
- Guardians shared across siblings
- Teacher and non-teaching staff records
- Secure document uploads

### 📅 Attendance Management
- Daily student and teacher attendance
- Attendance percentage calculations
- Low-attendance reports
- Leave requests with automatic attendance synchronization after approval

### 🗓️ Timetable Management
- Weekly timetable for each class and section
- Teacher and daily timetable views
- Conflict prevention for teachers, rooms, and classes

### 📝 Examinations & Report Cards
- Examination and subject-paper management
- Validated marks entry
- Configurable grading bands
- Pass/fail results and student rankings
- PDF report cards with remarks

### 💳 Student Fee Management
- Configurable fee types
- Individual and bulk fee assignment
- Partial payments and payment receipts
- Discounts with recorded reasons
- Fee defaulters reports
- PDF fee statements

### 💰 School Finance & Payroll
- Expense categories and expense records
- Teacher and staff salary records
- PDF salary slips
- Teacher self-service salary history
- Cash-basis financial summaries

### 📢 Communication & School Activities
- Notices with draft, publish, archive, and expiry workflows
- Audience-based notice visibility
- School calendar and holiday management
- Homework assignments and teacher-recorded submissions
- Parent–teacher meeting scheduling and slot booking
- In-app staff notifications
- Guardian emails with delivery logs and retry support
- Fee reminders

For detailed role permissions and workflows, see the [Roles & Permissions](docs/ROLES_AND_PERMISSIONS.md) and [User Guide](docs/USER_GUIDE.md).

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| Backend | Python 3.10+, Flask 3 |
| ORM | SQLAlchemy 2.0 |
| Database | PostgreSQL 14+ |
| Migrations | Flask-Migrate / Alembic |
| Authentication | Flask-Login |
| Forms & CSRF | Flask-WTF |
| Password Security | Flask-Bcrypt |
| Email | Flask-Mail |
| PDF Generation | ReportLab |
| Frontend | Jinja2, Bootstrap 5, Bootstrap Icons |
| Client-side Logic | Vanilla JavaScript |
| Testing | Smoke-test suite |

**Development environment:** Python 3.12 and PostgreSQL 16.

The frontend uses Bootstrap and Bootstrap Icons through a CDN, so an internet connection is required for those browser assets to load.

---

## 🚀 Getting Started

### Prerequisites

Before installing, make sure you have:

- Python 3.10 or newer
- PostgreSQL 14 or newer
- Git
- A Gmail account with an App Password, if you want to use Gmail for email delivery

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

Copy the example environment file:

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

Use the actual variable names and configuration format provided in `.env.example`.

### 5. Create the PostgreSQL Database

Create the application database using the instructions in [`docs/INSTALLATION.md`](docs/INSTALLATION.md).

Make sure PostgreSQL is running and the database connection details in `.env` are correct.

### 6. Apply Database Migrations

```bat
set FLASK_APP=run.py
flask db upgrade
```

This creates the database tables and applies all available migrations.

### 7. Start the Application

```bash
python run.py
```

Open the registration page:

**http://127.0.0.1:5000/auth/register**

Register your school to begin using the application.

> **PowerShell users:** Set the Flask application variable with `$env:FLASK_APP = "run.py"` instead of `set FLASK_APP=run.py`.

> **Important:** Run `flask db upgrade` before starting the application for the first time. Skipping migrations can cause database errors such as `relation "users" does not exist`. See the [Troubleshooting Guide](docs/TROUBLESHOOTING.md) if you encounter this issue.

---

## 🧪 Testing

The project currently includes a smoke-test suite covering Phase 8 modules and CSRF behavior.

Run the complete smoke-test suite:

```bash
python tests/smoke/run_all.py
```

Check that POST forms include CSRF protection:

```bash
python tools/check_csrf.py
```

**Testing status:** Earlier development phases were verified using temporary scripts that were not retained. A comprehensive, maintained `pytest` test suite is still on the roadmap.

---

## 🏗️ Project Structure

```text
SMS/
│
├── app/
│   ├── __init__.py          # Application factory and blueprint registration
│   ├── extensions.py        # Database, login, mail, CSRF, bcrypt, migrations
│   │
│   ├── models/              # SQLAlchemy database models
│   ├── forms/               # Flask-WTF forms
│   ├── routes/              # Feature-specific application blueprints
│   ├── services/            # Business logic, calculations, PDFs, email, audit
│   ├── utils/               # Decorators, tenant helpers, tokens, uploads
│   └── templates/           # Jinja2 templates and application layouts
│
├── migrations/
│   └── versions/            # Alembic database migrations
│
├── tests/
│   └── smoke/               # Smoke tests for Phase 8 and CSRF
│
├── tools/
│   ├── generate_docs.py     # Generates documentation from application code
│   └── check_csrf.py        # Checks POST forms for CSRF protection
│
├── docs/                    # Project documentation
│
├── config.py                # Environment-based configuration
├── run.py                   # Development server entry point
├── requirements.txt         # Project dependencies
├── .env.example             # Environment configuration template
└── README.md
```

---

## 🧠 Engineering Principles

The system follows a few important design principles:

- **Calculate instead of duplicate:** Attendance percentages, exam results, fee balances, and net salaries are calculated from their underlying records rather than stored as independently editable totals.
- **Preserve historical records:** Student class assignments are maintained through enrollment records, while attendance records retain the class information relevant when attendance was taken.
- **Enforce important rules twice:** Application-level validation provides helpful feedback, while database constraints act as an additional layer of protection.
- **Separate responsibilities:** Models, forms, routes, services, and utilities each have their own responsibilities.
- **Isolate school data:** Every school's records are scoped to that school to prevent cross-tenant access.

Read [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full technical design.

---

## 🔒 Security

Security measures currently implemented include:

- Bcrypt password hashing
- CSRF protection on forms
- HttpOnly and SameSite session cookies
- Signed, expiring email tokens
- File upload validation based on file content
- Per-school data isolation
- Server-side role and permission checks
- Audit logging for important actions

### Known Security Gaps

The following limitations must be addressed before exposing the application publicly:

- No login rate-limiting or account lockout.
- School registration is open to anyone who can access the site.
- Password-reset links are not single-use; they remain valid until expiration.

These are known gaps, not implemented protections. Review [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md#security-measures-and-known-gaps) before deployment.

---

## 📚 Documentation

The project includes detailed documentation for installation, daily workflows, development, and maintenance.

| Document | Description |
|---|---|
| [Installation](docs/INSTALLATION.md) | Setup, PostgreSQL, environment variables, Gmail, and production notes |
| [User Guide](docs/USER_GUIDE.md) | First-time setup and day-to-day workflows |
| [Roles & Permissions](docs/ROLES_AND_PERMISSIONS.md) | Staff roles, access rules, and ownership |
| [Architecture](docs/ARCHITECTURE.md) | Application structure, multi-tenancy, and security |
| [Database](docs/DATABASE.md) | Database conventions, migrations, and backup/restore |
| [Database Schema](docs/DATABASE_SCHEMA.md) | Generated table, column, and constraint documentation |
| [Routes](docs/ROUTES.md) | Generated application routes and permitted roles |
| [Development](docs/DEVELOPMENT.md) | Coding conventions, module development, migrations, and testing |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common errors and their solutions |
| [Roadmap](docs/ROADMAP.md) | Planned features and known limitations |
| [Changelog](CHANGELOG.md) | Development history and phase-by-phase changes |

---

## 🗺️ Roadmap

The next development stages focus on completing the remaining planned modules:

- Dashboard statistics and reporting improvements
- Student promotion and transfer workflows
- Student and staff ID card generation
- Data import and export
- In-application backup and restore
- Additional settings screens
- Parent and student portals
- Expanded automated testing

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the authoritative feature list.

---

## 📄 License

**No license has been selected yet.**

Until a license is added, the project is protected by default copyright law. Add a `LICENSE` file before granting others permission to use, modify, or distribute the code.

---

<p align="center">
  <strong>School Management System</strong><br>
  One platform for academic administration, school operations, and financial management.
</p>