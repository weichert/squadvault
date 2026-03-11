from __future__ import annotations

from pathlib import Path
import stat

REPO = Path(__file__).resolve().parents[1]
ORDER_TSV = REPO / "docs" / "80_indices" / "ops" / "CI_Guardrails_Ops_Cluster_Order_v1.tsv"
INDEX_DOC = REPO / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"
GATE = REPO / "scripts" / "gate_ci_guardrails_ops_cluster_canonical_v1.sh"

ORDER_TEXT = """scripts/gate_ci_guardrails_ops_cluster_canonical_v1.sh\tOps guardrails cluster canonical gate (v1)
scripts/gate_ci_guardrails_ops_entrypoint_exactness_v1.sh\tOps guardrails entrypoint exactness gate (v1)
scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh\tOps guardrails entrypoint parity gate (v1)
scripts/gate_ci_guardrails_ops_entrypoint_registry_completeness_v1.sh\tCI Guardrails Ops Entrypoint Registry Completeness (v1)
scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh\tCI Guardrails ops entrypoints section + TOC (v2)
scripts/gate_ci_guardrails_ops_renderer_shape_v1.sh\tOps guardrails entrypoint renderer shape gate (v1)
"""

GATE_TEXT = """#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

python3 - <<'PY_CHECK'
from pathlib import Path

prove = Path("scripts/prove_ci.sh")
order_tsv = Path("docs/80_indices/ops/CI_Guardrails_Ops_Cluster_Order_v1.tsv")

prove_text = prove.read_text(encoding="utf-8")
prove_lines = prove_text.splitlines()

expected_lines = []
for raw in order_tsv.read_text(encoding="utf-8").splitlines():
    raw = raw.strip()
    if not raw:
        continue
    path, _label = raw.split("\\t", 1)
    expected_lines.append(f"bash {path}")

positions = {}
for idx, line in enumerate(prove_lines):
    stripped = line.strip()
    if stripped in expected_lines:
        if stripped in positions:
            raise SystemExit(f"ERROR: duplicate Ops guardrails cluster line found: {stripped}")
        positions[stripped] = idx

missing = [line for line in expected_lines if line not in positions]
if missing:
    raise SystemExit(
        "ERROR: missing Ops guardrails cluster line(s) in scripts/prove_ci.sh:\\n- "
        + "\\n- ".join(missing)
    )

ordered_positions = [positions[line] for line in expected_lines]
start = min(ordered_positions)
end = max(ordered_positions) + 1
actual_block = [prove_lines[i].strip() for i in range(start, end)]

if actual_block != expected_lines:
    raise SystemExit(
        "ERROR: Ops guardrails cluster in scripts/prove_ci.sh is not canonical.\\n\\n"
        "Expected block:\\n- " + "\\n- ".join(expected_lines) + "\\n\\n"
        "Actual block:\\n- " + "\\n- ".join(actual_block)
    )

print("OK: CI Guardrails Ops cluster canonical (v1)")
PY_CHECK
"""

DOC_MARKER = "<!-- SV_CI_GUARDRAILS_OPS_CLUSTER_ORDER_SOURCE_v1 -->"
DOC_BULLET = "- Canonical Ops cluster order source: `docs/80_indices/ops/CI_Guardrails_Ops_Cluster_Order_v1.tsv`\n"
DOC_INSERT_AFTER = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->\n"

def write_if_changed(path: Path, text: str) -> bool:
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True

def ensure_executable(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

def patch_index(text: str) -> str:
    if DOC_MARKER in text:
        return text
    if DOC_INSERT_AFTER not in text:
        raise SystemExit("ERROR: could not find Ops bounded section begin marker in index doc")
    insert = DOC_INSERT_AFTER + DOC_MARKER + "\n" + DOC_BULLET
    return text.replace(DOC_INSERT_AFTER, insert, 1)

def main() -> int:
    changed = False

    if write_if_changed(ORDER_TSV, ORDER_TEXT):
        changed = True

    if write_if_changed(GATE, GATE_TEXT):
        ensure_executable(GATE)
        changed = True
    else:
        ensure_executable(GATE)

    index_text = INDEX_DOC.read_text(encoding="utf-8")
    new_index_text = patch_index(index_text)
    if new_index_text != index_text:
        INDEX_DOC.write_text(new_index_text, encoding="utf-8")
        changed = True

    if changed:
        print("OK: added single-source Ops cluster definition (v1)")
    else:
        print("OK: single-source Ops cluster definition already present (noop)")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
