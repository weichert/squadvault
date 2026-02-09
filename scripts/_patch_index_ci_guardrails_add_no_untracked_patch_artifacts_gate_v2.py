from __future__ import annotations

from pathlib import Path
import re
import sys

DOC = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

NEW_BULLET = "- scripts/gate_no_untracked_patch_artifacts_v1.sh — Guardrail: fail if untracked patch artifacts exist (v1)"

HEADER_RE = re.compile(r"^##\s+CI guardrails entrypoints\s+\(bounded\)\s*$", re.M)

def main() -> int:
    if not DOC.exists():
        print(f"ERROR: missing {DOC}", file=sys.stderr)
        return 2

    text = DOC.read_text(encoding="utf-8")

    hm = HEADER_RE.search(text)
    if not hm:
        print(
            "ERROR: Could not find section header '## CI guardrails entrypoints (bounded)'.\n"
            "Refusing to patch to avoid inserting in the wrong place.",
            file=sys.stderr,
        )
        return 3

    start = hm.end()
    next_header = re.search(r"^\s*##\s+", text[start:], flags=re.M)
    end = start + (next_header.start() if next_header else len(text[start:]))

    section = text[start:end]
    lines = section.splitlines()

    first_bullet_i = None
    for i, ln in enumerate(lines):
        if ln.strip().startswith("- "):
            first_bullet_i = i
            break

    if first_bullet_i is None:
        print(
            "ERROR: Found the bounded entrypoints header but no bullet list in that section.\n"
            "Refusing to patch.",
            file=sys.stderr,
        )
        return 4

    j = first_bullet_i
    while j < len(lines) and lines[j].strip().startswith("- "):
        j += 1

    bullet_run = lines[first_bullet_i:j]

    if NEW_BULLET not in bullet_run:
        bullet_run.append(NEW_BULLET)

    bullet_run_sorted = sorted(bullet_run)

    new_lines = lines[:first_bullet_i] + bullet_run_sorted + lines[j:]
    new_section = "\n".join(new_lines)
    if section.endswith("\n"):
        new_section += "\n"

    new_text = text[:start] + new_section + text[end:]
    DOC.write_text(new_text, encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
