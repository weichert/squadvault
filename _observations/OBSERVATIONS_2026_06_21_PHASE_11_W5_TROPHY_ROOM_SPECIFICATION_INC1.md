# Trophy Room (Unit W.5) - Specification, Increment 1 (memo 3 of 4) - DRAFT

**Date:** 2026-06-21
**Session type:** DECIDE (specification). No repo or DB writes. DRAFT for founder ratification + commit.
**Chain position:** memo 3 of 4. Executes the ratified D1-D5 rulings from memo 2. Registration is memo 4.
**Anchor:** engine HEAD `ac4141b`. Input: taxonomy v1.2 (binding once registered per D5).
**Scope of this increment:** the shared surface architecture (all 37 build on it) + the Championship Package (stage 1 of D3). Stages 2 (Live Records) and 3 (per-season grants / accumulations / fixed records) are framed in section 11 and specified in follow-on increments.

---

## 1. Ratified rulings carried in (memo 2, agreed 2026-06-21)

- **D1** - custody-behavior and display-provenance are separate axes; current holder is always a derived read, never a stored column.
- **D2** - the Belt's custody events are manually ratified; Live-Record transfers are derived from completed facts.
- **D3** - staged delivery; Championship Package first.
- **D4** - the Room is sectioned by category with the Championship Package featured; per-trophy custody timelines are drill-in, not all surfaced at once.
- **D5** - taxonomy v1.2 registered before binding; `trophy_custody_events` engine home per the Manual Fact Import frame.

## 2. Surface architecture (shared - all increments)

**Portal.** The clubhouse trophy case (W.2 plate 1) is the fixed navigation portal. Clicking it opens
the Trophy Room. The case never grows; the Room carries all growth (D4).

**Room layout.** Sectioned by the taxonomy's own structure: a featured **Championship Package** band at
the top, then six sections - Annual, Positional, Draft/Auction, In-Season, Live Records, Permanent. Each
section lists its artifacts as Trophy Cards (section 3). Growth is append-within-section; adding seasons
or artifacts never restructures the Room.

**Drill-in.** A Trophy Card opens its custody timeline on demand (the provenance chain for traveling
artifacts; the season-by-season grant list for per-season awards; the accumulated name list for
communal/mint-and-keep). Timelines are on-tap, never all-expanded - this is how 16-and-growing seasons
stay legible.

## 3. The Trophy Card (shared)

Each card renders, from the catalog + the derived-holder read (never stored):

- League name; trophy name; category; season/year (where applicable)
- **Recipient / current holder** - a DERIVED read (C1), labeled as derived, never a hardcoded field
- Award definition (the immutable qualification - kept pure per the Constitutional pass: no baked-in holder)
- Source-fact summary (what completed fact the holder derives from)
- **Docket ID** (section 5)
- **Trust bar** (section 6)
- Approval state (section 7)
- Optional ceremonial copy; optional visual rendering

The qualification text stays immutable; the holder updates by derivation. A card whose holder is unknown
or whose backfill is incomplete shows no holder, not a guessed one (silence over speculation).

## 4. Fact layer (shared framework)

Per the partition (memo 2 Part A), two data paths, kept distinct (D1):

- **Transfer ledger - `trophy_custody_events`** `(trophy_id, from_franchise, to_franchise, occasion,
  season/week, ratified_by, ratified_at)`. Append-only, RLS, no DELETE, matching every sibling. Current
  holder = derived read = latest event's `to_franchise` (multi-valued where co-held). Populated by
  **Groups 1-2 only** (the Belt manually per D2; Live Records derived per D2). Engine canonical home per
  the Manual Fact Import frame (D5). Historical backfill = founder ratification work, oral-history dignity.
- **Derived-holder reads** for Groups 3-5 (per-season grants, accumulations, fixed records): the holder
  is computed off existing award/record/championship data - no new custody events. The spec for those
  increments defines each read; nothing manual.

## 5. Docket ID scheme (shared)

A stable, human-legible identifier per artifact instance, for the trust bar and cross-reference:
`TR-<CAT>-<artifact#>-<season>` where `<CAT>` is the category code (CP, ANN, POS, DFT, INS, LRC, PRM),
`<artifact#>` is the taxonomy number, and `<season>` is the certified season the instance pertains to
(omitted for the communal League Trophy, which is perpetual; for Live Records, the season the current
mark was set). Example: the Belt for the 2025 champion = `TR-CP-1-2025`. IDs are derived from
catalog + fact, never minted mutable.

## 6. Trust bar + provenance (shared)

