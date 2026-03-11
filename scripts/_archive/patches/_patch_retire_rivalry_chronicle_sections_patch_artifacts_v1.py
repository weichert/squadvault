from __future__ import annotations

from pathlib import Path

FILES = [
    Path("scripts/_patch_prove_rivalry_chronicle_export_contract_sections_v11_relocate.py"),
    Path("scripts/patch_prove_rivalry_chronicle_export_contract_sections_v11_relocate.sh"),
    Path("scripts/_patch_prove_rivalry_chronicle_export_contract_sections_v12_rewrite.py"),
    Path("scripts/patch_prove_rivalry_chronicle_export_contract_sections_v12_rewrite.sh"),
]

def main() -> None:
    for p in FILES:
        if p.exists():
            p.unlink()

if __name__ == "__main__":
    main()
