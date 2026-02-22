#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_guard_ci_guardrails_autofill_idempotence_mode_v1.py
