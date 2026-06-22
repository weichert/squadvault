# A/V Room Name - Attested Basis (governed text surface provenance) - DRAFT

**Date:** 2026-06-21
**Session type:** DECIDE. No repo or DB writes. DRAFT for founder ratification + commit.
**Subject:** The rendered name "Mr. Herlth's A/V Room" (Unit W.1).
**Class:** Governed text surface provenance - same handling as the clubhouse banner
("PFL Buddies . Est. 1984"). The name renders in the product; its basis is recorded as an
attested fact, not a generated one.

---

## The governed text surface

"Mr. Herlth's A/V Room" - the displayed name of the W.1 archival photo/video room
(Mr. Herlth's A/V Room, the room the clubhouse Mantel portal opens into).

## Attested basis

| Field | Value |
|---|---|
| Honors | Ben Herlth |
| Who he is | Longtime PFL member; franchise `0008` (league 70985); team "the Gods" |
| Why this room | Media teacher by trade, so the league's media room is the fitting one to carry his name |
| Attested by | Steve (founder) |
| Attested on | 2026-06-21 |
| Basis | Founder first-hand knowledge |

## Corroboration

- Member identity is corroborated in canonical data: `scripts/seed_pfl_buddies_nicknames.sql`
  maps franchise `0008` / league `70985` to "Ben" (one of the ten PFL Buddies members).
- "The Gods" (team name) and "media teacher" (profession) rest on founder first-hand
  attestation; the team-name string is not in the engine repo (the nickname seed holds member
  names, not team names) and would be confirmed against the canonical franchises table in an
  EXECUTE session if a pinned-to-canonical record is ever wanted. Founder first-hand attestation
  is itself a gold-standard provenance source here and is not treated as a guess.

## Note on a corrected assumption (for the record)

An earlier draft of this basis read "high school media teacher" as if Ben were outside the
league. That was an unattested relationship bolted onto an attested fact - the same hazard class
as C7 (the generator-guessed "Phony Football League" expansion) and the founding-year saga
(generator 1985 / arithmetic ~1986 / attested 1984). The basis above carries only attested or
corroborated fields; nothing inferred.

## Recall placement (recommended)

- **Canonical anchor:** add a one-line attested-basis note to the W.1 unit entry in
  `docs/SquadVault_Product_Document_of_Record_v2_1.md` (line ~111), pointing here. This is the
  highest-recall location - it is where a future session reads what the A/V Room is.
- **Governing consumers:** the W.1 A/V Room specification
  (`_observations/OBSERVATIONS_2026_06_10_W1_AV_ROOM_SPECIFICATION.md`) governed-text-surface
  treatment, and the forthcoming Mantel spec (the Mantel portal surfaces this room name).
- **This memo** is the dated, append-only attestation record both of the above point to.

## Status

Founder-attested in session 2026-06-21. DRAFT pending founder ratification and commit; the DoR
one-line pointer is a next doc/EXECUTE-session edit (not written this DECIDE session).
