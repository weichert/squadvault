# Golden Path Pytest Pinning — Canonical State

## Status
DONE (v3)

## Canonical Mechanism
- scripts/_patch_prove_golden_path_pin_pytest_list_v3.py
- scripts/patch_prove_golden_path_pin_pytest_list_v3.sh

## Guarantees
- No `pytest -q Tests` directory invocation (standalone line)
- Git-tracked test enumeration only (`git ls-files Tests/test_*.py | sort`)
- Bash 3.2 compatible (no `mapfile`)
- ops_orchestrate idempotent (pass2)

## Notes
Earlier Golden Path pytest pin patchers (v1/v2) and related removal patchers are retained for audit history only.
