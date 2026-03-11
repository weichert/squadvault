from __future__ import annotations

from pathlib import Path

DOC = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

BEGIN = "<!-- SV_BEGIN: ops_entrypoints_hub (v1) -->"
END = "<!-- SV_END: ops_entrypoints_hub (v1) -->"

EXPECTED_SECTION = """\
<!-- SV_BEGIN: ops_entrypoints_hub (v1) -->
## Ops Entrypoints (Canonical)

If you are unsure where to start, use this section.

- [Ops Entrypoints Hub (v1.0)](Ops_Entrypoints_Hub_v1.0.md)
- [Canonical Indices Map (v1.0)](Canonical_Indices_Map_v1.0.md)
- [Process Discipline Index (v1.0)](Process_Discipline_Index_v1.0.md)
- [Recovery Workflows Index (v1.0)](Recovery_Workflows_Index_v1.0.md)
- [Ops Rules — One Page (v1.0)](Ops_Rules_One_Page_v1.0.md)
- [New Contributor Orientation (10 min) (v1.0)](New_Contributor_Orientation_10min_v1.0.md)
<!-- SV_END: ops_entrypoints_hub (v1) -->
"""

ANCHOR = "\n## Active Guardrails\n"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write(p: Path, text: str) -> None:
    if not text.endswith("\n"):
        text += "\n"
    p.write_text(text, encoding="utf-8")


def _refuse(msg: str) -> None:
    raise SystemExit(f"REFUSE-ON-DRIFT: {msg}")


def _extract_bounded(text: str) -> str | None:
    b = text.find(BEGIN)
    if b == -1:
        return None
    e = text.find(END, b)
    if e == -1:
        _refuse(f"found {BEGIN} but missing {END}")
    e = e + len(END)
    # include trailing newline if present
    if e < len(text) and text[e : e + 1] == "\n":
        e += 1
    return text[b:e]


def main() -> None:
    if not DOC.exists():
        _refuse(f"missing required file: {DOC}")

    existing = _read(DOC)

    bounded = _extract_bounded(existing)
    if bounded is not None:
        if bounded != EXPECTED_SECTION and bounded != (EXPECTED_SECTION + "\n"):
            _refuse(f"{DOC} ops_entrypoints_hub section exists but does not match expected canonical contents.")
        return

    if ANCHOR not in existing:
        _refuse("could not find anchor '## Active Guardrails' to insert canonical ops entrypoints section.")

    out = existing.replace(ANCHOR, "\n" + EXPECTED_SECTION + ANCHOR, 1)
    _write(DOC, out)


if __name__ == "__main__":
    main()
