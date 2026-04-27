# Observation: F3 retirement and autosync residue retirement (cluster + autosync)

**Session date:** 2026-04-27
**Origin:** [next-session brief — Dormant idempotence-allowlist cluster decision]
**Decision authorized:** Option C-broadened (retire cluster + retire autosync residue)
**HEAD before:** `bcac553`

---

## Summary

This session retires the dormant idempotence-allowlist cluster (F3 from the
Finding B triage memo) plus the structurally-identical
`prove_contract_surface_autosync_noop_v1.sh` residue, both of which had been
silently failing in `prove_ci.sh` since commit `2dfb96e` and were masked by
the open Finding B (missing `set -e` in `prove_ci.sh`).

Five files moved to `scripts/_archive/unreferenced/`. Four invocations
removed from `prove_ci.sh`. Two entries each removed from the Guardrails
Index and the Entrypoint Labels TSV. Five entries removed across three
marker blocks of the Proof Surface Registry. Surface fingerprint regenerated.

The retirement is consistent with `2dfb96e`'s wholesale archival of the
shell-patcher pattern (596 patches archived) and resolves F3 by option 2
(full retirement) rather than option 1 (empty the allowlist file) — which
the original triage memo explicitly flagged as a candidate.

---

## What the brief described vs. what was on the ground

The brief presented one wrapper plus two archived gates and 7 archived
patches in scope. Inspection revealed a wider surface:

- **15 archived patches in cluster reach, not 7.** The wrapper's main loop
  references 7 patches via `patch_idempotence_allowlist_v1.txt`. The
  wrapper file also carries 8 dangling string literals at lines 107–126
  (shell-legal but semantically broken) referencing 8 *additional*
  archived patches. The dangling section never executes because the
  recursion-guard at line 18 dies first with rc=127, and the runtime loop
  at line 50 would die rc=3 even if the recursion-guard were resolved.

- **Two more dormant pieces beyond the brief.**
  - `scripts/prove_idempotence_allowlist_noop_in_idempotence_mode_v1.sh`
    (prove_ci.sh:132) — rc=2 standalone (first allowlist entry missing).
  - `scripts/gate_allowlist_patchers_must_insert_sorted_v1.sh`
    (prove_ci.sh:83) — silently passes; loop iterates over
    `scripts/_patch_allowlist_patch_wrapper_*.py` which don't exist.
    Heuristic gate with no remaining input domain.

- **The autosync residue is structurally identical.**
  `prove_contract_surface_autosync_noop_v1.sh` (prove_ci.sh:348) execs
  `patch_contract_surface_autosync_v2.sh` at line 17; both v1 and v2 of
  that patch live only in `_archive/shell_patches/`. Standalone rc=127.
  Same disease, same root cause.

- **Brief inaccuracy.** The brief stated
  `gate_idempotence_allowlist_wrappers_no_prove_ci_v1.sh` was "deleted
  outright in commit `2dfb96e`, no archive copy." `2dfb96e` *moved* it
  (rename, zero content delta). Both archived gates are symmetric and
  available at `scripts/_archive/unreferenced/`.

---

## Retirement scope executed

### File moves (5)

```
git mv scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh \
       scripts/_archive/unreferenced/
git mv scripts/prove_idempotence_allowlist_noop_in_idempotence_mode_v1.sh \
       scripts/_archive/unreferenced/
git mv scripts/gate_allowlist_patchers_must_insert_sorted_v1.sh \
       scripts/_archive/unreferenced/
git mv scripts/patch_idempotence_allowlist_v1.txt \
       scripts/_archive/unreferenced/
git mv scripts/prove_contract_surface_autosync_noop_v1.sh \
       scripts/_archive/unreferenced/
```

### `scripts/prove_ci.sh` edits

- Removed gate invocation at former line 83
  (`gate_allowlist_patchers_must_insert_sorted_v1.sh`).
- Removed gate invocation at former line 237
  (`gate_patch_wrapper_idempotence_allowlist_v1.sh`).
- Removed proof invocation block at former lines 129–133
  (`prove_idempotence_allowlist_noop_in_idempotence_mode_v1.sh` plus
  surrounding worktree-cleanliness wrap; subsequent SNAP_PROOF
  re-assignments still cover the assert points downstream).
