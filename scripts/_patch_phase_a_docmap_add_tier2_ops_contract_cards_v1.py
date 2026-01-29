from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC = REPO_ROOT / "docs/canonical/Documentation_Map_and_Canonical_References.md"

SENTINEL = "<!-- SV_PHASE_A_TIER2_OPS_CONTRACT_CARDS_V1 -->"

BLOCK = "\n".join([
    SENTINEL,
    "",
    "## Tier 2 — Ops Contract Cards (Canonical)",
    "",
    "_Phase A Canonical Promotion: Tier-2 operational contract cards promoted to CANONICAL (v1.0)._",
    "",
    "- **Tone Engine (v1.0)** — `docs/30_contract_cards/ops/TONE_ENGINE_Contract_Card_v1.0.docx`",
    "- **Approval Authority (v1.0)** — `docs/30_contract_cards/ops/APPROVAL_AUTHORITY_Contract_Card_v1.0.docx`",
    "- **Version Presentation & Navigation (v1.0)** — `docs/30_contract_cards/ops/VERSION_PRESENTATION_NAVIGATION_Contract_Card_v1.0.docx`",
    "- **EAL Calibration (v1.0)** — `docs/30_contract_cards/ops/EAL_CALIBRATION_Contract_Card_v1.0.docx`",
    "- **Contract Validation Strategy (v1.0)** — `docs/30_contract_cards/ops/CONTRACT_VALIDATION_STRATEGY_Contract_Card_v1.0.docx`",
    "",
])

def main() -> int:
    if not DOC.exists():
        print(f"ERROR: missing docmap: {DOC}", file=sys.stderr)
        return 2

    txt = DOC.read_text(encoding="utf-8")

    if SENTINEL in txt:
        print(f"SKIP: sentinel present (already patched): {DOC}")
        return 0

    lower = txt.lower()
    anchor_idx = lower.find("tier 2")

    if anchor_idx == -1:
        DOC.write_text(txt.rstrip() + "\n\n" + BLOCK, encoding="utf-8")
        print(f"OK: appended Tier-2 ops block at end (no Tier 2 anchor found): {DOC}")
        return 0

    # insert at start of the line containing "tier 2"
    line_start = txt.rfind("\n", 0, anchor_idx)
    insert_at = 0 if line_start == -1 else (line_start + 1)

    txt2 = txt[:insert_at] + BLOCK + "\n" + txt[insert_at:]
    DOC.write_text(txt2, encoding="utf-8")
    print(f"OK: inserted Tier-2 ops block near anchor: {DOC}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
