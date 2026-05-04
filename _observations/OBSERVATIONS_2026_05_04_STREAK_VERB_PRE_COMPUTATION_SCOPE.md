# OBSERVATIONS — Step 3 Streak Verb Pre-Computation Scope

**Drafted:** 2026-05-04 UTC.
**HEAD:** `1db5cbd` on `main`.
**Phase:** 10 — Operational Observation.
**Position in plan:** Step 3 of the four-step playbook proven by the
score-string thread (`8082040` / `ff613a9` / `46c2ca5` / `be76817` /
`2fe75b2` plus the V8 follow-up at `c1b1eb0` / `f0fb9ba` / `1db5cbd`).
This memo scopes the audit work that precedes Step 3.1
(implementation), 3.2 (prompt + diagnostic), and 3.3 (verifier).
Doc-only — no source or test changes.

---

## TL;DR

- **Streak verb inversion fits the four-step playbook cleanly.** The
  data is right (post-game standings, post-game outcome lookup); the
  instrumentation around it is loose (no centralized format helper,
  no verbatim-copy prompt instruction, no verbatim-presence verifier
  check). Identical maturity gap to the score-string format pre-fix.
- **Pre-rendering is partial, not absent.** `_outcome_detail` already
  emits verb-explicit phrasing ("Beat OPP — streak continues" /
  "Lost to OPP — streak extended, not snapped"), and `_streak_str`
  already emits the standings-table marker. Step 3.1 consolidates
  rather than introduces.
- **17 in-scope call sites across 4 modules**, 3 out-of-scope player
  emitters across 1 module. Helper module proposed at 5 functions.
  Inventory in §3.
- **Coverage gaps surfaced by the taxonomy work** (§4) — most
  notably `_outcome_detail` does NOT emit "won-from-losing snap" or
  "lost-from-winning snap" phrasing, and `_detect_streak_records` is
  asymmetric (no "K losses from loss-streak record" form). These
  are coverage gaps in the data layer, NOT verbatim-format gaps,
  and so are out of scope for this thread; surfaced in §10.
- **Three follow-up briefs sequenced.** Step 3.1 implementation, 3.2
  prompt + diagnostic, 3.3 verifier. Preconditions per brief.

---

## 1. Why now

The score-string thread shipped a four-step pattern that's now
proven against one production failure mode:

1. **Pre-render** the high-risk element at the data layer with a
   single-source-of-truth helper (`format_matchup_score_str`).
2. **Refactor call sites** to consume the helper.
3. **Instruct verbatim copy** in the creative-layer prompt
   (`creative_layer_v1.py:307-314`).
4. **Verify verbatim presence** in the verifier
   (`verify_score_strings_verbatim` at `recap_verifier_v1.py:1036`).

The V8 follow-up (`c1b1eb0` / `f0fb9ba` / `1db5cbd`) added the
fifth lesson: instrumentation must track its own data-layer
contracts — the verifier reads expected formats THROUGH the helper,
never duplicates them.

Streak verbs are the next user-memory backlog item that matches this
shape. The model-side failure pattern is documented: "model writes
'won 3 in a row' of a losing streak (or 'snapped' of an extended
streak, or 'extended' of a snapped one)." The architectural cause
matches scores: data correct, paraphrase loose, no verbatim contract.
This memo is the scoping audit that produces the inputs Steps
3.1–3.3 need.

---

## 2. Why this is its own session (not folded into Step 3.1)

The score-string Step 2 brief did its format-design work inline
because there was one canonical format. Streaks have ~10 distinct
claim categories across 5 emitter functions in 4 modules. Three
factors made an inline approach risky:

1. **Cardinality.** ~10 templates vs 1; design choices need to
   stabilize before the implementation refactor starts.
2. **Coverage gaps surface during enumeration.** The
   "won-from-losing snap" gap (§10) was not visible from the user
   memory description — only an exhaustive walk of `_outcome_detail`
   plus the threshold guards in `_detect_streaks` reveals it.
   Better to surface in a memo than to grow scope mid-implementation.
