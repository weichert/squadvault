from __future__ import annotations

from pathlib import Path
import re
from typing import Dict, List, Tuple, Optional

INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

TOC_HEADING_LINE = "## Contents"
HOW_HEADING_LINE = "## How to Read This Index"

HOW_TO_READ_BODY = """\
- **Active Guardrails** are enforced by CI and will fail builds if violated.
- Sections explicitly labeled **local-only** document helpers or hygiene practices that are *not* invoked by CI.
- If a guardrail appears here, it must correspond to a concrete enforcement mechanism.
""".rstrip() + "\n"


def _slugify_github_like(heading_text: str) -> str:
    s = heading_text.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-{2,}", "-", s)
    return s.strip("-")


def _extract_top_level_sections(txt: str) -> tuple[str, List[Tuple[str, str]]]:
    matches = list(re.finditer(r"(?m)^##\s+.*$", txt))
    if not matches:
        return (txt, [])

    first = matches[0].start()
    preamble = txt[:first]
    sections: List[Tuple[str, str]] = []

    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(txt)
        block = txt[start:end]
        lines = block.splitlines(True)
        heading_line = lines[0].rstrip("\n")
        body = "".join(lines[1:])
        sections.append((heading_line, body))

    return preamble, sections


def _heading_key(heading_line: str) -> str:
    h = heading_line.strip()
    if h.startswith("##"):
        h = h[2:].strip()
    return h.lower()


def _build_contents_body() -> str:
    # Keep this focused; this is a mini TOC for major sections.
    toc_targets = [
        ("Operator Safety Note (Build Mode)", "Operator Safety Note (Build Mode)"),
        ("Active Guardrails", "Active Guardrails"),
        ("Proof Surface", "Proof Surface"),
        ("Notes", "Notes"),
        ("Ops Bundles", "Ops Bundles"),
        ("Guardrails Development", "Guardrails Development"),
        ("CWD Independence", "CWD Independence"),
        ("Local-only helpers (not invoked by CI)", "Local-only helpers (not invoked by CI)"),
        ("Local Workstation Hygiene", "Local Workstation Hygiene"),
    ]

    lines: List[str] = []
    for visible, heading in toc_targets:
        lines.append(f"- [{visible}](#{_slugify_github_like(heading)})")

    return "\n".join(lines).rstrip() + "\n"


def _strip_duplicate_sections(
    sections: List[Tuple[str, str]],
) -> List[Tuple[str, str]]:
    """
    Remove ALL occurrences of top-level:
      - ## Contents
      - ## How to Read This Index
    """
    filtered: List[Tuple[str, str]] = []
    for h, b in sections:
        k = _heading_key(h)
        if k in ("contents", "how to read this index"):
            continue
        filtered.append((h, b))
    return filtered


def _ensure_preamble_how_to_read(preamble: str) -> str:
    """
    Build top preamble block as:
      intro
      How-to-read
    (Operator Safety and Contents come next as real sections.)
    """
    txt = preamble.rstrip() + "\n\n"
    how_block = HOW_HEADING_LINE + "\n\n" + HOW_TO_READ_BODY + "\n"
    txt += how_block
    return txt.rstrip() + "\n"


def _reorder_sections_with_contents_after_operator_safety(
    preamble: str, sections: List[Tuple[str, str]]
) -> str:
    desired = [
        "operator safety note (build mode)",
        "active guardrails",
        "proof surface",
        "notes",
        "ops bundles",
        "guardrails development",
        "cwd independence",
        "local-only helpers (not invoked by ci)",
        "local workstation hygiene",
    ]

    sec_by_key: Dict[str, Tuple[str, str]] = {_heading_key(h): (h, b) for (h, b) in sections}

    python_shim_key = "python shim"
    python_shim_block = sec_by_key.get(python_shim_key)

    contents_block: Tuple[str, str] = (TOC_HEADING_LINE, "\n" + _build_contents_body() + "\n")

    used_keys = set()
    reordered: List[Tuple[str, str]] = []

    for k in desired:
        if k in sec_by_key:
            reordered.append(sec_by_key[k])
            used_keys.add(k)

            # Immediately after Operator Safety, insert Contents.
            if k == "operator safety note (build mode)":
                reordered.append(contents_block)
                used_keys.add("contents")

            # Keep Python Shim immediately after Ops Bundles
            if k == "ops bundles" and python_shim_block is not None:
                reordered.append(python_shim_block)
                used_keys.add(python_shim_key)

    # Append any remaining sections in original order (stable)
    for h, b in sections:
        k = _heading_key(h)
        if k not in used_keys and k != python_shim_key:
            reordered.append((h, b))
            used_keys.add(k)

    out = preamble.rstrip() + "\n"
    for h, b in reordered:
        out = out.rstrip() + "\n\n" + h + "\n" + b.lstrip("\n")

    return out.rstrip() + "\n"


def main() -> None:
    if not INDEX.exists():
        raise SystemExit(f"missing: {INDEX}")

    txt = INDEX.read_text(encoding="utf-8")
    preamble, sections = _extract_top_level_sections(txt)

    sections2 = _strip_duplicate_sections(sections)
    preamble2 = _ensure_preamble_how_to_read(preamble)

    out = _reorder_sections_with_contents_after_operator_safety(preamble2, sections2)

    # Light whitespace normalization only
    out = re.sub(r"\n{4,}", "\n\n\n", out).rstrip() + "\n"
    INDEX.write_text(out, encoding="utf-8")


if __name__ == "__main__":
    main()
