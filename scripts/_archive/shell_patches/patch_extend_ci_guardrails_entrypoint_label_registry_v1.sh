#!/usr/bin/env bash
set -euo pipefail
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
./scripts/py scripts/_patch_extend_ci_guardrails_entrypoint_label_registry_v1.py
