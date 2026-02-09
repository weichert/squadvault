from __future__ import annotations

from pathlib import Path

DOC = Path("docs/contracts/Contract_Markers_v1.0.md")
README = Path("docs/contracts/README.md")

DOC_TEXT = """\
# Contract Markers Policy (v1.0)

## Purpose

SquadVault uses lightweight “contract markers” in source files to link implementation code to
a versioned contract document in `docs/contracts/`.

This policy defines the only supported marker format and how gates interpret it.

## Marker Format

Markers are **comment-only** lines. They MUST appear exactly as comment-prefixed lines
to be considered declarations:

- `# SV_CONTRACT_NAME: <name>`
- `# SV_CONTRACT_DOC_PATH: <repo-relative path>`

### Notes

- The gate **MUST ignore** marker-like text that appears inside string literals.
- The doc path MUST be **repo-relative** (no leading `/`) and MUST resolve to an existing file.
- If either marker is present, **both** markers are required.

## Where Markers Belong

Markers are intended for **implementation scripts** that materially produce or validate a contract,
for example:

- export/assembly generators
- output-contract gates and proofs

Markers SHOULD NOT appear in “tooling about tooling” (patchers that edit gates, CI wrappers, etc.)
unless that tooling itself has a contract that must be indexed.

## Enforcement

The Contract Linkage Gate enforces:

- comment-only marker detection
- both-markers-present rule
- repo-relative doc-path rule
- doc-path must exist
"""

def ensure_doc() -> None:
    DOC.parent.mkdir(parents=True, exist_ok=True)
    if DOC.exists():
        existing = DOC.read_text(encoding="utf-8")
        if existing == DOC_TEXT:
            return
    DOC.write_text(DOC_TEXT, encoding="utf-8")

def ensure_readme_link() -> None:
    README.parent.mkdir(parents=True, exist_ok=True)

    link_line = "- Contract_Markers_v1.0.md — Contract markers policy (comment-only; linkage rules) (v1.0)\n"

    if README.exists():
        txt = README.read_text(encoding="utf-8")
    else:
        txt = ""

    if "Contract_Markers_v1.0.md" in txt:
        return

    lines = txt.splitlines(True)

    # Prefer to insert into an existing "Versioned" section if present.
    heading_idx = None
    for i, line in enumerate(lines):
        if line.strip() == "## Versioned Contracts":
            heading_idx = i
            break

    if heading_idx is None:
        # Create a minimal index if the README is missing or has unknown structure.
        new_txt = txt
        if new_txt and not new_txt.endswith("\n"):
            new_txt += "\n"
        if "## Versioned Contracts" not in new_txt:
            if new_txt:
                new_txt += "\n"
            new_txt += "## Versioned Contracts\n\n"
        new_txt += link_line
        README.write_text(new_txt, encoding="utf-8")
        return

    # Insert after heading and any immediate blank line(s).
    insert_at = heading_idx + 1
    while insert_at < len(lines) and lines[insert_at].strip() == "":
        insert_at += 1

    # If there is already a bullet list, insert at the start of that list; else insert a blank line then the bullet.
    if insert_at < len(lines) and lines[insert_at].lstrip().startswith("- "):
        lines.insert(insert_at, link_line)
    else:
        # Ensure there is a blank line between heading and bullets.
        if insert_at == heading_idx + 1:
            lines.insert(insert_at, "\n")
            insert_at += 1
        lines.insert(insert_at, link_line)

    README.write_text("".join(lines), encoding="utf-8")

def main() -> int:
    ensure_doc()
    ensure_readme_link()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
