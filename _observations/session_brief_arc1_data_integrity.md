# Session Brief -- Arc 1: Data Integrity
## SquadVault | Commissioner Review Arc | Verifier Hardening + Review Surface

**Session type:** Implementation
**Governing document:** _observations/SquadVault_Product_Vision_and_Storytelling_Architecture_v1_0.md
**Arc brief:** _observations/session_brief_commissioner_review_arc.md
**HEAD at brief authoring:** c73c066

---

## Why this arc exists

The 2025 season editorial review (2026-05-16) revealed that the commissioner
cannot validate hard facts without significant effort. 12 of 13 approved recaps
required at least one edit before distribution. Only W7 was approved clean.

The fabrication problem is characterized. The fix is known. This arc executes it.

Goal: hard factual errors do not reach the commissioner. The commissioner reads
a recap, judges quality, and approves or rejects it. No fact investigation required.

---

## Preamble verification (run before any other action)

    cd /Users/steve/projects/squadvault-ingest-fresh
    git rev-parse HEAD
    git log --oneline -5
    pytest Tests/ -x -q 2>&1 | tail -5
    ruff check src/squadvault/core/ --quiet
    mypy src/squadvault/core/

Expected:
- HEAD: c73c066
- Tests: 2227 passed / 3 skipped
- Ruff: zero errors
- Mypy: no issues found in 68 source files

---

## Root causes being addressed

RC1: Writer's Room generates beyond Signal Scout scope
  Synthesizes cumulative FAAB figures, player scoring averages,
  cross-season records -- none verified before reaching commissioner.

RC2: Verifier scope is narrow
  Does not check dollar amounts attributed to waiver acquisitions,
  cross-week player scoring claims, historical records, or any
  numeric figure not anchored to Signal Scout output.

RC3: Fabrications persist across weeks
  Brian Thomas Jr. ($51) appeared in W4 and W12.
  Justin Jefferson ($60) appeared in W13 and W14.
  Same context produces same hallucination. Constrained generation
  is the fix, not repeated verification attempts.

RC4: Review surface has no claim-level transparency
  Commissioner sees recap text only. No inline annotation, no
  verification report, no suggested edits.

---

## Phase A: Constrain the Writer's Room

### A1 -- Audit Writer's Room context (DO THIS FIRST)

Everything depends on understanding exactly what the Writer's Room
is currently seeing. Inspect the actual prompt.

Query the most recent prompt_audit record for a 2025 week:

    python3 -c "
    import sqlite3
    conn = sqlite3.connect('.local_squadvault.sqlite')
    cur = conn.cursor()
    cur.execute('''
        SELECT week_index, narrative_angles_text, budgeted_summary_json
        FROM prompt_audit
        WHERE league_id=70985 AND season=2025
        ORDER BY id DESC LIMIT 1
    ''')
    row = cur.fetchone()
    if row:
        print('Week:', row[0])
        print('Angles (first 2000):', str(row[1])[:2000])
        print('Budgeted (first 2000):', str(row[2])[:2000])
    conn.close()
    "

Then inspect Writer's Room prompt construction:

    grep -rn "system_prompt\|prior.*recap\|previous.*recap\|approved.*recap"         src/squadvault/core/recaps/ --include="*.py"

Key questions A1 must answer:
1. Is prior approved recap text being passed as context?
   (explains fabrication persistence across weeks)
2. What cross-week figures, if any, are currently computed and passed?
3. What instruction, if any, exists about numeric claim sourcing?

Deliverable: memo filed as:
_observations/OBSERVATIONS_ARC1_A1_WRITERS_ROOM_AUDIT.md

### A2 -- Add generation constraint to Writer's Room prompt

After A1, add explicit instruction to the Writer's Room system prompt:

  "Every specific numeric claim in this recap -- dollar amounts, point
  totals, counts, ratios, averages, streaks -- must appear verbatim in
  the Signal Scout context provided. Do not compute, estimate, or infer
  figures not present in this context. Omit rather than invent."

Test by regenerating W4. If constraint works, the fabricated FAAB
paragraph (Brian Thomas Jr., McConkey, Bowers) does not appear.

### A3 -- Extend Signal Scout context with verified cross-week figures

Push deterministic DB-computed figures into prompt context.

Priority additions:
1. Current season FAAB spend to date by franchise
   Source: WAIVER_BID_AWARDED, season + week <= current
2. Current season win/loss record by franchise
   Source: WEEKLY_MATCHUP_RESULT, season + week < current
3. Championship appearance count by franchise (all-time)
   Source: WEEKLY_MATCHUP_RESULT, championship weeks only
   (W16 for 2010-2020, W18 for 2021-2025)
4. All-time best regular season records
   Source: WEEKLY_MATCHUP_RESULT, regular season weeks only

Each addition: implement as deterministic query, verify against known
2025 values, then commit.

---

## Phase B: Extend the verifier

### B1 -- WAIVER_BID_AWARDED claim checker (highest priority)

Any dollar amount attributed to a waiver acquisition must exist in
WAIVER_BID_AWARDED for that franchise and player in that season.

