# Trophy Room vs The Mantel - Delineation and Sequencing (DRAFT for ratification)

**Date drafted:** 2026-06-21
**Session type:** DECIDE (scoping / delineation). No repo or DB writes. This is a pre-specification
delineation memo, not a specification.
**Status:** DRAFT. Founder ratifies before commit. Once ratified, this seats the two surfaces in
the four-memo chain and orders their specs.
**Anchor verified:** engine HEAD `8d030c0`, main-only, unshallowed (1,329 commits). Active in-flight
docket item per `docs/STATE.md` is W.1 Inc 2 EXECUTE; W.2 / W.3 / W.5-taxonomy are overflow-only behind it.

---

## 1. Why this memo exists

The W.5 session brief titled its surface "Trophy Mantel / Trophy Room" and pointed it at the
trophy taxonomy behind the clubhouse trophy-case portal. That title fused two clubhouse objects
that the design keeps deliberately apart. The object-plate brief itself separates them:

- **Plate 1 - Trophy case -> Trophy Room** (trophies)
- **Plate 2 - Mantel + framed photos / polaroids -> A/V Room** (photos)

A spec written under the fused title would have rendered trophies on a surface meant for photos,
and would have attached a 37-artifact trophy taxonomy to a portal that does not lead to the Trophy
Room at all. This memo draws the boundary so that cannot happen, and sequences the two specs.

## 2. The delineation in one line each

- **The Trophy Room** is a distinct room of its own, with its own schema, that renders the league's
  trophies and plaques. It consumes the trophy taxonomy. It already exists in v1 (championship-only)
  as the shipped `/league/[id]/trophy-room` surface; W.5 grows it up to the full taxonomy.
