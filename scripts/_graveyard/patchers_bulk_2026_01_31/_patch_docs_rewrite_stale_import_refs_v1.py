from __future__ import annotations

from pathlib import Path

DOCS_ROOT = Path("docs")

REWRITES = {
    # Ops docs
    "docs/_import/INBOX/SquadVault_AI_Development_Rules_of_Engagement_v1.0.docx":
        "docs/50_ops_and_build/SquadVault_AI_Development_Rules_of_Engagement_v1.0.docx",
    "docs/_import/INBOX/SquadVault_Engineering_Handoff_Checklist_v1.0.docx":
        "docs/90_archive/prior_versions/SquadVault_Engineering_Handoff_Checklist_v1.0.docx",
    "docs/_import/INBOX/SquadVault_Engineering_Handoff_Checklist_v1.1.pdf":
        "docs/50_ops_and_build/SquadVault_Engineering_Handoff_Checklist_v1.1.pdf",

    # Documentation map snapshots
    "docs/_import/INBOX/SquadVault_Documentation_Map_and_Canonical_References_v1.4.pdf":
        "docs/80_indices/SquadVault_Documentation_Map_and_Canonical_References_v1.4.pdf",
    "docs/_import/INBOX/SquadVault_Documentation_Map_and_Canonical_References_v1.3_NEW.docx":
        "docs/90_archive/prior_versions/SquadVault_Documentation_Map_and_Canonical_References_v1.3_NEW.docx",
    "docs/_import/INBOX/SquadVault_Documentation_Map_and_Canonical_References_v1.3_NEW.pdf":
        "docs/90_archive/prior_versions/SquadVault_Documentation_Map_and_Canonical_References_v1.3_NEW.pdf",

    # Signal Scout package -> promoted homes
    "docs/_import/INBOX/SquadVault_Signal_Scout_v1_Canonical_Package/Documentation_Map_Tier2_Addition_v1.4.md":
        "docs/80_indices/signal_scout/Documentation_Map_Tier2_Addition_v1.4.md",
    "docs/_import/INBOX/SquadVault_Signal_Scout_v1_Canonical_Package/Signal_Scout_Contract_Card_v1.0.md":
        "docs/30_contract_cards/signal_scout/Signal_Scout_Contract_Card_v1.0.md",
    "docs/_import/INBOX/SquadVault_Signal_Scout_v1_Canonical_Package/Signal_Scout_Signal_Type_Enum_v1.0.md":
        "docs/40_specs/signal_scout/Signal_Scout_Signal_Type_Enum_v1.0.md",
    "docs/_import/INBOX/SquadVault_Signal_Scout_v1_Canonical_Package/Tier1_Signal_Derivation_Specs_v1.0.md":
        "docs/40_specs/signal_scout/Tier1_Signal_Derivation_Specs_v1.0.md",
    "docs/_import/INBOX/SquadVault_Signal_Scout_v1_Canonical_Package/Tier1_Signal_Input_Contracts_v1.0.md":
        "docs/40_specs/signal_scout/Tier1_Signal_Input_Contracts_v1.0.md",
}

TEXT_EXTS = {".md", ".txt"}

def main() -> None:
    changed_files = 0
    total_replacements = 0

    for p in DOCS_ROOT.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in TEXT_EXTS:
            continue

        s = p.read_text(encoding="utf-8")
        s2 = s
        for old, new in REWRITES.items():
            if old in s2:
                s2 = s2.replace(old, new)
        if s2 != s:
            p.write_text(s2, encoding="utf-8")
            changed_files += 1
            # count replacements in a simple way
            for old, new in REWRITES.items():
                total_replacements += s.count(old)

    print(f"OK: rewritten stale import refs in {changed_files} file(s); replacements={total_replacements}")

if __name__ == "__main__":
    main()
