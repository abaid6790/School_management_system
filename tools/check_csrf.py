"""Fail if any POST form in the templates lacks a CSRF token.

CSRF protection is enabled app-wide, so a POST form without a token is rejected by the
browser flow with "400 Bad Request: The CSRF token is missing" — even though tests that
disable CSRF would still pass. Every POST form needs either `{{ form.hidden_tag() }}` or
`<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`.

Usage (project root):  python tools/check_csrf.py      (exit code 1 on any problem)
"""
import glob
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FORM = re.compile(r"<form\b[^>]*method=[\"']POST[\"'][^>]*>(.*?)</form>", re.S | re.I)
TOKEN = re.compile(r"csrf_token|hidden_tag")


def main():
    problems, total = [], 0
    for path in sorted(glob.glob(str(ROOT / "app" / "templates" / "**" / "*.html"), recursive=True)):
        text = Path(path).read_text()
        for match in FORM.finditer(text):
            total += 1
            if not TOKEN.search(match.group(0)):
                line = text[: match.start()].count("\n") + 1
                problems.append(f"{Path(path).relative_to(ROOT)}:{line}")
    print(f"{total} POST forms checked, {len(problems)} without a CSRF token")
    for p in problems:
        print("  missing token:", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