3. **D49's relationship to the streak helpers is non-obvious.**
   `SCORING_MOMENTUM_IN_STREAK` headlines embed "{N}-game win
   streak" as a sub-phrase rather than as the whole headline. A
   sub-phrase helper is the right abstraction; designing it inline
   would either bury the choice or risk drift.

Surfacing these in this memo before code starts mirrors the
diagnostic-first discipline that produced `8082040` before
`ff613a9` for scores.

---

## 3. Call-site inventory

Verified at HEAD `1db5cbd`. **In scope** = emits streak prose into
the prompt path (NARRATIVE ANGLES block via `narrative_angles_text`
or LEAGUE HISTORY / standings blocks via `season_context_v1`
renderers). **Out of scope** = present but doesn't emit streak
claim prose, or is player-level (separate thread per brief).

### 3.1 In scope (17 call sites, 4 modules)

| # | File | Line | Function / context | Output shape | Inputs | Consumer |
|---|------|------|---|---|---|---|
| 1 | `season_context_v1.py` | 616–622 | `_streak_str(s)` definition | Compact marker `W3` / `L2` / `-` | `current_streak: int` | Standings rows |
| 2 | `season_context_v1.py` | 651 | Standings row formatter | `Streak: {marker}` substituted into `"  {i}. {name} ({record}, PF: {pf}, Streak: {streak})"` | `_streak_str(rec.current_streak)` | Season-context block in prompt |
| 3 | `narrative_angles_v1.py` | 165 | `_outcome_detail` continuation | `"Record: {rec_str}. Beat {opp_name} this week — streak continues."` | rec_str, opp_name, won=True | NARRATIVE ANGLES detail |
| 4 | `narrative_angles_v1.py` | 166 | `_outcome_detail` extension | `"Record: {rec_str}. Lost to {opp_name} this week — streak extended, not snapped."` | rec_str, opp_name, won=False | NARRATIVE ANGLES detail |
| 5 | `narrative_angles_v1.py` | 175 | `_detect_streaks` long-form winning | `"{name} on {N}-game win streak"` (N≥4) | name, streak | NARRATIVE ANGLES headline |
| 6 | `narrative_angles_v1.py` | 183 | `_detect_streaks` short-form winning | `"{name} has won 3 straight"` | name | NARRATIVE ANGLES headline |
| 7 | `narrative_angles_v1.py` | 191 | `_detect_streaks` long-form losing | `"{name} on {N}-game losing streak"` (N≥4) | name, abs(streak) | NARRATIVE ANGLES headline |
| 8 | `narrative_angles_v1.py` | 199 | `_detect_streaks` short-form losing | `"{name} has lost 3 straight"` | name | NARRATIVE ANGLES headline |
| 9 | `narrative_angles_v1.py` | 557 | `_detect_streak_records` tied/broke win | `"{name} tied/broke the league win streak record ({N} games)"` | name, streak | NARRATIVE ANGLES headline |
| 10 | `narrative_angles_v1.py` | 558 | `_detect_streak_records` tied/broke win detail | `"Previous record: {R} by {holder}."` | record, holder name | NARRATIVE ANGLES detail |
| 11 | `narrative_angles_v1.py` | 565 | `_detect_streak_records` approaching win | `"{name} is 1 win from the league win streak record ({R})"` | name, record | NARRATIVE ANGLES headline |
| 12 | `narrative_angles_v1.py` | 576 | `_detect_streak_records` tied/broke loss | `"{name} tied/broke the league loss streak record ({N} games)"` | name, abs(streak) | NARRATIVE ANGLES headline |
| 13 | `narrative_angles_v1.py` | 577 | `_detect_streak_records` tied/broke loss detail | `"Previous record: {R} by {holder}."` | record, holder name | NARRATIVE ANGLES detail |
| 14 | `franchise_deep_angles_v1.py` | 873–874 | D49 strict growing | `"{name}'s {N}-game win streak has growing margins: {csv}"` | name, n_games, margin_str | NARRATIVE ANGLES headline |
| 15 | `franchise_deep_angles_v1.py` | 887–888 | D49 strict shrinking | `"{name}'s {N}-game win streak has shrinking margins: {csv}"` | name, n_games, margin_str | NARRATIVE ANGLES headline |
| 16 | `franchise_deep_angles_v1.py` | 898–899 | D49 mostly growing | `"{name}'s {N}-game win streak has mostly growing margins: {csv}"` | name, n_games, margin_str | NARRATIVE ANGLES headline |
| 17 | `franchise_deep_angles_v1.py` | 909–910 | D49 mostly shrinking | `"{name}'s {N}-game win streak has mostly shrinking margins: {csv}"` | name, n_games, margin_str | NARRATIVE ANGLES headline |
| 18 | `league_history_v1.py` | 811 | Longest win streak record (renderer) | `"  Longest win streak: {name} — {N} games ({span})"` | name, length, span | LEAGUE HISTORY block in prompt |
| 19 | `league_history_v1.py` | 816 | Longest loss streak record (renderer) | `"  Longest loss streak: {name} — {N} games ({span})"` | name, length, span | LEAGUE HISTORY block in prompt |

