#!/bin/bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

./scripts/py scripts/_patch_fix_ci_proof_runners_block_sorted_description_v1.py
