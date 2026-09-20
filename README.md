# 🏫 School Management System

A modular **School Management System** built with **Python, Flask, PostgreSQL, SQLAlchemy, and Bootstrap** for managing core school operations from a centralized web application.

The system is designed around separate modules for academics, students, staff, attendance, timetables, examinations, fees, and administrative auditing. It also includes authentication, email verification, password recovery, role-based navigation, multi-school data isolation, document uploads, and PDF generation.

---

## ✨ Overview

The School Management System provides a centralized platform for school administrators and authorized staff to manage day-to-day academic and administrative records.

### Current application areas

- 👨‍🎓 Student management
- 📝 Admissions
- 👪 Parent/guardian management
- 👨‍🏫 Teacher management
- 👨‍💼 Staff management
- 🏫 Classes, sections, subjects, periods, and academic sessions
- 📅 Student and teacher attendance
- 🕒 Timetables
- 📝 Examinations and marks
- 📊 Results, grading, rankings, and report cards
- 💰 Fee types, student fees, discounts, payments, receipts, and defaulters
- 🏖️ Leave requests
- 📎 Student documents
- 🔐 Authentication and account security
- 🧾 Audit logging
- 📄 PDF report generation

---

## 🚀 Features

### 🔐 Authentication & Account Management

- School registration
- Admin account creation
- Login/logout
- Email verification
- Resend verification email
- Forgot-password workflow
- Password reset
- Password hashing with Flask-Bcrypt
- Remember-me login support
- Active/inactive account handling
- Role-based access control
- Safe redirect handling
- Session security configuration

---

### 📊 Dashboard

- Centralized admin/staff dashboard
- Logged-in user information
- Current user role
- School information
- Role-filtered sidebar navigation
- Foundation for future dashboard statistics

> The current dashboard provides the application shell and navigation. Detailed live statistics such as total students, attendance summaries, and financial KPIs can be added as the dashboard module evolves.

---

# 🎓 Academics

## 👨‍🎓 Students

The student module supports:

- Student admission
- Student profiles
- Student search
- Filtering by class
- Filtering by status
- Student status management
- Admission numbers
- Class and section assignment
- Roll numbers
- Student enrollment records
- Guardian linking
- Guardian unlinking
- Student document uploads
- Student document downloads
- Student document deletion
- Student results
- Student fee records
- Fee statements
- Fee payment
- Fee discounts
- Fee receipts

Student listing also supports pagination for larger datasets.

---

## 📝 Admissions

- New student admission
- Admission number management
- Student academic placement
- Guardian information
- Initial enrollment information

---

## 👪 Parents / Guardians

- Guardian records
- Add guardian
- Edit guardian
- View guardian profile
- Guardian/student relationships
- Link guardians to students

Supported guardian relationships include:

- Father
- Mother
- Guardian
- Other

---

## 👨‍🏫 Teachers

- Teacher records
- Teacher profiles
- Add teacher
- Edit teacher
- View teacher
- Teacher status management
- Teacher attendance
- Teacher timetable

---

## 👨‍💼 Staff

- Staff records
- Staff profiles
- Add staff
- Edit staff
- View staff
- Employment status management

Supported employment states include:

- Active
- On Leave
- Resigned
- Terminated

---

## 🏫 Classes & Sections

- Academic class management
- Section management
- Class/section organization
- Section-specific student enrollment
- Roll number management

---

## 📚 Subjects

- Subject management
- Add subjects
- Edit subjects
- Subject types

Supported subject types include:

- Core
- Elective
- Practical
- Theory

---

## 📅 Academic Sessions

- Create academic sessions
- View academic sessions
- Activate an academic session
- Associate students, exams, and academic records with sessions

---

## ⏰ Academic Periods

- Period management
- Period creation
- Period editing
- Timetable-ready academic periods

---

# 🕒 Attendance & Schedule

## Student Attendance

- Mark student attendance
- Daily attendance
- Attendance history/reporting
- Attendance status tracking
- Low-attendance report

Supported attendance statuses:

- Present
- Absent
- Late
- Excused
- Leave

---

## 👨‍🏫 Teacher Attendance

Separate teacher attendance functionality includes:

- Mark teacher attendance
- Daily teacher attendance report
- Teacher attendance history

---

## 🗓️ Timetable

- Timetable entries
- Create timetable entries
- Edit timetable entries
- Delete timetable entries
- Teacher timetable view
- Daily timetable view

---

## 🏖️ Leave Management

