# OBSERVATIONS — Section 10 Q1 Bug 1 Step 0b (generation/eviction classifier results)

**Drafted:** 2026-05-06.
**HEAD at run:** `6329ae9` (classifier commit immediately preceding this memo).
**Phase:** 10 — Operational Observation.
**Position in plan:** Step 0b of the Section 10 Q1 Bug 1 actionable thread per the predecessor session brief. Diagnostic-only; gates the Step 1 production-path decision.

---

## TL;DR

- Classifier ran cleanly across all 13 specimens. **All 13 → NO_AUDIT_DATA.**
- Verified via direct `recap_artifacts` query: zero rows for any of the 6 historical seasons (2011, 2012, 2014, 2016, 2017, 2019) at league_id 70985. The NO_AUDIT_DATA result is the strict form: no recap was ever generated for any of those weeks; not "recap exists but audit was off."
- **GATE: DEFER.** EVICTION_LIKELY count is zero. No direct eviction evidence post-helper for the 13 cross-season specimens; specimen #1 (Brandon W14 2025) remains the sole direct observation, below the 2-and-2 threshold by definition.
- The `af80f12` finding (DIVERSITY TRIGGER SATISFIED, 5 franchises × 13 weeks) is unchanged in its scope: detector-eligibility across the historical corpus is real and cross-franchise. What this Step 0b clarifies is that detector-eligibility cannot be promoted to eviction-evidence in the absence of recap audit data; the 13 specimens were never recapped in this DB instance.
- Step 1 production-path code defers pending live post-helper observation. Tier 5 W14+ cadence is the natural next focus — accumulating post-helper audit data is what the classifier needs to fire EVICTION_LIKELY for any future specimen.
- The classifier itself is durable infrastructure. Re-running against any future audit state is one paste; no re-derivation needed.

---

## 1. Classifier output

Output captured at `/tmp/bug1_step_0a_output.txt`. Bucket counts:

| Bucket | Count | Distinct fids |
|---|---:|---:|
| GENERATED_AND_SURFACED | 0 | 0 |
| GENERATED_AND_BUDGETED_NOT_SURFACED | 0 | 0 |
| EVICTION_LIKELY | 0 | 0 |
| NOT_GENERATED_POST_HELPER | 0 | 0 |
| NOT_GENERATED_PRE_HELPER | 0 | 0 |
| **NO_AUDIT_DATA** | **13** | **4** |

Per-specimen result: every specimen returned the same evidence string (`no prompt_audit row for (league, season, week)`). No partial findings, no per-specimen variation.

