from __future__ import annotations

from pathlib import Path

DOC = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

MARKER = "<!-- SV_CI_PROOF_SURFACE_REGISTRY: v1 -->"
BULLET = "- scripts/check_ci_proof_surface_matches_registry_v1.sh — CI Proof Surface Registry Gate (canonical)"

# Stable anchor line from your diff context
ANCHOR = "- scripts/gate_docs_mutation_guardrail_v2.sh — Docs Mutation Guardrail Gate (canonical)"

# Bounded block we must not place the registry marker inside/after
BANNER_BEGIN = "<!-- SV_TERMINAL_BANNER_GATE_ENTRY_v1_BEGIN -->"
BANNER_END = "<!-- SV_TERMINAL_BANNER_GATE_ENTRY_v1_END -->"

def main() -> None:
    if not DOC.exists():
        raise SystemExit(f"ERROR: missing doc: {DOC}")

    lines = DOC.read_text(encoding="utf-8").splitlines(keepends=False)

    # Locate banner block boundaries (for safety checks)
    banner_begin_idxs = [i for i, ln in enumerate(lines) if ln.strip() == BANNER_BEGIN]
    banner_end_idxs = [i for i, ln in enumerate(lines) if ln.strip() == BANNER_END]
    if len(banner_begin_idxs) != 1 or len(banner_end_idxs) != 1:
        raise SystemExit("ERROR: expected exactly one terminal banner bounded block begin/end markers.")
    banner_begin = banner_begin_idxs[0]
    banner_end = banner_end_idxs[0]
    if banner_end <= banner_begin:
        raise SystemExit("ERROR: terminal banner block markers are out of order.")

    # Find all existing occurrences of marker/bullet
    marker_idxs = [i for i, ln in enumerate(lines) if ln.strip() == MARKER]
    bullet_idxs = [i for i, ln in enumerate(lines) if ln.strip() == BULLET]

    # If marker or bullet appear multiple times, refuse (too risky to auto-dedupe blindly)
    if len(marker_idxs) > 1 or len(bullet_idxs) > 1:
        raise SystemExit(
            "ERROR: registry marker/bullet appears multiple times; refusing to auto-dedupe.\n"
            f"marker_idxs={[i+1 for i in marker_idxs]} bullet_idxs={[i+1 for i in bullet_idxs]}"
        )

    # Remove single existing marker/bullet if present (we will reinsert canonically).
    # Also remove if present inside/after banner block.
    changed = False
    if marker_idxs:
        idx = marker_idxs[0]
        del lines[idx]
        changed = True
        # Adjust subsequent indices automatically by re-scan
        # If the bullet was immediately after, we'll remove it below by content match.
    # Remove bullet line wherever it currently is (single occurrence).
    # Re-scan because prior delete may have shifted.
    bullet_idxs = [i for i, ln in enumerate(lines) if ln.strip() == BULLET]
    if bullet_idxs:
        del lines[bullet_idxs[0]]
        changed = True

    # Find anchor insertion point
    anchor_idxs = [i for i, ln in enumerate(lines) if ln.strip() == ANCHOR]
    if len(anchor_idxs) != 1:
        raise SystemExit(f"ERROR: expected exactly one anchor line in doc:\n{ANCHOR}")
    anchor_i = anchor_idxs[0]

    # Insert marker+bullet immediately after anchor line (stable, outside banner block).
    insert_at = anchor_i + 1
    to_insert = [MARKER, BULLET]

    # Prevent inserting inside banner block: if anchor is above banner begin, we're fine.
    if banner_begin <= insert_at <= banner_end:
        raise SystemExit("ERROR: computed insertion point is inside terminal banner bounded block; refusing.")

    # If the doc already has the pair exactly in the right spot, changed should be False.
    # But we removed earlier if found; so check for canonical placement in original?
    # Simpler: compute the desired final lines and compare to original bytes to avoid churn.
    lines2 = lines[:insert_at] + to_insert + lines[insert_at:]

    # Safety: ensure we did not place marker/bullet after banner end (the buggy behavior we saw).
    banner_end_new = [i for i, ln in enumerate(lines2) if ln.strip() == BANNER_END][0]
    for i, ln in enumerate(lines2):
        if ln.strip() in (MARKER, BULLET) and i > banner_end_new:
            raise SystemExit("ERROR: registry marker/bullet ended up after banner block end; refusing.")

    new_text = "\n".join(lines2) + "\n"
    old_text = DOC.read_text(encoding="utf-8")

    if old_text == new_text:
        print("OK: ops index already canonical for proof surface registry block (v3 idempotent).")
        return

    DOC.write_text(new_text, encoding="utf-8")
    print("OK: wrote canonical proof surface registry marker+bullet location (v3).")

if __name__ == "__main__":
    main()
