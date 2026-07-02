# Observation - 2026-07-02 - Unit A7 (1.4) Fresh-Generation Failure-Rate Baseline

**Session type:** EXECUTE (Claude Code, Opus 4.8). Pre-registered measurement per
Completion Plan v1.3 Unit A7 / D-B (n=24-36) and brief
`_observations/session_brief_unit_1_4_fresh_generation_baseline.md` (v1.1).
Closure-certification-6 evidence; pre-season control for later in-season voice iteration.

**Status:** PRE-REGISTRATION BLOCK FROZEN at Gate 1 (founder ratified as-is, 2026-07-02).
Results sections populated post-run.

---

## 0. Ritual / provenance (verified this session)

- **HEAD at session start:** `89d9321` (brief authored against `c344c58`; HEAD differs,
  so all pinned config facts were re-verified against source per brief instruction).
- **Repo identity:** engine confirmed (`scripts/recap_artifact_regenerate.py` present).
- **Standard trio (green base):** ruff `check src/squadvault/` clean; mypy clean
  (163 source files); pytest **2380 passed, 2 skipped** (the 2 warnings are an in-test
  empty-API-key fixture in `test_creative_layer_rivalry_v1.py`, unrelated).
- **Production DB:** `.local_squadvault.sqlite`
  sha256 `effb00e54fce5c3860423a08338b8711bc96229172452888c97823bc8c5af36b`
  (recorded before any work; re-checked after the smoke - unchanged).
- **Scratch DB:** `/tmp/unit14_scratch.sqlite`, copied from prod; copy sha256 identical
  to source at copy time (`effb00e5...`). All generation runs against the scratch copy only.

### Config drift resolved (not a stop-and-ask; already founder-adjudicated)

The brief's Amendment Log pins the generation model at `claude-sonnet-4-20250514`. That
pin was retired between brief authoring and this session: a prior EXECUTE session hit the
Step 1 smoke, found that model EOL (HTTP 404 -> silent facts-only degradation), and -
founder-approved - repinned to `claude-sonnet-4-5-20250929` (commit `ff1c760`; memo
`_observations/OBSERVATIONS_2026_07_01_UNIT_1_4_MODEL_PIN_RETIREMENT.md`). That memo
explicitly deferred the baseline to "a fresh session ... against the corrected config."
**This is that session.** The measured model is therefore `claude-sonnet-4-5-20250929`,
re-verified at `creative_layer_v1.py:35` this session. All other pinned facts re-verified
unchanged (retry cap 3; temps [None,0.5,0.3]; no-retry {FAAB_CLAIM, NUMERIC_UNANCHORED};
verifier 14-category enum).

---

## 1. PRE-REGISTRATION BLOCK (FROZEN at Gate 1, founder-ratified as-is 2026-07-02)

### 1.1 Configuration in force (measured as-is; no edits)

| Item | Value (verified this session) |
|---|---|
| HEAD | `89d9321` |
| Scratch-DB source hash | `effb00e54fce5c3860423a08338b8711bc96229172452888c97823bc8c5af36b` |
| Generation model (`_MODEL`, `src/squadvault/ai/creative_layer_v1.py:35`) | `claude-sonnet-4-5-20250929` |
| Temperature (base) | `0.8` (`_TEMPERATURE`); retry decay `[None, 0.5, 0.3]` |
| Retry cap (`_MAX_VERIFICATION_RETRIES`) | `3` |
| No-retry categories (`_NO_RETRY_CATEGORIES`) | `FAAB_CLAIM`, `NUMERIC_UNANCHORED` |
| Verifier | `src/squadvault/core/recaps/verification/recap_verifier_v1.py`, 14-category enum (below) |
| Voice profile (`get_voice_profile(scratch, '70985')`) | PRESENT (commissioner-approved), len 3938, sha256 `3fdd8c9564c6066752d0b8f9129d3a45ce13b4c99859814df0d9ee467d407d8a` (full text in Appendix A) |
| Prompt-audit capture | `SQUADVAULT_PROMPT_AUDIT=1` (R1 data source) |

