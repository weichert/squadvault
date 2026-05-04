# OBSERVATIONS — Streak Prompt Pre-Fix Diagnostic (Step 3.2, four-step playbook)

**Drafted:** 2026-05-04 UTC.
**HEAD:** `a33d764` on `main`.
**Phase:** 10 — Operational Observation.
**Position in plan:** Step 3.2 of the streak verb pre-computation
thread per
`_observations/OBSERVATIONS_2026_05_04_STREAK_VERB_PRE_COMPUTATION_SCOPE.md`.
This memo is doc-only; lands as part of Commit 2 of the session
brief (with the prompt-instruction insert into
`src/squadvault/ai/creative_layer_v1.py`), recording the BASELINE
harness measurement under the OLD prompt (no streak instruction).

**Predecessors:**
- `30dd16f` — audit memo (Step 3 scope).
- `6e7d44a` — Step 3.1 helper module + refactor.
- `50a7794` — Step 3.2 brief + harness v1 (non-functional; see
  Methodology footnote).
- `a33d764` — harness fix-up to v1.2
  (functional).

**Successor:** `OBSERVATIONS_2026_05_04_STREAK_PROMPT_POST_FIX_OBSERVATION.md`
will record the POST-FIX measurement and the policy decision for
Step 3.3.

---

## TL;DR

- **Baseline VERBATIM rate is 0/19 across all three scopes** under
  the OLD prompt (no §6 streak instruction). Not a single canonical
  streak headline appears as a substring in any approved or draft
  prose. The model paraphrases every claim.
- **INVERTED rate is also 0/19.** The verb-inversion failure mode
  that motivated Step 3 (audit memo §1: *"model writes 'won 3 in a
  row' of a losing streak"*) does NOT manifest in this corpus.
  Every paraphrase preserves direction correctly.
- **PARAPHRASE is universal at 19/19 (100%).** Across T1/T3/T4
  templates surfaced (no T2/T5/T6/T8/T9/T10 angle fired in the
  sampled scopes), the model consistently rephrases the canonical
  headline while preserving the underlying fact.
- **T9-LOSS fabrication confirmed.** 5 of 13 W13 2025 rows contain
  phrasings like "one short of the league record" / "three short
  of the all-time record" / "closing in on the all-time league
  record of 15 games" — the model inventing the asymmetric
  record-approach form the helpers deliberately don't emit (audit
  memo §10 Q1). Stable across attempts; concrete data point for
  promoting Q1 from "deferred curiosity" to a named follow-up
  thread.
- **Policy implication for Step 3.3:** HARD `STREAK_VERBATIM` as a
  baseline rule would auto-reject every recap in this corpus, since
  0/19 are verbatim. The realistic post-fix floor is SOFT-by-default,
  possibly HARD per-template if the §6 instruction shifts compliance
  dramatically on a specific template. Final decision in the
  post-fix memo.

---

## Methodology

Diagnostic harness `scripts/step_1_streak_diagnostic_harness.py`
(v1.2) classifies each STREAK claim emitted in
`prompt_audit.narrative_angles_text` against the model's
`prompt_audit.narrative_draft` into:

- **VERBATIM** — canonical headline (T1/T2/T3/T4/T8/T9/T10) or
  canonical outcome clause (T5/T6) appears as a substring of the
  prose.
- **PARAPHRASE** — a franchise alias is named in the prose, no
  inversion phrase is attached to that alias, but the canonical
  headline is not present verbatim.
- **INVERTED** — a franchise alias is named in the prose AND an
  inversion phrase (`win streak` / `losing streak` / `snapped` /
  `won/lost N in a row|straight|consecutive` / `on a N-game ...`)
  appears within 30 chars after an alias mention (possessively or
  as subject).
- **OMITTED** — no franchise alias appears in the prose.

Helper-bound: canonical phrases route through
`streak_strings_v1.format_streak_*`. Alias resolution mirrors the
resolver's pass 4a (curated nickname from `franchise_nicknames`)
and pass 4b (owner first-word from `franchise_directory`), plus
franchise-name first-word and full-name fallbacks.

