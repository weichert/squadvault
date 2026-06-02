# Role-Aware 403 Rendering — Item 4(b) Closure

**Date:** 2026-05-31 (post-tighten dispatch session)
**Frontend commit:** `9e9b953`
**Closes:** §6 item 4(b) prerequisite of
  `OBSERVATIONS_2026_05_31_TROPHY_ROOM_TIGHTEN.md`

---

## What

Replaced silent redirects on the Office and Approve routes with an
explicit Forbidden rendering: a vault-card stating "This room is
reserved for the commissioner" plus a small return link. Per Design
Brief §VIII visibility principle: commissioner-only rooms are visible
to all roles but display a 403 state rather than being invisible.

## Why

The pre-existing pattern silently redirected non-commissioners back to
the community page on Office and Approve. That treatment violated §VIII
visibility principle in two ways: the visitor never saw they had been
denied entry, and the rooms behaved as if they did not exist. The
Forbidden rendering closes that gap. Members can know Office exists,
know what it is, and not be able to enter — which is the principle the
brief is asserting.

This change was dispatched in five decisions:

- **D1 — Which pages get the refactor.** Both Office and Approve.
  Refactoring only Office would have left a known inconsistency at the
  Approve route which has the same silent-redirect pattern.
- **D2 — Visual treatment.** Full page structure on Office (h1 +
  divider + back-link header above the Forbidden card), bare card on
  Approve (deep-link to a specific artifact, no room identity to
  show). Card copy: "This room is reserved for the commissioner."
- **D3 — Unauthenticated users.** Anon visitors continue to redirect
  to `/auth/login`. The Forbidden state is for "you're someone, but
  not the right someone," not for "you're nobody."
- **D4 — Component name.** `CommissionerOnly`. Most descriptive at
  import sites; the only role-restriction on the immediate horizon is
  commissioner-only, so the specific name reads clearer than a
  generic `Forbidden` or `RestrictedRoom`.
- **D5 — Null commissioner edge case.** Renders Forbidden under the
  existing inequality check (`null !== user.id` is true). Simpler
  than a special case and rare (only at early founding state, which
  has its own LockedRoom path).

## Scope of change

Three files, frontend repo:

- **NEW** `src/components/ui/commissioner-only.tsx` — server
  component, no hooks. Renders a vault-card with font-ceremonial
  italic copy at 1.2rem (matches the members empty-state stub) and a
  small font-mono return link (matches the restored Office back-link
  treatment).
- **EDIT** `src/app/league/[id]/office/page.tsx` — adds the
  CommissionerOnly import, replaces the `redirect(...)` call with a
  Forbidden-render branch that keeps the Office header (back-link +
  h1 + divider) above the locked card.
- **EDIT** `src/app/league/[id]/approve/[artifactId]/page.tsx` —
  adds the CommissionerOnly import, replaces the `redirect(...)`
  call with a Forbidden-render branch showing the bare card (no
  Office header — the Approve route is a deep link, not a room).

No tests touched. No styling tokens introduced. No imports beyond
the new component. Type-check passed locally on the dispatcher's
clone before commit.

## What this unblocks

Tighten memo §6 had two items gated on role-aware 403 rendering:

- **Item 4 — Mobile bottom tab bar.** Two prerequisites: (a) §5.4
  vs §VIII slot composition ambiguity, (b) role-aware 403 rendering.
  Prerequisite (a) closed in `7f61e89` (engine memo). Prerequisite
  (b) closed by this commit. Item 4 is now fully unblocked; the
  remaining work is implementation against the §VIII composition.
- **Item 5 — Commissioner-rule separator (Office, Approval in nav).**
  Blocked on role-aware 403 rendering only. Now unblocked. The
  TopNav currently does not know viewer identity; the follow-on work
  is to wire commissioner status into the layout, surface the Office
  tab (visible to all, leading to the Forbidden state for
  non-commissioners), and add the dim rule separator per §5.4.

## What this does not close

- **Item 5 itself.** This commit produces the Forbidden component
  but does not wire it into the nav. That is a clean follow-on
  session — TopNav becomes role-aware, gains the Office tab with the
  dim rule separator, and the existing four-tab nav becomes a
  five-tab nav. Splitting this out keeps blast radius bounded and
  each commit one-topic.
- **Mobile bottom tab bar implementation.** Same shape as the
  nav-wiring follow-on, but for mobile. Naturally bundled with item 5
  since both consume the same role-awareness wiring.
- **Office/Approval as separate desktop items** (§5.4 dim-rule
  separation). The current implementation collapses Approval into the
  Office queue; item 5's follow-on will not introduce a separate
  Approval tab.

## Cross-repo continuity

Engine memo paired with frontend commit per established pattern
(audience-split `044d07c`, Trophy Room UI v1 `e5aa22e`, Trophy Room
tighten `e160b5d`, office back-link `6ff4b2b`, mobile nav slot
composition `7f61e89`).
