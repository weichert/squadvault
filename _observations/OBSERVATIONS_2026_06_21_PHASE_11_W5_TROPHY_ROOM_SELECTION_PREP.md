# Trophy Room (Unit W.5) - Selection-Prep (memo 1 of 4) - DRAFT

**Date:** 2026-06-21
**Session type:** DECIDE (selection-prep). No repo or DB writes. DRAFT for founder ratification + commit.
**Chain position:** memo 1 of 4 (selection-prep -> decision-readiness -> specification -> registration). Opens the Unit W.5 chain.
**Anchor:** engine HEAD `ac4141b`, main, == origin/main. Naming + C7 committed (six-commit set, 2026-06-21).
**Template:** per-surface constitutional memo template v1.

---

## 1. What this memo does (and does not)

Opens the Unit W.5 (Trophy Room) chain: confirms the surface against committed ground, fixes its
relationship to the shipped display, and enumerates the candidate scope and the decisions to be
readied. It frames; it does not decide. The structural rulings (capacity model, layer composition,
staging) belong to decision-readiness (memo 2) and the spec (memo 3). Nothing here is the spec.

## 2. The surface (committed ground)

**The Trophy Room** is Unit W.5: the trophy-display surface behind the clubhouse trophy-case portal
(W.2 plate 1). It renders the league's trophies and plaques with their custody/provenance over time.
Naming is committed (founder ruling + DoR v2.1.2 note, 2026-06-21): the display is "the Trophy Room"
(not "the Mantel"); "the Mantel" is the photo fixture into the A/V Room (W.1), out of scope here.

Per the DoR (Unit W.5, closing R6), the surface has two layers:

- **Fact layer:** a new append-only `trophy_custody_events` class - `(trophy_id, from_franchise,
  to_franchise, occasion, season/week, ratified_by, ratified_at)`. Commissioner-ratified manual facts
  per the Manual Fact Import frame; append-only, RLS, no DELETE, matching every sibling table. Current
  holder is a **derived read, never stored mutable state** (C1). Historical backfill is founder
  ratification work, "same dignity as oral history."