**Verifier 14-category enum (no filter applied in R1):** SCORE, SUPERLATIVE, STREAK,
SERIES, BANNED_PHRASE, PLAYER_SCORE, PLAYER_FRANCHISE, FAAB_CLAIM, CHAMPIONSHIP_CLAIM,
SEASON_RECORD_CLAIM, PLAYER_AVG_CLAIM, NUMERIC_UNANCHORED, PLAYER_STREAK_CLAIM,
DRAFT_AUCTION_DOLLAR.

### 1.2 Census - eligible universe (read actual SQL; do not assume week ranges)

Single league in DB: `70985`. 64 recap_runs cells total. Eligibility SQL (the golden-path
core - a real weekly recap needs matchup results to recap):

```sql
SELECT season, week_index,
       COALESCE(json_extract(counts_by_type_json,'$.WEEKLY_MATCHUP_RESULT'),0) AS matchups
FROM recap_runs
WHERE league_id = '70985'
ORDER BY season, week_index;
```

Candidate eligibility criteria and resulting counts (actual results):

| Criterion | Count | Note |
|---|---|---|
| render-non-empty (weakest) | 64 | passes even for 0-event weeks; rejected as too weak |
| WEEKLY_MATCHUP_RESULT >= 1 | 49 | includes partial/playoff slates |
| **WEEKLY_MATCHUP_RESULT == 5 (full slate) [RECOMMENDED]** | **42** | complete week for this 10-team league; unambiguous "complete" |
| full slate minus smoke cell (2024 wk8) | **41** | **draw universe** |

Data-state facts surfaced (why the criterion matters): 2024 wk18 has 0 matchups; wk15-17
taper (4/2/1). **All of 2025 wk1-14 have 0 WEEKLY_MATCHUP_RESULT** (transactions ingested,
no game results), and 2025 wk15-18 taper (4/2/1/1) - so 2025 is effectively absent from a
matchup-complete universe by data state, not by criterion choice. Full seasons of complete
weeks: 2010-2023 (weeks 5 & 12 only per season = 28 cells) + 2024 wk1-14 (14 cells) = 42.

### 1.3 Draw procedure (deterministic, reproducible)

- **n = 36** (brief default; D-B permits 24-36).
- **seed = `20260701`**.
- **Method:** order the eligible universe by `sha256(f"{season}:{week_index}:{seed}")`
  hexdigest ascending, take first n. (SQLite has no native sha256; the hash+order is
  computed in Python - fully reproducible by anyone from the seed. The eligible universe
  itself is the SQL above. Exact draw code: `scratchpad/draw.py`, reproduced in Appendix B.)
- **Stratification:** none - flat draw; season spread reported below, not corrected.
- **Smoke cell 2024 wk8 excluded** from the universe before drawing (constraint 6).

### 1.4 The drawn sample (n=36) - THE PINNED CELLS

League `70985`, listed by (season, week) for readability (draw order is by hash):

```
2010 wk5    2010 wk12   2011 wk12   2012 wk5    2012 wk12   2013 wk5
2013 wk12   2014 wk5    2014 wk12   2015 wk5    2015 wk12   2016 wk5
2016 wk12   2017 wk12   2018 wk5    2019 wk5    2019 wk12   2020 wk5
2020 wk12   2021 wk5    2021 wk12   2022 wk5    2022 wk12   2023 wk5
2023 wk12   2024 wk1    2024 wk2    2024 wk3    2024 wk4    2024 wk6
2024 wk7    2024 wk9    2024 wk10   2024 wk11   2024 wk12   2024 wk14
```

**Season spread:** 2010(2) 2011(1) 2012(2) 2013(2) 2014(2) 2015(2) 2016(2) 2017(1)
2018(1) 2019(2) 2020(2) 2021(2) 2022(2) 2023(2) 2024(11). Era skew toward context-sparse
historical weeks (2010-2016 cells carry only matchup results, no transactions/rich
history) plus a run of full-context 2024 weeks - reported, not corrected.

