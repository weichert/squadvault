#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix ChronicleInputResolverV1.resolve() in input_contract_v1 (v4) ==="
python="${PYTHON:-python}"
$python scripts/_patch_rc_input_contract_fix_resolve_v4.py

echo "==> py_compile"
PYTHONPATH=src python -m py_compile src/squadvault/chronicle/input_contract_v1.py
echo "OK: py_compile"

echo "==> run only the two previously failing test modules"
PYTHONPATH=src python -m unittest -v \
  Tests.test_rivalry_chronicle_input_contract_v1 \
  Tests.test_rivalry_chronicle_generator_v1_determinism
echo "OK: targeted tests"
