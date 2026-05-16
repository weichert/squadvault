# 2021 DRAFT_PICK Gap -- Sub-variant Closed (Sub-B2 Confirmed)
## SquadVault | Phase 11 | 2026-05-16

**Predecessor:** OBSERVATIONS_2026_05_16_DRAFT_PICK_2021_GAP_CHARACTERIZATION.md (3a35308)
**Status:** Fully closed. Not recoverable.

---

## Finding

Live re-fetch of the MFL 2021 transactions export:

  URL: https://www44.myfantasyleague.com/2021/export?TYPE=transactions&L=70985&JSON=1

  Response: 208 transactions. Types seen:
    FREE_AGENT: 104
    BBID_WAIVER: 54
    LOCK_ALL_PLAYERS: 18
    BBID_AUTO_PROCESS_WAIVERS: 13
    LOAD_ROSTERS: 11
    TRADE: 4
    WAIVER: 2
    AUTO_PROCESS_WAIVERS: 2

  Auction/draft transactions: zero.

**Sub-B2 confirmed:** MFL's 2021 transactions export contains no auction pick
records. The gap is upstream of the ingest -- it is not a filter issue and not
a code defect. There is no data to fetch.

**Sub-B1 ruled out:** No transactions of any draft or auction shape appear in
the response. There is no type mismatch to correct; the filter is irrelevant
when the source returns nothing to filter.

**Not recoverable via re-ingest.** MFL does not expose 2021 auction pick
records through the transactions export endpoint. The cause upstream of MFL
(whether auction picks were never entered, entered under a different MFL
product path not surfaced by this endpoint, or lost) is unknown and out of
scope for SquadVault.

---

## Incidental observation

MFL returns raw types without the TRANSACTION_ prefix (e.g., FREE_AGENT, not
TRANSACTION_FREE_AGENT). The TRANSACTION_ prefix visible in canonical_events
is added by the ingest normalisation layer. This is expected and correct; no
action.

---

## Standing item disposition

The 2021 gap entry in Roadmap v2 section 7.3 is now fully closed:
- Gap confirmed: A2 Step 1 (2da7f21)
- Finding A ruled out: founder confirmation (this session)
- Finding C ruled out: free-agent transaction coverage (3a35308)
- Finding B confirmed: storage-layer probe (3a35308)
- Sub-B2 confirmed, Sub-B1 ruled out: live re-fetch (this commit)
- Not recoverable: confirmed

No further investigation warranted.

---

Filed: 2026-05-16
HEAD at filing: 86ed162
