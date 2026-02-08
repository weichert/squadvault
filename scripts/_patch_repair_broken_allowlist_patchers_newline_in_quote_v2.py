from __future__ import annotations

import re
from pathlib import Path

OFFENDERS = [
    Path("scripts/_patch_allowlist_patch_wrapper_add_gate_ops_indices_no_autofill_placeholders_v1.py"),
    Path("scripts/_patch_allowlist_patch_wrapper_bulk_index_ci_guardrails_entrypoints_v1.py"),
    Path("scripts/_patch_allowlist_patch_wrapper_cleanup_ci_guardrails_ops_entrypoint_parity_iterations_v1.py"),
    Path("scripts/_patch_allowlist_patch_wrapper_docs_fill_ci_guardrails_autofill_descriptions_v1.py"),
    Path("scripts/_patch_allowlist_patch_wrapper_fix_awk_portability_ci_guardrails_ops_entrypoint_parity_v4.py"),
    Path("scripts/_patch_allowlist_patch_wrapper_sync_add_gate_patcher_ci_guardrails_ops_entrypoint_parity_v3.py"),
]

# Core corruption: (" <newline> ") or (' <newline> ')
PAREN_SPLIT_DQUOTE = re.compile(r'\(\s*"\s*\n\s*"\s*\)')
PAREN_SPLIT_SQUOTE = re.compile(r"\(\s*'\s*\n\s*'\s*\)")

def _apply(text: str) -> tuple[str, int]:
    changed = 0

    # Replace the split-quote newline token with explicit "\\n"
    text2, n1 = PAREN_SPLIT_DQUOTE.subn(r'("\\n")', text)
    changed += n1

    text3, n2 = PAREN_SPLIT_SQUOTE.subn(r"('\\n')", text2)
    changed += n2

    return text3, changed

def main() -> None:
    total_files = 0
    total_edits = 0

    for p in OFFENDERS:
        if not p.exists():
            raise SystemExit(f"ERROR: missing offender: {p}")

        src = p.read_text(encoding="utf-8")
        new_src, edits = _apply(src)

        if edits:
            p.write_text(new_src, encoding="utf-8")
            print(f"UPDATED: {p} (edits={edits})")
            total_files += 1
            total_edits += edits
        else:
            print(f"OK: {p} (no split-quote newline tokens detected)")

    print(f"DONE: files_updated={total_files} total_edits={total_edits}")

if __name__ == "__main__":
    main()
