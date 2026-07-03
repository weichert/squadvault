# Observation - 2026-07-02 - Unit RM1: FAAB Fix Re-Measurement (Post-F1 Fresh-Generation Rate)

**Session type:** EXECUTE (Claude Code, Opus 4.8). Pre-registered re-measurement per D-Y
(one re-measurement for the fix arc) and D-B (n=24-36), brief
`_observations/session_brief_unit_rm1_faab_remeasurement.md`. Compares the fresh-generation
failure rate at current HEAD against the frozen A7 baseline (memo
`OBSERVATIONS_2026_07_02_UNIT_1_4_FRESH_GENERATION_BASELINE.md`, squash `1948de4`).

**Status:** PRE-REGISTRATION BLOCK FROZEN at Gate 1 (founder ratified as-is, 2026-07-02:
n=36, seed 20260702, universe 41, smoke-cell reuse 2024 wk8 confirmed, config-as-is).
Results sections populated post-run. `INELIGIBLE_POST_PIN` is the only permitted post-freeze
deviation; the sample is not re-drawable.

---

## 0. Ritual / provenance (verified this session)

- **HEAD at session start:** `8e300ac` (RM1 brief, PR #33). Verified `git rev-parse HEAD`.
- **Repo identity:** engine confirmed (`scripts/recap_artifact_regenerate.py` present).
- **Standard trio (green base):** recorded at session start - see section 0.2.
- **Production DB:** `.local_squadvault.sqlite`
  sha256 `effb00e54fce5c3860423a08338b8711bc96229172452888c97823bc8c5af36b`
  (recorded before any work; identical to A7's recorded prod hash - prod untouched since A7;
  re-checked after the smoke - unchanged).
- **Scratch DB:** `/tmp/unit_rm1_scratch.sqlite`, copied from prod; copy sha256 identical
  to source at copy time (`effb00e5...`). All generation runs against the scratch copy only.

### 0.1 Attribution audit (Step 0) - commit range `89d9321` (exclusive) .. `8e300ac` (inclusive)

Every commit on main from the A7 baseline HEAD to current HEAD, with file-level
classification (from `git diff-tree --name-only`):

| commit | subject | files touched | class |
|---|---|---|---|
| `1948de4` | Unit A7 baseline (#24) | `_observations/`, `docs/STATE.md` | docs-only |
| `e949c13` | remove false DoR model-pin carry-forward (#25) | `docs/STATE.md` | docs-only |
| `9571885` | FAAB_CLAIM attribution Stage A (#26) | `_observations/`, `docs/STATE.md` | docs-only |
| `1038da4` | Stage B session brief (#27) | `_observations/` | docs-only |
| `7f436bd` | FAAB_CLAIM attribution Stage B (#28) | `_observations/`, `docs/STATE.md` | docs-only |
| `b0b675b` | Unit F1 session brief (#29) | `_observations/` | docs-only |
| **`6778101`** | **Unit F1 verifier fix (#30)** | **`src/squadvault/core/recaps/verification/recap_verifier_v1.py`**, `Tests/test_recap_verifier_v1.py`, `_observations/`, `docs/STATE.md` | **SOURCE-BEHAVIORAL** |
| `06d8d0c` | Unit F2 session brief (#31) | `_observations/` | docs-only |
| `5c3fc04` | Unit F2 regression lock (#32) | `Tests/test_faab_starvation_regression_lock_v1.py`, `_observations/`, `docs/STATE.md` | tests-only |
| `8e300ac` | Unit RM1 session brief (#33) | `_observations/` | docs-only |

**Result: clean.** `6778101` (F1) is the ONLY commit touching `src/`. F2 (`5c3fc04`)
touches only `Tests/` + docs (no source). All other commits touch only `_observations/`
and/or `docs/STATE.md`. **The measured delta from the A7 baseline therefore attributes
to the Unit F1 verifier change and nothing else.** The memo claims no causal mechanism
beyond this audited attribution basis.

### 0.2 Standard trio (green base at session start)

Recorded at session start (HEAD `8e300ac`, before any work): ruff `check src/squadvault/`
**All checks passed**; mypy `src/squadvault/` **Success: no issues found in 160 source
files**; pytest **2397 passed, 2 skipped, 2 warnings in 395.44s**. The 2 warnings are the
known in-test empty-API-key fixture in `Tests/test_creative_layer_rivalry_v1.py`
(`ANTHROPIC_API_KEY not set -> facts-only`), unrelated to this measurement.

---

## 1. PRE-REGISTRATION BLOCK (DRAFT - freezes on Gate 1 founder ratification)

### 1.1 Configuration in force (measured as-is at HEAD `8e300ac`; no edits)

| Item | Value (verified this session) |
|---|---|
| HEAD | `8e300ac` |
| Scratch-DB source hash | `effb00e54fce5c3860423a08338b8711bc96229172452888c97823bc8c5af36b` |
| Generation model (`_MODEL`, `src/squadvault/ai/creative_layer_v1.py:35`) | `claude-sonnet-4-5-20250929` |
| Temperature (base) | `0.8` (`_TEMPERATURE`, `creative_layer_v1.py:36`); retry decay `[None, 0.5, 0.3]` (`weekly_recap_lifecycle.py:1334`) |
| Retry cap (`_MAX_VERIFICATION_RETRIES`, `weekly_recap_lifecycle.py:1277`) | `3` |
| No-retry categories (`_NO_RETRY_CATEGORIES`, `weekly_recap_lifecycle.py:1288`) | `FAAB_CLAIM`, `NUMERIC_UNANCHORED` |
| Verifier | `src/squadvault/core/recaps/verification/recap_verifier_v1.py` (F1-modified at `6778101`); 19 distinct emitted `category=` literals (below) |
| Voice profile (`get_voice_profile(scratch, '70985')`) | PRESENT (commissioner-approved), len 3938, sha256 `3fdd8c9564c6066752d0b8f9129d3a45ce13b4c99859814df0d9ee467d407d8a` (byte-identical to A7 Appendix A - same sha) |
| Prompt-audit capture | `SQUADVAULT_PROMPT_AUDIT=1` (R1 data source) |

**Verifier emitted-category set at HEAD (no filter applied in R1)** - 19 distinct literals
(`grep -oE 'category="[A-Z_]+"' recap_verifier_v1.py | sort -u`): BANNED_PHRASE,
CHAMPIONSHIP_CLAIM, CONSISTENCY, DRAFT_AUCTION_DOLLAR, FAAB_CLAIM, NUMERIC_UNANCHORED,
PLAYER_AVG_CLAIM, PLAYER_FRANCHISE, PLAYER_SCORE, PLAYER_STREAK_CLAIM,
RECORD_CLAIM_ANCHORING, SCORE, SCORE_VERBATIM, SEASON_RECORD_CLAIM, SERIES, SPECULATION,
STREAK, STREAK_INVERSION, SUPERLATIVE. This is the **same 19-category set A7 recorded** -
F1 changed the FAAB_CLAIM emit logic (vocabulary + binder-crossover), not the category
enum, so R1's category axis is directly comparable to A7's.

### 1.2 Census - eligible universe (re-probed on scratch at HEAD; A7 census NOT reused)

Single league in DB: `70985`. 64 recap_runs cells total. Eligibility SQL (the golden-path
core - a real weekly recap needs matchup results to recap; identical criterion discipline
to A7):

```sql
SELECT season, week_index,
       COALESCE(json_extract(counts_by_type_json,'$.WEEKLY_MATCHUP_RESULT'),0) AS matchups
FROM recap_runs
WHERE league_id = '70985'
ORDER BY season, week_index;
```

Candidate eligibility criteria and resulting counts (RM1 re-probe on scratch):

| Criterion | Count | Note |
|---|---|---|
| render-non-empty (weakest) | 64 | passes even for 0-event weeks; rejected as too weak |
| WEEKLY_MATCHUP_RESULT >= 1 | 49 | includes partial/playoff slates |
| **WEEKLY_MATCHUP_RESULT == 5 (full slate) [criterion]** | **42** | complete week for this 10-team league |
| full slate minus smoke cell (2024 wk8) | **41** | **draw universe** |

The re-probe reproduces A7's census exactly (64 / 49 / 42 / 41), as expected: the scratch
DB is byte-identical to A7's prod source (same sha `effb00e5...`). The re-probe is
performed fresh per the brief (do not reuse A7's results), not inherited.

**Smoke-cell choice (excluded from the universe).** RM1 reuses A7's throwaway smoke cell
2024 wk8 as its own Step 1 smoke cell. Both the A7 smoke cell and this session's smoke
cell are therefore the same member, and the exclusion yields the A7-defined universe of 41.
(Founder may direct a different RM1 smoke cell at Gate 1, which would drop the universe to
40 by excluding two distinct cells; the draw would then be re-derived on the ratified
universe before any pinned generation.)

### 1.3 Draw procedure (deterministic, reproducible)

- **n = 36** (brief default; D-B permits reduction to 24 at Gate 1).
- **seed = `20260702`** (A7 used `20260701`; RM1 is a fresh draw by design).
- **Method (A7 method, unchanged):** order the eligible universe by
  `sha256(f"{season}:{week_index}:{seed}")` hexdigest ascending, take first n. Computed in
  Python (SQLite has no native sha256); fully reproducible from the seed. Exact draw code:
  `scratchpad/rm1_census_draw.py`, reproduced in Appendix B.
- **Stratification:** none - flat draw; season spread reported below, not corrected.
- **Smoke cell 2024 wk8 excluded** from the universe before drawing.

### 1.4 The drawn sample (n=36) - THE PINNED CELLS

League `70985`, listed by (season, week) for readability (draw order is by hash):

```
2010 wk5    2010 wk12   2011 wk12   2012 wk5    2012 wk12   2013 wk5
2013 wk12   2014 wk5    2014 wk12   2016 wk5    2016 wk12   2017 wk5
2017 wk12   2018 wk5    2018 wk12   2019 wk5    2019 wk12   2020 wk5
2020 wk12   2021 wk12   2022 wk5    2022 wk12   2023 wk5    2023 wk12
2024 wk1    2024 wk2    2024 wk3    2024 wk4    2024 wk5    2024 wk6
2024 wk7    2024 wk9    2024 wk10   2024 wk11   2024 wk12   2024 wk13
```

**Season spread:** 2010(2) 2011(1) 2012(2) 2013(2) 2014(2) 2016(2) 2017(2) 2018(2)
2019(2) 2020(2) 2021(1) 2022(2) 2023(2) 2024(12). Note 2015 is entirely absent from this
draw (both 2015 full-slate cells fell outside the first 36), and 2024 contributes 12 cells.

**Draw-mix difference vs A7 (comparison-precision disclosure).** A7's spread was
2010(2) 2011(1) 2012(2) 2013(2) 2014(2) 2015(2) 2016(2) 2017(1) 2018(1) 2019(2) 2020(2)
2021(2) 2022(2) 2023(2) 2024(11). RM1 differs at: 2015 (A7 2 -> RM1 0), 2017 (1 -> 2),
2018 (1 -> 2), 2021 (2 -> 1), 2024 (11 -> 12). This is the intended fresh draw (D-B):
reusing A7's cells would measure per-cell reproduction, not the rate. The two draws' cell
mixes bound the comparison's precision; no significance claims are made (section 4).

**Full-slate cells NOT drawn (transparency):** 2011 wk5, 2015 wk5, 2015 wk12, 2021 wk5,
2024 wk14. (36 drawn + 5 not drawn = 41 universe.)

### 1.5 Readout definitions (pre-registered - written before results exist)

**R1 - first-attempt category breakdown** (no category filter; full 19-literal set
reported, zeros shown). Category-breakdown discipline per
`reverify_prompt_audit._category_counts_for_tag` (`json_each` over hard_failures; never
row-level pass/fail). Scoped to THIS run's rows via `id > :baseline_max_id` (baseline
captured immediately before Step 4) and the 36 drawn cells:

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
Step 4 run; the Step 1 smoke rows on 2024 wk8 sit at or below this baseline and are
excluded both by `id` and by the drawn-cell filter.)

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
   substituted; the only permitted post-freeze deviation)

Edge case: `verification_result is None` (duplicate-matchup gate / verification exception)
is an infrastructure signal, not a normal class - infra step retried and noted; if
persistent on a pinned cell it is recorded `INELIGIBLE_POST_PIN`.

**R3 - baseline-vs-RM1 category comparison (NEW, pre-registered).** A side-by-side of the
A7 first-attempt category breakdown (baseline side) against RM1's R1 (this run), FAAB_CLAIM
highlighted. The **baseline side is quoted verbatim from the committed A7 memo section 3.1
(squash `1948de4`) - NOT recomputed** from any surviving artifact. R3 introduces no new SQL:
its RM1 side is exactly the R1 output above; its baseline side is the frozen A7 table. The
comparison is category-level only (both sides produced by the same breakdown discipline);
no row-level pass/fail comparison is made. FAAB_CLAIM movement is reported as a count delta
only; no causal mechanism is asserted beyond the section 0.1 attribution basis.

A7 baseline first-attempt category breakdown (quoted from committed A7 memo, for the R3
baseline column):

| category | A7 first-attempt HF count |
|---|---:|
| STREAK | 15 |
| SCORE_VERBATIM | 12 |
| FAAB_CLAIM | 11 |
| SUPERLATIVE | 10 |
| SERIES | 8 |
| SEASON_RECORD_CLAIM | 5 |
| DRAFT_AUCTION_DOLLAR | 3 |
| PLAYER_STREAK_CLAIM | 2 |
| RECORD_CLAIM_ANCHORING | 2 |
| PLAYER_SCORE | 1 |
| PLAYER_AVG_CLAIM | 1 |
| SCORE / BANNED_PHRASE / PLAYER_FRANCHISE / CHAMPIONSHIP_CLAIM / NUMERIC_UNANCHORED | 0 |
| **A7 TOTAL first-attempt hard failures** | **70** |

---

## 2. GATE 1 - founder ratification

Founder confirms: (a) eligibility criterion = full slate (==5), universe 41 after smoke
exclusion; (b) n=36 (or reduce to 24); (c) seed=20260702 and the pinned cell list; (d)
scratch-DB measurement; (e) config-as-is including model `claude-sonnet-4-5-20250929` and
the F1-modified verifier at `6778101`; (f) smoke-cell choice 2024 wk8 (or direct a
different cell -> universe re-derives to 40). On confirmation this block is FROZEN.
`INELIGIBLE_POST_PIN` is the only permitted post-freeze deviation; the sample is not
re-drawable.

**Ratified:** founder, 2026-07-02, as-is (full-slate criterion, universe 41, n=36,
seed 20260702, scratch DB, config-as-is incl. model `claude-sonnet-4-5-20250929` and the
F1 verifier at `6778101`, smoke-cell reuse 2024 wk8 confirmed - draw NOT re-derived).
Block frozen. Sample not re-drawable.

---

## 3. Results (populated post-run; pre-registration block above unchanged after Gate 1)

### 3.1 R1 - first-attempt category breakdown

Produced by the pre-registered SQL (section 1.5) against scratch, `baseline_max_id = 367`
(= `MAX(prompt_audit.id)` immediately before the Step 4 run; the two Step 1 smoke rows sit
at ids 366-367, at/below the baseline, and are excluded both by `id` and by the drawn-cell
filter). Scope verified: exactly **36 attempt=1 rows across 36 distinct cells** - one first
attempt per pinned cell, none missing, none extra. Counts are hard-failure occurrences on
first attempts (a single first attempt may contribute several); category breakdown, never
row-level pass/fail.

| category | RM1 first-attempt HF count |
|---|---:|
| SUPERLATIVE | 15 |
| SCORE_VERBATIM | 14 |
| STREAK | 12 |
| SERIES | 6 |
| SEASON_RECORD_CLAIM | 6 |
| FAAB_CLAIM | 3 |
| PLAYER_AVG_CLAIM | 2 |
| all other emitted categories (DRAFT_AUCTION_DOLLAR, PLAYER_STREAK_CLAIM, RECORD_CLAIM_ANCHORING, PLAYER_SCORE, PLAYER_FRANCHISE, SCORE, BANNED_PHRASE, CHAMPIONSHIP_CLAIM, NUMERIC_UNANCHORED, CONSISTENCY, SPECULATION, STREAK_INVERSION) | 0 |
| **TOTAL first-attempt hard failures** | **58** |

### 3.2 R2 - final-outcome distribution

All 36 cells assigned to exactly one class (8+7+2+4+15 = 36). No `INELIGIBLE_POST_PIN`, no
infrastructure `None`/error, no `INFRA_ERROR`.

| outcome class | count | share |
|---|---:|---:|
| 1. passed on attempt 1 | 8 | 22.2% |
| 2. passed on attempt 2 | 7 | 19.4% |
| 3. passed on attempt 3 | 2 | 5.6% |
| 4. facts-only - Tier-2 short-circuit | 4 | 11.1% |
| 5. facts-only - 3 attempts exhausted | 15 | 41.7% |
| 6. INELIGIBLE_POST_PIN | 0 | 0% |
| **passed clean (1+2+3)** | **17** | **47.2%** |
| **facts-only fallback (4+5)** | **19** | **52.8%** |

**Per-cell ledger** (attempt = final verification attempt reached; trigger = category(ies)
that caused the facts-only fallback):

| cell | outcome | attempt | trigger |
|---|---|---:|---|
| 2010 wk5 | passed attempt 3 | 3 | - |
| 2010 wk12 | passed attempt 1 | 1 | - |
| 2011 wk12 | facts-only exhausted | 3 | PLAYER_STREAK_CLAIM |
| 2012 wk5 | passed attempt 1 | 1 | - |
| 2012 wk12 | facts-only exhausted | 3 | STREAK |
| 2013 wk5 | facts-only exhausted | 3 | SCORE_VERBATIM, SUPERLATIVE |
| 2013 wk12 | facts-only exhausted | 3 | SCORE_VERBATIM, SUPERLATIVE |
| 2014 wk5 | facts-only exhausted | 3 | PLAYER_AVG_CLAIM, SCORE_VERBATIM |
| 2014 wk12 | facts-only exhausted | 3 | SCORE_VERBATIM |
| 2016 wk5 | passed attempt 2 | 2 | - |
| 2016 wk12 | passed attempt 1 | 1 | - |
| 2017 wk5 | passed attempt 2 | 2 | - |
| 2017 wk12 | facts-only exhausted | 3 | PLAYER_SCORE, STREAK, SUPERLATIVE |
| 2018 wk5 | passed attempt 1 | 1 | - |
| 2018 wk12 | passed attempt 2 | 2 | - |
| 2019 wk5 | passed attempt 1 | 1 | - |
| 2019 wk12 | passed attempt 1 | 1 | - |
| 2020 wk5 | facts-only exhausted | 3 | STREAK |
| 2020 wk12 | passed attempt 1 | 1 | - |
| 2021 wk12 | passed attempt 2 | 2 | - |
| 2022 wk5 | facts-only Tier-2 short-circuit | 1 | FAAB_CLAIM |
| 2022 wk12 | facts-only exhausted | 3 | PLAYER_SCORE, SEASON_RECORD_CLAIM |
| 2023 wk5 | passed attempt 3 | 3 | - |
| 2023 wk12 | facts-only exhausted | 3 | PLAYER_AVG_CLAIM |
| 2024 wk1 | passed attempt 2 | 2 | - |
| 2024 wk2 | passed attempt 2 | 2 | - |
| 2024 wk3 | passed attempt 1 | 1 | - |
| 2024 wk4 | facts-only exhausted | 3 | SEASON_RECORD_CLAIM, SUPERLATIVE |
| 2024 wk5 | facts-only Tier-2 short-circuit | 2 | FAAB_CLAIM |
| 2024 wk6 | facts-only exhausted | 3 | SCORE_VERBATIM |
| 2024 wk7 | facts-only exhausted | 3 | SCORE_VERBATIM |
| 2024 wk9 | facts-only exhausted | 3 | SUPERLATIVE |
| 2024 wk10 | passed attempt 2 | 2 | - |
| 2024 wk11 | facts-only Tier-2 short-circuit | 1 | FAAB_CLAIM |
| 2024 wk12 | facts-only exhausted | 3 | SCORE_VERBATIM |
| 2024 wk13 | facts-only Tier-2 short-circuit | 1 | FAAB_CLAIM |

All 4 Tier-2 short-circuits were triggered by `FAAB_CLAIM` (`NUMERIC_UNANCHORED`, the other
no-retry category, never fired - as in A7). Three fired on attempt 1 (2022 wk5, 2024 wk11,
2024 wk13); one on attempt 2 (2024 wk5, which accrued retryable failures on attempt 1 then
a FAAB_CLAIM on attempt 2). This reconciles R1 and R2: R1's attempt=1 FAAB_CLAIM count (3)
equals the three attempt-1 short-circuits; the fourth (2024 wk5) fired its FAAB on attempt 2
and so does not appear in the attempt=1 R1 breakdown. For comparison, A7 recorded **11**
Tier-2 FAAB short-circuits; RM1 records **4**.

### 3.3 R3 - baseline-vs-RM1 comparison (FAAB_CLAIM highlighted)

Baseline column quoted verbatim from the committed A7 memo section 3.1 (squash `1948de4`);
RM1 column is the R1 output above. Category-level only, same breakdown discipline both
sides. Ordered by max(A7, RM1) descending.

| category | A7 (baseline) | RM1 | delta |
|---|---:|---:|---:|
| STREAK | 15 | 12 | -3 |
| SUPERLATIVE | 10 | 15 | **+5** |
| SCORE_VERBATIM | 12 | 14 | +2 |
| **FAAB_CLAIM** | **11** | **3** | **-8** |
| SERIES | 8 | 6 | -2 |
| SEASON_RECORD_CLAIM | 5 | 6 | +1 |
| DRAFT_AUCTION_DOLLAR | 3 | 0 | -3 |
| PLAYER_AVG_CLAIM | 1 | 2 | +1 |
| PLAYER_STREAK_CLAIM | 2 | 0 | -2 |
| RECORD_CLAIM_ANCHORING | 2 | 0 | -2 |
| PLAYER_SCORE | 1 | 0 | -1 |
| SCORE / BANNED_PHRASE / PLAYER_FRANCHISE / CHAMPIONSHIP_CLAIM / NUMERIC_UNANCHORED | 0 | 0 | 0 |
| **TOTAL** | **70** | **58** | **-12** |

**FAAB_CLAIM first-attempt: 11 -> 3 (delta -8).** This is the pre-registered highlighted
comparison and the largest single-category move in the table. It is the direction the
"expected shape" (section 4) stated in advance.

**Non-FAAB movements are reported, not explained away** (brief section 4). The largest
non-FAAB move is **SUPERLATIVE +5** (10 -> 15), an increase; SCORE_VERBATIM +2 and STREAK
-3 also moved. Total first-attempt hard failures fell 70 -> 58 (-12), but that fall is not
uniform and is bounded by the different cell mix (below). These movements are recorded as
findings for founder adjudication; no attribution work is performed here (out of scope) and
none is asserted beyond the section 0.1 audit.

**Comparison-precision caveat (n=36 vs n=36, different draws).** The two draws differ in
cell mix - RM1 season spread 2010(2) 2011(1) 2012(2) 2013(2) 2014(2) 2016(2) 2017(2)
2018(2) 2019(2) 2020(2) 2021(1) 2022(2) 2023(2) 2024(12) vs A7's 2010(2) 2011(1) 2012(2)
2013(2) 2014(2) 2015(2) 2016(2) 2017(1) 2018(1) 2019(2) 2020(2) 2021(2) 2022(2) 2023(2)
2024(11). RM1 omits 2015 entirely and carries one more 2024 cell. Cell-mix differences
bound the comparison's precision; **no significance claims are made.**

### 3.4 Infrastructure notes

- Run: 36 cells generated sequentially against scratch, `SQUADVAULT_PROMPT_AUDIT=1`, model
  `claude-sonnet-4-5-20250929`, `force=True`, no mid-run intervention. Exit code 0.
- **Zero infrastructure retries** across all 36 cells (no network / rate-limit / API
  exceptions; harness infra-retry wrapper never fired). Zero `INFRA_ERROR`, zero
  `verification_result is None`.
- Zero API-failure/dead-key facts-only fallbacks: every facts-only outcome is a genuine
  verification result (Tier-2 short-circuit or exhaustion), consistent with the Step 1 smoke.
- prompt_audit: 78 rows written across all attempts (ids 368-445; `baseline_max_id` 367);
  36 attempt=1 rows (one per cell), the remainder are attempts 2-3.
- **Production DB untouched:** sha256 `effb00e5...4f36b` before work and after the full run -
  unchanged. All writes landed in the scratch copy only.

### 3.5 Plain reading (counts only, no causal speculation)

Over the 36 pinned cells (league 70985, seasons 2010-2024, full-slate weeks), generated
fresh against production config at HEAD `8e300ac` with model `claude-sonnet-4-5-20250929`
and the F1-modified verifier (`6778101`):

- **First-attempt verification failure rate: 28/36 = 77.8%** (8/36 = 22.2% passed clean on
  the first attempt). A7's was 25/36 = 69.4%.
- **Final outcome after the tier-aware retry loop: 17/36 = 47.2% passed clean** (8 att1 /
  7 att2 / 2 att3); **19/36 = 52.8% fell back to facts-only** (4 Tier-2 short-circuits, 15
  exhausted). A7's was 20/36 = 55.6% clean / 16/36 = 44.4% facts-only.
- **FAAB_CLAIM first-attempt hard failures: 11 (A7) -> 3 (RM1), delta -8.** FAAB-triggered
  Tier-2 short-circuits: 11 (A7) -> 4 (RM1). The FAAB_CLAIM count moved materially lower,
  the direction stated in advance. Every Tier-2 short-circuit in RM1 was still FAAB_CLAIM;
  NUMERIC_UNANCHORED never fired.
- Other first-attempt categories moved within the draw-mix-bounded comparison: SUPERLATIVE
  rose (10 -> 15), SCORE_VERBATIM rose (12 -> 14), STREAK fell (15 -> 12); total first-attempt
  hard failures fell 70 -> 58. The overall clean rate did NOT improve (55.6% -> 47.2%) and the
  first-attempt failure rate rose (69.4% -> 77.8%) - i.e. the FAAB reduction did not lift the
  aggregate pass rate in this draw, and non-FAAB categories (notably SUPERLATIVE) account for
  more of the failures here than in A7.

No causal attribution beyond the section 0.1 audit is offered (the audit establishes only
that F1 is the sole source change between the two HEADs; it does not by itself explain the
non-FAAB movements, which the different cell mix confounds). Whether the FAAB_CLAIM
reduction, read against the non-FAAB movements and the mix caveat, is sufficient to close
the FAAB arc is a founder adjudication in the DECIDE lane on these numbers - explicitly NOT
decided here.

---

## Appendix A - voice profile

sha256 `3fdd8c9564c6066752d0b8f9129d3a45ce13b4c99859814df0d9ee467d407d8a` (len 3938),
probed from scratch this session. Byte-identical to A7 memo Appendix A (same sha); full
text is reproduced there and not duplicated here per documentation-hygiene (no duplication).

## Appendix B - draw code (reproduced)

```python
"""Unit RM1 seeded draw (deterministic, reproducible). NO API calls.
Eligible universe: recap_runs cells with a FULL matchup slate
(WEEKLY_MATCHUP_RESULT == 5), minus the smoke cell (2024 wk8). Draw n cells by
ordering on sha256(season:week:seed). RM1 differs from A7 only in seed (20260702)."""
import sys, hashlib, sqlite3
sys.path.insert(0, "src")

DB = "/tmp/unit_rm1_scratch.sqlite"
LEAGUE = "70985"
SEED = "20260702"
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
universe = [c for c in full_slate if c != SMOKE]

def order_key(cell):
    s, w = cell
    return hashlib.sha256(f"{s}:{w}:{SEED}".encode()).hexdigest()

drawn = sorted(universe, key=order_key)[:N]
```

## Smoke record (Step 1, pre-Gate-1; throwaway cell 2024 wk8, excluded from draw)

Cell 2024 wk8, scratch `/tmp/unit_rm1_scratch.sqlite`, `SQUADVAULT_PROMPT_AUDIT=1`,
`force=True`: `verification_attempts=2`, `checks_run=16`, `passed=True` (recovered on
attempt 2), final `hard_failures=[]`. prompt_audit delta +2 (one row per attempt, ids
366-367 on scratch). No RuntimeWarnings; API-failure/dead-key facts-only degradation NOT
detected (a first, key-less attempt earlier in the session correctly produced the
`ANTHROPIC_API_KEY not set -> facts-only` warning with delta +0 and was discarded; the
re-run with `.env.local` sourced in the same shell produced the real generation recorded
here). Prod DB hash unchanged (`effb00e5...`). Confirms live LLM generation + verifier +
tier-aware retry on the config-as-is (Sonnet 4.5, F1 verifier).
