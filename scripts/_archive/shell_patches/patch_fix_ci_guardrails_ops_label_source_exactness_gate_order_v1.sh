#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_fix_ci_guardrails_ops_label_source_exactness_gate_order_v1.py
