#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
"$REPO_ROOT/scripts/py" "$REPO_ROOT/scripts/_patch_add_gate_ci_guardrails_ops_label_registry_parity_v1.py"
