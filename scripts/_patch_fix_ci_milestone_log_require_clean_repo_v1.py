from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "_patch_add_ci_milestone_log_v1.py"

MARK_BEGIN = "# <!-- SV_CI_MILESTONE_LOG_REQUIRE_CLEAN_REPO_v1_BEGIN -->"
MARK_END   = "# <!-- SV_CI_MILESTONE_LOG_REQUIRE_CLEAN_REPO_v1_END -->"

INSERT_BLOCK = "\n".join(
    [
        MARK_BEGIN,
        "    # Safety: refuse to write a milestone if the repo is dirty.",
        "    status = _git([\"git\", \"status\", \"--porcelain=v1\"])",
        "    if status:",
        "        raise SystemExit(\"ERROR: repo is dirty; refuse to write CI milestone.\")",
        MARK_END,
        "",
    ]
)

def main() -> int:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    s = TARGET.read_text(encoding="utf-8")

    # 1) Fix the stray '>' bug if it exists (safe + idempotent).
    #    Example bad line: entry = f"...\n"> 
    s2 = re.sub(r'(entry\s*=\s*f".*\\n")\s*>\s*$', r"\1", s, flags=re.MULTILINE)

    # 2) Ensure the "require clean repo" guard exists exactly once.
    if MARK_BEGIN in s2 and MARK_END in s2:
        TARGET.write_text(s2, encoding="utf-8")
        print("OK: require-clean guard already present (idempotent).")
        return 0

    # Insert right after the ts=... line (best anchor across versions).
    # We match the first occurrence only.
    pat = r"(^\s*ts\s*=\s*datetime\.datetime\.utcnow\(\)\.strftime\([^\n]*\)\s*$)"
    m = re.search(pat, s2, flags=re.MULTILINE)
    if not m:
        raise SystemExit("ERROR: could not find ts=... anchor in _patch_add_ci_milestone_log_v1.py")

    insert_at = m.end(1)
    updated = s2[:insert_at] + "\n" + INSERT_BLOCK + s2[insert_at+1:] if s2[insert_at:insert_at+1] == "\n" else s2[:insert_at] + "\n" + INSERT_BLOCK + s2[insert_at:]

    TARGET.write_text(updated, encoding="utf-8")
    print("OK: inserted require-clean guard into CI milestone patcher.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