**Full-slate cells NOT drawn (transparency):** 2011 wk5, 2017 wk5, 2018 wk12, 2024 wk5,
2024 wk13.

### 1.5 Readout definitions (pre-registered - written before results exist)

**R1 - first-attempt category breakdown** (no category filter; full 14-enum reported,
zeros shown). Category-breakdown discipline per `reverify_prompt_audit._category_counts_for_tag`
(`json_each` over hard_failures; never row-level pass/fail). Scoped to THIS run's rows via
`id > :baseline_max_id` (baseline captured immediately before Step 4) and the drawn cells:

```sql
SELECT json_extract(hf.value, '$.category') AS category, COUNT(*) AS n
FROM prompt_audit pa,
     json_each(json_extract(pa.verification_result_json, '$.hard_failures')) hf
WHERE pa.id > :baseline_max_id
  AND pa.attempt = 1
  AND pa.league_id = '70985'
  AND (pa.season || ':' || pa.week_index) IN (<the 36 drawn cells>)
GROUP BY category
ORDER BY n DESC;
```

(`:baseline_max_id` = `SELECT MAX(id) FROM prompt_audit` on scratch immediately before the
run; currently 366 post-smoke, re-captured at Step 4 start.)

**R2 - final-outcome distribution.** Each of the 36 cells assigned to exactly one class,
derived from `GenerateDraftResult` (`verification_attempts`, `verification_result.passed`,
`verification_result.hard_failures[].category`):

1. passed on attempt 1  (`passed==True`, attempts==1)
2. passed on attempt 2  (`passed==True`, attempts==2)
3. passed on attempt 3  (`passed==True`, attempts==3)
4. facts-only - Tier-2 short-circuit  (`passed==False` AND final hard_failures contains a
   no-retry category) - record triggering category(ies) and the attempt it fired
5. facts-only - 3 attempts exhausted  (`passed==False`, attempts==3, no no-retry category) -
   record attempt-3 triggering category(ies)
6. `INELIGIBLE_POST_PIN`  (a pinned cell proves ineligible at run time - recorded, never
   substituted)

Edge case: `verification_result is None` (empty narrative / verification exception) is an
infrastructure signal, not a normal class - infra step retried and noted; if persistent,
flagged (would indicate silent degradation the smoke ruled out).

---

## 2. GATE 1 - founder ratification

Founder confirms: (a) eligibility criterion = full slate (==5), universe 41 after smoke
exclusion; (b) n=36 (or reduce to 24); (c) seed=20260701 and the pinned cell list; (d)
scratch-DB measurement; (e) config-as-is including model `claude-sonnet-4-5-20250929`.
On confirmation this block is FROZEN. `INELIGIBLE_POST_PIN` is the only permitted post-freeze
deviation.

**Ratified:** founder, 2026-07-02, as-is (full-slate criterion, universe 41, n=36,
seed 20260701, scratch DB, config-as-is incl. model `claude-sonnet-4-5-20250929`).
Block frozen. Sample not re-drawable.

---

## 3. Results (populated post-run; pre-registration block above unchanged since Gate 1)

### 3.1 R1 - first-attempt category breakdown

Produced by the pre-registered SQL (section 1.5). Scope verified: exactly **36 attempt=1
rows across 36 distinct cells** (`id > 366`, league 70985, drawn set) - one first attempt
per pinned cell, none missing, none extra. Counts are hard-failure occurrences on first
attempts (a single first attempt may contribute several); this is the category breakdown,
never row-level pass/fail.

| category | first-attempt HF count | in brief's 14-enum |
|---|---:|---|
| STREAK | 15 | yes |
| SCORE_VERBATIM | 12 | **NO - emitted, absent from brief listing** |
| FAAB_CLAIM | 11 | yes |
| SUPERLATIVE | 10 | yes |
| SERIES | 8 | yes |
| SEASON_RECORD_CLAIM | 5 | yes |
| DRAFT_AUCTION_DOLLAR | 3 | yes |
| PLAYER_STREAK_CLAIM | 2 | yes |
| RECORD_CLAIM_ANCHORING | 2 | **NO - emitted, absent from brief listing** |
| PLAYER_SCORE | 1 | yes |
| PLAYER_AVG_CLAIM | 1 | yes |
| SCORE | 0 | yes |
| BANNED_PHRASE | 0 | yes |
| PLAYER_FRANCHISE | 0 | yes |
| CHAMPIONSHIP_CLAIM | 0 | yes |
| NUMERIC_UNANCHORED | 0 | yes |
| **TOTAL first-attempt hard failures** | **70** | |

