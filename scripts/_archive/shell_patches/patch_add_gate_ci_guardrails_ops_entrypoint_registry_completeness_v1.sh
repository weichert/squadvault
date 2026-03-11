#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py -u scripts/_patch_add_gate_ci_guardrails_ops_entrypoint_registry_completeness_v1.py
