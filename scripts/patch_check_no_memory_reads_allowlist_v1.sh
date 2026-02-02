#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: check_no_memory_reads allowlist (v1) ==="

SCRIPT="scripts/check_no_memory_reads.sh"
if [[ ! -f "$SCRIPT" ]]; then
  echo "ERROR: missing $SCRIPT" >&2
  exit 2
fi

./scripts/py scripts/_patch_check_no_memory_reads_allowlist_v1.py

echo "==> smoke"
bash "$SCRIPT"
echo "OK"
