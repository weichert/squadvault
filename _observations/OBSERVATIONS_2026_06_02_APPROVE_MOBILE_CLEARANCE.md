# Observation — Approval-UX Mobile Clearance (Phase 11, Design Brief §VIII)

**Date:** 2026-06-02
**Repo of record:** frontend (`weichert/squadvault-frontend`)
**Frontend commit:** `f32da90`
**Engine commit (this memo):** docs-only; `prove_ci` skipped per established pattern.
**Closes:** the deferred adjacency filed in
`_observations/OBSERVATIONS_2026_06_02_MOBILE_BOTTOM_TAB_BAR.md` §7
(Approval-UX mobile action-zone stacking).

---

## 1. The collision

The mobile bottom tab bar (frontend `64d18ad`) is fixed at the bottom of the
viewport at `zIndex: 50` across all active-league surfaces, including the
approval reading view at `/league/[id]/approve/[artifactId]`. Three fixed-bottom
elements in `artifact-review.tsx` share that anchor and z-index and would overlap
the bar on mobile: the **action zone** (Approve / Withhold / Request Changes, at
`bottom: 0`), the post-approval **"The record is open."** line, and the
**withheld** card (both at Tailwind `bottom-8` = 2rem).

## 2. The fix (contained, spec-consistent)

§VIII keeps the bar present on every surface; the resolution is to lift the
approve-route fixed elements above it rather than suppress the bar. Two
responsive clearance classes in `globals.css` own the `bottom` offset:

- `.approve-action-zone` → `bottom: calc(var(--bottom-nav-height) + safe-area)`
  on mobile, `bottom: 0` at `md` and up.
- `.approve-floating-bottom` → `bottom: calc(2rem + var(--bottom-nav-height) +
  safe-area)` on mobile, `bottom: 2rem` at `md` and up.

`--bottom-nav-height` already cascades from the `.league-shell` wrapper set in
the league layout, so no new wiring is needed. `artifact-review.tsx` changes are
three surgical edits: the action zone drops its inline `bottom: 0` and takes
`.approve-action-zone`; the two `bottom-8` floating states swap to
`.approve-floating-bottom`. Desktop rendering is byte-unchanged (the bar does not
exist there; the `md` overrides restore `bottom: 0` / `bottom: 2rem`).

## 3. Doctrinal posture

Presentational only. No fact, narrative, governance, or persisted state is
touched. The scroll-to-unlock approval gate, the stamp ceremony, and the
state-machine actions are untouched — this only moves where the already-built
action zone sits on small viewports.

## 4. Local validation

Reproduced against the post-`64d18ad` tree: apply is anchor-asserting and
idempotent (second run is a no-op), and `npm run type-check` is clean (exit 0)
with the nav and approval-clearance changes coexisting. Governance tests not run
(no RLS / state-machine / trust-bar surface touched).

## 5. Confidence

- **Highest:** the clearance math and the desktop-unchanged guarantee
  (`md` overrides restore the original offsets); type-check-clean.
- **Medium-high:** correct by construction but not visually verified on a real
  device this session — Steve's mobile pass on the approve route (scroll to
  unlock, confirm the buttons sit clear above the bar) is the confirmation.
- **Deliberate silence:** no change to whether the bar *should* appear on a
  focused approval task at all (a §VIII "full-screen article view" reading would
  suppress chrome); that remains a larger design question, not opened here.
