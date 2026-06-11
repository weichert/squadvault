# W.1 A/V Room - Increment 1 routes/UI built (frontend deliverables 3-5)

Date: 2026-06-10
Repo: `weichert/squadvault-frontend` (`~/squadvault`), branch `feat/w1-av-room-routes`
(LOCAL - not pushed; founder proves + opens PR + merges). Commits `df79a4f` (governance
tighten), `c284053` (routes + read-model), `7eee29d` (ingest + display UI).
Base: frontend `main` `2cd9f17` - Increment 1 FOUNDATION (PR #1) merged + founder-proven
on live Supabase (tables + RLS via pg_policies; `league-media` bucket private; storage
policy `league_media_commissioner_insert` live). Built against engine brief
`session_brief_w1_increment_1_frontend.md` (`92679d1`) deliverables 3-5; W.1 spec sections
5-7 govern.
Routing: standard Opus build (ratified spec implementation, not a new surface).

## What was built (deliverables 3-5)

- **Server routes** (`src/app/api/av-room/*`, deliverable 3) - all commissioner-authored;
  the authed SSR client carries the write so RLS (commissioner-only INSERT, append-only) is
  the hard guarantee, route checks give clean 4xx:
  - `upload` - multipart passthrough; bytes -> private `league-media` via the authed client
    (storage policy enforces) at `{league_id}/{media_entry_id}/original.{ext}`, then INSERT
    `media_entries`; orphan object rolled back on insert failure; original retained (6.9).
  - `tag` - append a provenance tag; validation mirrors the DB CHECKs + rejects vacuous
    contributor/season/event (note 2); supersede must target a tag on the same entry.
  - `room` - ratify the room (the fail-closed gate, 5.4).
  - `withdraw` - item withdrawal; commissioner requests AND ratifies -> effective at insert
    (note 3); `league_id` carried for RLS when `media_entry_id` is null (Inc 2 reuse).
  - `sign` - short-TTL (120s) signed URL after a league-membership check (no member
    storage-read policy exists, so that check IS the boundary).
- **Shared read-model** `src/lib/av-room.ts` - one source of derived truth for routes +
  both pages: tag vocabulary + value-required rule, league commissioner/member checks, and
  `loadRoomState` (current = latest non-superseded tag per (entry,kind); withdrawn items drop
  from forward display; member identification resolves to a name only against a current 2a
  `media_appearance` grant, else silent).
- **Ingest** `/league/[id]/av-room/ingest` (deliverable 4, commissioner-only; non-commissioner
  -> `CommissionerOnly` 403): photo-first upload, tagging across the five kinds with a
  client-side no-vacuous-tag guard mirroring the write path, read-only 2a grant state shown
  beside member identification (W.6 5), correction-by-supersession, item withdrawal, room
  ratification. Commissioner sees their own uploads (incl. video) via signed URL on this
  management surface (not member-facing display).
- **Display** `/league/[id]/av-room` (deliverable 5, league-authenticated): FAIL-CLOSED -
  sealed state until a `room_ratification_event` exists (6.6); photo-first chronological
  corpus; per-item provenance panel with honest gaps (6.8); `member_identification` shows a
  name only against a current 2a grant, else silent (5.3); photos via short-TTL server-issued
  signed URLs.

## Three carry-forward notes from PR-review (all folded in)

1. (`df79a4f`) Governance G12-G15(a) now assert RLS denial **42501** specifically (helper
   `assertRlsInsertDenied`), not any-error - an incidental FK/NOT-NULL/CHECK failure can no
   longer masquerade as an RLS pass. (RLS WITH CHECK is evaluated before row constraints, so a
   genuine commissioner-only denial always surfaces as 42501.)
2. Ingest enforces `tag_value` presence for contributor/season/event (client + server) - no
   vacuous tag events. `VALUE_REQUIRED_KINDS` in `av-room.ts`.
3. Display/withdraw treat a `media_display_withdrawals` row as effective AT INSERT;
   `ratified_by` is set by the inserting commissioner (= `requested_by`). Item drops from
   forward display immediately.

## Founder decision recorded (2026-06-10): video playback DEFERRED

Spec 5.7 gates video playback on a commissioner "no member voice" attestation OR all
identified members' 2b grants current. The merged foundation schema (011) has no structured
place for that attestation (only `media_kind` + `upload_note`; the five tag kinds carry no
voice signal), so on the proven schema NO video can play (strictly fail-closed). Founder chose
**defer** (no schema change; keep the proven-schema rhythm): photos ship fully; video displays
as a present item with provenance + a plain "playback pending voice attestation" placeholder;
attestation + playback are a clean next increment. Alternatives weighed and not taken: a
migration 012 structured attestation class; a `voice_presence` tag_kind.

## Scope held (NOT built)

NO nav change - the canonical section-VIII `TopNav` is W.2's (clubhouse navigation) domain and
out of scope; both surfaces are route-reachable (ingest links to the room). No member-facing
writes (Inc 2, gated E2.3); no AI path; no W.2 aesthetics beyond a plain dignified default; no
W.8 match surfacing; no engine-side change. No counts/ordering knobs/nudges (6.3-6.5).

## Verified vs NOT verified

- VERIFIED (this session, no live DB needed): `tsc --noEmit` clean; `npm run build` clean -
  both pages + all five routes compile as dynamic.
- NOT verified (FOUNDER runtime steps - need live DB/Storage/creds): `npm run test:governance`
  (G12-G15 now assert 42501); commissioner click-through (upload photo + video, tag five kinds
  incl. honest partial date, ratify room, withdraw; confirm fail-closed + honest gaps + 2a
  silence with no member grants).

## Open / next

- Founder: prove (`test:governance` + click-through) on `feat/w1-av-room-routes`, then PR +
  merge. On merge, W.1 Increment 1 DISCHARGES (foundation + routes/UI complete).
- Deferred within Inc 1: video playback + commissioner voice attestation (next increment).
- Increment 2 (member captions/marginalia/self-identification) stays gated on E2.3.
