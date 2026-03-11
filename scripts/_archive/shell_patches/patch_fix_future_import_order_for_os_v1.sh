#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix __future__ import ordering vs import os (v1) ==="

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

"$repo_root/scripts/py" "$repo_root/scripts/_patch_fix_future_import_order_for_os_v1.py"

echo "OK"
