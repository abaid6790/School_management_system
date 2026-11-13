# User Guide

This guide follows the order in which a school is normally set up and then used day to day. Menu names match the sidebar. Not every role sees every menu — see [ROLES_AND_PERMISSIONS.md](ROLES_AND_PERMISSIONS.md).

## 1. First-time setup checklist (Admin)

Do these roughly in order — later steps need the earlier ones to exist.

1. **Register the school** at `/auth/register`: school name, a short URL-style *slug* (lowercase letters, digits, hyphens), your name, email and password (8+ characters). You become the school's Admin.
2. **Verify your email** using the link sent to you (valid 24 hours; use *Resend verification* on the login page if it expires), then log in.
3. **System → Academic Sessions → New Session.** Enter a name such as `2026-2027`, start and end dates, and tick *Make this the active session*. Only one session can be active; most screens work only with the active session.
4. **Academics → Classes → New Class** (for example *Grade 8*), then open the class's **sections** link to add *A*, *B*, … (with an optional room and capacity). Classes belong to the session that was active when you created them.
5. **Academics → Teachers → Add Teacher.** Each teacher receives an email to set their own password. Add teachers *before* the next step so they can be selected.
6. **Academics → Subjects → New Subject.** Choose the class, code, maximum/passing marks, type, and the teacher who teaches it. (Class teachers are set on the class/section edit forms.)
7. *(If you use timetables)* **Timetable → Manage Periods**: define the school-wide period grid (Period 1 08:00–08:45, Lunch Break marked as a break, …).
8. *(If you use exams)* **Examinations → Exams → Grade Bands**: define your grading scale (for example 90–100 = A+). Ranges must not overlap; gaps are allowed but a percentage in a gap gets no letter grade.
9. *(If you charge fees)* **Finance → Fees → Fee Types**: create *Tuition Fee*, *Admission Fee*, … with optional default amounts.
10. *(If you track expenses)* **Finance → Expenses → Categories**: create *Electricity*, *Maintenance*, …
11. **Academics → Staff → Add Staff Member** for non-teaching employees. Tick *needs login* only for Accountants and Receptionists (they get a setup email like teachers do).
12. **Admit your students** (section 2) and link their guardians.

## 2. Students and guardians

**Admit a student:** *Academics → Admissions* (or *Students → Admit Student*). The admission number is suggested (`ADM-<year>-0001`) but editable and must be unique. Choose the class, then the section (the list filters to that class), and a roll number — it must be unique within that class/section for the session. The student starts as *Active*.

**Student profile** shows personal and academic details, guardians, documents, attendance %, and links to **View Results** and **View Fees**.

- **Edit** changes details and can move the student to another class/section (this *corrects* the current placement; it is not a yearly promotion — promotion is not built yet).
- **Change Status** (Admin) sets Active, Inactive, Graduated, Transferred or Withdrawn with an optional reason that is appended to the notes. Students are never deleted, so their attendance, fees and results stay intact.
- **Guardians → Add Guardian:** first search for an existing guardian by name or phone — siblings should share **one** guardian record — and link them with a relationship, or create a new guardian. *Remove* only unlinks; the guardian record stays.
- **Documents:** upload PDF/JPG/PNG files (up to 8 MB) such as a birth certificate. Files are checked by content, not just by name. Admin can delete.

**Parents menu** lists all guardians with search; open one to see all linked children. **Give each guardian an email address** if you want them to receive notices, homework and reminders — guardians have no logins, so email is the only way they are reached.

## 3. Attendance

*Attendance → Mark Attendance:* choose class, section and date. Everyone defaults to Present — change exceptions, or use **Mark All Present**, then **Save**. Saving again for the same date **updates** it; it never duplicates. The page lists each student's current roll number.

Statuses are Present, Absent, Late, Excused and Leave. **Attendance % = (Present + Late) ÷ (Present + Late + Absent)**; Excused and Leave days are left out so an excused absence doesn't count against anyone.

