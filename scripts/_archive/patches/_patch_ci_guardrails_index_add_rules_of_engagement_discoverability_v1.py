from __future__ import annotations

from pathlib import Path

TARGET = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

BLOCK = """\

<!-- SV_DOCS_MUTATION_DISCOVERABILITY: rules_of_engagement (v1) -->
- docs/process/rules_of_engagement.md — Docs + CI Mutation Policy (Enforced)
"""

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"missing canonical file: {TARGET}")

    text = TARGET.read_text(encoding="utf-8")

    # If already present, no-op
    if "rules_of_engagement" in text and "Docs + CI Mutation Policy" in text:
        return

    # Ensure we satisfy both needles deterministically
    # (append a small discoverability block at EOF)
    new_text = text
    if not new_text.endswith("\n"):
        new_text += "\n"
    new_text += BLOCK

    TARGET.write_text(new_text, encoding="utf-8")

if __name__ == "__main__":
    main()
