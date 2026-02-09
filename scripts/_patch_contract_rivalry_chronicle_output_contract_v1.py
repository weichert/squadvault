from __future__ import annotations

from pathlib import Path

DOC = Path("docs/contracts/rivalry_chronicle_output_contract_v1.md")

TEXT = """# Rivalry Chronicle Output Contract (v1)

Status: CANONICAL (contract)

This contract locks the **exported** output structure for Rivalry Chronicle artifacts so downstream creative tooling can rely on stable fields.

## Scope

Applies to the exported Markdown file produced by the Rivalry Chronicle export step, e.g.:

- `artifacts/exports/<league_id>/<season>/week_<WEEK>/rivalry_chronicle_v1__approved_latest.md`

(Exact root dir may vary by environment; the **filename + content structure** is what is contractual.)

## Invariants

### File must be Markdown text
- UTF-8 text
- Unix newlines preferred (`\\n`)
- No binary content

### Required top-of-file header block
The file must begin with a stable metadata header block using this exact marker format:

- Line 1: `# Rivalry Chronicle (v1)`
- Within the first ~40 lines, there must exist a metadata section that includes:
  - `League:` (string)
  - `Season:` (int)
  - `Week:` (int)
  - `State:` must be `APPROVED`
  - `Artifact Type:` must be `RIVALRY_CHRONICLE_V1`

(Exact spacing may vary, but keys must be present exactly once.)

### Required sections
The document must contain these headings in order (additional subheadings allowed):

1. `## Matchup Summary`
2. `## Key Moments`
3. `## Stats & Nuggets`
4. `## Closing`

### Disallowed patterns
- Must not include `(autofill)` placeholder text
- Must not include raw debug dumps (e.g., `{'id': ...}` python dict repr blocks)
- Must not include absolute local filesystem paths

## Versioning rules
- Future changes require a new versioned contract file (v2, v3...)
- Silent drift is forbidden.

"""
def main() -> None:
    DOC.parent.mkdir(parents=True, exist_ok=True)
    if DOC.exists():
        cur = DOC.read_text(encoding="utf-8")
        if cur == TEXT:
            return
    DOC.write_text(TEXT, encoding="utf-8")

if __name__ == "__main__":
    main()