- Create leave requests
- View leave requests
- Leave details
- Approve leave
- Reject leave
- Cancel leave

Supported leave types:

- Sick
- Casual
- Annual
- Emergency
- Other

Supported leave statuses:

- Pending
- Approved
- Rejected
- Cancelled

---

# 📝 Examinations

## Exams

- Create exams
- Edit exams
- View exams
- Change exam status
- Associate exams with academic sessions and classes
- Add subjects to exams
- Configure maximum marks
- Configure passing marks
- Enter student marks

Supported exam types include:

- Midterm
- Final
- Monthly Test
- Quiz
- Assignment
- Practical
- Custom

Supported exam statuses:

- Scheduled
- Completed
- Cancelled

---

## 📊 Results & Grading

- Exam result generation
- Student result details
- Class ranking
- Percentage calculation
- Grade calculation
- Pass/fail evaluation
- Incomplete-result indication
- Grade band management
- Teacher remarks
- Principal remarks

The result system is designed to distinguish between complete and incomplete marking before treating a ranking/result as final.

---

## 📄 Report Cards

The system can generate report cards containing information such as:

- School information
- Student information
- Admission number
- Class
- Section
- Roll number
- Examination information
- Subject marks
- Maximum marks
- Passing marks
- Obtained marks
- Percentage
- Grade
- Overall result
- Class position
- Attendance percentage
- Teacher remarks
- Principal remarks
- Signature placeholders

Report cards are generated as PDFs using **ReportLab**.

---

# 💰 Finance & Fees

## Fee Types

- Create fee types
- Edit fee types
- Enable/disable fee types
- Organize school fee categories

---

## Student Fees

- Assign fees to students
- Bulk fee assignment
- Assign fees to a class
- Assign fees to a section
- View individual student fees
- Track due dates
- Track outstanding balances

---

## 💸 Discounts

Supported discount types include:

- Fixed amount
- Percentage
- Scholarship
- Need-based
- Custom

---

## 💵 Payments

Supported payment methods include:

- Cash
- Bank Transfer
- Card
- Cheque
- Mobile Wallet
- Other

The system supports:

- Partial payments
- Payment history
- Receipt numbers
- Payment dates
- Payment notes
- Remaining balance calculation

---

## 🧾 Fee Receipts & Statements

PDF generation is available for:

- Individual fee payment receipts
- Student fee statements

Fee calculations include:

- Original fee amount
- Discounts
- Net payable
- Total paid
- Remaining balance
- Computed fee status

Supported computed fee states include:

- Paid
- Partially Paid
- Unpaid
- Overdue

---

## ⚠️ Fee Defaulters

The finance module includes a defaulters view for identifying students with outstanding fee balances.

---

# 📎 Student Documents

The student module supports document management for records such as:

- Admission form
- Birth certificate
- Previous school certificate
- CNIC/B-Form
- Transfer certificate
- Other documents

Supported file formats:

```text
PDF
JPG
JPEG
PNG
```

The application also applies an upload size limit and stores uploads separately from the application source.

---

# 🧾 Audit Logging

The system includes an audit logging mechanism for tracking important actions performed within the application.

Examples include:

- School registration
- User registration
- Email verification
- Login/logout
- Password reset
- Administrative changes

The audit log is accessible to authorized administrative roles.

---

# 👥 User Roles

The application defines the following roles:

| Role | Description |
|---|---|
| Super Admin | Platform-level administration |
| Admin | School-level administration |
| Teacher | Teaching and academic operations |
| Accountant | Financial operations |
| Receptionist | Admissions and administrative operations |
| Parent | Reserved for future expansion |
| Student | Reserved for future expansion |

Navigation is filtered according to the authenticated user's role.

---

# 🏢 Multi-School Architecture

The application is designed with **school-level data isolation** in mind.

Core records include a `school_id` relationship where appropriate, allowing the system to support multiple schools within the same application architecture.

The registration flow creates:

1. A school
2. School settings
3. An initial administrator
4. Related audit records

This provides a foundation for a multi-tenant school management platform.

---

# 🛠️ Technology Stack

## Backend

- **Python**
- **Flask 3.0.3**
- **Flask-SQLAlchemy**
- **Flask-Migrate**
- **Flask-Login**
- **Flask-Bcrypt**
- **Flask-Mail**
- **Flask-WTF**
- **WTForms**

## Database

- **PostgreSQL**
- **psycopg2-binary**
- **SQLAlchemy ORM**
- **Alembic / Flask-Migrate**

