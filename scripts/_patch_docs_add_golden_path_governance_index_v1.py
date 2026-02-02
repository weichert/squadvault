from __future__ import annotations

from pathlib import Path

TARGET = Path("docs/80_indices/ops/Golden_Path_Governance_Index_v1.0.md")

CONTENT = """\
# Golden Path — Governance Index (v1.0)

Status: CANONICAL-ADJACENT — INDEX (Operator Discoverability)

This index exists to make Golden Path governance artifacts easy to find.

## Canonical Freeze

- **Golden Path — Production Freeze (v1.0)**  
  `docs/canonical/Golden_Path_Production_Freeze_v1.0.md`

## Operational Guardrails

- **Golden Path — Pytest Pinning (v1.0)**  
  `docs/80_indices/ops/Golden_Path_Pytest_Pinning_v1.0.md`

## Canonical Map Pointer

- **Documentation Map & Canonical References (v1.0)**  
  `docs/canonical/Documentation_Map_and_Canonical_References.md`
"""

def main() -> None:
    if TARGET.exists():
        raise SystemExit(f"ERROR: target already exists (refusing to overwrite): {TARGET}")

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(CONTENT, encoding="utf-8")
    print(f"OK: created {TARGET}")

if __name__ == "__main__":
    main()
