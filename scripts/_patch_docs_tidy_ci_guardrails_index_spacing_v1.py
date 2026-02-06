from __future__ import annotations

from pathlib import Path
import re

INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

def main() -> None:
    if not INDEX.exists():
        raise SystemExit(f"missing: {INDEX}")

    txt = INDEX.read_text(encoding="utf-8")

    # Normalize excess blank lines (keep markdown readable, don't over-compress).
    # - collapse 3+ newlines to 2
    txt = re.sub(r"\n{3,}", "\n\n", txt)

    # Remove accidental empty line directly after headings (common after insertions).
    txt = re.sub(r"(## [^\n]+)\n\n+", r"\1\n", txt)

    # Ensure a single blank line BEFORE each heading (except file start)
    txt = re.sub(r"([^\n])\n(## )", r"\1\n\n\2", txt)

    # Ensure file ends with newline
    txt = txt.rstrip() + "\n"

    INDEX.write_text(txt, encoding="utf-8")

if __name__ == "__main__":
    main()
