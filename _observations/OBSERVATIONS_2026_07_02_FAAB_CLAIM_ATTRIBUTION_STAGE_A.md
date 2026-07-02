# Observation - 2026-07-02 - FAAB_CLAIM Attribution, Stage A (deterministic)

**Session type:** EXECUTE (Claude Code, Opus 4.8). Diagnosis-only (D-W): no edits to verifier,
prompts, Tier-2 policy, data layer, or any source file; prod DB opened read-only; zero
generation API calls. Follow-on to the Unit A7 baseline (memo squash `1948de4`).
**Brief:** pasted FAAB_CLAIM Attribution Stage A brief (2026-07-02); the brief file is not
committed in-repo - the pasted content is the source of record for this session.

## 0. Ritual / provenance

- **HEAD:** `e949c13` (verified `git log -1`).
- **Repo identity:** engine confirmed (`scripts/recap_artifact_regenerate.py` present).
- **Standard trio:** ruff `check src/squadvault/` clean; mypy clean (163 files); pytest
  green (2380 passed, 2 skipped; the 2 warnings are the in-test empty-key fixture, unrelated).
- **Prod DB start hash:** `effb00e54fce5c3860423a08338b8711bc96229172452888c97823bc8c5af36b`
  (`.local_squadvault.sqlite`).
- **Prod DB end hash:** `effb00e54fce5c3860423a08338b8711bc96229172452888c97823bc8c5af36b`
  (re-verified at session end - **identical to start hash; DB untouched**).
- All probes opened the DB via `file:...?mode=ro` (read-only); a write attempt was rejected
  (`attempt to write a readonly database`) - confirmed before any probe ran.

## 1. Inherited cell list (verbatim from the A7 memo R2 short-circuit ledger)

The 11 FAAB_CLAIM Tier-2 short-circuit cells (extracted from
`_observations/OBSERVATIONS_2026_07_02_UNIT_1_4_FRESH_GENERATION_BASELINE.md`, section 3.2):

`2019 wk5 · 2020 wk12 · 2022 wk5 · 2023 wk5 · 2023 wk12 · 2024 wk2 · 2024 wk4 · 2024 wk9 ·
2024 wk11 · 2024 wk12 · 2024 wk14`

Note (per brief + Gate-2 deletion): the A7 baseline scratch DB was deleted, so the per-attempt
rejected prose does not exist. This session works only from the memo, code at HEAD, and prod data.

## 2. Code reading - verifier side (file:line at HEAD `e949c13`)

**FAAB_CLAIM check** - `src/squadvault/core/recaps/verification/recap_verifier_v1.py`:
- Ground truth loader `_load_faab_bids` (`:4432`): reads **all WAIVER_BID_AWARDED events for
  the whole season** from `v_canonical_best_events` (`:4446`), keyed player_id -> [bid_amount].
  Not week-scoped.
- Detection loop (`:4533`): for each `$NN(.NN)` (`_FAAB_DOLLAR_PATTERN`, `:4416`) that has a
  FAAB keyword (faab|waiver|pickup|claim|acquisition|investment|grabbed|snagged|spent|bid,
  `:4421`) within `_FAAB_KEYWORD_WINDOW=30` chars (`:4429`, `:4539`), with a "draft" context
  suppressor (`:4546`).
- **Player binding by proximity** (`:4558-4569`): binds the dollar to the *nearest* known
  player name within 100 chars (`best_name`, `best_dist`). This is a heuristic, not a claim
  parse - it can bind a dollar to a player the sentence did not intend.
- **Two HARD-fail branches:** (a) nearest player has **no** WAIVER_BID_AWARDED record this
  season -> "not acquired via FAAB" (fabrication) (`:4582-4597`); (b) player has bids but the
  amount is off by more than the +/-1.0 tolerance (`:4598-4612`).

**Tier-2 short-circuit** - `src/squadvault/recaps/weekly_recap_lifecycle.py`:
- `_NO_RETRY_CATEGORIES = frozenset({"FAAB_CLAIM", "NUMERIC_UNANCHORED"})` (`:1288`).
- On any hard failure whose category is in that set, the retry loop **breaks immediately** to
  facts-only (`:1433-1455`): "same context produces same hallucination - correction feedback
  won't fix it." This is why one FAAB_CLAIM ends the cell at facts-only with no further
  attempts. (Described only, per D-W; not evaluated.)

## 3. Code reading - assembly side (does FAAB reach the prompt?)

Every FAAB **dollar** that can reach the prompt originates from **WAIVER_BID_AWARDED** - the
same source the verifier checks. Three paths:

1. **Deterministic weekly bullets** - `src/squadvault/core/recaps/render/deterministic_bullets_v1.py`:
   `WAIVER_BID_AWARDED` -> `"{team} won {player} for ${bid} on waivers."` (`:263-268`, amount
   from `bid_amount`). `TRANSACTION_FREE_AGENT` -> `"{team} added {player} (free agent)."`
   with **no amount** (`:270-273`). All other `TRANSACTION_*` (incl. `TRANSACTION_WAIVER`,
   `TRANSACTION_BBID_WAIVER`) hit the `else` branch and are **skipped** (`:310-314`) - they
   produce no bullet and are invisible to the model.