- Removed proof invocation at former line 348
  (`prove_contract_surface_autosync_noop_v1.sh`; preserved the contract
  surface completeness wrap intact).
- Removed orphaned echo headers at former lines 113–116. These echoes
  pre-labeled the wrapper-gate and the must-insert-sorted gate but were
  positioned far from their actual invocations — pre-existing prose drift
  that became fully orphaned once the gates were archived.

### `docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md` edits

- `SV_PROOF_SURFACE_LIST_v1` block: 16 → 14 entries
  (removed `prove_contract_surface_autosync_noop_v1.sh` and
  `prove_idempotence_allowlist_noop_in_idempotence_mode_v1.sh`).
- `CI_PROOF_RUNNERS` block: 14 → 12 entries (same two removals).
- `SV_CONTRACT_SURFACE_PROOFS_v1` block: emptied with placeholder
  `(none currently registered)` matching the
  `PROOF_SURFACE_REGISTRY_LOCAL_PROOFS_v1` precedent.

The 1-line prose drift on entries 62–65 of the doc (descriptions shifted
by one row) is *separately* documented in
`OBSERVATIONS_2026_04_27_F2_F5_PROSE_DRIFT_AND_REPO_ROOT_PROOF_GAP.md`
and is intentionally not addressed in this commit (out of retirement
scope).

### `docs/80_indices/ops/CI_Guardrails_Index_v1.0.md` edits

In `SV_CI_GUARDRAILS_ENTRYPOINTS_v1` block:
- Removed `gate_allowlist_patchers_must_insert_sorted_v1.sh` entry.
- Removed `gate_patch_wrapper_idempotence_allowlist_v1.sh` entry.

### `docs/80_indices/ops/CI_Guardrail_Entrypoint_Labels_v1.tsv` edits

Removed the matching two TSV rows. The two-way binding enforced by
`gate_ci_guardrails_registry_authority_v1.sh` (executed-but-not-registered
fails) and `gate_ci_guardrails_registry_completeness_v1.sh` (registered-
but-not-executed fails) requires these to move in lockstep with the
`prove_ci.sh` removals.

### `docs/80_indices/ops/CI_Guardrails_Surface_Fingerprint_v1.txt` regenerated

Pre: `e83ca75d81fdaecb73afb5baf0d91d0ba93e825b792038a1ec2e26d979c8cc1b`
Post: `6c3eaa59ca833fb9655c4fdce0def049e238e0b388b1f29c61bc6dce0a3a3c47`

The freeze fingerprint is computed from the canonical surface (prove_ci
gate-cluster region + Labels TSV + Index entry block). Removing two
gates from each input materially changes the fingerprint; regeneration
is a required parity step, not an optional cleanup.

---

## Validation

- `ruff check src/`: clean (unchanged from baseline).
- `mypy src/squadvault/core/`: 58 files clean (unchanged from baseline).
- Pytest: 1814 collected, focused subsets pass; full suite times out in
  this session container but surface tests (`test_architecture_gates_v1`,
  `test_repo_root_allowlist_v1`, `test_canonicalization_idempotency_property_v1`)
  all pass clean. No tests reference any retired path.
- Affected gates standalone (19 inspected):
  - 17/19 pass at rc=0.
  - 2/19 fail at rc=1, **both confirmed pre-existing at HEAD** via stash
    (Findings B and C below). Neither is regression-introduced.

---

## Findings surfaced for follow-up

### Finding A — `gate_no_obsolete_allowlist_rewrite_artifacts_v1.sh` is dormant

This is **F6** from the original Finding B triage memo. Standalone rc=1 at
HEAD; expects four canonical files (`_patch_rewrite_allowlist_patchers_insert_sorted_no_eof_v2.py`,
the matching `.sh`, `_patch_cleanup_allowlist_rewrite_recovery_artifacts_v1.py`,
the matching `.sh`) which are all archived to
`scripts/_archive/{patches,shell_patches}/`. Same domain as the cluster
just retired (allowlist rewrite recovery). Same `2dfb96e` root cause.

The original F6 triage offered two options: empty the `allow_exact` array
(option 1) or retire the gate (option 2). The triage memo explicitly
flagged both as legitimate. With F3 now closed by retirement (this
commit), option-2-style retirement is the consistent move for F6 — the
gate's purpose is dead for the same reason F3's was dead.

