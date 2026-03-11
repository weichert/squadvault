#!/bin/bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_move_prove_ci_structure_gate_after_registry_excludes_v1.py
