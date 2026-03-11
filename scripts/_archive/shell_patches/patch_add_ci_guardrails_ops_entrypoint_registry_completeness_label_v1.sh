#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py -u scripts/_patch_add_ci_guardrails_ops_entrypoint_registry_completeness_label_v1.py
