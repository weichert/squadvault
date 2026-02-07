from __future__ import annotations

from pathlib import Path

DOC = Path("docs/80_indices/ops/Ops_Entrypoints_Hub_v1.0.md")
MAP = Path("docs/80_indices/ops/Canonical_Indices_Map_v1.0.md")

# Links are relative to docs/80_indices/ops/
REL_CI_GUARDRAILS = "CI_Guardrails_Index_v1.0.md"
REL_CANONICAL_INDICES_MAP = "Canonical_Indices_Map_v1.0.md"
REL_PROCESS_DISCIPLINE = "Process_Discipline_Index_v1.0.md"
REL_RECOVERY_WORKFLOWS = "Recovery_Workflows_Index_v1.0.md"
REL_OPS_RULES_ONE_PAGE = "Ops_Rules_One_Page_v1.0.md"
REL_NEW_CONTRIB_ORIENTATION = "New_Contributor_Orientation_10min_v1.0.md"

MAP_BULLET_LINE = "- [Ops Entrypoints Hub (v1.0)](Ops_Entrypoints_Hub_v1.0.md)"

EXPECTED_DOC = f"""# Ops Entrypoints Hub (v1.0)

Purpose:
A one-screen “where do I start?” hub for SquadVault ops docs.

This is an index only. Authority remains in the linked canonical documents.

## Start here

- [CI Guardrails Index](<{REL_CI_GUARDRAILS}>)
- [Canonical Indices Map](<{REL_CANONICAL_INDICES_MAP}>)

## Common scenarios

- CI failing / repo is dirty / proofs blocked:
  - [Recovery Workflows Index](<{REL_RECOVERY_WORKFLOWS}>)
- “Where are the rules?” / process discipline:
  - [Process Discipline Index](<{REL_PROCESS_DISCIPLINE}>)
- “Give me the short version” (day-to-day):
  - [Ops Rules — One Page](<{REL_OPS_RULES_ONE_PAGE}>)
- New contributor onboarding:
  - [New Contributor Orientation (10 min)](<{REL_NEW_CONTRIB_ORIENTATION}>)
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


def _ensure_doc() -> None:
    if DOC.exists():
        existing = _read_text(DOC)
        if existing != EXPECTED_DOC:
            _refuse(f"{DOC} exists but does not match expected canonical contents.")
        return
    _write_text(DOC, EXPECTED_DOC)


def _ensure_map_link() -> None:
    if not MAP.exists():
        _refuse(f"missing required file: {MAP}")

    existing = _read_text(MAP)

    if MAP_BULLET_LINE in existing:
        return

    # Constraint: single bullet/link; no restructure.
    out = existing
    if not out.endswith("\n"):
        out += "\n"
    out += "\n" + MAP_BULLET_LINE + "\n"
    _write_text(MAP, out)


def main() -> None:
    _ensure_doc()
    _ensure_map_link()


if __name__ == "__main__":
    main()
