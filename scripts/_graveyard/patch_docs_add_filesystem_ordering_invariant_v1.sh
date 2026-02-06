#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: docs add filesystem ordering determinism invariant (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

OUT="docs/ops/invariants/Filesystem_Ordering_Determinism_Invariant_v1.0.md"
mkdir -p "$(dirname "${OUT}")"

cat > "${OUT}" <<'MD'
[SV_CANONICAL_HEADER_V1]
Contract Name: Filesystem Ordering Determinism Invariant
Version: v1.0
Status: CANONICAL

Defers To:
  - ENV Determinism Invariant (Tier-2) (as applicable)
  - Canonical Operating Constitution (Tier-0)

Default: Any behavior not explicitly permitted by this invariant is forbidden.

—

# Filesystem Ordering Determinism Invariant (v1.0)

## Purpose

Prevent nondeterministic behavior caused by filesystem enumeration order (directory traversal order, glob expansion order, or unordered listing APIs) that can affect:

- generated artifact contents
- approval/export stability
- test outcomes
- CI reproducibility

This invariant is a **hard gate** enforced in CI.

## Scope

Applies to:

- runtime and proof execution paths in `src/`
- operational scripts in `scripts/`

Explicitly excludes:

- patch tooling and diagnostics under `scripts/` matching:
  - `scripts/patch_*`
  - `scripts/_patch_*`
  - `scripts/_diag_*`

(Those tools may perform heuristic discovery; they are not runtime/proof determinism surface.)

## Required Behavior

### Shell

Any construct that uses filesystem enumeration as **data** MUST be explicitly ordered.

Forbidden unless explicitly sorted:

- `find ... | while read ...` (must add an ordering step, e.g. `| sort`)
- `ls ... | while read ...` and `ls ... | xargs ...` (prefer avoid `ls` as data; if used, order explicitly)

### Python

Unordered enumeration APIs MUST be ordered **at the callsite** before iteration:

- `Path.glob(...)` / `Path.rglob(...)` must be wrapped in `sorted(...)` (or an equivalent explicit ordering).
- `os.walk(...)` must sort both `dirnames` and `filenames` for deterministic traversal:
  - `dirs.sort()`
  - `files.sort()`

If ordering does not affect behavior, a waiver may be used (see below), but waivers are expected to be rare.

## Enforcement

This invariant is enforced by:

- `scripts/check_filesystem_ordering_determinism.sh`

The guardrail runs within the authoritative CI entrypoint:

- `scripts/prove_ci.sh`

### Fail Loud Requirement

Any detection failure MUST fail CI.

Additionally, **any grep stderr or pattern error** during the guardrail scan is treated as fatal (to avoid silent false-pass).

## Waiver Mechanism

To waive a specific flagged line, annotate it with:

- `# SV_ALLOW_UNSORTED_FS_ORDER`

Use only when ordering provably does not affect behavior and cannot leak into outputs.

## Determinism Compatibility

This invariant is designed to operate inside the deterministic execution envelope:

- `LC_ALL=C`, `LANG=C`, `TZ=UTC`, `PYTHONHASHSEED=0`
MD

echo "OK: wrote ${OUT}"
