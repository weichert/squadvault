# OBSERVATIONS — Voice variant rendering retired (Resolution: Position B — migrate caller)

**Date:** 2026-05-02
**HEAD at memo-write:** `96ea051` (origin/main).
**Predecessor finding:** `_observations/OBSERVATIONS_2026_05_02_VOICE_VARIANT_RENDERING_RETIRED.md` (`96ea051`) — captured the discovery; deferred the resolution decision.
**Working tree:** `/Users/steve/projects/squadvault-ingest-fresh`
**Phase:** 10 — Operational Observation.
**Status:** **Resolution selected — Position B.** Apply session is the next executable step.

---

## Recap of finding

`prove_ci.sh` post-`4eb2e6a` advanced through every meta/parity/surface/test gate and crashed at Export assemblies with:

```
RuntimeError: neutral recap render failed rc=1. stderr:
Voice variant rendering (--voice) has been retired. Use rendered_text from recap_artifacts instead.
```

The trace pointed to `src/squadvault/consumers/recap_export_narrative_assemblies_approved.py` line 452, function `run_neutral_recap_render`. The error message itself names the migration path: read `rendered_text` from `recap_artifacts`.

## What this session verified (greps run post-finding)

```
git grep -n "run_neutral_recap_render"
git grep -n "Voice variant rendering"
git grep -n "rendered_text" -- src/squadvault/
git log -S "Voice variant rendering (--voice) has been retired" --oneline
```

Findings:

1. **One caller, one definition, both in the same file:**
   - `src/squadvault/consumers/recap_export_narrative_assemblies_approved.py:147` — definition of `run_neutral_recap_render`
   - Same file `:452` — sole invocation, captured into local `neutral`

   No cross-module callers. The `run_neutral_recap_render` function is private to this file.

2. **Stub error message lives at:** `src/squadvault/consumers/recap_week_render.py:140-141`. The retired binary still ships; passing `--voice` triggers the migration guidance message and rc=1.

3. **Retirement commit:** `0638c9e` ("Remove EAL fallback dead code, retire 4 legacy consumers, clean recap_week_render"). Single commit retired voice-variant rendering, retired four legacy consumers, and shipped the stub. The migration to `rendered_text` was applied to the consumers `0638c9e` retired but not to `recap_export_narrative_assemblies_approved.py`'s subprocess invocation.

4. **The migration target is already in-tree, in the same file:**
   - Line 110: `rendered_text: str  # canonical facts block as stored` (dataclass field on the approved-artifact record)
   - Line 143: `rendered_text=str(row["rendered_text"] or "")` (load from `recap_artifacts` row)
   - Lines 381, 407, 448, 449, 476: file already reads `approved.rendered_text` for FACTS-block emission, empty-text guard, and main payload assembly

   The dataclass already carries the canonical text. The line-452 subprocess capture is the last piece of pre-`0638c9e` shape in this file.

## Revision to "3×" reading

The previous finding memo (`96ea051`) inherited an unconfirmed reading of `_observations/PRIORITY_LIST_2026_04_28.md:300` ("From multiple memos: 3× 'Voice variant rendering retired' warnings") as **three callers**. The greps invalidate that reading.

Best current read: **"3×" refers to three prior memos** that mentioned this dormancy in their standing-items lists, not three callers. The earlier `2026-05-02` finding memos (DOCS_INTEGRITY, GATE_CONTRACT_LINKAGE, PFL_REGISTRY) each carried Voice variant in their standing-items copy — that's three memo mentions. The grep for `run_neutral_recap_render` shows exactly one caller. The grep for the stub message shows exactly one source.

**Apply session must verify this read** by viewing `_observations/PRIORITY_LIST_2026_04_28.md` lines 295-305 for context before committing to a single-caller migration shape. If "3×" turns out to mean callers, the migration scope expands.

## Three positions

### Position A — Reconstitute voice-variant rendering

Restore the renderer that `0638c9e` retired, so `run_neutral_recap_render`'s subprocess call succeeds again.

