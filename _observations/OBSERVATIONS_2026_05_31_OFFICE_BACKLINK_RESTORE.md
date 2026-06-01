# Office Back-Link Restore — Item 1 Closure

**Date:** 2026-05-31 (post-tighten dispatch session)
**Frontend commit:** `029d41b`
**Closes:** §6 item 1 from `OBSERVATIONS_2026_05_31_TROPHY_ROOM_TIGHTEN.md`

---

## What

Restored the Office page's `← {league name}` back-link, which had been
removed in frontend commit `8b7ba23` (F3 four-tab nav layout) along with
the back-links on Archive and Trophy Room.

## Why

The F3 removal rule was about redundancy: the nav's Community tab
replaces per-page back-links *for surfaces that have a nav tab*.
Archive and Trophy Room have nav tabs, so the redundancy predicate
fires for them; Office does not have a nav tab yet (and won't until
role-aware 403 rendering and the commissioner-rule separator land per
Design Brief §5.4), so the redundancy predicate doesn't fire for
Office. F3 was an over-application of the scope rule to a surface
that doesn't satisfy the predicate.

The friction is real: Office is reachable from commissioner flows
(approval routes, league management) that don't always leave a
natural way home. With no nav tab and no back-link, the only return
paths were browser-back or URL typing. The rule's predicate — not
aesthetic uniformity across the three peer surfaces — is the right
test.

Dispatched as D1 this session: restore.

## Scope of change

One file, frontend repo:

- `src/app/league/[id]/office/page.tsx`: restore the `Link` block
  above the h1, restore `mt-3` on the h1.

No imports change (`Link` was already imported and used elsewhere in
the file). No types touched. No tests touched. No styling tokens
introduced. The restored markup matches the pre-F3 state byte-for-byte.

## Verification

- `npm run type-check`: zero errors
- Visual confirmation: back-link reads "← {league name}" in the same
  font-mono small-caps style as the pre-F3 state, above the
  "Commissioner Office" h1, with the `mt-3` gap restored.

## What remains open

Office still does not appear in the four-tab nav. The proper home for
Office in the nav surface is the commissioner-rule separator work
(§5.4: commissioner-only items separated visually by a dim rule,
visible to all roles but 403-rendered for non-commissioners). That
work is blocked on role-aware 403 rendering, which is itself listed
as §6 item 5 in the tighten memo.

Restoring the back-link is the interim measure. When Office earns a
nav slot through the commissioner-rule separator, the back-link
becomes redundant again and should be removed under the same scope
rule that removed it from Archive and Trophy Room. The frontend
commit body records this so the future remover finds the trail.

## Cross-repo continuity

Frontend commit closes item 1 from the tighten memo; this memo
records the decision and reasoning in the engine repo's governance
trail per established pattern (audience-split `044d07c`, Trophy Room
UI v1 `e5aa22e`, Trophy Room tighten `e160b5d`).
