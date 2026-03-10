#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py -u scripts/_patch_render_ci_guardrails_ops_entrypoints_block_fail_closed_registry_v1.py
