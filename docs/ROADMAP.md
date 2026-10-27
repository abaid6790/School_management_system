# Roadmap, Gaps and Known Limitations

An honest account of what exists and what doesn't. "Spec §" refers to the numbered sections of the original requirements document.

## Built (Phases 0–7)

Foundation and auth · academic setup · students, guardians, teachers, staff, documents · student/teacher attendance and leave · timetable · exams, marks, grading, results, report cards · student fees, payments, discounts, defaulters · expenses, salaries, financial summary. Details per phase: [CHANGELOG.md](../CHANGELOG.md).

## Not built yet

| Planned phase | Item | Spec § |
|---|---|---|
| **8 — Communication** | Homework | 34 |
| | Notices & announcements | 35 |
| | Events | 36 |
| | Parent–teacher meetings | 37 |
| | Notifications (fee due, low attendance, results, leave…) and email/SMS/in-app delivery | 44, 45 |
| **9 — Lifecycle** | Student **promotion** to the next session (history-preserving) | 38 |
| | Transfer / withdrawal workflow and transfer certificates | 39 |
| **10 — Reports & dashboard** | Real **dashboard** statistics and charts (today's page is a placeholder) | 2 |
| | Fuller reports: weekly/monthly/class attendance, student & fee reports, exam analytics | 16, 41 |
| | Student and teacher ID cards (incl. bulk) | 42, 43 |
| | Admission form/receipt printing; attendance, profile and result-sheet PDFs | 7, 52 |
| | Global search across students, teachers, receipts… | 40 |
| **11 — Data operations** | CSV/Excel import (with preview/validation) and export | 51 |
| | In-app backup and restore | 50 |
| | School **Settings** screens (grading rules, attendance thresholds, fee fines, school info, logo) | 53 |
| | Performance pass (indexes review, pagination everywhere, large-data testing) | 56 |
| **12 — Testing & polish** | Automated test suite | 59 |
| | Responsive/mobile polish, custom error pages, accessibility | 54 |
| *Optional add-ons* | QR-code attendance | 15 |
| | Parent and Student logins/portals | 49 |
| | Super Admin management screens (list/suspend schools) | 49 |
| | Photo upload (students, teachers) and school logo upload — the database columns exist, the screens don't | 4, 12, 26 |

Sidebar entries for **Results, Homework, Notices, Events and Settings** are placeholders marked "soon". Exam results are reachable from the exam page and a student's profile.

## Known limitations of what *is* built

**Access control**
- Teachers can view all students, exams and results and mark attendance for any class, not only their own.
- Receptionist/Accountant access is deliberately narrow; there is no custom-role system.

**Security** (see [ARCHITECTURE.md](ARCHITECTURE.md#security-measures-and-known-gaps))
- No login throttling/lockout; open school registration; password-reset/setup links are not single-use; no 2FA.

**Behaviour**
- **Exam ranking** is by percentage; a student with only some subjects marked is ranked alongside fully-marked students (flagged *Incomplete* but not excluded).
- Report-card attendance covers the whole session to date, not the exam period.
- **Defaulters report** aggregates in Python by reusing the per-fee calculation (correct and consistent, but slower than a single SQL aggregate on very large fee histories).
- **Attendance** is daily only (no per-period attendance); the minimum-attendance threshold exists in the database but has no editing screen.
- Settings fields present in the database but not yet used: late-arrival threshold, fee fine per day, default payment methods.
- Leave approval cannot be undone from the UI, and approving overwrites existing attendance for those dates.
- Classes belong to one academic session; there is no tool yet to carry classes, sections, subjects and students into the next session (promotion, Phase 9).
- Only one academic session is active at a time; "current" screens operate on it.
- A student's current class/section is corrected via *Edit*; this is not a promotion and doesn't create a new enrollment record.
- Audit logs store old/new values but the screen shows only action, table, record, user and time.
- Only auth-related emails are sent (verification, reset, account setup).
- No currency symbol or multi-currency support; "today" is the server's date; all PDFs are A4.
- Uploaded documents live on disk, so backups must include the uploads folder.
- Bootstrap and icons are loaded from a CDN, so the browser needs internet access.

**Engineering**
- No automated tests; no continuous integration; no containerisation.
- Requires Python 3.10+.