New check category: WAIVER_CLAIM
Detection: extract (franchise_name, player_name, dollar_amount) triples
Verification: look up in WAIVER_BID_AWARDED
Hard failure if no matching record

Regression test fixtures (confirmed fabricated, W4):
  Brandon / Brian Thomas Jr. / $51 -- hard failure expected
  Eddie / Ladd McConkey / $32 -- hard failure expected
  Steve / Brock Bowers / $46 -- hard failure expected

### B2 -- Historical claim checker

New categories: CHAMPIONSHIP_CLAIM, SEASON_RECORD_CLAIM
Verify against WEEKLY_MATCHUP_RESULT.

Regression test fixtures (W16/W17 errors):
  "six times" championship appearances -- hard failure (actual: 7)
  "12-2 record" -- hard failure (actual: 15-2)

### B3 -- Cross-week player scoring checker

New category: PLAYER_STREAK_CLAIM
Verify streaks and averages against WEEKLY_PLAYER_SCORE (32,649 rows).
Hard failure on mismatch, soft failure within 10% tolerance.

### B4 -- Numeric anchoring checker (implement after A2)

Any numeric figure not present in Signal Scout context is a violation.
Exception: figures derivable by simple arithmetic from context.
New category: NUMERIC_UNANCHORED.
Catch-all for A2 violations.

---

## Phase C: Smarter retry policy

Tier 1 -- retry eligible (up to 3 attempts):
  SERIES, PLAYER_FRANCHISE, PLAYER_SCORE
  Rationale: vary between attempts, model can self-correct.

Tier 2 -- no retry, immediate facts-only:
  WAIVER_CLAIM, NUMERIC_UNANCHORED
  Rationale: same context produces same hallucination. Retry wastes
  API calls. Fix is A2/A3, not more attempts.

Edit burden policy:
  More than 2 edits triggers regeneration prompt at commissioner review.

---

## Phase D: Commissioner review surface

Extend scripts/review_recap.py with claim-level verification status.

D1: Inline claim annotation after each paragraph:
  [VERIFIED] "$40 FAAB for Purdy" -- WAIVER_BID_AWARDED: $40.01
  [FLAGGED]  "$51 Brian Thomas Jr." -- no matching WAIVER_BID_AWARDED
  [OMITTED]  Claim removed before commissioner review

D2: Verification summary header before recap text:
  Verification status: PASSED / FLAGGED / WITHHELD
  Claims verified: N | Claims omitted: N | Suggested edits: N
  FLAGGED or WITHHELD recaps do not reach the approval prompt.

D3: Suggested edits for borderline claims with reason.
  Commissioner accepts or overrides. Decision logged.

D4: Edit burden counter with regeneration prompt at threshold of 3.

---

## Phase E: Verification query library

Formalize ad-hoc scripts from 2025 review into scripts/audit_queries/:

  faab_spend_by_franchise.py --season --week-through --league-id
  player_bid_lookup.py --season --franchise --player --league-id
  championship_appearances.py --franchise --league-id
  season_records_alltime.py --league-id [--franchise]
  player_scoring_by_week.py --season --franchise --player --league-id

Standalone, readable output, no dependencies beyond sqlite3.

---

## Sequencing within this session

1.  A1 -- audit Writer's Room prompt, file memo
2.  B1 -- WAIVER_BID_AWARDED checker (highest value, independent)
3.  A2 -- prompt constraint (informed by A1)
4.  C  -- retry policy (after B1)
5.  B2 -- historical claim checker
6.  A3 -- Signal Scout context extensions
7.  B3 -- cross-week player scoring checker
8.  B4 -- numeric anchoring checker (after A2)
9.  D  -- commissioner review surface (after B1, B2, C)
10. E  -- verification query library (interleave as needed)

Each step: tests passing, ruff and mypy clean, committed before next.

---

## Validation at arc completion

Regenerate and review W1-W5 of 2025 season after all phases complete.
Compare edit burden to 2026-05-16 session results.
Target: zero hard factual errors reach the commissioner.
Target: average edits per approved recap below one.

---

## Key facts from prior session

- WEEKLY_PLAYER_SCORE: 32,649 rows, 2010-2025
- WEEKLY_MATCHUP_RESULT: 1,182 rows, 2010-2025
- Championship weeks: W16 for 2010-2020, W18 for 2021-2025
- KP (0002) championship appearances: 7
  (2012W, 2014L, 2019W, 2020W, 2021L, 2024L, 2025W)
- All-time best winning pct: Miller 2018 at 14-1
- Most regular season wins: Playmakers 2025 at 15-2
- Confirmed fabrications (not in DB):
  Brian Thomas Jr. ($51, Brandon) -- W4, W12
  Ladd McConkey ($32, Eddie) -- W4
  Brock Bowers ($46, Steve) -- W4
  Justin Jefferson ($60, Michele) -- W13, W14

---

## What is NOT in scope this arc

- Arc 2+ work (player performance layer, manager identity)
- New Signal Scout detectors beyond A3
- New narrative angles
- Distribution tooling
- Rivalry Chronicles
- Personal artifacts (Arc 6)
- UI/UX surface (Arc 7)
