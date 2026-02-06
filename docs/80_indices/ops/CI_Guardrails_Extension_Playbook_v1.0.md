[SV_CANONICAL_HEADER_V1]
Contract Name: CI Guardrails Extension Playbook
Version: v1.0
Status: CANONICAL

Defers To:
  - Canonical Operating Constitution (Tier 0)
  - CI Guardrails Index (Tier 1)

Default: Any behavior not explicitly permitted by this contract is forbidden.

—

## Purpose

Provide a repeatable, low-risk workflow for adding new CI guardrails so the system remains:
- deterministic
- discoverable
- enforceable
- audited via patchers/wrappers

## Rule of Thumb

**If it’s in the CI Guardrails Index, it must be runtime-enforced.**
If it’s only advice, it belongs elsewhere (or in a local-only helper).

## Add a New CI Guardrail (Checklist)

1) Implement the guardrail as a concrete script (gate) OR as a deterministic check inside an existing gate.
   - Prefer a dedicated `scripts/gate_*.sh` when the behavior is distinct.

2) Wire it into `scripts/prove_ci.sh` so CI actually runs it.

3) Create a canonical doc under `docs/80_indices/ops/` describing:
   - Purpose
   - Enforced by (exact scripts)
   - What constitutes pass/fail

4) Add a link to the doc in `docs/80_indices/ops/CI_Guardrails_Index_v1.0.md`.

5) Provide a versioned patcher+wrapper pair for all repo changes:
   - `scripts/_patch_*.py` + `scripts/patch_*.sh`
   - wrappers run via `./scripts/py` and include `bash -n` checks

6) Verify from a clean repo:
   - `./scripts/prove_ci.sh`

7) Commit with a message that encodes scope + version (v1, v2…).

## When Something Is Local-Only

If the goal is workstation hygiene (shell init quirks, tool setup, etc.):
- write a **local-only helper** under `scripts/prove_local_*.sh` (or similar),
- link it in the CI Guardrails Index under a clearly labeled local-only section,
- do NOT invoke it from `prove_ci.sh`.
