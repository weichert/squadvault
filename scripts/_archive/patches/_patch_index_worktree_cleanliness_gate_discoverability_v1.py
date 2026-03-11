from __future__ import annotations

from pathlib import Path

IDX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

MARK = "<!-- SV_CI_WORKTREE_CLEANLINESS: v1 -->\n"
BULLET = "- scripts/gate_worktree_cleanliness_v1.sh — Worktree cleanliness: proofs must not mutate repo state (per-proof + end-of-run) (v1)\n"

def main() -> None:
    if not IDX.exists():
        raise SystemExit(f"ERROR: missing {IDX}")

    text = IDX.read_text(encoding="utf-8")

    if MARK in text and BULLET in text:
        return

    # Prefer inserting into the already-existing bounded "CI guardrails entrypoints" section if present.
    begin = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
    end = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

    if begin in text and end in text:
        pre, rest = text.split(begin, 1)
        block, post = rest.split(end, 1)
        if MARK in block:
            # marker exists but bullet missing (or vice versa)
            if MARK not in block:
                block = MARK + block
            if BULLET not in block:
                # insert near top after any header lines
                lines = block.splitlines(keepends=True)
                # find first bullet line or end
                ins = 0
                for i, line in enumerate(lines):
                    if line.lstrip().startswith("- "):
                        ins = i
                        break
                    ins = i + 1
                lines.insert(ins, MARK)
                lines.insert(ins + 1, BULLET)
                block = "".join(lines)
        else:
            # insert near the top of the bounded block
            lines = block.splitlines(keepends=True)
            ins = 0
            for i, line in enumerate(lines):
                if line.lstrip().startswith("- "):
                    ins = i
                    break
                ins = i + 1
            lines.insert(ins, MARK)
            lines.insert(ins + 1, BULLET)
            block = "".join(lines)

        new_text = pre + begin + block + end + post
        IDX.write_text(new_text, encoding="utf-8")
        return

    # Fallback: append at end (still discoverable, but not ideal)
    IDX.write_text(text + "\n" + MARK + BULLET, encoding="utf-8")

if __name__ == "__main__":
    main()
