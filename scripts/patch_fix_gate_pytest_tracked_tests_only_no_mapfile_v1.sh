#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_fix_gate_pytest_tracked_tests_only_no_mapfile_v1.py
