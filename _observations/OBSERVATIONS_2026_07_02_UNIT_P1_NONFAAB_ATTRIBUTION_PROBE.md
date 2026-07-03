# Observation - 2026-07-02 - Unit P1: Non-FAAB Attribution Probe (SUPERLATIVE / SCORE_VERBATIM / STREAK)

**Session type:** EXECUTE (Claude Code, Opus 4.8). Diagnosis-only, read-only. Pre-registered
per brief `_observations/session_brief_unit_p1_nonfaab_attribution_probe.md` (ratified
2026-07-02, deferral amendment). One founder gate (Gate 1: memo approval).

**Status:** COMPLETE - PENDING GATE 1 APPROVAL. Closing = stopping-rule outcome **(b) Prose
capture needed** (section 6). No source edits; zero generation API calls; prod read-only and
unchanged.

---

## 0. Ritual / provenance (verified this session)

- **HEAD:** `f514277` (`git rev-parse HEAD`). Repo identity: engine confirmed
  (`scripts/recap_artifact_regenerate.py` present).
- **Standard trio (green, session start AND end - no source touched):** ruff
  `check src/squadvault/` **All checks passed**; mypy **Success: no issues found in 160
  source files**; pytest **2397 passed, 2 skipped** (the 2 warnings are the known empty-key
  test fixture, unrelated).
- **Production DB:** `.local_squadvault.sqlite` sha256
  `effb00e54fce5c3860423a08338b8711bc96229172452888c97823bc8c5af36b`, recorded at start,
  re-checked after the read-only probe (section 3) - **unchanged**. Opened `mode=ro` for the
  probe; zero writes anywhere.
- **Frozen inputs:** A7 memo (`1948de4`), Stage A/B memos, F1/F2 memos, RM1 memo (`8007dff`)
  read as history, never amended. The RM1 scratch was deleted after its squash - **rejected
  attempt-1 prose does not exist**; findings work only from committed memos, code at HEAD,
  and prod read-only. Where the truth is "indeterminate without prose," it is said.

---

## 1. Code findings - the three checks at HEAD `f514277`

File: `src/squadvault/core/recaps/verification/recap_verifier_v1.py` unless noted.

### 1.1 SCORE_VERBATIM - `verify_score_strings_verbatim` (line 1050)

- **Mechanism.** For each canonical matchup with `m.week == week`, requires the canonical
  score string to appear in prose. Primary: exact substring of `format_matchup_score_str`
  output, both orderings (1103-1108). Relaxed: both 2-decimal scores within a 200-char
  proximity window (1098, 1134), **rejecting the hyphen-joined form** `X.XX-Y.YY` (1121-1125)
  because the canonical separator is " to ". Emits `SCORE_VERBATIM` HARD on miss (1139-1140).
- **Canonical source / tolerance.** `format_matchup_score_str` = `f"{winner_score:.2f} to
  {loser_score:.2f}"` (`src/squadvault/core/recaps/render/score_strings_v1.py:36,62`); the
  verifier imports the same formatter (`recap_verifier_v1.py:40`). Scores come from
  `_load_season_matchups` -> `v_canonical_best_events` WEEKLY_MATCHUP_RESULT (line 87, SQL
  96-101). Tolerance: exact 2-decimal string (or proximity), Policy A **HARD** (docstring
  1057-1082).
- **Structural over-strictness (true-statement shape it rejects).** Policy A demands **every**
  in-week matchup's exact score string be present. A recap that is true but *selective* -
  omitting a boring matchup's score, which the league voice profile explicitly invites
  ("skip matchups that weren't notable"; "Say less when less happened" - A7 memo Appendix A)
  - HARD-fails. This is rejection of an acceptable (true, incomplete) recap, but by **policy
  choice** (Policy A completeness), not a parse/source mismatch. Tier-2/policy is out of scope
  (section 7 of the brief); recorded, not scoped.

### 1.2 SUPERLATIVE - `verify_superlatives` (line 1157)

