# Owner-name step 5 + Option B decision

**Date:** 2026-04-19
**Scope:** Characterization only. No DB mutations, no ingest runs, no
code changes. Diagnostic output only.
**HEAD:** `c001a8c` — Phase 10 observation: owner-name step 5 auth-path
blocker.

---

## SHA-256 drift check

State captured at session open; matches the 2026-04-21 pre-read
(`ecbc1d4`) and the 2026-04-21 auth-blocker memo (`c001a8c`):

| File | SHA-256 | Matches |
|---|---|---|
| `src/squadvault/core/recaps/verification/recap_verifier_v1.py` | `745d1f8ad9dfadd0c5c2cb935611839b0ca1d20e00b89c922aff27190e9f8752` | ✅ |
| `src/squadvault/ingest/franchises/_run_franchises_ingest.py` | `0b1ea91a47c37cbbe6b83915bfed19d3bd5a6b9da50c2973f866d51fc562c70f` | ✅ |
| `src/squadvault/mfl/client.py` | `1ea40f247a1fbe4eac3370a69367e3bd5e46fd4ceefed10ecbb55667f985142d` | ✅ |
| `src/squadvault/mfl/historical_ingest.py` | `4210016b5095985e7661320db4edc7aae768d1fedbaf824232e3bf0d5773e843` | ✅ |

No drift. Safe to proceed.

---

## Summary

- **Q1** (MFL returns `owner_name` unauthenticated?): **No.** HTTP 200
  with `owner_name=None` across all 10 franchises. Answered
  definitively by `c001a8c` (auth-blocker memo); not re-probed.
- **Q2** (MFL returns `owner_name` authenticated?): **Yes.** All 10
  franchises returned populated LEGAL_NAME strings under forced auth.
  Cookie-jar diff (`[]` → `['MFL_PW_SEQ', 'MFL_USER_ID']`) confirms
  auth fired at transport level.
- **Q3** (per-franchise values): full classification table below.
- **Q4** (raw_json holds owner_name even though column is empty?):
  **No.** `raw_json.$.owner_name` is null-or-empty-string across all
  10 rows in both 2025 and 2024. Plain re-ingest will not populate
  from existing JSON; re-ingest requires forced auth.
- **Q5** (older seasons populated?): `franchise_directory` covers
  seasons 2009-2025 (17 seasons; one earlier than the pre-read's
  hypothesized 2010-2025). `n_rows = 10` and `n_name_populated = 10`
  for every season; `n_owner_populated = 0` for every season. Complete
  absence, not a partial gap.
- **Q6** (pass-4 alias collisions across all 10): none. All 10
  lowercased first-word aliases are distinct.

**Decision:** **Option B** — franchise 0002 (KP) returned Shape B
under authenticated MFL (legal-first `Kent Paradis`), which makes
the pass-4 alias `kent` dead for league-used "KP." Option A alone
would leave the F3 (Pat) and F6-KP attribution failures from the
2026-04-20 APPROVED_STREAK memo unresolved for the KP side.

---

## Investigation trail

### Step 1 — Drift check

Done. See SHA-256 table above.

### Step 2 — `franchise_directory` inventory (Q5)

```sql
.mode column
.headers on
SELECT season,
       COUNT(*) AS n_rows,
       COUNT(NULLIF(name, '')) AS n_name_populated,
       COUNT(NULLIF(owner_name, '')) AS n_owner_populated
FROM franchise_directory
WHERE league_id = '70985'
GROUP BY season
ORDER BY season;
```

**Result:**

```
season  n_rows  n_name_populated  n_owner_populated
------  ------  ----------------  -----------------
2009    10      10                0
2010    10      10                0
2011    10      10                0
2012    10      10                0
2013    10      10                0
2014    10      10                0
2015    10      10                0
2016    10      10                0
2017    10      10                0
2018    10      10                0
2019    10      10                0
2020    10      10                0
2021    10      10                0
2022    10      10                0
2023    10      10                0
2024    10      10                0
2025    10      10                0
```

**Interpretation (Q5):** 17 of 17 seasons carry complete franchise
rows (`n_rows=10`, `n_name_populated=10`) and zero `owner_name`
population. The gap is universal, not partial. Option A execution
would need to touch every season from 2009 onward. The 2009 row is
one earlier than the pre-read's hypothesized 2010-2025 range — minor
scope expansion, not a structural surprise.

### Step 3 — `raw_json` inspection (Q4)

2025 probe:

```sql
.mode line
SELECT franchise_id, name,
       json_extract(raw_json, '$.owner_name') AS raw_owner,
       json_extract(raw_json, '$.id') AS raw_id
FROM franchise_directory
WHERE league_id = '70985' AND season = 2025
ORDER BY franchise_id;
```

