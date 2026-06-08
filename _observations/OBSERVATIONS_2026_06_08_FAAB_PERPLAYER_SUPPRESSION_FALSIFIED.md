# OBSERVATIONS 2026-06-08 -- FAAB Per-Player Suppression A/B: Falsified (net-harmful)

**Session type:** Controlled regen experiment (pre-registered), diagnostic-first.
Engine HEAD at session start: 946b87f. The experiment used an uncommitted,
env-gated renderer patch (default = production behavior); the patch was REVERTED
after the run, so production is unchanged. This memo is the only committed artifact.
Doc-only; SKIPS prove_ci.

**DB:** ./.local_squadvault.sqlite (live ingest; league 70985; seasons 2022/2024/2025).
API used for regen (recap_artifact_regenerate.py forces SQUADVAULT_PROMPT_AUDIT=1).

---

## TL;DR

The hypothesis -- that removing the per-player FAAB acquisition + ROI lines (keeping
franchise totals) would eliminate FAAB_CLAIM fabrication "quieter and true" -- is
FALSIFIED. Both pre-registered falsifiers fired. Suppression was net-harmful: it made
recaps noisier AND falser across the board, not quieter and true.

The experiment did, however, cleanly decompose the FAAB failure into two mechanisms,
and that decomposition is the durable finding:
- **Mis-pairing** (model swaps amounts among real listed players): rare (1 of 18 runs).
  Caused by the list; removing the list eliminated it.
- **Phantom** (model invents a FAAB pickup for a non-acquired, salient player): dominant
  (9 occurrences). NOT caused by the list; removing the list made it WORSE (ON 3 -> OFF 6).

Phantom outweighs mis-pairing roughly 9:1. List-removal fixes the rare mode while
aggravating the dominant one. Bad trade.

**Strategic inference (now backed by two pre-registered controlled falsifications):**
manipulating the FAAB context block -- ADDING one (matchup anchors, 2026-06-07) or
REMOVING one (this experiment) -- both INCREASE fabrication. The model treats FAAB as a
"color slot" it will confabulate to fill regardless of what the context contains.
Context-block manipulation is the wrong lever for FAAB.

---

## Pre-registration (verbatim, written before the run)

Hypothesis: the per-player FAAB acquisition + ROI lines are the fabrication surface.
Both proven failure modes -- mis-pairing (W1 Johnston/Boutte amount swap) and phantom
(W8 Kraft/Hurts, players not in the canonical 50) -- occur WITH the list present.
Removing it (keeping franchise totals) should eliminate FAAB_CLAIM HARD failures
without inducing new HARD categories.

Arms (voice held ON for all; only the FAAB list varies): on = production; off =
SV_FAAB_PERPLAYER=off (per-player + ROI suppressed; totals kept). Weeks 1/8/16 (2025),
same instrument as the 2026-06-06 calibration grid. RUNS=3 per cell.

Pre-registered WIN ("quieter and true"): off => ZERO FAAB_CLAIM HARD failures and no
new HARD categories vs on.

Falsifiers: (a) off still shows FAAB_CLAIM fails -> suppression insufficient; (b) off
shows new HARD categories absent in on -> side effects; (c) off clean but below
useful-narrative floor -> escalate to week-scoped list.

---

## Prior diagnostic grounding (same investigation)

1. The data is fully wired: render_writer_room_context_for_prompt emits per-player
   FAAB acquisitions with resolved names under "Individual FAAB acquisitions this
   season (ONLY these amounts may be cited...)". Not a missing-data problem.
2. Rounding is a red herring: the renderer prints whole dollars (.0f) but the FAAB
   verifier (verify_faab_claims) carries a deliberate +/-1.0 tolerance that absorbs it
   (max rounding error 0.50). Do not re-chase rounding.
3. Canonical universe confirmed (diag_faab_mechanism.py, read-only): season 2025 has
   exactly 50 WAIVER_BID_AWARDED acquisitions. The Johnston/Boutte mis-pair is proven
   from the ledger -- Quentin Johnston canonical $8.77 (fid 0006), Kayshon Boutte
   canonical $15.02 (fid 0010), both bid 2025-09-11; the recap's "$15 to Johnston"
   is Boutte's amount on Johnston. Kraft/Hurts/Josh Allen/Jefferson appear nowhere in
   the 50 (genuine phantoms).
   - CAVEAT on that probe: its reverse name->id lookup mis-flagged "Tampa Bay
     Buccaneers" as phantom; TB DST is a REAL acquisition (fid 0004, $0.51, 2025-10-23).
     Trust the forward 50-row list, not that one cross-check line.

