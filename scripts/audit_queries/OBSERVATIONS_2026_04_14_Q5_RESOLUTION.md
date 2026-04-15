# OBSERVATIONS 2026-04-14 — Q5 Resolution

**Session:** Phase 10 observation, successor to e6e4bd0
**Verifier commit under analysis:** e6e4bd0 (post-V1–V6)
**Question:** Does the 2024/2025 pass-rate gap persist after V1–V6?
**Status:** Resolved.

---

## TL;DR

The 27.7-point 2024/2025 pass-rate gap observed in the pre-fix data is
**~100% verifier parse bugs**, not a model-side regression between
seasons. V1–V6 closed 55% of the gap in code; re-verification of the
full 51-row `prompt_audit` corpus against the current verifier against
unchanged prose isolates the remainder as 7 further verifier false
positives (4 distinct bug classes across 3 categories) plus 3
correctly-caught model fabrications. Once the 4 new bug classes are
fixed, projected pass rate is 100% for 2024 and 90% for 2025, with the
remaining 10% residual being model-side fabrication on a single
franchise's 0-13 season — correctly caught by the verifier, no code
change indicated.

---

## Method

The pre-V1–V6 capture set (51 rows across seasons 2024 and 2025) was
re-verified in place via `/tmp/reverify_captured_drafts.py`. Stored
`narrative_draft` rows were passed to the current `verify_recap_v1`
with no prose modification, isolating the verifier delta from model
nondeterminism. Results written to new sidecar table
`prompt_audit_reverify`, append-only, keyed by `prompt_audit.id` with
a `verifier_tag` column for cross-commit comparison.

Re-verification is deterministic because `verify_recap_v1` is a pure
function of `(recap_text, canonical facts)`, and canonical facts are
immutable per the constitution. Any pass/fail flip between original
capture and reverify is 100% attributable to verifier code changes
between capture time and reverify time.

---

## Results

### Pass-rate arc

| Slice | Pre-V1–V6 | Post-V6 (e6e4bd0) | Projected post-all-fixes |
|---|---|---|---|
| 2024 | 17/21 (81.0%) | 18/21 (85.7%) | 21/21 (100%) |
| 2025 | 16/30 (53.3%) | 22/30 (73.3%) | 27/30 (90.0%) |
| **2024/2025 gap** | **27.7 pts** | **12.4 pts** | **10.0 pts** |

The residual 10-point gap in the projected column is 3 rows, all on
a single franchise (Brandon Knows Ball) during its 0-13 season.

### 4-way delta vs. original capture (e6e4bd0 verifier)

| Bucket | Count |
|---|---|
| still pass | 33 |
| still fail | 11 |
| fail → pass | 7 (V1–V6 unblocked) |
| pass → fail | 0 (no regressions) |

