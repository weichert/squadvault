from __future__ import annotations

from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]

PROVE_CI = REPO / "scripts" / "prove_ci.sh"
INDEX_MD = REPO / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"
LABELS_TSV = REPO / "docs" / "80_indices" / "ops" / "CI_Guardrail_Entrypoint_Labels_v1.tsv"

NEW_GATE = "scripts/gate_ci_guardrails_registry_authority_v1.sh"
NEW_LABEL = "CI guardrails registry authority gate (v1)"

PROVE_ANCHOR = "bash scripts/gate_ci_guardrails_ops_topology_uniqueness_v1.sh\n"
PROVE_INSERT = PROVE_ANCHOR + f"bash {NEW_GATE}\n"

INDEX_ANCHOR = "- scripts/gate_ci_guardrails_ops_topology_uniqueness_v1.sh — Ops guardrails topology uniqueness gate (v1)\n"
INDEX_INSERT = INDEX_ANCHOR + f"- {NEW_GATE} — {NEW_LABEL}\n"

TSV_ANCHOR = "scripts/gate_ci_guardrails_ops_topology_uniqueness_v1.sh\tOps guardrails topology uniqueness gate (v1)\n"
TSV_INSERT = TSV_ANCHOR + f"{NEW_GATE}\t{NEW_LABEL}\n"


def patch_once(path: Path, anchor: str, replacement: str, needle: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if needle in text:
        return False
    if anchor not in text:
        raise SystemExit(f"ERROR: anchor not found in {path}")
    path.write_text(text.replace(anchor, replacement, 1), encoding="utf-8")
    return True


changed = False
changed |= patch_once(PROVE_CI, PROVE_ANCHOR, PROVE_INSERT, f"bash {NEW_GATE}\n")
changed |= patch_once(INDEX_MD, INDEX_ANCHOR, INDEX_INSERT, f"- {NEW_GATE} — {NEW_LABEL}\n")
changed |= patch_once(LABELS_TSV, TSV_ANCHOR, TSV_INSERT, f"{NEW_GATE}\t{NEW_LABEL}\n")

print("OK: applied Phase 7.7 registry authority gate patch." if changed else "OK: Phase 7.7 registry authority gate patch already present (noop).")
