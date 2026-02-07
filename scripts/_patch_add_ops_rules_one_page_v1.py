from __future__ import annotations

from pathlib import Path

DOC = Path("docs/80_indices/ops/Ops_Rules_One_Page_v1.0.md")
PROCESS_INDEX = Path("docs/80_indices/ops/Process_Discipline_Index_v1.0.md")

# Relative links from docs/80_indices/ops/
REL_PATCHER_WRAPPER_PATTERN = "../../process/Canonical_Patcher_Wrapper_Pattern_v1.0.md"
REL_RULES_OF_ENGAGEMENT = "../../process/rules_of_engagement.md"
REL_CI_CLEANLINESS = "CI_Cleanliness_Invariant_v1.0.md"
REL_PAIRING_GATE = "CI_Patcher_Wrapper_Pairing_Gate_v1.0.md"
REL_RECOVERY = "Recovery_Workflows_Index_v1.0.md"
REL_CI_GUARDRAILS_INDEX = "CI_Guardrails_Index_v1.0.md"
REL_CANONICAL_INDICES_MAP = "Canonical_Indices_Map_v1.0.md"

PROCESS_BULLET_LINE = "- [Ops Rules — One Page (v1.0)](Ops_Rules_One_Page_v1.0.md)"

EXPECTED_DOC = f"""# Ops Rules — One Page (v1.0)

What this is:
A one-page operational index/excerpt of the most-used SquadVault rules for day-to-day work.

What this is not:
This document does not define new rules. Authority remains in the linked canonical sources.

## Do this always

- Use versioned patchers + wrappers (avoid manual edits): [Canonical Patcher/Wrapper Pattern](<{REL_PATCHER_WRAPPER_PATTERN}>)
- Follow the process constraints and enforcement posture: [Rules of Engagement](<{REL_RULES_OF_ENGAGEMENT}>)
- Keep the repo clean when running proofs/CI: [CI Cleanliness Invariant](<{REL_CI_CLEANLINESS}>)
- Maintain patcher/wrapper pairing expectations: [Patcher/Wrapper Pairing Gate](<{REL_PAIRING_GATE}>)
- If stuck, use safe recovery steps: [Recovery Workflows Index](<{REL_RECOVERY}>)

## When in doubt

- Start at: [CI Guardrails Index](<{REL_CI_GUARDRAILS_INDEX}>)
- Or use the map: [Canonical Indices Map](<{REL_CANONICAL_INDICES_MAP}>)
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


def _ensure_process_index_link() -> None:
    if not PROCESS_INDEX.exists():
        _refuse(f"missing required file: {PROCESS_INDEX}")

    existing = _read_text(PROCESS_INDEX)

    if PROCESS_BULLET_LINE in existing:
        return

    # Constraint: single bullet/link; no restructure.
    out = existing
    if not out.endswith("\n"):
        out += "\n"
    out += "\n" + PROCESS_BULLET_LINE + "\n"
    _write_text(PROCESS_INDEX, out)


def main() -> None:
    _ensure_doc()
    _ensure_process_index_link()


if __name__ == "__main__":
    main()
