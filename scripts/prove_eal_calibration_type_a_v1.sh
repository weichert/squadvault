#!/usr/bin/env bash

echo
echo "==> unit tests (pytest; tracked Tests/ paths; bash3-safe)"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

# Prefer canonical Tests/ (capital T). Fall back to tests/ only if needed.
TEST_DIR=""
if [[ -d "Tests" ]]; then TEST_DIR="Tests"; fi
if [[ -z "${TEST_DIR}" && -d "tests" ]]; then TEST_DIR="tests"; fi
if [[ -z "${TEST_DIR}" ]]; then
  echo "ERROR: no Tests/ or tests/ directory found" >&2
  exit 2
fi
echo "Using TEST_DIR=${TEST_DIR}"

# Build a newline-separated list from git (no mapfile; bash 3.2 compatible)
tests_list="$(
  git ls-files \
    "${TEST_DIR}/test_editorial_attunement_v1.py" \
    "${TEST_DIR}/test_eal_writer_boundary_v1.py" \
    "${TEST_DIR}/test_recap_runs_eal_persistence_v1.py" \
    "${TEST_DIR}/test_get_recap_run_trace_optional_eal_v1.py" \
  || true
)"

if [[ -z "${tests_list}" ]]; then
  echo "ERROR: expected EAL test files not tracked under ${TEST_DIR}/" >&2
  echo "DEBUG: tracked ${TEST_DIR} root (first 120):" >&2
  git ls-files "${TEST_DIR}/*.py" | sed -n '1,120p' >&2 || true
  exit 2
fi

echo "Tracked EAL tests:"
echo "${tests_list}"

# Run them. (Safe: filenames have no spaces.)



REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

# Prefer git-tracked test paths (avoids tests/ vs Tests/ case collisions)
eal_tests=()
while IFS= read -r __line; do
  eal_tests+=("$__line")
done < <(
  git ls-files \
    'tests/test_editorial_attunement_v1.py' \
    'Tests/test_editorial_attunement_v1.py' \
    'tests/test_eal_writer_boundary_v1.py' \
    'Tests/test_eal_writer_boundary_v1.py' \
    'tests/test_recap_runs_eal_persistence_v1.py' \
    'Tests/test_recap_runs_eal_persistence_v1.py' \
    'tests/test_get_recap_run_trace_optional_eal_v1.py' \
    'Tests/test_get_recap_run_trace_optional_eal_v1.py'
)
unset __line

echo "Tracked EAL test files: ${#eal_tests[@]}"
if [[ ${#eal_tests[@]} -eq 0 ]]; then
  echo "ERROR: none of the expected EAL test files are tracked in git." >&2
  echo "DEBUG: here are tracked test roots:" >&2
  git ls-files 'tests/*.py' 'Tests/*.py' | sed -n '1,120p' >&2 || true
  exit 2
fi

# SV_PATCH: tracked-only pytest list (no tests/ lowercase pass)
echo "Running tracked EAL tests only (git ls-files)"
./scripts/py -m pytest -q "${eal_tests[@]}"
# /SV_PATCH: tracked-only pytest list (no tests/ lowercase pass)

# SV_PATCH: prune redundant TEST_DIR tail + dedupe tracked pytest run
# Removed redundant TEST_DIR auto-detect tail (case-collision risk).
# EAL tests are executed via git-tracked eal_tests[] above.
# /SV_PATCH: prune redundant TEST_DIR tail + dedupe tracked pytest run
