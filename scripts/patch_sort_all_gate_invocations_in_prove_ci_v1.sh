#!/bin/bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_sort_all_gate_invocations_in_prove_ci_v1.py