(Rows 1 + 2 count as one call site for refactor purposes — definition
+ single consumer. Same for the other definition/consumer pairs.
The table lists each line that emits prose; the helper-API count in
§5 collapses these to function granularity.)

### 3.2 Out of scope — player-level streaks (3 call sites, 1 module)

Per the session brief: "Player streaks (e.g., consecutive starts,
consecutive 25+ point weeks) are a separate thread if they exist."
They exist; they are not addressed by this audit.

| # | File | Line | Function | Output shape | Reason out of scope |
|---|------|------|----------|--------------|---------------------|
| P1 | `player_narrative_angles_v1.py` | 752–755 | `detect_player_hot_streak` | `"{player} has scored {threshold:.0f}+ points in {N} consecutive weeks for {franchise}"` | Player-level — different sense of "streak" (consecutive scoring weeks, not team W-L). |
| P2 | `player_narrative_angles_v1.py` | 804–807 | `detect_player_cold_streak` | `"{player} has scored under {threshold:.0f} points in {N} straight starts for {franchise}"` | Same — player consecutive-week scoring. |
| P3 | `player_narrative_angles_v1.py` | 1330–1333 | `detect_player_franchise_tenure` | `"... for {N} consecutive seasons"` | Player tenure (consecutive seasons on one franchise), not team W-L streak. |

If post-Step-3.3 measurement shows player-streak verb inversions in
the wild, those become a separate four-step thread; they would
follow the same pattern but with `player_streak_strings_v1` as the
helper module.

### 3.3 Pending-audit modules — confirmed NOT prose emitters

| File | Verdict | Rationale |
|------|---------|-----------|
| `recap_verifier_v1.py` | Verifier code, not emitter. | `_STREAK_PATTERN` (line 1380), `_POSSESSIVE_OBJECT_STREAK` (line 1405), `verify_streaks` (line 1567) — these are the regex-matchers that read prose, not generators. Step 3.3 ADDS to this file. |
| `voice_profile_v1.py` | Voice rule mention, not emitter. | Single match at line 140, prose meta-instruction inside the voice-profile string ("Reference history when it matters (rivalry records, losing streaks, past performances)"). Not in the streak-claim render path. |

---

## 4. Format taxonomy

Ten distinct streak claim categories are emitted into prose. Each
category fixes its template, the dataclass that supplies values,
and the verbatim-required window (the substring the verifier will
require to be present if the angle fires AND the model surfaces it).

### Status forms (4 templates)

**T1 — Long-form winning** (call site 5).
- Template: `"{name} on {N}-game win streak"`.
- Fires when: `current_streak >= 4`.
- Source: `SeasonRecord.current_streak` plus `fname(franchise_id)`.
- Verbatim window: full template post-name-resolution (model may
  insert verbiage around it but the named substring must be intact).

**T2 — Short-form winning** (call site 6).
- Template: `"{name} has won 3 straight"`.
- Fires when: `current_streak == 3`.
- Source: `SeasonRecord.current_streak == 3`, name resolved.
- Verbatim window: full template.

