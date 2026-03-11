#!/bin/bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

./scripts/py scripts/_patch_sort_ci_proof_runners_block_entries_v1.py
