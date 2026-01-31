from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "patch_writing_room_intake_exclusions_v1.sh"

def main() -> int:
    s = TARGET.read_text(encoding="utf-8")

    # Insert detection right after PY_BIN assignment line.
    # We’ll replace:
    #   PY_BIN="${PY_BIN:-python3}"
    # with a block that tries python, python3, then falls back.
    pattern = r'PY_BIN="\$\{PY_BIN:-python3\}"\n'
    if not re.search(pattern, s):
        raise SystemExit('ERROR: expected PY_BIN="${PY_BIN:-python3}" not found; refusing to patch.')

    block = (
        'PY_BIN="${PY_BIN:-}"\n'
        '\n'
        '# Choose a Python that has pytest installed.\n'
        '# Order: $PY_BIN (if provided) -> python -> python3 -> fall back to pytest executable.\n'
        'if [[ -n "${PY_BIN}" ]]; then\n'
        '  if ! "${PY_BIN}" -c "import pytest" >/dev/null 2>&1; then\n'
        '    echo "ERROR: PY_BIN is set to ${PY_BIN} but pytest is not installed in that interpreter." >&2\n'
        '    exit 2\n'
        '  fi\n'
        'else\n'
        '  if python -c "import pytest" >/dev/null 2>&1; then\n'
        '    PY_BIN="python"\n'
        '  elif python3 -c "import pytest" >/dev/null 2>&1; then\n'
        '    PY_BIN="python3"\n'
        '  else\n'
        '    PY_BIN=""\n'
        '  fi\n'
        'fi\n'
        '\n'
    )

    s2 = re.sub(pattern, block, s, count=1)
    if s2 == s:
        raise SystemExit("ERROR: patch made no changes; refusing to proceed.")

    # Now adjust the actual test invocation:
    # If we previously inserted "$PY_BIN -m pytest -q", keep it but guard if PY_BIN empty.
    s2 = s2.replace(
        '"$PY_BIN" -m pytest -q',
        'if [[ -n "${PY_BIN}" ]]; then\n'
        '  "$PY_BIN" -m pytest -q\n'
        'else\n'
        '  echo "WARNING: pytest not importable via python/python3; falling back to pytest executable on PATH" >&2\n'
        '  pytest -q\n'
        'fi'
    )

    TARGET.write_text(s2, encoding="utf-8")
    print(f"OK: patched {TARGET.relative_to(ROOT)}")
    print("Wrapper now auto-detects a pytest-capable Python (python -> python3 -> pytest).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