**T3 — Long-form losing** (call site 7).
- Template: `"{name} on {N}-game losing streak"`.
- Fires when: `current_streak <= -4`.
- Source: `abs(current_streak)`, name resolved.
- Verbatim window: full template. Note phrase is "losing streak"
  not "loss streak" — asymmetric with `_streak_str` marker `L{N}`
  but consistent with English usage.

**T4 — Short-form losing** (call site 8).
- Template: `"{name} has lost 3 straight"`.
- Fires when: `current_streak == -3`.
- Source: same as T3.
- Verbatim window: full template.

### Outcome forms (2 templates)

**T5 — Continuation outcome** (call site 3).
- Template: `"Record: {W}-{L}. Beat {opp_name} this week — streak continues."`
- Fires when: any T1/T2 angle fires AND `won_this_week=True`.
- Source: `_outcome_detail` reads `week_outcome[fid] = (True, opp_id)`.
- Verbatim window: minimum span is `"Beat {opp_name} this week — streak continues."` — the verb-bearing clause. The "Record: W-L." prefix is informational and may be paraphrased.

**T6 — Extension outcome** (call site 4).
- Template: `"Record: {W}-{L}. Lost to {opp_name} this week — streak extended, not snapped."`
- Fires when: any T3/T4 angle fires AND `won_this_week=False`.
- Verbatim window: minimum span is `"Lost to {opp_name} this week — streak extended, not snapped."`. The "not snapped" tail is the load-bearing fragment — its presence is what prevents the model from writing "snapped" and the inversion bug.

### Standings marker (1 template)

**T7 — Compact marker** (call sites 1, 2).
- Template: `"W{N}"` / `"L{N}"` / `"-"`.
- Fires for every team in `season_context_v1` standings rendering.
- Verbatim window: appears inside a structured row; not a prose
  claim. Verifier should NOT require this verbatim — it's
  presentational, not a model-generated claim. Marker stays in the
  helper module for parity but does not appear in the verifier
  pipeline.

### Record forms (3 templates)

**T8 — Tied/broke record (winning)** (call site 9 + detail 10).
- Template: `"{name} tied/broke the league win streak record ({N} games)"` plus detail `"Previous record: {R} by {holder}."`
- Fires when: `current_streak >= longest_win_streak.length`.
- Verbatim window: headline. The "tied/broke" wording IS the load-bearing fragment.

**T9 — Approaching record (winning)** (call site 11).
- Template: `"{name} is 1 win from the league win streak record ({R})"`.
- Fires when: `current_streak == longest_win_streak.length - 1`.
- Verbatim window: full headline.

**T10 — Tied/broke record (losing)** (call site 12 + detail 13).
- Template: `"{name} tied/broke the league loss streak record ({N} games)"` plus detail `"Previous record: {R} by {holder}."`
- Fires when: `abs(current_streak) >= longest_loss_streak.length`.
- Verbatim window: headline. **Asymmetry with T8/T9:** there is no
  "{name} is 1 loss from the league loss streak record (R)" form.
  See §10 Open Question 1.

### D49 streak-margin compositions (4 templates) — composed phrase

D49 templates (call sites 14–17) embed the substring `"{N}-game win
streak"` inside larger headline forms:

- `"{name}'s {N}-game win streak has growing margins: {csv}"`
- `"{name}'s {N}-game win streak has shrinking margins: {csv}"`
- `"{name}'s {N}-game win streak has mostly growing margins: {csv}"`
- `"{name}'s {N}-game win streak has mostly shrinking margins: {csv}"`

The "{N}-game win streak" substring is canonical streak phrasing
and should come from the helper module. The remainder
("has growing margins: ...") is D49-specific and remains in
`franchise_deep_angles_v1.py`. This argues for a low-level phrase
helper (§5).

### Renderer forms (2 templates)

**T11 — League-history longest win streak** (call site 18).
- Template: `"  Longest win streak: {name} — {N} games ({span})"`.
- Fires for every league-history rendering when `longest_win_streak`
  is non-null.
