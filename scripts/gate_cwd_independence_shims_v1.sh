#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

unset SV_DEBUG SV_DEBUG_JSON

cd "$tmp"

"$REPO_ROOT/scripts/check_shims_compliance.sh" >/dev/null
"$REPO_ROOT/scripts/py" -c 'print("OK: scripts/py")' >/dev/null
"$REPO_ROOT/scripts/recap.sh" --help >/dev/null
"$REPO_ROOT/scripts/recap" --help >/dev/null

echo "OK: CWD-independence gate passed."
