from __future__ import annotations

from pathlib import Path
import sys

TARGET = Path("scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh")
MARK = "gate_patch_idempotence_allowlist_canonical_v1.sh"

SNIPPET = """\n# gate_patch_idempotence_allowlist_canonical_v1\necho "==> Gate: idempotence allowlist canonical"\nbash scripts/gate_patch_idempotence_allowlist_canonical_v1.sh\n"""

def main() -> int:
    if not TARGET.exists():
        raise SystemExit(f"REFUSE: missing target: {TARGET}")

    text = TARGET.read_text(encoding="utf-8")
    if MARK in text:
        return 0

    anchor = 'if [[ ! -f "${ALLOWLIST}" ]]; then'
    if anchor not in text:
        raise SystemExit(f"REFUSE: cannot find anchor in {TARGET}: {anchor}")

    lines = text.splitlines(keepends=True)

    # Insert right after the allowlist existence check block (after the first 'fi' following the anchor).
    anchor_i = None
    for i, line in enumerate(lines):
        if anchor in line:
            anchor_i = i
            break
    if anchor_i is None:
        raise SystemExit("REFUSE: unexpected: anchor scan failed")

    fi_i = None
    for j in range(anchor_i, len(lines)):
        if lines[j].strip() == "fi":
            fi_i = j
            break
    if fi_i is None:
        raise SystemExit("REFUSE: cannot find closing 'fi' for allowlist existence check")

    insert_at = fi_i + 1
    new_text = "".join(lines[:insert_at] + [SNIPPET] + lines[insert_at:])
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
