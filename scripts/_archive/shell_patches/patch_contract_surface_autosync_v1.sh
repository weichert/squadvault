#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: contract surface autosync (v1) ==="

cd "$(git rev-parse --show-toplevel)"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

PATCHER="scripts/_patch_contract_surface_autosync_v1.py"

# Run patcher (deterministic; no temp artifacts)
"${PY}" "${PATCHER}"

# bash -n any touched shell scripts (bash3-safe)
TOUCHED_SH="$(git diff --name-only --diff-filter=AM | LC_ALL=C sort | grep -E '^scripts/.*\.sh$' || true)"
if [[ -n "${TOUCHED_SH}" ]]; then
  echo "==> bash -n (touched .sh)"
  echo "${TOUCHED_SH}" | while IFS= read -r f; do
    [[ -z "${f}" ]] && continue
    bash -n "${f}"
  done
fi

echo "==> Smoke: prove_contract_surface_completeness_v1"

# The proof enforces "do not mutate / do not leave dirty".
# If autosync produced diffs (expected), run the smoke proof in a temporary worktree
# with a local temp commit so the proof sees a clean tree state.
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "==> Repo is dirty after autosync; running smoke proof in temp worktree (clean temp commit)"

  # Capture current changes (staged + unstaged) as patches
  TMP_DIR="$(mktemp -d -t sv_autosync_worktree.XXXXXX)"
  cleanup() {
    # Best-effort cleanup; avoid failing the wrapper on cleanup errors
    git worktree remove --force "${TMP_DIR}" >/dev/null 2>&1 || true
    rm -rf "${TMP_DIR}" >/dev/null 2>&1 || true
  }
  trap cleanup EXIT

  # Add a detached worktree at HEAD
  git worktree add --detach "${TMP_DIR}" HEAD >/dev/null

  # Apply staged changes first, then unstaged, into the temp worktree
  if ! git diff --cached --quiet; then
    git diff --cached | (cd "${TMP_DIR}" && git apply)
  fi
  if ! git diff --quiet; then
    git diff | (cd "${TMP_DIR}" && git apply)
  fi

  # Commit in temp worktree so proof sees clean state
  (
    cd "${TMP_DIR}"
    git add -A
    git -c user.name="squadvault-autosync" -c user.email="autosync@local" \
      commit -m "temp: contract surface autosync smoke (v1)" >/dev/null
    bash scripts/prove_contract_surface_completeness_v1.sh
  )

  echo "==> Smoke proof OK (temp worktree)"
else
  # If no diffs, we can run proof directly
  bash scripts/prove_contract_surface_completeness_v1.sh
fi

echo "OK: patch_contract_surface_autosync_v1 complete."
