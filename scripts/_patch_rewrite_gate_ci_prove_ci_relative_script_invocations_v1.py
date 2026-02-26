from __future__ import annotations

from pathlib import Path

GATE = Path("scripts/gate_ci_prove_ci_relative_script_invocations_v1.sh")

CANON = """#!/usr/bin/env bash
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
if grep -nE '\\$REPO_ROOT/scripts/' "$PROVE" >/dev/null 2>&1; then
  echo "ERR: prove_ci uses \\$REPO_ROOT/scripts/ invocations (forbidden):" >&2
  grep -nE '\\$REPO_ROOT/scripts/' "$PROVE" >&2 || true
  fail=1
fi

# 2) Hard ban: absolute path containing /scripts/...*.sh
# (common CWD-coupling regressions; keep strict)
if grep -nE '(^|[[:space:]"\\x27])/[^[:space:]"\\x27]*/scripts/[^[:space:]"\\x27]+\\.sh' "$PROVE" >/dev/null 2>&1; then
  echo "ERR: prove_ci uses absolute /.../scripts/... invocations (forbidden):" >&2
  grep -nE '(^|[[:space:]"\\x27])/[^[:space:]"\\x27]*/scripts/[^[:space:]"\\x27]+\\.sh' "$PROVE" >&2 || true
  fail=1
fi

# 3) Soft structure check:
# If a line contains a bash call to scripts/*.sh, it must ultimately be a RELATIVE invocation.
# Allow common prefixes:
#   - if bash scripts/...
#   - VAR=1 bash scripts/...
#   - VAR="x y" bash scripts/...
# Ignore comment lines.
while IFS= read -r line; do
  case "$line" in
    \\#*) continue ;;
  esac

  # Only inspect lines that mention "bash" and a scripts/*.sh token.
  if ! echo "$line" | grep -Eq '[[:space:]]bash[[:space:]].*(\\./)?scripts/[^[:space:]"\\x27]+\\.sh'; then
    continue
  fi

  # Accept canonical relative patterns (optional: leading 'if' + env assignments)
  if echo "$line" | grep -Eq '^[[:space:]]*(if[[:space:]]+)?([A-Za-z_][A-Za-z0-9_]*=("[^"]*"|\\x27[^\\x27]*\\x27|[^[:space:]]+)[[:space:]]+)*bash[[:space:]]+"?(\\./)?scripts/[^[:space:]"\\x27]+\\.sh"?([[:space:]]|$)'; then
    continue
  fi

  echo "ERR: non-canonical bash scripts invocation (must be relative):" >&2
  echo "  $line" >&2
  fail=1
done < "$PROVE"

if [ "$fail" -ne 0 ]; then
  exit 1
fi

exit 0
"""

def main() -> None:
    old = GATE.read_text(encoding="utf-8") if GATE.exists() else ""
    if old == CANON:
        print("OK: gate_ci_prove_ci_relative_script_invocations_v1 already canonical (noop)")
        return
    GATE.write_text(CANON, encoding="utf-8")
    print("OK: rewrote gate_ci_prove_ci_relative_script_invocations_v1 to canonical body")

if __name__ == "__main__":
    main()
