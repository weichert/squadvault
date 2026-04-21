# Finding 2 — ops entrypoints gate retired (resolution)

**Date:** 2026-04-22
**Session:** Finding 2 fix pass.
**Closes:** Finding 2 classified in
`_observations/OBSERVATIONS_2026_04_22_FINDING2_OPS_ENTRYPOINTS_GATE_CLASSIFICATION.md`,
originally flagged in
`_observations/OBSERVATIONS_2026_04_20_PRECOMMIT_GATE_PARITY_DEFERRED_FINDINGS.md`.
**Status:** FINAL.

---

## Decision

**Option 2 — retire.** `scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh`
has been moved to `scripts/_archive/unreferenced/`, and every live
reference across the registry, prove_ci orchestration, and ordering-lock
infrastructure has been removed. The surface fingerprint has been
regenerated accordingly.

---

## Why retire (archaeology summary)

~20 minutes of archaeology on commit `0faf0c0` ("Phase 7.8 — CI
Guardrail Registry Completeness Lock", 2026-03-10) established that
the deletion of the `ops_entrypoints_toc` and `ops_entrypoints_hub`
marker families from `docs/80_indices/ops/CI_Guardrails_Index_v1.0.md`
was **deliberate scope reduction**, not accidental regression.

The relevant commit sequence:

- **Phase 7.7** (`3a7b389`) — add CI guardrails registry AUTHORITY gate
- **Phase 7.8** (`0faf0c0`) — add CI guardrails registry COMPLETENESS
  LOCK gate, narrow `CI_Guardrails_Index_v1.0.md` from 219 lines to a
  pure registry-only surface (-270/+1 lines)
- **Phase 7.9** (`e49f757`) — add CI guardrails SURFACE FREEZE gate
- **Phases 7.10–7.12** — repair/lock follow-ups

The index file's canonical shape at HEAD is a single
`SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN`/`_END` block containing ~57
gate entries. No title, no prose, no contents, no TOC. Adding the
deleted marker families back would mean inserting prose content into an
index that was deliberately stripped — direct conflict with Phase 7.8
design, and the surface-freeze gate would demand fingerprint rebase
anyway. Rewriting the gate for a new invariant would be a new gate
wearing an old name. Retirement is the archaeology-indicated shape.

Option C (revive an installer) was never on the table here — that was
the hook-installer analogy from an earlier session. The three shapes
for Finding 2 were Option 1 (re-introduce markers), Option 2 (retire),
Option 3 (rewrite). Option 2 won.

---

## What was retired

### Archived
- `scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh` →
  `scripts/_archive/unreferenced/gate_ci_guardrails_ops_entrypoints_section_v2.sh`
  (moved via `git mv` so blame is preserved; lives next to its v1
  predecessor which was already archived there).

### Live references removed

| File | Line | Shape |
|---|---|---|
| `scripts/prove_ci.sh` | 90 | invocation line |
| `docs/80_indices/ops/CI_Guardrails_Index_v1.0.md` | 12 | registry entry |
| `docs/80_indices/ops/CI_Guardrail_Entrypoint_Labels_v1.tsv` | 47 | TSV row |
| `docs/80_indices/ops/CI_Guardrails_Ops_Cluster_Order_v1.tsv` | 5 | TSV row |
| `scripts/gate_ci_guardrails_execution_order_lock_v1.sh` | 31 | expected-list entry |
| `scripts/gate_ci_guardrails_ops_cluster_canonical_v1.sh` | 18 | expected-list entry |
| `scripts/gate_ci_guardrails_ops_entrypoint_order_lock_v1.sh` | 19 | expected-list entry |

### Fingerprint regenerated
- `docs/80_indices/ops/CI_Guardrails_Surface_Fingerprint_v1.txt` —
  regenerated via `scripts/py scripts/gen_ci_guardrails_surface_fingerprint_v1.py`.

The retire was necessarily atomic. The three ordering-lock gates each
had a hardcoded expected-list snapshot of invocations containing the
target gate's invocation line; removing the gate from `prove_ci.sh`
without removing it from those expected-lists would have broken those
gates in turn.

---

## Verification

### Directly-affected CI-guardrail gates — all pass individually

- `gate_ci_guardrails_surface_freeze_v1.sh` (after fingerprint regen)
- `gate_ci_guardrails_execution_order_lock_v1.sh`
- `gate_ci_guardrails_ops_cluster_canonical_v1.sh`
- `gate_ci_guardrails_ops_entrypoint_order_lock_v1.sh`
- `gate_ci_guardrails_ops_entrypoint_registry_completeness_v1.sh`
- `gate_ci_guardrails_ops_entrypoint_parity_v1.sh`
- `gate_ci_guardrails_registry_authority_v1.sh`
- `gate_ci_guardrails_registry_completeness_v1.sh`
- `gate_ci_guardrails_ops_label_registry_parity_v1.sh`
- `gate_ci_guardrails_ops_label_source_exactness_v1.sh`
- `gate_ci_guardrails_ops_topology_uniqueness_v1.sh`
- `gate_ci_guardrails_ops_entrypoint_exactness_v1.sh`
- `gate_ci_guardrails_ops_renderer_shape_v1.sh`

### prove_ci.sh differential check

`prove_ci.sh` output was captured at pristine `038e51a` (pre-retire)
and at the retire-applied state, both under a 90-second timeout. The
retire introduced **zero new ERROR lines**. Every ERROR observed
post-retire is present in the pre-retire baseline (shim violations in
`scripts/process_full_season.sh`, filesystem-ordering determinism risks,
proof-surface registry sync, allowlist-wrapper absence).

These are pre-existing latent silent-red failures separate from Finding
2. They are covered by Finding B (below) and are not addressed here.

### Baselines

- Ruff (`ruff check src/`): unchanged (no src/ touched).
- Mypy (`mypy src/squadvault/core/`): unchanged (no src/ touched).
- Pytest: unchanged (no Tests/ touched).
- Pre-commit hook: all three gates fire (banner paste, no-xtrace,
  repo-root allowlist).

---

## Secondary effects

### Finding C resolved by retirement

The `extract_bounded` function in the retired gate swallowed its own
ERROR diagnostic via command-substitution capture. That function is
local to the retired gate file; nothing else references it. Finding C
goes away with the gate and needs no separate action.

### Finding B still deferred

`scripts/prove_ci.sh` still lacks `set -e` and still silently absorbs
per-gate failures. The differential check above incidentally confirmed
~10 pre-existing latent silent-red ERRORs in prove_ci.sh output at
pristine `038e51a` — all unrelated to Finding 2, all previously invisible
in CI for the same reason Finding 2 was invisible: prove_ci.sh's final
rc is its last command's rc, not an aggregate of its gate invocations'
rcs.

Finding B therefore has a visible surface of pre-existing failures
waiting for it (shim violations, ordering risks, registry sync,
allowlist wrapper absence). Its next session should start with a
similar differential check to distinguish "pre-existing latent" from
"new failures caused by whatever we change about prove_ci.sh".

---

## What this session did not do

- Did not address Finding B (prove_ci.sh errexit posture).
- Did not address the pre-existing latent ERRORs in prove_ci.sh output.
- Did not touch src/, Tests/, the Creative Layer, or anything outside
  the CI Guardrails lock-down infrastructure.
- Did not remove the archived gate's v1 predecessor (unchanged in
  `scripts/_archive/unreferenced/gate_ci_guardrails_ops_entrypoints_section_v1.sh`).

---

## Carry-forward

- **Finding 2:** CLOSED.
- **Finding C:** CLOSED (absorbed by retirement).
- **Finding B:** still deferred; visible failure surface now documented.
- **Standing backlog:** untouched. Q1/Q2/Q3, B2/C/D/E, latent callers,
  Phase 2 behavioral validation, `d['raw_mfl']` write, Item 4b re-scope,
  Thread-1 `Tests/` ruff cleanup (238 errors).
