# Troubleshooting

## Setup and database

**`relation "users" does not exist` when logging in (or any other `UndefinedTable` error)**
The tables were never created. The database exists but is empty. Run, in the project folder with the venv active:

```bat
set FLASK_APP=run.py
flask db upgrade
```

**`ModuleNotFoundError: No module named 'psycopg'`**
SQLAlchemy 2.1 and newer default to the `psycopg` (v3) driver for `postgresql://` URLs. Keep the driver explicit: `DATABASE_URL=postgresql+psycopg2://…`, and use the pinned `requirements.txt` (`SQLAlchemy==2.0.36`). Recreate the venv if it already has a newer SQLAlchemy: `pip install -r requirements.txt`.

**`Error: No such command 'db'`**
Usually means Flask could not import the app, so the Flask-Migrate command never registered. Look **above** this line for the real error (a missing module, a bad `.env`, a database URL problem). Also check the venv is active and `FLASK_APP=run.py` is set.

**`'flask' is not recognized as an internal or external command`**
The virtual environment isn't active. Run `venv\Scripts\activate`.

**`password authentication failed for user "postgres"`**
The password in `DATABASE_URL` is wrong. If it contains special characters, URL-encode them (`@` → `%40`, `:` → `%3A`, `/` → `%2F`, `#` → `%23`, `%` → `%25`).

**`database "school_management_db" does not exist`**
Create it first (INSTALLATION.md, section 4), then `flask db upgrade`.

**`could not connect to server` / connection refused**
PostgreSQL isn't running, or `localhost:5432` is wrong. Start the *postgresql* service (Windows → Services) and check the port.

**`RuntimeError: SECRET_KEY is not set` or `DATABASE_URL is not set`**
`.env` is missing or not in the project root. Copy `.env.example` to `.env` and fill it in.

**Migrations: "Target database is not up to date"** — run `flask db upgrade` before `flask db migrate`.

**Migrations: "Can't locate revision identified by '…'"**
The database's recorded revision isn't in your `migrations/versions/` folder — typically from mixing files from different project copies. On a **development** database with nothing to keep, drop and recreate it, then `flask db upgrade`. On real data, stop and get help; don't edit the `alembic_version` table casually.

## Email

**"Account created, but the verification email couldn't be sent"** (or a similar warning for teachers)
The account *was* created; only the email failed. Check:
- `MAIL_USERNAME` is the full Gmail address and `MAIL_PASSWORD` is a 16-character **App Password** (not your normal password), pasted without spaces.
- 2-Step Verification is enabled on the Gmail account.
- Port 587 isn't blocked by a firewall or antivirus.
- The terminal running the app prints `Failed to send email to …: <reason>` — that reason is the real answer.

Meanwhile you can verify a user or set a password from the shell: [INSTALLATION.md §9](INSTALLATION.md#9-working-without-email-development-only).

**"Your verification link has expired"** — use *Resend verification* on the login page. Verification links last 24 hours, reset links 1 hour, account-setup links 24 hours.

## Using the app

**"Please verify your email before logging in"** — click the emailed link, or resend it.

**"Your account has been deactivated"** — the person's employment status is not *Active* (Teachers/Staff → Change Status).

**Pages look unstyled or icons are missing** — the browser cannot reach the Bootstrap CDN (`cdn.jsdelivr.net`). Connect to the internet; offline hosting of assets isn't set up.

**`413 Request Entity Too Large` on upload** — the file exceeds the 8 MB limit.

**"File type not allowed" / "doesn't look like a valid PDF/image"** — only PDF, JPG, JPEG and PNG are accepted, and the content must match the extension.

**Fees show *Overdue* unexpectedly** — overdue is judged against the **server's current date**. Check the due date and the computer's clock.

**A teacher "can't see" a class or subject** — teachers must be selected on the subject (or class/section) form; they appear only after being added under Teachers.

**"Not a valid choice" on a form dropdown** — the selected item was deactivated or no longer exists (for example a deactivated expense category). Reload the form.

**Port 5000 is already in use** — set `APP_PORT=5001` in `.env` and restart.

## Why was my action refused?

| Message (shortened) | Rule |
|---|---|
| Roll number already used in that class/section | Unique per class/section per session |
| Admission number already in use | Unique per school |
| Employee ID already in use | Unique per school (teachers and staff) |
| An account with this email already exists | Emails are unique across the whole platform |
| This school URL is already taken | School slugs are unique |
| X is already teaching … / Room X is already booked / class already has … | Timetable clash |
| Marks must be between 0 and N | Marks validation; nothing was saved |
| Can't remove this subject — marks already recorded | Protects recorded marks |
| Amount can't exceed the remaining balance | Overpayment guard |
| Discount would exceed the fee amount / reduce net below what's paid | Discount guards |
| A salary record already exists for this person for this month | One per person per month |
| A paid salary record can't be edited | Paid records are locked |
| Overlaps with existing grade band | Grade ranges must not overlap |

## Still stuck?

Note the exact error text and the page URL, check the terminal where `python run.py` is running (it prints the traceback), and check the audit log (System → Audit Log) to see what was recorded last.
