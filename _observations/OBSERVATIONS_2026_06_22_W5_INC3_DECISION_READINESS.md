# Trophy Room (Unit W.5) Increment 3 - Decision-Readiness (memo 2 of 4) - DRAFT

**Date:** 2026-06-22
**Session type:** DECIDE (decision-readiness: probes + framing). No repo/DB writes. DRAFT for founder ratification + commit.
**Chain position:** memo 2 of 4 (increment 3). Builds on the selection-prep (memo 1).
**Anchors:** engine HEAD `0219b30`; frontend `7e0ee94`.
**Ratified going in (founder, 2026-06-22):** the Trophy Room will eventually hold ALL 37 - commit to the player-data domain.

---

## Part A - Probe: the player-domain facts are already ingested (B2 de-risked)

The selection-prep flagged B2 (15 player/draft/waiver awards) as gated on a data domain absent from the
frontend. The gating question was derivability at the ENGINE. Probe result:

- **Optimal-lineup indicator INGESTED** - `ingest/player_scores.py` carries the MFL `shouldStart` flag;
  `player_week_context_v1.py` already computes "optimal lineup points left on bench"; `franchise_deep_angles_v1`
  has a perfect-lineup detector. -> Benchwarmer, Clairvoyant (C2), Oracle (C2) are derivable.
- **Player scores INGESTED** (`player_id`, per week) -> positional awards derivable (confirm `position` field at
  spec; almost certainly present).
- **Bid / auction data INGESTED** (`bid_amount`, auction prices vs FAAB) -> draft/auction awards derivable
  (auction-era seasons only; pre-auction seasons silent, correct).

**So the "all 37" commitment is a SYNC + COMPUTE effort, not a data-acquisition one.** Every B2 fact exists
at the engine; the work is computing the per-season award winners and getting a compact result to the frontend.

## Part B - Framing the decisions

### D1 - Architecture: a `season_award_winners` fact table (recommended)

Do NOT replicate the raw player/draft/waiver domain to the frontend (millions of rows, heavy). Instead,
generalize the `franchise_season_records` pattern: **the engine computes the winner of each award per season
and syncs a compact `season_award_winners` table** - `(award_id, season, franchise_id, value, provenance,
[player_id/detail optional])`, one row per award per season, immutable, engine-derived. Frontend reads = "most
recent season's winner" (derived holder, C1), multi-valued on tie (C6). This serves Wave A, B1, and B2
uniformly, and keeps the frontend a thin governed read over derived facts - same idiom as everything shipped.
(Wave A can still read its 8 off `franchise_season_records` directly, or move to the unified table - a spec call.)

### D2 - Staging (recommended)

- **Wave A (8) - now.** Off existing synced `franchise_season_records` (incl. Wave 2 points-against). No new data.
- **Wave B1 (3) - next.** A weekly-franchise-score sync extension (Cannon, Black Rose, One-Point Club) - the
  Wave 2 pattern again.
- **Wave B2 (15) - the scoped sub-project, now de-risked.** Engine award-computation layer -> `season_award_winners`
  sync -> frontend reads. Sequenced after B1; its own EXECUTE arc, but no longer a data-acquisition unknown.

### D3 - Prerequisite probes before B2 spec (data-fact checks, silence-over-speculation)

Even with the domain committed, confirm each B2 fact is EXACTLY computable before its read ships:
- `position` field present + reliable on player scores (positional six).
- Auction-era coverage: which seasons have auction/bid data (draft/auction four are "auction-era only").
- Each award's exact computation pinned (e.g. Hammer's "score exceeded the winning margin", Clairvoyant's
  "correct decision rate", Oracle's "incorrect decision that flipped a win"). Anything not exactly computable
  DEFERS (the Unbroken Chain precedent) - it does not render a guess.

### D4 - Wave A exact reads (8, ship now)

#2 Bridesmaid Bouquet (most recent RUNNER_UP), #5 The Sieve (max regular-season points-against), #8 The Climb
(largest win-pct gain vs prior season; C4), #10 The Banner (best regular-season win pct), #11 The Engine (max
points-for), #32 Inaugural Champion (2010 CHAMPION - fixed), #34 Back-to-Back (only consecutive-CHAMPION
franchise - fixed), #35 The Perfect Storm (each 0-14 season, multi-list accumulating; C6; same data as The Floor).

### D5 - Founder's Seal + tone-care

#31 The Founder's Seal ("all 10 members present since the digital era") is a fixed **attested** statement, not a
computed competition - decision-readiness routes it as founder-attested (provenance idiom of the Herlth/PFL
attestations), not a derived read. Tone-care artifacts (Sieve, Benchwarmer, Black Rose, Burning Money) render
SHAME_RECORD provenance factually, never mockingly.

## Part C - What memo 3 (specification) executes

D2 staging with the D1 architecture: Wave A's 8 reads; the B1 weekly-score extension + 3 reads; the
`season_award_winners` design + the B2 award-computation definitions (those that pass D3) + reads; the
Founder's Seal attested-fact handling. Deferrals per D3 for any non-exactly-computable award.

## Constitutional carry

C1 (derived holder, never stored). C2 (Clairvoyant/Oracle: completed `(season, lineup, optimal)` facts only).
C3 (Patience Premium cleared). C4 (The Climb). C6 (Perfect Storm multi-list). Silence over speculation (D3
deferrals). Tone-care for SHAME_RECORD artifacts. Boundary: no points/leaderboards/streak mechanics;
append-only; human approves; no prediction/analytics/engagement loop. Architecture frozen.

## Provenance / status

DRAFT, DECIDE 2026-06-22. Memo 2 of the increment-3 chain. Part A confirms B2 feasibility (facts ingested);
Part B frames D1-D5 for ruling. On ratification, the rulings feed memo 3.
