from __future__ import annotations
from pathlib import Path

REG = Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md")

BEGIN = "<!-- SV_CI_PROOF_CREATIVE_SHAREPACK_IF_AVAILABLE_v1_BEGIN -->"
END   = "<!-- SV_CI_PROOF_CREATIVE_SHAREPACK_IF_AVAILABLE_v1_END -->"

BLOCK = f"""{BEGIN}
- scripts/prove_ci_creative_sharepack_if_available_v1.sh — Proof runner (CI): creative sharepack determinism if inputs present (v1)
{END}
"""

def main() -> None:
    text = REG.read_text(encoding="utf-8")

    if BEGIN in text and END in text:
        pre = text.split(BEGIN)[0]
        post = text.split(END)[1]
        out = pre + BLOCK + post
    else:
        out = text.rstrip() + "\n\n" + BLOCK + "\n"

    REG.write_text(out, encoding="utf-8", newline="\n")
    print("OK")

if __name__ == "__main__":
    main()
