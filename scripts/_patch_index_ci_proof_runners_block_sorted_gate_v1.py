from __future__ import annotations

from pathlib import Path
import re
import sys

TARGET = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

NEW_PATH = "scripts/gate_ci_proof_runners_block_sorted_v1.sh"

# Generic bounded entrypoints markers (tolerate naming variants).
BEGIN_RE = re.compile(r"^\s*<!--\s*.*ENTRYPOINT.*BEGIN.*-->\s*$", re.IGNORECASE)
END_RE = re.compile(r"^\s*<!--\s*.*ENTRYPOINT.*END.*-->\s*$", re.IGNORECASE)

# Bullet lines we reorder as a set (scripts/* only), preserving everything else.
BULLET_RE = re.compile(r"^(\s*-\s*)(scripts/\S+)(.*)$")


def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: missing target: {TARGET}", file=sys.stderr)
        return 2

    src = TARGET.read_text(encoding="utf-8")
    if NEW_PATH in src:
        return 0

    lines = src.splitlines(keepends=True)

    begin_i = None
    end_i = None

    for i, line in enumerate(lines):
        if begin_i is None and BEGIN_RE.match(line):
            begin_i = i
            continue
        if begin_i is not None and END_RE.match(line):
            end_i = i
            break

    if begin_i is None or end_i is None or begin_i >= end_i:
        print("ERROR: refused to patch (could not locate bounded entrypoints block markers).", file=sys.stderr)
        print("Expected a BEGIN marker like: <!-- ...ENTRYPOINT...BEGIN... -->", file=sys.stderr)
        print("and a matching END marker like: <!-- ...ENTRYPOINT...END... -->", file=sys.stderr)
        return 3

    pre = lines[: begin_i + 1]
    block = lines[begin_i + 1 : end_i]
    post = lines[end_i:]

    bullet_idxs: list[int] = []
    bullet_paths: list[str] = []

    for i, line in enumerate(block):
        m = BULLET_RE.match(line.rstrip("\n"))
        if not m:
            continue
        path = m.group(2)
        if not path.startswith("scripts/"):
            continue
        bullet_idxs.append(i)
        bullet_paths.append(path)

    # Add the new path into the bullet set (we will either place it into an existing slot,
    # or inject a new bullet if there are no bullet slots at all).
    if not bullet_idxs:
        # Insert at top of block (immediately after BEGIN) if no script bullets exist.
        new_block = [f"- {NEW_PATH}\n"] + block
        new_src = "".join(pre + new_block + post)
        TARGET.write_text(new_src, encoding="utf-8")
        return 0

    bullet_paths.append(NEW_PATH)
    sorted_paths = sorted(bullet_paths)

    # Replace only existing bullet slots in sorted order.
    it = iter(sorted_paths)
    new_block = list(block)
    for idx in bullet_idxs:
        original = new_block[idx].rstrip("\n")
        m = BULLET_RE.match(original)
        assert m is not None
        prefix = m.group(1)
        suffix = m.group(3)
        new_path = next(it)
        new_block[idx] = f"{prefix}{new_path}{suffix}\n"

    rebuilt = "".join(new_block)

    # If NEW_PATH didn't land, refuse (don’t surprise-insert).
    if NEW_PATH not in rebuilt:
        print("ERROR: refused to patch (could not place new bullet safely into existing bullet slots).", file=sys.stderr)
        print("This usually means the entrypoints block has fewer bullet slots than expected.", file=sys.stderr)
        return 4

    new_src = "".join(pre + new_block + post)
    if new_src != src:
        TARGET.write_text(new_src, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
