#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: allow tracking CI guardrails index patchers (v1) ==="

# Resolve repo root
if git_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  cd "${git_root}"
else
  echo "ERROR: not inside git repo" >&2
  exit 2
fi

# Patchers we want tracked (even if scripts/_patch_*.py is ignored by default)
PATCHERS=(
  "scripts/_patch_ci_guardrails_index_add_time_and_fs_v1.py"
  "scripts/_patch_ci_guardrails_index_fix_env_bullet_v1.py"
)

# Ensure .gitignore exists
touch .gitignore

changed=0

# Add unignore lines (idempotent)
for p in "${PATCHERS[@]}"; do
  unignore="!${p}"
  if ! grep -qF -- "${unignore}" .gitignore; then
    echo "${unignore}" >> .gitignore
    echo "OK: added to .gitignore: ${unignore}"
    changed=1
  else
    echo "OK: .gitignore already contains: ${unignore}"
  fi
done

# Ensure patchers exist and stage them (force-add in case ignore still matches)
for p in "${PATCHERS[@]}"; do
  if [[ ! -f "${p}" ]]; then
    echo "ERROR: patcher not found: ${p}" >&2
    exit 2
  fi
done

git add .gitignore
git add -f "${PATCHERS[@]}"

# Commit only if staging produced changes
if git diff --cached --quiet; then
  echo "OK: nothing to commit (already allowlisted + tracked)"
else
  git commit -m "Ops: allowlist CI guardrails index patchers (v1)"
  echo "OK: committed"
fi

echo "==> git status (porcelain)"
git status --porcelain=v1
echo "OK"
