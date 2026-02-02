#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." >/dev/null 2>&1 && pwd)"

echo "=== Proof: Signal Scout Tier-1 Type A invariants (v1) ==="
echo "    repo_root=${REPO_ROOT}"

# Run only the signal taxonomy Type A validation tests (canonical enforcement surface).
"${REPO_ROOT}/scripts/py" -m pytest -q "${REPO_ROOT}/Tests/validation/signals"

echo "OK: Signal Scout Tier-1 Type A invariants proved (v1)"
