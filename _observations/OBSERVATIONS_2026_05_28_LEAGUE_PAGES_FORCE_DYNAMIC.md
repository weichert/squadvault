# OBSERVATIONS — League Pages Force-Dynamic by Design (2026-05-28)

**Surfaced by:** M4 Block 3 — a synced A3 artifact landed in Supabase but `/league/70985/archive/records` continued to display "AWAITING FIRST ENTRY" until Cmd+Shift+R hard refresh. A standard browser refresh did not surface the new data. Initial diagnosis was incomplete; the full diagnostic trail is below.
**Engine HEAD at observation:** `386cf6d` (this memo lands after that).
**Frontend HEAD at observation:** `3466a65` (the fix lands on a successor commit in the squadvault-frontend repo).
**Disposition:** Two-part architectural pattern. (1) All Server Component pages under `src/app/league/[id]/` declare `export const dynamic = "force-dynamic"` to opt out of the Route Segment Cache. (2) `createServerClient` and `createAdminClient` in `src/lib/supabase/server.ts` override Supabase's underlying `fetch` with `cache: 'no-store'` to opt out of the Data Cache. The page-level directive alone is insufficient; both layers are required for genuinely live reads.
**Append-only:** This memo records the decision and rationale. It does not edit any prior memo.

---

## The decision

Two coordinated changes in the squadvault-frontend repo:

**(1) Page-level directive on all 8 Server Component pages under `src/app/league/[id]/`:**

```typescript
export const dynamic = "force-dynamic";
```

The 8 pages:

- `src/app/league/[id]/page.tsx` — league index
- `src/app/league/[id]/approve/[artifactId]/page.tsx` — approval workflow
- `src/app/league/[id]/archive/page.tsx` — archive index
- `src/app/league/[id]/archive/recaps/page.tsx` — weekly recaps list
- `src/app/league/[id]/archive/recaps/[artifactId]/page.tsx` — recap detail
- `src/app/league/[id]/archive/records/page.tsx` — permanent records list
- `src/app/league/[id]/archive/records/[artifactId]/page.tsx` — record detail
- `src/app/league/[id]/office/page.tsx` — member office (placeholder for M6)

**(2) Server-client fetch override in `src/lib/supabase/server.ts`:**

```typescript
const noStoreFetch: typeof fetch = (input, init) =>
  fetch(input, { ...init, cache: 'no-store' });
```

applied via `global: { fetch: noStoreFetch }` to both `createServerClient` (SSR) and `createAdminClient` (service-role).

## The diagnostic trail — initial wrong model

The initial fix attempt was the page-level directive alone, on the assumption that `force-dynamic` would propagate to every layer of Next.js's caching. Manual visual verification disproved this:

1. With `force-dynamic` declared on all 8 pages
2. With the dev server restarted (route segment configs sometimes need a clean restart to take effect)
3. With `UPDATE artifacts SET is_demo = true WHERE engine_artifact_id = 'archive:championship_timeline:38f85eb'` confirmed in Supabase
4. **Soft refresh did NOT update the page.** Hard refresh did.

The smoking gun came from `next.config.js`'s `logging: { fetches: { fullUrl: true } }` in dev. The dev server log showed:

```
│ GET https://qcaxemuydxlzpzgnnnoa.supabase.co/rest/v1/artifacts?...&is_demo=eq.false&...
│   200 in 0ms (cache hit)
```

- `(cache hit)` annotation: Next.js's Data Cache was serving the cached response
- `0ms` round-trip: not actually hitting Supabase
- Only hard refreshes produced `(cache skip)` with `cache-control: no-cache (hard refresh)` reason

The page WAS being executed on every soft refresh. The page WAS calling `createAdminClient().from("artifacts").select(...)`. But the underlying `fetch` call was returning the cached response from the Data Cache.

## The correct mental model

Next.js 14 has multiple caching layers, and `dynamic = "force-dynamic"` does NOT opt out of all of them:

| Layer | What `force-dynamic` does |
|---|---|
| Full Route Cache (static pre-rendering at build) | Opts out — page rendered on every request |
| Route Segment Cache (partial route output) | Opts out — segments re-rendered on every request |
| **Data Cache (per-fetch persistent cache)** | **Does NOT opt out by default in Next.js 14** |
| Request Memoization (within a single request) | Not affected — and is fine; we WANT deduplication within a single render |

The Data Cache is keyed on fetch URL + headers. In Next.js 14, the default for `fetch()` calls is `force-cache`, which means even with a dynamic page, individual fetch calls are cached unless explicitly told otherwise.

The Supabase JS client uses `fetch` under the hood. Next.js patches global `fetch` in the App Router. So Supabase queries — including those from `createAdminClient` and `createServerClient` — get cached even though the developer never called `fetch()` directly. This trap is documented in vercel/next.js Discussion #63518.

To bypass the Data Cache for Supabase queries, the right layer is the fetch override at client construction:

```typescript
global: { fetch: (input, init) => fetch(input, { ...init, cache: 'no-store' }) }
```

This sets `cache: 'no-store'` on every request the Supabase client makes, opting them all out of the Data Cache.

## Why both layers

The page-level `force-dynamic` directives are kept alongside the fetch override for explicit intent and defense in depth:

