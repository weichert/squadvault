# Execution brief - W.1 A/V Room, Increment 1 (frontend build)

Authored: 2026-06-10 (Claude Code, Opus), engine HEAD `0c33087`, frontend `main` `248895c`.
Type: EXECUTE brief per Charter section 5 + W.1 admission record (memo 4) section 4. Distills
the RATIFIED W.1 spec (`_observations/OBSERVATIONS_2026_06_10_W1_AV_ROOM_SPECIFICATION.md`,
sections 5-6) into a build checklist. NO new decisions - D-W1-1..6 are ratified (all as
recommended); the contract card's 7.2 declaration is binding. Where this brief and the spec
differ, the spec governs.
Target repo: `weichert/squadvault-frontend` at `~/squadvault`. REPO-CONFIRM before first write:
`test -f scripts/recap_artifact_regenerate.py` must FAIL here.

## Scope: Increment 1 only (D-W1-1(a) foundation)

Build the founder/commissioner-operable foundation; member-testimony (Increment 2) is
specified but build-gated on E2.3 and is OUT OF SCOPE here. All Increment 1 writes are
commissioner-authored; no member-facing write path is built.

## Verified grounding (frontend `248895c`)

- Next migration number: `011`. No media/storage/withdrawal tables exist (greenfield).
- Display-withdrawal class does NOT exist (the consent build deferred it) -> W.1 mints it
  (spec 5.5 reuse note is moot at this HEAD; verify again at build HEAD).
- `member_consent_current` view exists (migration `010:72`, security_invoker) - the consent
  gates read it; absence of a row = ungranted.
- `av-room` route absent; sibling routes live under `src/app/league/[id]/` (incl. `consent`).
- Append-only sibling discipline: `approval_events`/`member_consent_events` - RLS enabled,
  SELECT+INSERT policies only, no UPDATE/DELETE (default-deny). Helpers `is_commissioner`,
  `is_admin`, `get_user_league_id` in `003`.

## Deliverables (exact paths; shapes are spec section 5 minimums, not frozen)

1. **Migration `supabase/migrations/011_w1_av_room.sql`** - four append-only classes, all
   RLS default-deny (SELECT league-authenticated; INSERT commissioner-only in Inc 1; NO
   UPDATE/DELETE):
   - `media_entries` (spec 5.2): id, league_id, media_kind (photo|video CHECK), storage_path,
     mime_type, uploaded_by (auth id, C3), upload_note, created_at.
   - `media_provenance_tag_events` (spec 5.3): id, media_entry_id, tag_kind (contributor|date|
     season|event|member_identification CHECK), tag_value, date precision (exact|year|season)
     where kind=date, tagged_member_user_id (nullable; required iff member_identification),
     ratified_by, note, recorded_at, supersedes (nullable self-ref).
   - `room_ratification_events` (spec 5.4): id, league_id, ratified_by, scope_note, recorded_at.
   - `media_display_withdrawals` (spec 5.5): id, media_entry_id (or testimony id, nullable for
     Inc 2 reuse), requested_by, ratified_by, note, recorded_at. (W.1 mints this; later units
     reuse it.)
   - Types + Database Tables/Views allow-list entries in `src/lib/supabase/types.ts`.
2. **Storage**: private bucket `league-media` (spec 5.1). Object path
   `{league_id}/{media_entry_id}/original.{ext}`. No public policy; no client-direct write.
   Storage RLS policy as a migration where expressible. NOTE: bucket CREATION is a
   Supabase-side action (dashboard/CLI) = a FOUNDER runtime step; the migration/policy + code
   assume the bucket exists. Flag in the build close-out.
3. **Server routes** (`src/app/api/av-room/...`, all server-side, authed):
   - upload (commissioner-only): accept file -> store to bucket -> INSERT media_entries.
   - signed-URL issuance (short-TTL, server-side only, inside the login-gated tree).
   - tag-ratification (commissioner-only): INSERT tag event; supersede flow.
   - room-ratification (commissioner-only): INSERT room event.
   - display-withdrawal ratification (commissioner): INSERT withdrawal.
4. **Ingest surface** `src/app/league/[id]/av-room/ingest/page.tsx` (commissioner-only;
   getViewer isCommissioner gate): upload + tagging, PHOTO-FIRST (D-G); five tag kinds;
   grant-state shown read-only beside member_identification tagging (W.6 5); superseding flow.
5. **Display route** `src/app/league/[id]/av-room/page.tsx`: corpus browse photo-first,
   chronological/era ordering only; per-item provenance panel (current tag state = latest
   non-withdrawn event; honest gaps render as gaps); FAIL-CLOSED (renders nothing until a
   room_ratification_event exists). Video playback enabled per item only when commissioner-
   attested no-member-voice OR (Inc 2) all identified members' 2b grants current - in Inc 1,
   no member grants exist, so only commissioner-attested-no-voice video plays; photos full.
6. **Governance tests** (`scripts/test-governance.ts`, G-series style): for each new table,
   planted UPDATE and DELETE via anon are denied (append-only); commissioner-only INSERT
   (anon INSERT denied); SELECT scoped to league-authenticated; fail-closed room (no
   ratification -> empty render); signed-URL path not publicly readable.

## 7.2 consent declaration (carried from the contract card - the build honors it)

This surface READS 2a (member_identification display = derivation+publication), 2b (video
playback = publication), 2d (captions = Inc 2). Inc 1 builds the gate-reading plumbing; with
no member grants extant, identified display and member-voice playback are inert by default
(fail-closed), exactly as the default-posture law requires. Reads `member_consent_current`,
never `founding_sessions.consent`. The build close-out carries this declaration (the standing
7.2 requirement) even though W.1 is itself a consent-reading surface, not the consent system.

## Binary acceptance criteria (from spec 5-6)

1. Migration 011 applies; four tables + RLS exist; type-check clean.
2. Governance: planted UPDATE/DELETE denied on all four tables; commissioner-only INSERT;
   league-scoped SELECT; fail-closed room render. (Tests in deliverable 6 pass.)
3. Commissioner can upload a photo and a video, tag across the five kinds (honest partial
   dates), ratify the room; the item displays with its provenance panel and honest gaps.
4. Signed URLs are server-issued, short-TTL, and there is no public read path.
5. member_identification tags render identified display only against a current 2a grant
   (inert in Inc 1); video plays only if commissioner-attested no-voice (no member 2b grants
   exist).
6. No member-facing write path, no AI path, no W.2 aesthetics beyond a plain dignified default.

## Gates / verification

- `npm run type-check` (Opus can run). `npm run test:governance` + migration apply + bucket
  creation + `next build` + click-through = FOUNDER runtime steps (no DB/Storage/creds in the
  build session). Build foundation first (migration + types + governance tests), founder
  applies + proves, then the routes/UI ride a proven schema (the consent-build rhythm).

## OUT OF SCOPE

Increment 2 (member captions/marginalia/self-identification writes); any AI/proposal path;
W.2 aesthetic application (VHS shelf etc.); W.8 match surfacing; corkboard announcements
(W.3); any engine-side change; cross-league semantics.

## Already-done / hashes

- `member_consent_current` view at `010:72` (frontend) - the gate read target.
- Display-withdrawal class absent at `248895c` -> W.1 mints it (no twin).
- av-room greenfield at `248895c`.
