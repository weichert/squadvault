#!/usr/bin/env bash
set -euo pipefail

# Gate: forbid pytest directory invocation in prove scripts.
# Rationale: directory invocation can silently expand CI scope when new files appear.
# Allowed: running pytest against explicit .py files or pinned git-tracked lists (arrays).
# Forbidden: any pytest invocation that references "Tests" but not ".py" on the same line.

fail() {
  echo "ERROR: pytest directory invocation detected: $*" >&2
  exit 2
}

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
    fail "missing file: $f"
  fi

  lineno=0
  while IFS= read -r line; do
    lineno=$((lineno + 1))

    # Skip comments
    case "$line" in
      \#*) continue ;;
    esac

    # SV_PATCH_V2: refine detection (ignore echo/printf; only executable pytest lines)
SV_PATCH_V2: refine detection (ignore echo/printf; only executable pytest lines)
    # Only consider lines that appear to EXECUTE pytest.
    # - Ignore echo/printf lines (they may mention 'pytest' in log text)
    # - Match either: command starts with pytest, or contains '-m pytest'
    if echo "$line" | grep -Eq '^[[:space:]]*(echo|printf)[[:space:]]'; then
      continue
    fi

    if echo "$line" | grep -Eq '^[[:space:]]*pytest[[:space:]]' || echo "$line" | grep -Eq '[[:space:]]-m[[:space:]]+pytest[[:space:]]'; then
      # If the line references Tests but not .py, it's almost certainly a directory invocation.
      # This intentionally fails closed.
      if echo "$line" | grep -q 'Tests' && ! echo "$line" | grep -q '\.py'; then
          echo
          echo "=== Gate failure: pytest directory invocation forbidden ===" >&2
          echo "file: $f" >&2
          echo "line: $lineno" >&2
          echo "text: $line" >&2
          echo >&2
          echo "Fix: pin the test surface using a git-tracked list:" >&2
          echo "  tests=(\$(git ls-files 'Tests/.../test_*.py' | sort))" >&2
          echo "  pytest -q \"\${tests[@]}\"" >&2
          exit 2
        fi
  done < "$f"
done

echo "OK: no pytest directory invocation found in prove scripts"
