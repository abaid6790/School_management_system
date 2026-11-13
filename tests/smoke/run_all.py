"""Run every smoke test and report. Exit code is non-zero if any script fails.

    python tests/smoke/run_all.py            # all scripts, on temporary SQLite databases
    python tests/smoke/run_all.py ptm        # only scripts whose name contains "ptm"

To run the scripts that support it on PostgreSQL, point TEST_DB at a THROWAWAY database whose name
contains "test" (the scripts refuse anything else, because they create and drop tables):

    set TEST_DB=postgresql+psycopg2://postgres:password@localhost/sms_test
"""
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
only = sys.argv[1] if len(sys.argv) > 1 else ""
scripts = sorted(p for p in HERE.glob("*.py") if p.name != "run_all.py" and only in p.name)
env = dict(os.environ, PYTHONPATH=str(ROOT), NOTIFICATIONS_EMAIL_SYNC="True")
env.pop("DATABASE_URL", None)                       # the scripts must never see a real database URL

failed = 0
for script in scripts:
    result = subprocess.run([sys.executable, str(script)], env=env, cwd=str(ROOT), capture_output=True, text=True)
    output = result.stdout + result.stderr
    lines = [l for l in output.splitlines() if re.search(r"passed|accepted with CSRF", l)]
    summary = lines[-1].strip() if lines else "(no summary line — see output below)"
    status = "ok  " if result.returncode == 0 else "FAIL"
    print(f"{status} {script.stem:28s} {summary}")
    if result.returncode != 0:
        failed += 1
        for l in [l for l in output.splitlines() if l.startswith("FAIL") or "Traceback" in l or "Error" in l][:8]:
            print("       ", l)
print(f"\n{len(scripts) - failed}/{len(scripts)} scripts passed" if scripts else "no scripts matched")
sys.exit(1 if failed or not scripts else 0)
