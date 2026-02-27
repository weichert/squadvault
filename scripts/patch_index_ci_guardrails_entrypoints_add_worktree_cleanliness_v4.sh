#!/bin/bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_index_ci_guardrails_entrypoints_add_worktree_cleanliness_v4.py
