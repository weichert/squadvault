#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_fix_prove_ci_worktree_snapshot_init_v1.py