**Result (2025):** all 10 rows returned `raw_owner` as blank (null or
empty string — `.mode line` renders both identically, and the
distinction is decision-irrelevant because either value lands in the
same Q4 branch). `raw_id` populated correctly for all rows (0001-0010),
confirming `json_extract` path resolution is working and the blank
`raw_owner` is a real absence, not a pathing quirk.

2024 probe: identical shape — 10 rows, blank `raw_owner`, populated
`raw_id`.

**Interpretation (Q4):** MFL did not return `owner_name` at ingest
time for either season. The raw response reached the DB but the
field was not present (or present-but-empty) in the JSON. This is
consistent with the auth-blocker memo's Risk 2 confirmation —
ingest-time callers never authenticated, so MFL stripped the field
before responding. The "raw_owner populated → plain re-ingest
works" branch of Q4 is closed. Re-ingest (Option A execution or
Option B schema work) requires forced-auth plumbing through the
ingest path.

### Step 5 — Force-auth MFL probe (Q2, Q3, Q6)

Inline probe, one shot, no committed files. Cookie-jar diff added
on top of the brief's base probe to disambiguate three auth
failure modes (`_login` is silent on missing creds, rejected
creds, and rate-limited login) from a populated-null MFL response.

```bash
./scripts/py -c "
import os
from squadvault.mfl.client import MflClient
c = MflClient(
    server=os.environ['MFL_SERVER'],
    league_id='70985',
    username=os.environ['MFL_USERNAME'],
    password=os.environ['MFL_PASSWORD'],
)
print('COOKIES_PRE_LOGIN :', sorted(c.session.cookies.keys()))
c._login(2025)
print('COOKIES_POST_LOGIN:', sorted(c.session.cookies.keys()))
league_json, url = c.get_league_info(2025)
franchises = (
    league_json.get('league', {}).get('franchises', {}).get('franchise')
    or league_json.get('franchises', {}).get('franchise', [])
)
print('SOURCE URL:', url)
for f in franchises:
    print(f.get('id'), repr(f.get('name')), '->', repr(f.get('owner_name')))
"
```

**Result:**

```
COOKIES_PRE_LOGIN : []
COOKIES_POST_LOGIN: ['MFL_PW_SEQ', 'MFL_USER_ID']
SOURCE URL: https://www44.myfantasyleague.com/2025/export?TYPE=league&L=70985&JSON=1
0001 "Stu's Crew" -> 'David Stuart'
0002 "Paradis' Playmakers" -> 'Kent Paradis'
0003 'Purple Haze' -> 'Pat Nocero'
0004 'Eddie & the Cruisers' -> 'Eddie Carmichael'
0005 "Weichert's Warmongers" -> 'Steve Weichert'
0006 'Miller’s Genuine Draft' -> 'Dave Miller'
0007 "Robb's Raiders" -> 'Robb Maruyama'
0008 "Ben's Gods" -> 'Ben Herlth'
0009 'Italian Cavallini' -> 'Michele Bellanca'
0010 'Brandon Knows Ball' -> 'Brandon Carmichael'
```

**Contrast vs `c001a8c`:** that probe reported identical-shape output
with `owner_name=None` for every row. The current probe's cookie
transition (`[]` → `['MFL_PW_SEQ', 'MFL_USER_ID']`) and populated
`owner_name` values across all 10 franchises jointly prove that (1)
auth fired at transport level and (2) auth resolves the owner_name
absence. Q2 is answered: **MFL returns populated `owner_name` on
L=70985 under authenticated session.**

SOURCE URL does not carry an `APIKEY` query parameter — this is
consistent with MFL's cookie-based session auth (no per-request
credential); not a sign the probe authenticated on the wrong path.

---

## Full 10-franchise classification table (Q3)

| fid | franchise | owner_name | rubric | shape | pass-4 alias | league-used | match |
|---|---|---|---|---|---|---|---|
| 0001 | Stu's Crew | David Stuart | LEGAL_NAME | — | `david` | Stu | ❌ (not critical; pass-2 covers via `stu`) |
| 0002 | Paradis' Playmakers | **Kent Paradis** | **LEGAL_NAME** | **B** | `kent` | **KP** | ❌ **DEAD** |
| 0003 | Purple Haze | Pat Nocero | NICKNAME | **A** | `pat` | Pat | ✅ |
| 0004 | Eddie & the Cruisers | Eddie Carmichael | NICKNAME | — | `eddie` | Eddie | ✅ |
| 0005 | Weichert's Warmongers | Steve Weichert | NICKNAME | **A** | `steve` | Steve | ✅ |
| 0006 | Miller's Genuine Draft | Dave Miller | LEGAL_NAME | — | `dave` | Miller | ❌ (pass-2 covers via `miller`) |
| 0007 | Robb's Raiders | Robb Maruyama | NICKNAME | — | `robb` | Robb | ✅ |
| 0008 | Ben's Gods | Ben Herlth | NICKNAME | — | `ben` | Ben | ✅ |
| 0009 | Italian Cavallini | Michele Bellanca | NICKNAME | **A** | `michele` | Michele | ✅ |
| 0010 | Brandon Knows Ball | Brandon Carmichael | NICKNAME | — | `brandon` | Brandon | ✅ |

