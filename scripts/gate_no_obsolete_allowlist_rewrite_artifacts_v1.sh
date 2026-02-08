#!/usr/bin/env bash
set -euo pipefail

echo "=== Gate: no obsolete allowlist rewrite recovery artifacts (v1) ==="

# Canonical tools we allow to exist.
allow_exact=(
  "scripts/_patch_rewrite_allowlist_patchers_insert_sorted_no_eof_v2.py"
  "scripts/patch_rewrite_allowlist_patchers_insert_sorted_no_eof_v2.sh"
  "scripts/_patch_cleanup_allowlist_rewrite_recovery_artifacts_v1.py"
  "scripts/patch_cleanup_allowlist_rewrite_recovery_artifacts_v1.sh"
)

# Patterns we explicitly forbid from ever returning.
deny_globs=(
  "scripts/_patch_rewrite_allowlist_patchers_insert_sorted_no_eof_v1.py"
  "scripts/patch_rewrite_allowlist_patchers_insert_sorted_no_eof_v1.sh"
  "scripts/_patch_repair_broken_allowlist_patchers_newline_in_quote_v"*.py
  "scripts/patch_repair_broken_allowlist_patchers_newline_in_quote_v"*.sh
  "scripts/_patch_fix_rewrite_allowlist_no_eof_"*.py
  "scripts/patch_fix_rewrite_allowlist_no_eof_"*.sh
  "scripts/_patch_fix_no_eof_rewrite_template_literal_newlines_v"*.py
  "scripts/patch_fix_no_eof_rewrite_template_literal_newlines_v"*.sh
  "scripts/_patch_cleanup_"*shell_artifacts*.py
  "scripts/patch_cleanup_"*shell_artifacts*.sh
)

fail=0

# First: fail fast if any deny globs match.
for g in "${deny_globs[@]}"; do
  # compgen returns 0 if it matches at least one path
  if compgen -G "${g}" >/dev/null; then
    echo "ERROR: forbidden recovery artifact(s) present matching: ${g}"
    # print matches (best effort)
    for f in ${g}; do
      [[ -e "${f}" ]] && echo "  - ${f}"
    done
    fail=1
  fi
done

# Second: ensure canonical tools exist (defense-in-depth).
for f in "${allow_exact[@]}"; do
  if [[ ! -e "${f}" ]]; then
    echo "ERROR: expected canonical file missing: ${f}"
    fail=1
  fi
done

if [[ "${fail}" -ne 0 ]]; then
  echo "FAIL: obsolete allowlist rewrite recovery artifacts gate failed."
  exit 1
fi

echo "OK: no obsolete recovery artifacts; canonical tooling present."
