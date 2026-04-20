# Step 5 owner-name probe — auth-path blocker

**Date:** 2026-04-21
**Scope:** Characterization. No DB mutations, no ingest runs, no code changes.
Documents an empirically surfaced blocker that invalidates the decision rule's
applicability this pass.
**HEAD at observation-time:** `83ea9d3` — Phase 10 audit query: tarball-gap row recovery.
**Follows:** `ecbc1d4` — owner-name population pre-read (2026-04-21).

---

## Summary

Executed the 04-21 pre-read's Step 5 (authenticated MFL probe) against PFL Buddies
L=70985 for 2025. Probe ran cleanly — HTTP 200, valid JSON, 10 franchises returned —
but all 10 `owner_name` fields were `null`. A byte-identical unauthenticated `curl`
against the same URL returned byte-identical output, confirming the probe never
exercised auth.

**Root cause (confirmed at HEAD source, not inferred):** `MflClient.get_league_info`
uses a reactive auth pattern at `src/squadvault/mfl/client.py:140-158`: it issues an
unauthenticated GET first, and only retries with credentials if `status_code != 200`.
MFL serves 200-with-null-owners to unauthenticated callers for this league in 2025,
so the retry gate never fires. Credentials passed to the client constructor are
carried in the object but never placed on the wire.

**Consequence for the 04-21 decision rule:** all three branches (Option A / Option B /
reopen scoping) condition on a probe that actually exercised auth. This probe did not.
Applying the "all-EMPTY → reopen scoping" branch would record a false finding — MFL's
auth-conditioned response is still unknown. Per brief discipline, **no decision is
called this pass**, and the 04-21 pre-read's Step 5 DEFERRED slot remains effectively
unfilled.

**Filename divergence note:** the session brief's template named this memo
`OBSERVATIONS_2026_04_21_OWNER_NAME_STEP5_DECISION.md`. Renamed to `_STEP5_AUTH_BLOCKER`
because no decision was reached and a `_DECISION`-suffixed artifact would mislead future
readers scanning filenames.

---

## SHA-256 drift check

At session open, matching the session brief:

| File | SHA-256 | Brief match |
|---|---|---|
| `src/squadvault/core/recaps/verification/recap_verifier_v1.py` | `745d1f8ad9dfadd0c5c2cb935611839b0ca1d20e00b89c922aff27190e9f8752` | ✅ |
| `src/squadvault/ingest/franchises/_run_franchises_ingest.py` | `0b1ea91a47c37cbbe6b83915bfed19d3bd5a6b9da50c2973f866d51fc562c70f` | ✅ |
| `src/squadvault/mfl/client.py` | `1ea40f247a1fbe4eac3370a69367e3bd5e46fd4ceefed10ecbb55667f985142d` | ✅ |
| `src/squadvault/mfl/historical_ingest.py` | `4210016b5095985e7661320db4edc7aae768d1fedbaf824232e3bf0d5773e843` | ✅ |

No drift. Findings below are grounded in the committed HEAD.

---

## Evidence

### Probe execution (Step 5, "authenticated")

Command — verbatim from the 04-21 pre-read §5, plus one added `print('SOURCE URL:', url)`
line for provenance:

```python
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
print('SOURCE URL:', url)
for f in franchises:
    print(f.get('id'), repr(f.get('name')), '->', repr(f.get('owner_name')))
"
```

Output:

```
SOURCE URL: https://www44.myfantasyleague.com/2025/export?TYPE=league&L=70985&JSON=1
0001 "Stu's Crew" -> None
0002 "Paradis' Playmakers" -> None
0003 'Purple Haze' -> None
0004 'Eddie & the Cruisers' -> None
0005 "Weichert's Warmongers" -> None
0006 'Miller's Genuine Draft' -> None
0007 "Robb's Raiders" -> None
0008 "Ben's Gods" -> None
0009 'Italian Cavallini' -> None
0010 'Brandon Knows Ball' -> None
```

