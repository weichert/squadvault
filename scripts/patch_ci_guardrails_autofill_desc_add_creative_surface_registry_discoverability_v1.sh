#!/usr/bin/env bash
set -euo pipefail

script_dir="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "${script_dir}/.." && pwd)"

patcher="${repo_root}/scripts/_patch_ci_guardrails_autofill_desc_add_creative_surface_registry_discoverability_v1.py"
target="${repo_root}/scripts/_patch_docs_fill_ci_guardrails_autofill_descriptions_v1.py"

bash -n "$0"
"${repo_root}/scripts/py" -m py_compile "$patcher"
"${repo_root}/scripts/py" "$patcher"

key="gate_creative_surface_registry_discoverability_v1.sh"
c="$(grep -n --fixed-strings "$key" "$target" | wc -l | tr -d ' ')"
test "$c" = "1"
