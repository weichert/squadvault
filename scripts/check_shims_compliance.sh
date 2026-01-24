#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_SCRIPTS_DIR="$REPO_ROOT/scripts"


FIX=0
if [[ "${1:-}" == "--fix" ]]; then
  FIX=1
fi

# Files we consider "operator surface area"
# - shell scripts in "$TARGET_SCRIPTS_DIR"/
# - executable wrappers in "$TARGET_SCRIPTS_DIR"/
# Exclude patchers and this checker itself.
files() {
  # shell scripts
  find "$TARGET_SCRIPTS_DIR" -maxdepth 1 -type f -name "*.sh" -print
  # include recap.py? it's invoked via recap.sh, but operator-facing help text lives here.
  # We'll include it but allow an ignore exception below if needed.
  find "$TARGET_SCRIPTS_DIR" -maxdepth 1 -type f -name "recap.py" -print
  # any other top-level scripts without extension that are meant to be run (e.g. "$TARGET_SCRIPTS_DIR"/py, "$TARGET_SCRIPTS_DIR"/recap.sh already covered)
  find "$TARGET_SCRIPTS_DIR" -maxdepth 1 -type f ! -name "*.*" -print
}

is_excluded() {
  case "$1" in
    "$TARGET_SCRIPTS_DIR"/check_shims_compliance.sh) return 0 ;;
    "$TARGET_SCRIPTS_DIR"/_patch_*.py) return 0 ;;
  esac
  return 1
}

collect_targets() {
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    if is_excluded "$f"; then
      continue
    fi
    echo "$f"
  done < <(files | sort -u)
}

if [[ "${FIX}" == "1" ]]; then
  echo "== Shim compliance (fix mode) =="
  ./scripts/py "$TARGET_SCRIPTS_DIR"/_patch_operator_scripts_use_shims_v1.py || true
  ./scripts/py "$TARGET_SCRIPTS_DIR"/_patch_examples_use_shims_v1.py || true
  echo
fi

fail=0

targets="$(collect_targets)"

# 1) Disallow PYTHONPATH=src python usage
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  echo "ERROR: shim violation (PYTHONPATH=src python): $line" >&2
  fail=1
done < <(grep -nH -E "PYTHONPATH=src python" $targets 2>/dev/null || true)

# 2) Disallow direct recap.py invocation
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  echo "ERROR: shim violation (./scripts/recap.py): $line" >&2
  fail=1
done < <(grep -nH -E "\./scripts/recap\.py " $targets 2>/dev/null || true)

# 3) Warn on hardcoded python paths (not fatal)
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  echo "WARN: hardcoded python path found (consider replacing with "$TARGET_SCRIPTS_DIR"/py): $line" >&2
done < <(grep -nH -E "/opt/anaconda3/bin/python" $targets 2>/dev/null || true)

if [[ "${fail}" != "0" ]]; then
  if [[ "${FIX}" == "1" ]]; then
    echo "ERROR: shim compliance still failing after --fix" >&2
  fi
  exit 2
fi

echo "OK: shim compliance check passed"