Reports: **Daily Report** (counts and a list for a date, optionally by class) and **Low Attendance** (students below the school's minimum, default **75%**, over a date range; a student needs at least 5 counted days to appear). The threshold is stored in school settings but there is no screen to change it yet.

**Teacher attendance** (Admin): *Attendance → Mark Teacher Attendance* and *Daily Teacher Report*. Each teacher's profile has **Attendance History** by month.

## 4. Leave

*Leave → Apply for Leave.* Admins and Receptionists choose who the leave is for (student, teacher or staff member); a teacher's form is for themselves. Types: sick, casual, annual, emergency, other.

Only an **Admin** approves or rejects. **Approving writes the days into attendance automatically** — students become *Excused*, teachers become *Leave* — overwriting anything already marked on those dates. Rejected or cancelled requests never touch attendance. Staff leave is recorded but has no attendance effect (there is no staff attendance module). A pending request can be cancelled; a decided one cannot.

## 5. Timetable

*Timetable* shows a weekly grid for the chosen class and section. Admins click **+ Add** in a cell, choose a subject (the subject's teacher is pre-selected, change it for a substitute) and optionally a room. The system refuses a double booking and says exactly why: the section already has a subject in that period, the teacher is teaching another class then, or the room is taken. Break periods can be left empty. **Daily View** lists a whole day across classes; teachers use **My Timetable**.

## 6. Exams, marks, results and report cards

1. **Examinations → Exams → New Exam.** Pick the class (fixed afterwards), type, name and dates. The exam applies to *all sections* of that class.
2. Open the exam → **Add Subject** for each paper. Maximum/passing marks default from the subject but can differ per exam (a 20-mark quiz in a 100-mark subject). Date, time and room are optional.
3. **Enter Marks** (per subject; available to the Admin and that subject's teacher). Type marks for each student; a **blank box skips** that student and never overwrites an existing mark. Marks must be between 0 and the maximum; if any row is invalid nothing is saved and you see which students to fix. Decimals are allowed.
4. **View Class Results:** rank, total, percentage, grade and Pass/Fail per student. A student **passes only if every subject with a recorded mark is at or above its passing mark**, regardless of total percentage. Rows marked *Incomplete* are missing at least one subject. Ranking is competition-style (1, 2, 2, 4 when two students tie) and is based on percentage, so treat it as **provisional until every subject is fully marked**.
5. **Report Card** (per student): subject-wise marks, total, percentage, grade, class position, attendance %, and teacher's/principal's remarks. Type the remarks and **Save Remarks**, then **Download PDF** (A4). Attendance on the card is for the whole session so far, not just the exam period. There is no school logo yet.

Safeguards: you cannot remove a subject from an exam, or lower its maximum below an already recorded mark, once marks exist.

## 7. Fees

- **Assign:** one student at a time from the student profile (**View Fees → Assign Fee**), or many at once with **Fees → Assign Fee to Class** (a whole class or one section; it skips students who already have that fee with the same due date, so re-running is safe). The amount defaults from the fee type and can be changed.
- **Collect:** on the student's fee page click **Record Payment**. The amount defaults to the full remaining balance — lower it for a partial payment. A payment can't exceed what's still owed. Each payment gets a receipt number like `RCPT-2026-00001`; open the receipt and **Download PDF**.
- **Discounts** (Admin/Accountant): **Add Discount** with a type (fixed, percentage, scholarship, need-based, custom) and a **required reason**. Percentage discounts are calculated once, on the fee amount at that time. A discount can't exceed the fee, and can't push the net amount below what's already been paid. You can remove a discount; it is audit-logged.
- **Status** is always calculated: *Paid*, *Partially Paid*, *Unpaid*, or *Overdue* (unpaid balance past its due date, based on the server's date).
- **Fee Defaulters:** students with an outstanding balance (summed across all their fees), filterable by class, section and minimum days overdue (measured from their oldest outstanding due date).
- **Fee Statement** on the student's fee page gives all fees, discounts, payments and balances, with a PDF.
- **Fee reminders:** the defaulters report has a **Send fee reminders** button that emails guardians one message per family; see section 12.

## 8. Expenses, salaries and the financial summary

- **Expenses:** *Expenses → New Expense* with a category, description, amount, date, payment method and optional vendor. The list can be filtered by category and date and shows the total for the filter. Only an Admin can delete.
- **Salaries:** *Salaries → Generate Salary* for a teacher or staff member and a month (any date in the month; it's stored as the 1st). Net salary = basic + allowances + bonus − deductions. One record per person per month. A *pending* record can be edited; **Mark Paid** stamps today's date and locks it. **Download Slip** gives a PDF. Teachers can see their own history under **My Salary** on their profile.
- **Reports → Financial Summary** (Admin/Accountant): income, expenses, salaries paid and net balance for a date range (default: this month), plus expenses by category. It is **cash-basis**: income counts fee payments *received* in the range, and salaries count only records *marked paid* in the range — not fees merely billed or salaries merely generated.

## 9. Notices and the school calendar

**Notices (Admin).** *Communication → Notices → New Notice.* Choose who it is for: everyone, all staff, teachers only, parents, students, or one class (optionally one section). Optionally set an expiry date (it stays visible through that day and can't be in the past) and pin it to the top. **Save as draft** or **Publish now**. Notice text is plain text; line breaks are kept.

- Teachers, Accountants and Receptionists get a read-only **Notice Board** showing published, unexpired notices addressed to them (everyone and all-staff notices; teachers also see teachers-only ones).
- A published notice can be **edited** (changes are audit-logged) and **archived**, and an archived one can be **re-published**. Only **drafts** can be deleted, so what the school communicated stays on record.
- The first time a notice is published, the people it is addressed to are notified (see section 12). Re-publishing an archived notice does not notify anyone again.

**Calendar (Admin adds, everyone reads).** *Communication → Events* shows a Monday-first month grid; multi-day events fill every day they cover and up to three show per day, with "+N more". The **List** view shows upcoming events with date and type filters. Admins add an event with the "+" on any day or **New Event**. Event types are holiday, exam, sports, cultural, meeting, trip and other. A **holiday** always marks the school as closed, and any other type can opt in; closed days are shaded, and the **student and teacher attendance pages warn** when you mark attendance on a closed date (you can still record it if classes were held).

## 10. Homework

*Communication → Homework → Assign Homework.* Pick the class, optionally one section (otherwise every section), the subject and the dates. **Teachers can assign only for subjects assigned to them**; an Admin can choose any subject and teacher (leave the teacher on "the subject's own teacher" to use the one set on the subject). Class, section and subject can't be changed afterwards — cancel and create a new one.

- The homework page lists every **active student currently in that class/section**, in roll order. The owning teacher (or an Admin) records **Submitted, Late, Missing or Excused** and optional remarks, then **Save submissions**. Choosing "— not recorded —" clears an entry; a student you leave out of a request is never touched.
- **Handed in %** is (Submitted + Late) ÷ (students − Excused), and is always calculated, never stored. A student who leaves the class or becomes inactive stops counting.
- Every teacher can *view* all homework (the list defaults to "my upcoming"), but only the owner or an Admin can edit, cancel, delete or record submissions. **Cancel** keeps the record and can be undone (**Reinstate**); homework with recorded submissions **can't be deleted**.
- When homework is assigned, the families of the students it is for are emailed (section 12).

## 11. Parent–teacher meetings

*Communication → Parent Meetings.*

1. **Schedule (Admin).** Give the meeting a title, date, start and end time, minutes per appointment (5–120), a location, and optionally a class or section. The day is divided into equal slots; a partial slot at the end is dropped.
2. **Book.** Parents have no logins, so staff book on their behalf. Choose the teacher, the student, a free time slot, and who is coming (the student's linked guardians). Admins and Receptionists can book for any teacher; a teacher can book only for themselves. The app names any clash ("Tea1 is already booked at 09:00–09:15 (with Stu One)", or the family already has an appointment at that time), and refuses the same teacher and student twice in one meeting.
3. **Outcomes.** The teacher concerned (or an Admin) marks an appointment **Done** or **No-show**, can **Reopen** it, and keeps **private notes** that Receptionists and other teachers cannot see. A scheduled appointment can be **cancelled** by an Admin, a Receptionist or its teacher; the slot becomes free again and the cancelled booking stays in the history.
4. **Edit, complete or cancel the meeting (Admin).** Once appointments are booked, the times, appointment length and class are locked (the title, date and location can still change). *Mark completed* reports how many appointments are still marked scheduled. *Cancel meeting* cancels the scheduled appointments but keeps ones that already took place.

## 12. Notifications and email to guardians

**Staff** see a **bell with an unread count** in the sidebar and a **Notifications** inbox (times shown in UTC). Clicking one marks it read and opens the related page; *Mark all as read* clears the list.

**Guardians have no logins**, so they are reached by **email** — give each guardian record an email address. Every attempt is recorded per guardian, and *Notifications → Email delivery log* (Admin) shows each as **Sent**, **Failed** (with the reason), **No email address** or **Pending**.

| What happens | Staff (in-app) | Families (email) |
|---|---|---|
| A notice is published for the first time | Staff it is addressed to | Everyone / parents / the chosen class's families |
| An event is added | All staff | Only if the school is closed |
| Homework is assigned | — | Families of the students in that class/section |
| A meeting appointment is booked or cancelled | The teacher (unless they did it themselves) | The guardian chosen for that appointment |
| A meeting is cancelled | The affected teachers | Guardians of its scheduled appointments |
| A leave request is approved or rejected | The teacher who applied | The student's guardians (student leave) |

A family with several children in the same mailing receives **one** email, not one per child. Emails are sent after the change is saved, in the background, so a mail problem never stops the action you took. **Retry** (on the delivery log) resends emails that failed, ones whose guardian has since been given an address, and ones stuck "pending" for over ten minutes (for example after a server restart); it never resends something already sent.

**Fee reminders (Admin or Accountant).** On *Fees → Fee Defaulters*, **Send fee reminders** emails the guardians of the students currently listed (same class/section/overdue filters). Each family gets **one** email listing every child's outstanding balance. A guardian already reminded in the last 24 hours is skipped, so a double-click can't send twice. Reminders are sent only when you press the button — there are no automatic scheduled reminders yet.

If email isn't configured, or `GUARDIAN_EMAILS_ENABLED=False`, the notifications are still recorded and the log says why nothing was sent (see [INSTALLATION.md](INSTALLATION.md#6-email-gmail-app-password)).

## 13. Audit log

*System → Audit Log* (Admin) lists who did what and when: registrations and logins, student/teacher/staff changes, attendance marking, marks entry, payments, discounts, salaries, and so on. (Stored old/new values are not shown on screen yet.)

## 14. Everyday tips and common refusals

| If the app says… | It means… |
|---|---|
| "Roll number already used in that class/section" | Roll numbers are unique per class/section per session. |
| "Create and activate an academic session first" | Most screens need an active session (System → Academic Sessions). |
| "<Teacher> is already teaching … at this time" | Timetable clash — one teacher can't be in two classes in the same period. |
| "Can't remove this subject — marks have already been recorded" | A subject with recorded marks stays in the exam. Marks cannot be deleted from the UI, by design. |
| "Amount can't exceed the remaining balance" | Overpayment guard on fee payments. |
| "A paid salary record can't be edited" | Paid records are locked to keep payroll history trustworthy. |
| "Your account has been deactivated" | The person's employment status is not Active. |
| Pages look unstyled | The browser can't reach the Bootstrap CDN (no internet). |
| "Only drafts can be deleted" (notices) | Published notices are kept on record — archive them instead. |
| "Submissions have been recorded … can't be deleted" (homework) | Cancel the homework instead; its records stay. |
| "<Teacher> is already booked at …" / "family already has an appointment …" | Meeting slot clash — pick another slot. |
| An email shows **No email address** or **Failed** in the delivery log | Add/fix the guardian's address, then use **Retry**. |

## Sidebar reference

Items marked *coming soon* appear in the sidebar so you can see the planned structure, but have no page yet. (Exam **results** are reached from *Exams → an exam → View Class Results* or from a student's profile.)

<!-- SIDEBAR:START -->
| Section | Menu item | Status | Visible to |
|---|---|---|---|
| — | Dashboard | available | Admin, Teacher, Accountant, Receptionist, Super Admin |
| Academics | Students | available | Admin, Receptionist, Teacher |
| Academics | Admissions | available | Admin, Receptionist |
| Academics | Parents | available | Admin, Receptionist |
| Academics | Teachers | available | Admin |
| Academics | Staff | available | Admin |
| Academics | Classes | available | Admin |
| Academics | Sections | available | Admin |
| Academics | Subjects | available | Admin, Teacher |
| Attendance & Schedule | Attendance | available | Admin, Teacher |
| Attendance & Schedule | Timetable | available | Admin, Teacher |
| Attendance & Schedule | Leave | available | Admin, Teacher, Receptionist |
| Examinations | Exams | available | Admin, Teacher |
| Examinations | Results | *coming soon* (placeholder) | Admin, Teacher |
| Finance | Fees | available | Admin, Accountant, Receptionist |
| Finance | Expenses | available | Admin, Accountant |
| Finance | Salaries | available | Admin, Accountant |
| Communication | Homework | available | Admin, Teacher |
| Communication | Notices | available | Admin, Teacher, Accountant, Receptionist |
| Communication | Events | available | Admin, Teacher, Accountant, Receptionist |
| Communication | Parent Meetings | available | Admin, Teacher, Receptionist |
| System | Reports | available | Admin, Accountant |
| System | Audit Log | available | Admin, Super Admin |
| System | Academic Sessions | available | Admin |
| System | Settings | *coming soon* (placeholder) | Admin |
<!-- SIDEBAR:END -->
