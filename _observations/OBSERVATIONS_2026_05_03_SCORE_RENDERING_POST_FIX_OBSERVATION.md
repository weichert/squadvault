# OBSERVATIONS — Score-Rendering Post-Fix Observation (Step 4, four-step plan)

**Drafted:** 2026-05-03 (probe runs 2026-05-04T05:16Z–05:26Z UTC).
**HEAD:** `a3ff547` on `main` (Wave 1 complete).
**Phase:** 10 — Operational Observation.
**Position in plan:** Step 4 of the four-step plan documented in
`d76e71b`. This memo is doc-only, lands as the bridge between Wave 1
(Steps 1-3, complete) and Wave 2 (Step 5, deferred).

**Predecessor:** `_observations/OBSERVATIONS_2026_05_03_SCORE_RENDERING_PRE_FIX_DIAGNOSTIC.md`
(Step 1; reviewer-acceptance pattern, arc-split distribution).

---

## TL;DR

- **Wave 1 mechanical correctness confirmed.** Step 2's "to" format
  and Step 3's verbatim-copy instruction both propagate into the
  prompt for the regenerate code path.
- **The PARAPHRASE_ROUNDED hazard the four-step plan targeted is
  eliminated** in the post-fix sample. 0/15 pair-classifications
  hit the rounded-pair pattern across three regen attempts.
- **A new dominant pattern emerged: 100% PARAPHRASE_OTHER** (both
  decimal scores present in prose, not in verbatim paired form).
  This is the same pattern v17 was approved with — reviewer-acceptable
  per Step 1 evidence.
- **Step 5 severity recommendation: Policy C with HARD severity**,
  with proximity-window N calibrated empirically before
  implementation. Policy A would auto-reject every post-fix recap;
  Policy B (SOFT) provides no enforcement floor.
- **A Wave 1 verbatim-compliance regression is observable** but not
  load-bearing for Step 5: pre-fix `id=122` (2026-04-20) hit 5/5
  VERBATIM under the OLD prompt; post-fix `id=125-127` (2026-05-04)
  hit 0/5 VERBATIM under the NEW prompt. Flagged as separate thread.

---

## Methodology

Single regen on W13 2025 (the same week characterized in the Step 1
memo) using:

```
SQUADVAULT_PROMPT_AUDIT=1 scripts/py scripts/recap_artifact_regenerate.py \
    --db .local_squadvault.sqlite --league-id 70985 \
    --season 2025 --week-index 13 \
    --reason "Phase 10 observation: post-score-string-fix prose capture" \
    --created-by "steve"
```

The lifecycle ran 3 internal verification attempts. All 3 failed —
attempt 1 on a SERIES claim, attempts 2 and 3 on SUPERLATIVE claims —
unrelated to score-string format. **No new `recap_artifacts` row was
persisted** (`created_new: false` in the regenerate JSON output).
Evidence lives in `prompt_audit` rows id=125, 126, 127 (one per
attempt).

Score-format evidence comes from the audit prose, not from a
persisted `rendered_text`. The harness's `classify_pair` function
operates on raw prose and is the same logic that classified the
pre-fix Arc B distribution in the Step 1 memo, so the comparison is
apples-to-apples at the pair-classification level.

W13 2025 was chosen over W14+ to keep the comparison clean: same
canonical events, same matchup pairs, same franchises, same
nickname map as the Step 1 memo's evidence base.

---

## Probe 1 — Prompt-side propagation (Wave 1 mechanical correctness)

For each of the three post-fix audit rows, query whether the
assembled prompt contains:
1. The Step 2 "to" format applied to the W13 score (`107.65 to 65.40`).
2. The Step 3 verbatim-copy instruction marker.

| audit id | attempt | "to" format in prompt? | Step 3 instruction in prompt? |
|---|---|---|---|
| 125 | 1 | YES | YES |
| 126 | 2 | YES | YES |
| 127 | 3 | YES | YES |

**Both Step 2 and Step 3 are reaching the prompt.** Wave 1 is
mechanically correct for this code path. The model receives a prompt
that reflects the new contract on every attempt.

---

## Probe 2 — Post-fix prose classification

The diagnostic harness `classify_pair` applied to each attempt's
`narrative_draft`, against the 5 W13 2025 canonical matchup pairs.
Predecessor rows (114, 122, 123) included for trajectory context.

