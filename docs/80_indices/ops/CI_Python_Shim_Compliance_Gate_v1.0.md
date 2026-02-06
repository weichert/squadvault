[SV_CANONICAL_HEADER_V1]

Contract Name: CI Python Shim Compliance Gate
Version: v1.0
Status: CANONICAL

Defers To:
  - Canonical Operating Constitution (Tier 0)
  - CI Guardrails Index (Tier 1)

Default: Any behavior not explicitly permitted by this contract is forbidden.

—

## Purpose

Ensure patch wrappers and proof/gate scripts invoke Python via the repo-local shim:
- `./scripts/py`

This prevents PATH / venv ambiguity and keeps wrappers CWD-safe.

## Enforced By

- Gate script: `scripts/check_python_shim_compliance_v2.sh`
- CI runner: `scripts/prove_ci.sh`

## Canonical Patch Pairs

- Add gate:
  - `scripts/_patch_add_python_shim_compliance_gate_v1.py`
  - `scripts/patch_add_python_shim_compliance_gate_v1.sh`

- Standardize wrappers on shim:
  - `scripts/_patch_fix_patch_wrappers_use_py_shim_v5.py`
  - `scripts/patch_fix_patch_wrappers_use_py_shim_v5.sh`

- Refine enforcement:
  - `scripts/_patch_refine_python_shim_compliance_gate_v7.py`
  - `scripts/patch_refine_python_shim_compliance_gate_v7.sh`
