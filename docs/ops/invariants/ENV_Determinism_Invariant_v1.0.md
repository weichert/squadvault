[SV_CANONICAL_HEADER_V1]
Invariant Name: ENV_Determinism_Invariant
Version: v1.0
Status: CANONICAL

Defers To:
  - CI_Cleanliness_Invariant_v1.0.md (as applicable)

Applies To:
  - scripts/prove_ci.sh (authoritative CI proof entrypoint)
  - All downstream proof scripts invoked by prove_ci.sh

Default: Any CI proof run outside this envelope is invalid.

—

# ENV_Determinism_Invariant (v1.0)

## Statement
All SquadVault CI proofs MUST execute inside a deterministic environment envelope to prevent nondeterministic output drift caused by locale, timezone, or Python hash variance.

## Required Deterministic Envelope
The following environment variables MUST be set exactly:

- `LC_ALL=C`
- `LANG=C`
- `TZ=UTC`
- `PYTHONHASHSEED=0`

## Enforcement
- `scripts/prove_ci.sh` MUST export the required envelope before invoking any proof scripts.
- `scripts/prove_ci.sh` MUST validate the envelope (gate) and FAIL LOUDLY if any value differs.

## Failure Mode
If any required variable is missing or differs, CI MUST exit non-zero with a clear error stating the expected and observed value.

## Rationale
Locale and timezone can change ordering and formatting behavior across shells and platforms.
Python hash randomization can introduce ordering variance in hash-based containers when relied upon indirectly.
This invariant constrains the execution surface so proofs remain auditable and reproducible.

## Non-Goals
This invariant does not change product logic, selection logic, or narrative logic. It constrains only the execution environment for proofs.
