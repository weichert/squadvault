#!/bin/bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_move_no_untracked_patch_artifacts_gate_v2.py
