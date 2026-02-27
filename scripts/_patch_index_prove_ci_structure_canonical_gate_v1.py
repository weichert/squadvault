from __future__ import annotations

from pathlib import Path
import re
import sys

TARGET = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
END = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

NEW_PATH = "scripts/gate_prove_ci_structure_canonical_v1.sh"
DESC = "Enforce prove_ci gate invocation uniqueness + canonical ordering (v1)"

BULLET_RE = re.compile(r"^(\s*-\s*)(scripts/\S+)(.*)$")

def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: missing target: {TARGET}", file=sys.stderr)
        return 2

    src = TARGET.read_text(encoding="utf-8")
    if NEW_PATH in src:
        return 0

    if BEGIN not in src or END not in src:
        print("ERROR: refused to patch (missing bounded markers).", file=sys.stderr)
        print(f"Expected: {BEGIN} ... {END}", file=sys.stderr)
        return 3

    pre, rest = src.split(BEGIN, 1)
    block, post = rest.split(END, 1)

    lines = block.splitlines(keepends=True)

    bullet_idxs: list[int] = []
    bullet_paths: list[str] = []
    bullet_suffixes: list[str] = []

    for i, line in enumerate(lines):
        m = BULLET_RE.match(line.rstrip("\n"))
        if not m:
            continue
        path = m.group(2)
        if not path.startswith("scripts/"):
            continue
        bullet_idxs.append(i)
        bullet_paths.append(path)
        bullet_suffixes.append(m.group(3))

    if not bullet_idxs:
        # Insert at top of block
        new_block = f"- {NEW_PATH} — {DESC}\n" + block
        TARGET.write_text(pre + BEGIN + new_block + END + post, encoding="utf-8")
        return 0

    # Add + sort
    bullet_paths.append(NEW_PATH)
    sorted_paths = sorted(bullet_paths)

    # Replace only existing bullet slots; preserve original suffix per-slot if present,
    # but for the newly-introduced path we inject our canonical description.
    it = iter(sorted_paths)
    new_lines = list(lines)

    for idx in bullet_idxs:
        cur_path = next(it)
        suffix = ""
        # If this slot is placing our new entry, give it the canonical description.
        if cur_path == NEW_PATH:
            suffix = f" — {DESC}"
        else:
            # preserve whatever suffix was already on that slot
            m = BULLET_RE.match(new_lines[idx].rstrip("\n"))
            assert m is not None
            suffix = m.group(3)
        # preserve prefix spacing
        m0 = BULLET_RE.match(new_lines[idx].rstrip("\n"))
        assert m0 is not None
        prefix = m0.group(1)
        new_lines[idx] = f"{prefix}{cur_path}{suffix}\n"

    rebuilt = "".join(new_lines)
    if NEW_PATH not in rebuilt:
        print("ERROR: refused to patch (could not place new bullet into existing bullet slots).", file=sys.stderr)
        return 4

    TARGET.write_text(pre + BEGIN + rebuilt + END + post, encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