Source URL contains no `APIKEY` query param, no login-cookie indicator — the bare
export endpoint.

### Unauthenticated curl control

```bash
curl -s "https://www44.myfantasyleague.com/2025/export?TYPE=league&L=70985&JSON=1" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
fs = (d.get('league', {}).get('franchises', {}).get('franchise')
      or d.get('franchises', {}).get('franchise', []))
for f in fs:
    print(f.get('id'), repr(f.get('name')), '->', repr(f.get('owner_name')))
"
```

Output (owner_name column; identical to the probe above for all 10 rows):

```
0001 "Stu's Crew" -> None
...
0010 'Brandon Knows Ball' -> None
```

**Byte-identical to the "authenticated" probe output.** Confirms the probe's auth path
was never exercised.

### Source citation at HEAD 83ea9d3

`src/squadvault/mfl/client.py:140-158`:

```python
def get_league_info(self, year: int) -> tuple[dict[str, Any], str]:
    """
    Fetch TYPE=league export for franchise info and league metadata.

    v1 behavior: same auth pattern as get_transactions.
    """
    url = self.export_url(year, "league")
    resp = http_request_with_retries(self.session, "GET", url)

    if resp.status_code != 200 and self.username and self.password:
        logger.info(
            "MFL unauthenticated request failed (%s); attempting login then retry.",
            resp.status_code,
        )
        self._login(year)
        resp = http_request_with_retries(self.session, "GET", url)

    resp.raise_for_status()
    return resp.json(), url
```

Line 149 is the retry gate. MFL's 200-with-null-owners response fails the gate's first
clause; `_login()` is never called; the unauthenticated response is returned. **This
is structurally the pattern the 04-21 pre-read flagged as Risk 2.**

---

## Answered questions (partial)