2. **Season writer-room context** - `weekly_recap_lifecycle.py:1030-1053` calls
   `derive_faab_spending` / `derive_faab_acquisitions` / `derive_faab_roi`
   (`core/recaps/context/writer_room_context_v1.py:128/222`, both reading
   `WAIVER_BID_AWARDED`, `:152/:239`), rendered with player+amount, cumulative
   `through_occurred_at=window_end`. So in a WBA-bearing season, real FAAB acquisitions reach
   the prompt **even in a week that selected zero WAIVER_BID_AWARDED bullets**.
3. **Player narrative angles** - `weekly_recap_lifecycle.py:910` ->
   `player_narrative_angles_v1.detect_player_narrative_angles_v1` (FAAB detectors 17/18,
   `:1887+`), loading season WAIVER_BID_AWARDED (`:564/:581`).

Event types allowlisted for weekly recaps include both `WAIVER_BID_AWARDED` and
`TRANSACTION_BBID_WAIVER` (`config/recap_event_allowlist_v1.py:8-9`), but only the former is
rendered with a dollar amount.

**Structural consequences.**
- The verifier is **not stricter** than the assembly on the dollar *value*: both read
  WAIVER_BID_AWARDED `bid_amount`. A faithful transcription of a surfaced FAAB bullet/angle
  passes. So H2-by-value is structurally unsupported.
- Two failure mechanisms remain live and are **indistinguishable without the rejected prose**:
  - *H1 (invent-when-starved):* the model attaches an invented dollar to a name that carries
    no amount in the prompt - a `TRANSACTION_FREE_AGENT` add (surfaced with no $) or a matchup
    player - producing the verifier's "no WAIVER_BID_AWARDED record" fabrication branch.
  - *H2 (verifier over-strictness):* the proximity binder (`:4558-4569`) attaches a correct
    dollar to the *wrong* nearest player who has no WBA record -> false "no record".

## 4. Data probes (read-only; SQL verbatim)

Ground-truth season WBA and per-cell selection are the two independent columns (per hazard 3:
"FAAB data exists" != "FAAB data reaches the prompt").

**Probe A - season WAIVER_BID_AWARDED (verifier ground truth):**
```sql
SELECT COUNT(*) FROM v_canonical_best_events
WHERE league_id='70985' AND season=? AND event_type='WAIVER_BID_AWARDED';
```
Result: 2019 -> **0**, 2020 -> **0**, 2022 -> 46, 2023 -> 48, 2024 -> 65.

**Probe B - per-cell selection into the week's recap (what reaches bullets):**
```sql
SELECT counts_by_type_json, json_array_length(canonical_ids_json)
FROM recap_runs WHERE league_id='70985' AND season=? AND week_index=?;
```
Verbatim `counts_by_type_json` per cell in the table below. (A separate per-week canonical
probe keyed on `json_extract(payload_json,'$.week')` returned all-zero and is discarded as a
payload-key mismatch; `recap_runs.counts_by_type_json` is the authoritative selection ledger.)

| cell | season WBA (truth) | week WBA (bullet $) | FREE_AGENT (no $) | other txn selected | FAAB reaches prompt? |
|---|---:|---:|---:|---|---|
| 2019 wk5 | 0 | 0 | 5 | TRANSACTION_WAIVER 3 | **NO** (0 season WBA) |
| 2020 wk12 | 0 | 0 | 1 | TRANSACTION_WAIVER 3 | **NO** (0 season WBA) |
| 2022 wk5 | 46 | 4 | 13 | - | YES (bullets + writer-room) |
| 2023 wk5 | 48 | 5 | 8 | - | YES (bullets + writer-room) |
| 2023 wk12 | 48 | 1 | 5 | - | YES (bullets + writer-room) |
| 2024 wk2 | 65 | 8 | 7 | TRANSACTION_BBID_WAIVER 5 | YES (bullets + writer-room) |
| 2024 wk4 | 65 | 9 | 5 | TRANSACTION_BBID_WAIVER 7 | YES (bullets + writer-room) |
| 2024 wk9 | 65 | 2 | 11 | TRANSACTION_BBID_WAIVER 2 | YES (bullets + writer-room) |
| 2024 wk11 | 65 | 7 | 5 | TRANSACTION_BBID_WAIVER 5 | YES (bullets + writer-room) |
| 2024 wk12 | 65 | 1 | 1 | TRANSACTION_BBID_WAIVER 1 | YES (bullets + writer-room) |
| 2024 wk14 | 65 | 0 | 1 | TRANSACTION_WAIVER 6 | YES (season writer-room/angles only; no weekly WBA bullet) |

Every cell also carries WEEKLY_MATCHUP_RESULT 5 (omitted above for brevity).

## 5. Classification (pre-declared decision rule; per-cell evidence)