**Enum correction (factual, recorded per silence-over-speculation; does not affect the
measurement).** The brief's Amendment Log states the verifier emits 14 categories. The
verifier at HEAD `89d9321` actually emits **19** distinct `category=` literals
(`grep 'category="' recap_verifier_v1.py | sort -u`): the brief's 14 plus `SCORE_VERBATIM`,
`RECORD_CLAIM_ANCHORING`, `CONSISTENCY`, `SPECULATION`, `STREAK_INVERSION`. Because R1 was
pre-registered as "no category filter - reflect whatever the verifier emits," the readout
captured the two extra categories that actually fired (`SCORE_VERBATIM` x12,
`RECORD_CLAIM_ANCHORING` x2) rather than dropping them. Note `SCORE` fired 0 times while
`SCORE_VERBATIM` fired 12 - the brief's "SCORE" appears to be a mislabel of the emitted
`SCORE_VERBATIM`. Both extra categories are retryable (not in the no-retry set), so R2
classification is unaffected.

### 3.2 R2 - final-outcome distribution

All 36 cells assigned to exactly one class (11+8+1+11+5 = 36). No `INELIGIBLE_POST_PIN`,
no infrastructure `None`/error, no `UNEXPECTED`.

| outcome class | count | share |
|---|---:|---:|
| 1. passed on attempt 1 | 11 | 30.6% |
| 2. passed on attempt 2 | 8 | 22.2% |
| 3. passed on attempt 3 | 1 | 2.8% |
| 4. facts-only - Tier-2 short-circuit | 11 | 30.6% |
| 5. facts-only - 3 attempts exhausted | 5 | 13.9% |
| 6. INELIGIBLE_POST_PIN | 0 | 0% |
| **passed clean (1+2+3)** | **20** | **55.6%** |
| **facts-only fallback (4+5)** | **16** | **44.4%** |

**Per-cell ledger** (attempt = final verification attempt reached; trigger = category that
caused the facts-only fallback):

| cell | outcome | attempt | trigger |
|---|---|---:|---|
| 2010 wk5 | passed attempt 2 | 2 | - |
| 2010 wk12 | passed attempt 1 | 1 | - |
| 2011 wk12 | facts-only exhausted | 3 | PLAYER_STREAK_CLAIM |
| 2012 wk5 | passed attempt 1 | 1 | - |
| 2012 wk12 | passed attempt 1 | 1 | - |
| 2013 wk5 | passed attempt 1 | 1 | - |
| 2013 wk12 | passed attempt 2 | 2 | - |
| 2014 wk5 | facts-only exhausted | 3 | SCORE_VERBATIM |
| 2014 wk12 | passed attempt 2 | 2 | - |
| 2015 wk5 | facts-only exhausted | 3 | SERIES |
| 2015 wk12 | passed attempt 1 | 1 | - |
| 2016 wk5 | passed attempt 2 | 2 | - |
| 2016 wk12 | passed attempt 1 | 1 | - |
| 2017 wk12 | passed attempt 2 | 2 | - |
| 2018 wk5 | passed attempt 2 | 2 | - |
| 2019 wk5 | facts-only Tier-2 short-circuit | 1 | FAAB_CLAIM |
| 2019 wk12 | facts-only exhausted | 3 | STREAK |
| 2020 wk5 | facts-only exhausted | 3 | STREAK, SUPERLATIVE |
| 2020 wk12 | facts-only Tier-2 short-circuit | 1 | FAAB_CLAIM |
| 2021 wk5 | passed attempt 3 | 3 | - |
| 2021 wk12 | passed attempt 1 | 1 | - |
| 2022 wk5 | facts-only Tier-2 short-circuit | 1 | FAAB_CLAIM |
| 2022 wk12 | passed attempt 1 | 1 | - |
| 2023 wk5 | facts-only Tier-2 short-circuit | 1 | FAAB_CLAIM |
| 2023 wk12 | facts-only Tier-2 short-circuit | 1 | FAAB_CLAIM |
| 2024 wk1 | passed attempt 1 | 1 | - |
| 2024 wk2 | facts-only Tier-2 short-circuit | 3 | FAAB_CLAIM |
| 2024 wk3 | passed attempt 2 | 2 | - |
| 2024 wk4 | facts-only Tier-2 short-circuit | 2 | FAAB_CLAIM |
| 2024 wk6 | passed attempt 1 | 1 | - |
| 2024 wk7 | passed attempt 1 | 1 | - |
| 2024 wk9 | facts-only Tier-2 short-circuit | 2 | FAAB_CLAIM |
| 2024 wk10 | passed attempt 2 | 2 | - |
| 2024 wk11 | facts-only Tier-2 short-circuit | 3 | FAAB_CLAIM |
| 2024 wk12 | facts-only Tier-2 short-circuit | 1 | FAAB_CLAIM |
| 2024 wk14 | facts-only Tier-2 short-circuit | 1 | FAAB_CLAIM |