The four distinct fids are 0002 (Paradis' Playmakers), 0003 (Purple Haze), 0006 (MGD / Miller's Genuine Draft), 0008 (Ben's Gods) — the cross-franchise spread the `af80f12` scan identified, minus 0010 (Brandon, excluded from the 13 by design).

## 2. Recap-artifact verification

The classifier's NO_AUDIT_DATA bucket conflates two cases at decision time: (a) the recap was generated but `SQUADVAULT_PROMPT_AUDIT=1` was off when it ran, vs (b) no recap was ever generated for that (season, week). Direct query disambiguates:

    SELECT season, COUNT(*) AS n_artifacts, MIN(state) AS any_approved
      FROM recap_artifacts
     WHERE league_id='70985'
       AND season IN (2011, 2012, 2014, 2016, 2017, 2019)
     GROUP BY season ORDER BY season;

Result: zero rows. No `recap_artifacts` exist for any of the 6 historical seasons in this local DB.

The NO_AUDIT_DATA outcome is therefore the strict form (b): no recap was ever generated. PFL Buddies' canonical history through the MFL Platform Adapter has been backfilled to the canonical event corpus, but the recap-generation lifecycle (`weekly_recap_lifecycle.py`) hasn't run against any pre-2025 (season, week) pair in this DB instance. The 13 specimens are detector-eligible against the canonical events, but the lifecycle layer (which produces the prompt_audit rows the classifier needs) has no historical artifacts to inspect.

## 3. Reconciliation with `af80f12`

The cross-season scan memo at `af80f12` reported "DIVERSITY TRIGGER SATISFIED" with 13 specimens across 5 franchises and 6 seasons. That memo carried an explicit caveat:

> Important caveat: these are detector-eligible specimens, not generated-but-evicted specimens. The post-fix memo's specimen #1 proved generation-and-eviction; this scan only proves the first link in that chain (the detector would have fired). Confirming generation-and-eviction for these 13 specimens requires prompt_audit history inspection per (season, week), which is out of scope for the diversity-trigger question.

Step 0b *is* the prompt_audit history inspection. Result: the chain's second link (generation-and-eviction) cannot be confirmed because the chain's first link in the recap lifecycle (recap was generated at all) never happened for any of the 13 (season, week) pairs in this DB.

Both findings stand. They don't conflict; they answer different questions:

- `af80f12`'s question: "Is the detector-eligibility surface single-franchise or systemic?" Answer: **systemic.** 5 franchises across 6 seasons would have qualified.
- Step 0b's question: "Of the systemic detector-eligible cases, how many can we prove were generated-then-evicted?" Answer: **zero of the 13, because none were generated.**

The diversity trigger's purpose was to motivate Bug 1's promotion from "noted, single-specimen" to "actionable thread, multi-specimen, multi-franchise." That motivation holds. The actionable thread's first concrete production step (Step 1) requires direct eviction evidence at the threshold, which we don't have.

## 4. Gate verdict and rationale

**GATE: DEFER.**

Per the predecessor session brief's gate logic:

> EVICTION_LIKELY ≥ 2 across distinct franchises → Bug 1 production-path work justified.
> All NOT_GENERATED... and zero GENERATED_AND_EVICTED post-`0887556` → the systemic concern is hypothetical; defer Step 1 pending live post-`0887556` evidence.

EVICTION_LIKELY count is 0. The DEFER branch fires.

Rationale beyond the mechanical gate:

- **The Step 1 surgical surface is small, but the cost of premature shipping is non-trivial.** Reordering NOTABLE/HEADLINE selection across all weeks via record-claim reservation reshuffles existing approved-recap angle blocks if anyone re-runs against historical data. The cost of getting Step 1 right when evidence accumulates is the same as getting it right now; the cost of getting it wrong is non-zero. Silence over speculation applies to architectural changes too — defer until the surface area justifies the change.

- **Specimen #1 alone is too thin to satisfy the 2-and-2 threshold.** The post-fix memo `a5c5c1b` documented Brandon W14 2025 as the sole specimen with confirmed generation-and-eviction. One specimen = one franchise = one week. The 2-and-2 threshold isn't satisfiable from one observation; live post-helper accumulation is the only path.

- **Tier 5 is the natural mechanism.** The W14+ live observation cadence will produce post-helper prompt_audit rows weekly. As soon as a non-Brandon T9-LOSS angle is generated and evicted, the classifier picks it up on re-run.

## 5. Step 1 design surface (preserved for the next session)

To save the next session from re-deriving the code shape, the design surface is captured here. The grounding step in the predecessor commit `6329ae9` verified:

- `_budget_angles` lives at `src/squadvault/recaps/weekly_recap_lifecycle.py:573-690`. Three phases: HEADLINE (strength 3, alphabetical via precondition sort), NOTABLE (strength 2, rotation-hash via `_notable_key`), MINOR (strength 1, coverage-aware + rotation-hash).
- `format_streak_record` at `src/squadvault/core/recaps/render/streak_strings_v1.py:176-240` returns four canonical (headline, detail) shapes — T8 / T9-WIN / T9-LOSS / T10. The phrasings are deterministic and pattern-matchable from a small set of substrings.
- `_detect_streak_records` at `src/squadvault/core/recaps/context/narrative_angles_v1.py:540-596` confirms strength assignment: T8/T10 at strength=3, T9-WIN/T9-LOSS at strength=2.
- No pre-existing `is_record_claim_angle` helper.

Surgical Step 1 patch when evidence accumulates:

1. New helper `is_record_claim_angle(angle: NarrativeAngle) -> bool`, likely in `streak_strings_v1.py` near `format_streak_record` (helper-bound: pattern-match substrings come from the helper's emit shapes, never hand-written).
2. Modify `_notable_key` at line 631-635 to prepend a 0/1 record-claim flag as the primary tiebreak, with rotation hash falling through as secondary key for non-record-claim angles. Two-line change.
3. Optionally extend the precondition sort at line 880 to include the record-claim flag, so Phase 1 (HEADLINE) also prioritizes T8/T10 over alphabetically-earlier strength=3 categories. Editorial-tier decision per the brief's Q3.
4. Existing test fixture at `Tests/test_budget_angles_rotation_v1.py` — `test_streak_evicted_at_w12_2024` will need to bifurcate into "STREAK record-claim reserved" vs "STREAK non-record-claim still rotates."

The Step 1 patch is small enough to ship as a helper-then-wiring sequence (one commit for helper, one for `_budget_angles` change, one for test sentinel), per one-topic-per-commit discipline.

## 6. Re-activation criterion

DEFER, not CLOSE. The thread re-activates when:

- Tier 5 W14+ live observation produces a post-helper prompt_audit row for a non-Brandon franchise where T9-LOSS was generated AND evicted (the EVICTION_LIKELY signal: no T9-LOSS line in `narrative_angles_text`, but `(+ N minor angles omitted)` tail with N > 0 AND `_T9_LOSS_RECORD_APPROACH` matches in prose attached to the franchise), OR
- Two such specimens accumulate across distinct franchises (the 2-and-2 threshold), at which point the gate fires PROCEED.

Re-running the classifier is one paste:

    PYTHONPATH=src python scripts/step_1_streak_diagnostic_harness.py \
      --db .local_squadvault.sqlite \
      --league-id 70985 \
      --scope classify-bug1-specimens

The 13 cross-season specimens will continue to bucket as NO_AUDIT_DATA until those weeks are recapped (which is unlikely in normal operation; the canonical events are durable but the lifecycle layer typically only runs forward). The signal we care about is whether the bucket distribution shifts on future Tier 5 observations of *current-season* weeks — the harness can be extended to scan Tier 5 weeks alongside the 13 historical specimens, or a new scope variant can be added that operates on (season, week, fid) tuples discovered live.

## 7. Standing-backlog updates

- **Bug 1 (HEADLINE budget eviction):** stays "actionable thread"; Step 1 production-path commit defers pending live post-helper evidence. The Step 0a classifier infrastructure (`6329ae9`) is durable.
- **Tier 5 W14+ live observation cadence:** promotes from named-only to active-next-focus.
- The Step 1 design surface (above, §5) is captured for the next session. No re-derivation needed when evidence arrives.

Other open items unchanged:

- SCORE_VERBATIM 59-row drift (independent thread).
- Cat 3c row-76 attribution (deferred).
- Snap-outcome detection (named-only).
- NOTABLE-pass alphabetical lockout investigation (named-only).
- Tests/ ruff cleanup (deferred).
- `d['raw_mfl']` write at `extract_recap_facts_v1.py:190` (deferred).
- Strength-aware probe (NOTABLE-saturation follow-up, deferred).
- Consolidated paste-fragility hazard catalog memory edit (deferred).

## 8. Files and commits referenced

- `6329ae9` — Step 0a classifier commit (this thread).
- `cdaf1cd` / `af80f12` — cross-season scan and specimen-hunt memo.
- `a5c5c1b` — post-fix memo (specimen #1 framing, eviction-vs-omission distinction).
- `0887556` — Section 10 Q1 Step 1 (T9-LOSS form helper); the helper-shipped boundary.
- `_observations/OBSERVATIONS_2026_05_06_T9_LOSS_BUG_1_SPECIMEN_HUNT.md` — predecessor specimen-hunt memo.
- `_observations/OBSERVATIONS_2026_05_06_T9_LOSS_POST_FIX_REVERIFY.md` — specimen #1 post-fix memo.
- `scripts/step_1_streak_diagnostic_harness.py` — classifier harness (Step 0a).
- `src/squadvault/recaps/weekly_recap_lifecycle.py:573-690` — `_budget_angles` (Step 1 surface).
- `src/squadvault/core/recaps/render/streak_strings_v1.py:176-240` — `format_streak_record` (helper-bound source for Step 1's `is_record_claim_angle`).

---

## 9. Methodology notes

- **Step 0a classifier extension hit zero anchor drift.** Apply script ran clean on first paste; all five anchors uniquely matched. The four-step playbook's anchor-asserting apply pattern continues to be the reliable delivery vehicle for additive scope extensions.
- **The omitted-tail signal didn't fire here, but the schema is sound.** Future post-helper specimens with a real eviction surface will exercise `_extract_omitted_tail_count` and `_T9_LOSS_PROSE_SURFACED_RE`. The empty result is informative: it tells us we have no observations to feed the classifier yet, not that the classifier is broken. Smoke-tested at `6329ae9` apply time against synthetic fixtures (omitted-tail extracts integers correctly; prose regex matches canonical + paraphrase shapes; both reject negatives).
- **DEFER vs CLOSE.** This memo records DEFER (waiting on more evidence), not CLOSE (the question is settled). Bug 1 stays open in the standing backlog with a clear re-activation criterion (§6). The distinction matters for the next session brief: a closure memo would retire the thread; a DEFER memo keeps it on the shelf with infrastructure ready.
- **Sharper-than-the-brief framing held.** The brief's three-bucket schema would have collapsed all 13 specimens into "NOT_GENERATED" without the omitted-tail and pre/post-helper splits. The six-bucket version distinguishes "no recap exists" from "recap exists but couldn't have generated the angle" from "angle was budget-evicted" — even though only the first case fires here, the schema is durable for future specimens. The investment in Step 0a's refinement pays forward.