1. **Explicit page-level intent.** A reader of any page in `src/app/league/[id]/` sees immediately that the page is dynamic. They don't need to trace through Supabase client construction to understand the page's caching contract.
2. **Defense in depth.** If a future change to the Supabase client construction accidentally drops the `cache: 'no-store'` override, the page-level directives still ensure pages aren't statically pre-rendered. The failure mode is bounded: the page would still hit Supabase, just with possible Data Cache staleness — not silently statically pre-render at build time.
3. **No cost.** Page-level `force-dynamic` plus client-level `no-store` doesn't double up — they target different caching layers.

## Why the fetch override goes on the server client, not the page

The fetch override could in principle live on each page (call `unstable_noStore()` from `next/cache`, or pass `cache: 'no-store'` to individual fetch calls). It is better at the client construction layer because:

1. **Semantic alignment.** `createAdminClient` uses the service-role key and is called from pages that read ground truth for the commissioner. `createServerClient` uses auth cookies and is called from pages that need user-scoped server-side reads. Both clients exist to read live state. Caching their queries is a category error. The "never cache" contract belongs in the client itself, not in every caller.
2. **Centralization.** One file (`src/lib/supabase/server.ts`) holds the policy. New pages that use the admin or server client inherit the correct behavior automatically — they don't have to remember any directive at the page level.
3. **Future-proofing.** Next.js's caching defaults are evolving (v15 reverses many of v14's defaults; Cache Components in v16). Concentrating cache control in one place reduces the surface area that needs to change when we upgrade.

The page-level `force-dynamic` directives remain as explicit-intent documentation. They are not load-bearing for the staleness fix; the fetch override is.

## Verification

Manual visual verification, post both changes:

- **Before-state:** documented from M4 Block 3 and from the diagnostic session. Soft refresh did not surface SQL changes; only hard refresh worked.
- **After-state (expected):** with both changes deployed, set a row's `is_demo = true` in Supabase, soft-refresh the page (Cmd+R), confirm the row disappears immediately. Revert (`is_demo = false`), soft-refresh, confirm the row reappears immediately.
- **Diagnostic confirmation:** the dev server log should show no `(cache hit)` annotations on Supabase fetches after soft refreshes. Round-trip times should be on the order of tens to hundreds of milliseconds, not 0ms.

Automated rendering tests against a real Next.js server are not in the current frontend test suite (the governance suite tests Supabase directly, not via rendered pages). Adding rendering tests is out of scope for this fix.

## Scope

**Page-level `force-dynamic`:** every Server Component page that reads live Supabase state. The 8 pages under `src/app/league/[id]/` are the universe today. Future pages reading live state should declare it. A future static landing page or marketing surface should NOT declare it.

**Server-client fetch override:** both `createServerClient` and `createAdminClient` in `src/lib/supabase/server.ts`. Any future server-side Supabase client added to this file should inherit the same pattern, since the rationale (server clients read live state) applies uniformly.

The browser-side Supabase client (used in `'use client'` components for realtime, auth flows, etc.) is NOT affected by this change. Browser fetches bypass Next.js's server-side caching layers entirely.

## What this does NOT change

- The Supabase RLS policies, which gate WHO can read what, are unchanged.
- The `createAdminClient` / `createServerClient` distinction (service-role vs auth-cookies) is unchanged.
- The governance gates (G1–G9) are unchanged. They test Supabase-side invariants, not page-rendering behavior.
- Performance characteristics: each request now triggers a real Supabase round-trip instead of potentially serving from the Data Cache. For commissioner-facing pages (8 routes today, low traffic, single league), this is acceptable. Supabase round-trips are typically 50–200ms on warm connections.

## Why per-page directive (not layout cascade) for the force-dynamic part

A single `layout.tsx` at `src/app/league/[id]/layout.tsx` with `export const dynamic = "force-dynamic"` would cascade. Considered and rejected:

1. **Implicit cascade is harder to audit.** Reading a page in isolation, you cannot tell whether its caching contract is set by the page itself, by a parent layout, or by a Next.js default. Per-page declaration makes the contract local.
2. **Future routes may need different caching contracts.** Founding Session (M5), Member Office expansion (M6), and future read-mostly aggregation surfaces may legitimately benefit from caching. Per-page declaration forces explicit thought.
3. **Codebase style.** Existing engineering convention favors explicit, file-local contracts. Per-page route segment configs align with this.

The fetch override, in contrast, IS centralized (one file). This asymmetry is deliberate: page-level directives are explicit documentation; the fetch override is policy.

## Provenance

Decision made during the carry-over cleanup session of 2026-05-28, following M4 prove_ci stabilization. The bug was observed in real commissioner workflow during M4 Block 3 (frontend at HEAD `3466a65`). The first fix attempt (page-level `force-dynamic` only) was insufficient and produced the `(cache hit)` symptom in the dev server log. The corrected fix adds the Supabase fetch override in `src/lib/supabase/server.ts`. Both layers land in the squadvault-frontend repo. The apply script that introduces the page-level directives is archived at `scripts/_archive/apply_force_dynamic_to_league_pages_v1.py` for re-runnability.

References:

- vercel/next.js Discussion #63518 — same symptom (Supabase queries cached despite `force-dynamic`)
- Next.js 14 docs on Data Cache vs Route Segment Cache
- Next.js v14 → v15 caching evolution: v15 reverses the v14 default (fetches no longer cached by default), making this entire memo obsolete when we upgrade — but for now (v14.2.15) it applies.
