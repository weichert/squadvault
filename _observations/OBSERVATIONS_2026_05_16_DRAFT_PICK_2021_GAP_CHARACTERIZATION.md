# 2021 DRAFT_PICK Gap Characterization
## SquadVault | Phase 11 | 2026-05-16

**Status:** Finding characterized -- high confidence at storage layer
**Classification:** Finding B (fetch ran; zero auction events returned by MFL)
**Code change warranted:** No
**Recovery path:** Operational re-fetch against MFL 2021 transactions endpoint
**Preceding memo:** OBSERVATIONS_2026_05_14_PHASE_11_ROADMAP_SEASONS_COUNT_REVISION.md section 9.3

---

## 1. What was known entering this session

A2 Step 1 (OBSERVATIONS_2026_05_13_PHASE_11_A2_DECISION_READINESS_STEP_1_PROBES.md
section 4.1) established empirically that 2021 has zero DRAFT_PICK events
despite normal WEEKLY_PLAYER_SCORE and WEEKLY_MATCHUP_RESULT coverage. The gap
was recorded as confirmed; its cause was uncharacterized. Three candidates:

(a) Non-auction format in 2021 -- league ran a snake or keeper draft.
(b) Different MFL event_type -- auction conducted but under a type the filter
    does not match.
(c) Ingest gap -- the fetch was never attempted or returned an error.

The founder confirmed the league has run auction drafts exclusively for longer
than 2021, ruling out candidate (a) definitively.

---

## 2. Investigation probes run (in sequence)

Probe 1 -- DRAFT_PICK per season: zero in 2021; 150-180 in every other
auction year (2018-2020, 2022-2025). Clean gap, not sparse data.

Probe 2 -- draft/transaction-adjacent event types in 2021 (canonical_events):
No AUCTION, DRAFT, PICK, KEEPER, STARTUP, SNAKE, or SALARY event types. The
pre-season window shows only TRANSACTION_LOAD_ROSTERS (11 events, Aug 13-14).
Note: TRANSACTION_LOAD_ROSTERS also appears in auction years (e.g., 2018 has
one stray event alongside 153 DRAFT_PICK records); it is an MFL housekeeping
event, not a snake-era exclusive. This probe initially suggested Finding A but
that was withdrawn on founder confirmation.

Probe 3 -- league_id chain integrity: all 16 seasons stored under league_id
70985. 2021 has 2500 events -- normal coverage. No league_id-level gap.

Probe 4 -- canonical_events schema: no raw payload column; original MFL type
is stored in memory_events.payload_json under the key mfl_type.

Probe 5 -- memory_events for known 2018 DRAFT_PICK records (id 3740, 3741):
mfl_type=AUCTION_WON, source_url prefix https://www44.myfantasyleague.com/2018/
export?TYPE=transacti... The filter condition ("AUCTION" in t) correctly passes
AUCTION_WON. The ingest filter is not defective.

Probe 6 -- 2021 memory_events by external_source and event_type: zero
draft/auction entries. The full 2021 memory_events inventory is:
  MFL | WEEKLY_PLAYER_SCORE: 2227
  MFL | TRANSACTION_FREE_AGENT: 104
  MFL | WEEKLY_MATCHUP_RESULT: 78
  MFL | WAIVER_BID_AWARDED: 41
  MFL | TRANSACTION_LOCK_ALL_PLAYERS: 18
  MFL | TRANSACTION_BBID_AUTO_PROCESS_WAIVERS: 13
  MFL | TRANSACTION_LOAD_ROSTERS: 11
  MFL | TRANSACTION_TRADE: 4
  MFL | TRANSACTION_WAIVER: 2
  MFL | TRANSACTION_AUTO_PROCESS_WAIVERS: 2

---

## 3. Characterization

**Finding B confirmed at the storage layer -- high confidence.**

The 104 TRANSACTION_FREE_AGENT events in 2021 memory_events prove that
get_transactions(year=2021) was called and returned data. The ingest ran.
Finding C (fetch never attempted) is ruled out.

Zero auction events are stored in memory_events for 2021. The filter in
auction_draft.py (line 148: if "AUCTION" not in t and "DRAFT" not in t:
continue) would have dropped any transaction whose MFL type does not contain
either string. AUCTION_WON is the confirmed type for 2018-2020 and 2022-2025
and would pass the filter. Two sub-explanations remain:

Sub-B1 -- MFL returned 2021 auction picks under a non-matching type. This
would be unusual given AUCTION_WON is consistent across all other years and
no unrecognized draft-adjacent type appears in the 2021 memory_events inventory.
Confidence: low.

Sub-B2 -- MFL's transactions export returned no auction data for 2021. This
could occur if the 2021 auction was conducted in a part of the MFL product
that does not write to the standard transactions export endpoint, or if the
per-year MFL league_id for 2021 was not the one queried. Confidence: medium.

The two sub-variants cannot be distinguished without a live re-fetch.

**Finding A (non-auction format):** Ruled out by founder confirmation.
**Finding C (ingest never ran):** Ruled out by 2021 free-agent transaction
coverage in memory_events.

---

## 4. Recoverability

Conditionally recoverable. If MFL retains the 2021 auction transaction data
(which is likely but not guaranteed for a 5-year-old season), re-running the
transactions ingest for 2021 and inspecting the raw response would resolve the
sub-variant and either recover the picks (Sub-B1: filter expansion) or confirm
MFL does not expose them (Sub-B2: not recoverable).

This is an operational re-fetch task, not a code change. No code change is
warranted until the re-fetch confirms Sub-B1 (at which point a targeted filter
expansion would be a small, well-scoped fix).

---

## 5. Code assessment

The ingest filter in auction_draft.py is not defective. It correctly passes
AUCTION_WON (confirmed) and correctly excludes non-draft transaction types.
If Sub-B1 is confirmed by re-fetch, the fix is a narrow filter expansion at
line 148 -- a one-line change after characterization, not this session.

No code change this session.

---

## 6. Impact on the surface inventory

A2 (Draft History Vault): unaffected. The 7-season scope (2018-2020,
2022-2025) stands. The gap cause is now partially characterized (Finding B;
sub-variant open). No spec revision required.

Roadmap v2 standing items: the 2021 gap cause is characterized to the extent
the local DB permits. The standing-items entry should record Finding B
confirmed, sub-variant open, re-fetch needed to close.

---

## 7. Confidence summary

High confidence: the gap is a fetch-layer issue, not a code defect. The
ingest ran for 2021; zero auction events were returned or stored. Finding A
and Finding C ruled out.

Medium confidence: Sub-B2 (MFL API returned no auction data) is the more
parsimonious explanation given the consistent AUCTION_WON type in all other
years.

Unresolved: sub-variant (B1 vs B2) requires live re-fetch to close.

---

## 8. Recommended next action (low priority)

Re-run get_transactions(year=2021) against MFL, capture the raw response,
and inspect what transaction types are present for the pre-season window
(August 2021). If AUCTION_WON records appear: filter expansion is the fix.
If no auction records appear: the gap is upstream in MFL and not recoverable
via re-ingest. This is a future operational task; no session target set.

---

Filed: 2026-05-16
Predecessor chain: A2 Step 1 section 4.1 (D2-alpha) at 2da7f21;
Roadmap seasons-count revision section 9.3 at 143e65a (HEAD entering session)
