from __future__ import annotations

from pathlib import Path

GATE = Path("scripts/gate_contract_linkage_v1.sh")

POINTER_LINE = "# Policy: docs/contracts/Contract_Markers_v1.0.md\n"

def main() -> int:
    if not GATE.exists():
        raise SystemExit(f"ERR: missing gate: {GATE}")

    txt = GATE.read_text(encoding="utf-8")
    if POINTER_LINE.strip() in txt:
        return 0  # idempotent

    lines = txt.splitlines(True)

    # Insert after the "Contract Linkage Gate (v1)" header comment if present.
    insert_at = None
    for i, line in enumerate(lines):
        if line.strip() == "# Contract Linkage Gate (v1)":
            insert_at = i + 1
            break

    if insert_at is None:
        # Fallback: insert after shebang + set -euo if structure is unexpected.
        insert_at = 0
        for i, line in enumerate(lines[:20]):
            if line.startswith("set -euo pipefail"):
                insert_at = i + 1
                break

    # Ensure a blank line separation if we're inserting into a tight block.
    # We’ll place pointer immediately after the header line.
    lines.insert(insert_at, POINTER_LINE)

    GATE.write_text("".join(lines), encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
