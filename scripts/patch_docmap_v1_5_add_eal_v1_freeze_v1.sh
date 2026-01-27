#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Documentation Map v1.5 — add EAL v1 freeze cross-ref ==="

python scripts/_patch_docmap_v1_5_add_eal_v1_freeze_v1.py

echo "DONE"
