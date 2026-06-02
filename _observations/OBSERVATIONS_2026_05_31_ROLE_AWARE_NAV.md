# Commissioner-Rule Separator & Office Tab — Item 5 Closure

**Date:** 2026-05-31 (post-tighten dispatch session)
**Frontend commit:** `0bcf7fb`
**Closes:** §6 item 5 of `OBSERVATIONS_2026_05_31_TROPHY_ROOM_TIGHTEN.md`

---

## What

The top navigation now renders five tabs: Community, Archive, Trophy
Room, Members, then a dim-rule separator, then Office. Office is
visible to all viewers regardless of role per Design Brief §VIII
visibility principle. Non-commissioners reach the rendered Forbidden
state (`CommissionerOnly` component, shipped in frontend `9e9b953`)
when they click it; anonymous viewers reach the login flow first,
then Forbidden after auth.

A new `getViewer(canonicalId)` helper in `src/lib/league.ts` returns
`{ userId, isCommissioner }`, wrapped in `React.cache()` alongside
`getLeague`. The Office and Approve pages now use it instead of their
inline `createServerClient + auth.getUser + commissioner-id compare`
sequences. The helper composes naturally with `getLeague`: a single
auth lookup and a single league lookup per render request, regardless
of how many gated routes within that render call them.

## Why

§6 item 5 of the tighten memo named the commissioner-rule separator
as the next surface decision blocked by role-aware 403 rendering.
That prerequisite was closed by frontend `9e9b953` and engine memo
`6720c89`. With role-aware 403 in place, the Office tab can ship as
a peer slot — visible to everyone, denied to non-commissioners at
the route rather than at the nav. This is the §VIII pattern: rooms
are not hidden, only locked.

## Decisions

Dispatched as five decisions:

- **D1 — Visual treatment.** Dim rule yes (1px × 12px vertical,
  `var(--vault-border)` at 0.6 opacity, vertically centered between
  Members and Office). Office tab uses the same styling as public
  tabs — the 403 page does the denial work, not the tab styling.
  Muting the tab would add a second signal that fights the "not
  hidden" principle.
- **D2 — Component identity.** Two arrays (`PUBLIC_TABS` and
  `COMMISSIONER_TABS`), not one array with a flag. The dim rule is a
  structural separator between regions, not a per-tab decoration.
- **D3 — Server vs client split.** TopNav stays a Client Component
  (it uses `usePathname()` for active state). Per D5 it shows Office
  to everyone, so the layout doesn't currently pass a role prop. A
  future iteration that wants conditional hiding can add an
  `isCommissioner` prop without restructuring.
- **D4 — Helper shape.** `getViewer` returns
  `{ userId: string | null; isCommissioner: boolean }`. A bare
  boolean helper would have conflated anon with non-commissioner and
  forced the gated pages to keep separate anon checks anyway. This
  was a revision of an initial D4 recommendation: the shape needs to
  carry both pieces of information.
- **D5 — Anonymous viewers.** See the Office tab. Clicking leads to
  the login flow, then 403 after auth. The visibility principle is a
  single coherent path: visible to everyone, denied at the route.
  The alternative (hide for anon, show for authenticated) would mean
  two different navs for two unauthenticated states.

## Scope of change

Four files edited in the frontend repo:

- **`src/lib/league.ts`** — appends `getViewer` cached helper and a
  `Viewer` type export. Adds `createServerClient` to the import line.
- **`src/components/ui/top-nav.tsx`** — splits `TABS` into
  `PUBLIC_TABS` and `COMMISSIONER_TABS`; extracts `renderTab` helper
  and `TAB_STYLE` constant to deduplicate per-tab styling; adds the
  dim rule between the two groups. Top-of-file comment block updated
  to record the new five-tab order, the §VIII visibility framing,
  and a pointer to the mobile slot composition memo.
- **`src/app/league/[id]/office/page.tsx`** — drops the inline
  `createServerClient + auth.getUser`; uses `getViewer`. Two lines
  shorter in the function body, with the same three branches (anon
  → login, non-commissioner → Forbidden, commissioner → Office).
- **`src/app/league/[id]/approve/[artifactId]/page.tsx`** — same
  refactor pattern as Office.

The layout was not touched. With Office visible to everyone, the
layout doesn't yet need to read viewer identity. The `getViewer`
helper is positioned so a future iteration can add the role prop
trivially.

## What this unblocks

- **§6 item 4 — mobile bottom tab bar.** Both prerequisites are now
  closed: slot composition (`7f61e89`) and role-aware 403 rendering
  (`6720c89`). The mobile bottom tab bar implementation can map the
  five-slot composition directly onto the two arrays — public group
  on the left, commissioner group on the right, with the dim rule
  becoming whatever the mobile equivalent is (likely a vertical
  divider or the natural visual break between two rows).

## What this does not close

- **Mobile bottom tab bar implementation** itself. Unblocked but not
  scoped here. Natural follow-on session.
- **Layout-level isCommissioner prop.** Not needed for D5
  (anon-sees-Office). If a future iteration decides to conditionally
  hide tabs by role, the layout will read `getViewer` and pass an
  `isCommissioner` prop to TopNav. The helper is already shaped for
  that change.

## Cross-repo continuity

Engine memo paired with frontend commit per established pattern.

The session's commits today, in order:
- `6ff4b2b` engine — office back-link restore (item 1)
- `7f61e89` engine — mobile nav slot composition (item 4(a))
- `6720c89` engine — commissioner-only 403 rendering (item 4(b))
- `f430984` engine — request-scoped getLeague helper (item 7)
- `<TBD>`   engine — this memo (item 5)

Frontend counterparts:
- `029d41b` — office back-link
- `9e9b953` — CommissionerOnly component
- `ccceb72` — getLeague helper
- `0bcf7fb` — role-aware nav (item 5 frontend)
