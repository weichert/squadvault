#!/usr/bin/env bash
set -euo pipefail

# CI Cleanliness & Determinism Guardrail (v1)
# Fails loudly if the git working tree is not clean (tracked or untracked).
# No cleanup. No masking. Summary is explicit and actionable.

PHASE="${1:-}"
if [[ "${PHASE}" == "--phase" ]]; then
  PHASE="${2:-}"
fi
PHASE="${PHASE:-unknown}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

if ! command -v git >/dev/null 2>&1; then
  echo "ERROR: git is required for repo cleanliness guardrail." >&2
  exit 2
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: not inside a git work tree (repo_root: ${REPO_ROOT})." >&2
  exit 2
fi

# We intentionally treat *any* porcelain output as failure.
# This catches:
# - modified tracked files
# - staged changes
# - deletions
# - untracked files (which can mask "works on my machine" bugs)
STATUS="$(git status --porcelain=v1)"

if [[ -z "${STATUS}" ]]; then
  echo "OK: repo cleanliness (${PHASE}): clean"
  exit 0
fi

echo "ERROR: repo cleanliness (${PHASE}): working tree is DIRTY"
echo
echo "==> git status --porcelain=v1"
echo "${STATUS}"
echo

# Tracked diffs (if any)
echo "==> tracked diff (name-status)"
git diff --name-status || true
echo

echo "==> tracked diff (stat)"
git diff --stat || true
echo

# Staged diffs (if any)
echo "==> staged diff (name-status)"
git diff --cached --name-status || true
echo

echo "==> staged diff (stat)"
git diff --cached --stat || true
echo

echo "==> hint: recovery workflow"
cat <<'EOF'
1) Inspect:
   git status

2) If you want to discard ALL tracked changes (worktree + index):
   git restore --staged --worktree -- .

3) If untracked files exist and you want to remove them (DESTRUCTIVE):
   git clean -fd

4) Re-run the proof from a clean repo:
   ./scripts/prove_ci.sh
EOF

exit 1
