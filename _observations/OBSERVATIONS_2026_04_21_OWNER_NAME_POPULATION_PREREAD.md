# Owner-name population pre-read

**Date:** 2026-04-21
**Scope:** Characterization only. No DB mutations, no ingest runs, no
code changes. Diagnostic output only.
**HEAD:** `7324ee9` — Phase 10 observation: reverse_name_map owner-alias
diagnostic.

---

## SHA-256 drift check

State captured at session open:

| File | SHA-256 | Brief match |
|---|---|---|
| `src/squadvault/core/recaps/verification/recap_verifier_v1.py` | `745d1f8ad9dfadd0c5c2cb935611839b0ca1d20e00b89c922aff27190e9f8752` | ✅ matches brief |
| `src/squadvault/ingest/franchises/_run_franchises_ingest.py` | `0b1ea91a47c37cbbe6b83915bfed19d3bd5a6b9da50c2973f866d51fc562c70f` | first capture |
| `src/squadvault/mfl/client.py` | `1ea40f247a1fbe4eac3370a69367e3bd5e46fd4ceefed10ecbb55667f985142d` | first capture |
| `src/squadvault/mfl/historical_ingest.py` | `4210016b5095985e7661320db4edc7aae768d1fedbaf824232e3bf0d5773e843` | first capture |

No drift. Safe to proceed.

Empirical-completion session (2026-04-21 continuation) re-verified the
same four SHAs at the same HEAD; no drift between pre-read scaffolding
and empirical runs.

---

## Summary

- **Q1** (MFL returns `owner_name` unauthenticated?): **No.** HTTP 200
  returned but the `owner_name` key is **entirely absent** from all 10
  franchise dicts in the unauth TYPE=league response for L=70985 (step 4).
- **Q2** (MFL returns `owner_name` authenticated?): **DEFERRED** —
  `MFL_SERVER`/`MFL_USERNAME`/`MFL_PASSWORD` not in env or `.env.local`.
  A-vs-B decision gated on this probe.
- **Q3** (per-franchise values): **EMPTY across all 10 under unauth**
  (step-6 table). LEGAL_NAME / NICKNAME / OTHER classification for the
  4 critical franchises is pending step 5.
- **Q4** (raw_json holds owner_name even though column is empty?):
  **No.** `raw_json` omits `owner_name` for all 10 franchises in both
  2024 and 2025 (step 3) — the stored dicts mirror MFL's unauth response
  exactly. Risk 2 is confirmed active in a stronger form than the
  scaffold enumerated: the field is stripped **entirely**, not merely
  empty-strung.
- **Q5** (older seasons populated?): **No.** `owner_name` is empty for
  all 170 rows across the full 17-season window (2009–2025). Not a
  partial-coverage gap — uniform zero-population.

**Structural finding from static analysis (does not require probes):**

Pass-4 is load-bearing for only **4 of 10 franchises** in this league.
The other 6 franchises' owner short-forms are already covered by pass-2
first-word franchise-name aliases. Scope of "what owner_name population
unlocks" is narrower than "all 10 franchises" — it is specifically KP
(Paradis' Playmakers), Pat (Purple Haze), Steve (Weichert's Warmongers),
and Michele (Italian Cavallini).

**Recommended population strategy: Option A-or-B conditional** per the
decision rule. Both options require MFL credentials in `.env.local`;
step 4 confirms unauth re-ingest reproduces the current empty state
(the `!= 200` retry gate at `client.py:149` does not fire on
key-absent 200s). Final A-vs-B choice is gated on step 5's shape
finding and is deferred to the session that runs the authed probe.

---

## Franchise roster + pass-4 dependency (from static analysis)

Source: verbatim snapshot at `Tests/test_recap_verifier_v1.py:2318-2329`
(2026-04-18 live DB mirror). Owner mappings inferred from (a) existing
regression test at `Tests/test_recap_verifier_v1.py:258-262` and
(b) `_ROW7_PROSE` at `Tests/test_recap_verifier_v1.py:2356-2389` — in
particular line 2373: "Pat left massive production on his bench"
immediately following "Purple Haze also moved to 4-0", which grounds
Pat → Purple Haze.

