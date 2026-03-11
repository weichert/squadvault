from __future__ import annotations

from pathlib import Path

DOC = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

BEGIN = "<!-- SV_BEGIN: ops_entrypoints_toc (v1) -->"
END = "<!-- SV_END: ops_entrypoints_toc (v1) -->"

EXPECTED_BLOCK = """\
<!-- SV_BEGIN: ops_entrypoints_toc (v1) -->
- [Ops Entrypoints (Canonical)](#ops-entrypoints-canonical)
<!-- SV_END: ops_entrypoints_toc (v1) -->
"""

ANCHOR_LINE = "- [Active Guardrails](#active-guardrails)\n"


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
    if e < len(text) and text[e : e + 1] == "\n":
        e += 1
    return text[b:e]


def main() -> None:
    if not DOC.exists():
        _refuse(f"missing required file: {DOC}")

    s = _read(DOC)

    bounded = _extract_bounded(s)
    if bounded is not None:
        if bounded != EXPECTED_BLOCK and bounded != (EXPECTED_BLOCK + "\n"):
            _refuse(f"{DOC} ops_entrypoints_toc section exists but does not match expected canonical contents.")
        return

    if ANCHOR_LINE not in s:
        _refuse("could not find TOC anchor line '- [Active Guardrails](#active-guardrails)' to insert ops entrypoints TOC entry.")

    out = s.replace(ANCHOR_LINE, EXPECTED_BLOCK + "\n" + ANCHOR_LINE, 1)
    _write(DOC, out)


if __name__ == "__main__":
    main()
