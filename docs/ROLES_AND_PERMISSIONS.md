# Roles and Permissions

Permissions are enforced **on the server** for every protected URL (`@role_required`). Hiding a menu item is only cosmetic. The exact allowed roles per URL are in the generated [ROUTES.md](ROUTES.md); this page explains them in human terms.

## Roles

| Role | Who | Logs in today? |
|---|---|---|
| **Admin** | The school's administrator. The person who registers a school becomes its first Admin. Full control of that school. | Yes |
| **Teacher** | Teaching staff. Created by an Admin (Teachers → Add Teacher). | Yes |
| **Accountant** | Handles fees, expenses and salaries. Created by an Admin by adding a **Staff** member with "needs login" and the Accountant role. | Yes |
| **Receptionist** | Front desk: admissions, guardians, fee collection. Created the same way as an Accountant. | Yes |
| **Super Admin** | Platform-level operator, not tied to any school. Created only through the shell (see [INSTALLATION.md](INSTALLATION.md#9-working-without-email-development-only)). | Yes, but only the dashboard and audit log |
| Parent, Student | Defined in the data model for the future. **No login or portal exists yet.** | No |

Drivers, cleaners, security guards and other staff who don't need the system get a **Staff record without a login**.

## Permission matrix

✔ = allowed, — = not allowed. "own" = only records that belong to the signed-in person.

| Area / action | Admin | Teacher | Accountant | Receptionist |
|---|:-:|:-:|:-:|:-:|
| **Academic setup** — sessions, classes, sections, subjects, periods | ✔ | — | — | — |
| **Students** — view list and profile | ✔ | ✔ | — | ✔ |
| Students — admit, edit | ✔ | — | — | ✔ |
| Students — change status (archive, withdraw, …) | ✔ | — | — | — |
| Student documents — upload | ✔ | — | — | ✔ |
| Student documents — download | ✔ | ✔ | — | ✔ |
| Student documents — delete | ✔ | — | — | — |
| **Guardians** — view, create, edit, link/unlink | ✔ | — | — | ✔ |
| **Teachers** — list, add, edit, change employment status | ✔ | — | — | — |
| Teachers — view a profile | ✔ | own | — | — |
| **Staff** — all actions | ✔ | — | — | — |
| **Student attendance** — mark, daily report, low-attendance report | ✔ | ✔ | — | — |
| **Teacher attendance** — mark, daily report | ✔ | — | — | — |
| Teacher attendance — history | ✔ | own | — | — |
| **Leave** — see the list / open a request | ✔ all | own | — | ✔ all |
| Leave — apply | ✔ for anyone | ✔ for self | — | ✔ for anyone |
| Leave — approve / reject | ✔ | — | — | — |
| Leave — cancel a pending request | ✔ | own | — | — |
| **Timetable** — view class grid, daily view | ✔ | ✔ | — | — |
| Timetable — add / edit / remove entries | ✔ | — | — | — |
| Timetable — a teacher's own weekly view | ✔ any | own | — | — |
| **Exams** — view exams, results, report cards; save remarks; download PDF | ✔ | ✔ | — | — |
| Exams — create / edit, add subjects, change status, grade bands | ✔ | — | — | — |
| Marks — enter | ✔ | ✔ only for subjects assigned to them | — | — |
| A student's exam-results page | ✔ | ✔ | — | ✔ |
| **Fees** — landing page, defaulters report | ✔ | — | ✔ | ✔ |
| Fee types — view | ✔ | — | ✔ | — |
| Fee types — create, edit, activate/deactivate | ✔ | — | — | — |
| Fees — assign to a whole class/section | ✔ | — | ✔ | — |
| Fees — view / assign for one student, record payments, receipts, statements | ✔ | — | ✔ | ✔ |
| Fees — add / remove discounts | ✔ | — | ✔ | — |
| **Expenses** — view, add, edit; view categories | ✔ | — | ✔ | — |
| Expenses — delete; create/edit/deactivate categories | ✔ | — | — | — |
| **Salaries** — list, generate, view, edit (pending), mark paid, slip PDF | ✔ | — | ✔ | — |
| Salaries — own salary history, view and download own slip | — | own | — | — |
| **Financial summary** report | ✔ | — | ✔ | — |
| **Audit log** | ✔ (own school) | — | — | — |
| Dashboard | ✔ | ✔ | ✔ | ✔ |

The **Super Admin** can open the dashboard and the audit log (across all schools) and is refused (403) everywhere else.

## Rules behind the matrix

- **School isolation.** Every user sees only their own school's data; another school's record ids return "not found".
- **Ownership checks** apply on top of roles: a teacher can open only their own profile, attendance history, timetable and salary records; marks can be entered only by the teacher assigned to that subject (or an Admin).
- **Approval is Admin-only.** Teachers can request leave for themselves but cannot approve anything, including their own request.
- **Deactivating a person blocks login.** Setting a teacher's or staff member's employment status to anything other than *Active* (resigned, terminated, on leave) also disables their login immediately.
- **Account creation never exposes passwords.** When an Admin adds a teacher or a login-enabled staff member, the system emails them a one-time-style setup link (valid 24 hours) so they choose their own password.
- **Money screens are separate from academic screens.** Teachers cannot see fees, expenses, or other people's salaries; Receptionists can collect fees but cannot grant discounts.

## Known simplifications

- Teachers are not limited to "their" classes: they can view every student, exam and result in the school and can mark attendance for any class. Tightening this is on the [roadmap](ROADMAP.md).
- Accountants and Receptionists have no academic access beyond what's listed (for example, a Receptionist can open a student's profile and exam-results page but not the exams module).
- Only one level of administration exists inside a school: there is no "Principal" or "Vice-Principal" role distinct from Admin.
