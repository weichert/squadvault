#!/usr/bin/env bash
# SquadVault — recap CLI shim (deterministic python path)
# Purpose: run the canonical scripts/recap.py via scripts/py to enforce repo imports.
# CWD-independent: resolves paths relative to this script.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec "${SCRIPT_DIR}/py" "${REPO_ROOT}/scripts/recap.py" "$@"
