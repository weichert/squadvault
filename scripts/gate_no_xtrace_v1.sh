#!/usr/bin/env bash
set -euo pipefail

# Gate: forbid xtrace ('set -x') in CI proof/gate scripts.
#
# Why:
#   'set -x' can leak env values and internal state into CI logs.
#
# Scope (git-tracked only):
#   scripts/prove_ci.sh
#   scripts/prove_*.sh
#   scripts/gate_*.sh
#
# Allowed:
#   'set +x' is fine (turning xtrace off).
# NOTE:
#   This gate flags ANY committed occurrence of enabling xtrace.
#   Keep debugging local; do not commit xtrace.

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

fail=0

targets="$(
  {
    git ls-files 'scripts/prove_ci.sh'
    git ls-files 'scripts/prove_*.sh'
    git ls-files 'scripts/gate_*.sh'
  } | awk 'NF' | sort -u
)"

if [[ -z "${targets}" ]]; then
  echo "OK: no targets found (nothing to scan)."
  exit 0
fi

# Match enabling xtrace:
#   set -x
#   set -euxo pipefail  (contains -x)
# Avoid matching set +x
pattern='^[[:space:]]*set([[:space:]]+[^#]*|[[:space:]]*)-x([[:space:]]|$)'

while IFS= read -r f; do
  if grep -nE "${pattern}" "$f" >/dev/null; then
    echo "ERROR: forbidden xtrace detected: $f"
    grep -nE "${pattern}" "$f" || true
    fail=1
  fi
done <<< "${targets}"

if [[ "$fail" -ne 0 ]]; then
  cat <<'EOF'

==> remediation
Remove 'set -x' from CI proof/gate scripts.
If you need debugging, prefer:
  - explicit echo statements of non-sensitive values, or
  - temporary local-only instrumentation (never committed).

EOF
  exit 1
fi

echo "OK: no forbidden 'set -x' found in prove/gate scripts."