**Rubric definitions (from pre-read):**
- **LEGAL_NAME** — first-name form that is NOT the league-used
  short-form.
- **NICKNAME** — matches league-used short-form verbatim in the first
  token.

**Shape classification (critical 4 only; non-critical franchises
carry "—" since they are not load-bearing on pass-4):**
- **Shape A** (nickname-first): 3 of 4 — 0003 Pat, 0005 Steve, 0009
  Michele.
- **Shape B** (legal-first): 1 of 4 — **0002 KP**. MFL returned
  `Kent Paradis`; the legal first name `Kent` is a near-exact
  instance of the pre-read matrix's hypothetical `Kevin Paradis` —
  only the specific first name differs. Classification and
  consequence identical.
- **Shape C** (bare nickname): 0 of 4.

**Franchise 0001 (Stu / Stu's Crew) cross-check:** classified
LEGAL_NAME (`David Stuart`, first token `david` ≠ league-used `Stu`).
Not among the critical 4 because pass-2 already yields `stu` from the
franchise name `Stu's Crew`. Noted for completeness.

**Franchise 0006 apostrophe:** MFL returns `Miller's Genuine Draft`
with U+2019 RIGHT SINGLE QUOTATION MARK, not U+0027 APOSTROPHE. This
is the known MFL encoding inconsistency that
`_run_franchises_ingest._normalize_apostrophes` handles at ingest
time (line 121). The probe is client-side and does not apply that
normalization, so the raw MFL value appears verbatim in the probe
output. Not a finding; noted so future readers of the probe output
don't interpret it as a discrepancy.

---

## Risk 3 — Collision check (Q6)

Pass-4 lowercased first-word aliases across all 10 owners:

```
david, kent, pat, eddie, steve, dave, robb, ben, michele, brandon
```

All 10 unique. No collisions. `David` (0001) and `Dave` (0006) are
distinct tokens under `\w+` split — `david` and `dave` do not
collide even though they are the same given name informally.

**Risk 3 cleared.** Pass-4 suppression at
`recap_verifier_v1.py:406` will not fire for any franchise in this
league's 2025 roster.

---

## Decision rule application

Pre-read decision rule (verbatim):

> - Step 5 shows MFL returning **shape A or C for all 4 critical
>   franchises** → **Option A**.
> - Step 5 shows MFL returning **shape B for KP or Pat** → **Option B**
>   (Option A alone leaves known-bad F3/F6-KP cases unresolved).
> - Step 5 is **DEFERRED** → memo ships with decision conditional.
> - **Option C is not recommended** regardless of step 5 outcome.

**Critical-franchise shape distribution this session:** 0002 = **B**,
0003 = A, 0005 = A, 0009 = A.

**Franchise 0002 (KP) selected Shape B.** The second branch of the
decision rule fires: **Option B.** Mechanical selection — not a
close call. One of the two named worst-case franchises (KP)
returned legal-first form, and pass-4 alias `kent` is dead for
league-used "KP."

**Option A alone would resolve 3 of 4 critical franchises but leave
0002 (KP) unresolved.** The 2026-04-20 APPROVED_STREAK memo's F6-KP
attribution failure would remain a live defect under Option A.

---

## Incidental finding — unauth write paths extend beyond `client.py`

Pre-probe source audit (not part of the 04-21 pre-read's scope)
surfaced three distinct code paths that write to
`franchise_directory`, **all three of which omit authentication in
the happy case:**

1. **`_run_franchises_ingest.py` (direct CLI)** — uses
   `urllib.request.urlopen` at line 63 with no credentials
   parameter. `MflClient` is not involved. The unauth HTTP 200 is
   the only possible outcome of this path.
2. **`historical_ingest._ingest_franchise_info` with
   `league_json=None`** — calls `MflClient.get_league_info`, which
   uses reactive auth at `client.py:149` (`status_code != 200`
   gate). MFL returns HTTP 200 for unauth callers, so the auth
   branch never fires. This is the auth-blocker memo's Risk 2.
3. **`historical_ingest._ingest_franchise_info` with `league_json`
   from discovery (the standard flow)** — line 99-100 short-circuits
   past the client entirely. The cached JSON originates in
   `discovery._probe_season`, which is plain `session.get` at
   `discovery.py:183` with no auth parameter at all (not even a
   reactive path).

Empirical confirmation of this static finding: Step 2's universal-zero
`n_owner_populated` across 17 seasons and Step 3's universal-blank
`raw_owner` across 2024 and 2025 are the predicted outcome when all
three write paths converge on unauthenticated MFL responses.

**Consequence for the next session's scope:** the auth-blocker memo's
Option (ii) framing — "src/squadvault/mfl/client.py behavior change to
force auth on field-null responses" — is insufficient as stated.
Forcing auth on `client.py` alone would not populate `owner_name`
through `historical_ingest`, because that path preferentially uses
`disc_season.raw_franchises` from discovery, which never reaches the
client. Option (ii) scoping (if reached) would need to cover either
`discovery._probe_season` auth, or `_ingest_franchise_info` preferring
a fresh client call over the cache for FRANCHISE_INFO specifically,
or both. Not this session's concern; flagged for the Option B
scoping brief's context section.

**This is observation material, not a fix proposal.** No src
change recommended by this memo.

---

## Recommended next move

**Option B scoping brief.** Schema design (column on
`franchise_directory` vs separate `franchise_nicknames` table vs
override map), code change in `_build_reverse_name_map` (pass 5 or
pass-4 override), regression test design covering the KP dead-alias
case. That brief also needs to touch the auth-plumbing scope
surfaced above, since Option B's re-ingest step (if it re-ingests
at all) hits the same three unauth write paths.

Not an implementation pass. A scoping pass. Implementation is the
session after that.

---

## Out of scope

- Option B schema design, code change, and regression test (next
  session).
- Option A execution (population via `historical_ingest.py`).
- Option (ii) — `client.py`, `discovery.py`, or `historical_ingest.py`
  auth-plumbing changes. Distinct scoping brief, itself a
  precondition for Option B's re-ingest step.
- Per-franchise nickname curation decisions.
- `waiver_bids.py` ingest promotion.
- `deterministic_bullets_v1.py` consumer-layer leak pass.
- `audit_queries/README.md` catalog update (still deferred
  housekeeping).
- The four untracked `scripts/diagnose_*.py` entries.
- Amending the 2026-04-21 pre-read (`ecbc1d4`), the 2026-04-21
  audit query memo (`83ea9d3`), or the 2026-04-21 auth-blocker
  memo (`c001a8c`).

---

## Cross-references

- **Upstream pre-read:** `ecbc1d4` —
  `_observations/OBSERVATIONS_2026_04_21_OWNER_NAME_POPULATION_PREREAD.md`
  (Q1-Q5, rubric, matrix, decision rule).
- **Immediate predecessor:** `c001a8c` —
  `_observations/OBSERVATIONS_2026_04_21_OWNER_NAME_STEP5_AUTH_BLOCKER.md`
  (Risk 2 confirmation, force-auth requirement).
- **Attribution-failure root cause context:** 2026-04-20 APPROVED_STREAK
  memo — F1/F2 = Michele, F3 = Pat, F6 = Steve and KP. All four names
  are the pre-read's critical-4 franchises; Option B's dead-alias
  resolution targets F3 and F6-KP specifically.
- **Pass-4 alias derivation:**
  `src/squadvault/core/recaps/verification/recap_verifier_v1.py:388-410`.
- **Unauth write paths (incidental finding):**
  `src/squadvault/ingest/franchises/_run_franchises_ingest.py:63`,
  `src/squadvault/mfl/client.py:149`,
  `src/squadvault/mfl/discovery.py:183`,
  `src/squadvault/mfl/historical_ingest.py:99-100,712-715`.

---

## Observation-time state

- HEAD at observation-time: `c001a8c`
- Test baseline unchanged: 1849 passed, 2 skipped
- Ruff: 0 errors (`src/`); 238 pre-existing in `Tests/` (unchanged)
- Mypy: 0 errors (`src/squadvault/core/`); 59 source files clean
- No `src/` or `Tests/` changes in this session
- Credentials confirmed present at observation-time (cookie-jar
  transition `[]` → `['MFL_PW_SEQ', 'MFL_USER_ID']` proves
  MFL session establishment)
- No DB mutations, no ingest runs
- `_login` called at probe level only (diagnostic, not production);
  no change to its public/private API status
