#!/bin/bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

./scripts/py scripts/_patch_wire_prove_ci_structure_canonical_gate_v1.py
