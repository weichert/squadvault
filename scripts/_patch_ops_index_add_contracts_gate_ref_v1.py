from __future__ import annotations
from pathlib import Path

CANDIDATES = [
    Path("docs/80_indices/ops/CI_Guardrails_Index_v1.1.md"),
    Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"),
]

target = next((p for p in CANDIDATES if p.exists()), None)
if target is None:
    raise SystemExit("No CI Guardrails ops index found (expected v1.0 or v1.1).")

MARKER = "<!-- SV_CONTRACTS_INDEX_DISCOVERABILITY_V1 -->"
BULLET = "- scripts/gate_contracts_index_discoverability_v1.sh — Enforce docs/contracts/README.md indexes all versioned contracts (v1)"
DOC = "- docs/contracts/README.md — Contracts Index (canonical)"

txt = target.read_text(encoding="utf-8")
if MARKER in txt:
    raise SystemExit(0)

block = f"\n{MARKER}\n{DOC}\n{BULLET}\n"
target.write_text(txt.rstrip() + block, encoding="utf-8")
