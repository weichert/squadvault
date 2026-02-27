#!/usr/bin/env bash
set -euo pipefail

# REPO_CLEAN_AFTER_PROOFS_V1
# Enforce: repo must be clean at end of CI proofs.

repo_root="$(
  cd "$(dirname "$0")/.." >/dev/null 2>&1
  pwd
)"

cd "${repo_root}"

if ! command -v git >/dev/null 2>&1; then
  echo "ERROR: git not found; cannot check repo cleanliness" >&2
  exit 2
fi

dirty="$(git status --porcelain=v1 2>/dev/null || true)"
if [[ -n "${dirty}" ]]; then
  echo "ERROR: repo not clean after proofs" >&2
  echo "${dirty}" >&2
  exit 2
fi

echo "OK: repo clean after proofs."
