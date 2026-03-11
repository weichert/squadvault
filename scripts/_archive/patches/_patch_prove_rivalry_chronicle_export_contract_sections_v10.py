from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_rivalry_chronicle_end_to_end_v1.sh")

NEEDLE = '# Enforce Rivalry Chronicle output contract (v1): header + required metadata keys.'
ANCHOR = 'meta = upsert(meta, "Artifact Type", artifact_type_val)'
SENTINEL = "REQUIRED_SECTION_HEADINGS_V10"

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
        raise SystemExit("Refusing: expected v7+ contract block marker not found; cannot apply v10 safely.")

    # Idempotence
    if SENTINEL in txt0:
        return

    if ANCHOR not in txt0:
        raise SystemExit("Refusing: expected Artifact Type upsert anchor not found; cannot apply v10 safely.")

    lines = txt0.splitlines(True)
    out: list[str] = []
    inserted = False

    for ln in lines:
        out.append(ln)
        if (not inserted) and ANCHOR in ln:
            # Insert immediately after the artifact type upsert line
            out.append(INSERT_BLOCK + "\n")
            inserted = True

    if not inserted:
        raise SystemExit("Refusing: failed to insert v10 block (anchor scan did not trigger).")

    txt1 = "".join(out)
    if txt1 != txt0:
        PROVE.write_text(txt1, encoding="utf-8")

if __name__ == "__main__":
    main()
