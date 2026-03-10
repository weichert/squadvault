#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

python3 - <<'PY_CHECK'
from pathlib import Path

prove = Path("scripts/prove_ci.sh")
text = prove.read_text(encoding="utf-8")

expected_lines = [
    "bash scripts/gate_ci_guardrails_ops_cluster_canonical_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_entrypoint_exactness_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_entrypoint_registry_completeness_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh",
    "bash scripts/gate_ci_guardrails_ops_label_source_exactness_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_renderer_shape_v1.sh",
]

lines = text.splitlines()
positions = {}
for idx, line in enumerate(lines):
    stripped = line.strip()
    if stripped in expected_lines:
        if stripped in positions:
            raise SystemExit(f"ERROR: duplicate Ops guardrails cluster line found: {stripped}")
        positions[stripped] = idx

missing = [line for line in expected_lines if line not in positions]
if missing:
    raise SystemExit(
        "ERROR: missing Ops guardrails cluster line(s) in scripts/prove_ci.sh:\n- "
        + "\n- ".join(missing)
    )

ordered_positions = [positions[line] for line in expected_lines]
start = min(ordered_positions)
end = max(ordered_positions) + 1
actual_block = [lines[i].strip() for i in range(start, end)]

if actual_block != expected_lines:
    raise SystemExit(
        "ERROR: Ops guardrails cluster in scripts/prove_ci.sh is not canonical.\n\n"
        "Expected block:\n- " + "\n- ".join(expected_lines) + "\n\n"
        "Actual block:\n- " + "\n- ".join(actual_block)
    )

print("OK: CI Guardrails Ops cluster canonical (v1)")
PY_CHECK
