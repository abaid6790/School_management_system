# Installation Guide

This guide targets **Windows** (the project's primary environment). Linux/macOS differ only in the shell commands (`source venv/bin/activate`, `export FLASK_APP=run.py`).

## 1. Prerequisites

| Requirement | Notes |
|---|---|
| **Python 3.10 or newer** | Developed and tested on 3.12. The code uses `X \| None` type syntax, which needs 3.10+. Install from python.org and tick **"Add python.exe to PATH"**. Check with `python --version`. |
| **PostgreSQL 14 or newer** | Tested on 16. Use the installer from postgresql.org (it includes pgAdmin and `psql`). Remember the password you set for the `postgres` user. |
| **A browser with internet access** | Bootstrap and Bootstrap Icons are loaded from a CDN; without internet the pages render unstyled. |
| **An email account for SMTP** (optional while experimenting) | Used for verification, password-reset and account-setup emails. See section 6. |

## 2. Get the code

Unzip the project somewhere without spaces in the path, for example `D:\SMS`.

## 3. Create a virtual environment and install dependencies

```bat
cd D:\SMS
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Dependencies are **pinned on purpose** (notably `SQLAlchemy==2.0.36` and `alembic==1.13.3`). Do not upgrade them casually — a newer SQLAlchemy changed its default PostgreSQL driver and broke database connections during development (see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)).

## 4. Create the database

**Option A — pgAdmin:** right-click *Databases* → *Create* → *Database…* → name it `school_management_db`.

**Option B — psql:**

```bat
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -c "CREATE DATABASE school_management_db;"
```

Only the empty database is needed. The tables are created by migrations (section 7), not automatically when the app starts.

## 5. Configure `.env`

```bat
copy .env.example .env
```

Then edit `.env`:

| Variable | Required | Meaning |
|---|---|---|
| `SECRET_KEY` | yes | Signs sessions and email links. Generate one: `python -c "import secrets; print(secrets.token_hex(32))"`. Changing it later logs everyone out and invalidates unused email links. |
| `DATABASE_URL` | yes | `postgresql+psycopg2://USER:PASSWORD@localhost:5432/school_management_db`. Keep the `+psycopg2` part. If the password contains special characters, URL-encode them (`@`→`%40`, `:`→`%3A`, `/`→`%2F`, `#`→`%23`, `%`→`%25`). |
| `FLASK_ENV` | no | `development` (default) or `production`. Selects the config class: development turns debug on; production turns it off and marks cookies `Secure` (HTTPS only). |
| `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USE_SSL` | no | Defaults are for Gmail: `smtp.gmail.com`, `587`, `True`, `False`. |
| `MAIL_USERNAME`, `MAIL_PASSWORD` | for email | Full Gmail address and an **App Password** (section 6). |
| `MAIL_DEFAULT_SENDER` | no | Defaults to `MAIL_USERNAME`. |
| `APP_NAME` | no | Shown in the sidebar and emails. |
| `UPLOAD_FOLDER` | no | Where uploaded student documents are stored. Default `instance/uploads` inside the project. |
| `APP_HOST`, `APP_PORT` | no | Dev server binding for `python run.py`. Default `127.0.0.1:5000`. |

`.env` holds secrets — never commit it or share it. (`.gitignore` already excludes it.)

## 6. Email: Gmail App Password

Regular Gmail passwords do not work for SMTP. You need an **App Password**:

1. Turn on **2-Step Verification** for the Gmail account (Google Account → Security).
2. Open <https://myaccount.google.com/apppasswords>, create an app password (any name, e.g. "SMS").
3. Google shows a 16-character code. Put it in `MAIL_PASSWORD` **without spaces**, and put the full address in `MAIL_USERNAME`.

The app sends email for: school-registration **verification** (link valid 24 hours), **password reset** (1 hour), and **account setup** for teachers and login-enabled staff created by an Admin (24 hours). If sending fails, the app tells you instead of pretending it worked, and writes the reason to the terminal log.

## 7. Create the tables

```bat
set FLASK_APP=run.py
flask db upgrade
```

PowerShell: `$env:FLASK_APP = "run.py"`.

You should see four `Running upgrade` lines. `flask db current` should then report the latest revision as `(head)`. **Run `flask db upgrade` again after installing any newer version of the project** — new phases add migrations.

## 8. Run it

```bat
python run.py
```

Open <http://127.0.0.1:5000/auth/register>, register your school (this creates the school and its first Admin), click the link in the verification email, then log in. Continue with the first-time checklist in [USER_GUIDE.md](USER_GUIDE.md). Stop the server with `Ctrl+C`.

`run.py` listens on `127.0.0.1` only, deliberately, because development mode exposes the Flask debugger. Set `APP_HOST=0.0.0.0` only on a trusted network and never in production.

## 9. Working without email (development only)

If SMTP is not set up yet you can still use the app. Open a shell with the app loaded:

```bat
set FLASK_APP=run.py
flask shell
```

**Verify a registered user manually:**

```python
from app.extensions import db
from app.models import User
u = User.query.filter_by(email="you@example.com").first()
u.is_verified = True
u.verification_token = None
db.session.commit()
```

**Set someone's password directly** (for example a teacher whose setup email never arrived):

```python
u = User.query.filter_by(email="teacher@example.com").first()
u.set_password("ChangeMe123!")   # at least 8 characters
db.session.commit()
```

**Create a platform Super Admin** (not tied to any school):

```python
from app.extensions import db
from app.models import User
from app.models.enums import UserRole
u = User(name="Platform Admin", email="super@example.com",
         role=UserRole.SUPER_ADMIN, school_id=None, is_verified=True)
u.set_password("ChangeMe123!")
db.session.add(u)
db.session.commit()
```

A Super Admin can currently sign in and read the audit log across all schools; there are no other Super Admin screens yet (see [ROADMAP.md](ROADMAP.md)).

## 10. Production notes

The built-in `python run.py` server is for development. For real use:

1. Set `FLASK_ENV=production` in `.env`. This disables debug mode **and marks session cookies `Secure`, so the site must be served over HTTPS** or logins will not stick.
2. Use a production WSGI server. On Windows, [Waitress](https://docs.pylonsproject.org/projects/waitress/) works well (it is *not* in `requirements.txt`; install it with `pip install waitress`):

   ```bat
   waitress-serve --listen=127.0.0.1:8000 --call app:create_app
   ```

   Put a reverse proxy that handles HTTPS (IIS, nginx, Caddy) in front of it. The app does not configure proxy-header handling, so audit-log IP addresses will show the proxy's address.
3. Use a strong random `SECRET_KEY`, and give the app its own limited PostgreSQL user instead of the `postgres` superuser.
4. **School registration is open**: anyone who can reach `/auth/register` can create a new school (it is isolated from yours, but it still consumes resources). For a single-school deployment, restrict access at the network/proxy level or remove the route. See [ARCHITECTURE.md](ARCHITECTURE.md#security-measures-and-known-gaps).
5. Back up regularly (section 11) — both the database **and** the uploads folder.
6. "Today" for overdue calculations, default report ranges and attendance defaults is the **server's local date**.

## 11. Backups

There is no in-app backup feature yet (it is on the [roadmap](ROADMAP.md)). Until then:

```bat
:: back up (custom format, compressed)
pg_dump -U postgres -F c -f sms_backup.dump school_management_db

:: restore into an empty database
psql -U postgres -c "CREATE DATABASE school_management_db_restored;"
pg_restore -U postgres -d school_management_db_restored sms_backup.dump
```

(`pg_dump` / `pg_restore` live in `C:\Program Files\PostgreSQL\16\bin` — add it to your PATH or use the full path.) Also copy the uploads folder (`instance\uploads`, or whatever `UPLOAD_FOLDER` points to), because uploaded documents are stored on disk, not in the database.

## 12. Upgrading to a newer version of the project

1. Back up the database and the uploads folder.
2. Unzip the new version over a copy of the project, keeping your `.env` and uploads folder.
3. Activate the venv, then `pip install -r requirements.txt`.
4. Run `flask db upgrade`.
5. Restart the server.
