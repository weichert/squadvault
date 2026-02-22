#!/usr/bin/env bash
set -euo pipefail

# === Gate: No network/package-manager actions in CI proofs (v1) ===
# Scope: scripts/{prove_,gate_,check_}*.sh
# Goal: prevent flake + env drift (network, installs, VCS fetches).
#
# NOTE: This is a conservative static scan. If a command is legitimately needed,
# it should be moved outside CI proof surfaces (or explicitly allowlisted in a future v2).

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${HERE}/.." && pwd)"
cd "${REPO_ROOT}"

echo "=== Gate: No network/package-manager actions in CI proofs (v1) ==="

# Forbidden patterns (word-boundary-ish, bash-safe)
# - Network fetch: curl/wget
# - VCS network ops: git clone/fetch/pull/submodule update (networked)
# - Package installs: pip/poetry/uv/npm/yarn/pnpm install, brew/apt/apk/dnf/yum install
# Keep this list small to avoid false positives.
PATTERN='(^|[[:space:];&(])('\
'curl[[:space:]]|'\
'wget[[:space:]]|'\
'git[[:space:]]+(clone|fetch|pull)[[:space:]]|'\
'git[[:space:]]+submodule[[:space:]]+update([[:space:]]|$)|'\
'pip3?[[:space:]]+install[[:space:]]|'\
'python3?[[:space:]]+-m[[:space:]]+pip[[:space:]]+install[[:space:]]|'\
'poetry[[:space:]]+install([[:space:]]|$)|'\
'uv[[:space:]]+pip[[:space:]]+install[[:space:]]|'\
'npm[[:space:]]+(ci|install)([[:space:]]|$)|'\
'yarn[[:space:]]+(install|add)([[:space:]]|$)|'\
'pnpm[[:space:]]+(install|add)([[:space:]]|$)|'\
'brew[[:space:]]+install[[:space:]]|'\
'apt(-get)?[[:space:]]+install[[:space:]]|'\
'apk[[:space:]]+add[[:space:]]|'\
'dnf[[:space:]]+install[[:space:]]|'\
'yum[[:space:]]+install[[:space:]]'\
')'

# Only scan proof/gate/check shells (not all scripts) to minimize noise.
# Exclude _retired.
if grep -RIn \
  --exclude-dir='_retired' \
  --include='prove_*.sh' \
  --include='gate_*.sh' \
  --include='check_*.sh' \
  -E "${PATTERN}" scripts ; then
  echo "FAIL: forbidden network/package-manager pattern detected in CI proof/gate/check scripts."
  echo "Move the behavior out of CI proof surfaces or refactor to a deterministic local-only step."
  exit 1
fi

echo "OK: no forbidden network/package-manager actions found in CI proof surfaces (v1)."
