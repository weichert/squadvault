from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "patch_add_ci_milestone_log_v1.sh"

MARK_BEGIN = "# <!-- SV_CI_MILESTONE_LATEST_WIRED_v1_BEGIN -->"
MARK_END   = "# <!-- SV_CI_MILESTONE_LATEST_WIRED_v1_END -->"

BLOCK = "\n".join(
    [
        MARK_BEGIN,
        "",
        "# Also refresh the 'Latest' section so the log stays navigable.",
        "./scripts/py scripts/_patch_ci_milestone_log_add_latest_section_v1.py",
        "",
        MARK_END,
        "",
    ]
)

def main() -> int:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target wrapper: {TARGET}")

    s = TARGET.read_text(encoding="utf-8")

    if MARK_BEGIN in s and MARK_END in s:
        print("OK: latest wiring already present (idempotent).")
        return 0

    # Anchor: after the existing append patcher invocation.
    # Expect a line like: ./scripts/py scripts/_patch_add_ci_milestone_log_v1.py
    anchor = r"(^\s*\./scripts/py\s+scripts/_patch_add_ci_milestone_log_v1\.py\s*$)"
    m = re.search(anchor, s, flags=re.MULTILINE)
    if not m:
        raise SystemExit("ERROR: could not find _patch_add_ci_milestone_log_v1.py invocation in wrapper")

    insert_at = m.end(1)
    updated = s[:insert_at] + "\n" + BLOCK + s[insert_at:]

    TARGET.write_text(updated, encoding="utf-8")
    print("OK: wired latest refresh into patch_add_ci_milestone_log_v1.sh")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
