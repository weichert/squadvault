#!/usr/bin/env bash
set -euo pipefail
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
./scripts/py scripts/_patch_add_gate_no_xtrace_label_registry_row_v1.py
