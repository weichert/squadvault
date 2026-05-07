# OBSERVATIONS — SCORE_VERBATIM legacy-drift Step 0 probe results

**Drafted:** 2026-05-07.
**HEAD at run:** `2e05884` (probe commit immediately preceding this memo).
**Phase:** 10 — Operational Observation.
**Position in plan:** Step 0 of the SCORE_VERBATIM 59-row legacy-drift carry-forward thread. Diagnostic-only; gates the direction choice for the thread.

---

## TL;DR

- **Memory's "59-row drift" framing is wrong.** Actual SCORE_VERBATIM failing-row count under `verifier_tag=59846b0` is **127** rows out of 142 in the reverify corpus, with **579 failure-instances** spanning **34 distinct (season, week) pairs**. The 59 figure cited in memory edit and standing-backlog framing came from a different probe with a different methodology and is superseded by this Step 0.
- **Bucket distribution (per the four-bucket classifier in `2e05884`):**
  - ALL_LEGACY_HYPHEN: 62 rows / 283 failures
  - MIXED_LEGACY_AND_NO_SCORE: 43 rows / 213 failures
  - ALL_NO_SCORE: 22 rows / 83 failures
  - POST_FIX_TO_PRESENT: 0 rows / 0 failures
- **Era cross-tab against Wave 1 ship date (2026-05-03):** 124 pre-Wave-1 rows / 3 post-Wave-1 rows / 0 verifier-impossible.
- **The 3 post-Wave-1 rows (audit_ids 128, 135, 137) are not regressions.** Each is ALL_NO_SCORE on exactly 1 matchup (out of 5); each had `original_passed=0` — the verifier rejected them at recap-time as designed. Retry/fallback behavior absorbed these; they did not reach published prose. The probe's automatic verdict overstated these as "real-bug signal"; correcting that framing here.
- **VERDICT: Direction 1 (acceptance memo + close) is supported by evidence.** No production-path bug. Verifier surface is helper-bound and sound (zero POST_FIX_TO_PRESENT). The reverify row-level pass→fail is exactly the legacy-drift artifact memory edit #16 already documents.
- **Direction 2 (reverify-script enhancement) is a separable paper-cut fix.** Not session-blocking. If pursued, it eliminates the manual category-breakdown SQL at every merge gate. Worth considering as an independent follow-up.

---

## 1. Probe output (verbatim)

Full probe output captured at `/tmp/score_verbatim_step_0_output.txt`. Headline counts:

| Bucket | Rows | Failures | Notes |
|---|---:|---:|---|
| ALL_LEGACY_HYPHEN | 62 | 283 | Every failing matchup has a hyphen-form score in prose; clean pre-Wave-1 capture |
| MIXED_LEGACY_AND_NO_SCORE | 43 | 213 | Some matchups hyphen-form, others elided; transitional pre-Wave-1 |
| ALL_NO_SCORE | 22 | 83 | No score string of any form in prose for any failing matchup |
| POST_FIX_TO_PRESENT | 0 | 0 | Verifier-construction-impossible bucket; zero hits = helper-bound discipline holds |
| **Total** | **127** | **579** | 34 distinct (season, week) pairs |

Era cross-tab:

| Bucket | pre-Wave-1 | post-Wave-1 |
|---|---:|---:|
| ALL_LEGACY_HYPHEN | 62 | 0 |
| MIXED_LEGACY_AND_NO_SCORE | 43 | 0 |
| ALL_NO_SCORE | 19 | 3 |
| POST_FIX_TO_PRESENT | 0 | 0 |
| **Total** | **124** | **3** |

## 2. The 59-vs-127 reconciliation

Memory edit and predecessor session-brief framing both cited "59-row drift" as established by "Probe 1.4.A.B in the post-fix memo." The 59 figure does not appear in this Step 0's probe output and does not match the 142-row corpus's actual SCORE_VERBATIM-failing-row count under any plausible interpretation.

Plausible explanations for the 59 figure (none verified in this session):
- A different reverify tag run (older, smaller corpus).
- A different probe methodology (e.g., distinct (season, week) pairs of approved-only artifacts, not prompt_audit attempts).
- A typo from "59" being the verifier_tag prefix (`59846b0`) rather than a row count.

This memo's count (127 rows) is the authoritative number going forward. Memory edit will be updated post-commit.

## 3. Pre-Wave-1 cohort (124 rows): legacy drift

