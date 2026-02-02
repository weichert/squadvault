#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = REPO_ROOT / "docs/canonical/Documentation_Map_and_Canonical_References.md"

DOC = """# SquadVault — Documentation Map & Canonical References

Version: v1.0  
Status: CANONICAL  
Authority Tier: Tier 0 — Meta Governance  
Applies To: All canonical docs and operator governance artifacts  

---

## Tier 0 — Meta Governance

- Documentation Map & Canonical References (v1.0)

---

## Tier 1 — Constitutions and Charters

- SquadVault — Canonical Operating Constitution (v1.0)

---

## Tier 2 — Contract Cards (Active Governance)

- Ops Shim & CWD Independence Contract (v1.0)

---

## Tier 3 — Runbooks and Operator Guides

- (Reserved)

---

## Tier 4 — Specs, Schemas, and Technical References

- (Reserved)

---

## Notes

- Canonical documents live under `docs/canonical/`.
- Tier placement governs precedence. Higher tiers override lower tiers.
"""

def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)

def write_exact(path: Path, content: str) -> bool:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"OK: created {path.relative_to(REPO_ROOT)}")
        return True

    existing = path.read_text(encoding="utf-8")
    if existing == content:
        print(f"OK: {path.relative_to(REPO_ROOT)} already matches minimal canonical v1.0; no changes.")
        return False

    die(
        f"{path.relative_to(REPO_ROOT)} exists but does not match minimal canonical v1.0 content.\n"
        f"Refusing to overwrite. Resolve manually or bump version."
    )

def main() -> int:
    changed = write_exact(MAP_PATH, DOC)
    print("OK: documentation map lock applied." if changed else "OK: no changes needed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
