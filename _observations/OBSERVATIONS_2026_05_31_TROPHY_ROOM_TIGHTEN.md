## OBSERVATIONS_2026_05_31_TROPHY_ROOM_TIGHTEN

**Date authored:** 2026-05-31 (end of Trophy Room tighten session)
**Authoring context:** Frontend follow-on to the 2026-05-30 Trophy Room v1 shipment. Three follow-ons from §5 of the Trophy Room shipment memo (`e5aa22e`): F1 (visual check on staging), F3 (top-level nav layout + members stub), F2 (community page trophy preview). All three landed in this session.
**Engine state:** No change. Engine remains at `e5aa22e`, baseline 2,314 passed / 2 skipped. This memo is the cross-repo governance trail.
**Frontend state:** Two new commits on `main`. Type-check zero on both. Governance 102/102 against staging on both.

---

### 1. Mission

Tighten the Trophy Room area before declaring it done. The 2026-05-30 Trophy Room v1 shipment left three open items in its §5: visual check on staging (O1), community page Trophy Room preview (O4), top-level nav (O5). This session closes all three.

Per the session brief, direction-setting was open within the "tighten Trophy Room" scope; the larger §12 roadmap was parked. Shape C was chosen at session open: F3 before F2, with F1 running in parallel on the staging surface.

### 2. What shipped

**Frontend Commit 1 (F3):** `feat(nav): top-level four-tab layout and members stub` (`8b7ba23`)

Three new files:
- `src/app/league/[id]/layout.tsx` — Server Component, queries league `status + name`, renders `<TopNav>` above `{children}` for active leagues, returns bare `{children}` for founding-state or missing leagues
- `src/components/ui/top-nav.tsx` — Client Component, four tabs (Community, Archive, Trophy Room, Members), gold-underline active state, `usePathname()` for active resolution
- `src/app/league/[id]/members/page.tsx` — empty-state stub: "The members area opens with the first founding session."

Four edits:
- `src/app/league/[id]/page.tsx` — main element pulls itself up by `var(--nav-height)` so the plaque dominates the community page viewport
- `src/app/league/[id]/{archive,office,trophy-room}/page.tsx` — each loses its per-page `← {league name}` back-link; trophy-room also drops the now-unused `next/link` import; the section title's prior `mt-3` is removed in each

**Frontend Commit 2 (F2):** `feat(community): trophy room preview on league home` (`98b0724`)

One new file:
- `src/components/ui/trophy-preview.tsx` — Server Component, queries top 3 championship entries season-DESC, returns `null` for zero entries, renders three year-led horizontal cards using the Trophy Room surface's article + trust-bar pattern at scaled-down proportions

One edit:
- `src/app/league/[id]/page.tsx` — imports `TrophyPreview`; renders it between the plaque close and the existing "archive is being populated" placeholder line

**F1 outcome.** Visual check on staging green-lit. Three demo championship entries on `/league/70985/trophy-room` render with gold CERTIFIED trust bars per D4 of the Trophy Room shipment memo. Season-descending order intact. Provenance badge bottom-right. Card layout reads as intended; the bottom-edge weighting where the article's 40%-opacity gold-dim border meets the trust bar's solid gold-dim border is not visually distracting. No corrective tweak needed; the two recovery options named in the shipment memo (remove article bottom border, or move trust bar outside article with bracketing-style spacing) remain available if real-data leagues surface visual issues later.

### 3. Decision record — F3

Six decisions surfaced and approved before any F3 code was written.

