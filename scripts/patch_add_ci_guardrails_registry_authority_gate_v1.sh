#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
python3 scripts/_patch_add_ci_guardrails_registry_authority_gate_v1.py
