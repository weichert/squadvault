from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

BEGIN = "# SV_GATE: contracts_index_discoverability (v1) begin"
END = "# SV_GATE: contracts_index_discoverability (v1) end"

BLOCK = f"""\
{BEGIN}
echo "==> Gate: contracts index discoverability (v1)"
bash scripts/gate_contracts_index_discoverability_v1.sh
{END}
"""

def main() -> None:
    text = PROVE.read_text(encoding="utf-8")

    if BEGIN in text and END in text:
        return  # idempotent

    # Insert near other docs/ops gates; safest: just before "==> docs integrity" if present
    anchor = "==> docs integrity"
    idx = text.find(anchor)
    if idx == -1:
        # fallback: append at end (still deterministic)
        new = text.rstrip() + "\n\n" + BLOCK + "\n"
        PROVE.write_text(new, encoding="utf-8")
        return

    new = text[:idx] + BLOCK + "\n" + text[idx:]
    PROVE.write_text(new, encoding="utf-8")

if __name__ == "__main__":
    main()
