#!/usr/bin/env bash
set -euo pipefail

echo "=== Proof: EAL Calibration — Type A invariants (v1) ==="

echo "==> py_compile"
./scripts/py -m py_compile src/squadvault/core/eal/eal_calibration_v1.py
echo "OK: compile"

echo
echo "==> unit test (path-import workaround)"
python Tests/test_eal_calibration_v1.py -q
echo "OK: tests"