**Note on harness iteration.** The v1 harness shipped at `50a7794`
had three bugs that produced misleading numbers in the first two
diagnostic runs: (1) `last10-approved` returned 0 claims due to
over-narrow temporal-proximity SQL on the prompt_audit join;
(2) 100% OMITTED across W13 due to missing alias resolution (the
model uses owner-first-word, not the angle-rendered full name);
(3) cross-team INVERTED false positives where another team's
opposite-direction streak in the windowed prose flagged inversion
incorrectly. The v1.2 fix-up at
`a33d764` resolves all three. Numbers
below are from v1.2.

Three query scopes were run:

1. **`last10-approved`:** the 10 most-recent `(season, week_index)`
   pairs that have at least one APPROVED artifact, with the latest
   `prompt_audit` row per pair. Selection-biased — these prose
   samples survived human review.
2. **`week --season 2024 --week-index 13`:** all `prompt_audit`
   rows for W13 2024.
3. **`week --season 2025 --week-index 13`:** all `prompt_audit`
   rows for W13 2025.

---

## Probe 1 — last10-approved (cross-season, selection-biased)

3 STREAK claims surfaced across the 10 approved-week pairs sampled.
The other 7 pairs surfaced no STREAK claims in their latest
`prompt_audit` row — either because the relevant week had no
franchise at `|streak| >= 3`, or because the angle text for that
particular pa row didn't contain a STREAK angle line.

| pa.id | season | week | attempt | template | direction | category   | canonical_headline                                  |
|------:|-------:|-----:|--------:|----------|-----------|------------|-----------------------------------------------------|
| 129   | 2024   | 13   | 2       | T4       | loss      | PARAPHRASE | Miller's Genuine Draft has lost 3 straight          |
| 44    | 2024   | 12   | 1       | T1       | win       | PARAPHRASE | Weichert's Warmongers on 6-game win streak          |
| 39    | 2024   | 9    | 1       | T3       | loss      | PARAPHRASE | Miller's Genuine Draft on 9-game losing streak      |

### Aggregate

| Category   | Count | %      |
|------------|------:|-------:|
| VERBATIM   |     0 |   0.0% |
| PARAPHRASE |     3 | 100.0% |
| INVERTED   |     0 |   0.0% |
| OMITTED    |     0 |   0.0% |

### Per-template

| Template                | n | V | P | I | O |
|-------------------------|--:|--:|--:|--:|--:|
| T1 (long-form winning)  | 1 | 0 | 1 | 0 | 0 |
| T3 (long-form losing)   | 1 | 0 | 1 | 0 | 0 |
| T4 (short-form losing)  | 1 | 0 | 1 | 0 | 0 |

### Reading

Even on the published surface (selection-biased toward verbatim
compliance for SCORE — see the score-thread Probe 1 finding of
42/42 VERBATIM), STREAK shows 0/3 verbatim. The contrast is
striking: under the OLD prompt, score format was approximately
learnable through iteration (the model converged on verbatim-paired
scores by versions 22-34 of W13 2024-2025 recaps); STREAK format
is not. The franchise is always named, the fact is always
preserved, but the canonical headline never reproduces. This
corroborates the audit memo §1 framing — streak prose has "data
correct, paraphrase loose, no verbatim contract" — and absent the
contract, the model never converges on verbatim form regardless of
review iteration.

---

## Probe 2 — W13 2024 (all states)

3 STREAK claims, all the same T4 angle for "Miller's Genuine Draft"
across attempts 1-2 of the most recent regen plus an earlier draft.
W13 2024 had only one franchise at `|streak| >= 3` —
Miller's Genuine Draft on a 3-game losing streak.

| pa.id | season | week | attempt | template | direction | category   |
|------:|-------:|-----:|--------:|----------|-----------|------------|
| 124   | 2024   | 13   | 1       | T4       | loss      | PARAPHRASE |
| 128   | 2024   | 13   | 1       | T4       | loss      | PARAPHRASE |
| 129   | 2024   | 13   | 2       | T4       | loss      | PARAPHRASE |

