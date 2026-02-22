#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_canonicalize_ci_guardrails_index_pytest_tracked_tests_only_v1.py
