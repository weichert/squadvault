# Trophy Room (Unit W.5) Increment 3 - Grants / Accumulations / Fixed - Specification (memo 3 of 4) - DRAFT

**Date:** 2026-06-23
**Session type:** DECIDE (specification). No repo/DB writes. DRAFT for founder ratification + commit.
**Chain position:** memo 3 of 4 (increment 3). Executes the ratified rulings of selection-prep (memo 1) and decision-readiness (memo 2) on probe-confirmed data.
**Anchors:** engine HEAD `0219b30` (verified this session: increment 2 + Wave 2 generators merged, PR #3; `franchise_season_records` carries `points_against` regular-season-only + `blowout_wins_60`); frontend `7e0ee94`.
**Recovery note:** the original memo-3 draft was lost with the prior session's container scratch. This is a reconstruction grounded in the two surviving drafts, the committed increment-2 spec, and direct inspection of the generator pipeline (`gen_franchise_records.py`, `gen_supabase_rebuild.py`). No new design is introduced; this specifies only what increments 1-2 already established.

---

## 1. Ratified inputs carried in (from memo 2)

- **D1 - `season_award_winners` fact table.** The engine computes the winner of each per-season award and syncs one compact row per (award, season); the frontend reads it as a thin governed read. Not a replication of the raw player/draft/waiver domain.
- **D2 - staging.** Wave A (8) now off existing synced data; Wave B1 (3) via a weekly-score sync extension; Wave B2 (15) as a scoped sub-project, de-risked but sequenced after B1.
- **D3 - data-fact gate.** Each B2 award must be EXACTLY computable before its read ships; anything not exactly computable DEFERS (the Unbroken Chain precedent), it does not render a guess.
- **D4 - Wave A exact reads** (section 3 below).
- **D5 - the Founder's Seal is founder-attested, not derived; tone-care artifacts render SHAME_RECORD provenance factually, never mockingly.**

**Spec call made here (memo 2 left it open):** Wave A reads its 8 directly off `franchise_season_records` - FRONTEND-only, no migration, not blocked on the new table. `season_award_winners` is introduced at Wave B1, whose 3 weekly-derived awards are its first tenants (de-risking the table before B2's 15 land on it). Wave A may later migrate onto the unified table for uniformity; that is an optional future tidy, non-blocking.

## 2. Surface and shared-architecture reuse

The remaining Trophy Room sections (Annual ex-Belt, Positional, Draft/Auction, In-Season, Permanent) render as Trophy Cards on increment 1's shared architecture: Room section, Trophy Card, Docket ID, trust bar (provenance = CANONICAL, engine-derived facts), commissioner approval (publication gate). Three custody models, none writing `trophy_custody_events`:

- **Per-season grant** - holder = the most recent season's winner of that award (derived, C1).
- **Accumulating multi-list** - every qualifying instance is a permanent entry (C6); render lists ALL.
- **Fixed permanent** - a single immutable fact (a fixed champion, or an attested statement).

Multi-valued on tie throughout: where two franchises tie, the render lists all co-holders, never one arbitrary pick (C6).

## 3. Wave A - 8 plaques on existing synced data (`franchise_season_records`), FRONTEND-only

Each is a derived read; the immutable qualification stays pure (no baked-in holder).

**Per-season grants** (holder = most recent season's winner; 2025 is the most recent certified season - `franchise_season_records` holds 2010-2025):

- **#2 Bridesmaid Bouquet** - the most recent season's RUNNER_UP. (Distinct from increment 2's #26 The Eternal Runner-Up, the all-time most-runner-ups-without-a-title - different artifact, different custody.)
- **#5 The Sieve** (tone-care) - the franchise with the most regular-season `points_against` in the most recent season. Reads the Wave 2 column directly.
- **#8 The Climb** (C4) - the largest win-pct gain versus the prior season; needs the most-recent and prior-season rows per franchise, both present in `franchise_season_records`.
- **#10 The Banner** - the best regular-season win pct in the most recent season.
- **#11 The Engine** - the most points-for in the most recent season.

**Fixed permanent:**

- **#32 Inaugural Champion** - the 2010 CHAMPION. A single immutable fact; holder is permanent.
- **#34 Back-to-Back** - the franchise(s) with consecutive CHAMPION seasons, derived from the championship roll. Treated as fixed-permanent; multi-valued if more than one franchise has ever repeated.

**Accumulating multi-list:**

- **#35 The Perfect Storm** (tone-care; C6) - every winless (0-14) season is a permanent entry. Same data as increment 2's #30 The Floor; distinct artifact, distinct custody. Lists all entries (e.g. Brandon / franchise 0010, 2025), never one.

No migration. Wave A is shippable the moment the frontend section and cards exist.

## 4. Wave B1 - 3 plaques after a weekly-franchise-score sync extension

The three need per-week franchise scores, which are exactly derivable off completed `WEEKLY_MATCHUP_RESULT` (winner_score / loser_score per matchup) - the same stream Wave 2 used to derive `points_against`. Wave B1 introduces `season_award_winners` and is its first consumer.

### 4.1 The `season_award_winners` table (D1)

- Columns: `award_id TEXT` (docket/taxonomy id), `season INTEGER`, `franchise_id TEXT` (canonical `0001`..`0010`), `value NUMERIC NULL` (the winning metric - a score, a margin, a pct; null for boolean-membership awards), `detail JSONB NULL` (optional: player_id, week, opponent - for B2 and drill-in), `provenance TEXT` (e.g. `engine:matchup-derived`).
- Natural key `(award_id, season, franchise_id)` - co-holders allowed (a tie writes multiple rows; the frontend lists all, C6). One award's per-season winner is one row (or N on tie).
- Immutable / append-only. Corrections happen by recomputing and reseeding the affected rows, never by mutating a fact's meaning in place.
- Franchise references resolve by `(league canonical_id, canonical_franchise_id)` - no hardcoded UUIDs, no `F01`/`0001` ambiguity (the resolution the increment-2 pipeline already adopted).

### 4.2 The provenance lesson, applied (folded in from increment 2)

Synced facts must be produced by a **tracked, in-repo generator** whose derivation is auditable in git, and applied via an **idempotent, FK-safe seed transaction** - the `gen_supabase_rebuild` idiom - NOT pushed row-by-row through an untracked script. Concretely:

- New engine generator `gen_season_award_winners.py`, born tracked under `scripts/` (the increment-2 generators initially lived untracked in `~/sv-apply/`; that gap is the lesson). READ-ONLY on the engine DB; reads the same `HistoricalMatchup` stream as `gen_franchise_records.py`; emits JSON.
- New Supabase migration (number build-confirmed; latest known is 026 from the W.5 custody ledger, so approximately 027) creates `season_award_winners`.
- An idempotent seed (e.g. `004_season_award_winners.sql`) emitted from the JSON: FK-safe DELETE-then-INSERT for the affected awards, re-runnable, BEGIN/COMMIT-wrapped.
- **FRESH prod object-existence probe before any apply** (standing hazard: repo-Done is not prod-applied; a green gate can be green because the guarded object does not yet exist).

### 4.3 The 3 reads

- **#4 The Cannon** - the all-time highest single-week franchise score. The generator writes, per season, that season's max single-week score (one `season_award_winners` row); the frontend reads the max over all seasons. Per-season rows give a free chronological drill-in.
- **#12 The Black Rose** (tone-care) - the all-time highest LOSING score (you scored huge and still lost). Same shape: per-season highest losing score in; all-time max read out.
- **#33 One-Point Club** (accumulating multi-list, C6) - championship games decided by a margin < 2. The generator writes the qualifying championship result per season (if any); the frontend lists all such seasons = the club. **Build pin:** the exact margin threshold/inclusivity and whether membership is the winner only or both finalists, confirmed against the championship-week matchup data before the read ships.

## 5. Wave B2 - 15 player-domain plaques (framed; each gated on D3)

Memo 2 Part A confirmed every B2 fact is INGESTED at the engine (player scores with the MFL `shouldStart`/optimal indicator, `player_id` per week, `bid_amount`/auction prices). So B2 is a sync + compute effort: extend `gen_season_award_winners.py` with the player-domain award computations, carrying `player_id`/`position`/detail in `detail JSONB`, syncing per-season winners into the same table, and reading them on the frontend.

memo 3 specifies the architecture (above) and the D3 gates; it does NOT spec-final each of the 15, because each needs its data-fact pin first (memo 2 Part C). The 15 and their gates:

- **Positional six (#13-18)** - gated on the `position` field being present and reliable on player scores.
- **Draft/Auction four (#19-22)** - gated on auction-era coverage: which seasons carry bid/auction data. Auction-era seasons only; pre-auction seasons render nothing (silence, not a guess). (Includes the tone-care "Burning Money"-class SHAME_RECORD - factual, never mocking.)
- **Benchwarmer (#6), Clairvoyant (#7, C2), Oracle (#9, C2)** - gated on the optimal indicator (`shouldStart`) being exactly ingested; read completed `(season, lineup, optimal)` facts only, no forward-looking mechanic.
- **Hammer (#3), The Lifeline (#23)** - gated on each award's exact computation being pinned (Hammer: "score exceeded the winning margin"; The Lifeline: the waiver definition).

Anything not exactly computable at its D3 check DEFERS - registered, not rendered.

## 6. The Founder's Seal (#31) - attested, not derived

The Founder's Seal ("all 10 members present since the digital era") is a membership STATEMENT, not a computed competition - so it routes as **founder-attested**, the provenance idiom of the Herlth and PFL attestations (C7). It renders as a fixed attested plaque whose qualification is supplied by founder attestation at build, recorded as a provenance triple; it writes no `season_award_winners` row and computes no winner.

A **franchise-continuity check** runs at build as CORROBORATION - the way "Phony Bowl" corroborated PFL: confirm all 10 canonical franchise_ids are present in every season 2010-2025 in `franchise_season_records`. If the real history has a wrinkle (a late join, a replacement), it surfaces there and the qualification is corrected rather than rendering a falsehood. Attestation is the mechanism for the founder to confirm the fact; it is not a guess.

## 7. Tone-care render treatment (D5)

SHAME_RECORD-class artifacts - The Sieve, The Black Rose, Benchwarmer, the "Burning Money" draft/auction award - render their provenance factually and plainly, never mockingly. The fact is the fact; the framing carries no editorial sneer.

## 8. Award provenance / drill-in

A per-season-grant or record award surfaces its chronological history (prior winners / the mark over time) on drill-in, derived by reading the `season_award_winners` rows across seasons - the computed analogue of the Belt's ratified chain. No live counter, no streak-as-game mechanic: the value and its history are displayed as record, not contest.

## 9. Constitutional carry

C1 (holder = derived read, never stored). C2 (Clairvoyant/Oracle: completed `(season, lineup, optimal)` facts only). C4 (The Climb). C6 (Perfect Storm + One-Point Club multi-lists; multi-valued render on every tie). C7 (the PFL/Herlth attestation idiom reused for the Founder's Seal). Silence over speculation (every D3 deferral; the One-Point Club and Founder's Seal build pins). Tone-care for SHAME_RECORD artifacts. Boundary: no points / leaderboards / live-streak mechanics / prediction / analytics / engagement loop; append-only facts; human approves publication. Architecture frozen.

## 10. Build path (memo 4 registers; EXECUTE builds)

- **Wave A (8):** FRONTEND-only - eight derived reads off existing synced `franchise_season_records` + the Trophy Room sections/cards + multi-valued render. No migration. Ships first.
- **Wave B1 (3):** ENGINE - `gen_season_award_winners.py` (born tracked) computes the three weekly-derived awards per season -> `season_award_winners` migration (approximately 027, build-confirmed) -> idempotent seed -> three frontend reads. Founder-applied migration; FRESH prod object-existence probe first. First tenant of the new table.
- **Wave B2 (15):** ENGINE - extend the generator with the player-domain computations that pass their D3 pin -> reads. Sequenced after B1; its own EXECUTE arc. D3 deferrals for any non-exactly-computable award (registered, not rendered).
- **Founder's Seal (#31):** attested plaque; founder supplies the fact at build; the continuity check corroborates.

Destination for this memo and its chain: `_observations/` (not repo root - the root allowlist enforces exactly five files).

## 11. Provenance / status

DRAFT, DECIDE 2026-06-23. Memo 3 of the increment-3 chain, reconstructed against verified engine HEAD `0219b30` and the inspected generator pipeline. Executes memo 2's D1-D5 with the Wave-A-direct / B1-introduces-`season_award_winners` sequencing call made here. Pending founder ratification + commit. On ratification, memo 4 registers the chain and the build opens (Wave A first - frontend-only, low-risk, lights up 8 plaques immediately).
