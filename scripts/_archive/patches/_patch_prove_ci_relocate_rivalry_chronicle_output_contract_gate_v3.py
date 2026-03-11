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
    return (pre.rstrip() + "\n\n" + post.lstrip()).rstrip() + "\n"

def main() -> None:
    txt0 = PROVE.read_text(encoding="utf-8")
    txt = strip_existing(txt0)

    if BEGIN in txt or END in txt:
        raise SystemExit("Refusing: failed to strip existing gate block cleanly.")

    lines = txt.splitlines(True)  # keep newlines
    # Find the anchor line index
    i_anchor = None
    for i, ln in enumerate(lines):
        if ANCHOR in ln:
            i_anchor = i
            break
    if i_anchor is None:
        raise SystemExit(f"Refusing: could not find anchor: {ANCHOR}")

    # Walk forward to consume the full continued invocation:
    # We consider the invocation "in progress" once we see an arg line starting with '--'
    seen_arg = False
    j = i_anchor
    while j < len(lines):
        ln = lines[j]
        stripped = ln.strip()

        if stripped.startswith("--"):
            seen_arg = True

        # We only stop AFTER we've seen at least one arg line, and we hit a line that does NOT end with '\'
        # (i.e., the end of the continued command)
        if seen_arg and not ln.rstrip("\r\n").endswith("\\"):
            j += 1  # insert after this line
            break

        j += 1

    if not seen_arg:
        raise SystemExit("Refusing: did not find any argument lines ('--...') after the Rivalry Chronicle prove invocation.")
    if j >= len(lines):
        # inserting at EOF is acceptable
        pass

    insert_at = sum(len(lines[k]) for k in range(0, j))
    out = txt[:insert_at] + "\n" + BLOCK + "\n" + txt[insert_at:]

    if out != txt0:
        PROVE.write_text(out, encoding="utf-8")

if __name__ == "__main__":
    main()