- Verbatim window: this is a structured renderer line in the LEAGUE
  HISTORY block, not a NARRATIVE ANGLE. Same treatment as T7 —
  helper-module hosted, NOT verifier-required-verbatim. The model
  is told the longest streak, but expressing it back in prose is
  legitimate paraphrase territory.

**T12 — League-history longest loss streak** (call site 19).
- Template: `"  Longest loss streak: {name} — {N} games ({span})"`.
- Same treatment as T11.

### Taxonomy summary

12 templates total. Categorization for verifier scope:

- **Verbatim-required if surfaced** (8): T1, T2, T3, T4, T5 (clause), T6 (clause), T8, T9, T10. (Verifier asserts: if the model talks about the streak at all, the canonical phrasing must appear.)
- **Helper-hosted but not verifier-required** (4): T7, T11, T12, plus the D49 sub-phrase. (Format consolidated, but model paraphrase is legitimate; no compliance bar.)

---

## 5. Proposed API — `streak_strings_v1`

Module location: `src/squadvault/core/recaps/render/streak_strings_v1.py`
(parallel to `score_strings_v1.py`).

Constraints carried over from `score_strings_v1`:

- No I/O, no canonical fact creation, no side effects.
- Single source of truth — every in-scope call site in §3.1 calls
  this module after Step 3.1 lands.
- Output is `str` (or `str | None` where the angle does not fire).
  No structured returns.
- Out-of-scope consumers (`creative_layer_rivalry_v1`, `chronicle/`)
  are explicitly named in the module docstring.

### Proposed signatures

```python
def format_streak_phrase(streak: int) -> str | None:
    """Canonical noun phrase. Covers the sub-span shared by T1, T3, and D49.
    Returns "{N}-game win streak" / "{N}-game losing streak" for |streak| >= 2,
    None otherwise.
    """

def format_streak_status(franchise_name: str, streak: int) -> str | None:
    """Canonical STREAK headline. Covers T1, T2, T3, T4.
    Returns full headline for |streak| >= 3, None for |streak| < 3.
    Threshold matches _detect_streaks (lines 172/180/188/196).
    """

def format_streak_outcome(
    franchise_name: str,
    record_str: str,
    won_this_week: bool,
    opponent_name: str,
) -> str:
    """Canonical outcome detail. Covers T5, T6.
    SNAP cases (won-from-losing, lost-from-winning) NOT covered here —
    those angles don't fire today. See §10 Q2.
    """

def format_streak_record(
    franchise_name: str,
    streak: int,
    record_length: int,
    record_holder_name: str,
) -> tuple[str, str] | None:
    """Canonical (headline, detail) for record claims. Covers T8, T9, T10.
    No T9-loss form (asymmetric — see §10 Q1).
    Tuple return keeps tied/broke branch and matching detail adjacent.
    """

def format_streak_marker(streak: int) -> str:
    """Compact standings marker. Covers T7. "W{N}" / "L{N}" / "-".
    Helper-hosted but NOT verifier-required — structured cell, not a claim.
    """
```

### Anti-fragility property

After Step 3.1, every consumer in §3.1 calls one of these helpers.
Step 3.3's verifier reads the same canonical strings by calling
the same helpers — never by hand-writing the format in the verifier.
This is the V8 lesson applied: a single declaration of "what the
phrase looks like" tracked by both the emitter and the validator.

If `format_streak_phrase` ever changes its template (e.g.,
"N-game W streak" if the league wanted shorter prose), Step 3.1's
refactor and Step 3.3's verifier both pick up the change without
edits to either consumer file.

---

## 6. Proposed prompt addition

The score-format instruction lives in `creative_layer_v1.py:307-314`
adjacent to the FACTS block. Streaks are emitted via the NARRATIVE
ANGLES block at `creative_layer_v1.py:269-280`, so the parallel
location is immediately after the existing
`narrative_angles.strip()` append at line 279.

### Existing instruction (score, lines 307–314, reproduced for parallelism):

```python
parts.append(
    "Matchup scores in the facts block appear in this exact format: "
    "'<winner_score> to <loser_score>' (e.g., '107.65 to 65.40'). "
    "When stating a matchup score, copy this format verbatim. Do not "
    "round, abbreviate, or substitute the separator. You may describe "
    "margins separately in plain language (e.g., 'an 11-point win') "
    "alongside the verbatim score string."
)
```