## Manipulation check (verified before interpreting results)

prompt_audit confirmed the off arm genuinely stripped the block. Newest W8 rows:
- off run: perplayer=0, totals=1 (per-player block gone, totals kept) -- yet vpass=0,
  draft still framed Hurts as a $1 FAAB pickup.
- on run: perplayer=1, totals=1 (production).
So the phantom in the off arm is a real list-independent result, not a patch-not-applied
confound.

## Results (RUNS=3, 9 runs per arm)

| metric | on (production) | off (list suppressed) |
|---|---|---|
| clean passes | 4/9 | 3/9 |
| FAAB_CLAIM fail runs | 3/9 | 6/9 |
| STREAK | 1 | 5 |
| SERIES | 0 | 2 |
| CHAMPIONSHIP_CLAIM | 0 | 1 |
| SEASON_RECORD_CLAIM | 0 | 1 |
| SUPERLATIVE | 1 | 0 |

off lost on every axis. Both falsifiers (a) and (b) fired.

## FAAB failure decomposition (by verifier evidence string)

- Mis-pairing ("Canonical FAAB bids for X: $Y"): 1 occurrence in 18 runs
  (on W16: Alec Pierce $1 vs real $14.78). off had ZERO -- list-removal eliminated it.
- Phantom ("No WAIVER_BID_AWARDED record found"): 9 occurrences; on=3 (Hurts x1,
  Hurts+Josh Allen in one run), off=6 (Hurts x2, Kraft x1, Justin Jefferson x3).
  Every phantom is a salient star not acquired via FAAB.

Tell of a learned trope, not data: both ON and OFF phantoms defaulted to "$1" cheap-flier
framing. And off W16's phantom was "$60 FAAB for Justin Jefferson" -- $60 is the rounded
franchise TOTAL the model saw (fid 0009 = $60.02 spent). Strip the per-player list and
the model grabs the big round total and pins it on a star. The per-player list at least
kept individual claims near small real-ish amounts.

## Findings

1. Suppression is net-harmful and is contraindicated. Do not ship list-removal.
2. Phantom invention is list-INDEPENDENT. It is fed by PLAYER HIGHLIGHTS salience +
   franchise totals + a learned cheap-pickup trope, not by the per-player list. This is
   the dominant FAAB failure mode (~9:1 over mis-pairing) and it is robust to FAAB-block
   manipulation.
3. Context-block manipulation is the wrong lever for FAAB. Adding a "cite these" block
   (matchup anchors, OBSERVATIONS_2026_06_07_MATCHUP_ANCHORS_PHASE1_FRESH_GEN_VALIDATION,
   disposition 2026-06-08) increased fabrication; removing a block (this experiment) also
   increased fabrication. Two pre-registered controlled falsifications now agree.

## Constitutional note

Nothing here is broken. The verifier caught 100% of these as HARD and the lifecycle fell
back to facts-only every time. Silence-over-speculation is operating exactly as designed;
no fabricated FAAB has ever shipped. The open issue is narrative DENSITY on FAAB-dense
weeks (facts, not story), not member-facing safety -- and that density gap has now been
shown to be unfixable by FAAB-block tweaks.

## Disposition

- Env-gate patch (writer_room_context_v1.py SV_FAAB_PERPLAYER) REVERTED; production
  unchanged. The toggle is not committed.
- FAAB phase-2 context-block tweaking declared contraindicated, alongside the
  matchup-anchors disposition. No third FAAB context experiment should be reflexively built.
- Accepting the facts-only floor on FAAB-dense weeks is the current principled stance.
  Any future attempt at FAAB narrative must work UPSTREAM of prompt-block content
  (a different lever entirely) and is a strategic decision for the founder, not a patch.
  A defensible reading is that FAAB is simply not a model-narratable signal for this
  league.

## Artifacts / state

- This memo (committed).
- ~/sv-apply/diag_faab_mechanism.py (read-only canonical-FAAB probe) and
  ~/sv-apply/run_faab_ab.py (A/B runner with pre-registration in its header). Kept
  outside the repo per convention.
- Engine HEAD after this commit advances by one doc-only commit on top of 946b87f.
  Worktree clean after revert.
