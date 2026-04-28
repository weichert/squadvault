# Observation: Findings C + E retirement (Phase 7.8 prose-deletion residue)

**Session date:** 2026-04-27
**Origin:** Finding C from F3 memo + Finding E surfaced during Finding D
validation. Discovery during this session: a third related gate
(`gate_docs_integrity_v2.sh`) and a fourth requiring surgery
(`gate_docs_mutation_guardrail_v2.sh`) belong to the same cluster.
**HEAD before:** `70e4003` (Finding D)
**Decision:** Path A (wholesale retirement of dormant gates) per
commissioner authorization.

---

## Summary

This commit retires the post-Phase-7.8 dormancy cluster. Commit `0faf0c0`
(Phase 7.8 — CI Guardrail Registry Completeness Lock, 2026-03-10) deleted
270 lines of prose from `CI_Guardrails_Index_v1.0.md`, removing 43 SV
markers in the process. Five gates were left silently failing — checking
for markers and bullets that no longer existed.

Three gates retired wholesale. Two gates surgically edited (real
non-marker logic preserved).

## Retirements (3 files via git mv to `_archive/unreferenced/`)

  - `gate_ci_proof_surface_registry_index_discoverability_v1.sh`
    (Finding C — pure marker+bullet check, no other logic)
  - `gate_creative_surface_registry_discoverability_v1.sh`
    (Finding E — pure marker+bullet check, no other logic)
  - `gate_docs_integrity_v2.sh`
    (Finding F — discovered this session; pure marker check only)

## Surgical edits (2 files — real logic preserved)

### `gate_creative_surface_registry_usage_v1.sh`
Removed the line-43 invocation of the now-archived discoverability gate.
The gate's CREATIVE_SURFACE_* token validation logic (lines 50+) is
real, valuable, and survives. Without the dependency call, the gate
runs to completion and validates the canonical Creative Surface tokens.

### `gate_docs_mutation_guardrail_v2.sh`
Stripped two dormant checks:
1. The Index marker + bullet check (target: marker deleted in Phase 7.8)
2. The `scripts/_patch_example_noop_v1.{py,sh}` existence check (both
   files archived in `2dfb96e`)

Surviving real-work portion: enforces that
`docs/process/rules_of_engagement.md` exists and contains the
"## Docs + CI Mutation Policy (Enforced)" anchor + `scripts/_patch_` /
`scripts/patch_` references. This is the only active gate enforcing
rules-of-engagement.md content; preserved.

## prove_ci.sh edits

- Removed invocations of all 3 retired gates.
- Removed `SV_GATE: proof_registry_exactness (v1) begin/end` markers
  that wrapped the creative-surface discoverability invocation.
- Removed `SV_GATE: ci_registry_execution_alignment (v1) begin/end`
  markers that wrapped the docs_integrity_v2 invocation (drift —
  marker name didn't match wrapped content).

## Doc edits

- `CI_Guardrails_Index_v1.0.md`: removed 3 entries.
- `CI_Guardrail_Entrypoint_Labels_v1.tsv`: removed 3 rows.
- `CI_Guardrails_Surface_Fingerprint_v1.txt`: regenerated (post-D was
  `?` → post-C+E `0a605e3bb1fd22b4e27aad07bbadafc9977cf33022fcf42a23cadbe72904237f`).

## Validation

- ruff src/: clean.
- mypy src/squadvault/core/: clean.
- 9 affected gates pass standalone under `LC_ALL=C` (the 9 inherit
  Finding D's portability fix).
- `gate_creative_surface_registry_usage_v1.sh` now passes standalone
  for the first time (was rc=1 due to discoverability dependency).
- `gate_docs_mutation_guardrail_v2.sh` now passes standalone for the
  first time (was rc=1 due to deleted markers + archived example
  patcher files).

## prove_ci.sh ERROR-line delta (clean tree, projected)

Pre (commit `70e4003`, post-Finding-D): 1 ERROR + 2 No-such-file lines.

Three retired gates emitted "FAIL:" lines (not "ERROR:") in prove_ci.sh
output. Steve's `grep -c ERROR` didn't catch them. They were:
- `gate_docs_integrity_v2.sh`: 2 FAIL: lines (one per missing marker)
- (Other discoverability gates exited silently rc=1 with no output;
   set -e + pipefail aborted before their echo lines executed.)

Post-this-commit:
- Same ERROR count (1, the env export-assemblies error)
- Same No-such-file count (2, both pre-existing pre-thread)
- **−2 FAIL: lines** in `grep -c FAIL:`

The silent-rc=1 failures are also gone (3 retired gates removed
entirely from prove_ci.sh; 2 surgically-edited gates now pass).

## Key intent notes

`0faf0c0` carried the explicit name "CI Guardrail Registry Completeness
Lock" — the commit added a Registry Completeness gate to TSV/index
plumbing while wholesale removing the prose-rich Index. The commissioner
confirmed Path A (retirement) on the basis that the prose deletion was
deliberate and the deferred cleanup never followed.

Genuinely valuable enforcement (rules-of-engagement.md anchors, Creative
Surface token validation) is preserved by the surgical edits. The
retired gates were pure meta-documentation enforcement whose
documentation target was deliberately removed.

## Findings still open (carried forward)

- **Finding B** (sed `\b` portability + worktree_cleanliness intentional
  pattern in `gate_prove_ci_structure_canonical_v1.sh`) — open.
- **F7 §finding memo amendment** — pending bullets accumulated.
- **export-assemblies env ERROR** — environmental, separate scope.
- **`_status.sh` and `gate_contract_linkage_v1.sh` No-such-file lines**
  — pre-existing, second resolves with unpushed `9404659`.
- **Hygiene bundle `9404659`** — still unpushed; item 4 subsumed by
  Finding D.
- **Path to Finding B mechanism closure**: after Finding B is addressed,
  silent-red gate count goes to zero (the visible-FAIL gates are now
  retired or fixed). `set -euo pipefail` addition to `prove_ci.sh`
  becomes the natural cap.

---

## Cross-references

- F3 memo: `_observations/OBSERVATIONS_2026_04_27_F3_RETIREMENT_AND_AUTOSYNC_RESIDUE.md`
- F6 memo: `_observations/OBSERVATIONS_2026_04_27_F6_RETIREMENT.md`
- Finding D memo: `_observations/OBSERVATIONS_2026_04_27_FINDING_D_LC_ALL_PORTABILITY.md`
- Original triage memo: `_observations/OBSERVATIONS_2026_04_20_FINDING_B_PROVE_CI_TRIAGE.md`
- `0faf0c0`: Phase 7.8 — CI Guardrail Registry Completeness Lock (root cause)
- `2dfb96e`: 1,427-file root cause sweep (archived example patcher files)