| fid | franchise | owner (league-used) | pass-2 first-word alias | pass-3 last-word alias | pass-4 load-bearing? |
|---|---|---|---|---|---|
| 0001 | Stu's Crew | Stu | `stu` (3 ≥ 3 ✅) | — (`crew` 4 < 5 ❌) | ❌ — pass-2 covers owner short-form |
| 0002 | Paradis' Playmakers | **KP** | `paradis` | `playmakers` | ✅ **load-bearing** |
| 0003 | Purple Haze | **Pat** (row-7 prose) | `purple` | — (`haze` 4 < 5 ❌) | ✅ **load-bearing** |
| 0004 | Eddie & the Cruisers | Eddie | `eddie` | `cruisers` | ❌ — pass-2 covers |
| 0005 | Weichert's Warmongers | **Steve** | `weichert` | `warmongers` | ✅ **load-bearing** |
| 0006 | Miller's Genuine Draft | Miller | `miller` | — (`draft` stop-worded ❌) | ❌ — pass-2 covers |
| 0007 | Robb's Raiders | Robb | `robb` (4) | `raiders` | ❌ — pass-2 covers |
| 0008 | Ben's Gods | Ben | `ben` (3) | — (`gods` 4 < 5 ❌) | ❌ — pass-2 covers |
| 0009 | Italian Cavallini | **Michele** | `italian` | `cavallini` | ✅ **load-bearing** |
| 0010 | Brandon Knows Ball | Brandon | `brandon` | — (`ball` 4 < 5 ❌) | ❌ — pass-2 covers |

**Net:** 4 franchises genuinely depend on pass-4 for league-used owner
short-form coverage. Populating `owner_name` unlocks recognition of KP,
Pat, Steve, and Michele as attribution anchors — the exact four names
the 2026-04-20 APPROVED_STREAK memo identified as attribution failure
root causes (F1/F2 = Michele, F3 = Pat, F6 = Steve and KP).

---

## Investigation trail

### Step 1 — Drift check
Done. See SHA-256 table above.

### Step 2 — `franchise_directory` inventory (Q4, Q5)

```sql
-- sqlite3 .local_squadvault.sqlite
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

**Interpretation (Q5):** Populated across 0/17 seasons; the gap is
total, not partial — `owner_name` is empty for all 170 rows across
2009–2025. `name` is fully populated everywhere, so the ingest is
otherwise healthy; owner_name is the sole missing field.

### Step 3 — raw_json inspection (Q4)

2025 probe (all 10 rows; output is per-franchise single-line):
```sql
.mode line
SELECT franchise_id, name,
       json_extract(raw_json, '$.owner_name') AS raw_owner,
       json_extract(raw_json, '$.id') AS raw_id
FROM franchise_directory
WHERE league_id = '70985' AND season = 2025
ORDER BY franchise_id;
```

```
franchise_id = 0001
        name = Stu's Crew
   raw_owner =
      raw_id = 0001

franchise_id = 0002
        name = Paradis' Playmakers
   raw_owner =
      raw_id = 0002

franchise_id = 0003
        name = Purple Haze
   raw_owner =
      raw_id = 0003

franchise_id = 0004
        name = Eddie & the Cruisers
   raw_owner =
      raw_id = 0004

franchise_id = 0005
        name = Weichert's Warmongers
   raw_owner =
      raw_id = 0005

franchise_id = 0006
        name = Miller's Genuine Draft
   raw_owner =
      raw_id = 0006

franchise_id = 0007
        name = Robb's Raiders
   raw_owner =
      raw_id = 0007

franchise_id = 0008
        name = Ben's Gods
   raw_owner =
      raw_id = 0008

franchise_id = 0009
        name = Italian Cavallini
   raw_owner =
      raw_id = 0009

