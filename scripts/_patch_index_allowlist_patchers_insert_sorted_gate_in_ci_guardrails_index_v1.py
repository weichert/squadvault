from __future__ import annotations

from pathlib import Path

INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
END = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

BULLET = "- scripts/gate_allowlist_patchers_must_insert_sorted_v1.sh — Enforce allowlist patchers insert wrappers in sorted order (v1)\n"

def main() -> None:
    if not INDEX.exists():
        raise SystemExit(f"ERROR: missing {INDEX}")

    text = INDEX.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        raise SystemExit("ERROR: bounded entrypoints markers missing; refuse")

    pre, rest = text.split(BEGIN, 1)
    bounded, post = rest.split(END, 1)

    if "scripts/gate_allowlist_patchers_must_insert_sorted_v1.sh" in bounded:
        print("OK: bullet already present in bounded section")
        return

    lines = bounded.splitlines(True)
    out: list[str] = []
    inserted = False

    # Insert near other allowlist/idempotence-related bullets if possible.
    for line in lines:
        out.append(line)
        if (not inserted) and "gate_patch_wrapper_idempotence_allowlist_v1.sh" in line:
            out.append(BULLET)
            inserted = True

    if not inserted:
        if not bounded.endswith("\n"):
            out.append("\n")
        out.append(BULLET)

    bounded_out = "".join(out)
    INDEX.write_text(pre + BEGIN + bounded_out + END + post, encoding="utf-8")
    print("UPDATED:", INDEX)

if __name__ == "__main__":
    main()
