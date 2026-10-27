# Route Reference

> **Generated from the route decorators** (`app/routes/`) — do not edit by hand. Regenerate with `python tools/generate_docs.py`. Roles shown are those allowed by `@role_required`; some routes add *ownership* rules on top (for example a teacher may only open their own salary record) — see [ROLES_AND_PERMISSIONS.md](ROLES_AND_PERMISSIONS.md).

**117 routes**, plus `GET /health` (public, defined in `app/__init__.py`).

| Module | URL | Methods | Roles allowed |
|---|---|---|---|
| academic | `/academic/sessions` | GET | ADMIN |
| academic | `/academic/sessions/new` | GET/POST | ADMIN |
| academic | `/academic/sessions/<int:session_id>/activate` | POST | ADMIN |
| academic | `/academic/classes` | GET | ADMIN |
| academic | `/academic/classes/new` | GET/POST | ADMIN |
| academic | `/academic/classes/<int:class_id>/edit` | GET/POST | ADMIN |
| academic | `/academic/classes/<int:class_id>/sections` | GET | ADMIN |
| academic | `/academic/classes/<int:class_id>/sections/new` | GET/POST | ADMIN |
| academic | `/academic/sections/<int:section_id>/edit` | GET/POST | ADMIN |
| academic | `/academic/subjects` | GET | ADMIN |
| academic | `/academic/subjects/new` | GET/POST | ADMIN |
| academic | `/academic/subjects/<int:subject_id>/edit` | GET/POST | ADMIN |
| academic | `/academic/periods` | GET | ADMIN |
| academic | `/academic/periods/new` | GET/POST | ADMIN |
| academic | `/academic/periods/<int:period_id>/edit` | GET/POST | ADMIN |
| attendance | `/attendance/` | GET | ADMIN, TEACHER |
| attendance | `/attendance/mark` | GET/POST | ADMIN, TEACHER |
| attendance | `/attendance/reports/daily` | GET | ADMIN, TEACHER |
| attendance | `/attendance/reports/low-attendance` | GET | ADMIN, TEACHER |
| audit | `/audit-logs` | GET | ADMIN, SUPER_ADMIN |
| auth | `/auth/register` | GET/POST | public (no login) |
| auth | `/auth/verify/<token>` | GET | public (no login) |
| auth | `/auth/resend-verification` | GET/POST | public (no login) |
| auth | `/auth/login` | GET/POST | public (no login) |
| auth | `/auth/logout` | GET | any logged-in user |
| auth | `/auth/forgot-password` | GET/POST | public (no login) |
| auth | `/auth/reset-password/<token>` | GET/POST | public (no login) |
| dashboard | `/` | GET | any logged-in user |
| exams | `/exams/` | GET | ADMIN, TEACHER |
| exams | `/exams/new` | GET/POST | ADMIN |
| exams | `/exams/<int:exam_id>` | GET | ADMIN, TEACHER |
| exams | `/exams/<int:exam_id>/edit` | GET/POST | ADMIN |
| exams | `/exams/<int:exam_id>/status` | POST | ADMIN |
| exams | `/exams/<int:exam_id>/subjects/new` | GET/POST | ADMIN |
| exams | `/exams/<int:exam_id>/subjects/<int:exam_subject_id>/edit` | GET/POST | ADMIN |
| exams | `/exams/<int:exam_id>/subjects/<int:exam_subject_id>/delete` | POST | ADMIN |
| exams | `/exams/<int:exam_id>/subjects/<int:exam_subject_id>/marks` | GET/POST | ADMIN, TEACHER |
| exams | `/exams/grade-bands` | GET | ADMIN |
| exams | `/exams/grade-bands/new` | GET/POST | ADMIN |
| exams | `/exams/grade-bands/<int:band_id>/edit` | GET/POST | ADMIN |
| exams | `/exams/grade-bands/<int:band_id>/delete` | POST | ADMIN |
| exams | `/exams/<int:exam_id>/results` | GET | ADMIN, TEACHER |
| exams | `/exams/<int:exam_id>/results/<int:student_id>` | GET | ADMIN, TEACHER |
| exams | `/exams/<int:exam_id>/report-card/<int:student_id>` | GET | ADMIN, TEACHER |
| exams | `/exams/<int:exam_id>/report-card/<int:student_id>/remarks` | POST | ADMIN, TEACHER |
| exams | `/exams/<int:exam_id>/report-card/<int:student_id>/pdf` | GET | ADMIN, TEACHER |
| expenses | `/expenses/` | GET | ADMIN, ACCOUNTANT |
| expenses | `/expenses/new` | GET/POST | ADMIN, ACCOUNTANT |
| expenses | `/expenses/<int:expense_id>/edit` | GET/POST | ADMIN, ACCOUNTANT |
| expenses | `/expenses/<int:expense_id>/delete` | POST | ADMIN |
| expenses | `/expenses/categories` | GET | ADMIN, ACCOUNTANT |
| expenses | `/expenses/categories/new` | GET/POST | ADMIN |
| expenses | `/expenses/categories/<int:category_id>/edit` | GET/POST | ADMIN |
| expenses | `/expenses/categories/<int:category_id>/toggle-status` | POST | ADMIN |
| fees | `/fees/` | GET | ADMIN, ACCOUNTANT, RECEPTIONIST |
| fees | `/fees/types` | GET | ADMIN, ACCOUNTANT |
| fees | `/fees/types/new` | GET/POST | ADMIN |
| fees | `/fees/types/<int:fee_type_id>/edit` | GET/POST | ADMIN |
| fees | `/fees/types/<int:fee_type_id>/toggle-status` | POST | ADMIN |
| fees | `/fees/assign-bulk` | GET/POST | ADMIN, ACCOUNTANT |
| fees | `/fees/defaulters` | GET | ADMIN, ACCOUNTANT, RECEPTIONIST |
| guardians | `/guardians/` | GET | ADMIN, RECEPTIONIST |
| guardians | `/guardians/new` | GET/POST | ADMIN, RECEPTIONIST |
| guardians | `/guardians/<int:guardian_id>` | GET | ADMIN, RECEPTIONIST |
| guardians | `/guardians/<int:guardian_id>/edit` | GET/POST | ADMIN, RECEPTIONIST |
| leave | `/leave/` | GET | ADMIN, TEACHER, RECEPTIONIST |
| leave | `/leave/new` | GET/POST | ADMIN, RECEPTIONIST, TEACHER |
| leave | `/leave/<int:leave_id>` | GET | ADMIN, TEACHER, RECEPTIONIST |
| leave | `/leave/<int:leave_id>/decide` | POST | ADMIN |
| leave | `/leave/<int:leave_id>/cancel` | POST | ADMIN, TEACHER |
| reports | `/reports/financial-summary` | GET | ADMIN, ACCOUNTANT |
| salaries | `/salaries/` | GET | ADMIN, ACCOUNTANT |
| salaries | `/salaries/new` | GET/POST | ADMIN, ACCOUNTANT |
| salaries | `/salaries/<int:salary_id>` | GET | ADMIN, ACCOUNTANT, TEACHER |
| salaries | `/salaries/<int:salary_id>/mark-paid` | POST | ADMIN, ACCOUNTANT |
| salaries | `/salaries/<int:salary_id>/edit` | GET/POST | ADMIN, ACCOUNTANT |
| salaries | `/salaries/<int:salary_id>/slip/pdf` | GET | ADMIN, ACCOUNTANT, TEACHER |
| salaries | `/salaries/my` | GET | TEACHER |
| staff | `/staff/` | GET | ADMIN |
| staff | `/staff/new` | GET/POST | ADMIN |
| staff | `/staff/<int:staff_id>` | GET | ADMIN |
| staff | `/staff/<int:staff_id>/edit` | GET/POST | ADMIN |
| staff | `/staff/<int:staff_id>/status` | POST | ADMIN |
| students | `/students/` | GET | ADMIN, RECEPTIONIST, TEACHER |
| students | `/students/new` | GET/POST | ADMIN, RECEPTIONIST |
| students | `/students/<int:student_id>` | GET | ADMIN, RECEPTIONIST, TEACHER |
| students | `/students/<int:student_id>/results` | GET | ADMIN, RECEPTIONIST, TEACHER |
| students | `/students/<int:student_id>/fees` | GET | ADMIN, ACCOUNTANT, RECEPTIONIST |
| students | `/students/<int:student_id>/fees/new` | GET/POST | ADMIN, ACCOUNTANT, RECEPTIONIST |
| students | `/students/<int:student_id>/fees/<int:fee_id>/pay` | GET/POST | ADMIN, ACCOUNTANT, RECEPTIONIST |
| students | `/students/<int:student_id>/fees/<int:fee_id>/receipts/<int:payment_id>` | GET | ADMIN, ACCOUNTANT, RECEPTIONIST |
| students | `/students/<int:student_id>/fees/<int:fee_id>/receipts/<int:payment_id>/pdf` | GET | ADMIN, ACCOUNTANT, RECEPTIONIST |
| students | `/students/<int:student_id>/fees/<int:fee_id>/discounts/new` | GET/POST | ADMIN, ACCOUNTANT |
| students | `/students/<int:student_id>/fees/<int:fee_id>/discounts/<int:discount_id>/delete` | POST | ADMIN, ACCOUNTANT |
| students | `/students/<int:student_id>/fees/statement` | GET | ADMIN, ACCOUNTANT, RECEPTIONIST |
| students | `/students/<int:student_id>/fees/statement/pdf` | GET | ADMIN, ACCOUNTANT, RECEPTIONIST |
| students | `/students/<int:student_id>/edit` | GET/POST | ADMIN, RECEPTIONIST |
| students | `/students/<int:student_id>/status` | POST | ADMIN |
| students | `/students/<int:student_id>/guardians/add` | GET/POST | ADMIN, RECEPTIONIST |
| students | `/students/<int:student_id>/guardians/<int:link_id>/unlink` | POST | ADMIN, RECEPTIONIST |
| students | `/students/<int:student_id>/documents/upload` | POST | ADMIN, RECEPTIONIST |
| students | `/students/<int:student_id>/documents/<int:doc_id>/download` | GET | ADMIN, RECEPTIONIST, TEACHER |
| students | `/students/<int:student_id>/documents/<int:doc_id>/delete` | POST | ADMIN |
| teacher_attendance | `/teacher-attendance/mark` | GET/POST | ADMIN |
| teacher_attendance | `/teacher-attendance/reports/daily` | GET | ADMIN |
| teacher_attendance | `/teacher-attendance/history/<int:user_id>` | GET | ADMIN, TEACHER |
| teachers | `/teachers/` | GET | ADMIN |
| teachers | `/teachers/new` | GET/POST | ADMIN |
| teachers | `/teachers/<int:user_id>` | GET | ADMIN, TEACHER |
| teachers | `/teachers/<int:user_id>/edit` | GET/POST | ADMIN |
| teachers | `/teachers/<int:user_id>/status` | POST | ADMIN |
| timetable | `/timetable/` | GET | ADMIN, TEACHER |
| timetable | `/timetable/entry/new` | GET/POST | ADMIN |
| timetable | `/timetable/entry/<int:entry_id>/edit` | GET/POST | ADMIN |
| timetable | `/timetable/entry/<int:entry_id>/delete` | POST | ADMIN |
| timetable | `/timetable/teacher/<int:user_id>` | GET | ADMIN, TEACHER |
| timetable | `/timetable/daily` | GET | ADMIN, TEACHER |
