# Request-Scoped getLeague Helper — Item 7 Closure

**Date:** 2026-05-31 (post-tighten dispatch session)
**Frontend commit:** `ccceb72`
**Closes:** §6 item 7 of `OBSERVATIONS_2026_05_31_TROPHY_ROOM_TIGHTEN.md`

---

## What

Added `src/lib/league.ts` exposing `getLeague(canonicalId)` wrapped in
`React.cache()`. Refactored all 11 league surfaces and the trophy-
preview component to call the helper instead of fetching the leagues
row inline. The same canonical_id within a single render request now
hits the cache after the first call.

## Why

The tighten memo §6 item 7 named layout-level league context as a
tech-debt candidate. The original trigger: *worth doing when a third
surface starts duplicating the same fetch.* That trigger had already
fired — the layout, every page below it, the community page's
`generateMetadata`, and the trophy-preview component were all
fetching the same row keyed on canonical_id. Counting fetches across
the league surface tree:

| Surface | Fetches |
|---|---|
| `layout.tsx` | 1 |
| `[id]/page.tsx` (community) | 2 (generateMetadata + body) |
| `trophy-room/page.tsx` | 1 |
| `members/page.tsx` | 1 |
| `office/page.tsx` | 1 |
| `approve/[artifactId]/page.tsx` | 1 |
| `archive/page.tsx` | 1 |
| `archive/recaps/page.tsx` | 1 |
| `archive/recaps/[artifactId]/page.tsx` | 1 |
| `archive/records/page.tsx` | 1 |
| `archive/records/[artifactId]/page.tsx` | 1 |
| `trophy-preview.tsx` (component) | 0 (consumed leagueUuid prop) |

Each viewer hit on a league surface ran the layout fetch plus the
page fetch (and on the community page, also a `generateMetadata`
fetch). All three returned the same row.

`React.cache()` is the Next.js-blessed pattern for this case. The
helper memoizes per-request; each render gets a fresh cache; nothing
persists across requests. Consumers call the helper without thinking
about whether they are the first or third caller — second and
subsequent calls in the same render are free.

## Decisions

Dispatched as six decisions:

- **D1 — Approach.** `React.cache()` helper, not status-quo cleanup
  or doc-only update. This is exactly the pattern's intended use.
- **D2 — Fetch shape.** One canonical helper returning the union of
  fields any consumer reads (`id, name, founding_year, status,
  canonical_id, commissioner_user_id`). The leagues row is tiny; one
  shape simpler than several narrower shapes.
- **D3 — Missing-league behavior.** Helper returns `null`. The
  layout treats null and `status === "founding"` differently — that
  branching logic belongs at call sites, not in the helper.
- **D4 — Trophy preview prop.** Drop the `leagueUuid` prop. The
  component resolves internal `leagues.id` via the cache, parent no
  longer orchestrates. Self-contained component, single prop.
- **D5 — generateMetadata.** Include it. Same request, same cache;
  the second call is free. (Optional verification: check network
  panel during dev render shows only one Supabase request for the
  leagues table per page load.)
- **D6 — Scope.** All 11 files in one commit. The memo trigger fired
  for *all* of them; partial refactors leave known inconsistencies.
  The diff is mechanical and atomic by topic.

## Scope of change

12 files edited + 1 file created in the frontend repo:

- **NEW** `src/lib/league.ts` — exports `getLeague` and `League` type.
- **EDIT** `src/app/league/[id]/layout.tsx` — replaces inline fetch
  with `getLeague(id)`, removes `LeagueStatusRow` type alias.
- **EDIT** `src/app/league/[id]/page.tsx` (community) — collapses
  the two inline fetches (`generateMetadata` and body) into one
  helper call each. Removes the `LeagueRow` type alias. Drops the
  `leagueUuid` prop on `<TrophyPreview>`.
- **EDIT** 8 other league surface pages — same pattern: import
  `getLeague`, replace inline fetch, remove orphaned `LeagueRow`
  type alias where present.
- **EDIT** `src/components/ui/trophy-preview.tsx` — drops the
  `leagueUuid` prop, resolves internal id via the cached helper,
  updates the FUTURE comment block to remove the now-resolved item.

Net change: 12 fetches per league surface render reduce to 1 (one
DB hit per request regardless of how many cached callers).

## Verification

- `npm run type-check`: zero errors
- Apply script idempotency: 13 no-ops on re-run
- Optional manual verification during dev render: inspect the
  Supabase network requests on any league surface page. The leagues
  table should be hit exactly once per page load, not 2-3 times.

## What this does not close

- **`PROVENANCE_LABEL` / `PROVENANCE_STYLE` shared module** (§6
  item 8). Still duplicated across `trophy-room/page.tsx` and
  `trophy-preview.tsx`. Trigger has not yet fired — only two
  consumers. Memo guidance: extract on next surface that needs them.
- **NULL-season ordering** (§6 item 9). Trigger has not fired —
  real-data leagues have not surfaced the issue.
- **Phase 11 seasons-count compound drift** (§6 item 16). Out of
  scope for this refactor.
- **A2 anchor correction** (§6 item 17). Out of scope.

## Cross-repo continuity

Engine memo paired with frontend commit per established pattern.
Engine repo has no code changes — this is a frontend-only data-path
refactor — but the decision trail and the closure of §6 item 7 live
in the engine's governance trail alongside earlier session memos
(`6ff4b2b` office back-link, `7f61e89` mobile nav slot composition,
`6720c89` commissioner-only 403).
