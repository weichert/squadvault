#!/usr/bin/env bash
set -euo pipefail

# === Gate: Time & Timestamp Determinism (static scan) ===
# Policy: fail loud on unsafe wall-clock time usage and implicit local-time conversions.
# Escape hatch: add "SV_TIME_OK" on the same line to allow a deliberate exception.

# Repo root resolution:
# - Prefer git top-level (works from anywhere inside repo)
# - Fallback: script directory parent
if git_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  REPO_ROOT="${git_root}"
else
  SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
  REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
fi
cd "${REPO_ROOT}"

SCAN_DIRS=("src" "scripts")

# --- Precondition: expected scan directories must exist ---
for d in "${SCAN_DIRS[@]}"; do
  if [[ ! -d "${d}" ]]; then
    echo "ERROR: scan directory missing: ${d}" >&2
    exit 2
  fi
done
# --- /Precondition ---

EXCLUDE_DIRS=(
  ".venv"
  "venv"
  ".git"
  "__pycache__"
  ".mypy_cache"
  ".pytest_cache"
  "build"
  "dist"
  ".local"
  "docs/_import"
)

PRUNE_EXPR=()
for d in "${EXCLUDE_DIRS[@]}"; do
  PRUNE_EXPR+=( -path "*/${d}/*" -o )
done
PRUNE_EXPR+=( -false )

PATTERN='\
\bdatetime\.now\s*\(|\
\bdatetime\.utcnow\s*\(|\
\bdate\.today\s*\(|\
\btime\.time\s*\(|\
\btime\.localtime\s*\(|\
\btime\.strftime\s*\(|\
\btime\.mktime\s*\(|\
\bdatetime\.fromtimestamp\s*\(|\
\bdatetime\.timestamp\s*\(|\
\bos\.path\.getmtime\s*\(|\
\bPath\([^)]*\)\.stat\s*\(\)\.st_mtime\b|\
\bstat\s*\([^)]*\)\.st_mtime\b\
'

echo "=== Gate: Time & Timestamp Determinism (static scan) ==="

FOUND=0

while IFS= read -r file; do
  case "${file}" in
    *.py|*.sh) ;;
    *) continue ;;
  esac

  if grep -nE "${PATTERN}" "${file}" 2>/dev/null | grep -v 'SV_TIME_OK' >/dev/null; then
    if [ "${FOUND}" -eq 0 ]; then
      echo
      echo "ERROR: unsafe time/timestamp usage detected."
      echo "Add 'SV_TIME_OK' inline only for deliberate, reviewed exceptions."
      echo
    fi
    FOUND=1
    echo "--- ${file} ---"
    grep -nE "${PATTERN}" "${file}" 2>/dev/null | grep -v 'SV_TIME_OK' || true
    echo
  fi
done < <(
  find "${SCAN_DIRS[@]}" \
    \( "${PRUNE_EXPR[@]}" \) -prune -o \
    -type f -print
)

if [ "${FOUND}" -ne 0 ]; then
  echo "FAIL: Time & Timestamp Determinism gate."
  exit 1
fi

echo "OK: no unsafe time/timestamp patterns found."
