#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: prove_eal_calibration_type_a_v1 (no mapfile; use Tests/) (v4) ==="

SCRIPT="scripts/prove_eal_calibration_type_a_v1.sh"
if [[ ! -f "$SCRIPT" ]]; then
  echo "ERROR: missing $SCRIPT" >&2
  exit 2
fi

python - <<'PY'
from pathlib import Path
import re

p = Path("scripts/prove_eal_calibration_type_a_v1.sh")
s = p.read_text()

# Ensure repo-root cd exists (idempotent enough)
if "REPO_ROOT=" not in s:
    s = re.sub(
        r"(set -euo pipefail\s*\n)",
        r"\1\nREPO_ROOT=\"$(cd \"$(dirname \"${BASH_SOURCE[0]}\")/..\" && pwd)\"\ncd \"${REPO_ROOT}\"\n",
        s,
        count=1,
    )

unit_block = r'''
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
./scripts/py -m pytest -q ${tests_list}
'''

# Replace any existing unit-test section starting at '==> unit tests'
if "==> unit tests" in s:
    s = re.sub(
        r'(?s)\n*echo\s*\n*echo\s*"\=\=>\s*unit tests.*?(?=\n\n|\Z)',
        "\n" + unit_block + "\n",
        s,
        count=1,
    )
else:
    s += "\n" + unit_block + "\n"

# Remove any bogus "OK: tests" masking line if present
s = s.replace('echo "OK: tests"\n', '')

p.write_text(s)
print("OK: patched", p)
PY

echo "==> smoke"
bash "$SCRIPT"
echo "OK"
