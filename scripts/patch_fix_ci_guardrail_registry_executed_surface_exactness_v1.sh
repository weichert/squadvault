#!/usr/bin/env bash
set -euo pipefail

repo_root="$(
  CDPATH= cd -- "$(dirname -- "$0")/.." && pwd
)"
cd "$repo_root"

./scripts/py scripts/_patch_fix_ci_guardrail_registry_executed_surface_exactness_v1.py
