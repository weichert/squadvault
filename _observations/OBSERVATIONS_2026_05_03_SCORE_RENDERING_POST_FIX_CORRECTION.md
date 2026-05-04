# OBSERVATIONS — Score-Rendering Post-Fix Correction (Step 4 amendment)

**Drafted:** 2026-05-03 (probe runs 2026-05-04T05:42Z–05:50Z UTC).
**HEAD:** `46c2ca5` on `main` (Step 4 memo) at memo-write time.
**Phase:** 10 — Operational Observation.
**Position in plan:** Correction to the Step 4 memo at
`_observations/OBSERVATIONS_2026_05_03_SCORE_RENDERING_POST_FIX_OBSERVATION.md`.
This memo supersedes that memo's post-fix classification numbers and
Step 5 policy recommendation. Other content in the predecessor
memo (methodology, propagation verification, two of three follow-up
threads) remains valid.

---

## TL;DR

- **The Step 4 memo's post-fix distribution is wrong.** It reported
  100% PARAPHRASE_OTHER. Actual distribution is **100% VERBATIM**
  (15/15 pair-classifications across three regen attempts).
- **Root cause: a bug in the diagnostic harness, not in production
  code.** The v3.1 harness's `classify_pair` hardcoded the
  pre-Step-2 hyphen-form bullet pattern as the only VERBATIM
  signal. When Step 2 (commit `ff613a9`) changed the data layer to
  emit `"X.XX to Y.YY"` instead of `"X.XX-Y.YY"`, the harness fell
  out of sync with what it was measuring.
- **Step 5 policy recommendation: Policy A** (HARD verbatim).
  The brief's selection rule (≥95% VERBATIM → A) cleanly applies.
  The Step 4 memo's Policy C recommendation was based on a
  misreading of post-fix evidence.
- **The "Wave 1 verbatim-compliance regression" follow-up thread
  named in the Step 4 memo does not exist.** It was an artifact of
  the v3.1 classifier bug. The model did not regress on verbatim
  compliance — it produced 5/5 verbatim under both pre-fix
  (`id=122`, hyphen form) and post-fix (`id=125-127`, "to" form)
  prompts.
- **Wave 1 outcome is materially better than the Step 4 memo
  characterized.** Not just "ROUNDED hazard eliminated" — full
  verbatim compliance achieved.

---

## The bug

`step_1_score_diagnostic_harness.py` v3.1, `classify_pair`:

```python
# VERBATIM: deterministic-bullet pattern (current "X-Y" form)
if (f"{w_dec}-{l_dec}" in prose or f"{l_dec}-{w_dec}" in prose):
    return "VERBATIM"
```

That hardcoded check was written when the data layer emitted bullets
like `"X.XX-Y.YY"`. When Step 2 changed the data layer to
`"X.XX to Y.YY"`, the harness's VERBATIM check stopped recognizing
verbatim copies. Prose that contained literal `"107.65 to 65.40"`
fell through to the next branch and got classified as
PARAPHRASE_OTHER (both decimals present, not in paired form) —
because the classifier didn't think `"107.65 to 65.40"` *was* the
paired form.

The harness's `extract_snippet` had the parallel bug: its VERBATIM
anchoring only looked for hyphen-form needles. Snippets centered on
verbatim "to"-form prose would have fallen through to
`(no anchorable prose found)`. The Step 4 memo did not run a snippet
extraction probe so this didn't surface during Step 4 drafting.

### Where it should have been caught

The brief's Preamble check 1 (in v2 of the score-string brief)
verified that production verifier code (`verify_scores`'
`_SCORE_PATTERN` and `_INT_SCORE_PATTERN`) was format-agnostic and
remained additive across the format change. **The same check was
not applied to the diagnostic harness.** The harness's classifier
needed an update parallel to Step 2's data-layer changes; that
update did not happen.

This is the same class of failure the brief was specifically built
to prevent — the v2 brief revision warned about render-site
enumeration via clone-grep being load-bearing. The instrumentation
that classifies *output* needs the same discipline as the
production code that produces output.

### How the bug was caught

Step 5's calibration probe (Step 4 memo's "first concrete action")
measured decimal-pair gaps for each pair classified as
PARAPHRASE_OTHER. Result: every gap was 9 or 10 characters across
all 15 pair-classifications (`min=9, max=10, mean=9.8`).

