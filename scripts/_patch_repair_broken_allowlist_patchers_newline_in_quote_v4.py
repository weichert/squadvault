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

# Core corruption: f"{m}<newline>" or f"{w}<newline>" (and single-quote variants)
F_M_DQ = re.compile(r'f"\{m\}\s*\n\s*"')
F_M_SQ = re.compile(r"f'\{m\}\s*\n\s*'")
F_W_DQ = re.compile(r'f"\{w\}\s*\n\s*"')
F_W_SQ = re.compile(r"f'\{w\}\s*\n\s*'")

def _apply(text: str) -> tuple[str, int]:
    changed = 0

    text2, n = F_M_DQ.subn(r'f"{m}\\n"', text)
    changed += n
    text3, n = F_M_SQ.subn(r"f'{m}\\n'", text2)
    changed += n

    text4, n = F_W_DQ.subn(r'f"{w}\\n"', text3)
    changed += n
    text5, n = F_W_SQ.subn(r"f'{w}\\n'", text4)
    changed += n

    return text5, changed

def main() -> None:
    files_updated = 0
    total_edits = 0

    for p in OFFENDERS:
        if not p.exists():
            raise SystemExit(f"ERROR: missing offender: {p}")

        src = p.read_text(encoding="utf-8")
        new_src, edits = _apply(src)

        if edits:
            p.write_text(new_src, encoding="utf-8")
            print(f"UPDATED: {p} (edits={edits})")
            files_updated += 1
            total_edits += edits
        else:
            print(f"OK: {p} (no split f-string tokens detected)")

    print(f"DONE: files_updated={files_updated} total_edits={total_edits}")

if __name__ == "__main__":
    main()
