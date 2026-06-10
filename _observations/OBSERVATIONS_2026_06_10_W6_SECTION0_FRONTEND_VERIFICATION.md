# W.6 memo - Section 0 substrate finding INDEPENDENTLY VERIFIED (frontend `4e44bb3`)

Date: 2026-06-10
Records: an independent, read-only verification (from the engine workspace) of the
load-bearing frontend claims in the W.6 Consent Governance Memo v1.2 DRAFT (Fable session).
Engine anchor: `c441c75`. Frontend anchor verified: `4e44bb3`.
Related: `session_brief_w6_consent_governance.md` (the brief that flagged the substrate
hazard); W.6 v1.2 DRAFT is a chat/Fable artifact (not yet in-repo, not yet ratified).

## Why this verification happened

W.6 v1.2's Section 0 CORRECTS the DoR (Part 3, Unit W.6 says W.6 "extends
`founding_sessions.consent`"). The correction's whole architecture - "build a new
append-only per-member event class, do not extend the field" - rests on frontend facts:
the field is mutable, league-level, and a three-boolean bundle. Those specifics (file path,
line numbers, RLS policy name, the three booleans) are NOT derivable from the DoR, so they
were either truly read from the frontend repo or fabricated. The project refuses
plausible-but-unread claims, so before this becomes Track W/L constitutional law the claims
were checked at the layer they are about (Charter hazard: "data correct on prod is not the
same as the code path being guarded in the repo").

Path: the verification challenge went back to the Fable session, which produced Appendix A
(file:line evidence register). Then the frontend repo `weichert/squadvault-frontend` was
cloned to `~/projects/squadvault-frontend`, checked out at `4e44bb3` (the memo's authoring
anchor), and each claim re-read independently.

## Results - Appendix A claims at `4e44bb3` (all confirmed)

| # | Claim | Result |
|---|---|---|
| A1 | `consent jsonb NOT NULL DEFAULT '{}'`, table 129-144 | exact - `001_core_schema.sql:137` |
| A2 | mutable via UPDATE | exact - `consent/route.ts:84,87` |
| A3 | RLS policy `founding_sessions_update` permits UPDATE | exact - `003_rls_policies.sql:216-220` (`commissioner_user_id = auth.uid() OR is_admin()`) |
| A4 | no append-only protection; RLS default-deny is the mechanism | confirmed - 13x ENABLE RLS, 0 FOR DELETE, 0 explicit-deny in `003`; `is_demo` immutability precedent `002:138` |
| A5 | league-level, commissioner-keyed, no member dimension | exact - `001:132` `commissioner_user_id ... NOT NULL` |
| A6 | three-boolean bundle | exact - `types.ts:239-242` (`photos` / `voice_recording` / `text_likeness`) |
| A7 | UI promises the unbuilt per-member layer | confirmed - `consent-panel.tsx:54` |
| A8 | no other consent store exists | substance confirmed - `member_consent`/`consent_event`: zero hits (see imprecision) |

## The one imprecision (non-load-bearing)

A8's parenthetical "13 tables total, all in `001`" is slightly off: `001` creates 13 tables,
but migrations `008`/`009` each add one more (`franchise_season_records`,
`franchise_season_names`) - 15 tables total, not 13, not all in `001`. Those two are
franchise records, NOT consent stores, so the load-bearing A8 claim ("no other consent store
exists") holds completely. The "thirteen tables" figure in the memo's D-V note is correct as
of migration `003`'s authoring (008/009 did not exist yet) and is irrelevant to the design -
`member_consent_events` enables its own RLS regardless.

## Engine-side confirmations (verifiable in this repo)

- No consent state anywhere in the engine: `grep consent src/squadvault/core/storage/` empty.
- The memo's 7.3 read-path invariant cites the "FAAB-allowlist pattern" as engine precedent;
  it is real and current: `src/squadvault/core/recaps/context/writer_room_context_v1.py:456`
  ("Any player NOT listed here received NO FAAB ...") - the copy-only allowlist from the
  2026-06-09 residual remediation.

## Verdict

Section 0's substrate finding is independently confirmed. The memo's conclusion (new
append-only per-member event class, not a field extension) is grounded in verified fact. The
v1.2 D-V self-correction (RLS default-deny, not "no-UPDATE/no-DELETE policies") is not just
plausible but correct (0 DELETE policies; default-deny is the actual no-rewrite mechanism).
The verification gap the founder asked to close is closed.

## Scope / boundaries

- Verification only. NOT ratification (founder-only) and NOT constitutional adjudication of
  D-S..D-X (Fable lane, Charter section 2.4 - never Opus for constitutional adjudication).
- Frontend repo read-only: cloned, checked out detached at `4e44bb3`, nothing written or
  committed there. The clone persists at `~/projects/squadvault-frontend` (useful for the
  coming W.1 build).
- Environment hazard (carried): `~/projects/squadvault` is a stale divergent ENGINE clone
  (`a5a2d60`), separate from the working repo (`c441c75`) - a "which repo am I in" risk.
- Corrections to this memo, if ever needed, are new dated memos (supersession-then-fold-in).
