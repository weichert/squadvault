#!/usr/bin/env bash
set -euo pipefail
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
./scripts/py scripts/_patch_finalize_ci_guardrails_label_registry_and_refresh_block_v1.py
