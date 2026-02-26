#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_fix_gate_pytest_array_guard_allow_escaped_quotes_v12.py
