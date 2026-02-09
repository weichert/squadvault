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
