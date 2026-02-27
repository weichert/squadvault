#!/bin/bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_prove_ci_remove_rivalry_chronicle_gate_v1.py