**D1 — Layout component over per-page header.** Options: (a) Next.js layout at `src/app/league/[id]/layout.tsx`, (b) `<TopNav>` component imported into each page header. (a) won — Next.js layouts are the convention, scope the nav exactly to `/league/[id]/*` (won't leak into auth, root marketing, or LockedRoom surfaces), give a single source of truth for active-state computation; (b) would duplicate active-state logic across four pages.

**D2 — Members tab presence and surface.** Options: (a) skip the Members tab until a Members surface exists, (b) include the tab with a principled empty-state stub, (c) include the tab with a minimal roster page. (b) won — establishes the four-tab structure from day one, defers the surface honestly, mirrors the engine's silence-over-speculation principle into UI. Empty-state language mirrors Trophy Room's: "The members area opens with the first founding session."

**D3 — Per-page back-link scope.** With nav present, archive/office/trophy-room each lose their `← {league name}` back-link. Scope is **top-level peers only**; archive sub-pages (recaps index, records index, individual artifacts) keep their back-to-parent links because the nav does not replace intra-section hierarchy.

**D4 — Community page nav suppression.** §7.1 calls for "Founding plaque: full-width, takes 100% of the visible viewport above the fold"; §5.4 specifies the surface tabs sit below the league name in the top nav. Two readings: (a) nav above plaque on every page (pragmatic, slight deviation from §7.1's literal phrasing), (b) nav suppressed on the community page only (spec-faithful; community IS home; the plaque has primacy; F2 trophy preview + future charter member row + §7.1 most-recent-artifact are the discovery substrate). (b) won.

Implementation: layout renders nav unconditionally for non-founding leagues; community page's `<main>` uses `marginTop: calc(-1 * var(--nav-height, 0px))` plus `position: relative; z-index: 1` to overlap the nav. The nav remains in the DOM; active state still computes correctly because pathname stays `/league/[id]`. The negative-margin trick was preferred over a React Context fallback for simplicity. Staging visual check confirmed the trick works without z-index gymnastics or mobile weirdness.

**Mid-session check:** Steve briefly flagged "I don't see any navigation options on the main league page" before recalling the D4 agreement. Captured because the no-nav-on-community state is unusual and the mental-model surprise is real. F2 trophy preview is the first content-led discovery affordance, partially answering the gap; the remaining §7.1 blocks (most-recent-artifact, charter member row) will further address it as they ship.

**D5 — Gold-on-first-load nav ceremony.** §5.4 specifies the league name in the nav is "Outfit 500, gold on first load, cream after." Options: (a) cream always for v1, (b) gold always for v1, (c) implement the first-load-gold transition. (a) won — the ceremony belongs with the rest of Part VI ceremony-moments work as a coherent unit, not piecemeal. Cream-always reads as the permanent post-ceremony state.

**D6 — Mobile bottom tab bar.** §5.4 specifies mobile collapses to a bottom tab bar with five slots; §VIII lists those five as "Community, Archive, Trophy Room, Members, Office." Options: (a) desktop-style responsive nav for v1, defer bottom tab bar; (b) build the bottom tab bar now; (c) responsive nav now + bottom tab bar as a focused future session. (a) won. Three reasons converge: role-awareness for the Office slot needs real engineering, the §5.4 vs §VIII Archive/Trophy slot ambiguity must be resolved deliberately before any mobile-nav session opens, and the bottom tab bar deserves its own focused session.

### 4. Decision record — F2

Three decisions surfaced and approved before any F2 code was written.

**D7 — Card layout.** Options: (a) three columns side-by-side, year-led, (b) three columns side-by-side, franchise-led, (c) single horizontal scroll row with vertical cards inside. (a) won — year-led matches the Trophy Room surface's ceremonial register and §7.6's "season year (large, Cormorant Garamond)" lead element.

**D8 — Preview-to-full-surface connection.** Options: (a) section title is the link, (b) section title + small "See all" text link below row, (c) each card is a link to the full Trophy Room. (a) won — spare; no "click here to see more" upsell chrome; matches the engine's silence-over-speculation register. Cards stay informational, not interactive.

**D9 — Zero-championship rendering.** Options: (a) render nothing, (b) render section title + empty-state line "The trophy room opens with the first championship entry." (a) won — the community page's own "archive is being populated" line covers the empty state; the Trophy Room surface itself has its empty state for direct navigation. Stacking another empty-state message would read as noise. Trade-off: new tenant onboarding with zero championships sees a community page with plaque + placeholder line only, no preview block. Accepted for v1; the preview adds value once championships exist.

### 5. Implementation notes worth carrying forward

**Negative-margin overlap as nav-suppression pattern.** The community page's `<main>` pulls itself up by exactly the nav height via a CSS custom property set on the layout's wrapping div (`{--nav-height: 80px}`). Stacking is enforced with `position: relative; z-index: 1` rather than relying on DOM-order defaults. The fallback proposed at decision time (React Context) was never needed.

**Scaled-down card pattern.** Trophy Preview cards use the same article + trust-bar shape as the Trophy Room surface but at reduced proportions: year `2.2rem` vs `3rem`, franchise `1.1rem` vs `1.45rem`, title `0.85rem` vs `1.1rem`, padding `5/6/4` vs `8/8/6`. The preview is a *signal* of history, not a display. `flex flex-col flex-1` on the card body plus `mt-auto` on the badge wrapper pins the trust bar at the bottom of all three cards in the grid, giving equal heights across the row.

**Two-query data pattern, preserved.** Both the Trophy Room surface and the new Trophy Preview component use the same two-query pattern (entries first, franchises by id, merge via Map in JS). Worth keeping as the default for surfaces with cross-table joins where the joined data is small.

**TopNav as Client Component.** Active-state computation needs `usePathname()`, which is client-only. The nav has no server-side data needs once `leagueId` and `leagueName` are passed as props from the Server Component layout. Standard Next.js 14 pattern.

**Force-dynamic on layout.** Layout reads live league status; cache-segment skipping matches the pattern documented in `OBSERVATIONS_2026_05_28_LEAGUE_PAGES_FORCE_DYNAMIC.md`.

**`leagueUuid` prop on TrophyPreview.** Component takes both `leagueId` (canonical_id, for navigation links) and `leagueUuid` (internal id, for the `trophy_room_entries.league_id` join). Avoids an internal canonical-to-id resolution query inside the component since the community page has already resolved both. Future layout-level league context would obviate the prop.

### 6. Open items for the next session

**Office page back-link.** F3 removed Office's `← {league name}` back-link on the same scope rule as archive/trophy-room. With Office not in the four-tab nav (commissioner-only, deferred to role-aware 403 work), the only way back to community from Office is the browser back button or typing the URL. Two readings: (a) restore Office's back-link as a small follow-up since Office isn't in the nav and won't be until role-aware rendering ships, (b) leave as-is and accept the temporary friction until the commissioner-rule separator work lands. **Decision pending; (a) is a one-line revert in a follow-up commit if chosen.**

**Mobile viewport visual review of F2 trophy preview.** Cards reflow to single-column on mobile per `grid-cols-1 md:grid-cols-3`. Worth eyeballing at iPad-narrow and phone-narrow widths to confirm the grid transition reads cleanly. Not blocking; small tweak if anything reads off.

**Gold-on-first-load nav ceremony.** Lands with the broader Part VI ceremony-moments work. Captures from D5.

**Mobile bottom tab bar.** Captures from D6. Two prerequisites: (a) deliberate resolution of the §5.4 vs §VIII slot ambiguity (§5.4 says "Archive and Trophy Room share one slot with a sub-menu" — five total; §VIII table says five separate slots "Community, Archive, Trophy Room, Members, Office"), (b) role-aware 403 rendering for the Office slot.

**Commissioner-rule separator with Office/Approval in nav.** §5.4: "Commissioner-only items (Office, Approval) separated visually by a dim rule. Not hidden from other roles — they are visible but display a 403 state rather than being invisible." Requires role-aware 403 rendering.

**Layout-level league context.** Eliminates the duplicate `name` query (layout + each page both fetch it) and the `leagueUuid` prop passed to `TrophyPreview`. Worth doing when a third surface starts duplicating the same fetch.

**`PROVENANCE_LABEL` / `PROVENANCE_STYLE` shared module.** Now duplicated across `trophy-room/page.tsx` and `trophy-preview.tsx`. Extract on next surface that needs them.

**NULL-season ordering.** Trophy Preview inherits Trophy Room's behavior; null seasons sort first in DESC order per Postgres default. Revisit with `.order("season", { ascending: false, nullsFirst: false })` if real-data leagues surface the issue.

**"Archive is being populated" placeholder line.** Reads slightly differently with the trophy preview above it (the Trophy Room IS populated). Acceptable as a placeholder for the remaining §7.1 blocks (most-recent-artifact, charter member row), but worth rephrasing or removing when those land.

### 7. Continuity surfaces touched

- Trophy Room shipment memo (`e5aa22e`) §5 open items O1, O4, O5: **all closed** by this session (F1, F2, F3 respectively).
- Frontend-inclusive gap analysis (`1752ddc`) §12.1 short-path frontend wins: two further items closed (Trophy Room UI nav, Trophy preview). SETUP.md rewrite still open.
- Cross-repo decision-with-memo pattern: third established instance (audience-split `044d07c`, Trophy Room UI shipment `e5aa22e`, this memo).

### 8. Status at end of session

- **Frontend:** two new commits on `main` (`8b7ba23` F3 nav, `98b0724` F2 preview). Type-check zero on both. Governance 102/102 against staging on both.
- **Engine:** this memo on `main`, no code changes, baseline 2,314 / 2 unchanged.
- **Trophy Room area:** structurally complete as a peer top-level surface plus community-page preview, with the four-tab nav substrate live. Phase 11 §12 candidates open as before, minus §6.5 (closed by the Trophy Room v1 shipment) and minus the Trophy Room shipment memo's §5 O1/O4/O5 (closed by this session).

---

**References:**
- `_observations/OBSERVATIONS_2026_05_29_FRONTEND_INCLUSIVE_GAP_ANALYSIS.md` §6.5, §12.1
- `_observations/OBSERVATIONS_2026_05_30_AUDIENCE_SPLIT_DECISION_OPTION_B.md`
- `_observations/OBSERVATIONS_2026_05_30_TROPHY_ROOM_UI_SHIPMENT.md` §5 (O1, O4, O5 closed)
- `_observations/OBSERVATIONS_2026_05_28_LEAGUE_PAGES_FORCE_DYNAMIC.md` (Server Component force-dynamic pattern)
- Frontend: `src/app/league/[id]/layout.tsx`
- Frontend: `src/components/ui/top-nav.tsx`
- Frontend: `src/app/league/[id]/members/page.tsx`
- Frontend: `src/components/ui/trophy-preview.tsx`
- Design Brief: `/SquadVault_Clubhouse_Design_Brief_v1_0.docx` §2.5, §5.2, §5.4, §7.1, §7.6, Part VIII, Part IX
- Frontend commits: `8b7ba23` (F3 nav), `98b0724` (F2 trophy preview)
