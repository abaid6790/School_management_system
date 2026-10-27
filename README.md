# School Management System (SMS)

A multi-tenant web application built with **Python, Flask, and PostgreSQL** to manage a school's daily operations, including admissions, attendance, timetables, examinations, report cards, student fees, staff salaries, and financial records.

The system is designed around real database records, accurate calculations, and strict separation of school data. **No demo data is included**—every newly registered school starts with an empty database space of its own.

## Project Status

**Current Progress: Phases 0–7 of 12 completed**

The core academic and financial workflows are implemented and working end to end.

Several planned features are still under development, including dashboard statistics, homework, notices, events, student promotion, ID cards, data import/export, automated backups, additional settings screens, and parent/student portals.

An automated pytest suite has not yet been implemented. Existing functionality has been checked using scripted smoke tests.

See the [Project Roadmap](docs/ROADMAP.md) for the remaining work.

## Features

| Module | Key Features |
|---|---|
| **Accounts & Authentication** | School registration, email verification, login/logout, password reset, role-based access control, audit logging, and school-level data isolation |
| **Academic Management** | Academic sessions, active-session management, classes, sections, subjects, and school-wide period configuration |
| **Student Management** | Student records, enrollment history, guardian management across siblings, and secure document uploads |
| **Staff Management** | Teacher records, non-teaching staff records, and staff-related operations |
| **Attendance Management** | Daily student and teacher attendance, attendance percentages, low-attendance reports, and leave requests synchronized with attendance after approval |
| **Timetable Management** | Weekly class and section timetables, teacher and daily views, and teacher, classroom, and class conflict prevention |
| **Examination Management** | Exam creation, subject papers, validated marks entry, configurable grading bands, results, pass/fail status, rankings, and PDF report cards with remarks |
| **Student Fee Management** | Fee types, individual and bulk fee assignments, partial payments, PDF receipts, discounts with recorded reasons, defaulter reports, and PDF fee statements |
| **School Finance** | Expense categories, expense records, teacher and staff salary records, PDF salary slips, teacher self-service salary history, and cash-basis financial summaries |

For detailed permissions and workflows, see the [Roles and Permissions Guide](docs/ROLES_AND_PERMISSIONS.md) and [User Guide](docs/USER_GUIDE.md).

## Technology Stack

### Backend
- Python 3.10+ (developed with Python 3.12)
- Flask 3
- SQLAlchemy 2.0
- Flask-Migrate and Alembic
- Flask-Login
- Flask-WTF for CSRF protection
- Flask-Bcrypt for password hashing
- Flask-Mail for email delivery

### Database
- PostgreSQL 14+
- Tested with PostgreSQL 16

### Frontend
- HTML5
- CSS3
- JavaScript
- Jinja2 templates
- Bootstrap 5
- Bootstrap Icons

Bootstrap and Bootstrap Icons are loaded through a CDN, so an internet connection is required to load those assets in the browser.

### PDF Generation
- ReportLab

PDF generation uses a Python library and does not require additional system libraries on Windows.

## Installation and Setup

### Prerequisites

Before running the application, install:

- Python 3.10 or later
- PostgreSQL 14 or later
- Git (optional, for cloning the repository)

### 1. Navigate to the Project Directory

Open Command Prompt and run:

```bat
cd /d D:\SMS
```

Replace `D:\SMS` with your actual project directory if necessary.

### 2. Create a Virtual Environment

```bat
python -m venv venv
```

Activate it:

```bat
venv\Scripts\activate
```

### 3. Install Dependencies

```bat
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create your environment configuration file:

```bat
copy .env.example .env
```

Open `.env` and configure the required values, including:

- `SECRET_KEY`
- `DATABASE_URL`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`

Use the appropriate PostgreSQL connection string and a Gmail App Password if Gmail is your email provider.

**Important:** Keep `.env` private. Never commit actual passwords, API credentials, or production secrets to GitHub.

### 5. Create the PostgreSQL Database

Create the application database and configure the connection string in `.env`.

Follow the [Installation Guide](docs/INSTALLATION.md) for the complete PostgreSQL configuration and email setup instructions.

### 6. Apply Database Migrations

Set the Flask application entry point:

```bat
set FLASK_APP=run.py
```

Apply the database migrations:

```bat
flask db upgrade
```

This step creates the database tables required by the application.

**Do not skip this step.** Without the initial migrations, database operations may fail with errors such as:

```text
relation "users" does not exist
```

If this occurs, consult the [Troubleshooting Guide](docs/TROUBLESHOOTING.md).

### 7. Start the Application

```bat
python run.py
```

Open the following address in your browser:

**School Registration:** http://127.0.0.1:5000/auth/register

Register a school to begin using the application.

**PowerShell users:** Set the Flask application variable with:

```powershell
$env:FLASK_APP = "run.py"
```