A 9-10 character gap is what the verbatim "to" string produces — in
`"107.65 to 65.40"`, the start position of `1` is 0 and the start
position of `6` (in `65.40`) is 10. The "to " separator is exactly
the four-character token that bridges the gap. **The calibration
probe wasn't measuring what we thought it was measuring; it was
inadvertently surfacing the harness bug.**

Cross-check: a `re.finditer` for the pattern
`r"\d{2,3}\.\d{2}\s+to\s+\d{2,3}\.\d{2}"` against the same prose
(`prompt_audit.id=125`) found 5 matches — exactly one per matchup
pair. The model produced verbatim "to"-form score strings for all
five matchups in all three attempts. Sample:

> *"...took down Stu 96.95 to 94.60 in the week's tightest..."*
>
> *"...with a 101.15 to 97.80 win over Pat..."*
>
> *"...with a 107.65 to 96.50 victory over Brandon..."*
>
> *"...crushing Eddie 149.95 to 105.10 behind Patrick Maho..."*
>
> *"...handled Ben 112.15 to 100.95, with Jameson Willi..."*

---

## Corrected post-fix distribution

Re-classification of `prompt_audit` rows 125–127 under v3.2 of the
harness (which accepts both hyphen and "to" forms as VERBATIM):

| audit id | attempt | V_old (v3.1) | V_new (v3.2) | ROUND | OTHER | MARG | OMIT |
|---|---|---|---|---|---|---|---|
| 127 | 3 | 0 | **5** | 0 | 0 | 0 | 0 |
| 126 | 2 | 0 | **5** | 0 | 0 | 0 | 0 |
| 125 | 1 | 0 | **5** | 0 | 0 | 0 | 0 |

**Aggregate (15 pair-classifications across 3 attempts):**

| Category | Count | % |
|---|---|---|
| VERBATIM | 15 | **100.0%** |
| PARAPHRASE_ROUNDED | 0 | 0.0% |
| PARAPHRASE_OTHER | 0 | 0.0% |
| MARGIN_ONLY | 0 | 0.0% |

Pre-fix predecessor rows reclassify the same way under v3.2 as
under v3.1 — backward-compatible — confirming v3.2 doesn't shift
any previously-VERBATIM classification.

---

## Updated Step 5 policy selection

The brief's selection rule:
- **≥95% VERBATIM → Policy A** (HARD verbatim)
- 70–95% → Policy C (verbatim OR proximity)
- <70% → Policy B (SOFT)

**Post-fix VERBATIM rate: 100%. → Policy A.**

The Step 4 memo recommended Policy C. That recommendation was based
on the v3.1 misclassification reading 0% VERBATIM. With corrected
data, Policy A is the rule's clean output and the right choice:

- **Policy A (HARD verbatim)** auto-rejects any prose that does not
  contain the canonical score string verbatim. Under the post-fix
  prompt and data layer, the model produces verbatim 100% of the
  time (15/15 in observed sample). Auto-rejection on the rare miss
  is appropriate enforcement.

- **Policy C** would still pass the same prose (via verbatim
  branch) but adds a proximity branch the data does not need. Extra
  surface area without value.

- **Policy B** (SOFT) provides no enforcement; not applicable to a
  ≥95% rate.

### What about the v17 evidence from Step 1?

The Step 1 memo's v17 reviewer-acceptance pattern showed an APPROVED
recap with one PARAPHRASE_OTHER pair (Cavallini 149.95 vs Eddie
105.10, decimals 174 chars apart). The Step 4 memo argued Policy A
would over-reject prose like v17's.

**That argument no longer applies in the same way.** v17 was approved
under the OLD prompt and OLD data layer (hyphen form). Under the NEW
prompt and NEW data layer, the model produces verbatim "to"-form
strings consistently (15/15). The reviewer-acceptance question is
still valid in principle — does the reviewer accept individual-
decimals-across-sentences prose if the model produces it? — but the
empirical question now is: **does the post-fix model produce that
pattern?**

Available evidence says no. Three attempts on W13 2025 produced
zero PARAPHRASE_OTHER pairs. If a future regen surfaces the pattern,
Policy A would HARD-fail it; the hard fail surfaces in the review
queue for human disposition; if the human approves, that's a signal
to revisit the policy. **Policy A is the right starting position
because the evidence says it has no false-positive risk against
current model behavior.** A Policy C escape valve can be added
later if data warrants.

---

## What in commit `46c2ca5` is superseded vs. retained

### Superseded by this memo

- **Probe 2 numbers** ("100% PARAPHRASE_OTHER", "0% VERBATIM",
  per-attempt classification counts).
