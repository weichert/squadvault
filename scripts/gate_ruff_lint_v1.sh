#!/usr/bin/env bash
set -euo pipefail
export LC_ALL=C

# Gate: ruff lint must be clean on the shipped source tree (v1).
#
# Why:
#   ruff's absence from the pre-commit chain is what let R1 land (10 lint
#   errors reached HEAD before CI caught them). This gate moves the same
#   check CI runs to commit time, so lint regressions are blocked locally.
#
# Scope:
#   src/squadvault/  (identical to .github/workflows/ci.yml "Lint" step;
#   Tests/ ruff is intentionally out of scope here).
#
# Determinism / Safety:
#   - repo-root anchored
#   - no network, no package installs, no xtrace
#   - ruff version is pinned in requirements.txt (E1.1, bf0833e)

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

echo "==> ruff lint gate"

if ! command -v ruff >/dev/null 2>&1; then
  echo "ERROR: ruff not found on PATH. Install pinned deps: pip install -r requirements.txt" >&2
  exit 1
fi

ruff check src/squadvault/
echo "OK: ruff lint clean (src/squadvault/)."
