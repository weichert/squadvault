from __future__ import annotations

from pathlib import Path

README_PATH = Path("docs/contracts/README.md")

# If an earlier patch accidentally appended a bounded section, remove it exactly.
BAD_BEGIN = "<!-- SV_CONTRACTS_CREATIVE_SURFACE_v1_BEGIN -->"
BAD_END = "<!-- SV_CONTRACTS_CREATIVE_SURFACE_v1_END -->"

NEEDED_LINE = "- `docs/contracts/creative_sharepack_output_contract_v1.md`"

def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def _write(p: Path, s: str) -> None:
    p.write_text(s, encoding="utf-8", newline="\n")

def _remove_bad_block(txt: str) -> str:
    if (BAD_BEGIN in txt) != (BAD_END in txt):
        raise SystemExit("REFUSE: README has only one of the bad BEGIN/END markers; cannot safely edit.")
    if BAD_BEGIN not in txt:
        return txt

    pre, rest = txt.split(BAD_BEGIN, 1)
    _, post = rest.split(BAD_END, 1)

    # Remove surrounding blank lines deterministically.
    pre = pre.rstrip("\n")
    post = post.lstrip("\n")
    if post:
        return pre + "\n\n" + post
    return pre + "\n"

def _insert_under_contract_documents(txt: str) -> str:
    lines = txt.splitlines()

    # Anchor: exact header
    try:
        h = lines.index("## Contract Documents")
    except ValueError:
        raise SystemExit("REFUSE: anchor header not found: '## Contract Documents'")

    # Find bullet list immediately following header (skip at most one blank line).
    i = h + 1
    while i < len(lines) and lines[i].strip() == "":
        i += 1

    # bullets are lines starting with "- `docs/contracts/"
    bullets_start = i
    if bullets_start >= len(lines) or not lines[bullets_start].startswith("- `docs/contracts/"):
        raise SystemExit("REFUSE: expected bullet list starting with '- `docs/contracts/' under '## Contract Documents'")

    j = bullets_start
    while j < len(lines) and lines[j].startswith("- `docs/contracts/"):
        j += 1
    bullets_end = j  # insertion point

    # If already present, no-op.
    if any(l.strip() == NEEDED_LINE for l in lines[bullets_start:bullets_end]):
        return "\n".join(lines) + ("\n" if not txt.endswith("\n") else "")

    # Insert at end of that bullet block (no reordering).
    new_lines = lines[:bullets_end] + [NEEDED_LINE] + lines[bullets_end:]
    return "\n".join(new_lines) + "\n"

def main() -> None:
    if not README_PATH.exists():
        raise SystemExit(f"REFUSE: missing required file: {README_PATH}")

    before = _read(README_PATH)

    step1 = _remove_bad_block(before)
    after = _insert_under_contract_documents(step1)

    if after != before:
        _write(README_PATH, after)

    print("OK")

if __name__ == "__main__":
    main()
