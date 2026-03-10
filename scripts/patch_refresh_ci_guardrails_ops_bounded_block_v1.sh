#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

./scripts/py scripts/_patch_refresh_ci_guardrails_ops_bounded_block_v1.py
