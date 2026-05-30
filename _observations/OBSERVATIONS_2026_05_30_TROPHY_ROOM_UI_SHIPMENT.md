## OBSERVATIONS_2026_05_30_TROPHY_ROOM_UI_SHIPMENT

**Date authored:** 2026-05-30 (end of Trophy Room v1 session)
**Authoring context:** Frontend Trophy Room UI shipment, the second §12.1 item from the 2026-05-29 gap analysis, following the audience-split closure (2026-05-30).
**Engine state:** No change. Engine remains at `044d07c`, baseline 2,314 passed / 2 skipped. This shipment is frontend-only with a cross-repo governance trail recorded here.
**Frontend state:** Two new commits land in `weichert/squadvault-frontend`. Type-check zero, governance 102/102 against staging.

---

### 1. Mission

Phase 11 §12.1 candidate: ship the Trophy Room UI surface as the first league-level ceremonial page. Schema (`trophy_room_entries`, `provenance` enum) was ready before this session — the gap was UI only, no engine dependency. Design Brief §7.6 specified the surface.

The 2026-05-30 audience-split shipment established the precedent that cross-repo decisions get an engine-repo memo even when the code lands only in the frontend. This memo follows that pattern.

### 2. What shipped

**Frontend Commit 1 (precondition fix):**
`fix(trust-bar): handle CANONICAL provenance as CERTIFIED variant`

The `TrustBar.resolveVariant()` function had explicit cases for `provenance === 'COMMISSIONER_ATTESTED'` and `provenance === 'DEMO'` but no case for `CANONICAL`. A trophy entry with `provenance='CANONICAL'` fell through to the DRAFT variant (dashed gray). Pre-existing bug; harmless until a surface rendered canonical trophy entries.

Fix is a single conditional added in the natural position (after the other provenance checks, before the `approvalState` mapping). The `is_demo` strongest-signal precedence is unchanged.

**Frontend Commit 2 (feature):**
`feat(trophy-room): v1 surface - championship entries only`

New route at `/league/[id]/trophy-room`, peer top-level surface (not under `/archive/`), matching Design Brief §5.4 and §8 nav spec. The archive lists *artifacts*; trophy entries are a different governance model. Server Component + admin client + `force-dynamic`, mirroring the established league-page pattern documented in `_observations/OBSERVATIONS_2026_05_28_LEAGUE_PAGES_FORCE_DYNAMIC.md`.

Two-query data path (entries then franchises by id) mirrors the recap archive. Avoids PostgREST embedding semantics; the typing stays flat.

### 3. Five-decision record

The session opened with five decisions surfaced before any code was written. All five resolved with the recommended option. The record is preserved here so the rationale is durable.

**D1 — Scope: CHAMPIONSHIP-only for v1.** Schema supports four entry types (`CHAMPIONSHIP`, `PHYSICAL_TROPHY`, `COMMISSIONER_ATTESTED`, `SHAME_RECORD`). The seed has only CHAMPIONSHIP. PHYSICAL_TROPHY needs a commissioner-entry path that doesn't exist yet — separate scope. SHAME_RECORD appears only in the typography specimen ("Hall of Fame & Shame"), not as a §7.6 surface element. v1 ships what the data supports and what §7.6's primary spec describes.

**D2 — Score and one-line note: drop from v1.** Design Brief §7.6 calls for "championship score" and "one-line note from the recap if available" on each card. The schema has neither field, no FK to artifacts. Three options were on the table: (a) drop both, (b) schema migration to add a subtitle column, (c) schema migration + FK to championship artifact. v1 ships option (a): no schema change. The seed `title` field already carries descriptive content ("Most Improbable Run in League History", "The Record Bid"), serving the note role. A score-addition or artifact-FK pass can be a focused follow-up commit if the surface needs it later.

**D3 — TrustBar CANONICAL gap: fix in component, ship as separate commit.** Two options: fix `resolveVariant` to recognize `CANONICAL` as `CERTIFIED`, or work around at the call site by passing `approvalState="APPROVED"` on trophy surfaces. The component fix is semantically honest — `trophy_room_entries` have no `approval_state` column; the `provenance` value IS the state, and `CANONICAL` carries the same record-entry meaning that `APPROVED` carries on artifacts. Workaround would be a lie. Shipped as Frontend Commit 1, separate from the trophy room surface, matching the audience-split precedent of isolating pre-existing concerns from new feature work.

**D4 — Seed provenance: leave as CANONICAL.** The three demo PFL Buddies championship entries are seeded with `provenance='CANONICAL'`, even though the league itself is the staging demo league (artifacts are `is_demo=true`, demo voice profile, etc.). With D3 fixed, these entries render with the gold CERTIFIED trust bar — not the amber DEMO trust bar. Confirmed as intentional: the seed represents canonical demo history for visual showcase of the surface. The `is_demo` convention applies to `artifacts` rows; `trophy_room_entries` use `provenance` as the discriminator and there is no `is_demo` column on this table.

**D5 — Route location: `/league/[id]/trophy-room`, not `/league/[id]/archive/trophy-room`.** Design Brief §5.4 and §8 treat Trophy Room as a peer top-level surface alongside Archive, Community, Members, Office. The archive lists *artifacts*; trophy_room_entries are a separate table with a separate governance model. Routes mirror governance boundaries.

### 4. Implementation notes worth carrying forward

