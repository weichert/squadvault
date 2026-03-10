#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_add_gate_ci_guardrails_ops_cluster_canonical_v1.py
