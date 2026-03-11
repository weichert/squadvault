#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

python3 scripts/_patch_fix_ci_guardrail_registry_completeness_parse_v1.py