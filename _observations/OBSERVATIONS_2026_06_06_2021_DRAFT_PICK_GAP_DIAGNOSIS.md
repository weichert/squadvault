# OBSERVATIONS — 2021 DRAFT_PICK Gap Diagnosis

**Date:** 2026-06-06
**Engine HEAD:** `84564a4` (DRAFT_AUCTION_DOLLAR / Category 13 live)
**Session type:** DIAGNOSTIC ONLY — classification with evidence. No fix, no ledger writes, no bundling.
**League:** PFL Buddies, canonical `70985`.

---

## 1. Confirmed DRAFT_PICK season coverage (the empirical "7")

`DRAFT_PICK` events exist for **seven** auction-era seasons:

| Season | DRAFT_PICK rows |
|--------|-----------------|
| 2018 | 153 |
| 2019 | 150 |
| 2020 | 180 |
| 2022 | 170 |
| 2023 | 170 |
| 2024 | 170 |
| 2025 | 170 |

**2021 is the sole gap** (zero rows). This is the empirical "7" that feeds — but does not
resolve — the Phase 11 `8 -> 7` seasons-count reconciliation (see follow-on 3).

## 2. Stage 1 fork outcome — "export exists" branch

2021 is fully ingested. The canonical view and the raw ledger agree exactly:

    TRANSACTION_FREE_AGENT            104
    TRANSACTION_LOCK_ALL_PLAYERS      18
    TRANSACTION_BBID_AUTO_PROCESS..   13
    TRANSACTION_LOAD_ROSTERS          11
    TRANSACTION_TRADE                 4
    TRANSACTION_AUTO_PROCESS_WAIVERS  2
    TRANSACTION_WAIVER                2
    WAIVER_BID_AWARDED                41
    WEEKLY_MATCHUP_RESULT             78
    WEEKLY_PLAYER_SCORE               2227
    DRAFT_PICK                        (absent)

TRANSACTION/WAIVER families are present; DRAFT_PICK alone is absent. The 2021 transactions
export was fetched and non-empty. **C5 (season/league-id resolution miss) is ruled out.**

## 3. Classification

**C4 — legitimately no auction-draft event data exists in MFL for 2021.**

Zero `DRAFT_PICK` is **correct-by-design**, not a defect. The Category-13 SOFT no-coverage
tier is the **permanent** right answer for 2021. There is nothing to backfill.

C1, C2, C3, C5 are each affirmatively refuted (evidence below).

## 4. Evidence trail (trimmed)

**Matched type vocabulary across the 7 working seasons (Stage 2).** Every working season is
`AUCTION_WON` (plus 2 stray `AUCTION_BID` in 2018). Both contain "AUCTION", clear the
`if "AUCTION" not in t and "DRAFT" not in t` gate, and parse player IDs cleanly from the
`playerid|bid|` transaction field. So when auction rows are present, the deriver captures them.

    AUCTION_BID  2018    2
    AUCTION_WON  2018  151
    AUCTION_WON  2019  150
    AUCTION_WON  2020  180
    AUCTION_WON  2022  170
    AUCTION_WON  2023  170
    AUCTION_WON  2024  170
    AUCTION_WON  2025  170

**2021 transactions re-fetch (read-only; faithful `_extract_type` / `_extract_player_id`).**
208 transactions, full type histogram, zero draft-typed rows:

    n_txns: 208
    types: LOCK_ALL_PLAYERS 18, FREE_AGENT 104, WAIVER 2, AUTO_PROCESS_WAIVERS 2,
           BBID_WAIVER 54, BBID_AUTO_PROCESS_WAIVERS 13, TRADE 4, LOAD_ROSTERS 11
    draftish_count (passes AUCTION/DRAFT gate): 0

There are no auction/draft-typed transactions at all.
- **C2 (type-string miss) refuted:** no draft-like rows exist to fail the substring gate.
- **C3 (player-id parse miss) refuted:** no draftish rows exist to reach the player-id parse.

**2021 draftResults peek (read-only; the C1 discriminator).** The endpoint this pipeline never
ingests returns 200 with a container but no picks:

    http_status: 200
    draftUnit count: 1
    total draftPick rows: 0
    picks with round/pick fields (snake signal): 0
    picks with price/bid/amount fields (auction-in-wrong-endpoint): 0

- **C1 (draft lived in draftResults) refuted:** draftResults is empty. No auction landed in a
  different endpoint; there is no recorded draft of any kind in MFL for 2021.

**2021 league draft-config signal.** `draft_kind = fflm` — a non-standard value whose exact
meaning is **unconfirmed** and deliberately not guessed (see follow-on 1). It does not change
the classification: with zero auction transactions and an empty draftResults, no draft event
data exists in the source ledger regardless of what `fflm` denotes.

## 5. Correction to the session brief's C4 reasoning

The brief's candidate table noted of C4: *"a snake draft is still 'DRAFT'-typed and would yield
DRAFT_PICK rows with bid_amount=None, not zero rows ... Zero rows argues against C4."*

This rests on a wrong premise. In MFL, **non-auction drafts populate the `draftResults`
endpoint, not the `transactions` export**; auctions are what surface as `AUCTION_WON`
transactions. A non-auction year therefore correctly produces **zero** transaction-derived
DRAFT_PICK rows. Zero rows does not argue against C4 — combined with an empty `draftResults`,
it confirms it. The transactions export and `draftResults` are the only two on-platform
sources of draft data; both are empty for 2021.

## 6. What a fix would entail per cause (named, not built)

- **C5** (ruled out): n/a.
- **C2** (refuted): would broaden the type heuristic to accept a 2021-specific draft type
  string — unnecessary; no draft-typed rows exist.
- **C3** (refuted): would extend `_extract_player_id` to a 2021 field shape — unnecessary; no
  draftish rows reach that path.
- **C1** (refuted): would add a read-only `draftResults` ingest path — unnecessary; draftResults
  is empty, so there is nothing to ingest.
- **C4** (the finding): **no fix.** Zero DRAFT_PICK is correct; SOFT is the permanent answer.
  The only action is this documentation.

## 7. Named follow-ons (do not start from this session)

1. **Confirm `draft_kind=fflm`.** Resolve what this MFL value denotes (off-platform draft,
   keeper-only, no draft, etc.). Refines the *narrative* of why 2021 has no auction; does **not**
   change the classification — silence remains correct regardless.
2. **Off-platform draft history — constitutional question.** If a 2021 draft physically occurred
   off-platform, decide whether such history is ever in scope as a separate, clearly-marked
   non-MFL fact source. This would be a deliberate sourcing decision under the
   append-only / no-fabrication invariant, **not** a bug fix.
3. **Phase 11 seasons-count input.** This confirms the auction substrate is empirically **7**
   recorded seasons; the `8 -> 7` drift is correct (2021 had no auction), not data loss. Feeds
   the Phase 11 reconciliation sweep, which remains a separate session.

---

*Diagnostic-only. No code changed. No ledger writes. Re-fetch was read-only and tallied in
memory. Classification: C4 — correct-by-design; SOFT no-coverage is permanent for 2021.*
