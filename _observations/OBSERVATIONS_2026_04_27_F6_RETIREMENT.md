# Observation: F6 retirement (gate_no_obsolete_allowlist_rewrite_artifacts_v1)

**Session date:** 2026-04-27
**Origin:** Carried forward from `OBSERVATIONS_2026_04_20_FINDING_B_PROVE_CI_TRIAGE.md`
§Finding F6, with retirement-via-option-2 precedent established by F3
closure in commit `e358886`.
**Decision:** Option 2 (full retirement) over option 1 (empty `allow_exact`).
**HEAD before:** `e358886` (F3 retirement + autosync residue)

---

## Summary

This session retires `gate_no_obsolete_allowlist_rewrite_artifacts_v1.sh`,
the last live remnant of the dormant allowlist-rewrite-recovery
infrastructure that was archived wholesale in `2dfb96e`. The gate has
been silently failing rc=1 in `prove_ci.sh` since the F3 cluster's
domain was retired alongside the same `2dfb96e` sweep — visible only
as four "expected canonical file missing" ERROR lines, masked by the
open Finding B (missing `set -e` in `prove_ci.sh`).

One file moved to `scripts/_archive/unreferenced/`. One invocation
removed from `prove_ci.sh`. One entry each removed from the Guardrails
Index and Entrypoint Labels TSV. Two orphaned `SV_GATE` markers in
`prove_ci.sh` removed (they explicitly named the retired gate, leaving
prose drift if preserved). Surface fingerprint regenerated.

---

## Why option 2 (retirement) over option 1 (empty `allow_exact`)

The original triage memo offered both options. Option 1 (empty the
`allow_exact` array) would preserve the `deny_globs` half as a
forward-looking denylist, in case the broken-iteration patterns
attempted to re-enter the codebase.

Inspection of both halves confirms neither has live purpose:

- **`allow_exact` half:** Four canonical files
  (`_patch_rewrite_allowlist_patchers_insert_sorted_no_eof_v2.{py,sh}`
  and `_patch_cleanup_allowlist_rewrite_recovery_artifacts_v1.{py,sh}`)
  all archived in `_archive/{patches,shell_patches}/`. These were the
  canonical patcher tools for the allowlist file
  `patch_idempotence_allowlist_v1.txt` — itself retired by commit
  `e358886` (F3).

- **`deny_globs` half:** Ten patterns, all allowlist-domain-specific:
  - `patch_rewrite_allowlist_patchers_insert_sorted_no_eof_v1.{py,sh}`
  - `patch_repair_broken_allowlist_patchers_newline_in_quote_v*.{py,sh}`
  - `patch_fix_rewrite_allowlist_no_eof_*.{py,sh}`
  - `patch_fix_no_eof_rewrite_template_literal_newlines_v*.{py,sh}`
  - `patch_cleanup_*shell_artifacts*.{py,sh}`

  Every pattern names a broken-iteration patcher that was attempting to
  fix issues with `patch_idempotence_allowlist_v1.txt`. With the
  allowlist file retired, the deny patterns guard against fixes for an
  artifact that no longer exists. Any future attempt to re-create one
  of these patchers wouldn't have anything to fix.

Option 1 leaves a guard whose denied patterns are forward-impossible
(no allowlist artifact remains to be patched). Option 2 is the honest
move: silence over speculation, removal over hollow forward-looking
infrastructure.

---

## Retirement scope executed

### File move (1)

```
git mv scripts/gate_no_obsolete_allowlist_rewrite_artifacts_v1.sh \
       scripts/_archive/unreferenced/
```

### `scripts/prove_ci.sh` edits

- Removed gate invocation at line 222
  (`bash scripts/gate_no_obsolete_allowlist_rewrite_artifacts_v1.sh`).
- Removed orphan `SV_GATE` markers at lines 117 and 120
  (`# SV_GATE: no_obsolete_allowlist_rewrite_artifacts (v1) begin/end`).
  These markers wrapped a non-related gate
  (`gate_ci_prove_ci_relative_script_invocations_v1.sh`) — same prose
  drift pattern as F3's lines 113-116 cleanup.

### `docs/80_indices/ops/CI_Guardrails_Index_v1.0.md`

Removed entry from `SV_CI_GUARDRAILS_ENTRYPOINTS_v1` block.

### `docs/80_indices/ops/CI_Guardrail_Entrypoint_Labels_v1.tsv`