The current development setup uses a **local PostgreSQL database on the laptop**.

## Frontend

- HTML5
- CSS3
- JavaScript
- Bootstrap 5
- Bootstrap Icons
- Jinja2 templates

## PDF & Documents

- **ReportLab**
- **Pillow**

## Configuration

- **python-dotenv**
- Environment-based configuration

---

# 🏗️ Application Architecture

The project uses the **Flask Application Factory pattern** with modular blueprints, models, forms, services, utilities, and templates.

```text
school-management-system/
│
├── app/
│   ├── models/
│   │   ├── academic.py
│   │   ├── student.py
│   │   ├── teacher_profile.py
│   │   ├── staff.py
│   │   ├── guardian.py
│   │   ├── enrollment.py
│   │   ├── student_attendance.py
│   │   ├── teacher_attendance.py
│   │   ├── leave_request.py
│   │   ├── timetable.py
│   │   ├── exam.py
│   │   ├── exam_subject.py
│   │   ├── mark.py
│   │   ├── grade_band.py
│   │   ├── fee_type.py
│   │   ├── student_fee.py
│   │   ├── fee_discount.py
│   │   ├── fee_payment.py
│   │   ├── audit.py
│   │   └── ...
│   │
│   ├── routes/
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── students.py
│   │   ├── guardians.py
│   │   ├── teachers.py
│   │   ├── staff.py
│   │   ├── academic.py
│   │   ├── attendance.py
│   │   ├── teacher_attendance.py
│   │   ├── leave.py
│   │   ├── timetable.py
│   │   ├── exams.py
│   │   ├── fees.py
│   │   └── audit.py
│   │
│   ├── services/
│   │   ├── student_service.py
│   │   ├── attendance_service.py
│   │   ├── timetable_service.py
│   │   ├── result_service.py
│   │   ├── grading_service.py
│   │   ├── fee_service.py
│   │   ├── receipt_service.py
│   │   ├── report_card_service.py
│   │   ├── email_service.py
│   │   └── audit_service.py
│   │
│   ├── forms/
│   ├── utils/
│   ├── templates/
│   ├── static/
│   ├── extensions.py
│   └── __init__.py
│
├── migrations/
├── config.py
├── run.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

# 🧠 Architecture Flow

```text
Browser
   │
   ▼
Flask Routes / Blueprints
   │
   ├──────────────┐
   ▼              ▼
Forms          Services
   │              │
   └──────┬───────┘
          ▼
     SQLAlchemy ORM
          │
          ▼
      PostgreSQL
```

PDF-producing modules use ReportLab independently from the HTML rendering layer:

```text
Application
    │
    ├── Fee Statement ──────► ReportLab ──────► PDF
    │
    ├── Fee Receipt ────────► ReportLab ──────► PDF
    │
    └── Report Card ────────► ReportLab ──────► PDF
```

---

# 🗄️ Database

The project uses PostgreSQL as its relational database.

Example local configuration:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/school_management_db
```

Create the database before starting the application:

```sql
CREATE DATABASE school_management_db;
```

Database schema changes are managed using **Flask-Migrate / Alembic**.

Current migration history includes the initial schema followed by examination and fee-management phases.

---

# ⚙️ Installation & Setup

## 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/school-management-system.git
cd school-management-system
```

---

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Create PostgreSQL Database

Using PostgreSQL / pgAdmin:

```sql
CREATE DATABASE school_management_db;
```

---

## 5. Configure Environment Variables

Copy:

```text
.env.example
```

to:

```text
.env
```

Then configure:

```env
SECRET_KEY=your-secret-key

FLASK_ENV=development

DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/school_management_db

MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

