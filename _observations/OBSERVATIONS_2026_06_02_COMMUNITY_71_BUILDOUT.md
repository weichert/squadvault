# Observation — Community Page §7.1 Build-Out (Phase 11)

**Date:** 2026-06-02
**Repo of record:** frontend (`weichert/squadvault-frontend`)
**Frontend commit:** `4f2e4e4`
**Engine commit (this memo):** docs-only; `prove_ci` skipped per established pattern.
**Closes:** roadmap items **19** (charter member row) and **20** (most-recent
approved artifact); displaces tighten memo §6 **item 3** (placeholder line).
**Predecessor reads:** `trophy-preview.tsx` (the server-component idiom this
mirrors), `recap-audience.ts` (audience split), the audience-split closure memo
(engine `044d07c`).

---

## 1. Decision record (D1–D3, all recommended accepted)

- **D1 — Composition order:** plaque → **The Record** (most-recent artifact) →
  Trophy Room preview → **Charter Members**. A front-door arc: who we are → what
  we just produced → what we have won → who we are made of. The flat placeholder
  (`"The archive is being populated. Check back soon."`) is removed.
- **D2 — Most-recent artifact block:** newest `APPROVED`/`DISTRIBUTED`,
  non-demo artifact; **public shareable segment only** via
  `extractShareableSegment`; derived headline + first-two-sentence teaser;
  docket ID (reusing `DocketId`), trust bar (`TrustBar` auto-derives CERTIFIED),
  and a type-routed "read the full record" link.
- **D3 — Charter members:** `franchises` where `charter_member = true`, small
  name cards with a restrained gold-register seal (the `docket-id.tsx` ring+dot
  glyph reused, **no new image asset**), horizontal scroll on mobile per §VIII.

## 2. What shipped (two new components + page wiring, one commit)

- **`src/components/ui/recent-artifact.tsx`** — server component mirroring
  `TrophyPreview`. Fetches a 5-row candidate window (newest by `approved_at`),
  pulls their current-version `content_markdown` in one round trip, and features
  the **first renderable** one — skipping any whose shareable segment is a
  principled silence (audit-only WEEKLY_RECAP), so the front door never shows
  audit content and a silence-case latest entry does not suppress a good older
  one. Link routes by shape: WEEKLY_RECAP → `/archive/recaps/{id}`, A1/A2/A3 →
  `/archive/records/{id}`, else `/archive`.
- **`src/components/ui/charter-row.tsx`** — server component; charter franchises
  as horizontally-scrolling name cards with the seal glyph. Renders null when
  none flagged (silence over speculation).
- **`src/app/league/[id]/page.tsx`** — imports + block order; placeholder div
  replaced by `<CharterRow />`, `<RecentArtifact />` inserted above
  `<TrophyPreview />`.

## 3. Empty states (§IX posture)

The block hierarchy degrades gracefully and always communicates potential rather
than absence:

- **No renderable record yet** → The Record renders its header and a §IX line,
  *"The archive begins with the first approved record."* This is the role the
  removed placeholder used to serve, now in the right place and the right voice.
- **No championships** → Trophy preview renders null (unchanged, per its own D9).
- **No charter members flagged** → Charter row renders null.

So an active league always has a meaningful front door (plaque + The Record at
minimum), and a fully-populated league shows all four tiers.

## 4. Doctrinal posture

Read-only public surface via `createAdminClient()` (RLS-bypassing public reads,
the established archive pattern). No fact, narrative, or governance mutation; no
new persisted state. The audience split is honored exactly — the public front
door cannot surface commissioner audit content. No analytics, no engagement
instrumentation. Headline/teaser are derived (a light markdown strip), never
fact-creating — they are a verbatim slice of already-approved public prose.

## 5. Local validation

Built against a fresh clone at frontend `f32da90`: apply is anchor-asserting and
idempotent (second run is a clean no-op, zero spurious churn), and `npm run
type-check` is clean (exit 0). Governance tests not run (no RLS / state-machine /
trust-bar invariant is touched — `TrustBar` renders unconditionally as before).

## 6. Confidence and carried-forward

- **Highest:** the audience-split-honoring select path; the type-routed link
  map; type-check-clean; the never-bare front-door guarantee.
- **Medium-high:** headline/teaser derivation is correct by construction but
  reads best when the shareable segment opens with a heading; without one it
  falls back to a two-sentence lead (no headline). Visual confirmation on real
  approved prose is Steve's pass.
- **Doc drift (minor, not touched):** `trophy-preview.tsx`'s header comment
  still says *"The community page's own placeholder line covers the
  not-yet-populated case."* That placeholder is gone; The Record's §IX line now
  covers it. Comment-only staleness; left for a future docs sweep to avoid
  widening this commit beyond §7.1.
- **Deliberate silence:** no PWA, no OG-per-artifact, no charter seal as a
  bespoke image — all out of this build's scope.