franchise_id = 0010
        name = Brandon Knows Ball
   raw_owner =
      raw_id = 0010
```

2024 probe:
```sql
.mode line
SELECT franchise_id, name,
       json_extract(raw_json, '$.owner_name') AS raw_owner,
       json_extract(raw_json, '$.id') AS raw_id
FROM franchise_directory
WHERE league_id = '70985' AND season = 2024
ORDER BY franchise_id;
```

```
franchise_id = 0001
        name = Stu's Crew
   raw_owner =
      raw_id = 0001

franchise_id = 0002
        name = Paradis' Playmakers
   raw_owner =
      raw_id = 0002

franchise_id = 0003
        name = Purple Haze
   raw_owner =
      raw_id = 0003

franchise_id = 0004
        name = Eddie & the Cruisers
   raw_owner =
      raw_id = 0004

franchise_id = 0005
        name = Weichert's Warmongers
   raw_owner =
      raw_id = 0005

franchise_id = 0006
        name = Miller's Genuine Draft
   raw_owner =
      raw_id = 0006

franchise_id = 0007
        name = Robb's Raiders
   raw_owner =
      raw_id = 0007

franchise_id = 0008
        name = Ben's Gods
   raw_owner =
      raw_id = 0008

franchise_id = 0009
        name = Italian Cavallini
   raw_owner =
      raw_id = 0009

franchise_id = 0010
        name = Brandon Knows Ball
   raw_owner =
      raw_id = 0010
```

**Interpretation (Q4):** `json_extract(raw_json, '$.owner_name')` returns
an empty result for all 10 franchises in both 2024 and 2025 — consistent
with the `owner_name` key being absent (or null/empty) in the stored
dict. The stored raw_json mirrors step 4's live unauth response, where
the key is absent entirely. This is the **auth-required branch** of the
memo's original two-branch interpretation: MFL never returned
`owner_name` on the original unauth ingest calls. Re-ingest under Option
A requires auth env vars; the current retry gate at `client.py:149`
does not catch this response class.

_Schema note: `raw_json` stores the per-franchise dict (via
`json.dumps(fr, ...)` at `_run_franchises_ingest.py:136`). Expected
fields: `id`, `name`, `owner_name`, `abbrev`, `division`. No `server`
field (server discovery is in-memory only; `DiscoveryReport` never
persisted)._

### Step 4 — Unauthenticated MFL probe (Q1)

Server resolution: not in DB; use env `MFL_SERVER` or fallback
`www44.myfantasyleague.com` (from `_run_franchises_ingest.py:17`
usage example).

```bash
curl -s "https://www44.myfantasyleague.com/2025/export?TYPE=league&L=70985&JSON=1" \
  | python3 -m json.tool | head -200
```

Look for the `"franchise"` array. Capture the first 2-3 entries.

```
URL: https://www44.myfantasyleague.com/2025/export?TYPE=league&L=70985&JSON=1
HTTP status: 200

First 3 franchise entries:
{
  "abbrev": "SC",
  "division": "00",
  "icon": "https://www46.myfantasyleague.com/fflnetdynamic2010/78078_franchise_icon0001.jpg",
  "id": "0001",
  "logo": "https://www46.myfantasyleague.com/fflnetdynamic2010/78078_franchise_logo0001.jpg",
  "name": "Stu's Crew",
  "waiverSortOrder": "5"
}
{
  "abbrev": "PP",
  "division": "01",
  "icon": "https://www44.myfantasyleague.com/fflnetdynamic2025/70985_franchise_icon0002.jpg",
  "id": "0002",
  "name": "Paradis' Playmakers",
  "waiverSortOrder": "1"
}
{
  "abbrev": "PH",
  "division": "00",
  "icon": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS1SVW3knsuS4vO9-t3zy-36sK54FybobThGWNnbr9YxQ&s=10",
  "id": "0003",
  "logo": "https://www44.myfantasyleague.com/fflnetdynamic2017/70985_franchise_logo0003.jpg",
  "name": "Purple Haze",
  "stadium": "Hendrix Field",
  "waiverSortOrder": "4"
}

