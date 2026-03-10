#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
./scripts/py scripts/_patch_render_ci_guardrails_ops_from_cluster_order_source_v1.py