Removed entry. The two-way binding enforced by
`gate_ci_guardrails_registry_authority_v1.sh` and
`gate_ci_guardrails_registry_completeness_v1.sh` requires this in
lockstep with the `prove_ci.sh` removal.

### `docs/80_indices/ops/CI_Guardrails_Surface_Fingerprint_v1.txt`

Pre: `6c3eaa59ca833fb9655c4fdce0def049e238e0b388b1f29c61bc6dce0a3a3c47`
Post: `20899905c055e03f5c6c45c5e384fc929bc64245b9171ba243c343f699039443`

---

## Validation

- `ruff check src/`: clean (unchanged from baseline).
- `mypy src/squadvault/core/`: 58 files clean (unchanged from baseline).
- 11 affected parity gates all pass under `LC_ALL=C` envelope (Finding D
  from F3 commit message — bare `sort` in some gates requires the
  envelope; documented but not yet fixed).
- Architecture and repo-root-allowlist tests pass.
- No tests reference the retired gate.

---

## prove_ci.sh ERROR-line delta (clean tree, projected)

Pre (commit `e358886`, post-F3): 5 ERROR lines + 2 No-such-file lines.

After this retirement:
- −4 ERROR lines (the 4 "expected canonical file missing" lines from
  the gate's `allow_exact` check, which fired because all 4 canonical
  files are archived).
- −1 ERROR line ("FAIL: obsolete allowlist rewrite recovery artifacts
  gate failed.")
- 0 change to No-such-file count (the gate didn't emit those; it was a
  graceful-failure pattern, not a missing-script pattern).

Projected post-F6: **0 ERROR lines + 2 No-such-file lines**.

The 2 remaining No-such-file lines are pre-existing (predate this thread):
- `scripts/_status.sh` sourced by `scripts/recap` (line 5)
- `scripts/gate_contract_linkage_v1.sh` (hygiene bundle item 1 from the
  unpushed `9404659`; restored on commit when that bundle lands)

The remaining 0 ERROR lines means **`prove_ci.sh` would now run
silently green from start to finish under any envelope**, modulo the
pre-existing `set -e`-masked dormant gates documented as Findings B and
C in the F3 memo. Those gates fail rc=1 standalone but their stderr
goes to terminal, not to ERROR-marked output lines.

This brings Finding B's mechanism closure (the `set -euo pipefail`
addition to `prove_ci.sh`) closer to actionable. After Findings B and C
from the F3 memo are addressed (each separate commit), `set -e` can
land safely.

---

## Findings still open (carried forward)

- **F7 §finding memo amendment** (4-bullet pending update from prior
  session, plus one bullet from F3, plus one bullet from F6 — the
  retirement-precedent established here is itself the kind of
  observation worth surfacing for future similar findings).
- **Finding B** (NEW from F3): `gate_prove_ci_structure_canonical_v1.sh`
  flags `gate_worktree_cleanliness_v1.sh` as duplicate (intentional
  pattern). Gate appears misimplemented.
- **Finding C** (NEW from F3): `gate_ci_proof_surface_registry_index_discoverability_v1.sh`
  expects marker + bullet absent from the Index.
- **Finding D** (NEW from F3): multiple parity gates use bare `sort`
  without `LC_ALL=C`, silently relying on `prove_ci.sh`'s envelope.
- **Hygiene bundle `9404659`**: still unpushed; commit-shape decision
  still open.
- **Finding B mechanism closure**: 4 of 7 sub-findings now closed (F1,
  F2+F5, F3, F4, F6, F7). After Findings B/C/D, the `set -e` addition
  becomes the natural cap.

---

## Cross-references

- F3 closure: commit `e358886` and
  `_observations/OBSERVATIONS_2026_04_27_F3_RETIREMENT_AND_AUTOSYNC_RESIDUE.md`
- F2+F5 closure (registry+fingerprint regen precedent): commit `a56c147`
  and `_observations/OBSERVATIONS_2026_04_27_F2_F5_PROSE_DRIFT_AND_REPO_ROOT_PROOF_GAP.md`
- Original triage memo: `_observations/OBSERVATIONS_2026_04_20_FINDING_B_PROVE_CI_TRIAGE.md`
  §Finding F6 (closed by this commit).
- `2dfb96e`: 1,427-file root cause sweep.
