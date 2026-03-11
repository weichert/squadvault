#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_fix_pytest_target_parser_allow_array_expansions_v1.py
