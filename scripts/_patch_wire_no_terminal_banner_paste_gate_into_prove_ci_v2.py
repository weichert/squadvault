from __future__ import annotations

from pathlib import Path
import sys

TARGET = Path("scripts/prove_ci.sh")
MARK = "gate_no_terminal_banner_paste_v1.sh"
SNIP = "\n==> Gate: no pasted terminal banners in scripts/\nbash scripts/gate_no_terminal_banner_paste_v1.sh\n"

ANCHORS = [
    # Prefer inserting near other early “text/static” gates:
    "bash scripts/gate_no_bare_chevron_markers_v1.sh",
    "bash scripts/gate_no_xtrace_v1.sh",
    "bash scripts/gate_no_pytest_directory_invocation_v",
    "bash scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh",
]

def main() -> int:
    if not TARGET.exists():
        raise SystemExit(f"REFUSE: missing target: {TARGET}")

    text = TARGET.read_text(encoding="utf-8")
    if MARK in text:
        return 0

    anchor_idx = -1
    anchor_used = None
    for a in ANCHORS:
        anchor_idx = text.find(a)
        if anchor_idx >= 0:
            anchor_used = a
            break

    if anchor_idx < 0 or anchor_used is None:
        raise SystemExit(f"REFUSE: cannot find any anchor in {TARGET}. Tried: {ANCHORS}")

    lines = text.splitlines(keepends=True)

    # Locate the line containing the anchor, then insert after the next blank line (or right after the line).
    anchor_line_idx = None
    for i, line in enumerate(lines):
        if anchor_used in line:
            anchor_line_idx = i
            break
    if anchor_line_idx is None:
        raise SystemExit("REFUSE: anchor line scan failed")

    insert_at = None
    for j in range(anchor_line_idx, len(lines)):
        if lines[j].strip() == "":
            insert_at = j + 1
            break
    if insert_at is None:
        insert_at = anchor_line_idx + 1

    new_text = "".join(lines[:insert_at] + [SNIP] + lines[insert_at:])
    TARGET.write_text(new_text, encoding="utf-8")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