- **Mechanism.** Three regex loops - season-high (`_SEASON_HIGH_PATTERN`), season-low,
  all-time (`_ALLTIME_PATTERN`). Each match: extract a nearby score via
  `_extract_nearby_score` (1206/1265/1336), compare to the actual computed value, tolerance
  **abs(delta) <= 0.01** (1216/1220/1269/1346/1350). Team high/low = `max`/`min` of
  `season_matchups` team scores (1173-1174); player high passed in. Emits `SUPERLATIVE` HARD
  (1234/1271/1364).
- **Canonical source / scope.** Team scores from the same view (WEEKLY_MATCHUP_RESULT).
  Season scope is **week-filtered**: the entrypoint passes `season_matchups_through_week`
  (weeks <= recap week, 5007-5012) - the "future weeks" false-positive is already guarded.
  Player highs: `_load_player_season_high(through_week=week)` and `_load_alltime_player_high`,
  both **starters only** (`is_starter=1`, SQL 291-306 / 320-324), loaded only when the
  matching pattern is present (5001-5005 / 4995-4999).
- **Guards V1-V7 (1183-1334).** previous-qualifier, ordinal ("second-highest"),
  possessive-scope, all-time-series context, auction-investment context, integer-object
  ("record of 15" = games), frequency-marker ("Nth time in league history"). The breadth of
  these guards is itself evidence that the `_extract_nearby_score` regex-proximity extractor
  has a **history of grabbing the wrong adjacent number** (each guard patches one such class).
- **Residual verifier-side surface.** `_extract_nearby_score` can still pull an unrelated
  adjacent XX.XX from a non-superlative clause and compare it to the true high -> a false
  positive on a true statement. Whether this fired in RM1 is not determinable from committed
  data (section 5).

### 1.3 STREAK - `verify_streaks` (line 1620) + `_compute_streaks` (1514)

- **Mechanism.** `_compute_streaks(season_matchups, through_week)` builds each franchise's
  consecutive win/loss run through the week (1525 filters `m.week > through_week`); computes
  `actual_streaks` (through week) and `pre_week_streaks` (through week-1) (1629-1630). Two
  loops: explicit-count claims (`_STREAK_PATTERN`, 1633) and "snapped" claims
  (`_SNAP_PATTERN`, 1702). Tolerance: claimed count must equal **current OR pre-week** count
  (1675/1689); else `STREAK` HARD (1677/1691/1758/1768/1790/1800).
- **Canonical source.** Same view (WEEKLY_MATCHUP_RESULT), through-week correct.
- **Attribution layer = the FAAB-binder sibling.** Which franchise a streak claim belongs to
  is resolved by `_resolve_streak_count_attribution` (1552) / `_find_nearby_franchise`
  (window=150, 1616/1778) / `_POSSESSIVE_OBJECT_STREAK`. The docstrings (1552-1600, 1732-1741)
  document prior misattribution where proximity picked a decoy franchise over the true streak
  owner - structurally the same shape as the FAAB per-player binder that Stage B identified.
  Guards (possessive-object, idiomatic-snap, historical-reference) mitigate; a residual
  misattribution surface remains.
- **Residual verifier-side surface.** A true streak statement whose owner the attribution
  layer resolves to the wrong franchise -> compared against that franchise's streak -> false
  positive. Whether this fired in RM1 is not determinable from committed data (section 5).

---

## 2. Assembly-side findings - what the prompt hands the model

Entry: `src/squadvault/ai/creative_layer_v1.py`, `_build_user_prompt`. **All three facts are
GIVEN to the model (pre-computed and injected), none volunteered:**

- **SCORES - GIVEN, verbatim.** Pre-rendered `"X.XX to Y.YY"` via `format_matchup_score_str`
  into the VERIFIED FACTS bullets (`deterministic_bullets_v1.py:301`) and the season-context
  week block (`season_context_v1.py:655`). Prompt instruction (`creative_layer_v1.py:352-359`,
  verified verbatim): *"When stating a matchup score, copy this format verbatim. Do not round,
  abbreviate, or substitute the separator. You may describe margins separately in plain
  language ... alongside the verbatim score string."*
