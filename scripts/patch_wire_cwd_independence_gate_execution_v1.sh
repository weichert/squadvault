#!/usr/bin/env bash
set -euo pipefail

repo_root="$(
  CDPATH= cd -- "$(dirname -- "$0")/.." && pwd
)"
cd "$repo_root"

./scripts/py scripts/_patch_wire_cwd_independence_gate_execution_v1.py
