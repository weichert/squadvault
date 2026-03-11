#!/usr/bin/env bash
set -euo pipefail
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
./scripts/py scripts/_patch_fix_ci_guardrails_no_network_label_v1.py
