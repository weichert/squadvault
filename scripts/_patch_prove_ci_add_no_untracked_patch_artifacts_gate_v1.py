from __future__ import annotations

from pathlib import Path
import re
import sys

PROVE = Path("scripts/prove_ci.sh")

BEGIN = "# SV_GATE: no_untracked_patch_artifacts (v1) begin"
END = "# SV_GATE: no_untracked_patch_artifacts (v1) end"

BLOCK = (
    f"{BEGIN}\n"
    f"bash scripts/gate_no_untracked_patch_artifacts_v1.sh\n"
    f"{END}\n"
)

def main() -> int:
    if not PROVE.exists():
        print(f"ERROR: missing {PROVE}", file=sys.stderr)
        return 2

    text = PROVE.read_text(encoding="utf-8")

    if BEGIN in text and END in text:
        # Already patched (idempotent)
        return 0

    # Prefer inserting early, just before the repo cleanliness check that uses git status porcelain
    # Stable insertion points (first match wins):
    #  1) A line that calls `git status --porcelain=v1` (common repo cleanliness precondition)
    #  2) A line that prints "Repo cleanliness" (if present)
    candidates: list[re.Pattern[str]] = [
        re.compile(r"^.*git status --porcelain=v1.*$", re.M),
        re.compile(r"^.*Repo cleanliness.*$", re.M),
    ]

    insert_at = None
    for pat in candidates:
        m = pat.search(text)
        if m:
            insert_at = m.start()
            break

    if insert_at is None:
        print(
            "ERROR: Could not find a stable insertion point in scripts/prove_ci.sh.\n"
            "Expected to find a repo cleanliness check (e.g. `git status --porcelain=v1`) or a 'Repo cleanliness' marker.\n"
            "Refusing to patch to avoid silent mis-wiring.",
            file=sys.stderr,
        )
        return 3

    new_text = text[:insert_at] + BLOCK + "\n" + text[insert_at:]
    PROVE.write_text(new_text, encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
