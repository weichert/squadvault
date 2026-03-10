#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_fix_ci_guardrails_ops_renderer_shape_gate_canonical_slot_v1.py
