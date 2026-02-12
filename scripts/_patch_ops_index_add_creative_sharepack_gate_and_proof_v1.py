from __future__ import annotations
from pathlib import Path

IDX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

BEGIN = "<!-- SV_CREATIVE_SHAREPACK_GUARDRAILS_v1_BEGIN -->"
END   = "<!-- SV_CREATIVE_SHAREPACK_GUARDRAILS_v1_END -->"

BLOCK = f"""{BEGIN}
- scripts/gate_creative_sharepack_output_contract_v1.sh — Gate: creative sharepack output contract (v1)
- scripts/prove_creative_sharepack_determinism_v1.sh — Proof: creative sharepack determinism (v1)
{END}
"""

def main() -> None:
    text = IDX.read_text(encoding="utf-8")
    if BEGIN in text and END in text:
        pre = text.split(BEGIN)[0]
        post = text.split(END)[1]
        out = pre + BLOCK + post
    else:
        out = text.rstrip() + "\n\n" + BLOCK + "\n"
    IDX.write_text(out, encoding="utf-8", newline="\n")
    print("OK")

if __name__ == "__main__":
    main()
