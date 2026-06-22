# Trophy Room vs Mantel - Naming Ruling (governing memo) - DRAFT

**Date:** 2026-06-21
**Session type:** DECIDE (adjudication). No repo or DB writes this session. DRAFT for founder ratification + commit.
**Anchor:** engine HEAD `8d030c0`; DoR `v2.1` at HEAD (`docs/SquadVault_Product_Document_of_Record_v2_1.md`).
**Governs:** the DoR's Unit W.5 / "the Mantel" naming. Carries a DoR v2.1.2 supersession note (section 4).

---

## 1. The ruling

Founder ruling, 2026-06-21: **the trophy-display surface is "the Trophy Room"; the name "the Mantel"
is reassigned to the framed-photo fixture, which is the clubhouse portal into the A/V Room.** Align
the names to the clubhouse art direction, and amend the DoR to match.

## 2. The collision this resolves

The DoR carried two namings for the trophy surface that the later clubhouse art split apart:

- DoR W.2 navigation (line 113): "trophy case -> Trophy Room, framed photos -> A/V Room door." The
  trophy-case destination is "Trophy Room"; the photo path goes to the A/V Room.
- DoR Unit W.5 (lines 119, 121): "Trophy custody system ('the Mantel')," whose display layer is
  "the Mantel in the clubhouse scene."

So the DoR named the trophy custody display "the Mantel." The W.2 art direction then drew a trophy
CASE for trophies (-> Trophy Room) and a literal MANTEL holding framed photos (-> A/V Room). The art
moved the trophies into a case and put photos on the mantel, and the unit-name "the Mantel" stopped
matching what the mantel holds. This ruling aligns the names to the art.

## 3. Naming canon (ratified)

- **The Trophy Room** - the trophy-display surface behind the clubhouse trophy-case portal. Home of
  the trophy custody system (Unit W.5). Today it is the shipped flat `/league/[id]/trophy-room`
  (`trophy_room_entries`, championship-only); W.5 grows it to full custody (`trophy_custody_events`,
  provenance chains, the v1.2 taxonomy). This name supersedes the DoR's "the Mantel" for W.5's display.
- **The Mantel** - the literal mantelpiece fixture in the clubhouse scene holding framed photos /
  polaroids. It is the navigation portal into Mr. Herlth's A/V Room (Unit W.1). It holds no trophies
  and is not a unit of its own; it is a doorway into W.1.
- **The A/V Room (Mr. Herlth's A/V Room)** - the archival photo/video room (Unit W.1), reached via
  the Mantel.

## 4. DoR amendment - v2.1.2 supersession note (insert after the v2.1.1 note, top of DoR)

Per the DoR's append-only convention (body retained unmodified; supersession notes plus a governing
memo carry the change, exactly as the v2.1.1 / W.6 note does), add:

> **v2.1.2 supersession note (2026-06-21):** Part 3 Unit W.5 names the trophy custody surface "the
> Mantel," and its Display-layer bullet calls the display "the Mantel in the clubhouse scene."
> Founder ruling 2026-06-21 (governing memo
> `_observations/OBSERVATIONS_2026_06_21_TROPHY_ROOM_NAMING_RULING.md`) **supersedes** that naming.
> The trophy-display surface behind the clubhouse trophy-case portal is **"the Trophy Room"** -
> already the W.2 nav name at line 113 ("trophy case -> Trophy Room"). The name **"the Mantel"** is
> reassigned to the literal mantelpiece fixture holding framed photos, which is the navigation portal
> into Mr. Herlth's A/V Room (Unit W.1, "framed photos -> A/V Room door" at line 113). Unit W.5's
> identity, fact layer (`trophy_custody_events`), boundary, and four-memo chain are unchanged; only
> the display-surface name changes from "the Mantel" to "the Trophy Room." DoR body text below (lines
> ~119, ~121, ~230, ~238) is retained unmodified per append-only discipline; where it says "the
> Mantel"/"the mantel" in reference to the trophy display, read "the Trophy Room" per this note.

The W.2 nav line (113) already matches the ruling and needs no change. The closing flourish (line 238,
"put the trophies on the mantel with their criminal records") is poetic and may stay as metaphor or be
refreshed at a future W.2 touch-point; non-blocking, founder's call.

## 5. What this does NOT change

- Unit W.5's identity, scope, fact layer (`trophy_custody_events`), boundary (no points / no theft
  leaderboards / no custody-streak mechanics), and four-memo chain.
- The shipped `trophy_room_entries` table name (it is already "Trophy Room"-aligned).
- Unit W.1 (Mr. Herlth's A/V Room) and its A/V lineage.
- C1 / C2 / C7. C7 (PFL expansion) remains OPEN; the Belt/Ring/League Trophy nameplates stay
  governed-blank until attested. This ruling is about surface naming, not the nameplate attestation.

## 6. Landing plan (EXECUTE / doc session - repo writes, not this DECIDE lane)

Order to commit, one topic per commit:

1. **DoR:** insert the v2.1.2 supersession note (section 4). Body unchanged.
2. **This ruling memo** -> `_observations/OBSERVATIONS_2026_06_21_TROPHY_ROOM_NAMING_RULING.md`.
3. **Delineation memo** (`..._TROPHY_ROOM_vs_MANTEL_DELINEATION_AND_SEQUENCING`) - now consistent
   with the DoR under this ruling; its section 8 "proposed" label becomes "ratified per this memo."
   Add a pointer to this ruling + the supersession note.
4. **A/V Room name attestation** (`..._AV_ROOM_NAME_ATTESTATION_HERLTH`).
5. **STATE.md:** seat the Trophy Room (W.5) and record the naming ruling + the Mantel-as-A/V-portal.

Then, and only then, the Trophy Room selection-prep (memo 1) opens. The selection-prep brief and
prompt already drafted hold under this ruling; their pre-work should additionally confirm the v2.1.2
note and this memo are committed.

## 7. Provenance

Founder-attested ruling. Attested by: Steve (founder). Attested on: 2026-06-21. Basis: align the
DoR's W.5/Mantel naming to the clubhouse art direction (trophy case -> Trophy Room; mantel holds
photos -> A/V Room), consistent with the DoR's own W.2 nav line. DRAFT pending ratification + commit.
