# member_consent_events - increment 2 built (write path + member panel, W.6)

Date: 2026-06-10
Repo: `weichert/squadvault-frontend` (`~/squadvault`), branch `feat/member-consent-events`,
commit `06cf568` (pushed). Built on increment 1 (`d58191b`) after the founder applied
migration 010 and `test:governance` (G11) passed. Brief: `session_brief_member_consent_events_frontend.md`.

## What was built

- `src/app/api/consent/events/route.ts` - POST write path. member_user_id from the session
  (never the body); RLS member-only insert is the hard guarantee (W.6 1.3). League-membership
  gate (commissioner or franchise member). Append-only insert; 2e requires rendering_class,
  others forbid it (mirrors the DB CHECK).
- `src/components/consent/member-consent-panel.tsx` - client panel: per-category current
  state, one-tap grant/revoke, own event history. Default-no-use renders NOT SHARED.
  synthesized_voice (2e) is informational only, never grantable here (no synthesis class
  admitted; Part 8).
- `src/app/league/[id]/consent/page.tsx` - authenticated page; SSR/RLS-scoped to the viewer's
  own rows; subject = the authenticated person (W.6 1.2).

7.2 declaration (per the brief's condition): this surface WRITES consent events for all five
categories; it does NOT consume consent at any gate (it is the substrate W.1/W.4/W.8/L-units
read). 2e is never granted here.

## Two architectural findings (surfaced during the build)

1. **The Member Office page is public + admin-read** (RLS-bypassing, viewer-agnostic) - it
   cannot host member-only consent writes. W.6 section 5 names "the Member Office" as the home;
   the actual page is the wrong host. RESOLUTION: a separate AUTHENTICATED page
   `/league/[id]/consent`. Placement is provisional - W.2 (clubhouse navigation) may relocate
   it into the scene.
2. **Member identity is not linked yet.** `franchises.member_user_id` is populated by NO app
   flow (appears only in types + tests); `/league/*` is login-gated but nothing connects a
   logged-in user to their franchise. So the only resolvable consent subject TODAY is the
   commissioner. RESOLUTION: the panel keys off the authenticated person (auth.uid()), so it is
   functional for the commissioner now and extends to the ten members the moment onboarding
   (E2.3) links member_user_id - no rework needed. This is a real PREREQUISITE for multi-member
   use, flagged here, not a defect in this unit.

## Verified vs NOT verified

- VERIFIED here: `npm run type-check` (`tsc --noEmit`) clean for both increments.
- NOT run here (no DB/runtime/creds in the build session): `npm run test:governance`,
  `next build`, and live click-through. Founder's steps. The RLS contract is proven by G11
  (increment 1); the route adds an app-level league-membership 403 check (not an RLS concern).

## Deferred (named, not silently dropped)

- Commissioner read-only "at the gates" (W.6 section 5 / 7.4): the consumer surfaces that show
  it (W.1 tag ratification, W.4/W.8 pitch review) do not exist yet - build the read-only view
  with its first consumer, not now (nothing to gate, no member grants to show).
- The `founding_sessions.consent` reinterpretation doc-note (W.6 7.1): still OPEN, frontend repo.
- Authenticated-session governance tests (member-vs-member isolation; commissioner-no-proxy):
  the harness does anon-denial only; a signed-in-session extension is a follow-up (noted in G11).

## State of the branch

`feat/member-consent-events` (frontend `06cf568`) carries both increments. Merge-ready after
the founder's runtime verification (`test:governance` green on the applied schema + a
click-through of `/league/[id]/consent`). Not merged by the session. Gates W.1 + L.3.
