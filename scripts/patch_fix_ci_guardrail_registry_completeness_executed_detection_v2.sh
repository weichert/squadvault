#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

python3 scripts/_patch_fix_ci_guardrail_registry_completeness_executed_detection_v2.py
