# Trophy Room (Unit W.5) Increment 2 - Live Record Plaques - Selection-Prep (memo 1 of 4) - DRAFT

**Date:** 2026-06-22
**Session type:** DECIDE (selection-prep). No repo/DB writes. DRAFT for founder ratification + commit.
**Chain position:** memo 1 of 4 for increment 2. Builds on the discharged increment-1 spec/architecture.
**Anchors:** engine HEAD `5464526`; frontend `a6eb95b` (increment 1 Championship Package discharged, gov 154/0).
**Input:** taxonomy v1.2 (Live Record Plaques, section 5; 7 artifacts).

---

## 1. What this memo does

Opens the increment-2 chain: confirms the Live Records surface, fixes its relationship to the
discharged increment 1, and - critically - resolves the data-source question that was flagged as
increment 2's gating unknown. It frames; it does not spec. The rendering and data-extension rulings
belong to decision-readiness (memo 2).

## 2. The surface

The **Live Records section** of the Trophy Room: the 7 traveling-record plaques (taxonomy section 5).
Custody model = **traveling record** (memo-2/CP partition Group 2): the plaque travels when a completed
fact surpasses the prior mark; current holder is a DERIVED read off the data, **multi-valued when tied**
(co-held). This is NOT the manual `trophy_custody_events` ledger - that is the Belt's (increment 1).
Live Records derive their holder from completed facts (ratified D2 in the CP chain). The surface reuses
the increment-1 shared architecture (Room sections, Trophy Card, Docket ID, trust bar, approval); it adds
no manual custody ledger.

The 7 plaques: #24 The Cavallini Standard (all-time win-pct leader), #25 The Dynasty (most titles),
#26 The Eternal Runner-Up (most runner-ups, no title), #27 The Executioner (most blowout wins above a
margin), #28 The Iron Curtain (best all-time points-allowed avg), #29 The Unbroken Chain (longest
playoff-appearance streak; C5), #30 The Floor (worst single-season record; co-held on tie, C6; tone-care).

## 3. Data-source resolution (the gating unknown - now answered)

Probe of both repos: records are engine-derived off `WEEKLY_MATCHUP_RESULT` (e.g.
`scripts/audit_queries/season_records_alltime.py`) and a subset is synced to the frontend. The frontend
already holds **`franchise_season_records`** (migration 008): `(franchise, season, wins, losses, ties,
points_for, result[CHAMPION/RUNNER_UP])`, engine-derived + immutable. Mapping the 7 plaques against it:

| Group | Plaques | Source status |
|---|---|---|
| **A - ships from existing data** | #24 Cavallini Standard, #25 Dynasty, #26 Eternal Runner-Up, #30 The Floor | Directly derivable from `franchise_season_records` (aggregate W-L / count CHAMPION / count RUNNER_UP-with-zero-titles / worst season). No new pipeline. |
| **B - needs a data decision** | #28 The Iron Curtain (needs `points_against` - table has points_for only), #27 The Executioner (needs game-level blowout margins - season aggregates insufficient), #29 The Unbroken Chain (needs playoff-*appearance* history - table marks only CHAMPION/RUNNER_UP) | Each is engine-side derivable from the canonical matchup data (margins, points-against) EXCEPT possibly playoff-appearance, which the 008 comment flags as "not exactly derivable, omitted per silence-over-speculation." |

So increment 2 is **not** blocked on a missing pipeline - 4 of 7 ship on existing synced data. The real
decision is scoped to Group B: extend the engine->frontend sync for the exactly-derivable facts
(points-against, game margins), and DEFER any plaque whose fact is not exactly derivable (silence over
speculation) - The Unbroken Chain is the candidate to test against C5 + exact-derivability.

## 4. Constitutional requirements carried in

- **C1** - current holder = derived read off the data, never stored mutable state.
- **C5** - governs The Unbroken Chain (playoff-streak definition); confirm exact-derivability in memo 2.
- **C6** - The Floor is co-held on tie: the current-holder read is **multi-valued**; the render shows all
  co-holders, never a single arbitrary one.
- **Silence over speculation** - load-bearing here: a plaque whose fact is not exactly derivable is NOT
  rendered with a guessed value; it is deferred until the fact exists exactly. (Group B gate.)
- **Boundary** - no points/leaderboards/streak-as-game mechanics; a record's transfer ordinal and the
  record value itself are factual, not a contest. Append-only; human approves publication.

## 5. Out of scope

- Increment 3 (per-season grants, accumulations, fixed records) - its own chain.
- The manual `trophy_custody_events` ledger (Belt/increment 1 only) - Live Records do not write it.
- The Mantel / A/V Room (W.1). Any analytics, optimization, engagement loop, prediction.

## 6. What decision-readiness (memo 2) must resolve

(a) The Group A derived reads (4 plaques) - exact definitions + the multi-valued (co-held) holder render
for The Floor. (b) The Group B data decision - which facts to add to the sync (points-against, game
margins) vs defer (playoff-appearance, pending C5 + exact-derivability). (c) Whether increment 2 ships
Group A first (staged) or waits for the Group B sync extension. (d) The traveling-record "surpassed"
read - how a transfer is detected from completed facts (no manual ledger).

## 7. Provenance / status

DRAFT, DECIDE 2026-06-22. Opens the increment-2 chain on discharged increment-1 ground. Pending founder
ratification + commit.

