from __future__ import annotations

from pathlib import Path
import re

INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

HOW_TO_READ = """\
## How to Read This Index

- **Active Guardrails** are enforced by CI and will fail builds if violated.
- Sections explicitly labeled **local-only** document helpers or hygiene practices that are *not* invoked by CI.
- If a guardrail appears here, it must correspond to a concrete enforcement mechanism.
"""

def main() -> None:
    if not INDEX.exists():
        raise SystemExit(f"missing: {INDEX}")

    txt = INDEX.read_text(encoding="utf-8")

    # 1) Insert "How to Read This Index" near the top (after intro line).
    if "## How to Read This Index" not in txt:
        txt = re.sub(
            r"(This index enumerates \*\*active, enforced CI guardrails\*\* for the SquadVault ingest system\.\n)",
            r"\1\n" + HOW_TO_READ + "\n",
            txt,
            count=1,
        )

    # 2) Clarify enforcement scope language (tighten semantics; no behavior change).
    txt = txt.replace(
        "- Guardrails listed here are **runtime-enforced**, not advisory.",
        "- Unless explicitly marked as **local-only**, guardrails listed in **Active Guardrails** are **runtime-enforced**, not advisory.",
    )

    INDEX.write_text(txt.rstrip() + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
