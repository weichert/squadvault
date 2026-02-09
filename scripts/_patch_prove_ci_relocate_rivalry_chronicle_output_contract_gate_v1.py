from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

BEGIN = "# SV_GATE: rivalry_chronicle_output_contract (v1) begin"
END = "# SV_GATE: rivalry_chronicle_output_contract (v1) end"

BLOCK = f"""\
{BEGIN}
echo "==> Gate: Rivalry Chronicle output contract (v1)"
# Must run AFTER Rivalry Chronicle export exists; pass canonical export path (fixture league/week).
bash scripts/gate_rivalry_chronicle_output_contract_v1.sh artifacts/exports/70985/2024/week_06/rivalry_chronicle_v1__approved_latest.md
{END}
"""

ANCHOR = "bash scripts/prove_rivalry_chronicle_end_to_end_v1.sh"

def strip_existing(txt: str) -> str:
    if BEGIN not in txt or END not in txt:
        return txt
    pre, rest = txt.split(BEGIN, 1)
    _mid, post = rest.split(END, 1)
    # remove any adjacent blank lines introduced by old insertion
    out = (pre.rstrip() + "\n\n" + post.lstrip()).rstrip() + "\n"
    return out

def insert_after_anchor(txt: str) -> str:
    if BEGIN in txt and END in txt:
        return txt

    idx = txt.find(ANCHOR)
    if idx == -1:
        raise SystemExit(f"Refusing: could not find anchor in prove_ci: {ANCHOR}")

    # insert after the *line* containing the anchor
    line_end = txt.find("\n", idx)
    if line_end == -1:
        line_end = len(txt)

    insert_at = line_end + 1
    new = txt[:insert_at] + "\n" + BLOCK + "\n" + txt[insert_at:]
    return new

def main() -> None:
    txt = PROVE.read_text(encoding="utf-8")
    txt2 = strip_existing(txt)
    txt3 = insert_after_anchor(txt2)
    if txt3 != txt:
        PROVE.write_text(txt3, encoding="utf-8")

if __name__ == "__main__":
    main()
