from __future__ import annotations
from pathlib import Path

DOC_REF = "- Golden Path Output Contract (v1): docs/contracts/golden_path_output_contract_v1.md"
GATE_REF = "- Gate: scripts/gate_golden_path_output_contract_v1.sh"
MARKER = "<!-- GOLDEN_PATH_OUTPUT_CONTRACT_V1_REFS -->"

CANDIDATES = [
    Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md"),
    Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"),
    Path("docs/80_indices/ops/CI_Guardrails_Index_v1.1.md"),
]

target = next((p for p in CANDIDATES if p.exists()), None)
if target is None:
    raise SystemExit("No known ops index found (expected one of CI_Proof_Surface_Registry_v1.0.md or CI_Guardrails_Index_v1.*.md)")

txt = target.read_text(encoding="utf-8")
if MARKER in txt:
    raise SystemExit(0)

block = f"\n{MARKER}\n{DOC_REF}\n{GATE_REF}\n"
target.write_text(txt.rstrip() + block, encoding="utf-8")
