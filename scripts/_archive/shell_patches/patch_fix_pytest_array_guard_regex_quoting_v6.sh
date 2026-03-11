#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_fix_pytest_array_guard_regex_quoting_v6.py
