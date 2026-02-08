from __future__ import annotations

from pathlib import Path

DOC = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

BEGIN = "<!-- SV_TERMINAL_BANNER_GATE_ENTRY_v1_BEGIN -->"
END = "<!-- SV_TERMINAL_BANNER_GATE_ENTRY_v1_END -->"

PROOF_LINE = "- scripts/prove_no_terminal_banner_paste_gate_behavior_v1.sh — Proof: terminal banner paste gate behavior (v1)\n"

def main() -> None:
    if not DOC.exists():
        raise SystemExit(f"ERROR: missing doc: {DOC}")

    text = DOC.read_text(encoding="utf-8")
    if PROOF_LINE.strip() in text:
        print("OK: terminal banner proof runner already present in Ops index (idempotent).")
        return

    b = text.find(BEGIN)
    e = text.find(END)
    if b == -1 or e == -1 or e < b:
        raise SystemExit("ERROR: could not locate terminal banner gate bounded section markers in Ops index.")

    section = text[b:e]

    # Insert proof runner line inside the bounded section, ideally near the gate entry.
    # Strategy:
    #  - If the canonical gate bullet exists, insert immediately after it.
    #  - Else insert just before END marker (within section).
    gate_bullet = "- scripts/gate_no_terminal_banner_paste_v1.sh"
    insert_at = None

    lines = section.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.strip().startswith(gate_bullet):
            insert_at = i + 1
            break

    if insert_at is None:
        # Place near end of the section (but before trailing blank lines).
        insert_at = len(lines)
        while insert_at > 0 and lines[insert_at - 1].strip() == "":
            insert_at -= 1

    # Ensure there is exactly one blank line separating if needed (keep it simple/stable).
    new_lines = lines[:insert_at] + [PROOF_LINE] + lines[insert_at:]

    new_section = "".join(new_lines)
    new_text = text[:b] + new_section + text[e:]

    DOC.write_text(new_text, encoding="utf-8")
    print("OK: inserted terminal banner proof runner into Ops index bounded section.")

if __name__ == "__main__":
    main()
