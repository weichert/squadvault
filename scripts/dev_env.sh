#!/usr/bin/env bash
# SV_PATCH_DEV_ENV_V1: source-from-anywhere header
# Source this from anywhere inside the repo:
#   source /path/to/repo/scripts/dev_env.sh

export REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${PYTHONPATH:-$REPO_ROOT/src}"

echo "REPO_ROOT=$REPO_ROOT"
echo "PYTHONPATH=$PYTHONPATH"
