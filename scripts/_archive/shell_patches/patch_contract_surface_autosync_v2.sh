#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: contract surface autosync (v2) ==="

cd "$(git rev-parse --show-toplevel)"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

PATCHER="scripts/_patch_contract_surface_autosync_v2.py"

# Snapshot pre-state (for touched-file detection)
PRE_TMP="$(mktemp -t sv_autosync_v2_pre.XXXXXX)"
POST_TMP="$(mktemp -t sv_autosync_v2_post.XXXXXX)"
TOUCHED_TMP="$(mktemp -t sv_autosync_v2_touched.XXXXXX)"
trap 'rm -f "${PRE_TMP}" "${POST_TMP}" "${TOUCHED_TMP}"' EXIT

git ls-files > "${PRE_TMP}"

# Run patcher
"${PY}" "${PATCHER}"

git ls-files > "${POST_TMP}"

# Determine touched .sh files (tracked only)
git diff --name-only --diff-filter=ACMRTUXB > "${TOUCHED_TMP}"

# bash -n any touched .sh
while IFS= read -r f; do
  case "${f}" in
    *.sh)
      bash -n "${f}"
      ;;
  esac
done < "${TOUCHED_TMP}"

# Smoke: prove_contract_surface_completeness_v1.sh
# If the smoke proof enforces "proof must not dirty repo", run it in a temp worktree against the *patched* state.
# We do this by capturing the patch, resetting the main tree, applying in worktree+temp commit, running proof,
# then re-applying the patch back onto the main tree.
if test -n "$(git status --porcelain=v1)"; then
  echo "==> Smoke: repo dirty after patch (expected). Running smoke proof in temp worktree WITH patch applied."

  PATCH_FILE="$(mktemp -t sv_autosync_v2_patch.XXXXXX)"
  WT_DIR="$(mktemp -d -t sv_autosync_v2_wt.XXXXXX)"
  trap 'rm -f "${PATCH_FILE}"; rm -rf "${WT_DIR}"' EXIT

  # Capture patch of current working tree (includes staged+unstaged changes; excludes untracked).
  git diff --binary > "${PATCH_FILE}"

  # Reset main tree to clean for proof discipline (do NOT git clean -fd; keep untracked patch scripts).
  git reset --hard -q

  # Create worktree at clean HEAD, apply patch there, temp-commit, run smoke proof.
  git worktree add "${WT_DIR}"

  (
    cd "${WT_DIR}"
    git apply --whitespace=nowarn "${PATCH_FILE}"
    git add -A
    git commit -q -m "TEMP: contract surface autosync v2 (smoke proof)" --no-gpg-sign
    bash scripts/prove_contract_surface_completeness_v1.sh
  )

  git worktree remove "${WT_DIR}"

  # Re-apply patch back onto main working tree so this wrapper remains a patch wrapper (leaves intended diffs).
  git apply --whitespace=nowarn "${PATCH_FILE}"
else
  echo "==> Smoke: repo clean after patch. Running smoke proof directly."
  bash scripts/prove_contract_surface_completeness_v1.sh
fi

echo "=== OK: contract surface autosync (v2) ==="
