[SV_CANONICAL_HEADER_V1]
Contract Name: Docs Integrity Gate Invariant
Version: v1.0
Status: CANONICAL — FROZEN

Defers To:
  - SquadVault — Canonical Operating Constitution (Tier 0)
  - SquadVault — Ops Shim & CWD Independence Contract (Ops)
  - SquadVault Development Playbook (MVP)

Default: Any behavior not explicitly permitted by this invariant is forbidden.

—

# SquadVault — Docs Integrity Gate Invariant (v1.0)

## Objective

Enforce **structural documentation governance invariants** for canonical SquadVault documentation.

This gate is **fail-closed** and **deterministic**.

## What This Gate Checks (Structural Only)

1) **Canonical header presence (structural)**
- For versioned canonical artifact-like filenames (containing `_vX.Y`) under canonical roots, require the canonical header marker:
  - `[SV_CANONICAL_HEADER_V1]`

2) **Duplicate canonical artifact basenames**
- If two canonical-looking artifacts in canonical roots share the same basename (case-sensitive), fail.

3) **Documentation map pointer resolution**
- Parse **text documentation maps only** (v1 allowlist) and extract repo-local `docs/...` and `scripts/...` references.
- Any referenced path must exist.

4) **Index coverage (minimal)**
- Ensure the CI guardrails index references:
  - this invariant doc, and
  - the docs integrity proof runner.

## Out of Scope (Explicit)

- Semantic interpretation or contradiction detection
- Doc refactors or folder reorganizations
- Auto-fixing or rewriting docs
- New product features or runtime behavior changes
- Any weakening of CI enforcement or bypassing proof registry

## Canonical Roots Allowlist (v1 Locked)

This gate scans only these canonical roots (v1):

- `docs/30_contract_cards/...`
- `docs/40_specs/...`
- `docs/80_indices/...`
- `docs/canon_pointers/...`
- `docs/canonical/...`

Expanding this list requires a v2 patch (explicit version bump).

## Determinism + Fail-Closed

- Sorted traversal everywhere
- Stable parsing heuristics
- No network access
- Fail closed on ambiguity or missing canonical targets

## Remediation

If the gate fails:
- Add `[SV_CANONICAL_HEADER_V1]` to missing versioned canonical artifacts.
- Rename/remove duplicates so basenames are unique across canonical roots.
- Fix documentation map references to point to existing repo-local paths.
- Ensure the CI guardrails index references this invariant and the proof runner.

## Canonical References

- CI Guardrails Index: `docs/80_indices/ops/CI_Guardrails_Index_v1.0.md`
- CI Proof Surface Registry: `docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md`
- Docs Integrity Proof Runner: `scripts/prove_docs_integrity_v1.sh`
