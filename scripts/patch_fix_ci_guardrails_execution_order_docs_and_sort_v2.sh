#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
"$ROOT/scripts/py" "$ROOT/scripts/_patch_fix_ci_guardrails_execution_order_docs_and_sort_v2.py"
