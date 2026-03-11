#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: .gitignore allowlist post-hardening tidy patchers (v1) ==="
python="${PYTHON:-python}"

./scripts/py scripts/_patch_gitignore_allow_post_pytest_surface_hardening_tidy_patchers_v1.py

echo "==> verify allowlist lines present"
grep -n '^\!scripts/_patch_gitignore_allow_post_pytest_surface_hardening_tidy_patchers_v1\.py$' .gitignore >/dev/null
grep -n '^\!scripts/_patch_docs_add_golden_path_pytest_pinning_index_v1\.py$' .gitignore >/dev/null
grep -n '^\!scripts/_patch_deprecate_obsolete_golden_path_patchers_v1\.py$' .gitignore >/dev/null
grep -n '^\!scripts/_patch_prove_golden_path_add_pinned_note_v1\.py$' .gitignore >/dev/null
echo "OK"
