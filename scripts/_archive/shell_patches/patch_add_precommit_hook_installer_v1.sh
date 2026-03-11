#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add pre-commit hook template + installer (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PATCHER="scripts/_patch_add_precommit_hook_installer_v1.py"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

echo "==> py_compile patcher"
${PY} -m py_compile "${PATCHER}"

echo "==> run patcher"
${PY} "${PATCHER}"

echo "==> chmod +x installer + hook template"
chmod +x scripts/install_git_hooks_v1.sh
chmod +x scripts/git-hooks/pre-commit_v1.sh

echo "==> bash -n"
bash -n scripts/install_git_hooks_v1.sh
bash -n scripts/git-hooks/pre-commit_v1.sh

echo "==> smoke: installer help (dry run install)"
bash scripts/install_git_hooks_v1.sh >/dev/null

echo "OK"
