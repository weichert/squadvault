#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_fix_pytest_array_guard_before_all_tests_anchors_v5_1.py
