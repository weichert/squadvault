# SquadVault — CI + Docs Hardening Freeze (v1.0)

Status: **FROZEN (ops)**

This addendum marks the completion of a hardening pass that enforces:
- CI cleanliness (no working-tree mutation)
- Deterministic environment envelope
- Filesystem ordering determinism gate
- Time & timestamp determinism gate
- Docs housekeeping audit (deterministic scan; structured outputs)

## Policy (frozen)

All changes to `docs/` or CI guardrails must be implemented through:
- A **versioned patcher** (`scripts/_patch_*.py`), and
- A **versioned wrapper** (`scripts/patch_*.sh`),
so that changes are auditable, repeatable, and CI-safe.

Inline/manual edits are permitted only for emergency repair, and must be followed by a patcher+wrapper retrofit.