- **Display layer:** each traveling trophy shown with its provenance chain ("held by Miller's Genuine
  Draft since 2025 W9 - taken from Stu's Crew - 7th transfer in trophy history"), full custody timeline
  on tap, era-correct names via `franchise_season_names`.

## 3. Why this surface, why now

- The naming collision and the one constitutional blocker (C7) are both resolved and committed, so the
  surface can be specified on settled ground rather than relitigated.
- The trophy taxonomy is ratified at v1.2 (37 artifacts), giving the surface its catalog of what to render.
- A display predecessor already ships (section 4), so this is a successor/expansion with a concrete
  starting point, not a greenfield build.
- W.5 has no member-likeness or voice surface, so - unlike the Writer's Room trophy-heist *features*,
  which are post-W.5 - it carries **no W.6 (consent) predecessor**. The Trophy Room itself is clear to proceed.

## 4. Relationship to the shipped surface (positioning - settled)

The shipped `/league/[id]/trophy-room` (records: `OBSERVATIONS_2026_05_30_TROPHY_ROOM_UI_SHIPMENT`,
`..._05_31_TROPHY_ROOM_TIGHTEN`) is a **flat display table** (`trophy_room_entries`; four entry types
CHAMPIONSHIP / PHYSICAL_TROPHY / COMMISSIONER_ATTESTED / SHAME_RECORD; renders CHAMPIONSHIP only). The
DoR calls it "display entries only - see R6."

W.5 is the **successor/expansion** of that surface, not a new one. It adds the custody-over-time event
ledger on top of the flat registry and grows the catalog from championships-only to the full taxonomy.
So three things compose, and keeping them distinct is the heart of the spec:

- **Taxonomy v1.2** = the catalog (which 37 artifacts exist, in which category, with which custody model).
- **`trophy_room_entries`** (shipped) = the display registry (what is shown).
- **`trophy_custody_events`** (new, W.5) = the custody ledger (transfers over time -> derived current
  holder + provenance chain).

## 5. Candidate scope to enumerate (hand to decision-readiness; do not decide here)

1. **Layer composition.** How taxonomy x display registry x custody ledger compose without bleed -
   the central structural question.
2. **Which custody models even have custody-over-time.** Not all 37 artifacts transfer. The Belt
   (traveling) generates transfer events; the Ring (mint-and-keep) does not - one minted per champion,
   kept forever; the League Trophy (communal perpetual) accumulates names rather than transferring;
   annual/positional awards are per-season grants; live records are a derived current-holder read;
   permanent records never move. Decision-readiness must partition the taxonomy into "has a custody
   timeline" vs "static grant/record," because only the former populates `trophy_custody_events`.
3. **Staging.** Full 37 at once vs staged by custody category (e.g. Championship Package first - the
   richest custody story and the one the shipped v1 already touches - then the rest).
4. **Capacity / growth model.** 16-and-growing seasons. The clubhouse trophy case stays fixed as the
   portal; the Room behind it carries the growth (curated/featured display, sectioned views, multiple
   cabinets). The main design decision.
5. **Trophy Card elements, Docket ID scheme, trust bar, commissioner approval.** Reconcile with the
   shipped `TrustBar` / provenance enum / approval flow rather than reinvent; extract the shared
   provenance module flagged in the tighten memo.
6. **Historical backfill.** Custody backfill is founder ratification work (oral-history dignity) - how
   much, how staged, how surfaced before it is complete (silence over speculation for gaps).

## 6. Constitutional requirements carried in

- **C1** - current holder is a derived read off the append-only `trophy_custody_events` ledger, never
  stored mutable state. (DoR-explicit for this unit.)
- **C2** - if The Clairvoyant is rendered, completed `(season, lineup, optimal)` facts only; no
  forward-looking mechanic.
- **C7 - CLOSED** - PFL = Phony Football League (founder-attested 2026-06-21). The expansion is
  engraveable on the Belt / Ring / League Trophy nameplates; which string renders where ("Phony
  Football League" vs the MFL designation "PFL Buddies") is a per-artifact governed-text-surface choice
  for the spec. Per-artifact champion + year remain governed text surfaces (derived holder read /
  per-championship attestation).
- **Boundary (DoR-explicit)** - heists rendered with relish, but **no points, no theft leaderboards,
  no custody-streak/contest mechanics**. No prediction, no analytics or engagement loops, append-only
  facts, silence over speculation, human approves publication.

## 7. Prerequisites / open items to ready (named here, resolved downstream)

- **Register the taxonomy.** Taxonomy v1.2 is the input of record (header confirms v1.2; no v1.2.1
  exists; filename "v1_0" is stale), but it lives only as a carry-in - it is not committed to the repo.
  By this project's discipline ("decided is not binding until registered"), it must be committed/
  registered as the binding input. This belongs in decision-readiness or spec, and the chain must not
  treat the taxonomy as binding until it lands. (Flagged by the verification session.)
- **Per-artifact governed text surfaces.** C7 unblocks the league-identity expansion; each
  championship's champion + year still require their per-artifact derived/attested handling.
- **Fact-layer canonical home.** The `trophy_custody_events` engine-side canonical home is set "per the
  Manual Fact Import frame's adjudication" - decision-readiness confirms that placement (no build here).

## 8. Out of scope

- The Mantel (A/V lineage, Unit W.1) and anything photo-side.
- The specification itself (memo 3) and any "ratification needed" language.
- Engine / schema / migration / DB writes (EXECUTE), including building `trophy_custody_events`.
- Cleat render assignment (The Workhorse vs The Boot) - design-track, non-blocking.

## 9. Next memo (decision-readiness, memo 2) must resolve

The custody-model partition (item 5.2), the layer-composition model (5.1), the staging call (5.3), and
the capacity/growth model (5.4) - plus confirm the taxonomy registration and the fact-layer canonical
home. The spec (memo 3) then renders each custody model and the Trophy Card from those rulings.

## 10. Provenance / status

DRAFT, DECIDE session 2026-06-21. Opens the Unit W.5 four-memo chain on committed ground (naming + C7
landed at HEAD `ac4141b`). Pending founder ratification + commit as memo 1.

