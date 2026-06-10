# W.1 A/V Room - Increment 1 foundation built (frontend DB + governance layer)

Date: 2026-06-10
Repo: `weichert/squadvault-frontend` (`~/squadvault`), branch `feat/w1-av-room`,
commit `c21e858` (LOCAL - not pushed; founder proves + merges, per the foundation-first
rhythm). Built against engine brief `session_brief_w1_increment_1_frontend.md` (engine
`92679d1`), which distills the ratified W.1 spec sections 5-6.
Routing: standard Opus build, frontend repo, no Fable chain (implementation of the
ratified W.1 four-memo chain, not a new surface; D-W1-1..6 all ratified as recommended).
Frontend base HEAD at build: `248895c` (matches the brief's verified grounding exactly).

## What was built (Increment 1 foundation = DB + types + governance only)

Per the brief's foundation-first sequencing (lines 96-98): migration + types + governance
tests ship first; the founder applies + proves; THEN the routes/UI ride a proven schema.
This session built the foundation only - the ingest surface, display route, and server
routes (brief deliverables 3-5) are deliberately NOT in this commit.

- `supabase/migrations/011_w1_av_room.sql`: four NEW append-only classes, all RLS
  default-deny - SELECT league-authenticated (`get_user_league_id` OR `is_commissioner`
  OR `is_admin`); INSERT commissioner-only (`is_commissioner`/`is_admin`, unlike the
  member-only consent log - every Inc 1 write is commissioner-authored, D-W1-1(a)); NO
  UPDATE and NO DELETE policy (append-only via RLS default-deny, the approval_events /
  member_consent_events precedent).
  - `media_entries` (5.2): photo|video CHECK; `uploaded_by = auth.uid()` enforced in the
    INSERT WITH CHECK (no proxy); `storage_path` keys the private `league-media` bucket.
  - `media_provenance_tag_events` (5.3): five tag kinds; two biconditional CHECKs
    (`date_precision` iff `date`; `tagged_member_user_id` iff `member_identification`,
    same technique as `member_consent_events_class_iff_synth`); self-ref `supersedes`;
    scoped through the parent `media_entries` via EXISTS (the approval_events-through-
    artifacts idiom); `ratified_by = auth.uid()` enforced.
  - `room_ratification_events` (5.4): the fail-closed gate (display renders nothing until
    a row exists for the league).
  - `media_display_withdrawals` (5.5): W.1 MINTS this class (later units reuse it);
    `media_entry_id` nullable for Inc 2 testimony reuse, `league_id` carried explicitly
    (NOT NULL) so RLS league-scoping holds when `media_entry_id` is null.
  - Plus a guarded `storage.objects` INSERT policy for `league-media` (commissioner
    write-scope keyed off the `{league_id}/...` path; no public SELECT - bytes served only
    by server-issued signed URLs). Wrapped in a DO block that RAISE NOTICEs (does not
    abort) if `storage.objects` is absent or privilege is insufficient.
- `src/lib/supabase/types.ts`: `MediaEntry` / `MediaProvenanceTagEvent` /
  `RoomRatificationEvent` / `MediaDisplayWithdrawal` interfaces + `MediaKind` /
  `MediaProvenanceTagKind` / `MediaDatePrecision` unions; registered in the `Database`
  Tables allow-list (`Update: never`, append-only).
- `scripts/test-governance.ts`: G12-G15, one per table, mirroring G11's anon-denial idiom -
  anon INSERT denied (commissioner-only), seeded-row anon SELECT/UPDATE/DELETE denied
  (append-only). Shared `resolveMember()` helper for the auth.users FK seeds; sub-tests
  skip with a note (G11 pattern) where no franchise member exists in the environment.

## 7.2 consent declaration (carried from the contract card; the build honors it)

This surface READS member grants via `member_consent_current` (migration 010) for 2a
(member_identification display) and 2b (video playback); it never reads
`founding_sessions.consent`. With NO member grants extant in Increment 1, identified
display and member-voice playback are inert by default (fail-closed), exactly as the
default-posture law requires. Inc 1 builds the governed schema; the gate-READING happens
in the display route (a later deliverable, not in this commit). 2d (captions) is Inc 2.

## Verified vs NOT verified (honest status)

- VERIFIED: `tsc --noEmit` clean on the full tree (the gate Opus can run). Confirmed tsc
  actually covers `scripts/` via an injected-error probe (then restored) - the new
  governance code is genuinely type-checked, not silently excluded.
- NOT verified this session (FOUNDER runtime steps - no DB/Storage/creds in the build
  session): migration apply; `league-media` bucket creation (a Supabase-side action);
  `npm run test:governance` against a live DB; `next build`; commissioner click-through.
  These are the brief's gates 2-5 / deliverable-6 runtime assertions.
- `next lint` is NOT configured in the frontend repo (interactive setup prompt); it is not
  a real gate here. The authoritative type gate is `tsc --noEmit`.

## Open / next

- NEXT SESSION (after the founder applies + proves the foundation): brief deliverables 3-5 -
  server routes (`src/app/api/av-room/...`), the commissioner ingest surface
  (`.../av-room/ingest/page.tsx`, photo-first), and the display route
  (`.../av-room/page.tsx`, fail-closed, provenance panels with honest gaps). These ride the
  proven schema.
- Founder runtime checklist before merge of `feat/w1-av-room` to frontend `main`: apply 011,
  create the private `league-media` bucket, `npm run test:governance` green, `next build`.
- Increment 2 (member captions/marginalia/self-identification writes) stays build-gated on
  E2.3 (the standing member-identity prerequisite).