**Argument against:** `0638c9e` was deliberate architectural cleanup. Its commit message names "EAL fallback dead code" and "4 legacy consumers" as removed artifacts. Reconstitution would reintroduce the EAL fallback path the cleanup deliberately eliminated. The architecture is frozen at Phase 10; reverting Phase 10 cleanup is out of scope. Position A is mentioned only for completeness.

### Position B — Migrate the caller

Replace the line-452 subprocess call with direct read from the `approved.rendered_text` dataclass field that's already loaded earlier in the same function. Delete `run_neutral_recap_render` (definition lines ~147+) along with any imports (`subprocess`, etc.) that become unused.

**Argument for:**
- The error message itself names this migration path
- The same file already uses `approved.rendered_text` for every other downstream path (FACTS-block, empty guard, main payload)
- The dataclass field is already populated from `recap_artifacts.rendered_text` at line 143
- Migration is **local** — no contract changes, no schema changes, no callers outside this file affected
- Net behavior preserved (the subprocess was producing what's now in the field)
- Pattern precedent: `0638c9e` already migrated 4 other consumers; this is the same shape

### Position C — Retire the caller

Move `recap_export_narrative_assemblies_approved.py` to `_archive/` along with the stale function.

**Argument against:** The export consumer is **not orphaned**. It's invoked by `prove_ci.sh`'s "Export assemblies" stage and is presumed to be invoked by operational export scripts. Only the `run_neutral_recap_render` path within it is stale. Retiring the whole file would lose functional behavior. Position C is the wrong instrument — too coarse for the actual problem.

## Position selected: **B — migrate the caller**

The decision reasoning, distilled:

1. **The error message names the migration target.** The retirement commit author signaled the path forward in the stub itself.
2. **The migration target is already in-tree in the same file.** This is not a new dependency; it's plumbing already loaded and used elsewhere in `main()`.
3. **Scope is local.** No contracts, no schemas, no other callers, no tests downstream of `run_neutral_recap_render`'s output (verify in apply session).
4. **Risk is minimal.** Worst case is a behavioral diff in what `neutral` represents downstream — verifiable via test suite and prove_ci.
5. **Pattern precedent.** `0638c9e` already shipped this migration shape for 4 other consumers; we're applying the same shape to the one consumer it missed.

Position B is selected.

## Implementation scope (apply session)

**Single-file diff in `src/squadvault/consumers/recap_export_narrative_assemblies_approved.py`:**

1. **Replace the line-452 invocation** with a direct read. Likely shape:
   ```
   neutral = approved.rendered_text
   ```
   The exact replacement depends on what `neutral` is used for at lines 453+. Apply session must read those lines before drafting the diff.

2. **Delete `run_neutral_recap_render` definition** (lines ~147 through end of function). Likely also deletes the line-161 `RuntimeError(...)` raising path that surfaced the original failure trace.

3. **Drop unused imports** that the deleted function relied on (likely `subprocess` if it's not used elsewhere; verify before removing).

4. **Verify no test references the deleted function** by name. If any do, decide per test whether to delete (if the test was specifically for the subprocess shape) or migrate (if the test was for the export behavior). `git grep -n "run_neutral_recap_render" Tests/` answers this.

Estimated diff size: 30-60 lines net deletion in a single file. Single commit.

**No marker-block handling.** This is a Python file edit, not a shell-gate retirement; the gate_contract_linkage v2 apply-script template doesn't apply directly. The apply script for this session will be smaller and shaped around `view`-then-`str_replace` rather than `git mv` + `sed`.

**No fingerprint regeneration.** The CI guardrails surface fingerprint covers shell gates, not Python consumers; no surface change to declare.

**No docs index updates.** `run_neutral_recap_render` is not registered as a CI guardrail entrypoint.

## Open questions for the apply session

These must be answered by source reads **before** the apply script is drafted:

1. **What is `neutral` used for at lines 453-510 of `recap_export_narrative_assemblies_approved.py`?** The migration shape depends on whether `neutral` is consumed as-is, transformed, or compared against `approved.rendered_text` somewhere. Read lines 440-510.

2. **Does `run_neutral_recap_render` have any callers in `Tests/`?** Run `git grep -n "run_neutral_recap_render" Tests/`. If yes, those tests need triage.

3. **Does the file import `subprocess` for any reason other than `run_neutral_recap_render`?** Run `grep -n "^import\|^from" src/squadvault/consumers/recap_export_narrative_assemblies_approved.py` and check whether `subprocess` is used elsewhere in the file. If not, drop the import in the apply diff.

4. **Does `_observations/PRIORITY_LIST_2026_04_28.md:300` mean callers or memos?** Verify "3×" reading by viewing lines 295-305. If callers, expand scope. (High confidence in "memos" reading per this memo's analysis, but verify.)

5. **Is there a `--voice` invocation anywhere in `scripts/`?** Run `git grep -n "\-\-voice" scripts/`. Operational scripts may pass `--voice` to the export consumer or to a renderer; if so, those need triage too.

## Risks / mitigations

- **Behavioral drift in `neutral` downstream.** Mitigation: pytest suite + prove_ci.sh post-apply. Both ran clean before the line-452 trace, so any new test failures or assembly-content drift will surface.
- **Hidden subprocess dependency.** Mitigation: question 3 above. If `subprocess` is used elsewhere, leave the import; only drop if exclusively used by the deleted function.
- **Test fixtures that mock `run_neutral_recap_render`.** Mitigation: question 2 above. Tests calling it directly are the canary.
- **The 30-60 line estimate is wrong if lines 453-510 do something unexpected with `neutral`.** Mitigation: read first, draft second. Apply script doesn't get written until question 1 is answered concretely.

## Out of scope

- **Retiring the `--voice` stub message in `recap_week_render.py:140`.** The stub is doing its job (signaling the migration path). It can be removed in a future session once all known consumers are migrated and there's confidence no operational script still passes `--voice`. Leaving it for now is conservative.
- **Removing the line `from PRIORITY_LIST_2026_04_28.md` standing-items entry.** That's a documentation update; it can ship in the same commit as the migration if the apply session has bandwidth, or as a follow-up. Preference is to ship in the same commit if scope allows ("the standing-item is closed by this commit" reads well in a commit message).
- **Architecture changes.** Frozen at Phase 10.
- **The other standing item (`_status.sh` missing).** May surface after this resolution ships; will get its own finding/resolution cycle if it does.

## Pre-conditions for the apply session

- HEAD = `96ea051` (or descendant) on origin/main
- Tree clean
- `prove_ci.sh` continues to fail at Export assemblies (i.e., no other intervening change)
- Source reads for questions 1-5 above completed before any code is drafted

If any pre-condition fails, stop and reconcile before drafting.

## For the next session

**Brief shape:** like `session_brief_pfl_registry_surgical_retirement.md`, adapted for a Python single-file edit.

**Steps:**
1. Re-ground (`bash ~/Downloads/sv_reground_v2.sh`)
2. Pre-flight reads — answer questions 1-5 above
3. Draft the migration diff (single-file `str_replace` based on what reads reveal)
4. Apply, run gate sequence (ruff / mypy / pytest)
5. Commit (single topic: migrate `run_neutral_recap_render` caller to read `rendered_text` directly)
6. Post-commit `prove_ci.sh` — expect either rc=0 (chain bottoms out) or another standing-items issue (likely `_status.sh` missing)
7. Push

**Apply script shape:** Probably simpler than the shell-retirement scripts. The pattern is: print pre-edit anchor counts (using the v2 `count_matches` helper), perform the `str_replace`-style edits via Python or `sed -i.bak`, post-edit verification, stage, commit-message preview, stop short of commit.

**One commit, one topic.** The optional standing-items list update (in PRIORITY_LIST_2026_04_28.md) can land in the same commit if the apply session judges it as part of the same retirement; otherwise as a follow-up commit.

## The point

The previous finding memo deferred the decision; this memo locks it in. Position B is well-supported by the in-tree evidence: the migration target is already loaded, already used elsewhere in the same file, and the error message names it explicitly. Apply session is small, scope is local, risk is minimal. The resolution → apply gap from `3d5b006` to `4eb2e6a` was about an hour today; this one should be similar shape if not faster.

This memo does **not** ship the migration. It commits to Position B and hands a well-shaped apply session to the next sitting.
