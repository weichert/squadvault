#!/usr/bin/env bash

echo
echo "==> unit tests (pytest; git-tracked paths)"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

# Prefer git-tracked test paths (avoids tests/ vs Tests/ case collisions)
mapfile -t eal_tests < <(
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

echo "Tracked EAL test files: ${#eal_tests[@]}"
if [[ ${#eal_tests[@]} -eq 0 ]]; then
  echo "ERROR: none of the expected EAL test files are tracked in git." >&2
  echo "DEBUG: here are tracked test roots:" >&2
  git ls-files 'tests/*.py' 'Tests/*.py' | sed -n '1,120p' >&2 || true
  exit 2
fi

# Run exactly what git says exists
./scripts/py -m pytest -q "${eal_tests[@]}"



# Always run from repo root (pytest path resolution depends on cwd)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

# Prefer whichever directory actually contains the files (case-safe)
TEST_DIR=""
for d in tests Tests; do
  if [[ -d "$d" ]]; then
    # pick this dir if it contains any of the target files
    if [[ -f "$d/test_editorial_attunement_v1.py" ]] || [[ -f "$d/test_eal_writer_boundary_v1.py" ]] || [[ -f "$d/test_recap_runs_eal_persistence_v1.py" ]] || [[ -f "$d/test_get_recap_run_trace_optional_eal_v1.py" ]]; then
      TEST_DIR="$d"
      break
    fi
  fi
done

if [[ -z "${TEST_DIR}" ]]; then
  echo "ERROR: could not find expected EAL-related test files under tests/ or Tests/." >&2
  echo "DEBUG: repo_root=${REPO_ROOT}" >&2
  echo "DEBUG: listing tests dirs:" >&2
  ls -la tests Tests 2>/dev/null || true
  echo "DEBUG: matching files:" >&2
  ls -la tests/test_*eal* Tests/test_*eal* 2>/dev/null || true
  exit 2
fi

echo "Using TEST_DIR=${TEST_DIR}"

# Build the list of tests that actually exist (so we fail clearly if missing)
args=()
for f in \
  test_editorial_attunement_v1.py \
  test_eal_writer_boundary_v1.py \
  test_recap_runs_eal_persistence_v1.py \
  test_get_recap_run_trace_optional_eal_v1.py; do
  if [[ -f "${TEST_DIR}/${f}" ]]; then
    args+=("${TEST_DIR}/${f}")
  fi
done

if [[ ${#args[@]} -eq 0 ]]; then
  echo "ERROR: no target tests exist under ${TEST_DIR}." >&2
  exit 2
fi

./scripts/py -m pytest -q "${args[@]}"


# Run the existing EAL-related tests by filename (directory-case safe)
./scripts/py -m pytest -q \
  "${TEST_DIR}/test_editorial_attunement_v1.py" \
  "${TEST_DIR}/test_eal_writer_boundary_v1.py" \
  "${TEST_DIR}/test_recap_runs_eal_persistence_v1.py" \
  "${TEST_DIR}/test_get_recap_run_trace_optional_eal_v1.py"
