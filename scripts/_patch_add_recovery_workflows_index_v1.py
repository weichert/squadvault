from __future__ import annotations

from pathlib import Path

INDEX_DOC = Path("docs/80_indices/ops/Recovery_Workflows_Index_v1.0.md")
CI_INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

# Relative links from docs/80_indices/ops/
REL_CI_GUARDRAILS_INDEX = "CI_Guardrails_Index_v1.0.md"
REL_CI_CLEANLINESS = "CI_Cleanliness_Invariant_v1.0.md"
REL_RULES_OF_ENGAGEMENT = "../../process/rules_of_engagement.md"
REL_PATCHER_WRAPPER_PATTERN = "../../process/Canonical_Patcher_Wrapper_Pattern_v1.0.md"
REL_PAIRING_GATE_DOC = "CI_Patcher_Wrapper_Pairing_Gate_v1.0.md"

CI_BULLET_LINE = "- [Recovery Workflows Index (v1.0)](Recovery_Workflows_Index_v1.0.md)"

EXPECTED_INDEX_DOC = f"""# Recovery Workflows Index (v1.0)

Purpose:
A 2am index of *safe* recovery workflows when CI, cleanliness, or patch discipline blocks you.

This is an index only. Authority remains in the linked canonical documents.

## Primary entrypoints

- [CI Guardrails Index](<{REL_CI_GUARDRAILS_INDEX}>)
- [CI Cleanliness Invariant](<{REL_CI_CLEANLINESS}>)

## Process authority

- [Rules of Engagement](<{REL_RULES_OF_ENGAGEMENT}>)
- [Canonical Patcher/Wrapper Pattern](<{REL_PATCHER_WRAPPER_PATTERN}>)
- [Patcher/Wrapper Pairing Gate](<{REL_PAIRING_GATE_DOC}>)

## Common recovery moves (safe, explicit)

- Inspect working tree:
  - `git status --porcelain=v1`
- Discard ALL tracked changes (worktree + index):
  - `git restore --staged --worktree -- .`
- Remove untracked files (destructive):
  - `git clean -fd`
- Re-run proof from a clean repo:
  - `bash scripts/prove_ci.sh`

Notes:
- If a patcher refuses-on-drift, do not “edit around it.” Update the patcher/wrapper to match the new canonical intent.
- Prefer patchers/wrappers over manual doc edits; keep changes versioned and reproducible.
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
