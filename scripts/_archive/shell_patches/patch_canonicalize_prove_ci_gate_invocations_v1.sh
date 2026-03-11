#!/bin/bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_canonicalize_prove_ci_gate_invocations_v1.py