Note on Tier-2 timing: the short-circuit fires on the first attempt whose hard failures
include a no-retry category, which is not always attempt 1 - cells 2024 wk4/wk9 (attempt 2)
and 2024 wk2/wk11 (attempt 3) accrued retryable failures first, then a `FAAB_CLAIM`
appeared on a later attempt and short-circuited. All 11 Tier-2 short-circuits were
triggered by `FAAB_CLAIM`; `NUMERIC_UNANCHORED` (the other no-retry category) never fired.

### 3.3 Infrastructure notes

- Run: 36 cells generated sequentially against scratch, `SQUADVAULT_PROMPT_AUDIT=1`,
  model `claude-sonnet-4-5-20250929`. Exit code 0.
- **Zero infrastructure retries** across all 36 cells (no network / rate-limit events).
- Zero API-failure fallbacks (the silent facts-only degradation guarded against): every
  facts-only outcome is a genuine verification result (Tier-2 short-circuit or exhaustion),
  not a dead-model/dead-key artifact - consistent with the Step 1 smoke.
- prompt_audit: 36 attempt=1 rows written above baseline id 366 (one per cell); total rows
  written across all attempts follow the per-cell attempt counts in 3.2.
- **Production DB untouched:** sha256 `effb00e54fce5c3860423a08338b8711bc96229172452888c97823bc8c5af36b`
  before work and after the full run - unchanged. All writes landed in the scratch copy only.

### 3.4 Plain reading (counts only, no causal speculation)

Over the 36 pinned cells (league 70985, seasons 2010-2024, full-slate weeks), generated
fresh against production config with model `claude-sonnet-4-5-20250929`:

- **First-attempt verification failure rate: 25/36 = 69.4%** (11/36 = 30.6% passed clean on
  the first attempt). This is the headline baseline quantity.
- **Final outcome after the tier-aware retry loop: 20/36 = 55.6% passed clean** (11 on
  attempt 1, 8 on attempt 2, 1 on attempt 3); **16/36 = 44.4% fell back to facts-only**
  (11 Tier-2 short-circuits, 5 exhausted after 3 attempts).
- Of the 25 first-attempt failures, 9 were recovered by retry (8 at attempt 2, 1 at
  attempt 3) and 16 ended facts-only.
- Most frequent first-attempt hard-failure categories: STREAK (15), SCORE_VERBATIM (12),
  FAAB_CLAIM (11), SUPERLATIVE (10), SERIES (8); 70 first-attempt hard failures in total.
- Every Tier-2 short-circuit (11) was triggered by FAAB_CLAIM; NUMERIC_UNANCHORED never
  fired in this sample.

