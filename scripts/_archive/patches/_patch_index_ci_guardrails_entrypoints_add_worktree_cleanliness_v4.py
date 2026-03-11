from __future__ import annotations

from pathlib import Path
import sys

DOC = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
END = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

BULLET = "- scripts/gate_worktree_cleanliness_v1.sh — Worktree cleanliness gate (v1)\n"

def _key(line: str) -> bytes:
    # Match the gate’s lexicographic byte-order intent.
    return line.encode("utf-8")

def _is_scripts_bullet(line: str) -> bool:
    # Only these are considered “entrypoint list items” we insert among.
    # (Do NOT treat other markdown bullets as part of that list.)
    s = line.lstrip()
    return s.startswith("- scripts/")

def main() -> int:
    if not DOC.exists():
        print(f"ERROR: missing doc: {DOC}", file=sys.stderr)
        return 2

    src = DOC.read_text(encoding="utf-8")
    if BEGIN not in src or END not in src:
        print("ERROR: refused to patch (missing bounded block markers).", file=sys.stderr)
        print(f"Missing: {BEGIN} or {END}", file=sys.stderr)
        return 3

    pre, rest = src.split(BEGIN, 1)
    mid, post = rest.split(END, 1)

    lines = mid.splitlines(keepends=True)

    # Already present => no-op.
    if any(ln == BULLET for ln in lines):
        return 0

    # Collect indices of the script-bullets we care about.
    script_idxs = [i for i, ln in enumerate(lines) if _is_scripts_bullet(ln)]

    # If no script bullets exist yet, insert after any initial whitespace/comment-y stuff.
    # (We avoid trying to interpret structure beyond “keep existing content where it is”.)
    if not script_idxs:
        insert_at = 0
        while insert_at < len(lines) and lines[insert_at].strip() == "":
            insert_at += 1
        lines.insert(insert_at, BULLET)
    else:
        # Determine insertion point among script-bullets by byte-order of the full line.
        scripts = [lines[i] for i in script_idxs]
        scripts_sorted = sorted(scripts, key=_key)

        new_k = _key(BULLET)
        pos = 0
        for j, s in enumerate(scripts_sorted):
            if new_k <= _key(s):
                pos = j
                break
        else:
            pos = len(scripts_sorted)

        # Map that position back to the concrete insertion index in the original list.
        # We insert relative to existing script bullet indices (stable: we do not reorder others).
        if pos == 0:
            insert_at = script_idxs[0]
        elif pos >= len(script_idxs):
            insert_at = script_idxs[-1] + 1
        else:
            insert_at = script_idxs[pos]

        lines.insert(insert_at, BULLET)

    new_mid = "".join(lines)
    new_src = pre + BEGIN + new_mid + END + post

    if new_src != src:
        DOC.write_text(new_src, encoding="utf-8")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