| cell | class | evidence |
|---|---|---|
| 2019 wk5 | **H1** | Season WBA = 0: no WBA bullet, no FAAB writer-room/angle possible. Verifier ground truth empty -> any FAAB-$ sentence hits the "no record" branch. Data absent -> invention. |
| 2020 wk12 | **H1** | Season WBA = 0: identical to above. Data absent -> invention. |
| 2022 wk5 | **H3** | FAAB present + surfaced (4 WBA bullets, season writer-room); verifier not stricter by value; invent-on-FA-add (13 FA names, no $) vs proximity-misbind both live. Needs prose. |
| 2023 wk5 | **H3** | Present + surfaced (5 WBA bullets); same two mechanisms unresolved without prose. |
| 2023 wk12 | **H3** | Present + surfaced (1 WBA bullet + season writer-room); unresolved without prose. |
| 2024 wk2 | **H3** | Present + surfaced (8 WBA bullets); unresolved without prose. |
| 2024 wk4 | **H3** | Present + surfaced (9 WBA bullets); unresolved without prose. |
| 2024 wk9 | **H3** | Present + surfaced (2 WBA bullets + 11 FA names no $); unresolved without prose. |
| 2024 wk11 | **H3** | Present + surfaced (7 WBA bullets); unresolved without prose. |
| 2024 wk12 | **H3** | Present + surfaced (1 WBA bullet); unresolved without prose. |
| 2024 wk14 | **H3** | No weekly WBA bullet, but season writer-room/angles surface real FAAB (season WBA=65) -> "surfaced", not starved; mechanism unresolved without prose. |

**Counts: H1 = 2 · H2 = 0 · H3 = 9.** All 11 classified; none dropped.

## 6. Closing - (b) Stage B required

Attribution is **partially** established and cannot be completed deterministically:

- **Established (no prose needed):** For the 2 zero-data cells (2019 wk5, 2020 wk12) the failure
  is unambiguously **H1** (invent-when-starved: FAAB dollars fabricated where no WAIVER_BID_AWARDED
  data exists in the season at all). The responsible layer for these is **data/assembly**
  (nothing to surface), not the verifier.
- **Structural finding:** All prompt-side FAAB dollars originate from WAIVER_BID_AWARDED, the
  verifier's own source, so the verifier is not over-strict *by value*. The remaining risk
  surfaces are (i) the amount-less `TRANSACTION_FREE_AGENT` adds co-surfaced with FAAB context,
  and (ii) the verifier's nearest-player-within-100-chars proximity binder.
- **Unresolved (9 H3 cells):** distinguishing H1-invention from H2-proximity-misbind requires
  the rejected prose, which no longer exists for the A7 run.

**Exact capture list Stage B must record** (per implicated cell, from a fresh instrumented
generation run - config-as-is, scratch DB, SQUADVAULT_PROMPT_AUDIT retained, prose NOT deleted):
1. The verbatim FAAB sentence(s) the model emitted that the verifier failed.
2. Each triggering dollar amount and the player name the *sentence* attributes it to.
3. The verifier's `best_name` binding for that dollar (the nearest-player it actually compared).
4. Whether that `best_name` player has a WAIVER_BID_AWARDED record (tests invention) and whether
   a *different* nearby player carries exactly that dollar as a real WBA (tests proximity-misbind).
5. The event type of the model-named player's pickup, if any (FREE_AGENT / BBID_WAIVER / none).

These five fields deterministically separate H1 from H2 per cell; no further code reading is
needed. No fix is designed here (D-W): the candidate responsible layers named above are the
prompt/assembly (FA adds surfaced without amounts; starvation in zero-WBA seasons) and the
verifier proximity binder - Stage B's capture decides which.

## Appendix (non-load-bearing, exploratory)

- Discarded probe: a per-week canonical FAAB probe was run
  (`SELECT COUNT(*) ... WHERE event_type=? AND CAST(json_extract(payload_json,'$.week') AS INTEGER)=?`)
  and returned all-zero for every cell - a payload-key mismatch (the week is not stored under
  `$.week` in these payloads), not a data-absence signal. It was discarded; the per-week
  selection facts in section 4 come from `recap_runs.counts_by_type_json` (the authoritative
  selection ledger) instead.
- `TRANSACTION_BBID_WAIVER` is allowlisted (`recap_event_allowlist_v1.py:8`) but never rendered
  to a bullet (`deterministic_bullets_v1.py:310-314`); it and `TRANSACTION_WAIVER` are invisible
  to the model. Whether the canonical model should treat BBID-waiver as a FAAB award is a
  data-modeling question, not part of this attribution.
- Prod carries 365 historical `prompt_audit` rows, but these are prior real-run artifacts, not
  the A7 baseline run (that ran on the deleted scratch copy); they are a different population and
  were not used to classify A7 outcomes.
- Tier-2's immediate short-circuit means each of these 11 cells failed on the *first* FAAB_CLAIM
  regardless of other content quality - consistent with the A7 R2 ledger (attempts 1-3 varied).