124 of 127 failing rows were captured before 2026-05-03. The breakdown by bucket:
- 62 ALL_LEGACY_HYPHEN — every flagged matchup has at least one hyphen-form score string in `narrative_draft`. The model produced prose under the OLD data layer (which emitted `"X.XX-Y.YY"` in the prompt's facts block); the model copied that form. The new verifier expects `"X.XX to Y.YY"`; substring match fails. Pure legacy drift.
- 43 MIXED_LEGACY_AND_NO_SCORE — partial coverage; some matchups got hyphen-form, others got no score at all. Transitional under the old prompt's variable model behavior.
- 19 ALL_NO_SCORE — the model elided all flagged matchup scores from prose. Score-elision-as-avoidance pattern; documented in `OBSERVATIONS_2026_05_03_SCORE_RENDERING_POST_FIX_OBSERVATION.md` Arc B as the dominant pre-fix failure mode (80% MARGIN_ONLY rate).

None of these 124 rows constitute a production-path bug. The captured prose is captured. The recap_artifacts those rows correspond to (where state=APPROVED) were approved under the old verifier surface. Whether any of those approved recaps have user-visible score-format issues is a separate quality question, not a verifier-correctness question.

## 4. Post-Wave-1 cohort (3 rows): verifier-consistent rejections, not regressions

Three post-Wave-1 rows fall in the failing set:

| audit_id | captured_at | (S, Wk, attempt) | original_passed | failing matchups | Bucket |
|---:|---|---|---:|---:|---|
| 128 | 2026-05-04T09:15:43 | (2024, 13, 1) | 0 | 1 | ALL_NO_SCORE |
| 135 | 2026-05-04T10:57:15 | (2024, 9, 3) | 0 | 1 | ALL_NO_SCORE |
| 137 | 2026-05-04T10:58:06 | (2024, 12, 1) | 0 | 1 | ALL_NO_SCORE |

Common pattern: the model wrote prose under the post-Wave-1 prompt+data layer, hit verbatim "to"-form on 4 of 5 matchups, and elided the 5th. The verifier caught the elision and rejected the attempt at recap-time (`original_passed=0`). The lifecycle's retry-or-fallback behavior absorbed each of these; none reached published prose.

This is exactly what the verifier is supposed to do. Re-running reverify reproduces the same correct rejection. These are not regressions, not legacy drift, and not bugs. The probe's automatic verdict logic — which I wrote at `2e05884` — overstated this finding by labelling any post-Wave-1 row not in POST_FIX_TO_PRESENT as "real-bug signal" without considering `original_passed`. Correcting that framing in this memo: the verdict is sound only when read alongside the original_passed column.

A future enhancement to the probe could refine the verdict to:
- POST_FIX_TO_PRESENT > 0 → verifier/helper drift; investigate.
- post-Wave-1 row with `original_passed=1` → real regression in approved prose; investigate.
- post-Wave-1 row with `original_passed=0` → verifier-consistent rejection; non-finding.

Not implementing this in this session — Direction 1 doesn't require probe enhancement, and the manual interpretation is documented here for future re-runs.

## 5. POST_FIX_TO_PRESENT = 0 — verifier construction sound

Zero rows in the impossible-by-construction bucket confirms the verifier helper-bound discipline: every captured failure encodes the canonical scores in its evidence string, and every canonical-form regeneration of those scores correctly fails substring matching against the captured prose. There is no helper drift between the captured reverify (`verifier_tag=59846b0`) and the current `format_matchup_score_str` at `score_strings_v1.py:36`.

This is a strong signal: even if the verifier or the helper changes in the future, the probe's POST_FIX_TO_PRESENT bucket will surface drift on next re-run. Durable infrastructure.

## 6. Verdict and direction

**Direction 1 (acceptance memo + close) is the correct call.**

Evidence:
- Pre-Wave-1 cohort (124 rows) is by-construction not a bug. The verifier surface changed; old captured prose retroactively flags. This is what "legacy drift" means.
- Post-Wave-1 cohort (3 rows) is verifier-consistent rejection, not regression. `original_passed=0` for all three.
- Zero POST_FIX_TO_PRESENT — verifier construction sound; no helper drift to investigate.

What "close" means concretely:
- Retire "SCORE_VERBATIM 59-row legacy drift" from the standing backlog.
- Update memory edit #17 (or its successor) to reflect the closure.
- Reverify-as-merge-gate technique (memory edit #16) remains the operational guidance: when reverify prints "REGRESSION: do NOT merge" with pass→fail > 0, run category-breakdown SQL filtering to legacy-drift categories before deciding. The 124-row legacy cohort is durable; it will continue to print regression warnings at every merge gate until rotated out of the corpus (which requires regenerating those weeks under post-Wave-1 — out of scope for this thread).

## 7. Optional follow-on — Direction 2 (reverify-script enhancement)

Direction 2 was framed as: extend `reverify_prompt_audit.py` to emit per-category delta attribution as a first-class summary column, eliminating the manual category-breakdown SQL step at every merge gate.

Step 0's evidence does not require this. The legacy-drift cohort is a known constant; the manual SQL works; the cost-per-merge-gate is small (one paste of category-breakdown SQL).

That said, Direction 2 remains a small, well-scoped paper-cut fix. The script change is roughly:
- Add a `--baseline-tag` flag for delta computation against a prior reverify tag.
- Emit a per-category attribution summary alongside the row-level pass→fail count.
- Print "REGRESSION (CATEGORY-NEW): n" rather than just "REGRESSION".

If pursued, that's a separate session — single file, one commit, not gating on more diagnostic work. Recording here as named-only follow-on; not in scope for this Step 0 closure.

## 8. Re-activation criterion

The thread closes here, but conditions under which it would re-fire:

- POST_FIX_TO_PRESENT bucket increments above zero on a future reverify run → verifier or helper drift; investigate immediately.
- Post-Wave-1 row appears in the failing set with `original_passed=1` → real regression in approved prose; promotes back to actionable.
- A new verifier rule analogous to SCORE_VERBATIM ships (e.g., STREAK_VERBATIM per the streak-verb thread) and creates its own legacy-drift cohort → same playbook, distinct thread.

The probe at `scripts/diagnose_score_verbatim_drift.py` is durable. Re-running against a future reverify tag is one paste; the four-bucket classification is generic to the SCORE_VERBATIM verifier surface.

## 9. Standing-backlog updates

- **SCORE_VERBATIM 59-row legacy drift:** CLOSED. Promoted from open horizon to retired with this memo.
- **Direction 2 (reverify-script category-attribution enhancement):** named-only follow-on; promoted to standing backlog as a small, well-scoped item.

Other open items unchanged:
- Cat 3c row-76 W14 2025 attribution edge case (deferred).
- Snap-outcome detection (named-only).
- Tier 5 W14+ live observation cadence (active-next-focus per Bug 1 Step 0b closure).
- NOTABLE-pass alphabetical lockout investigation (named-only).
- Tests/ ruff cleanup (deferred).
- `d['raw_mfl']` write at `extract_recap_facts_v1.py:190` (deferred).
- Section 10 Q1 Bug 1 Step 1 production-path code (DEFER pending Tier 5 evidence; per `50e3141`).

## 10. Files referenced

- `2e05884` — Step 0 probe commit (`scripts/diagnose_score_verbatim_drift.py`).
- `OBSERVATIONS_2026_05_06_NOTABLE_SATURATION_STEP_1_CLOSURE.md` — source of the 142-row corpus framing and the per-category reverify breakdown table.
- `OBSERVATIONS_2026_05_03_SCORE_RENDERING_POST_FIX_OBSERVATION.md` — source of the Arc B / Arc A distribution analysis; documents the 80% MARGIN_ONLY pre-fix rate referenced in §3.
- `OBSERVATIONS_2026_05_03_SCORE_RENDERING_POST_FIX_CORRECTION.md` — source of the post-fix 100% verbatim rate (single-recap, 15-pair sample); does not contradict this memo's corpus-wide finding.
- `src/squadvault/core/recaps/verification/recap_verifier_v1.py:1036-1101` — `verify_score_strings_verbatim` function under analysis.
- `src/squadvault/core/recaps/render/score_strings_v1.py:36-62` — `format_matchup_score_str` helper; the canonical "to"-form source.
- `scripts/reverify_prompt_audit.py` — the reverify infrastructure; would be the surface for Direction 2 if pursued.
- `/tmp/score_verbatim_step_0_output.txt` — captured probe output from this session.

## 11. Methodology notes

- **The probe's verdict logic was too conservative.** The automatic verdict labelled any post-Wave-1 row not in POST_FIX_TO_PRESENT as "real-bug signal" without considering `original_passed`. Interpreting verdict output requires reading the per-row `orig` column. A future enhancement would refine the verdict to factor `original_passed` directly. Documenting here so the probe's future re-runs are interpreted correctly.
- **Helper-bound discipline (memory edit #12) held.** The probe's `_EVIDENCE_SCORES_RE` parses the verifier's evidence string format directly; `format_matchup_score_str`-equivalent canonical strings are computed via the same float-formatter the verifier uses. Zero POST_FIX_TO_PRESENT confirms the construction is sound across the 142-row corpus.
- **Smoke testing at apply time (memory edit pattern).** The probe's classification logic was smoke-tested against synthetic prose fixtures before commit: all four buckets, reverse-form (loser-first hyphen), zero-loser edge case. All passed. The probe shipped with confidence in the classification correctness; the only interpretation surface that needed refinement post-deployment was the automatic verdict, which is human-readable text rather than computational logic.
- **Memory accuracy hazard.** The "59 rows" figure in memory and prior session briefs was wrong by more than 2x. The lesson: when a backlog item carries a specific number, that number deserves verification at session start, not at end. Step 0 caught this — but only because the diagnostic was fresh-implemented rather than re-citing memory. A future memory-correction discipline could re-verify standing-backlog numbers periodically rather than letting them drift unchallenged.
- **Direction 1 vs Direction 2 selection.** Step 0's evidence supports Direction 1 unambiguously. Direction 2 was framed as a separable paper-cut; the evidence doesn't argue for it but doesn't argue against it either. Editorial call to defer.
