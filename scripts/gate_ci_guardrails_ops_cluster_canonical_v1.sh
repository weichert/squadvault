#!/usr/bin/env bash
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
    path, _label = raw.split("\t", 1)
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
        "ERROR: missing Ops guardrails cluster line(s) in scripts/prove_ci.sh:\n- "
        + "\n- ".join(missing)
    )

ordered_positions = [positions[line] for line in expected_lines]
start = min(ordered_positions)
end = max(ordered_positions) + 1
actual_block = [prove_lines[i].strip() for i in range(start, end)]

if actual_block != expected_lines:
    raise SystemExit(
        "ERROR: Ops guardrails cluster in scripts/prove_ci.sh is not canonical.\n\n"
        "Expected block:\n- " + "\n- ".join(expected_lines) + "\n\n"
        "Actual block:\n- " + "\n- ".join(actual_block)
    )

print("OK: CI Guardrails Ops cluster canonical (v1)")
PY_CHECK
