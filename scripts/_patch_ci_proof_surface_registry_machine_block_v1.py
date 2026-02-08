from __future__ import annotations

from pathlib import Path
import subprocess
import sys

DOC = Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md")

BEGIN = "<!-- SV_PROOF_SURFACE_LIST_v1_BEGIN -->"
END = "<!-- SV_PROOF_SURFACE_LIST_v1_END -->"

SECTION_HEADER = "## Canonical Proof Surface List (Machine-Managed)\n"

def _git_ls_files(pattern: str) -> list[str]:
    out = subprocess.check_output(["git", "ls-files", pattern], text=True)
    items = [line.strip() for line in out.splitlines() if line.strip()]
    items.sort()
    return items

def _render_block(items: list[str]) -> str:
    lines = [BEGIN, ""]
    for p in items:
        lines.append(f"- {p}")
    lines.append("")
    lines.append(END)
    return "\n".join(lines) + "\n"

def _replace_between_markers(text: str, replacement_block: str) -> str:
    if BEGIN not in text or END not in text:
        return text

    pre, rest = text.split(BEGIN, 1)
    _, post = rest.split(END, 1)
    # Keep markers canonical from replacement_block
    return pre.rstrip("\n") + "\n" + replacement_block + post.lstrip("\n")

def _insert_new_section(text: str, block: str) -> str:
    insert = (
        SECTION_HEADER
        + "This block is updated by `scripts/patch_ci_proof_surface_registry_machine_block_v1.sh`.\n"
        + "Do not edit manually.\n\n"
        + block
        + "\n"
    )

    # Insert after first H1 line if present, else at top.
    lines = text.splitlines(keepends=True)
    if lines and lines[0].lstrip().startswith("#"):
        # insert after first heading block (first line + following blank line if present)
        idx = 1
        if idx < len(lines) and lines[idx].strip() == "":
            idx += 1
        return "".join(lines[:idx]) + "\n" + insert + "".join(lines[idx:])
    return insert + text

def main() -> int:
    if not DOC.exists():
        print(f"ERROR: missing doc: {DOC}", file=sys.stderr)
        return 1

    items = _git_ls_files("scripts/prove_*.sh")
    block = _render_block(items)

    original = DOC.read_text(encoding="utf-8")
    if BEGIN in original and END in original:
        updated = _replace_between_markers(original, block)
    else:
        updated = _insert_new_section(original, block)

    if updated != original:
        DOC.write_text(updated, encoding="utf-8")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
