# OBSERVATIONS — §10 Q1 paired thread pre-fix diagnostic

**Date:** 2026-05-05 (evening session)
**HEAD:** `850478c`
**Status:** Diagnostic complete. Bug 2 (T9-LOSS form, RECORD_APPROACH
shape) advances to Step 1 unconditionally per the integrity-tier gate.
Bug 1 (HEADLINE budget eviction, STATUS_CLAIM_OMITTED shape) defers
with a diversity-based follow-on trigger.

## What this session set out to answer

The §10 Q1 paired-thread brief
(`session_brief_section_10_q1_paired_revised_post_review.md`,
committed `cdbca96`) frames a two-tier gate decision: integrity-tier
fabrications ship unconditionally; editorial-tier silence shapes
elect per silence-vs-density preference; both-zero defers Step 3
entirely. The session executes that gate by extending the streak
diagnostic harness with a fabrication-shape classifier and reading
the bucket counts against the established W11/W13 2025 fixture set.

The two questions:

* **Bug 2** — does the model produce T9-LOSS-shaped record-approach
  prose ("matching the league's all-time record", "closing in on the
  record", "longest active losing streak") when no STREAK angle
  anchors it? If so, ship the four-step playbook fix.

* **Bug 1** — when the HEADLINE budget evicts a long-form T3 status
  angle (`|streak| >= 5`), does the model fabricate a status claim
  with a wrong count (EVICTED shape), or does the §6 silence-fallback
  hold and the recap simply omits the streak status mention (OMITTED
  shape)? If EVICTED, integrity-tier ship; if OMITTED only, editorial
  call.

## Measurement instrument

`scripts/step_1_streak_diagnostic_harness.py` (commit `850478c`)
classifies each (prompt_audit row, franchise) pair into one of five
fabrication-shape buckets. The classifier requires per-row
counterfactual angle reconstruction by re-running `_detect_streaks`
against derived canonical context, because
`prompt_audit.angles_summary_json` strips `franchise_ids` and
`headline` fields per `prompt_audit_v1.py:174`.

The harness invocation for this session:

```
scripts/py scripts/step_1_streak_diagnostic_harness.py \
    --db .local_squadvault.sqlite --league-id 70985 \
    --scope week --season 2025 --week-index <11|13>
```

### Three iterative refinements applied during pre-0b validation

The first harness run reported empty buckets at W11 and only 4 hits
at W13, surfacing two regex/gate gaps and one attribution gap that
the brief's prescribed forms had not covered:

1. **`_T9_LOSS_RECORD_APPROACH` regex** — broadened to
   `(?:[a-zA-Z'\-]+\s+){0,3}record` between optional "the" and
   "record". The brief's `(?:league|all-time)?` permits one
   adjective; specimens like "the league's all-time record" and "the
   all-time league record" need two. Verified 6/6 against brief
   specimens after correction.

2. **`STATUS_CLAIM_OMITTED` gate** — inverted from `not found_alias`
   to `found_alias AND not status_match AND not angle_present`. The
   silent-omission shape the brief's Revision rationale points at is
   the case where the model *talks about* the franchise (in a
   matchup-loss or record context) but *omits* the canonical T3
   status claim. The earlier draft would have miscounted W11
   id=140-shape rows as MISS.

3. **RECORD_APPROACH attribution helper** —
   `_is_record_approach_attached_to_alias` mirrors the architectural
   pattern of `_is_inversion_attached_to_alias` (look backward from
   regex match to alias variant) with a 200-char lookback. The
   earlier earliest-alias-window approach
   (`_extract_window(prose, found_alias, before=120, after=200)`)
   missed W11 id=140 because the matching-record phrase appears 267
   chars after the BKB mention but only 31 chars after a closer
   "Brandon's" possessive.

All three refinements are recorded in `850478c`'s diff against
`afec7b6`.

## Bucket counts — fixture set

```
=== W11 2025 — 6 prompt_audit rows × 10 franchises = 60 instances ===
RECORD_APPROACH           :   1
STATUS_CLAIM_EVICTED      :   0
STATUS_CLAIM_OMITTED      :   5
STATUS_CLAIM_NOT_EVICTED  :   0
MISS                      :  54

=== W13 2025 — 15 prompt_audit rows × 10 franchises = 150 instances ===
RECORD_APPROACH           :   7
STATUS_CLAIM_EVICTED      :   0
STATUS_CLAIM_OMITTED      :   0
STATUS_CLAIM_NOT_EVICTED  :   0
MISS                      : 143
```

Per-instance dump (read-only `tool_search`-style probe against the
harness as a module) confirms every non-MISS entry in both weeks
attributes to fid=0010 (Brandon Knows Ball).

## Bug 2 — RECORD_APPROACH (T9-LOSS form fabrication)

### Empirical shape

8 specimens of identical fabrication shape across 2 weeks, all
attributed to BKB. The model produces a record-approach claim when
no STREAK angle in the rendered angles block carries that
phrasing — `_detect_streak_records` does not currently emit a
T9-LOSS form (the helper has only T8 win-broke, T9-WIN
1-from-record, and T10 loss-broke; the symmetric "1 loss from
record" form is documented as deliberately absent in
`streak_strings_v1.py:200, 205, 226`).

The shape is consistent across attempts: the model reasons across
STANDINGS data (BKB's `current_streak`) and LEAGUE_HISTORY data
(`longest_loss_streak.length` after temporal scoping), draws the
"close to record" inference, and writes the inference into the prose
without an angle anchor.

### Specimens — W11 2025

| Row | Attempt | Fabrication snippet |
| --: | :-----: | :--- |
| 140 | 1 | "extended Brandon's streak to 11 straight defeats, **matching the league's all-time record for futility**" |

### Specimens — W13 2025

| Row | Attempt | Fabrication snippet |
| --: | :-----: | :--- |
| 112 | 1 | "Brandon's nightmare season rolled on — now 0-13 and **riding a streak that matches the all-time league record of 15 straight losses**" |
| 114 | 3 | "13th straight loss — a streak that now spans two seasons and **sits just two games shy of the all-time league record of 15**" |
| 122 | 1 | "extended Brandon's streak to 13 straight, **closing in on the all-time league record of 15 games**" |
| 123 | 2 | "stretched Brandon's streak to 13 straight — **still three short of the all-time record of 15 games set across 2024-2025**" |
| 125 | 1 | "Brandon's 13-game losing streak reaching historic territory. That's now the **longest active losing streak across the last 16 seasons of data**" |
| 126 | 2 | "stretched Brandon's streak to 13 straight — **one shy of the league record he set last season**" |
| 127 | 3 | "Brandon's losing streak now sits at 13 games — **one short of the league record he set last season**" |

Note: the brief enumerated 5 W13 specimens (122/123/125/126/127); the
harness surfaces 7 by detecting the same fabrication shape on rows
112 and 114, both of which had been overlooked in the brief's
specimen survey. The brief's count was a manual-survey
under-enumeration, not a harness false positive — the
classifier confirms identical attribution mechanics across all 7.

### Decision

**Bug 2 advances to Step 1 unconditionally.** Constitutional
integrity violation: facts are derived from canonical inputs but a
fact-creating inference (the record-approach claim) is appearing in
narrative prose without an angle anchor. The four-step playbook
applies straightforwardly:

1. Extend `format_streak_record` to emit a T9-LOSS form for
   `streak <= -3 AND abs(streak) == record_length - 1`.
2. Extend `_detect_streak_records` to invoke the new T9-LOSS form
   and emit a STREAK angle at appropriate strength.
3. Add a verifier rule in `recap_verifier_v1.py` that flags
   record-approach prose without a corresponding STREAK angle
   (RECORD_CLAIM_ANCHORING category extension or new STREAK_RECORD_
   APPROACH category — Step 1's Step 4 will decide which).
4. Reverify-as-merge-gate against the W11/W13 fixture set: confirm
   all 8 specimens either become VERBATIM (canonical phrasing
   accepted into prose) or get caught by the verifier (rejection
   loop forces revision).

A symmetric T10-LOSS tied/broke form (`streak == -record_length`)
is **not** in scope for Step 1 — none of the 8 specimens are
tied/broke shape (W11 BKB at -11, W13 BKB at -13, both
`streak == record - 1`). If evidence for the tied/broke shape
surfaces in future weeks, it gets its own thread; the asymmetric-
by-design note at `streak_strings_v1.py:30` stands as the current
documented intent, and Step 1 narrows it to "asymmetric on the
tied/broke axis only" rather than removing the asymmetry wholesale.

The `_would_t9_loss_fire` predicate at
`scripts/step_1_streak_diagnostic_harness.py:450` ships with an
explicit "remove me after Step 1" comment; once Step 1 lands, the
harness reverts to invoking `_detect_streak_records` directly.

## Bug 1 — STATUS_CLAIM_OMITTED (HEADLINE budget eviction silence)

### Empirical shape

5 specimens of silent-omission shape, all W11, all attributed to
BKB. The model is named in the prose (matchup recap, 0-11 record
mention), but the canonical T3 long-form status claim ("Brandon
Knows Ball on 11-game losing streak") is not made. STATUS_CLAIM_
EVICTED (fabrication with disagreeing count) is **zero across the
entire fixture set** — the §6 silence-fallback is doing its job on
the integrity dimension.

The W11 `Total claims: 0` per-claim aggregate confirms the upstream
mechanism: the HEADLINE budget evicted **every** T3 status angle
across all 6 W11 attempts. With no canonical T3 in the angles
block, the model has no anchor — and per §6 it correctly produces
silence rather than fabrication.

### Specimens — W11 2025

| Row | Attempt | Franchise | Evidence |
| --: | :-----: | :-------- | :------- |
| 20  | 1 | BKB | `\|streak\|=11` mentioned but no canonical claim |
| 21  | 2 | BKB | `\|streak\|=11` mentioned but no canonical claim |
| 22  | 3 | BKB | `\|streak\|=11` mentioned but no canonical claim |
| 54  | 1 | BKB | `\|streak\|=11` mentioned but no canonical claim |
| 55  | 2 | BKB | `\|streak\|=11` mentioned but no canonical claim |

### Decision: defer with diversity-based follow-on trigger

This is an editorial-tier gap, not an integrity violation. Two
arguments weigh against each other:

* **Density restoration** (for shipping) — a recap that does not
  mention the league's worst team's 11-game losing streak is
  information-light on a story PFL Buddies readers care about. The
  HEADLINE budget eviction is producing observable recap-quality
  loss, not just structural neutrality.

* **Silence-over-speculation** (for deferring) — silence is
  constitutionally preferred. The §6 silence-fallback is functioning
  as designed. The current evidence is concentrated on a single
  franchise across a single week (BKB-W11); generalizing from a
  single specimen risks designing a fix that solves a BKB-specific
  symptom rather than a league-wide pattern.

**Decision: defer.** The constitutional argument is the stronger
one under the brief's own framing — silence-over-speculation is a
non-negotiable principle, density restoration is a quality-of-life
concern. The Bug 1 fix (HEADLINE budget revision; eviction priority
adjustment for high-`|streak|` T3) belongs to a thread that has
broader empirical evidence than 5 BKB-W11 attempts.

### Diversity-based follow-on trigger

The standing-backlog item that picks Bug 1 back up activates when
the harness reports STATUS_CLAIM_OMITTED for **≥2 distinct
franchises across ≥2 distinct weeks**. The harness's
STATUS_CLAIM_OMITTED bucket is the standing measurement instrument;
no new tooling is needed for the follow-on, only re-running against
new approved weeks as the 2025 season completes.

Why diversity rather than volume: more BKB-W11-shape rows
accumulating doesn't change the editorial calculus — they reinforce
the same single-franchise specimen. Diversity across franchises and
weeks is the signal that the silence pattern is league-wide and the
density argument materially strengthens.

## Gate verdict summary

| Bug | Bucket | Tier | Disposition |
| :-- | :----- | :--- | :---------- |
| Bug 2 | RECORD_APPROACH = 8 (W11: 1, W13: 7) | Integrity | **Ship Step 1 unconditionally** |
| Bug 1 | STATUS_CLAIM_EVICTED = 0; OMITTED = 5 (W11 only, BKB only) | Editorial | **Defer with diversity follow-on trigger** |
| — | STATUS_CLAIM_NOT_EVICTED = 0 | Distribution context | Not surfaced |

## Implications for the rest of the §10 Q1 thread

* Step 1 (Bug 2 fix) ships per the four-step playbook. Re-runs of
  this harness against W11 and W13 after Step 1 should report
  RECORD_APPROACH = 0 across the fixture set (all 8 specimens
  either canonical-phrased into prose or caught by the verifier).
* The RECORD_APPROACH bucket itself stays in the harness post-Step-1
  as a regression sentinel against the same fabrication shape
  re-emerging in future weeks.
* STATUS_CLAIM_OMITTED bucket stays in the harness as the standing
  measurement instrument for the diversity trigger.
* The harness's three pre-0b refinements (regex, gate, attribution)
  are scoped to the §10 Q1 fabrication-shape classifier; they have
  no effect on the per-claim VERBATIM/PARAPHRASE/INVERTED/OMITTED
  pipeline that supports the streak verb-inversion thread.

## Files and commits referenced

* `850478c` — diagnostic harness with fabrication-shape classifier
  (this session's three pre-0b refinements applied)
* `afec7b6` — parent commit; player-streak verb inversion
  diagnostic brief (queued post-§10 Q1)
* `cdbca96` — §10 Q1 paired-thread brief (post-review revision)
* `bd680e3`, `10e12a8`, `8082040` — LEAGUE_HISTORY temporal
  scoping (Phase 1 and Phase 2; required for `as_of_season` /
  `as_of_week` parameters used by this harness's counterfactual
  reconstruction)
* `src/squadvault/core/recaps/render/streak_strings_v1.py:200, 205, 226`
  — T9-LOSS form documented as deliberately absent
* `src/squadvault/core/recaps/context/narrative_angles_v1.py:539`
  — `_detect_streak_records` (T8/T9-WIN/T10 detector to be extended
  in Step 1)
* `src/squadvault/core/recaps/context/narrative_angles_v1.py:142, 185, 203`
  — `_detect_streaks` (T1/T3 long-form gate at strength=3 used by
  the STATUS_CLAIM family classification)
