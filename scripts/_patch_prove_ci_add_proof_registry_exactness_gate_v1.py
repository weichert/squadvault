from __future__ import annotations

from pathlib import Path
import sys

PROVE = Path("scripts/prove_ci.sh")

BEGIN = "# SV_GATE: proof_registry_exactness (v1) begin"
END = "# SV_GATE: proof_registry_exactness (v1) end"

BLOCK = f"""\
{BEGIN}
bash scripts/gate_ci_proof_surface_registry_exactness_v1.sh
{END}
"""

def main() -> int:
    if not PROVE.exists():
        print(f"ERROR: missing {PROVE}", file=sys.stderr)
        return 1

    text = PROVE.read_text(encoding="utf-8")

    if BEGIN in text and END in text:
        # idempotent: replace bounded region
        pre = text.split(BEGIN, 1)[0]
        post = text.split(END, 1)[1]
        updated = pre.rstrip("\n") + "\n" + BLOCK + "\n" + post.lstrip("\n")
    else:
        # Insert near existing gate section: after docs_integrity gate if present, else near top.
        needle = "# SV_GATE: docs_integrity"
        idx = text.find(needle)
        if idx != -1:
            # insert after the docs_integrity bounded block end if present
            end_idx = text.find("# SV_GATE: docs_integrity", idx)
            # find the next blank line after that block
            # (simple: insert after first occurrence of 'end' line if present)
            marker_end = "end"
            pos_end = text.find(marker_end, idx)
            if pos_end != -1:
                # insert after the line containing 'end'
                line_end = text.find("\n", pos_end)
                if line_end != -1:
                    updated = text[: line_end + 1] + "\n" + BLOCK + "\n" + text[line_end + 1 :]
                else:
                    updated = text + "\n\n" + BLOCK + "\n"
            else:
                updated = text + "\n\n" + BLOCK + "\n"
        else:
            updated = text + "\n\n" + BLOCK + "\n"

    if updated != text:
        PROVE.write_text(updated, encoding="utf-8")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