- **Q1** (MFL returns `owner_name` unauthenticated?): **No — HTTP 200 with
  `owner_name: null` for all 10 franchises in 2025.** Matches the 04-21 pre-read's
  "Step 4 middle branch" (HTTP 200 with empty owner_name — silent gap, risk #2).
- **Q2** (MFL returns `owner_name` authenticated?): **Still unanswered.** The current
  `MflClient` probe path cannot answer this without forcing auth explicitly.
- **Q3** (per-franchise values): **Not answerable this pass.** Depends on Q2.
- **Q4** (raw_json holds owner_name even though column is empty?): Not probed this
  pass (Step 3 SQL not run; scope was Step 5 only). Re-enters scope once Q2 is resolved.
- **Q5** (older seasons populated?): Not probed this pass (same reason).
- **Q5-derived** (does the decision rule select A, B, or reopen?): **Not applicable.**
  See below.

---

## Decision rule — not applicable

The 04-21 pre-read's decision rule:

- Shape A or C across all 4 critical franchises → Option A
- Shape B for KP or Pat → Option B
- All-EMPTY even under auth → reopen scoping

**All three branches condition on a probe that actually exercised auth.** This probe
did not. Routing the all-None result under "all-EMPTY even under auth → reopen" would
be an improvised branch the rule does not cover — we do not yet know MFL's auth-
conditioned response for this league. Per brief discipline ("Do not improvise a
decision for a shape the rule doesn't cover"), no decision is called. The 04-21
pre-read's Step 5 slot transitions from DEFERRED-for-missing-creds to DEFERRED-for-
auth-path-blocker; the decision remains pending on the next session.

---

## Risk 2 promoted from hypothetical to confirmed

The 04-21 pre-read flagged this exact shape as Risk 2 ("Silent HTTP-200 auth gap")
with the caveat that it required empirical verification. This pass supplies that
verification:

- MFL does serve this 200-with-stripped-owner_name response class for PFL Buddies
  L=70985 in 2025.
- `MflClient.get_league_info` at `client.py:149` does not catch it.
- Credentials in env, credentials in the client constructor — both are structurally
  inert against this response class.

**Consequence for Option A viability:** the 04-21 pre-read's Risk 2 language said
"re-ingest under Option A requires explicit auth env vars." This pass shows that
understates the blocker. Env vars are present; they don't fire auth. **Option A as
the pre-read defined it (plain re-ingest with creds in env) reproduces the empty-
owner_name gap for this league**, because `_run_franchises_ingest` walks through the
same `get_league_info` call with the same reactive-auth gate.

This does not promote Option B by elimination — Q2 is still unanswered, so KP/Pat
dead-alias risk under shape B is still hypothetical. It does mean that whatever
Option A re-ingest would look like cannot be a plain re-run; it needs either a
force-auth change upstream or a probe-established understanding that MFL will serve
populated owner_name under auth for this league.

---

## Collision risk (Risk 3) — deferred

The 04-21 pre-read's Risk 3 (pass-4 first-word-alias collisions across the 10
franchises) cannot be evaluated until real `owner_name` strings are in hand.
Deferred to the session that successfully answers Q2.

---

## Collateral finding — `.env.local` export discipline

`.env.local` contained the three MFL vars as plain `KEY=value` assignments without
`export ` prefix. Plain `source .env.local` set them as shell-local variables but did
not propagate to `os.environ`, causing the probe's first attempt to fail with
`KeyError: 'MFL_SERVER'`. Worked around in-session with `set -a ; source .env.local ;
set +a`.

**Housekeeping:** prepending `export ` to each of the three MFL lines in `.env.local`
fixes this for plain `source` usage going forward. Not a code change (user-machine
local file, not under version control). Filed here for next-session awareness.

---

## Recommended next-session scope

Before re-running Step 5, the probe path needs to force auth independent of HTTP
status. Two directions:

**Option (i) — diagnostic-only probe harness in `scripts/`:**

A one-off probe script that calls `MflClient._login(2025)` explicitly before
`get_league_info`, bypassing the reactive gate. Answers Q2 without touching `src/`.
Follows the untracked-`scripts/diagnose_*.py` pattern already established in this
repo. Lowest blast radius. Recommended as the next session's primary.

**Option (ii) — `src/squadvault/mfl/client.py` change:**

Modify `get_league_info` (and for symmetry `get_players`, `get_transactions`) to
force `_login` when creds are present and a sensitive field (owner_name, or analogous)
comes back null. This is an adapter-layer behavior change; needs its own scoping brief
with test coverage. **Not the next session** unless Option (i) data specifically
motivates it.

**Recommendation:** next session = Option (i). Force-auth diagnostic, answer Q2,
unblock the 04-21 decision rule. If Option (i) shows MFL returns populated
`owner_name` under auth, Option (ii) becomes the scoping question for the session
after that. If Option (i) shows MFL returns null even under auth, the decision rule's
reopen-scoping branch activates cleanly and Option (ii) is irrelevant.

---

## Out of scope (what this pass did NOT do)

- No DB writes (no INSERT/UPDATE/DELETE).
- No ingest runs.
- No code changes to `src/` or `Tests/`.
- No new committed files in `scripts/`.
- No amendment of the 04-21 pre-read or any prior memo.
- No decision called — decision rule is inapplicable given the probe's actual auth
  status.
- Steps 2, 3, 4 of the pre-read's investigation trail (franchise_directory inventory,
  raw_json inspection, unauthenticated MFL probe via curl) were not fully walked; only
  the unauth curl was re-used this session as a control for Step 5. Those steps
  re-enter scope once Q2 is resolved.

---

## Cross-references

- 04-21 pre-read: `_observations/OBSERVATIONS_2026_04_21_OWNER_NAME_POPULATION_PREREAD.md`
  (commit `ecbc1d4`) — this memo's upstream.
- 04-21 reverse-name-map diagnostic: commit `7324ee9` — root of the owner-name thread.

HEAD at observation-time: `83ea9d3`. Test baseline unchanged (no tests run this pass;
no code touched). Staging gate: one file staged. One-topic discipline: Risk 2
confirmation + decision-rule non-applicability + next-session scope named.