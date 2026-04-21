#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
TARGET="$ROOT/scripts/prove_ci.sh"

if [ ! -f "$TARGET" ]; then
  echo "ERROR: missing target: scripts/prove_ci.sh" >&2
  exit 1
fi

cd "$ROOT"

./scripts/py - <<'PY'
from __future__ import annotations

from pathlib import Path
import re
import sys

TARGET = Path("scripts/prove_ci.sh")
text = TARGET.read_text(encoding="utf-8")

EXPECTED = [
    "bash scripts/gate_ci_guardrails_execution_order_lock_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_cluster_canonical_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_entrypoint_exactness_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_entrypoint_order_lock_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_entrypoint_registry_completeness_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_label_registry_parity_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_label_source_exactness_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_renderer_shape_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_topology_uniqueness_v1.sh",
    "bash scripts/gate_ci_guardrails_registry_authority_v1.sh",
    "bash scripts/gate_ci_guardrails_registry_completeness_v1.sh",
    "bash scripts/gate_ci_guardrails_surface_freeze_v1.sh",
]

pattern = re.compile(r"^bash scripts/gate_ci_guardrails_[A-Za-z0-9_]+\.sh$", re.M)
found = pattern.findall(text)

if not found:
    print("ERROR: no CI guardrail execution lines found in scripts/prove_ci.sh", file=sys.stderr)
    sys.exit(1)

if found != EXPECTED:
    print("ERROR: CI guardrail execution order mismatch", file=sys.stderr)
    print("EXPECTED:", file=sys.stderr)
    for line in EXPECTED:
        print(f"  {line}", file=sys.stderr)
    print("FOUND:", file=sys.stderr)
    for line in found:
        print(f"  {line}", file=sys.stderr)
    sys.exit(1)

block = "\n".join(EXPECTED)
if text.count(block) != 1:
    print("ERROR: canonical CI guardrail execution block must appear exactly once", file=sys.stderr)
    sys.exit(1)

print("OK: CI guardrail execution order is canonical")
PY
