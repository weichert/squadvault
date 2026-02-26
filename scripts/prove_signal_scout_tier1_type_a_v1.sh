#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." >/dev/null 2>&1 && pwd)"

echo "=== Proof: Signal Scout Tier-1 Type A invariants (v1) ==="
echo "    repo_root=${REPO_ROOT}"

# Run only the signal taxonomy Type A validation tests (canonical enforcement surface).
# SV_PATCH: pinned, git-tracked pytest list (avoid broad directory invocation)
  {
    # Bash-3-safe pinned, git-tracked pytest list.
    # We explicitly enumerate git-tracked Tests/validation/signals/test_*.py files
    # to prevent accidental surface expansion.
    ss_tests=()
    while IFS= read -r p; do
      ss_tests+=("$p")
    done < <(git ls-files 'Tests/validation/signals/test_*.py' | sort)

    if [ "${#ss_tests[@]}" -eq 0 ]; then
      echo "ERROR: no git-tracked Tests/validation/signals/test_*.py files found for Signal Scout Tier-1 proof" >&2
      exit 1
    fi

    # Intentional: unquoted array expansion so gate sees Tests/... as path token
# shellcheck disable=SC2068
"${REPO_ROOT}/scripts/py" -m pytest -q ${ss_tests[@]}
  }

# /SV_PATCH: pinned, git-tracked pytest list

echo "OK: Signal Scout Tier-1 Type A invariants proved (v1)"