- **SUPERLATIVES - GIVEN and gated.** Actual season-high/low numbers injected
  (`season_context_v1.py:682-691`) and record-setting weeks carry the number in a narrative
  angle (`narrative_angles_v1.py:348,357`); player highs likewise
  (`player_narrative_angles_v1.py`, starter-filtered - see 3.2). The model is explicitly
  gated (`creative_layer_v1.py:329-334`, verified verbatim): *"SUPERLATIVE WARNING: NONE of
  these scores are season highs, all-time records ... UNLESS a NARRATIVE ANGLE above
  explicitly says so. Do NOT infer records from these numbers - your inference will be wrong."*
- **STREAKS - GIVEN, verbatim.** Per-franchise streak phrasings via `format_streak_status`
  (`streak_strings_v1.py:107-110`) as angles (`narrative_angles_v1.py:142,177`) and standings
  (`season_context_v1.py:644,647`). Prompt (`creative_layer_v1.py:307-318`, verified
  verbatim): *"copy the relevant phrasing verbatim. Do not paraphrase the verb ... do not
  invert the direction ... If the angles do not supply a phrasing ... omit the streak claim -
  silence is preferred over fabrication."*

---

## 3. Source-alignment (Stage-A-style structural test) + prod probe

### 3.1 Shared canonical spine - CONFIRMED

The verifier's loaders and the creative-layer assembly read the **same** canonical source:
`v_canonical_best_events` (a VIEW over `canonical_events` JOIN `memory_events`,
`schema.sql:85-105`). Verifier: `_load_season_matchups` (98), `_load_all_matchups` (154),
player-high loaders (293/302/321). Assembly: `season_context_v1.py:243`,
`league_history_v1.py:248` (the verifier's `_load_all_matchups` docstring, 141-142, calls
itself "the verifier's private analog to `league_history_v1.load_all_matchups`"),
`narrative_angles_v1.py`, `player_narrative_angles_v1.py`. There is **no separate scoring
table**; both sides draw from one spine.

### 3.2 The one flagged suspect - player-high `is_starter` - RESOLVED aligned

The verifier's player highs filter `is_starter=1`. The assembly's player-high angles filter
the **same**: `detect_player_season_high` restricts to `r.is_starter`
(`player_narrative_angles_v1.py:831`) and `detect_player_alltime_high` to `r.is_starter`
(`:1076`), same view, same through-week. So the model is given the identical starter-only
high the verifier checks - **no source misalignment on player-high.**

### 3.3 Prod probe (read-only, `mode=ro`; SQL + verbatim result)

Cell 2024 wk9 (an RM1 SUPERLATIVE final-trigger cell), league 70985:

```sql
-- [1] object type of the shared source
SELECT type FROM sqlite_master WHERE name='v_canonical_best_events';           -- view
-- [2] verifier team season-high THROUGH wk9 (WEEKLY_MATCHUP_RESULT, same view assembly uses)
SELECT MAX(MAX(winner_score, loser_score)) ... week <= 9;                      -- 173.05
-- [3] verifier player season-high THROUGH wk9 (WEEKLY_PLAYER_SCORE, is_starter=1)
SELECT MAX(score) ... is_starter=1 AND week <= 9;                              -- 47.7
-- [4] is_starter filter is meaningful
SELECT SUM(is_starter=1), COUNT(*) ... 2024 WEEKLY_PLAYER_SCORE;               -- 1382 / 2263
```

Result: the values the SUPERLATIVE check compares against (team 173.05, starter player 47.7
through wk9) are computed from the **same view** the assembly injects from; the `is_starter`
filter is non-trivial (1382 of 2263) and is applied identically on both sides. **Source
alignment holds empirically.** Prod hash unchanged after the probe (`effb00e5...`).

### 3.4 Consequence for attribution

