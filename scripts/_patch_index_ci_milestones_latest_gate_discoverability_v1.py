from __future__ import annotations

from pathlib import Path
import sys

IDX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
END   = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

BULLET = "- scripts/gate_ci_milestones_latest_block_v1.sh — Enforce CI_MILESTONES.md has exactly one bounded ## Latest block (v1)"

def main() -> None:
    text = IDX.read_text(encoding="utf-8")

    b_ct = text.count(BEGIN)
    e_ct = text.count(END)
    if b_ct != 1 or e_ct != 1:
        raise SystemExit(f"ERR: expected exactly one bounded entrypoints block: BEGIN={b_ct} END={e_ct}")

    if BULLET in text:
        print("OK: CI milestones Latest gate already indexed in bounded entrypoints block (noop)")
        return

    b_i = text.find(BEGIN)
    e_i = text.find(END)
    if not (0 <= b_i < e_i):
        raise SystemExit("ERR: entrypoints markers out of order")

    before = text[:e_i]
    after = text[e_i:]

    # Insert immediately before END, without reordering any existing bullets.
    if not before.endswith("\n"):
        before += "\n"
    new = before + BULLET + "\n" + after

    if new == text:
        print("OK: no changes needed (noop)")
        return

    IDX.write_text(new, encoding="utf-8")
    print("OK: indexed CI milestones Latest gate inside bounded entrypoints block")

if __name__ == "__main__":
    main()
