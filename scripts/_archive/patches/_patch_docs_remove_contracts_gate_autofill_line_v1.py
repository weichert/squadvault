from __future__ import annotations

from pathlib import Path

DOC = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

BAD = "- scripts/gate_contracts_index_discoverability_v1.sh — (autofill) describe gate purpose"

def main() -> None:
    if not DOC.exists():
        raise SystemExit(f"Missing ops index: {DOC}")

    txt = DOC.read_text(encoding="utf-8")
    if BAD not in txt:
        return  # already clean

    out = [ln for ln in txt.splitlines(True) if ln.rstrip("\n") != BAD]
    DOC.write_text("".join(out), encoding="utf-8")

if __name__ == "__main__":
    main()
