# member_consent_events - increment 1 built (frontend foundation, W.6 D-V)

Date: 2026-06-10
Repo: `weichert/squadvault-frontend` (`~/squadvault`), branch `feat/member-consent-events`,
commit `d58191b` (pushed). Engine ledger anchor: built against brief
`session_brief_member_consent_events_frontend.md` (engine `8a33648`).
Routing: standard Opus build, frontend repo, no Fable chain (founder 2026-06-10);
implementation of ratified W.6, not a new surface.

## What was built (increment 1 = DB + governance layer only)

- `supabase/migrations/010_member_consent_events.sql`: append-only event table (subject =
  `auth.users`, not franchise). Member-only INSERT (`member_user_id = auth.uid()`, NO
  commissioner/admin proxy - W.6 1.3); NO UPDATE and NO DELETE policy (append-only via RLS
  default-deny, matching the `approval_events` sibling). CHECKs for the 5 categories +
  GRANT/REVOKE; `rendering_class` required iff `synthesized_voice` (2e). Plus the
  `member_consent_current` view (`security_invoker`) for derived current state; absence of a
  row = ungranted (default-posture law, 1.4).
- `src/lib/supabase/types.ts`: `MemberConsentEvent` / `MemberConsentCurrent` interfaces;
  registered in the `Database` Tables + Views allow-list (`Update: never`).
- `scripts/test-governance.ts`: G11 - anon cannot INSERT / READ / UPDATE / DELETE (RLS +
  append-only). Mirrors G10's anon-denial idiom.

## Verified vs NOT verified (honest status)

- VERIFIED here: `npm run type-check` (`tsc --noEmit`) clean.
- NOT verified here (no live DB/creds in the build session, and applying a migration to the
  live Supabase is an outward-facing act the session must not take unilaterally):
  `npm run test:governance` (needs the instance with 010 applied) and the migration apply.
  These are the FOUNDER's steps; G11 proves out only after apply.
- `npm run lint` is unconfigured in the repo (`next lint` drops to an interactive first-run
  setup prompt) - pre-existing repo gap, not introduced here.
- Harness limitation (noted in G11): member-vs-member SELECT isolation and the
  commissioner-cannot-proxy-INSERT guarantee need authenticated member/commissioner sessions;
  this harness exercises anon-denial only. An authenticated-session extension is a follow-up.

## Why increment 1 stops here (not routes/UI)

The constitutional crux is the RLS posture, which cannot be proven without applying 010 to the
DB. Building the API routes and Member Office consent panel on an unproven schema would be
backwards. Increment 2 (grant/revoke routes + read; the member consent panel; commissioner
read-only) builds once the founder applies 010 and `test:governance` (incl. G11) is green.

## Next steps (founder)

1. Apply migration 010 to the Supabase instance.
2. Run `npm run test:governance` - confirm G11 passes (and the prior G-series still does).
3. Then increment 2 is unblocked. Per the brief's 7.2 condition, increment 2's close-out
   carries a 7.2-style declaration (categories touched + gates) even though it IS the consent
   system.

## Notes

- An untracked `CLAUDE.md` exists in `~/squadvault` (not created by this session, left
  untouched, not staged). Flagged for founder awareness.
- The unit gates W.1 (A/V Room photo-consent reads) and L.3 (The Vault, pre-August deadline).
