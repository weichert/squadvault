#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_add_ci_guardrails_desc_pytest_tracked_tests_only_v1.py