| audit id | attempt | captured_at | verifier passed | prose len | VERB | ROUND | OTHER | MARG | OMIT |
|---|---|---|---|---|---|---|---|---|---|
| 127 | 3 | 2026-05-04T05:17:25Z | 0 | 1719 | **0** | **0** | **5** | 0 | 0 |
| 126 | 2 | 2026-05-04T05:17:07Z | 0 | 1862 | **0** | **0** | **5** | 0 | 0 |
| 125 | 1 | 2026-05-04T05:16:49Z | 0 | 2293 | **0** | **0** | **5** | 0 | 0 |
| 123 | 2 | 2026-04-20T20:31:45Z | 1 | 1624 | 0 | 1 | 0 | 4 | 0 |
| 122 | 1 | 2026-04-20T20:31:30Z | 0 | 2273 | 5 | 0 | 0 | 0 | 0 |
| 114 | 3 | 2026-04-16T23:43:24Z | 1 | 1935 | 0 | 2 | 0 | 3 | 0 |

(Bold rows are post-fix.)

### What the post-fix distribution shows

Across 15 pair-classifications (3 attempts × 5 pairs):

| Category | Count | % |
|---|---|---|
| VERBATIM | 0 | 0% |
| PARAPHRASE_ROUNDED | 0 | 0% |
| PARAPHRASE_OTHER | 15 | 100% |
| MARGIN_ONLY | 0 | 0% |
| OMITTED | 0 | 0% |

- **PARAPHRASE_ROUNDED hazard eliminated** (0/15). This is the
  failure mode the four-step plan targeted; the data-layer fix
  works.
- **MARGIN_ONLY rate collapsed to 0%** (down from Arc B's 80%
  pre-fix). The model is now stating both scores in every matchup,
  not eliding them.
- **PARAPHRASE_OTHER dominates at 100%.** The model uses both
  decimal scores in narrative prose but does not paste the verbatim
  paired form. This matches the v17 reviewer-accepted pattern
  documented in the Step 1 memo:
  > *"Italian Cavallini put up 149.95 points to demolish Eddie & the
  > Cruisers by nearly 45 points... Eddie managed just 105.10..."*

### What the predecessor rows show

- **id=122 (2026-04-20, OLD prompt):** 5/5 VERBATIM under the OLD
  prompt. Failed verification on SUPERLATIVE (claim of 48.75), not
  score format. Confirms the model **was capable** of full verbatim
  compliance under the old hyphen format.
- **id=123 (2026-04-20):** 0 VERBATIM, 1 ROUNDED, 4 MARGIN_ONLY —
  yet `verification_passed: 1`. This row passed the verifier with
  the dominant-failure hazard pattern, never persisted to
  `recap_artifacts`. Documents an asymptotic verifier-coverage
  point: the existing `verify_scores` pair-detection did not catch
  the rounded-form pair in this prose, while a stricter SCORE_VERBATIM
  check would have. (Already named in user-memory's
  "verifier coverage is asymptotic" thread.)
- **id=114 (2026-04-16):** 0 VERBATIM, 2 ROUNDED, 3 MARGIN_ONLY —
  predecessor of the `recap_artifacts.id=1252` v22 row. Sanity-check
  on the harness; matches the Step 1 memo's Arc B characterization.

---

## What this evidence supports

### Wave 1 closure

The four-step plan's score-rendering hazard goal is met:

| Pre-fix Arc B (v18-v22 from Step 1) | Post-fix (id=125-127) |
|---|---|
| 4.0% VERBATIM | 0% VERBATIM |
| 12.0% PARAPHRASE_ROUNDED | **0% PARAPHRASE_ROUNDED ✓** |
| 4.0% PARAPHRASE_OTHER | **100% PARAPHRASE_OTHER** |
| 80.0% MARGIN_ONLY | 0% MARGIN_ONLY |

The hazard in the brief's targeting (PARAPHRASE_ROUNDED, the
ambiguous hyphen-rounded form) is gone in 0/15. The
score-elision-as-avoidance pattern (MARGIN_ONLY) collapsed in
parallel — the model is no longer routing around the verifier
or the prompt by omitting scores entirely.

### Step 5 severity policy: Policy C, HARD

The brief's selection rule (≥95% VERB → A; 70-95% → C; <70% → B)
was designed assuming a post-fix distribution dominated by VERBATIM
or its absence. The actual distribution is dominated by
PARAPHRASE_OTHER, which the rule does not categorize.