### Aggregate

| Category   | Count | %      |
|------------|------:|-------:|
| VERBATIM   |     0 |   0.0% |
| PARAPHRASE |     3 | 100.0% |
| INVERTED   |     0 |   0.0% |
| OMITTED    |     0 |   0.0% |

### Reading

All three rows paraphrase to the same shape:
`"extending Miller's losing streak to three games"` (or close
variants — `"Miller has mathematically locked up the worst season..."`).
The verb "extending" is the model's preferred substitute for the
canonical T4 phrasing `"has lost 3 straight"`. Direction is
preserved (loss), count is preserved (3), franchise is named
(alias `"Miller"` resolves correctly via owner-first-word). What's
missing is the verb-bearing minimum span the helpers emit
(`"has lost 3 straight"`). This is a textbook PARAPHRASE — exactly
the failure mode the §6 instruction targets.

Note: id=129 also appears in Probe 1 since it's the most recent
W13 2024 row tied to an APPROVED artifact. Cross-probe deduplication
is not applied; each scope's findings are independent.

---

## Probe 3 — W13 2025 (all states)

13 STREAK claims, all the same T3 angle for "Brandon Knows Ball"
across multiple regens (`pa.id` 24, 25, 26, 56, 97, 112, 113, 114,
122, 123, 125, 126, 127). W13 2025 has Brandon on a 13-game losing
streak — the heaviest STREAK angle currently in the league and the
load-bearing test case for the streak thread.

### Aggregate

| Category   | Count | %      |
|------------|------:|-------:|
| VERBATIM   |     0 |   0.0% |
| PARAPHRASE |    13 | 100.0% |
| INVERTED   |     0 |   0.0% |
| OMITTED    |     0 |   0.0% |

### Per-template

| Template               |  n |  V |  P |  I |  O |
|------------------------|---:|---:|---:|---:|---:|
| T3 (long-form losing)  | 13 |  0 | 13 |  0 |  0 |

### Reading

Same finding shape as Probe 2 at higher volume: 0 verbatim, 0
inverted, 13 paraphrases, all preserving direction and count.
Brandon's 13-game streak is mentioned in every draft, with the
alias `"Brandon"` (owner first-word) resolving consistently.
Variant verbs the model uses include
`"extended Brandon's streak to 13 straight"`,
`"Brandon's losing streak now sits at 13 games"`,
`"Brandon's 13-game losing streak reaching historic territory"`,
`"remains winless at 0-13"`. The canonical T3 form
`"Brandon Knows Ball on 13-game losing streak"` never appears.

### T9-LOSS fabrication (audit memo §10 Q1 evidence)

5 of the 13 W13 2025 rows contain a fabricated T9-LOSS-shaped
claim — the model inventing the asymmetric record-approach form
that the helpers deliberately don't emit:

| pa.id | Fabricated phrasing                                                              |
|------:|----------------------------------------------------------------------------------|
| 122   | "closing in on the all-time league record of 15 games"                           |
| 123   | "still three short of the all-time record of 15 games set across 2024-2025"      |
| 125   | "longest active losing streak across the last 16 seasons of data"                |
| 126   | "one shy of the league record he set last season"                                |
| 127   | "one short of the league record he set last season"                              |

This is a direct §10 Q1 data point. The audit memo deferred Q1
(asymmetric record-approach on the losing side) as an out-of-scope
coverage gap, but the model is filling that gap on its own —
sometimes plausibly accurate (if Brandon set a 13- or 14-game
record last season), sometimes apparently fabricated (the "15 games
set across 2024-2025" claim and the "16 seasons of data"
specificity warrant ground-truth verification against
`LeagueHistoryContextV1.longest_loss_streak`).

The numbers are also inconsistent across attempts:

- ids 122, 123: claim is "15 games"
- ids 126, 127: claim is "one [short/shy] of the league record he
  set last season" — implying record is 14 (since Brandon is at 13)