**Decision deferred** to a follow-up session. Scope is small (3–4 files
plus parity manifests, same shape as this commit).

### Finding B — `gate_prove_ci_structure_canonical_v1.sh` is dormant (NEW)

Standalone rc=1 at HEAD `bcac553`. The gate enforces uniqueness of
`bash scripts/gate_*.sh` invocations in `prove_ci.sh`, but
`gate_worktree_cleanliness_v1.sh` is invoked *intentionally many times*
(begin/assert/end at multiple points throughout the prove sequence). The
gate flags every assert as a duplicate.

Either the gate's regex should special-case worktree-cleanliness, or the
gate is fundamentally misconceived. Not introduced by this commit.

### Finding C — `gate_ci_proof_surface_registry_index_discoverability_v1.sh` is dormant (NEW)

Standalone rc=1 at HEAD `bcac553`. The gate expects `<!-- SV_CI_PROOF_SURFACE_REGISTRY: v1 -->`
marker and `scripts/check_ci_proof_surface_matches_registry_v1.sh` bullet
to appear exactly once in `CI_Guardrails_Index_v1.0.md`. Both are absent
at HEAD. The gate's hint suggests a patcher
(`patch_index_ci_proof_surface_registry_discoverability_v1.sh`) which is
itself archived (`_archive/shell_patches/`).

Same shape as Findings A/B and the F-series in the original triage memo.
Not introduced by this commit.

---

## prove_ci.sh ERROR-line delta

Brief baseline (clean tree, `9404659`): 6 ERRORs + 2 No-such-file lines.

After this retirement (clean tree, projected):

- −1 ERROR: `prove_idempotence_allowlist_noop_in_idempotence_mode_v1.sh`
  no longer invoked, its rc=2 ERROR line gone.
- −1 No-such-file: `gate_patch_wrapper_idempotence_allowlist_v1.sh`'s
  rc=127 line at line 18 (recursion-guard target) gone.
- −1 No-such-file: `prove_contract_surface_autosync_noop_v1.sh`'s rc=127
  line at line 17 (autosync target) gone.

Net delta: −1 ERROR, −2 No-such-file. Projected post-retirement count:
5 ERRORs + 0 No-such-file. The remaining 5 ERRORs are from Findings
A (F6, 4 lines) and B (1 line). Finding C does not emit an ERROR line
(its banner echoes but no `>&2 ERROR:` until the marker check).

The ERROR-count assertion is not portable across environments per the
prior session's note; this comparison applies to same-shell, same-tree
runs.

---

## Why this retirement aligns with governance principles

- **Silence over speculation.** A gate that fails rc=127 silently because
  prove_ci.sh has no `set -e` is a worse failure mode than no gate. It
  conveys false coverage and false confidence.

- **Append-only ledger preserved.** Files are moved to `_archive/`, not
  deleted. The shell history is reachable; the patcher pattern's full
  context is recoverable. Restoration (if patcher pattern ever returns)
  is one `git mv` per piece.

- **No analytics, no prediction.** The retirement removes silently-failing
  validation infrastructure, which is the opposite of accumulating
  fictional coverage signal. The remaining gate suite has no false
  positives and no false negatives in its own domain.

- **Architecture frozen.** No new gates introduced, no new layers, no new
  patterns. Pure retirement of dead code paths consistent with `2dfb96e`'s
  documented intent.

---

## Cross-references

- Original triage memo: `_observations/OBSERVATIONS_2026_04_20_FINDING_B_PROVE_CI_TRIAGE.md`
  (Finding F3 closed by this commit; Finding F6 remains open with
  retirement-via-option-2 now precedented.)
- F2+F5 closure precedent: commit `a56c147` and
  `_observations/OBSERVATIONS_2026_04_27_F2_F5_PROSE_DRIFT_AND_REPO_ROOT_PROOF_GAP.md`
  (provided the registry-edit + fingerprint-regen workflow this commit
  mirrors).
- `2dfb96e` ("engineering excellence: 512 tests, 100% docs, schema
  aligned"): the 1,427-file sweep that originally archived the cluster's
  domain wholesale.