(total franchises in response: 10)
```

**Interpretation (Q1):**

_The scaffold enumerated three patterns:_
- HTTP 200 with populated `owner_name`: Q1 = "yes". Unauth re-ingest suffices.
- HTTP 200 with empty `owner_name`: silent gap (risk #2). Auth required.
- HTTP non-200: standard auth-required response. Client retries with creds automatically.

_Observed: a fourth pattern — HTTP 200 with the `owner_name` key
**entirely absent** from every franchise dict._ The keys actually
present are `abbrev`, `division`, `icon`, `id`, `logo` (sometimes),
`name`, `stadium` (sometimes), `waiverSortOrder`. This collapses
operationally to pattern 2 — `client.py:149`'s `!= 200` retry gate
doesn't fire, so the client accepts the 200 without retrying under
auth — but the mechanism is stronger than "empty-strung": the field
is stripped entirely, which is what any `fr.get("owner_name")` in
the ingest path sees as `None` and normalizes into the empty-string
column we see in step 3. **Risk 2 confirmed active.** Auth probe is
required to determine what the authenticated response shape looks
like (step 5).

### Step 5 — Authenticated MFL probe (Q2)

**Pre-check:** are `MFL_SERVER`, `MFL_USERNAME`, `MFL_PASSWORD` set in env?

- **Yes** → run probe below.
- **No** → **DEFERRED**; note and proceed. Credentials go in
  `.env.local`, never mid-session.

```bash
# Only if all three env vars are set:
./scripts/py -c "
import os
from squadvault.mfl.client import MflClient
c = MflClient(
    server=os.environ['MFL_SERVER'],
    league_id='70985',
    username=os.environ['MFL_USERNAME'],
    password=os.environ['MFL_PASSWORD'],
)
league_json, url = c.get_league_info(2025)
franchises = (
    league_json.get('league', {}).get('franchises', {}).get('franchise')
    or league_json.get('franchises', {}).get('franchise', [])
)
for f in franchises:
    print(f.get('id'), repr(f.get('name')), '→', repr(f.get('owner_name')))
