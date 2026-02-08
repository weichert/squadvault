from __future__ import annotations

from pathlib import Path

# We intentionally KEEP the canonical v2 rewrite tooling.
KEEP = {
    "scripts/_patch_rewrite_allowlist_patchers_insert_sorted_no_eof_v2.py",
    "scripts/patch_rewrite_allowlist_patchers_insert_sorted_no_eof_v2.sh",
}

# Explicit deletions: only files created during the recovery session(s).
REMOVE = [
    # early/failed rewrite attempts
    "scripts/_patch_rewrite_allowlist_patchers_insert_sorted_no_eof_v1.py",
    "scripts/patch_rewrite_allowlist_patchers_insert_sorted_no_eof_v1.sh",

    # template/braces/extractor fixes (obsolete once v2 template moved to sentinel replacement)
    "scripts/_patch_fix_rewrite_allowlist_no_eof_template_braces_v1.py",
    "scripts/patch_fix_rewrite_allowlist_no_eof_template_braces_v1.sh",
    "scripts/_patch_fix_rewrite_allowlist_no_eof_template_braces_v2.py",
    "scripts/patch_fix_rewrite_allowlist_no_eof_template_braces_v2.sh",
    "scripts/_patch_fix_rewrite_allowlist_no_eof_template_allow_braces_v1.py",
    "scripts/patch_fix_rewrite_allowlist_no_eof_template_allow_braces_v1.sh",
    "scripts/_patch_fix_rewrite_allowlist_no_eof_extractor_v1.py",
    "scripts/patch_fix_rewrite_allowlist_no_eof_extractor_v1.sh",
    "scripts/_patch_fix_no_eof_rewrite_template_literal_newlines_v1.py",
    "scripts/patch_fix_no_eof_rewrite_template_literal_newlines_v1.sh",

    # repair series (v1..v5) and wrappers
    "scripts/_patch_repair_broken_allowlist_patchers_newline_in_quote_v1.py",
    "scripts/patch_repair_broken_allowlist_patchers_newline_in_quote_v1.sh",
    "scripts/_patch_repair_broken_allowlist_patchers_newline_in_quote_v2.py",
    "scripts/patch_repair_broken_allowlist_patchers_newline_in_quote_v2.sh",
    "scripts/_patch_repair_broken_allowlist_patchers_newline_in_quote_v3.py",
    "scripts/patch_repair_broken_allowlist_patchers_newline_in_quote_v3.sh",
    "scripts/_patch_repair_broken_allowlist_patchers_newline_in_quote_v4.py",
    "scripts/patch_repair_broken_allowlist_patchers_newline_in_quote_v4.sh",
    "scripts/_patch_repair_broken_allowlist_patchers_newline_in_quote_v5.py",
    "scripts/patch_repair_broken_allowlist_patchers_newline_in_quote_v5.sh",

    # cleanup helpers created during the incident
    "scripts/_patch_cleanup_accidental_shell_artifacts_v1.py",
    "scripts/patch_cleanup_accidental_shell_artifacts_v1.sh",
    "scripts/_patch_cleanup_more_shell_artifacts_v1.py",
    "scripts/patch_cleanup_more_shell_artifacts_v1.sh",
]

def main() -> None:
    repo_root = Path(".").resolve()

    # Safety: refuse if KEEP paths are missing.
    missing_keep = [p for p in sorted(KEEP) if not Path(p).exists()]
    if missing_keep:
        raise SystemExit("ERROR: expected KEEP files missing:\n" + "\n".join(missing_keep))

    # Apply deletions (idempotent).
    removed = 0
    missing = 0
    for rel in REMOVE:
        if rel in KEEP:
            raise SystemExit(f"ERROR: REMOVE includes KEEP file: {rel}")
        p = Path(rel)
        if p.exists():
            p.unlink()
            print(f"REMOVED: {rel}")
            removed += 1
        else:
            print(f"OK: already absent: {rel}")
            missing += 1

    # Extra safety: ensure we did not delete anything outside scripts/
    # (All paths above are scripts/*; enforce that.)
    for rel in REMOVE:
        if not rel.startswith("scripts/"):
            raise SystemExit(f"ERROR: non-scripts path in REMOVE list: {rel}")

    print(f"DONE: removed={removed} already_absent={missing}")
    print(f"KEEP: {', '.join(sorted(KEEP))}")

if __name__ == "__main__":
    main()
