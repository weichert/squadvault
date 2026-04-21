#!/usr/bin/env bash
# SquadVault — gate: repo-root allowlist (v1)
#
# Purpose:
#   Fail if any file at repo root is outside Tests/test_repo_root_allowlist_v1.py's
#   ALLOWED_ROOT_FILES set (catches phantom files, stray memos, un-archived
#   delivery scripts). Enforces the class of mistake where an observation memo
#   lands at repo root instead of _observations/.
#
# Scope:
#   - Narrow pytest invocation against a single test file (runs in < 1s).
#   - Intentionally narrow: this gate is wired into the pre-commit hook and
#     must stay fast enough that operators will not disable it.
#
# Escape hatch:
#   None at the gate level. The pre-commit hook's SV_SKIP_PRECOMMIT=1 hatch
#   applies to the entire hook chain, which includes this gate.
#
# Determinism / Safety:
#   - repo-root anchored
#   - no network, no package installs, no xtrace
#   - python3 -m pytest avoids PATH ambiguity

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

echo "==> Repo-root allowlist gate"

python3 -m pytest -q Tests/test_repo_root_allowlist_v1.py