### Proposed addition (streak, to insert after line 279):

```python
parts.append(
    "Streak claims in the angles above use these exact phrasings: "
    "'<name> on <N>-game win streak', '<name> on <N>-game losing streak', "
    "'<name> has won 3 straight', '<name> has lost 3 straight', "
    "'Beat <opp> this week — streak continues', and "
    "'Lost to <opp> this week — streak extended, not snapped'. "
    "When mentioning a streak, copy the relevant phrasing verbatim. "
    "Do not paraphrase the verb (won/lost/snapped/extended/continues), "
    "do not invert the direction, and do not substitute "
    "'snapped' for 'extended' or vice versa. If the angles do not "
    "supply a phrasing for what you want to say, omit the streak "
    "claim — silence is preferred over fabrication."
)
```

### Side-by-side rationale

- **Same shape as the score instruction.** Names the format,
  instructs verbatim copy, calls out the specific failure modes
  (paraphrase, substitution, inversion), invokes the standard
  silence-over-fabrication fallback.
- **Targets the verb, not just the count.** The score-format bug
  was hyphen-vs-decimal — a separator. The streak bug is verb
  inversion — `won/lost`, `snapped/extended`. The instruction
  enumerates the verbs explicitly because that is the load-bearing
  vocabulary.
- **Names the templates inline.** Score-format had one template;
  streak has five active templates plus two outcome clauses. Listing
  them in the prompt anchors the model to canonical phrasing
  without forcing it through the angle-detail string verbatim.
- **Silence fallback.** The score instruction ends with "alongside
  the verbatim score string" because score is always present; the
  streak instruction ends with the silence fallback because streak
  angles don't always fire and partial coverage is the dominant
  case.
- **Step 3.2's job is to validate this draft.** Run the diagnostic
  with this addition in place; measure VERBATIM compliance per
  category; choose policy (HARD vs SOFT) based on observed rate
  the same way `46c2ca5` chose Policy A for scores.

---

## 7. Proposed verifier — `verify_streak_verbs_verbatim`

Parallel to `verify_score_strings_verbatim` at
`recap_verifier_v1.py:1036`. Wired as Category 3b in `verify_recap_v1`,
between Category 3 (existing `verify_streaks`) and Category 4
(`verify_series_records`).

### Design

```python
def verify_streak_verbs_verbatim(
    recap_text: str,
    standings: list[_StandingsFact],   # streak per franchise
    week_outcomes: dict[str, tuple[bool, str]],  # franchise_id -> (won, opp_id)
    history: _HistoryFact | None,      # for record-claim variants
    reverse_name_map: dict[str, str],
    week: int,
) -> list[VerificationFailure]:
    """Verify that streak claims appear in prose using canonical phrasings.

    Pass condition: for each franchise whose post-game current_streak
    fires a STREAK angle (|streak| >= 3) AND whose name appears in
    recap_text, the canonical phrasing produced by
    streak_strings_v1.format_streak_status / format_streak_outcome /
    format_streak_record must appear as a substring of recap_text.
    Negative case: if the franchise is not mentioned in recap_text,
    no claim is required (silence is permitted).

    Severity: TBD by Step 3.2 diagnostic. This brief proposes HARD
    with a SOFT fallback — re-evaluated by post-fix observation.

    Failure category: STREAK_VERBATIM, distinct from STREAK. The
    existing STREAK category catches value-of-claim errors (wrong
    streak length, wrong direction); STREAK_VERBATIM catches
    format-of-claim errors (paraphrased verb, inverted direction
    even when the count was right). This separation parallels
    SCORE / SCORE_VERBATIM and provides triage clarity.

    Defensive return: if standings is empty or no franchise has
    |streak| >= 3, return [] without iterating.
    """
```

### Decisions captured

- **Verbatim-required if surfaced.** T1–T4 status headlines, T5/T6
  outcome clauses (verb-bearing minimum span), T8/T9/T10 record
  headlines — when the franchise is mentioned in prose. T7, T11,
  T12, and the D49 composed headline NOT required. See §4.