Reading the evidence in light of v17 reviewer-acceptance:

- **Policy A (HARD verbatim)** would auto-reject 100% of post-fix
  recaps including reviewer-acceptable prose. **Wrong.**
- **Policy B (SOFT flag)** would surface no rejection signal. With
  the PARAPHRASE_ROUNDED hazard eliminated, Policy B provides no
  enforcement floor against any future regression. **Insufficient.**
- **Policy C (verbatim OR both scores within proximity window)**
  passes the post-fix PARAPHRASE_OTHER pattern via the proximity
  branch while preserving HARD severity against any future
  PARAPHRASE_ROUNDED. **Correct fit.**

Policy C requires a calibrated proximity window. Two anchors:

1. **Step 1 memo's v17 evidence** showed a 174-character gap between
   decimals in reviewer-accepted prose. **N=80** (the brief's default
   matching `_PAIR_WINDOW = 80`) would HARD-fail v17 — false-reject.
2. **The post-fix prose lengths** are 1719 / 1862 / 2293 chars. With
   5 matchups per recap, decimal pairs may be spread across multiple
   sentences with player attribution between them.

**Calibration step required as the first concrete action of Step 5
implementation:** before writing the verifier function, run a probe
that classifies each PARAPHRASE_OTHER pair in tonight's three
audit rows by minimum-decimal-pair gap. The recommendation for N
follows from that distribution. A reasonable a-priori range is
**N ∈ [200, 400]** — wide enough to capture v17's 174-char gap with
a buffer, narrow enough to retain signal against scattered
unrelated decimal mentions.

---

## Out of scope — flagged for follow-up

### Wave 1 verbatim-compliance regression thread

`id=122` (2026-04-20, OLD prompt) achieved 5/5 VERBATIM on attempt 1.
`id=125-127` (2026-05-04, NEW prompt) achieved 0/5 VERBATIM on every
attempt. Both samples come from the same model, same league, same
week. The change in compliance correlates directly with Wave 1's
prompt and format change.

Most plausible cause: **the post-fix bullet form `"X beat Y 142.60
to 98.30."` is longer and more multi-token than the pre-fix
`"X beat Y 142.60-98.30."` form. The model may treat the longer
phrase as friction and route around it by rendering scores
individually-in-sentences in narrative voice.**

This is observable but **not load-bearing for Step 5**. The
PARAPHRASE_OTHER pattern is reviewer-acceptable; the failure mode
the brief targeted (PARAPHRASE_ROUNDED) is eliminated; Policy C is
robust to PARAPHRASE_OTHER. The regression thread bears on **prompt
design** (would a different format recover verbatim compliance?)
not on **verifier policy**.

If the thread ever becomes actionable, the diagnostic-first move is
to A/B the format choice with a probe: regenerate W13 2025 once with
each candidate format ("to", "vs.", en-dash with `_ascii_punct`
carve-out) and compare verbatim rates. Not in scope for Wave 2.

### W13 2025 SUPERLATIVE/SERIES blocking pattern

Three of three post-fix attempts hit verifier rejection on
SUPERLATIVE or SERIES claims. The model fabricates "all-time"
record claims (e.g., "claim of 27.30" is rejected because actual
all-time high team score is 198.80). User memory already names this
as the verifier-asymptotic-coverage thread; W13 2025 is now
demonstrably blocked-on-verification independent of score format.

If the post-v17 regression thread (Step 1 memo) traces to this
SUPERLATIVE pattern — where the model retries against verifier
feedback by progressively eliding more content — that would unify
two threads. Not investigated here. Out of scope for Step 5.

### `prompt_audit` ↔ `recap_artifacts` sync gap

`id=123` from 2026-04-20T20:31:45Z has `verification_passed: 1`.
There is no corresponding row in `recap_artifacts` for that
timestamp. Either the lifecycle's persist path was bypassed for
that attempt, or a `selection_fingerprint` collision suppressed the
write, or the regen invocation took a different code path. Out of
scope here; flagged adjacent to the editorial_actions population
gap from the Step 1 memo as audit-system observability work.

---

## Limitations of this memo's evidence

1. **Single regen, single week.** Three attempts within one regen
   session is a thin denominator. The 100% PARAPHRASE_OTHER pattern
   is consistent within the sample but a second regen on a different
   week (W14 or earlier 2025) would test whether the pattern
   generalizes.