Reuse the shipped `TrustBar` and `provenance` enum; do not fork. Map the display-provenance axis (D1) to
the existing variants: CANONICAL (derived from engine-certified facts - most cards), COMMISSIONER_ATTESTED
(manually ratified facts - Belt custody events, manual occasions), DRAFT/APPROVED (publication state). The
shared `PROVENANCE_LABEL`/`PROVENANCE_STYLE` module flagged in the tighten memo is the home for these;
extract it so both the Trophy Room and the Mantel (later) consume one module.

## 7. Commissioner approval flow (shared)

AI assists, human approves (constitutional). No artifact becomes shareable/published until the
commissioner approves it. Derived facts surface as CANONICAL automatically; manually ratified facts
(Belt custody) require the ratify step (`ratified_by`/`ratified_at`) before they read as holder. Approval
is a publication gate, not a fact-creation step - it never invents a holder, only releases a derived one.

## 8. Increment 1 - the Championship Package

One completed fact (winning the season championship) produces three artifacts with three custody models.

**8.1 The Belt (CP1 / #1) - traveling individual.** One physical artifact; passes to each new champion.
- Data: `trophy_custody_events`, manually ratified (D2) - one event per championship; historical journey
  (occasions, the heist narrative) backfilled by founder ratification.
- Render: current holder derived = latest event's `to_franchise`; drill-in shows the full provenance chain
  ("held by Miller's Genuine Draft since 2025 W9 - taken from Stu's Crew - 7th transfer in trophy history"),
  era-correct names via `franchise_season_names`. Heists rendered with relish; **no transfer count
  leaderboard, no streaks** (boundary).
- Governed nameplate: section 9.

**8.2 The Ring (CP2 / #36) - mint-and-keep individual.** Each champion receives their own ring, kept
permanently; rings accumulate, nothing transfers.
- Data: derived from the championship record (one ring per certified champion-season). No transfer events.
- Render: an accumulating set; each ring's holder = that season's champion, permanently. Drill-in = the
  list of all champion-seasons. Governed nameplate: section 9.

**8.3 The League Trophy (CP3 / #37) - communal perpetual.** One perpetual trophy in the shared case;
never leaves; accumulates every champion's name append-only.
- Data: derived from the championship record (append each new champion). Custody is communal (the league),
  not individual.
- Render: the cumulative winners list (Stanley-Cup model); drill-in = every champion in order. Governed
  nameplate: section 9.

## 9. Governed text surfaces (Championship Package nameplates)

- **PFL expansion:** "Phony Football League" - **attested (C7 closed, 2026-06-21)**; engraveable. Per-
  artifact choice of the rendered string ("Phony Football League" vs the MFL designation "PFL Buddies")
  is a render decision; default to the attested expansion on the formal nameplate, "PFL Buddies" where the
  platform designation is wanted. No other expansion is permitted (it is the only attested one).
- **Champion + year:** per-artifact governed text surface - the champion is a derived read off the
  championship fact; the year is the certified season. The Belt's brass nameplate carries the current
  champion + year; the Ring carries its season's champion + year permanently; the League Trophy carries
  the cumulative list. A nameplate with no attested champion yet shows blank, not a guess.

## 10. Capacity / growth (D4, applied)

The Championship Package band is featured and fixed in position; it grows by appending one Belt-transfer,
one Ring, and one League-Trophy name per championship - never a redesign. The six category sections below
append within themselves. The Room's structure is the taxonomy's structure, so it scales by addition.

## 11. Deferred increments (framed; specified next)

- **Increment 2 - Live Record Plaques (7, Group 2).** Travels when surpassed; holder derived from completed
  facts (D2); current-holder read is **multi-valued on tie** (The Floor co-held; C6). Spec reuses sections
  2-7; defines the derived-transfer read and the multi-valued holder rendering.
- **Increment 3 - per-season grants (22), accumulations (Ring-like + Perfect Storm), fixed records (4).**
  All derived/fixed; no transfer ledger. The Perfect Storm multi-lists names (each 0-14 appends; the "only"
  framing is retired per ratified decision 3). Tone-care artifacts (The Sieve, The Floor, The Perfect Storm)
  carry the SHAME_RECORD display provenance with care.

## 12. Constitutional carry

C1 (holder always derived, never stored). C2 (Clairvoyant: completed facts only). C7 CLOSED (PFL = Phony
Football League, attested). Boundary: heists with relish, **no points / no theft leaderboards / no custody-
streak or contest mechanics**; append-only facts; silence over speculation (no guessed holders, blank
nameplates, no backfill invention); human approves publication; no prediction, analytics, or engagement loop.

## 13. Provenance / status

DRAFT, DECIDE session 2026-06-21. Memo 3 of the Unit W.5 chain, increment 1 (shared architecture +
Championship Package). Pending founder ratification + commit. On ratification: memo 4 registers the chain
(and the taxonomy v1.2 per D5), then the build is an EXECUTE increment - Championship Package first.

