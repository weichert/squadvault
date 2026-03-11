#!/bin/bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

./scripts/py scripts/_patch_fix_gate_prove_ci_structure_extractor_v1.py
