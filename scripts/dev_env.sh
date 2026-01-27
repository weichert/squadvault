#!/usr/bin/env bash
# Source this from repo root:  source scripts/dev_env.sh
set -euo pipefail

export REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${PYTHONPATH:-$REPO_ROOT/src}"

echo "REPO_ROOT=$REPO_ROOT"
echo "PYTHONPATH=$PYTHONPATH"