Because source-alignment holds for all three categories (shared spine; scores pre-rendered
verbatim; superlatives given + gated; streaks pre-phrased; player-high starter-aligned), the
**FAAB-style structural source-misalignment fault is ruled out** for SUPERLATIVE,
SCORE_VERBATIM, and STREAK. FAAB failed because the verifier's per-player binder rejected true
claims the assembly surfaced (Stage B); no equivalent source/scope mismatch exists here. What
remains are (i) model non-compliance with the verbatim/gate instructions, and (ii) two
residual verifier-side over-rejection surfaces (`_extract_nearby_score` misparse; streak
attribution misfire) whose firing cannot be confirmed without the rejected prose.

---

## 4. Variance sub-readout (pre-registered; committed data only, no significance claims)

### 4.1 Mechanism is byte-identical A7 -> RM1 (keystone)

`git diff 89d9321 8e300ac` on the verifier touches **only** `_load_faab_bids` /
`verify_faab_claims` (hunks at 4478-4693); `verify_superlatives`, `verify_score_strings_
verbatim`, `verify_streaks`, `_compute_streaks` are **unchanged**. The only verifier-touching
commit in range is F1 (`6778101`). Therefore every A7->RM1 movement in these three categories
is **cell-mix + model stochasticity, not a mechanism change** (brief hazard 4).

### 4.2 First-attempt occurrences (R1, aggregate - unconfounded by short-circuiting)

Quoted from committed A7 memo section 3.1 and RM1 memo section 3.1:

| category | A7 | RM1 | delta |
|---|---:|---:|---:|
| SUPERLATIVE | 10 | 15 | +5 |
| SCORE_VERBATIM | 12 | 14 | +2 |
| STREAK | 15 | 12 | -3 |
| DRAFT_AUCTION_DOLLAR | 3 | 0 | -3 |

**Per-cell distribution of these first-attempt occurrences is INDETERMINATE** - it lived in
the RM1 scratch `prompt_audit` (per-attempt rows), deleted after the squash. Only the
aggregate survives in the committed memo.

### 4.3 Final-trigger concentration (per-cell, from committed R2 ledgers)

The surviving per-cell records are the R2 final-outcome ledgers. Cells whose **final**
facts-only trigger included each category:

| category | A7 cells (n) | RM1 cells (n) |
|---|---|---|
| SUPERLATIVE | 2020 wk5 (1) | 2013 wk5, 2013 wk12, 2017 wk12, 2024 wk4, 2024 wk9 (5) |
| SCORE_VERBATIM | 2014 wk5 (1) | 2013 wk5, 2013 wk12, 2014 wk5, 2014 wk12, 2024 wk6, 2024 wk7, 2024 wk12 (7) |
| STREAK | 2019 wk12, 2020 wk5 (2) | 2012 wk12, 2017 wk12, 2020 wk5 (3) |