**Two-query data pattern over PostgREST embeds.** The franchise display name for each championship entry is resolved via a second query (`.in("id", franchiseIds)`) then merged in JS via a Map. Rationale: PostgREST embed semantics for nullable to-one relations have edge cases around array vs. object inference; the two-query pattern is what the recap archive already uses. Slight extra round trip, much cleaner typing. Worth keeping as the default pattern for surfaces with cross-table joins where the joined data is small.

**Card layout: trust bar inside the article boundary.** Each trophy entry card has the trust bar rendered inside the article element (not bracketing it like the recap artifact page). The card's border is at 40% gold-dim per Design Brief §5.2; the trust bar's border is solid gold-dim. Result is that the bottom 1px of the card is slightly darker than the other three sides — reads as visual weight anchoring the trust bar's role. Honors §IX anti-pattern "the artifact and its provenance are a single unit" most literally. If this turns out to be visually distracting on staging, a small follow-up tweak can either (a) remove the article's bottom border so the trust bar's border serves both roles, or (b) move the trust bar outside the article with bracketing-style spacing.

**Provenance label appears twice on each entry.** Once as the bottom-right badge inside the card body (per §5.2 "Provenance badge bottom-right") and again on the trust bar (per §IV trust bar variants). The badge is the compact data tag; the trust bar is the formal attestation. Both are required by the brief; the redundancy is deliberate.

**Year in cream, not gold.** Design Brief §2.5 reserves gold "ONLY on: certified trust bar, docket ID, founding plaque text, approve button background, section rule accents." The year on a trophy card is not on that list. Cormorant 300 at 3rem with the cream `text-vault-text` carries the ceremonial weight without burning gold tokens.

**Empty state language: principled silence.** "The trophy room opens with the first championship entry." Mirrors the recap archive's "The record opens with the first approved recap." Honors §IX anti-pattern against "Nothing here yet" framings.

### 5. Open items for the next session

**O1. Visual review on staging.** Steve to confirm three demo entries render with gold CERTIFIED trust bars per the D4 decision, layout reads as intended, no double-border artifact at card bottom. If the bottom-edge weighting reads wrong, a small tweak is available.

**O2. PHYSICAL_TROPHY card surface.** §7.6 specifies a dedicated physical trophy card with photo upload slot and COMMISSIONER ATTESTED trust bar. Schema supports it (`image_url`, `entry_type='PHYSICAL_TROPHY'`). Needs:
  - a commissioner-entry UI (currently no surface exists for commissioner-attested entries of any kind)
  - a Supabase Storage bucket for trophy photos (not yet configured)
  - decision on whether physical trophy is pinned-to-top per §VIII or part of the chronological list

**O3. SHAME_RECORD surface or fold into A1.** The typography specimen says "Hall of Fame & Shame" but the actual A1 archive route is already named "Hall of Fame & Shame" in the archive index. Possible duplication. Worth a one-line decision: does SHAME_RECORD belong on the trophy room (alongside championships, as ceremonial low points) or on A1 (as records-based shame entries)?

**O4. Community page Trophy Room preview.** §7.1 calls for "Trophy room preview: three most recent championship entries as horizontal cards" on the community page. Not built. Small follow-up — the data path already exists; would be a slimmer version of this surface rendered on the league home.

**O5. Top-level nav.** Design Brief §5.4 specifies "Community, Archive, Trophy Room, Members" as the four top-level tabs with gold-underline active state. Currently no top-level nav component exists; pages link back to community via a small `← {league name}` text link. With Trophy Room now live as a peer of Archive, the nav substrate is more material. Could be paired with a future Members surface.

**O6. Cross-repo schema-contract document.** Gap analysis §11.5 candidate. The shape of `trophy_room_entries` is documented only in `supabase/migrations/001_core_schema.sql` and `src/lib/supabase/types.ts`. With this surface live, the contract has a consumer. Worth recording the contract somewhere stable that survives migration renumbering.

### 6. Continuity surfaces touched

- Gap analysis §6.5 (Trophy Room UI): closed by this shipment.
- Gap analysis §12.1 short-path frontend wins: one item closed (Trophy Room UI), two remain (SETUP.md rewrite, the rest of §12).
- Cross-repo decision-with-memo pattern: second instance after audience-split, becoming established.

### 7. Status at end of session

- Frontend: two new commits on `main`, type-check zero, governance 102/102.
- Engine: this memo on `main`, no code changes, baseline 2,314 / 2 unchanged.
- Trophy Room v1 live at `/league/70985/trophy-room` (PFL Buddies staging).
- Roadmap §12 candidates open as before, minus §6.5.

---

**References:**
- `_observations/OBSERVATIONS_2026_05_29_FRONTEND_INCLUSIVE_GAP_ANALYSIS.md` §6.5, §12.1
- `_observations/OBSERVATIONS_2026_05_30_AUDIENCE_SPLIT_DECISION_OPTION_B.md` (precedent for cross-repo memo pattern)
- `_observations/OBSERVATIONS_2026_05_28_LEAGUE_PAGES_FORCE_DYNAMIC.md` (Server Component pattern)
- Frontend: `src/app/league/[id]/trophy-room/page.tsx`
- Frontend: `src/components/ui/trust-bar.tsx` (resolveVariant fix)
- Supabase: `supabase/migrations/001_core_schema.sql` (trophy_room_entries)
- Design Brief: `/SquadVault_Clubhouse_Design_Brief_v1_0.docx` §2, §3, §5.2, §7.6, §8, §9
