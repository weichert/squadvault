from __future__ import annotations
from pathlib import Path

CANDIDATES = [
    Path("docs/80_indices/ops/CI_Guardrails_Index_v1.1.md"),
    Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"),
]
target = next((p for p in CANDIDATES if p.exists()), None)
if target is None:
    raise SystemExit("No CI Guardrails ops index found (expected v1.0 or v1.1).")

MARKER = "<!-- SV_RIVALRY_CHRONICLE_OUTPUT_CONTRACT_V1 -->"
DOC = "- docs/contracts/rivalry_chronicle_output_contract_v1.md — Rivalry Chronicle Output Contract (v1)"
BULLET = "- scripts/gate_rivalry_chronicle_output_contract_v1.sh — Enforce Rivalry Chronicle export conforms to output contract (v1)"

txt = target.read_text(encoding="utf-8")
if MARKER in txt:
    raise SystemExit(0)

block = f"\n{MARKER}\n{DOC}\n{BULLET}\n"
target.write_text(txt.rstrip() + block, encoding="utf-8")
