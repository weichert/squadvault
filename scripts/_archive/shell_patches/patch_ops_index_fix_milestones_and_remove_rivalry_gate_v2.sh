#!/bin/bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_ops_index_fix_milestones_and_remove_rivalry_gate_v2.py
