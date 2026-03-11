from __future__ import annotations

from pathlib import Path

INDEX_DOC = Path("docs/80_indices/ops/Canonical_Indices_Map_v1.0.md")
CI_INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

# Links are relative to docs/80_indices/ops/
REL_CI_GUARDRAILS_INDEX = "CI_Guardrails_Index_v1.0.md"
REL_PROCESS_DISCIPLINE = "Process_Discipline_Index_v1.0.md"
REL_RECOVERY_WORKFLOWS = "Recovery_Workflows_Index_v1.0.md"
REL_PAIRING_GATE_DOC = "CI_Patcher_Wrapper_Pairing_Gate_v1.0.md"
REL_CI_CLEANLINESS = "CI_Cleanliness_Invariant_v1.0.md"

CI_BULLET_LINE = "- [Canonical Indices Map (v1.0)](Canonical_Indices_Map_v1.0.md)"

EXPECTED_INDEX_DOC = f"""# Canonical Indices Map (v1.0)

Purpose:
A curated map of canonical ops indices so you can find the right entrypoint fast.

This is an index only. Authority remains in the linked canonical documents.

## Primary entrypoints

- [CI Guardrails Index](<{REL_CI_GUARDRAILS_INDEX}>)
- [Process Discipline Index](<{REL_PROCESS_DISCIPLINE}>)
- [Recovery Workflows Index](<{REL_RECOVERY_WORKFLOWS}>)

## CI discipline references

- [CI Patcher/Wrapper Pairing Gate](<{REL_PAIRING_GATE_DOC}>)
- [CI Cleanliness Invariant](<{REL_CI_CLEANLINESS}>)
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
