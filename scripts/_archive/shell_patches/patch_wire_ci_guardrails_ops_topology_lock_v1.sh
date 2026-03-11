#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
python3 scripts/_patch_wire_ci_guardrails_ops_topology_lock_v1.py
