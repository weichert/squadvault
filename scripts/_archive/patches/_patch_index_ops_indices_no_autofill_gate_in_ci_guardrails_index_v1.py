from __future__ import annotations

from pathlib import Path

INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
END = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

BULLET = "- scripts/gate_ops_indices_no_autofill_placeholders_v1.sh — Enforce Ops indices contain no autofill placeholders (v1)\n"

def main() -> None:
    if not INDEX.exists():
        raise SystemExit(f"ERROR: missing {INDEX}")

    text = INDEX.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        raise SystemExit("ERROR: bounded entrypoints markers missing; refuse")

    pre, rest = text.split(BEGIN, 1)
    bounded, post = rest.split(END, 1)

    if "scripts/gate_ops_indices_no_autofill_placeholders_v1.sh" in bounded:
        print("OK: bullet already present in bounded section")
        return

    # Insert after the parity gate bullet (keeps this section coherent)
    lines = bounded.splitlines(True)
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if (not inserted) and "gate_ci_guardrails_ops_entrypoint_parity_v1.sh" in line:
            out.append(BULLET)
            inserted = True

    if not inserted:
        # Fallback: append before END within bounded section
        if not bounded.endswith("\n"):
            bounded += "\n"
        out = [bounded, BULLET]

    bounded_out = "".join(out)
    new_text = pre + BEGIN + bounded_out + END + post
    INDEX.write_text(new_text, encoding="utf-8")
    print("UPDATED:", INDEX)

if __name__ == "__main__":
    main()
