from __future__ import annotations
from pathlib import Path
import subprocess
import datetime

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "docs" / "logs" / "CI_MILESTONES.md"

BEGIN = "<!-- SV_CI_MILESTONE_LOG_v1_BEGIN -->"
END = "<!-- SV_CI_MILESTONE_LOG_v1_END -->"

def _git(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, cwd=ROOT).decode().strip()

def main() -> int:
    commit = _git(["git", "rev-parse", "--short", "HEAD"])
    branch = _git(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    subject = _git(["git", "log", "-1", "--pretty=%s"])
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    entry = f"- {ts} — CI: prove_ci clean on {branch} @{commit} — {subject}\n"

    LOG.parent.mkdir(parents=True, exist_ok=True)

    if not LOG.exists():
        LOG.write_text(
            "# CI Milestones\n\n"
            f"{BEGIN}\n"
            f"{entry}"
            f"{END}\n",
            encoding="utf-8",
        )
        print("OK: created CI_MILESTONES.md with first entry.")
        return 0

    s = LOG.read_text(encoding="utf-8")

    if entry in s:
        print("OK: milestone entry already present (idempotent).")
        return 0

    if BEGIN not in s or END not in s:
        raise SystemExit("ERROR: bounded markers missing in CI_MILESTONES.md")

    LOG.write_text(s.replace(BEGIN, f"{BEGIN}\n{entry}", 1), encoding="utf-8")
    print("OK: appended CI milestone entry.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
