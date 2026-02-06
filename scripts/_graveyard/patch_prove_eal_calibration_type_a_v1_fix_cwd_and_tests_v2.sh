#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: prove_eal_calibration_type_a_v1 fix cwd + test discovery (v2) ==="

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

# 1) Ensure we cd to repo root early (idempotent)
if "REPO_ROOT=" not in s:
    # insert after the first 'set -euo pipefail' occurrence
    s = re.sub(
        r"(set -euo pipefail\s*\n)",
        r"\1\nREPO_ROOT=\"$(cd \"$(dirname \"${BASH_SOURCE[0]}\")/..\" && pwd)\"\ncd \"${REPO_ROOT}\"\n",
        s,
        count=1,
    )

# 2) Replace the unit test block with a cwd-safe, existence-checked pytest invocation.
# We match from '==> unit tests' echo to the next blank line or EOF.
unit_block = (
    "\n\necho\n"
    "echo \"==> unit tests (pytest)\"\n"
    "\n"
    "# Always run from repo root (pytest path resolution depends on cwd)\n"
    "REPO_ROOT=\"$(cd \"$(dirname \"${BASH_SOURCE[0]}\")/..\" && pwd)\"\n"
    "cd \"${REPO_ROOT}\"\n"
    "\n"
    "# Prefer whichever directory actually contains the files (case-safe)\n"
    "TEST_DIR=\"\"\n"
    "for d in tests Tests; do\n"
    "  if [[ -d \"$d\" ]]; then\n"
    "    # pick this dir if it contains any of the target files\n"
    "    if [[ -f \"$d/test_editorial_attunement_v1.py\" ]] || [[ -f \"$d/test_eal_writer_boundary_v1.py\" ]] || [[ -f \"$d/test_recap_runs_eal_persistence_v1.py\" ]] || [[ -f \"$d/test_get_recap_run_trace_optional_eal_v1.py\" ]]; then\n"
    "      TEST_DIR=\"$d\"\n"
    "      break\n"
    "    fi\n"
    "  fi\n"
    "done\n"
    "\n"
    "if [[ -z \"${TEST_DIR}\" ]]; then\n"
    "  echo \"ERROR: could not find expected EAL-related test files under tests/ or Tests/.\" >&2\n"
    "  echo \"DEBUG: repo_root=${REPO_ROOT}\" >&2\n"
    "  echo \"DEBUG: listing tests dirs:\" >&2\n"
    "  ls -la tests Tests 2>/dev/null || true\n"
    "  echo \"DEBUG: matching files:\" >&2\n"
    "  ls -la tests/test_*eal* Tests/test_*eal* 2>/dev/null || true\n"
    "  exit 2\n"
    "fi\n"
    "\n"
    "echo \"Using TEST_DIR=${TEST_DIR}\"\n"
    "\n"
    "# Build the list of tests that actually exist (so we fail clearly if missing)\n"
    "args=()\n"
    "for f in \\\n"
    "  test_editorial_attunement_v1.py \\\n"
    "  test_eal_writer_boundary_v1.py \\\n"
    "  test_recap_runs_eal_persistence_v1.py \\\n"
    "  test_get_recap_run_trace_optional_eal_v1.py; do\n"
    "  if [[ -f \"${TEST_DIR}/${f}\" ]]; then\n"
    "    args+=(\"${TEST_DIR}/${f}\")\n"
    "  fi\n"
    "done\n"
    "\n"
    "if [[ ${#args[@]} -eq 0 ]]; then\n"
    "  echo \"ERROR: no target tests exist under ${TEST_DIR}.\" >&2\n"
    "  exit 2\n"
    "fi\n"
    "\n"
    "./scripts/py -m pytest -q \"${args[@]}\"\n"
)

if "==> unit tests" in s:
    s = re.sub(
        r'(?s)\n*echo\s*\n*echo\s*"\=\=>\s*unit tests.*?(?=\n\n|\Z)',
        unit_block,
        s,
        count=1,
    )
else:
    s += unit_block

# 3) Remove any bogus "OK: tests" masking line if present
s = s.replace('echo "OK: tests"\n', '')

p.write_text(s)
print("OK: patched", p)
PY

echo "==> smoke"
bash "$SCRIPT"
echo "OK"
