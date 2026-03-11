from __future__ import annotations

from pathlib import Path
import re
import sys

DOC = Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md")

BEGIN = "<!-- CI_PROOF_RUNNERS_BEGIN -->"
END = "<!-- CI_PROOF_RUNNERS_END -->"

# Match bullet lines beginning with "- scripts/" (allow leading whitespace)
BULLET_RE = re.compile(r"^(\s*-\s*)(scripts/\S+)(.*)$")


def main() -> int:
    if not DOC.exists():
        print(f"ERROR: missing doc: {DOC}", file=sys.stderr)
        return 2

    src = DOC.read_text(encoding="utf-8")

    if BEGIN not in src or END not in src:
        print("ERROR: missing bounded markers for CI_PROOF_RUNNERS block.", file=sys.stderr)
        print(f"Expected markers: {BEGIN} ... {END}", file=sys.stderr)
        return 3

    # Split exactly once at BEGIN and END
    parts = src.split(BEGIN)
    if len(parts) != 2:
        print("ERROR: refused to patch (multiple BEGIN markers).", file=sys.stderr)
        return 4

    pre, rest = parts
    mid_parts = rest.split(END)
    if len(mid_parts) != 2:
        print("ERROR: refused to patch (missing/duplicate END marker).", file=sys.stderr)
        return 5

    block, post = mid_parts
    block_lines = block.splitlines(keepends=True)

    bullet_idxs: list[int] = []
    bullet_paths: list[str] = []

    for i, line in enumerate(block_lines):
        m = BULLET_RE.match(line.rstrip("\n"))
        if not m:
            continue
        path = m.group(2)
        # Only entries beginning with scripts/
        if not path.startswith("scripts/"):
            continue
        bullet_idxs.append(i)
        bullet_paths.append(path)

    # Nothing to do if there are no script bullets
    if not bullet_idxs:
        return 0

    # Already sorted? (lexicographic)
    sorted_paths = sorted(bullet_paths)
    if bullet_paths == sorted_paths:
        return 0

    # Replace only bullet lines, in-place, preserving prefix/suffix and leaving comments/blanks untouched.
    it = iter(sorted_paths)
    new_lines = list(block_lines)
    for idx in bullet_idxs:
        original = new_lines[idx].rstrip("\n")
        m = BULLET_RE.match(original)
        assert m is not None
        prefix = m.group(1)
        suffix = m.group(3)  # preserve trailing text if any
        new_path = next(it)
        new_lines[idx] = f"{prefix}{new_path}{suffix}\n"

    new_block = "".join(new_lines)
    new_src = pre + BEGIN + new_block + END + post

    if new_src == src:
        return 0

    DOC.write_text(new_src, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
