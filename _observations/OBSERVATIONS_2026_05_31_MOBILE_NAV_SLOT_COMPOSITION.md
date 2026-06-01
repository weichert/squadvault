# Mobile Nav Slot Composition — §VIII Canonical

**Date:** 2026-05-31 (post-tighten dispatch session)
**Closes:** Prerequisite (a) of §6 item 4 in
  `OBSERVATIONS_2026_05_31_TROPHY_ROOM_TIGHTEN.md`
**Frontend commit:** _none — decision-only, no code change_

---

## What

The Design Brief contained an ambiguity about mobile bottom tab bar
composition:

- **§5.4 (Navigation):** "Mobile: the navigation collapses to a
  bottom tab bar with five slots. Archive and Trophy Room share one
  slot with a sub-menu."
- **§VIII (Mobile Strategy):** "Bottom navigation tab bar on mobile
  (5 slots: Community, Archive, Trophy Room, Members, Office). Only
  the commissioner sees the Office tab. All others see it but it
  requires commissioner auth."

Both passages declare five slots but compose them differently. §5.4
combines Archive and Trophy Room into a sub-menu slot. §VIII treats
them as separate peer slots and names Office as the fifth.

**Resolution: §VIII composition is canonical. §5.4's "Archive and
Trophy Room share one slot with a sub-menu" language is superseded.**

The canonical mobile bottom tab bar composition is therefore:

| Slot | Surface | Visibility |
|---|---|---|
| 1 | Community | All members |
| 2 | Archive | All members |
| 3 | Trophy Room | All members |
| 4 | Members | All members |
| 5 | Office | Visible to all; 403 for non-commissioners |

## Why

Four reasons, in descending weight:

1. **Implementation already matches §VIII.** The current desktop nav
   (frontend `8b7ba23`) has four peer tabs: Community, Archive,
   Trophy Room, Members. §VIII's mobile composition is the direct
   extension of that pattern with Office added as the fifth slot.
   §5.4's mobile composition would break desktop/mobile parity by
   combining tabs on mobile that are peers on desktop.

2. **Archive and Trophy Room are categorically different.** Archive
   is the working periodical record (§7.2 "feel like browsing a
   well-maintained periodical archive"). Trophy Room is the
   ceremonial surface (§7.6 "the league-level ceremonial surface,
   the most visually ambitious page"). Putting them in a shared
   sub-menu lumps these categorically distinct surfaces under a
   generic "history" header that loses both framings.

3. **§7.6 names Trophy Room as "the most visually ambitious page."**
   That is a peer-destination claim, not a sub-menu-item claim.

4. **Sub-menus on bottom tab bars are unusual UX.** Most mobile apps
   keep bottom tab bar items at the same hierarchy level. Sub-menus
   require popover-on-tap or long-press affordances, both uncommon
   and easy to miss. The §VIII composition avoids this entirely.

### What about Office and Approval as separate desktop items?

§5.4 also references "commissioner-only items (Office, Approval)
separated visually by a dim rule" on desktop. The current
implementation does not have a separate top-level Approval route —
approval is reached via `/league/[id]/approve/[id]` from the Office
queue. §VIII's "Office only" composition matches that implementation
pattern. This memo does not resolve the Office-vs-Approval question
for desktop (it is not part of the ambiguity being resolved here),
but observes that §VIII's collapsed treatment matches reality.

## Scope of decision

- Mobile bottom tab bar composition only.
- No frontend code change. The four-tab desktop nav shipped in
  `8b7ba23` is unchanged; this decision applies to future mobile
  bottom tab bar implementation.
- No Design Brief amendment. The brief is canonical at its current
  version. This memo serves as the canonical pointer for the §5.4
  vs §VIII reconciliation until the brief gets its next version
  pass.
- Engine-side governance trail only. No commit on the frontend repo
  (no code touched).

## What this unblocks

Tighten memo §6 item 4 (mobile bottom tab bar) had two prerequisites:

- **(a) Resolve §5.4 vs §VIII Archive/Trophy slot ambiguity.**
  Closed by this memo.
- **(b) Role-aware 403 rendering for the Office slot.**
  Still open as §6 item 5.

The mobile bottom tab bar implementation remains blocked on
prerequisite (b). When 403 rendering lands, the implementation can
proceed directly against the §VIII composition without revisiting
the slot question.

There is a partial path forward worth noting: a four-slot mobile
bottom tab bar (Community, Archive, Trophy Room, Members, no
Office) could ship before 403 rendering lands. That would match the
current desktop nav exactly and defer Office until 403 work
finishes. Not proposing it here — just naming that the §VIII
composition makes that intermediate step coherent rather than
ad-hoc.

## What this does not resolve

- The Office-vs-Approval desktop ambiguity in §5.4 (commissioner-
  only items separated by a dim rule). Out of scope; the
  implementation has already collapsed to Office-only, and §VIII
  agrees with that collapse for mobile. A future session can
  formally retire the Approval-as-separate-item language if needed.
- Whether the Design Brief gets amended in a future version pass to
  remove the superseded §5.4 sub-menu sentence. Out of scope; the
  brief is canonical at the version that exists.

## Cross-repo continuity

Engine memo only. The frontend repo gets no companion commit because
no frontend code changed. Follows the established pattern of paired
governance trails only when both repos receive substantive changes
(audience-split `044d07c`, Trophy Room UI v1 `e5aa22e`, Trophy Room
tighten `e160b5d`, office back-link `6ff4b2b`).
