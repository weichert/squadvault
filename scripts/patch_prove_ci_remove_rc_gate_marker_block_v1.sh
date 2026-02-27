#!/bin/bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_prove_ci_remove_rc_gate_marker_block_v1.py