"
```

```
DEFERRED — credentials not in env (missing: MFL_SERVER MFL_USERNAME MFL_PASSWORD)
```

Neither the shell environment nor `.env.local` (checked via the
harness) currently carries the three MFL credential vars. Per brief
discipline, credentials are not added mid-session. The authed probe
is deferred to a follow-up session where the credentials are added
to `.env.local` properly.

### Step 6 — Per-franchise classification (Q3)

League-used short-forms pre-filled. **MFL returns** column reflects
the unauth step-4 observation; authed classification for the 4
critical franchises is pending step 5.

| fid | franchise | league-used | MFL returns | classification | pass-4 alias |
|---|---|---|---|---|---|
| 0001 | Stu's Crew | Stu | (unauth: `owner_name` absent) | EMPTY | _(not load-bearing — pass-2 `stu`)_ |
| 0002 | Paradis' Playmakers | **KP** | (unauth: `owner_name` absent) | EMPTY; auth pending | **critical — deferred to step 5** |
| 0003 | Purple Haze | **Pat** | (unauth: `owner_name` absent) | EMPTY; auth pending | **critical — deferred to step 5** |
| 0004 | Eddie & the Cruisers | Eddie | (unauth: `owner_name` absent) | EMPTY | _(not load-bearing — pass-2 `eddie`)_ |
| 0005 | Weichert's Warmongers | **Steve** | (unauth: `owner_name` absent) | EMPTY; auth pending | **critical — deferred to step 5** |
| 0006 | Miller's Genuine Draft | Miller | (unauth: `owner_name` absent) | EMPTY | _(not load-bearing — pass-2 `miller`)_ |
| 0007 | Robb's Raiders | Robb | (unauth: `owner_name` absent) | EMPTY | _(not load-bearing — pass-2 `robb`)_ |
| 0008 | Ben's Gods | Ben | (unauth: `owner_name` absent) | EMPTY | _(not load-bearing — pass-2 `ben`)_ |
| 0009 | Italian Cavallini | **Michele** | (unauth: `owner_name` absent) | EMPTY; auth pending | **critical — deferred to step 5** |
| 0010 | Brandon Knows Ball | Brandon | (unauth: `owner_name` absent) | EMPTY | _(not load-bearing — pass-2 `brandon`)_ |

Rubric:
- **EMPTY** — nothing usable (empty / null / field absent)
- **LEGAL_NAME** — first+last or bare first (e.g. `Kevin Paradis`, `Patrick X`)
- **NICKNAME** — matches league-used short-form verbatim in the first token (e.g. `KP Paradis`, `Pat X`, `Michele Baroi`, `Steve Weichert`)
- **OTHER** — email, handle, unexpected

**The 4 critical rows are 0002 / 0003 / 0005 / 0009.** Other 6 can be
any classification without affecting coverage. Under current (unauth)
observation all 10 are EMPTY; no collision risk between critical rows'
observed values can be evaluated until step 5.

### Step 7 — Resolution-probability matrix

Alias derivation (`_build_reverse_name_map:395-398`):
`re.findall(r"\w+", owner_name)[0].lower()`, with `len ≥ 2`, stop-word
filter `{"the","and","team","club","fantasy"}`, uniqueness per alias,
non-override.

**None of the four league-used short-forms (KP, Pat, Steve, Michele)
hit the stop-word set.**

Outcome matrix per plausible MFL return shape, for the 4 critical
franchises:

| franchise | Shape A: nickname-first | Shape B: legal-first | Shape C: bare nickname |
|---|---|---|---|
|  | `KP Paradis` / `Pat X` / `Steve Weichert` / `Michele Baroi` | `Kevin Paradis` / `Patrick X` / `Steve Weichert` / `Michele Baroi` | bare `KP` / `Pat` / `Steve` / `Michele` |
| 0002 (KP) | `kp` ✅ | `kevin` ❌ **dead** | `kp` ✅ |
| 0003 (Pat) | `pat` ✅ | `patrick` ❌ **dead** | `pat` ✅ |
| 0005 (Steve) | `steve` ✅ | `steve` ✅ | `steve` ✅ |
| 0009 (Michele) | `michele` ✅ | `michele` ✅ | `michele` ✅ |

**Coverage by shape:**
- Shape A (nickname-first): 4/4 ✅ — exactly the convention encoded in the existing test at `Tests/test_recap_verifier_v1.py:258-262`
- Shape B (legal-first for KP/Pat): 2/4 — Steve/Michele covered; KP/Pat dead
- Shape C (bare nickname): 4/4 ✅

**Actual shape (observed under unauth, step 4):** All 10 franchises —
`owner_name` key **absent**. Functionally a null-shape: the loader
returns `{fid: ""}` (or does not populate the fid at all), and pass-4
processes empty-string owners as `re.findall(r"\w+", "")` → `[]` →
`continue`. None of the four critical franchises receives an alias
under current conditions. This reproduces the attribution-failure root
cause identified in the 2026-04-20 APPROVED_STREAK memo.

**Actual shape (authenticated):** Deferred to step 5. Decision rule
below selects Option A, Option B, or a conditional recommendation
based on this column once filled.

---

## Decision points for the population pass

### Option A — Re-ingest with auth, trust MFL values

**Pros:**
- Simplest. Zero code change. Existing ingest path verified correct
  (`_run_franchises_ingest.py:134, 154-164`).
- Append-only discipline respected.
- Works for future seasons automatically.

**Cons:**
- **Dead-alias risk for KP and Pat under shape B.** Pass-4 produces
  `kevin` / `patrick` — the league never uses these → no resolution of
  F3 or F6-KP-leg.
- Requires MFL credentials in env for ongoing ingests.
- **Silent HTTP-200 gap (risk #2):** if current rows reflect
  empty-owner_name 200s, unauth re-ingest reproduces the gap.
  **Confirmed active by step 4** in its stronger key-absent form.

**Blast radius:** depends on step 5. Guaranteed 2/4 resolution
(Steve, Michele). KP and Pat contingent on MFL's stored convention.

### Option B — Re-ingest + nickname curation layer

**Pros:**
- Captures MFL-as-source-of-truth AND league-used short-forms.
- Resolves every dead-alias case.
- Preserves ingest as source for the legal-name field.

**Cons:**
- Schema decision required: column on `franchise_directory`
  (`owner_nickname`) vs separate table (`franchise_nicknames` keyed by
  `(league_id, franchise_id)`) vs override map (config file).
- Code change in `_build_reverse_name_map` — pass 5, or modify pass 4
  to prefer nickname-over-owner-first-word.
- Scope escalation beyond pre-read → distinct brief for schema + code
  + regression test.

**Blast radius:** covers every resolvable case. Cost is a medium-sized
follow-up brief.

### Option C — Curated-only, ignore MFL

**Pros:**
- Total control over alias values.

**Cons:**
- **Breaks append-only discipline** — curation isn't ingest.
- Maintenance burden for every roster change.
- Disconnects `owner_name` from MFL — adapter-contract violation per
  the Platform Adapter Contract Card.
- Misaligned with frozen-architecture rule.

**Blast radius:** covers everything at architecture cost. Not
recommended.

---

## Decision rule (apply after filling step 6)

- Step 5 shows MFL returning **shape A or C for all 4 critical
  franchises** → **Option A**.
- Step 5 shows MFL returning **shape B for KP or Pat** → **Option B**
  (Option A alone leaves known-bad F3/F6-KP cases unresolved).
- Step 5 is **DEFERRED** → memo ships with decision conditional
  (Option A if shape A/C; Option B if shape B). Final decision in the
  session that runs step 5.
- **Option C is not recommended** regardless of step 5 outcome.

**Applied:** Step 5 DEFERRED → this memo ships with the conditional
recommendation. Both Option A and Option B require auth env; the
A-vs-B choice is decided by the authed probe when run. A third
outcome — step 5 also returning EMPTY for the critical franchises —
would reopen scoping: Option A becomes impossible, Option B's
MFL-backed half collapses to a non-MFL nickname source, and Option C's
architectural cost becomes the only remaining option. This is
unlikely (MFL's business centers on owner management) but flagged.

---

## Named downstream-blocker risks

### Risk 1 — First-word extraction dead-alias (Option A contingency)

`_build_reverse_name_map` line 395-398 takes `re.findall(r"\w+",
owner)[0].lower()`. If MFL stores a legal name where the league-used
short-form is a different token (Kevin → KP, Patrick → Pat), pass-4
creates the wrong alias. Specific known-failure cases: F3 (Pat),
F6-KP-leg (KP). **Load-bearing on step 5's KP and Pat classifications.**

### Risk 2 — Silent HTTP-200 auth gap

`client.py:147-155` retries with auth only on `status_code != 200`. If
MFL serves 200 with `owner_name` stripped to empty for unauthenticated
callers (documented MFL behavior for some league privacy settings), the
client accepts silently. If current `franchise_directory` rows were
written from such unauth 200s (step 3 reveals this via `raw_json`),
then **re-ingest under Option A requires explicit auth env vars** —
re-running the same ingest command without credentials reproduces the
empty result. The retry condition does not catch this response class.

**Confirmed active (step 4).** The observed form is slightly stronger
than this risk's original description: MFL returns HTTP 200 with the
`owner_name` key **absent entirely**, not empty-strung. Operationally
identical (the `!= 200` gate does not fire), but worth recording for
future diagnostic fidelity — any future check for "did owner_name
arrive?" must check for key-presence, not just non-empty value.

### Risk 3 — Collision suppression in pass 4 (line 406)

If two franchises' owner first-words collide, neither gets an alias
(`if len(fids) != 1: continue`). Unlikely in this league given
league-used short-forms are all distinct (KP, Pat, Steve, Michele,
Stu, Eddie, Miller, Robb, Ben, Brandon). Step 6 classification will
surface any collisions if present. Flagged for completeness.

Under current (unauth) conditions step 6 cannot surface collisions —
all 10 are EMPTY. Re-evaluate after step 5.

### Risk 4 — Pass-4 non-override (line 409)

`if alias not in reverse:` — pass-4 skips if a lowercased owner
first-word already matches a pass-1/2/3 alias. For this league's
10-franchise roster, no such collision exists for any of KP, Pat,
Steve, Michele. **Not a blocker;** flagged for completeness.

### Risk 5 — Test-encoded nickname-first hypothesis is untested against reality

The existing regression test at `Tests/test_recap_verifier_v1.py:258-262`
hard-codes `owner_map = {"F_CAVALLINI": "Michele Baroi", "F_KP": "KP
Paradis", "F_WEICHERT": "Steve Weichert"}` and asserts `kp`, `steve`,
`michele` appear in the reverse map. **The test passes regardless of
what MFL actually stores** — it's an isolated unit test, not a
production-data integration test. If MFL stores `Kevin Paradis` for
franchise 0002, this test still passes green (literal `"KP Paradis"`
input) while production's pass-4 produces `kevin` (dead). **Step 5 is
the empirical check for whether that test's encoded convention
matches reality.**

---

## Dependencies / blockers for the population pass itself

- **MFL credentials in env** (`.env.local`). Step 5 may need to defer
  to a follow-up session if creds aren't available. **Confirmed:
  currently deferred.**
- **Decision on Option A vs B** — made here against step 5 evidence;
  executed in a separate pass.
- **If Option B is chosen:**
  - Schema design (column on `franchise_directory` vs separate table
    vs config file).
  - Code change in `_build_reverse_name_map` — pass 5 or pass-4
    override.
  - Regression test exercising the nickname path for KP or Pat where
    shape B reveals the dead-alias case.

---

## Production callsites verified (no callsite gating required)

Two callers of `_load_franchise_owner_names` exist; both transparently
pick up populated data:
- `src/squadvault/core/recaps/verification/recap_verifier_v1.py:2944` —
  canonical `verify_recap_v1` entry point (lifecycle gate)
- `scripts/verify_season.py:112` — batch season-scan script

No unit test pins `_load_franchise_owner_names` returning `{}` — the
one live-DB-mirror test at `Tests/test_recap_verifier_v1.py:2462`
passes literal `{}` for `owner_map` rather than calling the loader, so
it does not regress when the DB is populated. All `"<alias>" not in
reverse` assertions (lines 272, 292, 301) use literal inputs and remain
valid.

---

## Out of scope (what this pass did NOT do)

- No DB writes (no INSERT/UPDATE/DELETE).
- No ingest runs.
- No code changes to `src/` or `Tests/`; no new files in `scripts/`.
- No per-franchise nickname curation decisions.
- No amendments to the 2026-04-18 or 2026-04-20 memos.
- No touching of Brief #1 (`_POSSESSIVE_OBJECT_WIN_STREAK` widening) or
  Brief #2 (proximity substring hardening).
- The four untracked diagnostic scripts under `scripts/` were not
  touched.

---

## Out of brief: adjacent alternatives (if time permits)

Per brief's "ADJACENT ALTERNATIVES", ordering preference:

1. **Alt 3** — recover tarball-gap rows from 04-19 scan (rows 10, 35,
   42, 56, 105). Smallest; re-run `sv_digit_prefix_scan.sh`.
2. **Alt 1** — ruff Tests/ cleanup (238 pre-existing errors;
   auto-fixable; Thread-1 open item).
3. **Alt 2** — `waiver_bids.py` ingest promotion (medium; follows
   ad3cb98 pattern).

Each independent of the pre-read.
