#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_fix_pytest_array_guard_unbound_t_v1.py