- **Mention-required gate.** Unlike `SCORE_VERBATIM` (every matchup
  unconditionally), `STREAK_VERBATIM` only fires when the franchise
  is named in prose. Streak claims are angle-driven; matchup
  coverage is not. Mirrors the existing `verify_streaks` gating
  shape (line 1567 onwards).
- **Severity proposal: HARD with SOFT fallback** — same as
  `SCORE_VERBATIM`, but contingent on Step 3.2's diagnostic showing
  ≥95% post-prompt compliance. Below that threshold: SOFT, or split
  HARD/SOFT per template. Final policy lands in 3.2.
- **Failure category: STREAK_VERBATIM**, distinct from STREAK
  (value vs format separation, parallel to SCORE / SCORE_VERBATIM).
- **Anti-fragility: helper-bound.** Verifier expected substrings
  come from `format_streak_status`, `format_streak_outcome`,
  `format_streak_record` — never hand-written. The V8 follow-up
  (`OBSERVATIONS_2026_05_03_V8_REGRESSION_COVERAGE_GAP.md`) showed
  hand-written format expectations leak silent regressions; same
  lesson applied here.

### Pipeline insertion

In `verify_recap_v1` immediately after Category 3 (`verify_streaks`,
line 3185):

```python
# Category 3b: Streak-phrasing verbatim verification
checks_run += 1
all_failures.extend(verify_streak_verbs_verbatim(
    narrative,
    standings=...,        # from _compute_streaks pattern
    week_outcomes=...,    # derived from season_matchups for this week
    history=...,          # for record claims
    reverse_name_map=reverse_name_map,
    week=week,
))
```

Step 3.3 finalizes data-loading helpers; this brief sketches shape only.

---

## 8. Follow-up sequence

Three briefs follow this memo. Each has explicit preconditions; no
brief begins until its predecessor lands.

### Step 3.1 — Implementation

**Scope:** Create
`src/squadvault/core/recaps/render/streak_strings_v1.py` with the
five helpers in §5. Refactor the 17 in-scope call sites in §3.1 to
consume them. Behavioral parity required: every existing test passes
with no rendered-prose changes (the canonical strings produced by
the helpers must be byte-identical to what the call sites produce
today).

**Out of scope for 3.1:** No prompt change. No verifier change. No
new angles. No threshold changes.

**Precondition:** This memo committed.
**Success gate:** All existing tests pass; ruff clean; mypy clean
on `src/squadvault/core/`; no diff in any approved-recap rendered
prose under regen.

### Step 3.2 — Prompt + diagnostic

**Scope:** Add the prompt instruction draft from §6 to
`creative_layer_v1.py`. Run a pre-policy-decision diagnostic
mirroring the score-thread Step 1 harness
(`step_1_score_diagnostic_harness.py` → adapt to streak categories).
Classify each claim in approved/draft prose into VERBATIM /
PARAPHRASE / INVERTED / OMITTED. Output: post-fix observation memo +
policy selection (HARD vs SOFT, per-template if needed).

**Out of scope for 3.2:** No verifier change.

**Precondition:** Step 3.1 landed.
**Success gate:** Diagnostic memo committed at `_observations/`;
policy decision recorded.

### Step 3.3 — Verifier

**Scope:** Add `verify_streak_verbs_verbatim` per §7 with the
severity policy chosen in 3.2. Wire as Category 3b in
`verify_recap_v1`. Add tests covering all 10 in-scope templates
plus their negative-mention cases.

**Out of scope for 3.3:** No new prompt change.

**Precondition:** Step 3.2 memo committed AND policy selected.
**Success gate:** Test count rises by the number of new tests; ruff
and mypy clean; no pass→fail regressions on approved-recap reverify.

---

## 9. Risks and friction

- **Taxonomy drift between this memo and Step 3.1.** Mitigation:
  Step 3.1's session brief MUST cite this memo's §4 as the
  taxonomy authority and treat any deviation as a re-scope event.
