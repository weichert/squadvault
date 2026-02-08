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

# The specific break you showed:
#   out.append(f'  "{w}"
# (i.e., f' ... "{w}" <newline> ' )
SPLIT_W_QUOTED_SQ = re.compile(r'(out\.append\()\s*f\'([^\']*"\{w\})\s*\n\s*\'\s*(\))')
SPLIT_W_QUOTED_DQ = re.compile(r'(out\.append\()\s*f"([^"]*\"\{w\})\s*\n\s*"\s*(\))')

# Generic split f-string where the opening quote and closing quote are on different lines:
#   f" ... {m} <newline> "   or   f' ... {m} <newline> '
SPLIT_F_DQ = re.compile(r'(out\.append\()\s*f"([^"\n]*\{[mw]\}[^"\n]*)\s*\n\s*"\s*(\))')
SPLIT_F_SQ = re.compile(r"(out\.append\()\s*f'([^'\n]*\{[mw]\}[^'\n]*)\s*\n\s*'\s*(\))")

def _apply(text: str) -> tuple[str, int]:
    changed = 0
    out = text

    # 1) Fix the quoted-{w} variant by injecting \n\n (this is what the template intended)
    def _repl_w_sq(m: re.Match) -> str:
        nonlocal changed
        changed += 1
        return f"{m.group(1)}f'{m.group(2)}\\\\n\\\\n'{m.group(3)}"

    def _repl_w_dq(m: re.Match) -> str:
        nonlocal changed
        changed += 1
        return f'{m.group(1)}f"{m.group(2)}\\\\n\\\\n"{m.group(3)}'

    out2 = SPLIT_W_QUOTED_SQ.sub(_repl_w_sq, out)
    out3 = SPLIT_W_QUOTED_DQ.sub(_repl_w_dq, out2)
    out = out3

    # 2) Generic split f-strings: assume they wanted a single newline
    def _repl_generic_dq(m: re.Match) -> str:
        nonlocal changed
        changed += 1
        return f'{m.group(1)}f"{m.group(2)}\\\\n"{m.group(3)}'

    def _repl_generic_sq(m: re.Match) -> str:
        nonlocal changed
        changed += 1
        return f"{m.group(1)}f'{m.group(2)}\\\\n'{m.group(3)}"

    out2 = SPLIT_F_DQ.sub(_repl_generic_dq, out)
    out3 = SPLIT_F_SQ.sub(_repl_generic_sq, out2)
    out = out3

    return out, changed

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
            print(f"OK: {p} (no split-f-string patterns detected)")

    print(f"DONE: files_updated={files_updated} total_edits={total_edits}")

if __name__ == "__main__":
    main()