No causal attribution is offered here (out of scope; a separate failure-attribution unit
would be warranted only if the founder judges the counts to justify it). These are the
pre-season control counts against which in-season voice/prompt iteration (from Week 1,
~2026-09-08) will later be compared; the comparison itself is a future unit.

**Exploratory, NOT pre-registered** (recorded only so it is not silently dropped; no weight
should be placed on it): outcomes split by season era were - 2010-2016 (13 cells): 10 passed
clean / 3 facts-only; 2017-2023 (12 cells): 5 passed clean / 7 facts-only; 2024 (11 cells):
5 passed clean / 6 facts-only. This split was not a registered readout and no stratification
was applied; it is noted per the appendix discipline in the brief, not analyzed.

---

## Appendix A - voice profile (verbatim, as probed from scratch)

sha256 3fdd8c9564c6066752d0b8f9129d3a45ce13b4c99859814df0d9ee467d407d8a (len 3938):

```
LEAGUE VOICE PROFILE (commissioner-approved)

This is a 10-team league that has been together since the mid-1980s. Digital records go back approximately 16 seasons. When referencing historical data, always say "across the last 16 seasons of data" or "in available records" — NEVER frame 16 seasons as the league's total age or use phrasing like "over 16 seasons" that implies the league started then. The league is roughly 45 years old; the data is 16 seasons deep. These are different things. Fantasy football is the scaffolding — the friendship is the structure. A good recap should feel like it comes from inside this circle, not from someone covering it.

Team names and grammar:
- Paradis' Playmakers — plural ("the Playmakers scored"), owner: KP (he/him)
- Purple Haze — singular ("Purple Haze scored"), owner: Pat (he/him)
- Eddie & the Cruisers — plural ("the Cruisers scored"), owner: Eddie (he/him)
- Italian Cavallini — singular ("Italian Cavallini scored"), owner: Michele (he/him)
- Robb's Raiders — plural ("the Raiders scored"), owner: Robb (he/him)
- Ben's Gods — plural ("the Gods scored"), owner: Ben (he/him)
- Brandon Knows Ball — singular ("Brandon Knows Ball scored"), owner: Brandon (he/him)
- Weichert's Warmongers — plural ("the Warmongers scored"), owner: Steve (he/him)
- Stu's Crew — singular ("Stu's Crew scored"), owner: Stu (he/him)
- Miller's Genuine Draft — singular ("Miller's Genuine Draft scored"), owner: Miller (he/him)
All owners are male. Use he/him pronouns for all of them. Michele is an Italian male name — do NOT use she/her.
When a team name creates awkward grammar (especially double possessives like "Robb's Raiders' bench"), use the owner's first name instead: "Robb left 50 points on the bench." First names are natural in this league — these guys have known each other for 40 years. Use the full team name on first reference, then switch to first names freely for readability. IMPORTANT: First names replace the owner in ACTION phrases ("Steve left points on the bench") but do NOT replace the possessive in team names. The team name is "Weichert's Warmongers" — never write "Steve's Warmongers." Similarly, write "Paradis' Playmakers" not "KP's Playmakers." When shortening a plural team name, always include "the" — write "the Raiders" not "Raiders", "the Playmakers" not "Playmakers", "the Gods" not "Gods."

Communication register:
- Blunt, affectionate, and relentlessly ball-busting. Roasts are constant but never cruel — they land because everyone knows the line.
- Nobody writes long messages in this group. Keep it tight. Say less when less happened.
- Let big results speak through the numbers, not through adjectives.

Attention distribution:
- Lead with what's interesting, not what's comprehensive. Nobody in this group gives equal time to every matchup — pile on the best and worst results, skip the boring ones.
- Reference history when it matters (rivalry records, losing streaks, past performances) but don't force it when it doesn't.
- When someone loses badly or makes a bad roster decision, the group doesn't let it go. If the data shows a bench decision cost a game, say so plainly.

What this voice sounds like:
- The person in the league who actually remembers what happened.
- Comfortable with bluntness — state what happened and move on.
- Callbacks to history are welcome when the angles support them.
- Skip matchups that weren't notable rather than covering them with filler.

What this voice does NOT sound like:
- A sports columnist or broadcaster. No TV cadences, no hype language.
- "The kind of chaos that makes fantasy football beautiful" — nobody here talks like that.
- "Shows they're not giving up" — never infer someone's internal state.
- Equal coverage of every matchup with balanced analysis — the group piles on interesting results and skips boring ones.
- Precious about anyone's feelings — the group doesn't protect each other from bad results.
```