- **The Mantel** is not a room. It is the clubhouse-side doorway into the **W.1 A/V Room** (Mr.
  Herlth's A/V Room, the archival photo/video room). Its framed photos are a portal/curation view
  over the A/V Room's existing media corpus - member-contributed during onboarding, or from the
  league archives. It owns no trophies, no taxonomy, and no new room or table.

## 3. Surface A - The Trophy Room

| Field | Value |
|---|---|
| Clubhouse portal | Plate 1, the trophy case |
| Room behind the click | The Trophy Room (its own room) |
| Already shipped | `/league/[id]/trophy-room` v1 - championship entries only, `trophy_room_entries` table (provenance enum; entry types CHAMPIONSHIP / PHYSICAL_TROPHY / COMMISSIONER_ATTESTED / SHAME_RECORD), `TrustBar`, community-page `TrophyPreview`, four-tab nav (Community / Archive / Trophy Room / Members). Design Brief sections 5.4, 7.6. |
| Input | Trophy taxonomy (latest verifiable artifact is **v1.2**; see section 8 on the version and C7 discrepancies). 37 artifacts across Annual (12), Positional (6), Draft/Auction (4), In-Season (1), Live Record (7), Permanent (5), plus the Championship Package (Belt / Ring / League Trophy). |
| Custody models to render | traveling (Belt), mint-and-keep (Ring), communal perpetual (League Trophy), annual, positional, draft, live-record, permanent. Current holder is always a DERIVED read off the append-only ledger (C1), never baked into a definition. |
| Governance specifics | Append-only facts; commissioner approves publication; Docket ID scheme + trust bar; the Belt/Ring/League Trophy nameplates are governed text surfaces; C7 (PFL expansion) is an OPEN attestation blocker for those nameplates - see section 8. |
| Capacity/growth | 16-and-growing seasons. The clubhouse trophy case stays fixed as the portal; the Room behind it carries the growth (curated/featured display, sectioned views, multiple cabinets). This is the main open design decision for the Trophy Room spec. |
| Explicitly NOT in this surface | Photos as ceremonial display (those are the Mantel/A/V Room). No member-memory testimony rendering (that is L.1). No prediction or custody gamification. |

## 4. Surface B - The Mantel

| Field | Value |
|---|---|
| Clubhouse portal | Plate 2, the mantel with framed photos / polaroids |
| Room behind the click | The **W.1 A/V Room** (Mr. Herlth's A/V Room) - an EXISTING room, not a new one |
| Already shipped | W.1 Inc 1 (A/V Room foundation) merged + discharged; W.1 Inc 2 (member captions, two-layer "as remembered by" display) currently the active EXECUTE item. `media_entries` is the item attach point. Photo-first tooling per D-G; video accepted. |
| Input | The A/V Room's existing media corpus: photos contributed by members during onboarding, and photos from the league archives. No taxonomy. |
| What the Mantel surface itself adds | A clubhouse-side portal treatment: a curated/featured set of framed photos on the mantel that reads as a doorway and links into the full A/V Room. (Exact curation rule - most recent, founder-pinned, or rotating - is a Mantel-spec decision.) |
| Governance specifics | Inherits the A/V Room's governance: provenance on every media item; member captions are governed testimony (separate fact class, never merged into event facts); a photo whose year is unknown carries no year, not a guessed one (silence over speculation); commissioner approves publication. |
| Explicitly NOT in this surface | No trophies. No trophy taxonomy. No Belt/Ring/League Trophy. No new room. No new table or schema - the Mantel reads from `media_entries`, it does not mint its own store. |

## 5. The boundary - non-crossing rules (the certainty)

1. **A trophy never appears on the Mantel.** Trophies render only in the Trophy Room.
2. **A photo never appears in the Trophy Room as a trophy.** A championship photo can exist as an
   A/V Room media item shown on the Mantel; it does not become a `trophy_room_entries` row by being
   photographed. (The shipped schema's `PHYSICAL_TROPHY.image_url` is a photo OF a trophy attached to
   a trophy entry - that is inside the Trophy Room and stays there; it is not a Mantel item.)
3. **The Mantel mints no room and no schema.** It is a portal/curation view over W.1 `media_entries`.
   All persistence belongs to the A/V Room.
4. **The Trophy Room owns the taxonomy in full; the Mantel owns none of it.** The 37 artifacts, the
   eight custody models, and the Championship Package live entirely in the Trophy Room spec.
5. **Shared UI is reused, not forked, and carries no semantic bleed.** `TrustBar`, the provenance
   model, and the commissioner approval flow are common infrastructure (section 6). A trust bar on a
   Mantel photo attests the photo's provenance; a trust bar on a Trophy Room card attests the
   trophy's provenance. Same component, different subject. Neither surface's governance state leaks
   into the other.
6. **Lineage:** Trophy Room = trophy lineage (taxonomy, `trophy_room_entries`). Mantel = A/V lineage
   (W.1, `media_entries`, member captions). Cross-references are by link only, never by shared store.

## 6. Shared infrastructure that legitimately touches both

These are common and should be reused across both surfaces without duplication:

- **TrustBar / provenance variants** (CANONICAL, COMMISSIONER_ATTESTED, DEMO, DRAFT/APPROVED). A
  shared `PROVENANCE_LABEL` / `PROVENANCE_STYLE` module was already flagged for extraction in the
  Trophy Room tighten memo; both surfaces are consumers.
- **Commissioner approval flow** (AI assists, human approves publication) - constitutional, applies
  to any shareable artifact on either surface.
- **The four-tab nav** (Community / Archive / Trophy Room / Members). The Trophy Room already has a
  tab. The Mantel is reached through the clubhouse, not the top nav, so it adds no tab - confirm in
  the Mantel spec.

## 7. Sequencing (recommendation)

**Spec the Trophy Room first, the Mantel second.**

Rationale:

- The Trophy Room has both a ratified taxonomy input ready to consume and a shipped v1 to grow.
  Its spec has momentum and a clear lineage. STATE already labels this work "W.5-taxonomy."
- The Mantel depends on things still in flight: it is a portal over the W.1 A/V Room, whose Inc 2
  (member captions) is the active EXECUTE item, and it is rendered on W.2 plate 2 (the mantel plate),
  which is part of the clubhouse-integration track. A Mantel spec written before the A/V Room corpus
  and the clubhouse portal mechanics settle would be speculative about its own inputs.
- The two specs share infrastructure (section 6); writing the Trophy Room first lets the Mantel spec
  reference the extracted provenance/trust-bar module rather than re-derive it.

Dependencies to record:

- Trophy Room spec depends on: C7 attestation resolution (section 8) and a reconciliation of the
  taxonomy against the shipped `trophy_room_entries` schema.
- Mantel spec depends on: A/V Room corpus maturity (W.1), W.2 plate-2 finalization, and the curation
  rule for which photos surface on the mantel.

## 8. Open items each downstream spec must resolve (carried forward, not decided here)

- **C7 - PFL expansion, OPEN (Trophy Room).** The latest verifiable taxonomy (v1.2) marks the PFL
  expansion as generator-guessed and NOT attested - the same hazard class as the founding year
  (generator said 1985, arithmetic said ~1986, attested truth was 1984). It is blocking for the
  Belt / Ring / League Trophy nameplates. Until a human attestation with provenance fields
  (attested by / attested on / basis) exists, those nameplates stay governed-blank, same handling as
  the clubhouse banner. The session brief asserted "C7 closed, PFL = Phony Football League,
  founder-attested" - that string appears only in the brief, not in the taxonomy or git. If an
  attestation record exists, supply it and the Trophy Room spec consumes it as fact.
- **Taxonomy version (Trophy Room).** Brief cites v1.2.1; the latest artifact on hand is v1.2.
  Confirm whether a v1.2.1 exists and supersedes; otherwise v1.2 is the input of record.
- **Shipped-schema reconciliation (Trophy Room).** The shipped `trophy_room_entries` has four entry
  types; the taxonomy has six categories plus the Championship Package. The Trophy Room
  decision-readiness memo must decide how the taxonomy maps onto (or extends) the shipped schema.
- **Mantel curation rule.** Which photos surface on the mantel, and how the portal links into the
  full A/V Room.
- **Roadmap label cleanup.** "W.5 trophy Mantel" baked the conflation into the label itself. Ratified
  (founder ruling 2026-06-21, see OBSERVATIONS_2026_06_21_TROPHY_ROOM_NAMING_RULING):
  W.5 = the Trophy Room (trophies, taxonomy); the Mantel = a W.1 A/V-Room portal (A/V lineage),
  so the label stops carrying the fused name.

## 9. Session discipline

- DECIDE only; nothing written to repo or DB this session.
- This memo is the pre-spec delineation. In the four-memo chain, the Trophy Room and the Mantel each
  still need selection-prep -> decision-readiness -> specification -> registration; per git neither has
  started one yet (no W.5 or Mantel memo exists in `_observations/`). This memo feeds both chains.
- Commit ratified decisions before any "ratification needed" language reaches a committed spec.
