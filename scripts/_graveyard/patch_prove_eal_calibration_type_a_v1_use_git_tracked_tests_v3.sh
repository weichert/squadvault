#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: prove_eal_calibration_type_a_v1 use git-tracked test paths (v3) ==="

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

# Ensure repo-root cd exists
if "REPO_ROOT=" not in s:
    s = re.sub(
        r"(set -euo pipefail\s*\n)",
        r"\1\nREPO_ROOT=\"$(cd \"$(dirname \"${BASH_SOURCE[0]}\")/..\" && pwd)\"\ncd \"${REPO_ROOT}\"\n",
        s,
        count=1,
    )

unit_block = """
echo
echo "==> unit tests (pytest; git-tracked paths)"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

# Prefer git-tracked test paths (avoids tests/ vs Tests/ case collisions)
mapfile -t eal_tests < <(
  git ls-files \\
    'tests/test_editorial_attunement_v1.py' \\
    'Tests/test_editorial_attunement_v1.py' \\
    'tests/test_eal_writer_boundary_v1.py' \\
    'Tests/test_eal_writer_boundary_v1.py' \\
    'tests/test_recap_runs_eal_persistence_v1.py' \\
    'Tests/test_recap_runs_eal_persistence_v1.py' \\
    'tests/test_get_recap_run_trace_optional_eal_v1.py' \\
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
"""

# Replace any existing unit-test block starting at '==> unit tests'
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
