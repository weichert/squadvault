from __future__ import annotations

from pathlib import Path

ADDENDUM = Path("docs/addenda/CI_Docs_Hardening_Freeze_v1.0.md")
DOCMAP = Path("docs/canonical/Documentation_Map_and_Canonical_References.md")

FREEZE_DOC = """# SquadVault — CI + Docs Hardening Freeze (v1.0)

Status: **FROZEN (ops)**

This addendum marks the completion of a hardening pass that enforces:
- CI cleanliness (no working-tree mutation)
- Deterministic environment envelope
- Filesystem ordering determinism gate
- Time & timestamp determinism gate
- Docs housekeeping audit (deterministic scan; structured outputs)

## Policy (frozen)

All changes to `docs/` or CI guardrails must be implemented through:
- A **versioned patcher** (`scripts/_patch_*.py`), and
- A **versioned wrapper** (`scripts/patch_*.sh`),
so that changes are auditable, repeatable, and CI-safe.

Inline/manual edits are permitted only for emergency repair, and must be followed by a patcher+wrapper retrofit.
"""

LINK_SNIPPET = (
    "- **CI + Docs hardening freeze:**  \n"
    "  → [CI_Docs_Hardening_Freeze_v1.0.md](../addenda/CI_Docs_Hardening_Freeze_v1.0.md)\n"
)

def ensure_addendum() -> None:
    if ADDENDUM.exists():
        return
    ADDENDUM.parent.mkdir(parents=True, exist_ok=True)
    ADDENDUM.write_text(FREEZE_DOC, encoding="utf-8")

def ensure_docmap_link() -> None:
    if not DOCMAP.exists():
        raise SystemExit(f"ERROR: missing canonical docmap: {DOCMAP}")

    s = DOCMAP.read_text(encoding="utf-8")
    if "CI_Docs_Hardening_Freeze_v1.0.md" in s:
        return

    # Heuristic insert:
    # Prefer inserting near other addenda/canon pointers; fallback to append at end.
    anchor_candidates = [
        "## Addenda",
        "## Canonical Addenda",
        "## Notes",
    ]
    for a in anchor_candidates:
        if a in s:
            parts = s.split(a, 1)
            head, tail = parts[0], parts[1]
            # insert immediately after header line
            new_tail = a + "\n\n" + LINK_SNIPPET + "\n" + tail.lstrip("\n")
            DOCMAP.write_text(head + new_tail, encoding="utf-8")
            return

    # fallback: append
    DOCMAP.write_text(s.rstrip() + "\n\n## Addenda\n\n" + LINK_SNIPPET, encoding="utf-8")

def main() -> None:
    ensure_addendum()
    ensure_docmap_link()
    print("OK: created addendum + linked from canonical docmap")

if __name__ == "__main__":
    main()