- id 125: claim is "longest active losing streak across the last
  16 seasons of data" — phrasing is consistent with truth but the
  "16 seasons" specificity depends on actual league-history depth

Reviewer attention is required on each draft to verify the
league-record claim against canonical data. This is exactly the
burden the audit memo §1 lesson identifies as "not a sustainable
integrity mechanism" — and exactly the burden a verifier rule
would relieve.

**Recommendation:** Open a separate four-step thread for §10 Q1
(T9-LOSS form). The model is signaling demand by fabricating; the
helpers should emit the form so the prompt + verifier can constrain
it. Out of scope for the present Step 3.2-3.3 thread, but the data
justifies promoting Q1 from "deferred curiosity" to a named
follow-up thread after Step 3.3 lands.

---

## Manual audit of INVERTED hits

Zero INVERTED hits in this corpus. No manual audit required.

This is itself a finding worth surfacing: the original four-step
playbook for streaks targeted "verb inversion" as the load-bearing
failure mode (audit memo §1: *"'won 3 in a row' of a losing
streak"*). On the 19-claim baseline corpus measured here, the model
never inverts. Whether this means the inversion failure mode is
RARER than the audit memo posited, or whether it manifests on
weeks/templates not covered by the sampled scopes, is undetermined
from this baseline alone. The post-fix memo's larger corpus (more
weeks regenerated under the new prompt) may surface examples; if
it doesn't, the policy framing for Step 3.3 should de-emphasize
INVERTED severity in favor of PARAPHRASE-density as the load-bearing
metric.

---

## Disposition

The pre-fix data establishes the baseline. Three findings shape
what follows:

1. **Format paraphrase is the dominant failure mode**, not direction
   inversion. 19/19 paraphrases, 0 inversions. The §6 instruction's
   job is to shift PARAPHRASE → VERBATIM, not to fix INVERTED.
2. **Selection bias does not converge STREAK to verbatim.** Approved
   recaps show 0/3 VERBATIM, despite the same publication path that
   drove SCORE to 42/42 VERBATIM (score-thread Probe 1). STREAK
   requires explicit verbatim instruction; iteration alone does
   not produce it.
3. **T9-LOSS fabrication is observable and stable** at 5/13 (38.5%)
   in W13 2025. Concrete §10 Q1 evidence; promotes Q1 from deferred
   to a named follow-up thread.

The post-fix memo (next step in the brief) measures whether the
§6 instruction shifts these baselines. Specific quantities to
capture:

- VERBATIM rate after instruction lands (per-template).
- Whether T9-LOSS fabrication persists or fades. The §6 instruction's
  closing sentence — *"If the angles do not supply a phrasing for
  what you want to say, omit the streak claim — silence is preferred
  over fabrication"* — is the relevant guardrail; its observed
  effect on the T9-LOSS fabrication rate is a direct measurement
  of whether the silence-fallback principle propagates to the
  model's output.
- INVERTED rate (expected to remain near zero; track to confirm).

The Step 3.3 severity policy decision will land in the post-fix
memo, informed by the magnitude of the post-fix shift.

---

## Anti-drift discipline

1. Helper-bound: every canonical-phrase reference in this memo and
   in the harness routes through `streak_strings_v1`. No
   hand-written format expectations.
2. Observational, not authoritative: no INVERTED hit is treated as
   a model bug without manual audit confirmation. Zero hits to
   audit in this baseline.
3. The §6 instruction is the prompt change scope. No additional
   prompt edits in this session.
4. The T9-LOSS fabrication finding is reported but does NOT
   scope-creep Step 3.3. Q1 follow-up is named for visibility and
   tracked separately.
5. Step 3.3 begins only when this memo's successor (post-fix
   observation) is committed AND the policy decision is recorded.

---

## Stop signal

Baseline measurement captured. Numbers transferred from the
v1.2 harness output to this memo. Step 3.2 Commit 2 (prompt
instruction in `creative_layer_v1.py` + this memo) is the next
action in the brief.