- **Coverage gaps tempt scope expansion.** The "won-from-losing
  snap" gap (§10 Q2) and the asymmetric-record-approach gap (§10 Q1)
  are real but out of scope for the verbatim-format thread. If
  Steve decides to address them, they land as a separate detector
  thread BEFORE Step 3.1, not folded into it.
- **D49 helper integration.** Refactoring D49 to consume
  `format_streak_phrase` is the only call-site refactor with a
  composition shape (sub-phrase inside a larger headline). Risk:
  string-concatenation style matters here. Mitigation: Step 3.1
  lands the D49 refactor in the same commit as the rest, with
  before/after rendered-prose diff for inspection.
- **Player-streak follow-up.** If post-Step-3.3 measurement shows
  player-streak verb inversions, a separate four-step thread
  follows. Out of scope here; surfaced for visibility.
- **Verifier input plumbing.** `verify_streak_verbs_verbatim` needs
  more inputs than `verify_score_strings_verbatim` (standings,
  week-outcomes, history). Step 3.3 may need to extract a
  data-loading helper to keep `verify_recap_v1` readable.

---

## 10. Open questions

These are unresolved scope decisions that warrant Steve's review
BEFORE Step 3.1 starts.

### Q1 — Asymmetric record-approach form

`_detect_streak_records` emits "is 1 win from the league win streak
record" (T9) but has no parallel "is 1 loss from the league loss
streak record" form. Possible reasons:

- Intentional governance: emphasizing approach to a loss record
  may feel mean-spirited and the editorial bar is higher.
- Oversight: parallelism wasn't enforced when the detector was
  written.

Decision needed: does T9-loss exist as a follow-up coverage gap,
or is the asymmetry deliberate? If deliberate, the helper docstring
should record the rationale; if oversight, add a coverage gap to
the backlog.

**Default if no decision:** preserve current behavior. Helper omits
T9-loss.

### Q2 — Snap outcomes not currently emitted

`_outcome_detail` covers two of the four streak-end quadrants:

| Pre-week streak | Won this week | Current emit | Missing emit |
|---|---|---|---|
| Winning (>=3) | Yes | T5 ("streak continues") | — |
| Winning (>=3) | No | none (no angle fires post-week, current_streak <= 0) | "{name} snapped a {N}-game winning streak — lost to {opp}" |
| Losing (<=-3) | Yes | none (no angle fires post-week, current_streak >= 0) | "{name} snapped their {N}-game losing streak — beat {opp}" |
| Losing (<=-3) | No | T6 ("streak extended, not snapped") | — |

The two missing emits ("snap" outcomes) currently produce no angle
because `_detect_streaks` thresholds on the POST-WEEK `current_streak`,
which is in [-2, 2] when a streak just ended. The model is left
without a canonical claim for "X snapped Y's streak this week" and
must derive it — the exact pattern that produces verb inversions.

Decision needed: does Step 3.1 stay tightly scoped to verbatim
formatting (deferring snap-outcome detection), or does the snap
gap rate as a precondition coverage fix?

**Default if no decision:** stay tightly scoped. Snap-outcome
detection is a coverage thread, not a format thread, and folding
it in would expand Step 3.1 from a refactor to a behavior change.

### Q3 — D49's verifier treatment

D49 (SCORING_MOMENTUM_IN_STREAK) embeds "{N}-game win streak" as a
sub-phrase. Per the userMemories surfacing audit, D49 produces zero
shareable prose across 35 approved recaps — the model isn't using
it. So the verifier question is moot in practice today.

If Writing Room surfacing improves and D49 starts firing in prose,
should `verify_streak_verbs_verbatim` require the canonical
sub-phrase verbatim? Or is D49's whole headline ("{name}'s {N}-game
win streak has growing margins: {csv}") legitimate paraphrase
territory because it's a composed claim?

**Default if no decision:** D49 NOT verifier-required-verbatim in
3.3. The sub-phrase still gets centralized through the helper for
format-locality (anti-fragility), but the verifier doesn't enforce
its presence. Revisit if D49 surfacing improves materially.

---

*End of memo.*
