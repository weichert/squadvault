from __future__ import annotations

from pathlib import Path

INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
END = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

MARKER = "<!-- SV_RIVALRY_CHRONICLE_CONTRACT_LINKAGE: v1 -->"
BULLET = "- scripts/gate_rivalry_chronicle_contract_linkage_v1.sh — Rivalry Chronicle contract doc linkage gate (v1)"

ANCHOR_LINE_SUBSTR = "scripts/gate_rivalry_chronicle_output_contract_v1.sh"

def main() -> None:
    if not INDEX.exists():
        raise SystemExit(f"REFUSE: missing {INDEX}")
    text = INDEX.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        raise SystemExit("REFUSE: bounded section markers missing")

    pre, rest = text.split(BEGIN, 1)
    mid, post = rest.split(END, 1)

    if BULLET in mid:
        if MARKER not in mid:
            mid = mid.replace(BULLET, MARKER + "\n" + BULLET, 1)
            INDEX.write_text(pre + BEGIN + mid + END + post, encoding="utf-8")
            print("OK: added marker for existing bullet (v1).")
        else:
            print("OK: ops index already contains linkage gate bullet (v1 idempotent).")
        return

    lines = mid.splitlines()
    out = []
    inserted = False
    for ln in lines:
        out.append(ln)
        if (not inserted) and (ANCHOR_LINE_SUBSTR in ln):
            out.append(MARKER)
            out.append(BULLET)
            inserted = True

    if not inserted:
        raise SystemExit("REFUSE: could not find anchor line for Rivalry Chronicle output contract gate in bounded section")

    new_mid = "\n".join(out) + ("\n" if mid.endswith("\n") else "")
    INDEX.write_text(pre + BEGIN + new_mid + END + post, encoding="utf-8")
    print("OK: added ops index discoverability bullet for RC contract linkage gate (v1).")

if __name__ == "__main__":
    main()
