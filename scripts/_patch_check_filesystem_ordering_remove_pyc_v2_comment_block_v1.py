from __future__ import annotations

import re
from pathlib import Path

TARGET = Path("scripts/check_filesystem_ordering_determinism.sh")

KEEP_SENTINEL = "SV_PATCH: fs-order scan ignore __pycache__/ and *.pyc (portable v3)"
DROP_SENTINEL = "SV_PATCH: fs-order scan ignore __pycache__/ and *.pyc (v2)"

# Remove:
#   # SV_PATCH: ... (v2)
#   # ...
#   # /SV_PATCH
# plus trailing blank lines (at most a couple)
DROP_RE = re.compile(
    r"\n# "
    + re.escape(DROP_SENTINEL)
    + r"\n(?:#.*\n)*# /SV_PATCH\n(?:\n{1,3})?",
    re.M,
)

def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")

def main() -> None:
    if not TARGET.exists():
        die(f"missing target: {TARGET}")

    txt = TARGET.read_text(encoding="utf-8")

    # Fail-closed: ensure portable v3 is present (we are *not* removing the actual behavior).
    if KEEP_SENTINEL not in txt:
        die(f"refusing to patch: expected keep-sentinel not found: {KEEP_SENTINEL}")

    # If v2 block already gone, be idempotent.
    if DROP_SENTINEL not in txt:
        print("OK: v2 comment block already absent; nothing to do")
        return

    new_txt, n = DROP_RE.subn("\n", txt, count=1)
    if n != 1:
        die(f"refusing to patch: expected to remove exactly 1 v2 block; removed={n}")

    # Safety: confirm v3 block still present post-patch.
    if KEEP_SENTINEL not in new_txt:
        die("internal: keep-sentinel disappeared after patch (unexpected)")

    TARGET.write_text(new_txt, encoding="utf-8")
    print("OK: removed redundant v2 SV_PATCH comment block (kept portable v3)")

if __name__ == "__main__":
    main()
