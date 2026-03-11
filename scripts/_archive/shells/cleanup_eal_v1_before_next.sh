#!/usr/bin/env bash
set -euo pipefail

echo "=== Cleanup: EAL v1 repo hygiene (pre-next-step) ==="
bash -n "$0"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

echo
echo "== git status (before) =="
git status --porcelain=v1 || true

is_tracked() {
  # Exit 0 if tracked, 1 if not
  git ls-files --error-unmatch "$1" >/dev/null 2>&1
}

remove_path() {
  local p="$1"
  if [ ! -e "$p" ]; then
    return 0
  fi

  if is_tracked "$p"; then
    git rm -f "$p" >/dev/null
    echo "GIT_RM: $p"
  else
    rm -f "$p"
    echo "RM:     $p"
  fi
}

echo
echo "== removing exploratory patch scripts (tracked -> git rm, untracked -> rm) =="

TO_DELETE=(
  scripts/patch_fix_eal_insertion_v1.sh
  scripts/patch_fix_get_recap_run_trace_newline_v1.sh
  scripts/patch_fix_persist_eal_to_recap_runs_v1.sh
  scripts/patch_fix_persist_eal_to_recap_runs_v2.sh
  scripts/patch_fix_persist_eal_to_recap_runs_v3.sh
  scripts/patch_get_recap_run_trace_optional_eal_v1.sh
  scripts/patch_persist_eal_directive_payload_v1.sh
  scripts/patch_persist_eal_to_recap_runs_v1.sh
  scripts/patch_dedupe_persist_eal_to_recap_runs_v1.sh
)

for f in "${TO_DELETE[@]}"; do
  remove_path "$f"
done

echo
echo "== staging canonical EAL v1 artifacts =="

TO_ADD=(
  src/squadvault/core_engine
  src/squadvault/core/storage/schema.sql
  src/squadvault/recaps/weekly_recap_lifecycle.py
  Tests/test_editorial_attunement_v1.py
  Tests/test_recap_runs_eal_persistence_v1.py
  Tests/test_get_recap_run_trace_optional_eal_v1.py
  scripts/patch_add_editorial_attunement_layer_v1.sh
  scripts/patch_wire_eal_v1_safe.sh
  scripts/patch_schema_add_recap_runs_eal_v1.sh
  scripts/cleanup_eal_v1_before_next.sh
)

for f in "${TO_ADD[@]}"; do
  if [ -e "$f" ]; then
    git add "$f"
    echo "ADD: $f"
  else
    echo "WARN: missing expected path (skipping): $f"
  fi
done

echo
echo "== verify: shell syntax guard =="
./scripts/check_shell_syntax.sh

echo
echo "== verify: pytest (quiet) =="
python="${PYTHON:-python}"
PYTHONPATH=src "$python" -m pytest -q

echo
echo "== verify: golden path proof mode =="
./scripts/prove_golden_path.sh

echo
echo "== git status (after stage) =="
git status --porcelain=v1 || true

if git diff --cached --quiet; then
  echo "OK: nothing staged; no commit created."
  exit 0
fi

msg="${1:-Core Engine: Editorial Attunement Layer v1 (directive + persistence + trace contract)}"
echo
echo "== committing =="
echo "message: $msg"
git commit -m "$msg"

echo
echo "OK: cleanup complete."
echo "Next: git push origin main"
