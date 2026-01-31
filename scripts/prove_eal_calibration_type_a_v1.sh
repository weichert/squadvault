#!/usr/bin/env bash

echo
echo "==> unit tests (pytest)"
TEST_DIR=""
if [[ -d "tests" ]]; then TEST_DIR="tests"; fi
if [[ -z "${TEST_DIR}" && -d "Tests" ]]; then TEST_DIR="Tests"; fi
if [[ -z "${TEST_DIR}" ]]; then
  echo "ERROR: no tests/ or Tests/ directory found" >&2
  exit 2
fi

# Run the existing EAL-related tests by filename (directory-case safe)
./scripts/py -m pytest -q \
  "${TEST_DIR}/test_editorial_attunement_v1.py" \
  "${TEST_DIR}/test_eal_writer_boundary_v1.py" \
  "${TEST_DIR}/test_recap_runs_eal_persistence_v1.py" \
  "${TEST_DIR}/test_get_recap_run_trace_optional_eal_v1.py"
