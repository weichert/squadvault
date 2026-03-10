#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
"$ROOT/scripts/py" "$ROOT/scripts/_patch_fix_ci_guardrails_index_duplicate_markers_v2.py"