2. **No persisted draft.** The lifecycle did not write a v23. Step
   4's classification rests on `prompt_audit.narrative_draft`
   strings, not on `recap_artifacts.rendered_text`. This is fine
   for the score-format question (the prose is the prose) but
   means there is no DRAFT-state recap to compare downstream
   consumers against.

3. **The verifier blocked all three attempts on non-score-format
   reasons.** The model's prose under "have I just been rejected
   on SUPERLATIVE" feedback may differ from the prose it would
   produce on a clean attempt. If the SUPERLATIVE issue clears,
   the score-format pattern may shift.

4. **Proximity-window N is uncalibrated.** This memo recommends
   Policy C but defers N selection to the Step 5 implementation
   session, conditional on the calibration probe.

---

## Sample row IDs cited

| Table | id | Season/Wk | Attempt | captured_at | Used as evidence for |
|---|---|---|---|---|---|
| prompt_audit | 125 | 2025/13 | 1 | 2026-05-04T05:16:49Z | Post-fix attempt 1, 5/5 PARAPHRASE_OTHER |
| prompt_audit | 126 | 2025/13 | 2 | 2026-05-04T05:17:07Z | Post-fix attempt 2, 5/5 PARAPHRASE_OTHER |
| prompt_audit | 127 | 2025/13 | 3 | 2026-05-04T05:17:25Z | Post-fix attempt 3, 5/5 PARAPHRASE_OTHER |
| prompt_audit | 122 | 2025/13 | 1 | 2026-04-20T20:31:30Z | Pre-fix 5/5 VERBATIM under old prompt (regression evidence) |
| prompt_audit | 123 | 2025/13 | 2 | 2026-04-20T20:31:45Z | Pre-fix verifier-coverage gap (passed with 1 ROUNDED) |
| prompt_audit | 114 | 2025/13 | 3 | 2026-04-16T23:43:24Z | Pre-fix predecessor of recap_artifacts v22 |
| recap_artifacts | 1252 | 2025/13 | v22 | 2026-04-16T23:43:24Z | Latest persisted version (DRAFT, not the regen target) |

---

## Next actions in the brief's flow

1. This memo lands as the bridge commit between Wave 1 and Wave 2.
2. **Step 5 implementation session — first concrete action:**
   calibrate the Policy C proximity window N against the post-fix
   PARAPHRASE_OTHER pairs in id=125-127. Probe surfaces minimum gap
   per pair; recommendation is `max(observed_gaps) + buffer`,
   capped against signal-loss reasonableness (~400 chars).
3. **Step 5 implementation session — second action:** implement
   `verify_score_strings_verbatim` per the Policy C function
   skeleton (`step_5_verifier_three_policies.py`), with the
   calibrated N. Tests per the skeleton's commented Policy C
   sketches plus a v17-style decimal-pair-with-narrative test
   asserting acceptance.
4. Step 5 commits as Wave 2's only commit.

Separately tracked, not in this brief or Wave 2:

- Wave 1 verbatim-compliance regression thread.
- W13 2025 SUPERLATIVE/SERIES blocking pattern.
- `prompt_audit` ↔ `recap_artifacts` sync gap.
- All threads from the Step 1 memo's "out of scope" section
  (post-v17 regression, editorial_actions population gap).

---

## Anti-drift discipline notes

- This memo does not attempt to revisit Wave 1's design decisions.
  Step 2's format ("to") and Step 3's prompt instruction are
  committed; the verbatim-compliance regression is named as a
  follow-up thread, not as a retroactive design challenge.
- Step 5's policy selection is grounded in BOTH post-fix evidence
  (this memo) AND v17 reviewer-acceptance (Step 1 memo). Neither
  alone would suffice — the post-fix evidence shows what the model
  does; the v17 evidence shows what the reviewer accepts.
- Proximity window N is deliberately deferred to the implementation
  session. The diagnostic-first discipline says: probe before
  picking; pick before coding. The probe is one Python function;
  no need to commit to a number in the memo.
- Three attempts in one regen is a smaller denominator than Step
  1's 22-version arc-split. The recommendation is robust to
  expansion: if a second regen later reveals a different
  distribution, Policy C with a calibrated N still fits — it is the
  only policy that doesn't over-reject reviewer-accepted prose.
