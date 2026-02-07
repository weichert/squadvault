from __future__ import annotations

from pathlib import Path

INDEX_DOC = Path("docs/80_indices/ops/Process_Discipline_Index_v1.0.md")
CI_INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

# Relative links from docs/80_indices/ops/
REL_RULES_OF_ENGAGEMENT = "../../process/rules_of_engagement.md"
REL_PATCHER_WRAPPER_PATTERN = "../../process/Canonical_Patcher_Wrapper_Pattern_v1.0.md"
REL_HOW_TO_READ = "../../canon_pointers/How_to_Read_SquadVault_v1.0.md"
REL_CANON_POINTERS_README = "../../canon_pointers/README.md"

CI_BULLET_LINE = "- [Process Discipline Index (v1.0)](Process_Discipline_Index_v1.0.md)"

EXPECTED_INDEX_DOC = f"""# Process Discipline Index (v1.0)

Purpose:
A 2am “where are the rules?” index for SquadVault process discipline.

This is an index only. Authority remains in the linked canonical documents.

## Canonical process discipline docs

- [Rules of Engagement](<{REL_RULES_OF_ENGAGEMENT}>)
- [Canonical Patcher/Wrapper Pattern](<{REL_PATCHER_WRAPPER_PATTERN}>)
- [How to Read SquadVault](<{REL_HOW_TO_READ}>)
- [Canon Pointers README](<{REL_CANON_POINTERS_README}>)

## Ops reminder

- Prefer versioned patchers + wrappers over manual edits.
- Patchers must be idempotent and refuse-on-drift.
- This index is documentation-only and must not introduce new mechanics.
"""


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write_text(p: Path, text: str) -> None:
    if not text.endswith("\n"):
        text += "\n"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _refuse(msg: str) -> None:
    raise SystemExit(f"REFUSE-ON-DRIFT: {msg}")


def _ensure_index_doc() -> None:
    if INDEX_DOC.exists():
        existing = _read_text(INDEX_DOC)
        if existing != EXPECTED_INDEX_DOC:
            _refuse(f"{INDEX_DOC} exists but does not match expected canonical contents.")
        return
    _write_text(INDEX_DOC, EXPECTED_INDEX_DOC)


def _ensure_ci_index_link() -> None:
    if not CI_INDEX.exists():
        _refuse(f"missing required file: {CI_INDEX}")

    existing = _read_text(CI_INDEX)

    if CI_BULLET_LINE in existing:
        return

    # Constraint: single bullet/link; no restructure.
    out = existing
    if not out.endswith("\n"):
        out += "\n"
    out += "\n" + CI_BULLET_LINE + "\n"
    _write_text(CI_INDEX, out)


def main() -> None:
    _ensure_index_doc()
    _ensure_ci_index_link()


if __name__ == "__main__":
    main()
