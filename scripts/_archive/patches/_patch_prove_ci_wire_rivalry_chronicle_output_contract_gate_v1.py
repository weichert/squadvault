from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

BEGIN = "# SV_GATE: rivalry_chronicle_output_contract (v1) begin"
END = "# SV_GATE: rivalry_chronicle_output_contract (v1) end"

BLOCK = f"""\
{BEGIN}
echo "==> Gate: Rivalry Chronicle output contract (v1)"
# Prefer the canonical export path used by the proof if present; fallback to search in gate itself.
bash scripts/gate_rivalry_chronicle_output_contract_v1.sh artifacts/exports/70985/2024/week_06/rivalry_chronicle_v1__approved_latest.md || \\
  bash scripts/gate_rivalry_chronicle_output_contract_v1.sh
{END}
"""

def main() -> None:
    txt = PROVE.read_text(encoding="utf-8")

    if BEGIN in txt and END in txt:
        return

    # Insert after golden path output contract gate if present; else before final cleanliness check.
    anchor = "== Output contract gate (v1) =="
    idx = txt.find(anchor)
    if idx != -1:
        # insert after the golden path gate output block by placing after the next "OK:" line or next blank
        # simplest deterministic: insert immediately after anchor line (still fine)
        insert_at = idx
        # move to start of line containing anchor
        insert_at = txt.rfind("\n", 0, insert_at) + 1
        # put it *after* that anchor block by finding the next occurrence of "OK:" after idx
        ok_idx = txt.find("OK:", idx)
        if ok_idx != -1:
            # after that line
            line_end = txt.find("\n", ok_idx)
            if line_end != -1:
                insert_at = line_end + 1
        new = txt[:insert_at] + "\n" + BLOCK + "\n" + txt[insert_at:]
        PROVE.write_text(new, encoding="utf-8")
        return

    # Fallback: append near end
    PROVE.write_text(txt.rstrip() + "\n\n" + BLOCK + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
