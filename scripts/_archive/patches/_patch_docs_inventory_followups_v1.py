from __future__ import annotations

from pathlib import Path

README = Path("docs/canon_pointers/README.md")
GITIGNORE = Path(".gitignore")

DS_STORE_PATHS = [
    Path("docs/.DS_Store"),
    Path("docs/80_indices/.DS_Store"),
]

BEGIN = "<!-- CANONICALITY_RULES_v1_BEGIN -->"
END = "<!-- CANONICALITY_RULES_v1_END -->"

BLOCK = f"""{BEGIN}
## Canonicality and Document Authority

This repo contains multiple representations of SquadVault documentation (Markdown, PDF, DOCX).
To avoid drift and confusion, **treat these locations as authoritative**:

- **Canonical (binding source of truth):** `docs/canonical/**` (Markdown)
- **Operational invariants:** `docs/ops/invariants/**` (Markdown)
- **Indices / navigation (non-authoritative):** `docs/80_indices/**` (Markdown)
- **Process discipline:** `docs/process/**` (Markdown)

These locations are **not authoritative** (use only as reference or intake):

- **Imports / vendor drops:** `docs/_import/**`
- **Archives / prior versions:** `docs/90_archive/**`
- **Mixed-format snapshots (DOCX/PDF) under `docs/50_ops_and_build/**` and `docs/40_specs/**`**  
  (use as reference unless the same content is mirrored in `docs/canonical/**`)

Rule of thumb:
- If you need the **current rule**, prefer `docs/canonical/**` and `docs/ops/invariants/**`.
- If you need **how to execute safely**, prefer `docs/process/**` and the CI indices.
- If you need **historical context**, use `_import/` and `90_archive/`.

{END}
"""

def _ensure_gitignore_has_ds_store() -> None:
    if GITIGNORE.exists():
        text = GITIGNORE.read_text()
    else:
        text = ""

    lines = text.splitlines()
    if any(line.strip() == ".DS_Store" for line in lines):
        return

    # Append with a single trailing newline
    if text and not text.endswith("\n"):
        text += "\n"
    text += ".DS_Store\n"
    GITIGNORE.write_text(text)

def _remove_ds_store_files() -> None:
    for p in DS_STORE_PATHS:
        if p.exists():
            p.unlink()

def _ensure_readme_block() -> None:
    if not README.exists():
        raise RuntimeError(f"Missing required file: {README}")

    text = README.read_text()

    if BEGIN in text or END in text:
        # If markers exist, require an exact match to avoid silent reinterpretation.
        if BEGIN in text and END in text:
            existing_block = text.split(BEGIN, 1)[1].split(END, 1)[0]
            desired_block = BLOCK.split(BEGIN, 1)[1].split(END, 1)[0]
            if existing_block.strip() == desired_block.strip():
                return
            raise RuntimeError(f"{README} already contains canonicality markers but content differs; refusing to overwrite")
        raise RuntimeError(f"{README} has a partial canonicality marker; refusing to proceed")

    # Append block at end (simple, predictable, idempotent via markers)
    if text and not text.endswith("\n"):
        text += "\n"
    text += "\n" + BLOCK + "\n"
    README.write_text(text)

def main() -> None:
    _remove_ds_store_files()
    _ensure_gitignore_has_ds_store()
    _ensure_readme_block()

if __name__ == "__main__":
    main()