## Appendix B - draw code (reproduced)

```python
"""Unit 1.4 seeded draw (deterministic, reproducible). NO API calls.

Eligible universe (recommended criterion): recap_runs cells with a FULL matchup
slate (WEEKLY_MATCHUP_RESULT == 5, a complete week for this 10-team league),
minus the smoke cell (2024 wk8). Draw n cells by ordering on sha256(season:week:seed).
"""
import sys, hashlib, sqlite3
sys.path.insert(0, "src")

DB = "/tmp/unit14_scratch.sqlite"
LEAGUE = "70985"
SEED = "20260701"
N = 36
SMOKE = (2024, 8)

ELIGIBILITY_SQL = """
SELECT season, week_index,
       COALESCE(json_extract(counts_by_type_json,'$.WEEKLY_MATCHUP_RESULT'),0) AS matchups
FROM recap_runs
WHERE league_id = ?
ORDER BY season, week_index
"""

con = sqlite3.connect(DB)
rows = con.execute(ELIGIBILITY_SQL, (LEAGUE,)).fetchall()
con.close()

full_slate = [(s, w) for (s, w, m) in rows if m == 5]
at_least_1 = [(s, w) for (s, w, m) in rows if m >= 1]
render_all = [(s, w) for (s, w, m) in rows]

# Recommended universe: full slate minus smoke cell
universe = [c for c in full_slate if c != SMOKE]

def order_key(cell):
    s, w = cell
    return hashlib.sha256(f"{s}:{w}:{SEED}".encode()).hexdigest()

drawn = sorted(universe, key=order_key)[:N]

print("=== ELIGIBILITY CANDIDATE COUNTS ===")
print(f"render-non-empty (weakest)         : {len(render_all)}")
print(f">=1 matchup                        : {len(at_least_1)}")
print(f"full slate (==5) [RECOMMENDED]      : {len(full_slate)}")
print(f"full slate minus smoke (2024 wk8)  : {len(universe)}  <- draw universe")
print()
print(f"=== DRAW: n={N}, seed={SEED}, key=sha256('season:week:seed') ===")
print("Drawn cells (sorted by season, week for readability):")
by_season = {}
for s, w in sorted(drawn):
    by_season.setdefault(s, []).append(w)
    print(f"  {s} wk{w}")
print()
print("=== SEASON SPREAD of drawn cells ===")
for s in sorted(by_season):
    print(f"  {s}: {len(by_season[s])} cells  weeks={by_season[s]}")
print()
print(f"Total drawn: {len(drawn)}")
print()
print("=== cells in full-slate universe NOT drawn (for transparency) ===")
not_drawn = sorted(set(universe) - set(drawn))
for s, w in not_drawn:
    print(f"  {s} wk{w}")
```

## Smoke record (Step 1, pre-Gate-1; throwaway cell excluded from draw)

Cell 2024 wk8, scratch, `SQUADVAULT_PROMPT_AUDIT=1`: `verification_attempts=1`,
`checks_run=16`, `passed=False`, hard_failures `[FAAB_CLAIM, FAAB_CLAIM, PLAYER_AVG_CLAIM]`
-> attempt-1 Tier-2 `FAAB_CLAIM` short-circuit to facts-only (a legitimate R2 outcome-4,
NOT an API failure). API-failure fallback: NOT detected; no RuntimeWarnings. prompt_audit
delta +1. Prod DB hash unchanged. Confirms live LLM generation + verifier + retry
engagement on the corrected (Sonnet 4.5) config.
