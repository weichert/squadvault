#!/usr/bin/env bash
set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SELF_DIR/.." && pwd)"
cd "$REPO_ROOT"

./scripts/py scripts/_patch_add_gate_no_mapfile_readarray_in_scripts_v1.py
