#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix new patch wrappers to use scripts/py (v1) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py -m py_compile scripts/_patch_fix_new_patch_wrappers_use_scripts_py_v1.py
./scripts/py scripts/_patch_fix_new_patch_wrappers_use_scripts_py_v1.py

# Safety: ensure wrappers remain syntactically valid.
bash -n scripts/patch_add_coverage_baseline_v1.sh
bash -n scripts/patch_ops_index_add_best_in_class_guardrails_v1.sh
bash -n scripts/patch_ops_index_add_standard_show_input_need_coverage_gate_v1.sh
bash -n scripts/patch_ops_index_dedupe_fixture_immutability_proof_entry_v1.sh
bash -n scripts/patch_prove_ci_wire_indexed_guardrails_v1.sh

echo "OK"
