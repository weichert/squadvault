# Observation — Mobile Bottom Tab Bar (Phase 11, Design Brief §VIII)

**Date:** 2026-06-02
**Repo of record for the change:** frontend (`weichert/squadvault-frontend`)
**Frontend commit:** `64d18ad`
**Engine commit (this memo):** docs-only; `prove_ci` skipped per established pattern.
**Closes:** Tighten memo §6 **item 4** (mobile bottom tab bar implementation).
**Predecessor reads:** `_observations/OBSERVATIONS_2026_05_31_MOBILE_NAV_SLOT_COMPOSITION.md`
(item 4(a), §VIII-canonical composition), `OBSERVATIONS_2026_05_31_COMMISSIONER_ONLY_403`
(item 4(b), Forbidden rendering at the Office route), and the commissioner-rule
separator + Office tab shipment (frontend `0bcf7fb`).

---

## 1. Decision record

Three direction-laden choices were surfaced (D1–D3) and Steve accepted all
recommendations.

- **D1 — Where the bar lives → fold into `top-nav.tsx`.** The mobile bottom bar
  is a second presentation rendered from the *same* `PUBLIC_TABS` /
  `COMMISSIONER_TABS` arrays and the same `isActive` logic that the desktop bar
  uses. No tab-definition duplication; the layout still imports a single
  `TopNav`. (Alternatives: a separate component importing the arrays; a separate
  component duplicating them — rejected.)
- **D2 — Slot presentation & active indicator → label-only, gold top-rule.**
  Mono uppercase labels mirroring the desktop register; no icon vocabulary
  introduced (icons would be a separate design decision and risk the
  "friendly tech product" anti-pattern, §IX). The active indicator is a short
  gold rule along the **top** edge of the active slot — facing the content, the
  way the desktop underline faces its label — rather than an underline hugging
  the screen edge. (Alternative: icon + label — rejected for scope and
  anti-pattern risk.)
- **D3 — Commissioner separator → vertical dim rule before Office.** Reuses the
  desktop separator's token (`--vault-border` at 0.6 opacity), sized vertically
  for the bar. Preserves the §5.4 "separated visually by a dim rule" governance
  signal. (Alternatives: tint the Office slot; drop the separator — both
  rejected.)

## 2. Composition is §VIII-canonical (reaffirmed, not re-opened)

The only place the brief contradicts itself on this surface is **§VIII vs
§5.4**: §VIII enumerates *five separate slots* (Community, Archive, Trophy Room,
Members, Office); §5.4 says *"Archive and Trophy Room share one slot with a
sub-menu,"* which would yield four surface-slots. This conflict was already
resolved against §VIII in the item 4(a) memo, which the `top-nav.tsx` header
comment cites. This dispatch implements the §VIII reading: five separate slots,
Office last, no Archive/Trophy sub-menu. No re-litigation.

## 3. What shipped (four frontend files, one commit)

- **`src/components/ui/top-nav.tsx`** — refactored into `DesktopNav`
  (`hidden md:block`, output byte-identical to the prior bar) and `MobileTabBar`
  (`md:hidden`, `position: fixed; bottom: 0; zIndex: 50`, matching the
  `artifact-review.tsx` fixed-bottom precedent). `TopNav` renders both from one
  `usePathname()` read. Mobile slots: `flex:1`, `minWidth/minHeight: 44`,
  centered mono labels (wrap permitted for "Trophy Room"), gold when active.
- **`src/app/league/[id]/layout.tsx`** — wrapper now sets `--bottom-nav-height`
  alongside `--nav-height` and carries `.league-shell`, a mobile-only bottom
  offset so scrollable content clears the fixed bar.
- **`src/app/league/[id]/page.tsx`** — the community plaque's negative-margin
  overlap moved from an inline style to `.plaque-overlap`.
- **`src/app/globals.css`** — `.plaque-overlap` (overlap **desktop-only**),
  `.league-shell` (mobile bottom offset incl. `env(safe-area-inset-bottom)`),
  and `.nav-rule-active` + the `navRuleIn` keyframe (0.22s center-grow, no
  delay) with a `prefers-reduced-motion: reduce` guard.

## 4. The plaque-overlap interaction (why page.tsx and globals.css are in scope)

The community page pulls its `<main>` up by `--nav-height` to let the founding
plaque occupy the viewport (the top nav stays in the DOM, covered). Hiding the
desktop nav on mobile (`hidden md:block`) makes that negative margin pull
against zero height, **clipping the plaque top by 80px**. The fix scopes the
overlap to `md` and up; on mobile the plaque starts at the top and the bottom
bar (zIndex 50, fixed) floats above it. Desktop behavior is unchanged.

## 5. Doctrinal posture

No fact, narrative, or governance surface is touched. This is presentational
chrome. Office visibility on the mobile bar follows the §VIII principle exactly:
the tab is shown to everyone and the Forbidden render stays at the route — **no
role logic lives in the nav** (item 4(b) remains the single source of the 403).
No analytics, no engagement instrumentation, no new persisted state.

## 6. Local validation

Reproduced against a fresh clone at frontend `0bcf7fb`: the apply script is
anchor-asserting and idempotent (second run is a no-op), and `npm run
type-check` (`tsc --noEmit`) is **clean, exit 0**, on the transformed tree.
Governance tests were not run locally (no RLS / state-machine / trust-bar
surface is touched); they remain green as of the 2026-05-31 staging run.

## 7. Deferred adjacency (captured, not solved)

On the Office/approval route, `artifact-review.tsx` pins an action zone with
`fixed bottom-8`. On mobile that would stack against the bottom tab bar
(56px + safe area). The Approval UX is commissioner-only and desktop-primary
(§VIII), so the mobile stacking resolution is filed as a follow-on
**Approval-UX mobile pass**, not folded into this nav port.

## 8. Confidence

- **Highest:** the §VIII five-slot composition; no-role-logic-in-nav posture;
  type-check-clean transform.
- **Medium-high:** the plaque-overlap desktop-only fix is correct by
  construction and type-checks, but has not been visually verified on a real
  device this session (Steve's manual mobile-viewport pass is the confirmation).
- **Deliberate silence:** no icon set, no PWA/home-screen manifest, no
  device-frame visual QA captured here — all out of this port's scope.
