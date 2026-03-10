#!/usr/bin/env bash
set -euo pipefail
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
./scripts/py scripts/_patch_fix_finalize_ci_guardrails_refresh_renderer_invocation_v1.py
