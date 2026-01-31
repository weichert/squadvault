from __future__ import annotations
from pathlib import Path

DOCS_ROOT = Path("docs")

REWRITES = {
    "docs/30_contract_cards/ops/APPROVAL_AUTHORITY_Contract_Card_v1.0.docx":
        "docs/90_archive/contract_cards_docx/APPROVAL_AUTHORITY_Contract_Card_v1.0.docx",
    "docs/30_contract_cards/ops/TONE_ENGINE_Contract_Card_v1.0.docx":
        "docs/90_archive/contract_cards_docx/TONE_ENGINE_Contract_Card_v1.0.docx",
}

TEXT_EXTS = {".md", ".txt"}

def main() -> None:
    changed = 0
    replacements = 0

    for p in DOCS_ROOT.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in TEXT_EXTS:
            continue

        s = p.read_text(encoding="utf-8")
        s2 = s
        for old, new in REWRITES.items():
            if old in s2:
                replacements += s2.count(old)
                s2 = s2.replace(old, new)

        if s2 != s:
            p.write_text(s2, encoding="utf-8")
            changed += 1

    print(f"OK: rewritten moved contract-card refs in {changed} file(s); replacements={replacements}")

if __name__ == "__main__":
    main()