- **Step 5 severity recommendation** (Policy C with HARD severity →
  now Policy A).
- **Calibration probe step** (the proximity window N is moot under
  Policy A).
- **A-priori N range** (200-400 chars).
- **The "Wave 1 verbatim-compliance regression" follow-up thread**
  — does not exist. The model produced 5/5 verbatim under both
  prompts; the apparent regression was a classifier artifact.
- **The framing that "Step 4 evidence dominated by PARAPHRASE_OTHER
  doesn't cleanly map to the brief's selection rule"** — the
  evidence does cleanly map; the rule selects Policy A.

### Retained from `46c2ca5`

- **Methodology** — single regen on W13 2025, evidence in
  `prompt_audit` rows, no persisted artifact.
- **Probe 1: Wave 1 mechanical correctness confirmed** — both
  Step 2 and Step 3 propagate into the prompt; verified via
  `prompt_text` LIKE queries.
- **PARAPHRASE_ROUNDED hazard elimination** — 0/15 ROUNDED pairs
  under both v3.1 and v3.2. The brief's targeted hazard is gone.
- **W13 2025 SUPERLATIVE/SERIES blocking pattern thread** —
  unchanged; still a real verifier-coverage / model fact-fabrication
  thread independent of score format.
- **`prompt_audit` ↔ `recap_artifacts` sync gap thread** —
  unchanged; `id=123` still passed verification but has no
  corresponding artifact row.
- **Limitations** (single regen, single week, three attempts) —
  still apply.
- **Sample row IDs cited** — unchanged.

---

## Lessons / discipline notes

1. **Diagnostic instrumentation tracks data-layer contracts.** When
   production code's output format changes, instrumentation that
   reads or classifies that output needs a parallel update.
   v3 of this brief is "the artifact of clone-grep discipline" for
   render sites; v3.2 of the harness is the parallel artifact for
   instrumentation discipline.

2. **Anomalies in metric distributions deserve investigation, not
   acceptance.** The Step 5 calibration probe's `gap=10 across all
   15 pairs` was statistically suspicious — real-world variance is
   never zero. The Step 4 memo accepted a 100% PARAPHRASE_OTHER
   reading without questioning whether the underlying classifier
   was producing that reading correctly. Future memos should treat
   "all observations identical" as a signal to verify the
   instrument before reasoning from the data.

3. **Cross-validate classification with raw-prose inspection.**
   The bug surfaced in 30 seconds once the right `re.finditer`
   pattern ran against the prose. The Step 4 memo could have run
   the same check before publishing. Future Step-N memos that
   classify model output should include at least one raw-prose
   probe alongside the aggregate counters.

4. **The brief's Preamble check pattern generalizes beyond
   production code.** v2 of the score-string brief verified
   `verify_scores` pair-detection was format-agnostic; that same
   shape of check should have been applied to the harness. Add to
   future briefs: "any tool that reads or classifies the format
   under change must be Preamble-checked alongside production code."

---

## Next actions

1. **Land this correction memo as a doc-only commit.** Title:
   `observations: Step 4 post-fix observation correction`. The
   commit explicitly references `46c2ca5` as the predecessor it
   amends.

2. **Re-publish the harness as v3.2.** Whether or not it gets
   tracked in the repo (the Step 1 memo's discipline says no — keep
   it as a `/tmp/`-only diagnostic), the canonical version going
   forward is v3.2. Future runs that revive the harness should pull
   v3.2, not v3.1.

3. **Step 5 implementation under Policy A.** The implementation
   skeleton at `step_5_verifier_three_policies.py` already has
   `verify_score_strings_verbatim__policy_a_hard` drafted. Tests
   per the skeleton's commented Policy A sketches. Single commit
   closes Wave 2.

---

## Anti-drift discipline notes

- This memo does not amend or rewrite history. `46c2ca5` stays in
  the log as-is. The audit trail of "we found a bug in our own
  diagnostic instrumentation" is more valuable than a clean history
  that hides the diagnostic process.
- Step 5 policy selection is now grounded in v3.2-classified
  evidence, not v3.1-classified evidence. The harness change is
  the only material instrumentation change between this memo and
  the predecessor.
- All three of the predecessor's follow-up threads either are
  retained (SUPERLATIVE blocking, audit sync gap) or explicitly
  closed (verbatim regression — closed because the regression
  doesn't exist).
- The "harness instrumentation tracks data layer" lesson is named
  here for future briefs to internalize, not just as session
  closure.
