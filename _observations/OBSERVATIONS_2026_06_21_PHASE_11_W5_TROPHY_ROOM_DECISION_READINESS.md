# Trophy Room (Unit W.5) - Decision-Readiness (memo 2 of 4) - DRAFT

**Date:** 2026-06-21
**Session type:** DECIDE (decision-readiness: probes + framing). No repo or DB writes. DRAFT for founder ratification + commit.
**Chain position:** memo 2 of 4. Builds on the selection-prep (memo 1). Readies decisions for the spec (memo 3); does not write the spec.
**Anchor:** engine HEAD `ac4141b`. Input: taxonomy v1.2 (37 artifacts; header-confirmed; not yet repo-committed - see D5).

---

## Part A - Probe: the custody partition

Memo 1 handed this memo the partition: sort the 37 artifacts by whether they have custody **over time**.
Read against taxonomy v1.2, the 37 fall into five custody behaviors, and only two of them transfer.

| Group | Behavior | Artifacts | Count | Populates `trophy_custody_events`? |
|---|---|---|---|---|
| 1 | **Traveling individual** - one physical artifact, transfers per championship; occasions/heist narrative; historical backfill is founder ratification | The Belt | 1 | **Yes - manually ratified** |
| 2 | **Traveling record** - holder travels when a completed fact surpasses the mark; may be multi-valued (co-held on tie) | Live Record Plaques | 7 | **Yes - derivable from completed facts** (see D2) |
| 3 | **Per-season grant** - one award event per season; current holder = most recent certified recipient; no transfer | Annual (11, ex-Belt) + Positional (6) + Draft/Auction (4) + In-Season (1) | 22 | No - derived off existing award computation |
| 4 | **Accumulating append-only** - never transfers; names accumulate | The Ring (mint-and-keep), The League Trophy (communal perpetual), The Perfect Storm (multi-list) | 3 | No - append-grant, not transfer |
| 5 | **Fixed permanent** - single immutable append; never changes | Permanent Historical Plaques (ex-Perfect Storm) | 4 | No - immutable record |

Total: 1 + 7 + 22 + 3 + 4 = 37. (The Belt is listed at Annual #1 but reclassified to Group 1, so Annual contributes 11 to Group 3.)

**The finding.** The new W.5 transfer ledger (`trophy_custody_events`, with its `from_franchise ->
to_franchise` shape) is genuinely needed only for **Groups 1 and 2 - 8 artifacts that change hands.**
The other 29 never transfer: 22 are per-season grants whose holder is computed from completed-season
data the engine already produces; 3 accumulate names append-only; 4 are fixed records. This scopes the
W.5 build sharply, and it means the custody machinery and the grant/record reads are **different code
paths**, not one uniform "trophy entry."

---

## Part B - Framing the open decisions (each ready for your ruling)

### D1 - Layer composition

Four inputs compose, and keeping them distinct is the spine of the spec:

- **Taxonomy v1.2** = the catalog (which 37 artifacts, which category, which custody behavior).
- **`trophy_room_entries`** (shipped) = the display registry (what is shown; today CHAMPIONSHIP only).
- **`trophy_custody_events`** (new) = the transfer ledger - **Groups 1-2 only**.
- **Existing award/record computation** = the derived-holder source for Groups 3-5.

Note the shipped registry's four entry types (CHAMPIONSHIP / PHYSICAL_TROPHY / COMMISSIONER_ATTESTED /
SHAME_RECORD) are a **provenance/display axis**, not the custody axis - they cross-cut the five groups
(e.g. SHAME_RECORD covers tone-care artifacts like The Sieve, The Floor, The Perfect Storm across
Groups 2/4/5). **Recommendation to ready:** the spec treats custody-behavior and display-provenance as
two separate axes and does not collapse them; current holder is always a derived read (C1), never a
column on the display row.

### D2 - Which transfers are manually ratified vs derived from data

- **The Belt (Group 1):** manually ratified. Its journey carries occasions and heist narrative ("taken
  from Stu's Crew - 7th transfer") that are not purely derivable; historical backfill is founder
  ratification work (oral-history dignity). -> `trophy_custody_events`, manual via the Manual Fact
  Import frame.
- **Live Records (Group 2):** the surpass that moves a plaque is a **completed fact already in the
  data**. **Open question to ready:** derive live-record transfers from the record data (no manual
  entry), or also route them through the ratified ledger for uniformity? **Recommendation:** derive
  them (silence/derivation over manual where the fact is computable), reserving `trophy_custody_events`
  for the Belt and any genuinely manual occasion. Founder to rule.

### D3 - Staging

**Options:** (a) full 37 at once; (b) staged by custody group. **Recommendation: staged.** Order:
Championship Package first (Belt + Ring + League Trophy - the marquee, it exercises all three hard
custody models at once, and it extends the shipped championship-only display), then Live Records
(Group 2, derived transfers + multi-valued holder), then Groups 3-5 (per-season grants, accumulations,
fixed records - mostly derived/low-risk). Each stage is its own spec increment. Founder to rule.

### D4 - Capacity / growth model (the main design decision)

16-and-growing seasons; the clubhouse trophy case stays fixed as the portal, the Room behind it carries
growth. **Options to ready:** (i) curated/featured only; (ii) full catalog, paginated; (iii)
**sectioned by category** with the Championship Package featured. **Recommendation:** (iii) - the
taxonomy already gives six sections plus the Championship Package, so the Room mirrors the catalog's own
structure and scales by appending within a section rather than redesigning. Per-trophy custody timelines
are on-tap (drill-in), not all surfaced at once. Founder to rule; this is the decision the spec most
depends on.

### D5 - Prerequisites to confirm

- **Register the taxonomy.** v1.2 is the input of record (header-confirmed; no v1.2.1; filename "v1_0"
  stale), but it is a carry-in, not repo-committed. It is **not binding until registered.** Ready as a
  commit in the registration memo (memo 4) or an EXECUTE step before the spec - the spec must not treat
  it as binding until it lands.
- **Fact-layer canonical home.** `trophy_custody_events` engine-side home is "per the Manual Fact Import
  frame's adjudication." Confirm that placement in the spec; no build here.

---

## What memo 3 (spec) executes from these rulings

Given the D1-D4 rulings: render each of the five custody behaviors (Part A) and the Trophy Card; define
the `trophy_custody_events` shape for Groups 1-2 and the derived-holder reads for Groups 3-5; lay out the
sectioned Room and the per-trophy custody-timeline drill-in; bind the per-artifact governed text surfaces
(C7-attested PFL expansion; per-championship champion + year).

## Constitutional carry

C1 (current holder = derived read, never stored mutable state - reinforced by the Group 3-5 derived
reads). C2 (Clairvoyant: completed facts only). C7 CLOSED (PFL = Phony Football League, attested;
nameplate string choice is per-artifact spec). Boundary: heists with relish, **no points / no theft
leaderboards / no custody-streak mechanics**; append-only; silence over speculation for backfill gaps;
human approves publication.

## Provenance / status

DRAFT, DECIDE session 2026-06-21. Memo 2 of the Unit W.5 chain. Part A (partition) is probe output;
Part B frames D1-D5 for founder ruling. Pending ratification + commit; on ratification, the rulings feed
memo 3 (specification).

