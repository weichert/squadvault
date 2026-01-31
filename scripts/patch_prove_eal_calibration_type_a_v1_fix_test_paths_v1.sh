#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: prove_eal_calibration_type_a_v1 test path autodetect (v1) ==="

SCRIPT="scripts/prove_eal_calibration_type_a_v1.sh"
if [[ ! -f "$SCRIPT" ]]; then
  echo "ERROR: missing $SCRIPT" >&2
  exit 2
fi

python - <<'PY'
from pathlib import Path

p = Path("scripts/prove_eal_calibration_type_a_v1.sh")
s = p.read_text()

# Replace the entire unit test block if present; otherwise append a sane one.
marker = '==> unit tests'
if marker in s:
    # crude but safe: replace from marker to next "OK: tests" (or end)
    import re
    s2 = re.sub(
        r'(?s)\n?echo\s*\n?echo\s*"==>\s*unit tests.*?(\n.*?)*?(?=\n\n|\Z)',
        "\n\necho\necho \"==> unit tests (pytest)\"\n"
        "TEST_DIR=\"\"\n"
        "if [[ -d \"tests\" ]]; then TEST_DIR=\"tests\"; fi\n"
        "if [[ -z \"${TEST_DIR}\" && -d \"Tests\" ]]; then TEST_DIR=\"Tests\"; fi\n"
        "if [[ -z \"${TEST_DIR}\" ]]; then\n"
        "  echo \"ERROR: no tests/ or Tests/ directory found\" >&2\n"
        "  exit 2\n"
        "fi\n"
        "\n"
        "# Run the existing EAL-related tests by filename (directory-case safe)\n"
        "./scripts/py -m pytest -q \\\n"
        "  \"${TEST_DIR}/test_editorial_attunement_v1.py\" \\\n"
        "  \"${TEST_DIR}/test_eal_writer_boundary_v1.py\" \\\n"
        "  \"${TEST_DIR}/test_recap_runs_eal_persistence_v1.py\" \\\n"
        "  \"${TEST_DIR}/test_get_recap_run_trace_optional_eal_v1.py\"\n",
        s,
        count=1,
    )
    s = s2
else:
    s += (
        "\n\necho\necho \"==> unit tests (pytest)\"\n"
        "TEST_DIR=\"\"\n"
        "if [[ -d \"tests\" ]]; then TEST_DIR=\"tests\"; fi\n"
        "if [[ -z \"${TEST_DIR}\" && -d \"Tests\" ]]; then TEST_DIR=\"Tests\"; fi\n"
        "if [[ -z \"${TEST_DIR}\" ]]; then\n"
        "  echo \"ERROR: no tests/ or Tests/ directory found\" >&2\n"
        "  exit 2\n"
        "fi\n"
        "\n"
        "./scripts/py -m pytest -q \\\n"
        "  \"${TEST_DIR}/test_editorial_attunement_v1.py\" \\\n"
        "  \"${TEST_DIR}/test_eal_writer_boundary_v1.py\" \\\n"
        "  \"${TEST_DIR}/test_recap_runs_eal_persistence_v1.py\" \\\n"
        "  \"${TEST_DIR}/test_get_recap_run_trace_optional_eal_v1.py\"\n"
    )

# Also: remove any bogus "OK: tests" echoes that might mask failures.
s = s.replace('echo "OK: tests"\n', '')

p.write_text(s)
print("OK: patched", p)
PY

echo "==> smoke"
bash "$SCRIPT"
echo "OK"
