#!/usr/bin/env bash
set -euo pipefail

# Enforce: scripts/prove_ci.sh must invoke scripts via relative repo-root paths
# (no $REPO_ROOT/scripts/..., no absolute /.../scripts/... paths).
PROVE="scripts/prove_ci.sh"

if [ ! -f "$PROVE" ]; then
  echo "ERR: missing file: $PROVE" >&2
  exit 1
fi

fail=0

# 1) Hard ban: $REPO_ROOT/scripts/
if grep -nE '\$REPO_ROOT/scripts/' "$PROVE" >/dev/null 2>&1; then
  echo "ERR: prove_ci uses \$REPO_ROOT/scripts/ invocations (forbidden):" >&2
  grep -nE '\$REPO_ROOT/scripts/' "$PROVE" >&2 || true
  fail=1
fi

# 2) Hard ban: absolute path containing /scripts/
# (common CWD-coupling regressions; keep strict)
if grep -nE '(^|[[:space:]"'\''])/[^[:space:]"'\'']*/scripts/[^[:space:]"'\'']+\.sh' "$PROVE" >/dev/null 2>&1; then
  echo "ERR: prove_ci uses absolute /.../scripts/... invocations (forbidden):" >&2
  grep -nE '(^|[[:space:]"'\''])/[^[:space:]"'\'']*/scripts/[^[:space:]"'\'']+\.sh' "$PROVE" >&2 || true
  fail=1
fi

# 3) Soft structure check: any bash-invoked scripts must start with bash scripts/... or bash ./scripts/...
# Ignore comment lines.
while IFS= read -r line; do
  case "$line" in
    \#*) continue ;;
  esac

  case "$line" in
    *"bash "*scripts/*".sh"*)
      # allow: bash scripts/foo.sh  OR  bash ./scripts/foo.sh  (with optional quotes)
      if echo "$line" | grep -Eq '^[[:space:]]*bash[[:space:]]+"?(\./)?scripts/[^[:space:]"]+\.sh"?([[:space:]]|$)'; then
        : # ok
      else
        echo "ERR: non-canonical bash scripts invocation (must be relative):" >&2
        echo "  $line" >&2
        fail=1
      fi
      ;;
  esac
done < "$PROVE"

if [ "$fail" -ne 0 ]; then
  exit 1
fi

exit 0
