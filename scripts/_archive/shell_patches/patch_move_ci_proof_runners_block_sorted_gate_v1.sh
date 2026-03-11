#!/bin/bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_move_ci_proof_runners_block_sorted_gate_v1.py
