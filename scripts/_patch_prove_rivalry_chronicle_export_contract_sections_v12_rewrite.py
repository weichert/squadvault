from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_rivalry_chronicle_end_to_end_v1.sh")

NEEDLE = '# Enforce Rivalry Chronicle output contract (v1): header + required metadata keys.'
START_MARK = "# --- REQUIRED_SECTION_HEADINGS_V10 ---"
ANCHOR = "new_lines = lines[:meta_start] + meta + lines[meta_end:]"

INSERT_BLOCK = """\
# --- REQUIRED_SECTION_HEADINGS_V10 ---
required = [
    "## Matchup Summary",
    "## Key Moments",
    "## Stats & Nuggets",
    "## Closing",
]
present = {ln.strip() for ln in new_lines}
missing = [h for h in required if h not in present]
if missing:
    # Append a minimal scaffold for any missing headings (keep existing content intact).
    # Ensure at least one blank line before the scaffold.
    if new_lines and new_lines[-1].strip() != "":
        new_lines.append("")
    for h in missing:
        new_lines.append(h)
        new_lines.append("")
"""

def main() -> None:
    txt0 = PROVE.read_text(encoding="utf-8")
    if NEEDLE not in txt0:
        raise SystemExit("Refusing: expected contract block marker not found; cannot apply v12 safely.")
    if ANCHOR not in txt0:
        raise SystemExit("Refusing: expected new_lines anchor not found; cannot apply v12 safely.")

    lines = txt0.splitlines(True)

    # 1) Remove ALL existing v10 blocks (robustly): skip from START_MARK until we hit ANCHOR.
    out: list[str] = []
    skipping = False
    removed = 0

    for ln in lines:
        if not skipping and START_MARK in ln:
            skipping = True
            removed += 1
            continue

        if skipping:
            # Stop skipping right BEFORE anchor line (keep the anchor line).
            if ANCHOR in ln:
                skipping = False
                out.append(ln)
            # else drop this line
            continue

        out.append(ln)

    if skipping:
        raise SystemExit("Refusing: saw section marker start but never found anchor to terminate removal (file unexpected).")

    txt1 = "".join(out)

    # 2) Ensure v10 block exists exactly once, immediately after the ANCHOR line.
    lines2 = txt1.splitlines(True)
    out2: list[str] = []
    inserted = False

    for ln in lines2:
        out2.append(ln)
        if (not inserted) and ANCHOR in ln:
            out2.append(INSERT_BLOCK + "\n\n")
            inserted = True

    if not inserted:
        raise SystemExit("Refusing: failed to insert v10 block after anchor (unexpected).")

    txt2 = "".join(out2)

    # Sanity: exactly one marker after rewrite.
    marker_count = txt2.count(START_MARK)
    if marker_count != 1:
        raise SystemExit(f"Refusing: expected exactly 1 v10 marker after rewrite, found {marker_count}.")

    if txt2 != txt0:
        PROVE.write_text(txt2, encoding="utf-8")

if __name__ == "__main__":
    main()