**Confound (must not be read as "more non-FAAB failures").** A7 had 11 FAAB Tier-2
short-circuits that terminated 11 cells early, **masking** any non-FAAB categories as final
triggers there; RM1 had only 4, so 15 cells ran to exhaustion (vs A7's 5), **un-masking**
non-FAAB categories as final triggers. The rise in RM1 final-trigger cells is substantially
the mechanical consequence of fewer FAAB short-circuits, not evidence of more non-FAAB
failing. The unconfounded axis is 4.2 (first-attempt), which always runs the full verifier.

### 4.4 Cell-mix comparison (season spreads, committed memos)

| | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|
| A7 | 2 | 1 | 2 | 2 | 2 | 2 | 2 | 1 | 1 | 2 | 2 | 2 | 2 | 2 | 11 |
| RM1 | 2 | 1 | 2 | 2 | 2 | **0** | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 2 | 12 |

RM1 omits 2015 entirely and carries one more 2024 cell (draw differences at 2015, 2017, 2018,
2021, 2024). With the check code byte-identical (4.1), these mix differences - not mechanism -
are the deterministic explanation available for the category moves (e.g. DRAFT_AUCTION_DOLLAR
3->0: auction-dollar prose is draw-dependent). **No significance claims; counts only.**

---

## 5. Per-category verdicts

- **SCORE_VERBATIM -> model-side plausible, verifier structurally sound.** The check is
  source-aligned and looks for the exact string the model is handed with a verbatim-copy
  instruction (2 / 3.1). No parse or source mismatch. The remaining failure modes are the
  model omitting a matchup's score (the voice profile invites selectivity) or deviating from
  the given string - model-side. The one structural note is a **policy tension** (Policy A
  HARD completeness vs the "skip boring matchups" voice), recorded not scoped (Tier-2/policy
  out of scope). The exact omission-vs-reformat split is not confirmable without prose.
- **SUPERLATIVE -> indeterminate without prose.** Source-aligned and the model is gated by an
  explicit SUPERLATIVE WARNING. A failure is therefore either (i) the model inferring a record
  the gate forbids (model-side) or (ii) `_extract_nearby_score` pulling an unrelated adjacent
  score and comparing it to the true high (verifier-side false positive; the V1-V7 guard
  lineage shows this class is real). Committed data cannot separate (i) from (ii).
- **STREAK -> indeterminate without prose.** Source-aligned and the model is given verbatim
  streak phrasings with an omit-if-absent instruction. A failure is either (i) the model
  paraphrasing/inverting/inventing a count (model-side) or (ii) the attribution layer
  (proximity/possessive, the FAAB-binder sibling) resolving a true claim to the wrong
  franchise (verifier-side false positive). Committed data cannot separate (i) from (ii).

---

## 6. Closing - stopping-rule outcome (b): PROSE CAPTURE NEEDED

The deterministic layer (code + committed data + read-only prod) produced one clean result -
**source-alignment holds for all three categories, ruling out a FAAB-style structural source
fault (no clean outcome (a))** - and one honest limit: for SUPERLATIVE and STREAK it cannot
distinguish model-side non-compliance from two real, cited verifier-side over-rejection
surfaces (`_extract_nearby_score` misparse; streak attribution misfire), because the only
evidence that could - the attempt-1 rejected prose - lived in the RM1 scratch and was deleted
after its squash. Declaring outcome (c) "structurally sound" would overclaim that soundness;
declaring (a) would assert a fault with no captured instance. The disciplined closing is **(b)
Prose capture needed**, auto-deferred past Week 1 unless the founder explicitly reopens.

**Capture list for a Stage-B-style run (if reopened):** re-generate a small pinned set on a
scratch copy capturing each **attempt-1 rejected narrative** verbatim alongside its
`verification_result_json`, then per emitted SUPERLATIVE/STREAK failure classify:
(1) SUPERLATIVE - was the flagged number inside an actual superlative clause (verifier misparse
if not), and did a gating angle exist; (2) STREAK - did the verifier attribute the streak to
the franchise the prose actually named (misattribution if not), and was the phrasing a verbatim
copy of a provided angle. Suggested pinned cells (highest committed non-FAAB signal): the RM1
final-trigger cells 2013 wk5, 2013 wk12, 2017 wk12, 2024 wk4, 2024 wk9 (SUPERLATIVE) and
2012 wk12, 2017 wk12, 2020 wk5 (STREAK) - pre-registered afresh at capture time, not treated
as a measurement.

SCORE_VERBATIM does not require capture to reach a verdict (section 5: model-side, verifier
sound) but its prose would fall out of the same run for free.

**No fix is designed here.** Whether (b) is executed, or the season simply starts at the
RM1-measured facts-only rate (constitutionally safe - silence, not error), is the founder's
DECIDE-lane call under the ratified deferral.

---

## Appendix A - exploratory (NOT pre-registered; recorded so it is not silently dropped)

- The SCORE_VERBATIM policy tension (Policy A HARD completeness vs voice-profile selectivity)
  is the single deterministic structural observation that could, if the founder ever reopens
  Tier-2/policy (explicitly out of scope here), be examined as a demote-to-SOFT or
  notable-matchup-only question. Recorded only; no weight, no fix.
- Final-trigger concentration (4.3) is confounded by FAAB unmasking and should not be cited as
  a category trend; it is included solely because it is the only surviving per-cell record.
