from __future__ import annotations

from pathlib import Path

DOC = Path("docs/80_indices/ops/New_Contributor_Orientation_10min_v1.0.md")
MAP = Path("docs/80_indices/ops/Canonical_Indices_Map_v1.0.md")

# Relative links from docs/80_indices/ops/
REL_HOW_TO_READ = "../../canon_pointers/How_to_Read_SquadVault_v1.0.md"
REL_RULES_OF_ENGAGEMENT = "../../process/rules_of_engagement.md"
REL_PATCHER_WRAPPER_PATTERN = "../../process/Canonical_Patcher_Wrapper_Pattern_v1.0.md"
REL_CANONICAL_INDICES_MAP = "Canonical_Indices_Map_v1.0.md"
REL_OPS_RULES_ONE_PAGE = "Ops_Rules_One_Page_v1.0.md"
REL_RECOVERY = "Recovery_Workflows_Index_v1.0.md"
REL_CI_GUARDRAILS = "CI_Guardrails_Index_v1.0.md"

MAP_BULLET_LINE = "- [New Contributor Orientation (10 min) (v1.0)](New_Contributor_Orientation_10min_v1.0.md)"

EXPECTED_DOC = f"""# New Contributor Orientation (10 min) (v1.0)

Purpose:
Get productive quickly without violating SquadVault’s process discipline.

This is an index only. Authority remains in the linked canonical documents.

## Read in this order (10 minutes)

1. [How to Read SquadVault](<{REL_HOW_TO_READ}>)
2. [Rules of Engagement](<{REL_RULES_OF_ENGAGEMENT}>)
3. [Canonical Patcher/Wrapper Pattern](<{REL_PATCHER_WRAPPER_PATTERN}>)
4. [Canonical Indices Map](<{REL_CANONICAL_INDICES_MAP}>)
5. [Ops Rules — One Page](<{REL_OPS_RULES_ONE_PAGE}>)

## Do on day 1 (copy/paste)

- Prove CI from a clean repo:
  - `bash scripts/prove_ci.sh`
- Run the canonical noop patch (verifies patch workflow plumbing):
  - `bash scripts/patch_example_noop_v1.sh`
- Confirm cleanliness:
  - `git status --porcelain=v1`

## If something fails

- Use safe recovery steps: [Recovery Workflows Index](<{REL_RECOVERY}>)
- Start from guardrails: [CI Guardrails Index](<{REL_CI_GUARDRAILS}>)
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
