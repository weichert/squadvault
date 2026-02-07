#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: TEMPLATE (v0) ==="

# Hard stop: this is a template, not a runnable patch.
echo "ERROR: this is a TEMPLATE wrapper. Copy/rename it to scripts/patch_<real_name>_vN.sh and update paths."
exit 2


# 1) compile check
./scripts/py -m py_compile scripts/_patch_TEMPLATE_v0.py

# 2) run patcher
./scripts/py scripts/_patch_TEMPLATE_v0.py

# 3) wrapper sanity
echo "==> bash -n wrapper"
bash -n scripts/patch_TEMPLATE_v0.sh

# 4) lightweight assertions (edit per patch)
echo "==> quick assertions"
# grep -n "pattern" path/to/file || true

# 5) preview (edit per patch)
# sed -n '1,120p' path/to/file

echo "OK"
