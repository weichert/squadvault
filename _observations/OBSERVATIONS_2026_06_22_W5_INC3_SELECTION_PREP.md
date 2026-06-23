# Trophy Room (Unit W.5) Increment 3 - Grants / Accumulations / Fixed - Selection-Prep (memo 1 of 4) - DRAFT

**Date:** 2026-06-22
**Session type:** DECIDE (selection-prep). No repo/DB writes. DRAFT for founder ratification + commit.
**Chain position:** memo 1 of 4 (increment 3). Builds on discharged increments 1-2 (shared architecture, Live Records).
**Anchors:** engine HEAD `0219b30`; frontend `7e0ee94` (Wave 2 discharged; `franchise_season_records` now carries points_against + blowout_wins_60).
**Input:** taxonomy v1.2 - the 27 remaining artifacts (22 per-season grants + Perfect Storm + 4 fixed permanent).

---

## 1. What this memo does

Opens the increment-3 chain and partitions all 27 remaining Trophy Room artifacts by **data availability** -
because that, not design, is what gates this increment. It frames; it does not spec. The strategic finding
below is the thing decision-readiness (memo 2) must rule on.

## 2. The surface

The remaining Trophy Room sections: Annual (11, ex-Belt), Positional (6), Draft/Auction (4), In-Season (1),
Permanent (5). Custody models (no transfer ledger): **per-season grant** (holder = most recent certified
recipient, derived); **accumulating multi-list** (The Perfect Storm, C6); **fixed permanent** (single
immutable fact). All reuse the increment-1 shared architecture; none writes `trophy_custody_events`.

## 3. The partition (the finding)

| Group | Plaques | Data status |
|---|---|---|
| **A - ships now** (8) | #2 Bridesmaid Bouquet (runner-up), #5 The Sieve (max points-against - enabled by Wave 2), #8 The Climb (win-pct YoY), #10 The Banner (best reg-season pct), #11 The Engine (max points-for), #32 Inaugural Champion (2010), #34 Back-to-Back (consecutive champ), #35 The Perfect Storm (0-14 multi-list) | All derivable from existing synced `franchise_season_records` (incl. Wave 2 points-against). No new data. |
| **B1 - small sync extension** (3) | #4 The Cannon (highest single-week franchise score), #12 The Black Rose (highest losing score), #33 One-Point Club (championship-game margin < 2) | Need WEEKLY franchise-level scores - derivable at the engine off `WEEKLY_MATCHUP_RESULT`, not yet synced. Same pattern as Wave 2 (a scoped sync extension). |
| **B2 - a whole new data domain** (15) | #3 Hammer, #6 Benchwarmer, #7 Clairvoyant (C2), #9 Oracle (C2); #13-18 Positional (6); #19-22 Draft/Auction (4); #23 The Lifeline | Need PLAYER / DRAFT / WAIVER / OPTIMAL-LINEUP facts. **None of this exists in the frontend** (confirmed: zero player_score / draft / waiver / lineup tables). The engine has the events (`WEEKLY_PLAYER_SCORE`, `DRAFT_PICK`, `WAIVER_BID_AWARDED`); bringing them to the frontend is a major new sync domain. |
| **Fixed / attested** (1) | #31 The Founder's Seal (all 10 members present since the digital era - a membership statement, not a competition) | A fixed fact - likely founder-attested, not derived. Decision-readiness confirms attested vs derived. |

8 + 3 + 15 + 1 = 27.

## 4. The strategic finding (for decision-readiness to rule)

Increment 3 is not one buildable thing. **8 ship now; 3 need a small weekly-score extension; but 15 - more
than half - sit behind an entire data domain (player/draft/waiver/optimal) that has never touched the
frontend.** That B2 domain is plausibly the largest single data effort remaining in the Trophy Room,
larger than increments 1-2 combined, and it carries its own derivability questions (e.g. the "MFL optimal
indicator" the Benchwarmer/Clairvoyant/Oracle depend on - is it ingested and exact, or silence-over-
speculation territory?). The core decision-readiness ruling: **stage A -> B1 now, and treat B2 as its own
scoped sub-project (or deferral)** rather than letting it balloon increment 3.

## 5. Constitutional notes carried in

- **C1** holder = derived read, never stored. **C6** Perfect Storm = accumulating multi-list (pairs with The
  Floor; same 0-14 data). **C2** The Clairvoyant / Oracle read completed `(season, lineup, optimal)` facts
  only - no forward-looking mechanic (and gated on the optimal indicator being exactly ingested). **C3**
  Patience Premium cleared. **C4** The Climb.
- **Tone-care artifacts** (The Sieve, Benchwarmer, Black Rose, Burning Money) carry SHAME_RECORD display
  provenance with care - rendered factually, never mockingly.
- **Silence over speculation** - load-bearing for B2: any award whose underlying fact (optimal indicator,
  draft-era completeness) is not exactly ingested is DEFERRED, not rendered with a guess (the Unbroken Chain
  precedent).

## 6. Out of scope

- Increments 1 (Championship Package) + 2 (Live Records) - discharged. The Mantel / A/V Room (W.1).
- Any analytics, optimization, engagement loop, or predictive feature.

## 7. What decision-readiness (memo 2) must resolve

(a) Staging: Wave A (8) now off existing data; Wave B1 (3) via a weekly-score sync extension; **Wave B2 (15)
- build the player/draft/waiver domain, or defer.** (b) The exact derived reads for Wave A. (c) The Founder's
Seal - attested vs derived. (d) The optimal-indicator derivability check (Benchwarmer/Clairvoyant/Oracle) -
a data-fact probe like Wave 2's, before any B2 commitment. (e) The tone-care render treatment.

## 8. Provenance / status

DRAFT, DECIDE 2026-06-22. Opens the increment-3 chain on the discharged increments 1-2. The partition is
probe-confirmed (no player/draft/waiver domain in the frontend). Pending founder ratification + commit.