For complete setup instructions, production considerations, and additional configuration, see [docs/INSTALLATION.md](docs/INSTALLATION.md).

## Documentation

The project includes documentation covering installation, architecture, database design, development, security, and planned features.

| Document | Description |
|---|---|
| [Installation Guide](docs/INSTALLATION.md) | Prerequisites, PostgreSQL setup, environment variables, Gmail App Password, first run, production notes, and backups |
| [User Guide](docs/USER_GUIDE.md) | Initial setup and step-by-step workflows for each module |
| [Roles and Permissions](docs/ROLES_AND_PERMISSIONS.md) | Staff roles, access permissions, ownership rules, and account creation |
| [Architecture](docs/ARCHITECTURE.md) | Application structure, multi-tenancy, security measures, and design principles |
| [Database Guide](docs/DATABASE.md) | Database conventions, migrations, and backup/restore procedures |
| [Database Schema](docs/DATABASE_SCHEMA.md) | Tables, columns, relationships, and constraints; generated documentation |
| [Routes Reference](docs/ROUTES.md) | Application URLs and permitted roles; generated documentation |
| [Development Guide](docs/DEVELOPMENT.md) | Coding conventions, module development, migration workflow, testing notes, and known issues |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common errors and their solutions |
| [Project Roadmap](docs/ROADMAP.md) | Planned features, incomplete modules, and known limitations |
| [Changelog](CHANGELOG.md) | Changes and features delivered in each development phase |

## Project Structure

```text
SMS/
├── run.py                  # Development server entry point
├── config.py               # Environment-based configuration
├── requirements.txt        # Python dependencies
├── .env.example            # Environment configuration template
├── migrations/
│   └── versions/           # Alembic database migrations
├── tools/
│   └── generate_docs.py    # Documentation generation utility
├── docs/                   # Project documentation
└── app/
    ├── __init__.py         # Application factory and blueprint registration
    ├── extensions.py       # Database, authentication, mail, CSRF, bcrypt, migrations
    ├── models/             # SQLAlchemy database models
    ├── forms/              # Flask-WTF forms
    ├── routes/             # Feature-specific Flask blueprints
    ├── services/           # Business logic, calculations, PDFs, email, audit logging
    ├── utils/              # Decorators, tenant helpers, tokens, uploads, navigation
    └── templates/          # Jinja2 templates and application layouts
```

## Design Principles

### 1. Database-Driven Calculations

Values that can be derived from existing records are calculated rather than independently stored. Attendance percentages, examination results, fee balances, and net salaries are computed from their underlying data to reduce inconsistencies.

### 2. Historical Data Preservation

Student enrollment records preserve class assignments across academic sessions. Attendance records also retain the relevant class information from the time attendance was recorded.

### 3. Multi-Tenant Data Isolation

Each school operates within its own data scope. Application-level tenant filtering and server-side permission checks help prevent unauthorized access to another school's records.

### 4. Application and Database Validation

Important business rules are checked in the application and reinforced with database constraints where appropriate.

### 5. Modular Architecture

The application separates database models, forms, routes, business logic, utilities, and templates to make the codebase easier to maintain and extend.

For more details, see the [Architecture Documentation](docs/ARCHITECTURE.md).

## Security

The application includes several security measures:

- **Password security:** Bcrypt password hashing.
- **CSRF protection:** Flask-WTF protection for forms.
- **Session security:** HttpOnly and SameSite session-cookie settings.
- **Email verification:** Signed, expiring email tokens.
- **Upload validation:** File-content validation rather than relying only on file extensions.
- **Access control:** Server-side role checks for protected routes.
- **Tenant isolation:** School-specific data scoping.
- **Audit logging:** Records of important application actions.

### Known Security Limitations

The current implementation has limitations that should be addressed before public production deployment:

- Login rate limiting and account lockout are not implemented.
- School registration is open to anyone who can access the application.
- Password-reset links are not single-use and remain valid until expiration.

These limitations are documented in the [Architecture Guide: Security Measures and Known Gaps](docs/ARCHITECTURE.md#security-measures-and-known-gaps).

**Security note:** The listed measures do not constitute a complete security audit. Review authentication, authorization, configuration, database access, uploads, and deployment settings before exposing the application to the public internet.

## Development Roadmap

The application is being developed in 12 phases, with Phases 0–7 completed.

Planned improvements include:

- Dashboard statistics and analytics
- Homework management
- Notices and school events
- Student promotion workflows
- Student and staff ID cards
- Data import and export
- Automated database backups
- Additional configuration screens
- Parent and student portals
- Automated pytest coverage

For the authoritative list of pending features, see [docs/ROADMAP.md](docs/ROADMAP.md).

## License

**No license has been selected yet.**

Until a license is added, the project remains subject to the default copyright rules. If you plan to distribute the code or invite external contributions, add an appropriate `LICENSE` file and confirm the terms under which the project may be used.