"""Regenerate the machine-generated documentation from the code itself.

Usage (from the project root, venv active):

    python tools/generate_docs.py

Rewrites:
  docs/DATABASE_SCHEMA.md   from the SQLAlchemy models
  docs/ROUTES.md            from the route decorators
  the sidebar table inside docs/USER_GUIDE.md (between the SIDEBAR markers)

No database connection is needed; dummy settings are used if .env is missing.
"""
import glob
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
os.environ.setdefault("SECRET_KEY", "docs-generation-only")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/docs_generation_only")

from sqlalchemy.dialects import postgresql  # noqa: E402
from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
import app.models  # noqa: E402,F401

create_app("development")

GROUPS = [
    ("Foundation (Phase 0)", ["schools", "users", "academic_sessions", "classes", "sections", "subjects", "school_settings", "audit_logs"]),
    ("People (Phase 1)", ["guardians", "students", "student_enrollments", "student_guardians", "student_documents", "teacher_profiles", "staff"]),
    ("Attendance & leave (Phase 3)", ["student_attendance", "teacher_attendance", "leave_requests"]),
    ("Timetable (Phase 4)", ["periods", "timetable_entries"]),
    ("Examinations (Phase 5)", ["exams", "exam_subjects", "marks", "grade_bands", "report_card_remarks"]),
    ("Student fees (Phase 6)", ["fee_types", "student_fees", "fee_discounts", "fee_payments"]),
    ("School finance (Phase 7)", ["expense_categories", "expenses", "salary_records"]),
]


def schema_doc():
    tables = {t.name: t for t in db.metadata.sorted_tables}
    groups = [g for g in GROUPS]
    leftover = sorted(set(tables) - {n for _, ns in groups for n in ns})
    if leftover:
        groups.append(("Other (add to GROUPS in tools/generate_docs.py)", leftover))
    dialect = postgresql.dialect()
    ws = re.compile(r"\s+")
    out = ["# Database Schema Reference", "",
           "> **Generated from the SQLAlchemy models** (`app/models/`) — do not edit by hand. "
           "Regenerate with `python tools/generate_docs.py` after any model change.", "",
           f"**{len(tables)} tables.** Every tenant-owned table carries an indexed `school_id` foreign key — see "
           "[ARCHITECTURE.md](ARCHITECTURE.md) for how multi-tenancy is enforced.", ""]
    for title, names in groups:
        out += [f"## {title}", ""]
        for n in names:
            if n not in tables:
                continue
            t = tables[n]
            out += [f"### `{n}`", "", "| Column | Type | Null | Notes |", "|---|---|---|---|"]
            for col in t.columns:
                notes = []
                if col.primary_key:
                    notes.append("PK")
                for fk in col.foreign_keys:
                    notes.append(f"FK → `{fk.column.table.name}.{fk.column.name}` (ON DELETE {fk.ondelete or 'NO ACTION'})")
                if col.index:
                    notes.append("indexed")
                if col.unique:
                    notes.append("unique")
                try:
                    typ = col.type.compile(dialect=dialect)
                except Exception:
                    typ = str(col.type)
                out.append(f"| `{col.name}` | {typ} | {'yes' if col.nullable else 'no'} | {'; '.join(notes)} |")
            cons = []
            for c in t.constraints:
                cls, cname = c.__class__.__name__, c.name or ""
                if cls == "UniqueConstraint":
                    cons.append(f"- **UNIQUE** `{cname}` on ({', '.join(col.name for col in c.columns)})")
                elif cls == "CheckConstraint":
                    cons.append(f"- **CHECK** `{cname}`: `{ws.sub(' ', str(c.sqltext))}`")
            for ix in t.indexes:
                if ix.unique and ix.name and not ix.name.startswith("ix_"):
                    partial = ix.dialect_options["postgresql"].get("where") is not None
                    cons.append(f"- **UNIQUE INDEX** `{ix.name}` on ({', '.join(c.name for c in ix.columns)})" + (" — partial" if partial else ""))
            if cons:
                out += ["", "Constraints:", ""] + cons
            out.append("")
    return "\n".join(out), len(tables)


def routes_doc():
    init = open("app/__init__.py").read()
    reg_prefix = dict(re.findall(r'register_blueprint\((\w+)_bp, url_prefix="([^"]*)"\)', init))
    rows = []
    for f in sorted(glob.glob("app/routes/*.py")):
        src = open(f).read()
        name = Path(f).stem
        m = re.search(r'Blueprint\([^)]*url_prefix="([^"]*)"', src)
        prefix = m.group(1) if m else reg_prefix.get(name, "")
        pending = []
        for line in src.splitlines():
            s = line.strip()
            if s.startswith("@"):
                pending.append(s)
            elif s.startswith("def "):
                rt = next((p for p in pending if ".route(" in p), None)
                if rt:
                    path = re.search(r'route\("([^"]*)"', rt).group(1)
                    meth = re.search(r'methods=\[([^\]]*)\]', rt)
                    methods = re.sub(r'["\s]', "", meth.group(1)).replace(",", "/") if meth else "GET"
                    rr = next((re.search(r"role_required\((.*)\)", p).group(1).replace("UserRole.", "") for p in pending if "role_required" in p), None)
                    if rr is None:
                        rr = "any logged-in user" if any("login_required" in p for p in pending) else "public (no login)"
                    rows.append((name, (prefix + path) or "/", methods, rr))
                pending = []
            elif s:
                pending = []
    o = ["# Route Reference", "",
         "> **Generated from the route decorators** (`app/routes/`) — do not edit by hand. Regenerate with "
         "`python tools/generate_docs.py`. Roles shown are those allowed by `@role_required`; some routes add *ownership* "
         "rules on top (for example a teacher may only open their own salary record) — see [ROLES_AND_PERMISSIONS.md](ROLES_AND_PERMISSIONS.md).", "",
         f"**{len(rows)} routes**, plus `GET /health` (public, defined in `app/__init__.py`).", "",
         "| Module | URL | Methods | Roles allowed |", "|---|---|---|---|"]
    o += [f"| {r[0]} | `{r[1]}` | {r[2]} | {r[3]} |" for r in rows]
    return "\n".join(o) + "\n", rows


def sidebar_table():
    from app.utils.navigation import NAV_SECTIONS
    t = ["| Section | Menu item | Status | Visible to |", "|---|---|---|---|"]
    for sec in NAV_SECTIONS:
        for i in sec["items"]:
            status = "available" if i["endpoint"] else "*coming soon* (placeholder)"
            who = ", ".join(r.value.replace("_", " ").title() for r in i["roles"])
            t.append(f"| {sec['heading'] or '—'} | {i['label']} | {status} | {who} |")
    return "\n".join(t)


def main():
    schema, n_tables = schema_doc()
    Path("docs/DATABASE_SCHEMA.md").write_text(schema)
    routes, rows = routes_doc()
    Path("docs/ROUTES.md").write_text(routes)
    guide = Path("docs/USER_GUIDE.md")
    if guide.exists():
        text = guide.read_text()
        new = re.sub(r"(<!-- SIDEBAR:START -->).*?(<!-- SIDEBAR:END -->)",
                     lambda m: f"{m.group(1)}\n{sidebar_table()}\n{m.group(2)}", text, flags=re.S)
        guide.write_text(new)
    print(f"docs regenerated: {n_tables} tables, {len(rows)} routes")


if __name__ == "__main__":
    main()