APP_NAME=School Management System
```

### Email configuration

Email is used for:

- Account verification
- Verification email resend
- Password reset

For Gmail SMTP, use a **Gmail App Password** rather than your normal Gmail password.

---

# 🗃️ Database Migrations

After configuring the database, apply migrations:

```bash
flask --app run.py db upgrade
```

If your Flask environment is configured differently, the equivalent Flask-Migrate commands can be used.

For development, new schema changes can be generated with:

```bash
flask --app run.py db migrate -m "Describe the change"
```

Then apply them:

```bash
flask --app run.py db upgrade
```

---

# ▶️ Running the Application

Start the application with:

```bash
python run.py
```

The Flask server is configured to run on:

```text
http://127.0.0.1:5000
```

The application also exposes a health-check endpoint:

```text
/health
```

---

# 🔒 Security

Security-related implementation includes:

- Password hashing with Flask-Bcrypt
- CSRF protection with Flask-WTF
- Login protection with Flask-Login
- Email verification
- Expiring verification tokens
- Expiring password-reset tokens
- HTTP-only session cookies
- SameSite cookie configuration
- Optional secure cookies for production
- Environment-based secrets
- Safe redirect validation
- Upload file type restrictions
- Upload size limits
- Role-based navigation/access controls
- Audit logging
- School-level data scoping

> Production deployments should additionally use HTTPS, secure production secrets, a production WSGI server, appropriate PostgreSQL credentials, and hardened infrastructure configuration.

---

# 🧭 Current Sidebar Modules

The application interface is organized into the following areas:

```text
Dashboard

ACADEMICS
├── Students
├── Admissions
├── Parents
├── Teachers
├── Staff
├── Classes
├── Sections
└── Subjects

ATTENDANCE & SCHEDULE
├── Attendance
├── Timetable
└── Leave

EXAMINATIONS
├── Exams
└── Results

FINANCE
├── Fees
├── Expenses
└── Salaries

COMMUNICATION
├── Homework
├── Notices
└── Events

SYSTEM
├── Reports
├── Audit Log
├── Academic Sessions
└── Settings
```

Some sidebar items are intentionally marked **"soon"** in the current application because their corresponding full module is planned for a later development phase.

---

# 📌 Development Status

### Implemented modules

- [x] Authentication
- [x] School registration
- [x] Email verification
- [x] Password reset
- [x] Role-based navigation
- [x] Dashboard shell
- [x] Students
- [x] Admissions
- [x] Parents / Guardians
- [x] Teachers
- [x] Staff
- [x] Classes
- [x] Sections
- [x] Subjects
- [x] Academic sessions
- [x] Academic periods
- [x] Student attendance
- [x] Teacher attendance
- [x] Leave management
- [x] Timetable
- [x] Exams
- [x] Exam subjects
- [x] Marks entry
- [x] Grade bands
- [x] Results
- [x] Class ranking
- [x] Report cards
- [x] Report-card PDF generation
- [x] Fee types
- [x] Student fees
- [x] Fee discounts
- [x] Fee payments
- [x] Fee receipts
- [x] Fee statements
- [x] Fee defaulters
- [x] Student document management
- [x] Audit logs
- [x] PostgreSQL migrations

### Planned / future modules

- [ ] Advanced dashboard analytics
- [ ] Expenses
- [ ] Salaries / payroll
- [ ] Homework
- [ ] Notices
- [ ] Events
- [ ] Advanced reports
- [ ] Settings interface
- [ ] Parent portal
- [ ] Student portal
- [ ] Expanded permission management

---

# 📈 Future Enhancements

Potential future improvements include:

- 📊 Real-time dashboard statistics
- 📱 More responsive/mobile-focused UI
- 👪 Parent portal
- 👨‍🎓 Student portal
- 👨‍🏫 Teacher portal
- 💬 Notifications
- 📧 Automated school notifications
- 📱 SMS integration
- 📊 Advanced analytics
- 📑 Advanced reporting
- 📥 CSV/Excel import and export
- 🖨️ More printable documents
- 💳 Online fee payment integration
- ☁️ Production/cloud deployment
- 🔐 More granular permission management
- 📅 Automated timetable generation

---

# 🖥️ Interface

The application uses a sidebar-based administrative interface with navigation grouped into:

- Academics
- Attendance & Schedule
- Examinations
- Finance
- Communication
- System

The sidebar is dynamically filtered based on the authenticated user's role.

---

# 🤝 Contributing

Contributions and improvements are welcome.

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature/your-feature
```

3. Make your changes
4. Commit your changes

```bash
git commit -m "Add your feature"
```

5. Push your branch

```bash
git push origin feature/your-feature
```

6. Open a Pull Request

---

# 📄 License

This project is currently intended for development and educational purposes.

If you publish the project publicly, add the license that matches how you want others to use and modify the code.

---

# 👨‍💻 Developer

**Abaid-ur-Rehman**

Python / Flask Developer · AI & ML Enthusiast

### Technologies

`Python` · `Flask` · `PostgreSQL` · `SQLAlchemy` · `Bootstrap` · `JavaScript` · `HTML` · `CSS`

---

⭐ If you find this project useful, consider giving the repository a star.
