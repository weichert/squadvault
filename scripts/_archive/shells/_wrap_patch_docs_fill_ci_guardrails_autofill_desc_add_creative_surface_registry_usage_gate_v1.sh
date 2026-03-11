#!/usr/bin/env bash
set -euo pipefail
bash -n "$0"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

python -m py_compile scripts/_patch_docs_fill_ci_guardrails_autofill_desc_add_creative_surface_registry_usage_gate_v1.py
python scripts/_patch_docs_fill_ci_guardrails_autofill_desc_add_creative_surface_registry_usage_gate_v1.py

grep -n --fixed-strings "scripts/gate_creative_surface_registry_usage_v1.sh" scripts/_patch_docs_fill_ci_guardrails_autofill_descriptions_v1.py >/dev/null
