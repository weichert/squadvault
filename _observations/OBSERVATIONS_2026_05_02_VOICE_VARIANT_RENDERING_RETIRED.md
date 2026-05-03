# OBSERVATIONS — Voice variant rendering retired (recap_export caller stale)

**Date:** 2026-05-02
**HEAD at discovery:** `4eb2e6a` (post-`3d5b006`, pfl.registry surgical retirement)
**Predecessor:** `OBSERVATIONS_2026_05_02_PFL_REGISTRY_RESOLUTION.md` (3d5b006) — Position C retirement that advanced `prove_ci.sh` past the pfl.registry failure point and surfaced this next standing-items issue.
**Working tree:** `/Users/steve/projects/squadvault-ingest-fresh`
**Phase:** 10 — Operational Observation.
**Status:** **Deferred** — finding only, no resolution position selected. Next session opens with classification.

---

## Discovery context

`3d5b006`'s session brief explicitly predicted this. Standing-items list (per `OBSERVATIONS_2026_04_28_TRACK_A_FIRST_DISTRIBUTION.md`) has long carried `3× Voice variant rendering retired` as a known dormancy. The brief stated:

> If `_status.sh` or `3× Voice variant rendering retired` appears, record as a finding and stop — don't roll into a sixth retirement in the same session.

Today's `3d5b006` retirement removed the `pfl.registry` ModuleNotFoundError that was masking everything past prove_ci.sh line 236. The retirement commit `4eb2e6a` advanced the pipeline past that gate, through every meta/parity/surface/test gate, and then surfaced the Voice variant retirement message as the next dormancy.

This is the predicted, well-shaped outcome. It's the fifth time today's chain-of-findings has produced exactly the standing-items issue the prior brief named.

## Exact failure trace

From `bash scripts/prove_ci.sh` post-`4eb2e6a`:

```
== Export assemblies ==
NOTE: set SV_KEEP_EXPORT_TMP=1 to preserve the temp export dir for inspection
Traceback (most recent call last):
  File "/Users/steve/projects/squadvault-ingest-fresh/src/squadvault/consumers/recap_export_narrative_assemblies_approved.py", line 513, in <module>
    raise SystemExit(main(sys.argv[1:]))
  File "/Users/steve/projects/squadvault-ingest-fresh/src/squadvault/consumers/recap_export_narrative_assemblies_approved.py", line 452, in main
    neutral = run_neutral_recap_render(args.db, args.league_id, args.season, args.week_index)
  File "/Users/steve/projects/squadvault-ingest-fresh/src/squadvault/consumers/recap_export_narrative_assemblies_approved.py", line 161, in run_neutral_recap_render
    raise RuntimeError(f"neutral recap render failed rc={proc.returncode}. stderr:\n{proc.stderr}")
RuntimeError: neutral recap render failed rc=1. stderr:
Voice variant rendering (--voice) has been retired. Use rendered_text from recap_artifacts instead.

ERROR: export-assemblies failed (rc=1) and SV_STRICT_EXPORTS=1
prove_ci rc=1
```

## Initial reading

- The implicated consumer is `src/squadvault/consumers/recap_export_narrative_assemblies_approved.py`.
- It defines `run_neutral_recap_render` (line 161) which subprocesses some renderer.
- The renderer subprocess returns rc=1 with stderr `Voice variant rendering (--voice) has been retired. Use rendered_text from recap_artifacts instead.`
- The error message is a **deliberate stub** left by whatever commit retired voice-variant rendering. The retired binary still exists; calling it with the old `--voice` flag deterministically produces this guidance message.
- The migration path is named in the message itself: read `rendered_text` from `recap_artifacts` instead.

This is the same shape as the gate_docs_integrity, gate_contract_linkage, and pfl.registry findings: a downstream caller was not migrated when the upstream retirement shipped, and errexit-on (`bfee780`, 2026-04-29) plus today's earlier retirements made it visible.

## Open questions for the resolution session

1. **How many callers of voice-variant rendering remain?** The standing-items label says "3×". A `git grep` across `src/` and `scripts/` for `--voice` and `voice_variant` and `run_neutral_recap_render` will give the count.
2. **What commit retired voice-variant rendering and shipped the stub error?** Likely surfaces from `git log -S "Voice variant rendering (--voice) has been retired"` or similar. The stub-message commit is the architectural reference point.
3. **Was the migration to `rendered_text` from `recap_artifacts` ever executed for any caller?** If yes, the migration shape is already in-tree and replicable. If no, this is the first migration and shape is open.
4. **Does `recap_artifacts.rendered_text` exist as a column today?** Memory references `recap_artifacts` as a key table; need to confirm `rendered_text` is populated for the league/season/week the export touches.

## Notional positions (not selected — resolution session decides)

- **Position A — Reconstitute voice-variant rendering.** Restore the renderer the stub message points away from. Implies architectural reversal of a deliberate retirement; almost certainly out of scope. Mention only for completeness.
- **Position B — Migrate the caller to read `rendered_text` from `recap_artifacts`.** The error message itself names this as the path. Likely the right answer for any caller whose function is "produce a rendered recap for export". Net behavior preserved.
- **Position C — Retire the caller.** If the export consumer is itself orphaned (no upstream that depends on its output), surgical retirement matches the precedent of today's five retirements. Worth checking before defaulting to B.

The phrase "3× Voice variant rendering retired" in the standing-items list suggests **three callers**, which means resolution may not be uniform — some callers may be migrated (B), some retired (C), depending on whether each has a live upstream.

## Deferred

No resolution position selected here. Next session opens with:
1. The git-grep audit of remaining callers (resolves question 1)
2. The retirement-commit archaeology (resolves question 2)
3. The `recap_artifacts.rendered_text` shape check (resolves question 4)
4. Per-caller classification (B vs C)
5. Resolution memo
6. Surgical retirement / migration session(s) — possibly multiple, one per caller

## Where this sits in the standing-items list

After `4eb2e6a`, the list narrows to:
- `_status.sh` missing — may surface in a future prove_ci run if the Voice variant issue is fixed; not yet observed firsthand
- **`3× Voice variant rendering retired`** ← THIS FINDING

Today's session has shipped five surgical retirements and one finding memo:
1. `bfde774` — gate_docs_integrity
2. `4ceb28b` — gate_rivalry_chronicle_contract_linkage
3. `f40a459` — pfl.registry finding (deferred)
4. `3d5b006` — pfl.registry resolution
5. `4eb2e6a` — pfl.registry retirement applied
6. (this memo) — voice variant finding (deferred)

The chain has not bottomed out at rc=0; one more standing-items issue remains visible.

## For the next session

**Brief shape:** like `session_brief_pfl_registry_surgical_retirement.md` — re-grounding, pre-flight reads, apply script, commit, post-commit prove_ci.

**Pre-flight reads to start with:**

```
git grep -n "run_neutral_recap_render"
git grep -n "Voice variant rendering"
git grep -n "rendered_text" -- src/squadvault/
git log -S "Voice variant rendering (--voice) has been retired" --oneline
```

**Position decision:** likely B (migrate to `rendered_text`) for at least the export consumer, but verify per-caller before committing. The "3×" count may include test fixtures or scripts that should be retired (C) rather than migrated.

**Anti-drift discipline carried forward:** all six norms from `3d5b006`'s brief continue to hold.

## The point

Predicted finding, predicted shape, surfaced exactly where the prior brief said it would. No surprises in this session's output. Push close-out, file the finding, hand the resolution decision to a future session.