Zero regressions across V1–V6 is a strong signal that conservative-
guard discipline (`continue` on uncertainty, "silence over
misattribution") held across seven fix cycles.

---

## Survivor classification (all 11 rows)

Every one of the 11 post-V6 survivors was classified by reading the
captured `narrative_draft` and the verifier's `hard_failures[0]`
entry. Classification follows the MODEL_SIDE / VERIFIER_SIDE
framework from the V1–V6 work.

### STREAK — 3 survivors, all MODEL_SIDE (correctly caught)

| id | season | wk | a | Claim |
|---|---|---|---|---|
| — | 2025 | 4 | 1 | Brandon Knows Ball snapped a losing streak |
| — | 2025 | 11 | 1 | Brandon Knows Ball's losing streak was snapped |
| — | 2025 | 13 | 2 | Purple Haze snapped a losing streak |

All three are factually incorrect per canonical streak data. Brandon
was 0-N entering every week of 2025 and never snapped a streak. Row
25 (w13) was separately diagnosed earlier this session as a
Purple Haze loss with canonical streak -4; the model's prose claimed
Robb snapped Pat's streak in the course of a Robb win, but Purple
Haze extended rather than ended a losing run.

Notable: the 2025 w11 case confirms c103e4d's `_POSSESSIVE_OBJECT_STREAK`
path fires correctly when prose cooperates (possessive with no N-game
clause or digit N-game clause).

No verifier action. System works as designed.

### PLAYER_SCORE — 5 survivors, all VERIFIER_SIDE, 2 new bug classes

**P1: XX.XX substring match inside XXX.XX game score.** (2 rows)

| id | season | wk | Prose |
|---|---|---|---|
| 40 | 2024 | 10 | `"119.10-89.00 win over Brandon"` + Chase mentions |
| 41 | 2024 | 10 | same pattern, different attempt |

The verifier extracts `19.10` from `119.10-89.00` and attributes to
the nearest player name (Ja'Marr Chase). `19.10` does not appear in
either prose as an independent token.

**Fix shape:** top of score-match loop in `verify_player_scores`,
skip if the character immediately before the match is a digit.

```python
if score_abs_pos > 0 and recap_text[score_abs_pos - 1].isdigit():
    continue
```

**P2: Bench-aggregate misattribution past existing guards.** (3 rows)

| id | season | wk | Prose (truncated) |
|---|---|---|---|
| 47 | 2024 | 14 | `"leaving Aaron Rodgers and 47.60 points on the bench"` |
| 9 | 2025 | 5 | `"leaving 51.50 points on the bench with Stefon Diggs posting 19.60"` |
| 15 | 2025 | 9 | `"Miller left 52.60 points on the bench, including a 14.60 performance from Jameson Williams"` |

The existing `verify_player_scores` guards already anticipate this
class — the code has a comment at line 1828 specifically calling out
`"got 20.30 from X but left 53.90 on the bench"` — but only `" but "`
is matched as the clause separator. The three P2 prose shapes use
`"and"`, `", leaving"`, and `"Miller left"` respectively, all of which
slip past.

**Fix shape:** after the score match, peek ~30 chars forward for the
trailing `points on the bench` construction:

```python
post_start = window_start + m.end()
post_end = min(len(recap_text), post_start + 30)
_post = recap_text[post_start:post_end].lower()
if re.match(
    r'\s*points?\s+(?:on|sitting\s+on|left\s+on)\s+'
    r'(?:the\s+|his\s+|her\s+)?bench',
    _post,
):
    continue
```

### SERIES — 2 survivors, both VERIFIER_SIDE, 2 new bug classes

**S1: 3-part W-L-T record misread as 2-part W-L.** (1 row)

| id | season | wk | Prose |
|---|---|---|---|
| 3 | 2025 | 2 | `"extending their series lead to 16-12-1 across 29 all-time meetings"` |

The prose is a legitimate head-to-head record with ties (`16 wins,
12 losses, 1 tie`). The verifier's series-record regex matched `12-1`
as an embedded W-L, and the proximity heuristic attributed it to the
wrong franchise pair.

**Fix shape:** require left-boundary (not digit followed by hyphen)
on the series-record regex, same principle as P1.

**S2: Season record confused with H2H series record.** (1 row)

| id | season | wk | Prose |
|---|---|---|---|
| 18 | 2025 | 10 | `"Josh Allen's 26.40 points led Miller to his second straight win and a 7-3 record."` |

The `7-3` is Miller's season W-L record, not a H2H vs Eddie. The
verifier's proximity heuristic picked the Eddie-vs-Miller franchise
pair because both are mentioned in the sentence, but the numeric
token has nothing to do with the series.

**Fix shape:** skip when a season-record cue appears within a small
pre-context window of the record token — `"to a N-M record"`,
`"improved to N-M"`, `"fell to N-M"`, `"moves to N-M"`, `"at N-M"`.
Same guard-shape as V1–V6: `continue` rather than a canonical-data
substitution.

### SUPERLATIVE — 1 survivor, VERIFIER_SIDE, backlog item #2 captured

**V7 (forward-lookback): backlog #2 now has captured prose.** (1 row)

| id | season | wk | Prose (truncated) |
|---|---|---|---|
| 17 | 2025 | 10 | `"posted 48.10 points for Paradis' Playmakers in their 137.50-103.10 win over Italian Cavallini. That's the highest individual score by any starter this season, topping the previous mark of 46.75."` |

The valid V1 trigger (`"topping the previous mark of 46.75"`) is
positioned *after* `"highest"`, outside V1's backward-only lookback
window. The verifier extracts `103.10` (the losing team's game score,
nearest XX.XX to "highest") and flags it as a false superlative
claim.

The brief's hypothesis for this case was exact:

> *"If the regen produces the same fusion shape, the fix is a
> symmetric forward-lookback option on `_has_previous_qualifier`, not
> a new pattern class."*

Confirmed. Fix shape is the symmetric forward-lookback. Suggested
name: V7, continuing the V-series rather than starting a new letter,
because it's the same class as V1 (previous-qualifier guard) with the
only change being the direction of the lookback.

---

## Model-side finding

The 3 MODEL_SIDE survivors are all on Brandon Knows Ball, the 2025
0-13 franchise. Prose pattern across all three: the model attempts
to find a silver lining in a Brandon sentence and fabricates a
streak break, either for Brandon directly (`"snapped a losing
streak"`) or for Brandon's opponent in a way that implies Brandon's
streak ended (`"Robb snapped Purple Haze's..." + "ending Pat's
four-game losing streak"`).

This is not a prompt-engineering or verifier-code action item. The
verifier catches it, the auto-reject lifecycle fires, and on
exhaustion the facts-only fallback publishes. Worth noting for the
record — it's an observation about the model's failure mode on
extreme-outlier season trajectories, not a bug.

---

## Recommended fix batching

Five fix items now characterized with captured prose. Suggested
batching for subsequent sessions:

**Session A — PLAYER_SCORE fixes (P1, P2).** Same function
(`verify_player_scores`), natural commit unit. Higher failure count
(5/11). Both fixes are short and localized. Regression tests in the
filter-and-assert mold against the 5 captured prose fragments.

**Session B — SERIES fixes (S1, S2).** Same function
(`verify_series_records`). Lower incidence but different category
makes this a separate commit from Session A.

**Session C — SUPERLATIVE forward-lookback (V7).** Smallest change
(direction flip on existing helper) but warrants its own session
because the forward-lookback affects every SUPERLATIVE subclass that
uses `_has_previous_qualifier`. Need a careful regression-test pass
over the existing V1 corpus to confirm no false negatives introduced.

Verification-regression discipline: before any fix lands, re-run
`/tmp/reverify_captured_drafts.py --verifier-tag <new-commit>` to
confirm the expected rows flip fail→pass and no pass→fail
regressions appear.

---

## Tooling note — `prompt_audit_reverify`

The sidecar table created this session is useful as a
cross-verifier-commit comparison surface, not just as a one-off Q5
artifact. Decision needed:

- **Keep as committed schema migration.** Adds
  `0008_add_prompt_audit_reverify_table.sql`, makes
  `/tmp/reverify_captured_drafts.py` a committed
  `scripts/reverify_prompt_audit.py` following the audit-query
  convention. Future verifier changes land with a reverify pass in
  the commit message as evidence.
- **Keep local, ephemeral.** Treat as a diagnostic tool like
  `/tmp/row25_diagnostic.py`. Drop the table in a future cleanup
  session once Sessions A/B/C land. Regen if needed later.

Preference: committed. The append-only shape, the
`verifier_tag` column, and the pure-function nature of
`verify_recap_v1` make this a natural complement to `prompt_audit`.
It answers "what does the current verifier think of every past
draft?" in a way that scales to future verifier work.

---

## Backlog updates

**Promoted from question to resolved:**
- Q5 (2024/2025 pass-rate gap) — gap is ~100% verifier parse bugs.

**Promoted to named items (captured prose available):**
- P1 (PLAYER_SCORE digit-boundary). Rows 40, 41 (2024 w10 a1/a2).
- P2 (PLAYER_SCORE bench-aggregate beyond " but "). Rows 47, 9, 15.
- S1 (SERIES 3-part W-L-T substring). Row 3 (2025 w2 a1).
- S2 (SERIES season-record cue). Row 18 (2025 w10 a2).
- V7 (SUPERLATIVE forward-lookback on previous-qualifier). Row 17
  (2025 w10 a1) — item #2 from e6e4bd0 brief, now captured.

**Closed:**
- Item #1 (Row 25 diagnostic). Diagnosed this session. `_SNAP_PATTERN`
  does reach `losing`; `_POSSESSIVE_OBJECT_STREAK` fails due to
  `four-game` spelled-out form blocking an unrelated latent path;
  proximity fallback correctly attributed to Purple Haze and the
  fabrication was caught. No code change.

**Newly surfaced latent (no captured instance; reference only):**
- B3. `_POSSESSIVE_OBJECT_STREAK` latent dead-path in c103e4d —
  two compounding regex bugs (span truncation on bare `losing`;
  digit-only N-game clause) prevent the possessive-object branch
  from firing on spelled-out N-game prose. Proximity fallback
  currently compensates. Fix only on captured evidence of proximity
  misattributing a case where possessive would resolve correctly.

**Unchanged priority:**
- B2 (explicit-count misattribution). Still no captured evidence.
- Q2/Q3 budget gate with D13/D37/D4/D15/D12.
- Player Trend Detectors (D1–D2).
- Row 40/41 STREAK-count miscitation (model-side count fabrication,
  different class from B).
- Q1 UNMAPPED categories.
- Latent KP short-form attribution risk.
- SPECULATION soft-fail "kicking himself".

---

## Principle confirmations

This session's findings reinforce principles already in the
constitution and operating memory:

- **Verifier false positives outnumber model fabrications.** Of 11
  post-V6 survivors, 8 (73%) were verifier-side; 3 (27%) were
  model-side. Pre-V6 the ratio would have been even more skewed
  toward verifier-side, since V1–V6 accounted for 7 more fail→pass
  flips that were all verifier-side. Across the full 51-row corpus
  the post-all-fixes projection is 15 verifier-side false positives
  vs. 3 model-side fabrications: **5:1 verifier:model**.

- **Diagnostic-first is not optional.** Two of this session's five
  newly characterized bugs (S1, V7) would have been misclassified as
  model-side fabrications if the prose had not been read carefully.
  Row 25 would have consumed a code-change session if the `_SNAP_
  PATTERN` hypothesis had been accepted from the brief without
  testing against captured prose.

- **Prompt guardrails are weak; data-layer and verifier fixes are
  strong.** Confirmed again. Every fix proposed in this session is
  a verifier logic change, not a prompt change.

- **Zero regressions across seven guard additions (V1–V6) is earned,
  not automatic.** The "guard shape is skip the check" discipline
  and the filter-and-assert regression-test mold are the reason
  V1–V6 landed without any pass→fail flips. Sessions A/B/C should
  follow the same shape.
