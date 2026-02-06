from __future__ import annotations

from pathlib import Path
import re

INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

NAC_START = "<!-- SV_PATCH: nac fingerprint preflight doc (v1) -->"
NAC_END   = "<!-- /SV_PATCH: nac fingerprint preflight doc (v1) -->"

LOCAL_ONLY_HEADING = "## Local-only helpers (not invoked by CI)\n"
LOCAL_ONLY_SENTINEL = "_CI never invokes anything in this section._"

ACTIVE_GUARDRAILS_HEADING_RE = re.compile(r"(?m)^## Active Guardrails\s*$")


def _extract_nac_block(txt: str) -> tuple[str | None, str]:
    """
    Returns (nac_block_or_none, txt_without_block).
    Includes trailing whitespace/newlines after the block, but not more than needed.
    """
    pat = re.compile(
        re.escape(NAC_START) + r".*?" + re.escape(NAC_END) + r"\n?",
        re.DOTALL,
    )
    m = pat.search(txt)
    if not m:
        return None, txt
    block = txt[m.start():m.end()]
    new_txt = txt[:m.start()] + txt[m.end():]
    return block.rstrip() + "\n", new_txt


def _insert_after_active_guardrails(txt: str, block: str) -> str:
    if not block.strip():
        return txt

    # If already present somewhere, don't duplicate.
    if NAC_START in txt and NAC_END in txt:
        return txt

    m = ACTIVE_GUARDRAILS_HEADING_RE.search(txt)
    if not m:
        # If heading missing, append at end (shouldn't happen, but keep safe).
        if not txt.endswith("\n"):
            txt += "\n"
        return txt + "\n## Active Guardrails\n\n" + block + "\n"

    insert_pos = m.end()
    # Ensure exactly one blank line after heading, then block, then one blank line.
    before = txt[:insert_pos].rstrip() + "\n\n"
    after = txt[insert_pos:].lstrip("\n")
    return before + block.rstrip() + "\n\n" + after


def _ensure_local_only_boundary_line(txt: str) -> str:
    if LOCAL_ONLY_HEADING not in txt:
        return txt

    before, after = txt.split(LOCAL_ONLY_HEADING, 1)

    # If sentinel already exists close to the top of that section, do nothing.
    head = after[:400]
    if LOCAL_ONLY_SENTINEL in head:
        return txt

    # Insert boundary sentence immediately after the heading.
    insertion = LOCAL_ONLY_SENTINEL + "\n\n"
    # Keep the rest as-is (but avoid accidental leading blankline explosion).
    after = after.lstrip("\n")
    return before + LOCAL_ONLY_HEADING + insertion + after


def _normalize_spacing(txt: str) -> str:
    # Reduce 3+ blank lines to 2 (conservative).
    txt = re.sub(r"\n{3,}", "\n\n", txt)

    # Ensure file ends with newline.
    txt = txt.rstrip() + "\n"
    return txt


def main() -> None:
    if not INDEX.exists():
        raise SystemExit(f"missing: {INDEX}")

    txt = INDEX.read_text(encoding="utf-8")

    nac_block, txt = _extract_nac_block(txt)
    if nac_block:
        txt = _insert_after_active_guardrails(txt, nac_block)

    txt = _ensure_local_only_boundary_line(txt)
    txt = _normalize_spacing(txt)

    INDEX.write_text(txt, encoding="utf-8")


if __name__ == "__main__":
    main()
