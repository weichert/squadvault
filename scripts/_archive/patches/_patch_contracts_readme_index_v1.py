from __future__ import annotations

import re
from pathlib import Path

CONTRACTS_DIR = Path("docs/contracts")
README = CONTRACTS_DIR / "README.md"

def list_contract_files() -> list[str]:
    # Include only versioned contract docs: *_contract_v*.md (exclude README itself)
    files = []
    for p in sorted(CONTRACTS_DIR.glob("*_contract_v*.md")):
        if p.name.lower() == "readme.md":
            continue
        files.append(p.as_posix())
    return files

def render(files: list[str]) -> str:
    # Canonical README format — simple bullets, stable ordering
    lines = []
    lines.append("# Contracts Index")
    lines.append("")
    lines.append("Status: CANONICAL (index)")
    lines.append("")
    lines.append("This directory contains versioned contracts that lock down **structure and interfaces**.")
    lines.append("Contracts protect downstream creative tooling by making outputs predictable and discoverable.")
    lines.append("")
    lines.append("## Contract Documents")
    lines.append("")
    if not files:
        lines.append("_No contracts found._")
    else:
        for f in files:
            lines.append(f"- `{f}`")
    lines.append("")
    lines.append("## Indexing Rules (enforced)")
    lines.append("")
    lines.append("- Every file matching `docs/contracts/*_contract_v*.md` must be listed above exactly once.")
    lines.append("- New contract versions must be added as new files (v2, v3...) — silent drift is forbidden.")
    lines.append("")
    return "\n".join(lines)

def main() -> None:
    CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)
    files = list_contract_files()

    # Hard requirement: Golden Path Output Contract v1 must exist (this milestone assumes it)
    required = "docs/contracts/golden_path_output_contract_v1.md"
    if required not in files:
        raise SystemExit(
            "Refusing: required contract missing: docs/contracts/golden_path_output_contract_v1.md"
        )

    text = render(files)

    if README.exists():
        cur = README.read_text(encoding="utf-8")
        if cur == text:
            return

    README.write_text(text, encoding="utf-8")

if __name__ == "__main__":
    main()
