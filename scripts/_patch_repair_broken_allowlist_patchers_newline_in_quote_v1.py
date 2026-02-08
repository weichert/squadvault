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

# Fix common corruptions caused by accidental literal newlines inside quoted strings.
# We keep this intentionally narrow and explicit to avoid unintended edits.
FIXES: list[tuple[re.Pattern[str], str]] = [
    # line.rstrip(" <newline> )   -> line.rstrip("\\n")
    (re.compile(r'(\.rstrip\()"\s*\n\s*(\)\s*)'), r'\1"\\n"\2'),
    # line.endswith(" <newline> ) -> line.endswith("\\n")
    (re.compile(r'(\.endswith\()"\s*\n\s*(\)\s*)'), r'\1"\\n"\2'),
    # group( " <newline> ) / group(" <newline> ) edge cases
    (re.compile(r'(\.group\()"\s*\n\s*(\)\s*)'), r'\1"\\n"\2'),
    # replace(" <newline> , ...) -> replace("\\n", ...)
    (re.compile(r'(\.replace\()"\s*\n\s*(,\s*)'), r'\1"\\n"\2'),
    # Generic: (" <newline> )  -> ("\\n")
    (re.compile(r'\("\s*\n\s*\)'), r'("\\n")'),
]

def _apply(text: str) -> tuple[str, int]:
    changed = 0
    out = text
    for pat, repl in FIXES:
        out2, n = pat.subn(repl, out)
        if n:
            changed += n
        out = out2
    return out, changed

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
            print(f"OK: {p} (no newline-in-quote artifacts detected)")

    print(f"DONE: files_updated={total_files} total_edits={total_edits}")

if __name__ == "__main__":
    main()
