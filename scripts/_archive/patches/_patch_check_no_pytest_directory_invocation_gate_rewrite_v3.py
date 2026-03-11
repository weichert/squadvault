from __future__ import annotations

import os
from pathlib import Path

TARGET = Path("scripts/check_no_pytest_directory_invocation.sh")
MARKER = "# SV_PATCH_V3: rewrite gate (executable pytest detection; ignore echo/printf)\n"

CONTENT = """#!/usr/bin/env bash
set -euo pipefail
""" + MARKER + """
# Gate: forbid pytest directory invocation in prove scripts.
# Rationale: directory invocation can silently expand CI scope when new files appear.
# Allowed: running pytest against explicit .py files or pinned git-tracked lists (arrays).
# Forbidden: any EXECUTED pytest invocation that references "Tests" but not ".py" on the same line.
#
# Note: This gate intentionally ignores echo/printf lines that mention 'pytest' for logging.

# If args are provided, scan those files; otherwise scan git-tracked scripts/prove_*.sh (plus prove_ci.sh).
files=()
if [ "$#" -gt 0 ]; then
  files=("$@")
else
  while IFS= read -r p; do
    files+=("$p")
  done < <(git ls-files 'scripts/prove_*.sh' 'scripts/prove_ci.sh' | sort)
fi

if [ "${#files[@]}" -eq 0 ]; then
  echo "ERROR: no files to scan" >&2
  exit 2
fi

for f in "${files[@]}"; do
  if [ ! -f "$f" ]; then
    echo "ERROR: missing file: $f" >&2
    exit 2
  fi

  lineno=0
  while IFS= read -r line; do
    lineno=$((lineno + 1))

    # Skip comments + empty lines.
    case "$line" in
      "" ) continue ;;
      \\#* ) continue ;;
    esac

    # Ignore log lines that may mention pytest.
    if echo "$line" | grep -Eq '^[[:space:]]*(echo|printf)[[:space:]]'; then
      continue
    fi

    # Only consider lines that appear to EXECUTE pytest.
    # Covers:
    #   pytest ...
    #   python -m pytest ...
    #   scripts/py -m pytest ...
    is_pytest_exec=0
    if echo "$line" | grep -Eq '^[[:space:]]*pytest[[:space:]]'; then
      is_pytest_exec=1
    elif echo "$line" | grep -Eq '[[:space:]]-m[[:space:]]+pytest[[:space:]]'; then
      is_pytest_exec=1
    fi

    if [ "$is_pytest_exec" -eq 1 ]; then
      if echo "$line" | grep -q 'Tests' && ! echo "$line" | grep -q '\\.py'; then
        echo
        echo "=== Gate failure: pytest directory invocation forbidden ===" >&2
        echo "file: $f" >&2
        echo "line: $lineno" >&2
        echo "text: $line" >&2
        echo >&2
        echo "Fix: pin the test surface using a git-tracked list:" >&2
        echo "  tests=(\\$(git ls-files 'Tests/.../test_*.py' | sort))" >&2
        echo "  pytest -q \\"\\${tests[@]}\\"" >&2
        exit 2
      fi
    fi
  done < "$f"
done

echo "OK: no pytest directory invocation found in prove scripts"
"""

def main() -> None:
    if TARGET.exists():
        cur = TARGET.read_text(encoding="utf-8")
        if MARKER in cur and cur == CONTENT:
            print("OK: already rewritten (v3 marker present).")
            return

    TARGET.write_text(CONTENT, encoding="utf-8")
    st = os.stat(TARGET)
    os.chmod(TARGET, st.st_mode | 0o111)
    print("OK: rewrote pytest directory invocation gate (v3)")

if __name__ == "__main__":
    main()
