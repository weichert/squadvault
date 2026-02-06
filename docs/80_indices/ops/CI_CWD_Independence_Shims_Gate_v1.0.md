[SV_CANONICAL_HEADER_V1]
Contract Name: CI CWD Independence Gate (Shims)
Version: v1.0
Status: CANONICAL

Defers To:
  - Canonical Operating Constitution (Tier 0)
  - CI Guardrails Index (Tier 1)

Default: Any behavior not explicitly permitted by this contract is forbidden.

—

## Purpose

Ensure scripts that rely on repo-local shims (notably `./scripts/py`) are **CWD-independent**.
In other words: the guardrails and proof suite must work even when invoked from a directory
other than repo root.

This prevents subtle breakage when tools run scripts via absolute paths, CI runners change CWD,
or developers call scripts from nested directories.

## Enforced By

- Gate script: `scripts/gate_cwd_independence_shims_v1.sh`
- CI runner: `scripts/prove_ci.sh`

## Definition

A script is CWD-independent if it:
- Resolves repo root deterministically, and
- Invokes repo-local shims via a stable path (e.g., `./scripts/py` from repo root, or absolute path).

## Notes

- This is a **runtime-enforced guardrail** (not advisory).
- If a future script needs repo root, it must discover it (e.g., by walking parents to `.git`).
