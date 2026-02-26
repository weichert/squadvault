from __future__ import annotations

from pathlib import Path

REG = Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md")

BEGIN = "<!-- CI_PROOF_RUNNERS_BEGIN -->"
END   = "<!-- CI_PROOF_RUNNERS_END -->"

NEEDLE = "scripts/prove_ci_creative_sharepack_if_available_v1.sh"
BULLET = "- scripts/prove_ci_creative_sharepack_if_available_v1.sh — Proof runner (CI): creative sharepack determinism if inputs present (v1)"

def main() -> None:
    text = REG.read_text(encoding="utf-8")

    b_ct = text.count(BEGIN)
    e_ct = text.count(END)
    if b_ct != 1 or e_ct != 1:
        raise SystemExit(f"ERR: expected exactly one CI_PROOF_RUNNERS block: BEGIN={b_ct} END={e_ct}")

    b_i = text.find(BEGIN)
    e_i = text.find(END)
    if not (0 <= b_i < e_i):
        raise SystemExit("ERR: CI_PROOF_RUNNERS markers out of order")

    block_start = b_i + len(BEGIN)
    block = text[block_start:e_i]

    if NEEDLE in block:
        print("OK: CI_PROOF_RUNNERS already contains creative sharepack proof (noop)")
        return

    # Insert inside the bounded block, near other creative proofs if possible.
    # Prefer after prove_creative_determinism_v1.sh; else append before END.
    anchor = "scripts/prove_creative_determinism_v1.sh"
    ins = block.find(anchor)
    if ins != -1:
        # insert after the anchor line
        line_end = block.find("\n", ins)
        if line_end == -1:
            line_end = len(block)
        line_end += 1
        new_block = block[:line_end] + BULLET + "\n" + block[line_end:]
    else:
        # append at end of block (ensure trailing newline)
        new_block = block
        if not new_block.endswith("\n"):
            new_block += "\n"
        new_block = new_block + BULLET + "\n"

    new = text[:block_start] + new_block + text[e_i:]
    if new == text:
        print("OK: registry already canonical (noop)")
        return

    REG.write_text(new, encoding="utf-8")
    print("OK: added creative sharepack proof to CI_PROOF_RUNNERS block (v1)")

if __name__ == "__main__":
    main()
