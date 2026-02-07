# Canon Pointers (Repo Policy)

This repository does **not** vendor canonical narrative/contract documents under a `/canon` tree.

Canonical documents live as:
- Project-file artifacts (ChatGPT project files / data-room exports)

This repo stores:
- Implementation source of truth (code + tests)
- Deterministic gates
- **Pointers** to canonical docs (this folder)

If a `/canon` folder appears in the repo, treat it as accidental and remove it unless explicitly approved.

<!-- CANONICALITY_RULES_v1_BEGIN -->
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

<!-- CANONICALITY_RULES_v1_END -->

