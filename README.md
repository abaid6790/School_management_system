# 🎓 School Management System (SMS)

<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=700&size=27&duration=2800&pause=900&color=6366F1&center=true&vCenter=true&width=850&height=65&lines=One+School.+One+Connected+System.;Simplifying+School+Management.;Manage.+Monitor.+Organize.+Grow." alt="Animated School Management System heading">

### A Complete Digital Platform for Modern School Operations

A multi-tenant School Management System built with **Flask, PostgreSQL, SQLAlchemy, and Bootstrap 5**, designed to bring academic administration, student management, attendance, examinations, fee collection, and school finances into one centralized platform.

<br>

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3-000000?style=for-the-badge&logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)

<br>

<badge color="success">Core workflow operational</badge> <badge color="info">Phases 0–7 of 12 complete</badge>

**[Features](#-core-features) · [Architecture](#-architecture) · [Installation](#-getting-started) · [Documentation](#-documentation) · [Roadmap](#-development-roadmap)**

</div>

---

## 🏫 Overview

Managing a school involves much more than maintaining student records. Admissions, class assignments, attendance, examinations, fee collection, staff salaries, and daily expenses all require accurate records and coordinated workflows.

The **School Management System (SMS)** brings these operations together in a centralized, multi-tenant web application.

Each school registers its own account and operates within an isolated environment. School administrators can manage academic activities, staff can perform their assigned responsibilities, and financial records can be maintained without relying on disconnected spreadsheets or manual registers.

### What makes this system different?

- **Multi-tenant architecture:** Multiple schools can use the same application while keeping their data isolated.
- **Database-driven calculations:** Every displayed figure comes from actual database records.
- **No artificial demo data:** A newly registered school starts with an empty database workspace.
- **Role-based access:** Staff members receive permissions according to their responsibilities.
- **Historical records:** Student enrollment and attendance history are preserved.
- **Integrated financial workflows:** Fees, expenses, salaries, receipts, and financial summaries work together.

> **Development status:** Phases 0–7 of the planned 12 phases are complete. The core academic and financial workflows are operational. Several planned modules remain under development. There is currently no automated test suite. See the [Roadmap](docs/ROADMAP.md) for the exact implementation status.

## ✨ Core Features

The following modules represent functionality implemented in the current application.

### 📊 Feature Overview

| Module | Implemented capabilities |
|---|---|
| 🔐 Accounts & Authentication | School registration, email verification, login/logout, password reset |
| 👥 Role Management | Four staff roles, server-side permissions, school-level isolation |
| 🏫 Academic Management | Academic sessions, classes, sections, subjects, period configuration |
| 🎓 Student Management | Student profiles, enrollment history, guardian management |
| 👨‍🏫 Staff Management | Teacher records, non-teaching staff, teacher self-service salary history |
| 📅 Attendance | Student and teacher attendance, attendance percentages, low-attendance reports |
| 📝 Leave Management | Leave requests and automatic attendance synchronization upon approval |
| 🕒 Timetable | Weekly timetables, teacher and daily views, clash prevention |
| 📚 Examination | Exams, subject papers, marks entry, grading, rankings, report cards |
| 💳 Fee Management | Fee structures, individual and bulk assignments, partial payments, discounts |
| 🧾 Financial Records | Payment receipts, fee statements, defaulters reports |
| 💰 School Finance | Expenses, salary records, salary slips, cash-basis financial summaries |
| 📋 Audit Trail | Recording important administrative actions |
| 📄 Document Management | Secure document uploads and PDF generation |

### 🔐 Authentication & Access Control

- Independent school registration.
- Email verification.
- Secure login and logout.
- Password-reset workflow.
- Four staff roles with server-side authorization.
- School-specific data isolation.
- Audit logging for important activities.

### 🏫 Academic Administration

- Create and manage academic sessions.
- Maintain one active academic session at a time.
- Organize classes and sections.
- Manage subjects.
- Configure the school-wide period grid.
- Maintain student enrollment history.

### 👨‍🎓 Student & Staff Management

- Student profiles and enrollment records.
- Guardian records shared across siblings.
- Teacher management.
- Non-teaching staff management.
- Secure document uploads.
- Historical student enrollment information.

### 📅 Attendance & Leave Management

- Daily student attendance.
- Daily teacher attendance.
- Automatic attendance percentage calculations.
- Low-attendance reporting.
- Staff leave requests.
- Attendance synchronization when leave is approved.

### 🕒 Timetable Management

- Weekly class and section timetables.
- Teacher-specific timetable views.
- Daily timetable views.
- Prevention of teacher scheduling conflicts.
- Prevention of classroom and class timetable conflicts.

### 📝 Examination & Results

- Examination creation.
- Subject-wise examination papers.
- Validated marks entry.
- Configurable grading bands.
- Pass/fail calculations.
- Student rankings.
- PDF report cards.
- Teacher remarks on report cards.

### 💳 Student Fee Management

- Configurable fee types.
- Individual student fee assignment.
- Bulk fee assignment.
- Partial fee payments.
- Payment receipts in PDF format.
- Discounts with recorded reasons.
- Defaulters reports.
- Student fee statements in PDF format.

### 💰 School Financial Management

- Expense categories.
- Expense recording.
- Teacher and staff salary records.
- PDF salary slips.
- Teacher self-service salary history.
- Cash-basis financial summaries.

---

## 🧑‍💼 User Roles & Permissions

The application uses role-based access control to ensure that staff members can only perform authorized operations.

The current system includes four staff roles:

| Role | Primary responsibility |
|---|---|
| **Admin** | Overall school administration and management |
| **Manager** | Assigned academic and operational management |
| **Teacher** | Teaching-related operations and permitted self-service functions |
| **Accountant** | Fee collection and financial operations |

Permissions are enforced on the server rather than relying only on hiding interface elements.

For detailed permissions, ownership rules, and account creation workflows, see [Roles & Permissions](docs/ROLES_AND_PERMISSIONS.md).

---

## 🛠️ Technology Stack

The project uses a traditional server-rendered Flask architecture with PostgreSQL as its primary database.

| Layer | Technology | Purpose |
|---|---|---|
| Backend | Python 3.10+ | Application logic |
| Web Framework | Flask 3 | Routing and application foundation |
| ORM | SQLAlchemy 2.0 | Database operations and models |
| Database | PostgreSQL 14+ | Persistent relational data |
| Migrations | Flask-Migrate / Alembic | Database schema versioning |
| Authentication | Flask-Login | Session-based authentication |
| Forms & Security | Flask-WTF | Form handling and CSRF protection |
| Password Security | Flask-Bcrypt | Password hashing |
| Email | Flask-Mail | Verification and password-reset emails |
| Frontend | Jinja2 | Server-rendered HTML templates |
| UI Framework | Bootstrap 5 | Responsive interface |
| Icons | Bootstrap Icons | Interface iconography |
| JavaScript | Vanilla JavaScript | Client-side interactions |
| PDF Generation | ReportLab | Receipts, statements, report cards, salary slips |

### Architecture Choice

The system uses Flask and Jinja2 rather than a separate React frontend.

This provides:

- A simpler application architecture.
- Server-side rendering.
- Centralized business logic.
- Direct integration between forms and backend validation.
- Fewer frontend build dependencies.
- Straightforward deployment and maintenance.

Bootstrap 5 and Bootstrap Icons are loaded through a CDN, so an internet connection is required in the browser for those assets.

---

## 🏗️ Architecture

The application follows a modular Flask architecture with a clear separation between database models, forms, routes, services, utilities, and templates.

### Application Architecture

```text
                 SCHOOL MANAGEMENT SYSTEM
                            |
                            |
                 Flask Application Factory
                            |
              +-------------+-------------+
              |             |             |
           Routes         Forms        Extensions
              |             |             |
              +-------------+-------------+
                            |
                     Service Layer
                            |
              +-------------+-------------+
              |             |             |
          Calculations     PDFs       Audit Logging
              |             |             |
              +-------------+-------------+
                            |
                     SQLAlchemy ORM
                            |
                       PostgreSQL
```

### Multi-Tenant Data Isolation

Each school operates within its own data scope.

```text
                 SMS APPLICATION
                        |
          +-------------+-------------+
          |             |             |
       School A      School B      School C
          |             |             |
       Students      Students      Students
       Teachers      Teachers      Teachers
       Classes       Classes       Classes
       Fees          Fees          Fees
       Expenses      Expenses      Expenses
          |             |             |
          +-------------+-------------+
                        |
                    PostgreSQL
```

The application enforces school-specific data scoping so that one school's users cannot access another school's records through ordinary application workflows.

---

## 🗄️ Database & Data Integrity

The system is designed around relational data and database-backed calculations.

### Core Database Principles

**1. Calculate instead of storing derived values**

Information that can be calculated from existing records is not unnecessarily stored as an independent value.

Examples:

- Attendance percentages are calculated from attendance records.
- Examination results are calculated from entered marks.
- Fee balances are calculated from assigned fees and payments.
- Net salaries are calculated from the underlying salary records.

This reduces inconsistencies between related records.

**2. Preserve historical information**

Historical information is maintained through dedicated records.

For example:

- Student class assignments are stored in enrollment records for each academic session.
- Attendance records preserve the class information relevant when attendance was recorded.

**3. Validate at multiple levels**

Important business rules are checked in application logic and reinforced through database constraints where applicable.

**4. Use database migrations**

Flask-Migrate and Alembic manage schema changes, allowing database structures to evolve in a controlled way.

For additional details, see:

- [Database Documentation](docs/DATABASE.md)
- [Database Schema](docs/DATABASE_SCHEMA.md)
- [Architecture](docs/ARCHITECTURE.md)

---

## 🔐 Security

Security is incorporated into the application through multiple layers.

### Implemented Security Measures

| Security measure | Implementation |
|---|---|
| Password protection | Bcrypt password hashing |
| CSRF protection | Flask-WTF |
| Session security | HttpOnly and SameSite cookie settings |
| Email verification | Signed, expiring tokens |
| Password reset | Signed, expiring tokens |
| File uploads | Content-based file validation |
| Tenant isolation | Per-school data scoping |
| Authorization | Server-side role enforcement |
| Auditability | Important administrative actions recorded |

### Known Security Gaps

The application is still under development and should not be treated as production-hardened.

The following known gaps must be addressed before public deployment:

- No login rate-limiting or account lockout.
- School registration is open to anyone who can access the application.
- Password-reset links are not single-use and remain valid until expiration.

Other production-readiness concerns should also be reviewed, including deployment configuration, email security, backups, access policies, and operational monitoring.

See [Architecture — Security Measures and Known Gaps](docs/ARCHITECTURE.md#security-measures-and-known-gaps).

---

## 🚀 Getting Started

### Prerequisites

Before installing the project, make sure you have:

| Requirement | Version |
|---|---|
| Python | 3.10+ |
| PostgreSQL | 14+ |
| pip | Latest recommended |
| Git | Recommended |
| Web Browser | Modern browser |

The project was developed using Python 3.12 and tested with PostgreSQL 16.

### 1. Clone or download the repository

```powershell
git clone <YOUR_REPOSITORY_URL>
cd SMS
```

Alternatively, download the repository and extract it into your desired project directory.

### 2. Create a virtual environment

```powershell
python -m venv venv
```

### 3. Activate the environment

```powershell
venv\Scripts\activate
```

### 4. Install dependencies

```powershell
pip install -r requirements.txt
```

### 5. Configure environment variables

Create your environment file:

```powershell
copy .env.example .env
```

Open `.env` and configure the required values.

Example:

```env
SECRET_KEY=replace-with-a-secure-random-secret

DATABASE_URL=postgresql://username:password@localhost:5432/sms_db

MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
```

Use actual credentials for your environment. Do not commit `.env` or expose passwords and secret keys publicly.

### 6. Create the PostgreSQL database

Create a PostgreSQL database before running the application.

For example, using `psql`:

```sql
CREATE DATABASE sms_db;
```

Make sure your `DATABASE_URL` matches the database name and credentials.

### 7. Apply database migrations

Set the Flask application entry point:

```powershell
$env:FLASK_APP = "run.py"
```

Run migrations:

```powershell
flask db upgrade
```

<details>
<summary><strong>⚠️ Important: Why database migrations are necessary</strong></summary>

The migration command creates the database tables required by the application.

If you skip this step, the application may fail during authentication or other database operations with errors such as:

```text
relation "users" does not exist
```

Always apply the migrations before the first application run.

</details>

### 8. Start the application

```powershell
python run.py
```

### 9. Register your school

Open the following URL in your browser:

**http://127.0.0.1:5000/auth/register**

Register a school account and complete the email verification process.

A newly registered school starts with no demo records. You can configure its academic sessions, classes, sections, subjects, staff, students, and other records through the application.

> **Complete installation instructions:** [docs/INSTALLATION.md](docs/INSTALLATION.md)

---

## 📂 Project Structure

```text
SMS/
│
├── run.py
├── config.py
├── requirements.txt
├── .env.example
├── CHANGELOG.md
│
├── migrations/
│   └── versions/
│
├── tools/
│   └── generate_docs.py
│
├── docs/
│   ├── INSTALLATION.md
│   ├── USER_GUIDE.md
│   ├── ROLES_AND_PERMISSIONS.md
│   ├── ARCHITECTURE.md
│   ├── DATABASE.md
│   ├── DATABASE_SCHEMA.md
│   ├── ROUTES.md
│   ├── DEVELOPMENT.md
│   ├── TROUBLESHOOTING.md
│   └── ROADMAP.md
│
└── app/
    │
    ├── __init__.py
    ├── extensions.py
    │
    ├── models/
    │   └── SQLAlchemy models
    │
    ├── forms/
    │   └── Flask-WTF forms
    │
    ├── routes/
    │   └── Module-based blueprints
    │
    ├── services/
    │   └── Business logic, PDFs, email, audit
    │
    ├── utils/
    │   └── Decorators, tenant helpers, tokens,
    │       uploads, navigation
    │
    └── templates/
        └── Jinja2 templates
```

### Directory Responsibilities

| Directory / File | Responsibility |
|---|---|
| `run.py` | Development server entry point |
| `config.py` | Environment-based configuration |
| `app/__init__.py` | Application factory and blueprint registration |
| `app/extensions.py` | Database, login, mail, CSRF, bcrypt, and migration extensions |
| `app/models/` | Database models and relationships |
| `app/forms/` | Form definitions and validation |
| `app/routes/` | Application routes and module blueprints |
| `app/services/` | Business calculations, PDFs, email, and audit logging |
| `app/utils/` | Shared utilities and security helpers |
| `app/templates/` | Server-rendered Jinja2 interface |
| `migrations/` | Database migration history |
| `tools/` | Documentation generation utilities |
| `docs/` | Technical documentation and user guides |

---

## 📚 Documentation

The project includes dedicated documentation for installation, everyday usage, development, architecture, and troubleshooting.

| Documentation | Description |
|---|---|
| [Installation Guide](docs/INSTALLATION.md) | Python, PostgreSQL, environment configuration, Gmail setup, first run, and production notes |
| [User Guide](docs/USER_GUIDE.md) | Initial school setup and everyday workflows |
| [Roles & Permissions](docs/ROLES_AND_PERMISSIONS.md) | Role responsibilities, authorization, and account ownership |
| [Architecture](docs/ARCHITECTURE.md) | Application structure, multi-tenancy, security, and design principles |
| [Database Guide](docs/DATABASE.md) | Database conventions, migrations, backup, and restoration |
| [Database Schema](docs/DATABASE_SCHEMA.md) | Generated database tables, columns, and constraints |
| [Routes Reference](docs/ROUTES.md) | Generated route list and role permissions |
| [Development Guide](docs/DEVELOPMENT.md) | Coding conventions, modules, migrations, and testing notes |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Known errors and their solutions |
| [Roadmap](docs/ROADMAP.md) | Planned features, incomplete modules, and known limitations |
| [Changelog](CHANGELOG.md) | Development phases and delivered functionality |

---

## 🛣️ Development Roadmap

The project is being developed incrementally, with a planned total of 12 phases.

<details open>
<summary><strong>Completed development</strong></summary>

| Phase | Scope | Status |
|---:|---|---|
| 0–7 | Core application, academic management, attendance, timetable, examinations, fees, and school finance | ✅ Complete |

</details>

<details>
<summary><strong>Planned / incomplete functionality</strong></summary>

The following features are not yet implemented in the current application:

- Dashboard statistics and enhanced analytics.
- Homework management.
- School notices and announcements.
- School events management.
- Student promotion workflows.
- Student and staff ID card generation.
- Data import and export.
- Backup management.
- Additional settings screens.
- Parent portal.
- Student portal.

These features are planned, not completed. Their implementation status and dependencies should be checked in [docs/ROADMAP.md](docs/ROADMAP.md).

</details>

---

## 🧪 Testing & Verification

**Current testing status: No automated test suite is available yet.**

Implemented functionality has been verified through scripted smoke tests and manual workflow checks.

The project plans to convert these checks into an automated `pytest` test suite.

Areas that should be covered include:

- Authentication and registration.
- School-level tenant isolation.
- Role-based authorization.
- Student enrollment and historical records.
- Attendance calculations and leave synchronization.
- Timetable clash prevention.
- Examination grading and result calculations.
- Fee assignments, partial payments, and receipts.
- Salary and expense calculations.
- PDF generation.
- Database constraints and migration behavior.
- Security and invalid-input handling.

Until automated tests are implemented, the application should be considered functionally developed but not comprehensively regression-tested.

---

## ⚠️ Current Limitations

Transparency is important when evaluating the current development state.

| Area | Current limitation |
|---|---|
| Development | Phases 0–7 of 12 complete |
| Automated testing | No automated test suite |
| Dashboard | Enhanced statistics not implemented |
| Homework | Not implemented |
| Notices & events | Not implemented |
| Promotion | Not implemented |
| ID cards | Not implemented |
| Import/export | Not implemented |
| Backups | Planned functionality not implemented |
| Settings | Additional settings screens not implemented |
| Portals | Parent and student portals not implemented |
| Security | Login rate limiting and single-use password reset are missing |
| Production | Not yet production-hardened |

For the authoritative and updated list, see [ROADMAP.md](docs/ROADMAP.md).

---

## 🔒 Data & Privacy

The application is designed around school-owned records and local database storage.

- A new school starts with an empty workspace.
- Student, guardian, teacher, attendance, and financial information is stored in PostgreSQL.
- Application-generated PDFs are produced from database records.
- Important administrative actions are recorded through the audit trail.
- School-specific data access is enforced through tenant scoping.

The application requires email configuration for email-dependent authentication workflows. Bootstrap assets and icons are loaded from a CDN.

---

## 📜 License

**No license has been selected yet.**

Until a license is added, the source code is subject to the default copyright restrictions. Add an appropriate `LICENSE` file before distributing or publishing the repository under an open-source license.

---

<div align="center">

### 🎓 Better School Management Starts with Connected Systems.

**School Management System (SMS)**

*Academic Administration · Student Management · Attendance · Examinations · Fees · School Finance*

<br>

Built with **Python · Flask · PostgreSQL · Bootstrap 5**

<br>

<sub>Developed as an evolving multi-tenant school management platform.</sub>

</div>