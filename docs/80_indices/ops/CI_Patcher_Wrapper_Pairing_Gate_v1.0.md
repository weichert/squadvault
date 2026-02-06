# CI Patcher/Wrapper Pairing Gate (v1.0)

Status: CANONICAL (Ops/CI Guardrail)

## Purpose

Enforce SquadVault's operational convention:

- A **versioned patcher** (`scripts/_patch_*.py`)
- must have a corresponding **versioned wrapper** (`scripts/patch_*.sh`)
- and vice-versa.

This reduces drift and preserves executable traceability.

## Enforcement

- Gate script: `scripts/check_patch_pairs_v1.sh`
- CI entrypoint: `scripts/prove_ci.sh`

## Rule

For tracked files:

- `scripts/patch_<name>.sh` MUST have `scripts/_patch_<name>.py`
- `scripts/_patch_<name>.py` MUST have `scripts/patch_<name>.sh`

## Legacy exceptions (audited)

Historical scripts may be exempted only via the tracked allowlist:

- `scripts/patch_pair_allowlist_v1.txt`

This allowlist is explicit, reviewable, and should not grow without clear rationale.
