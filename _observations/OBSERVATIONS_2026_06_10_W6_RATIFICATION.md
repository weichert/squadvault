# W.6 Consent Governance Memo - RATIFIED (all six decisions as recommended)

Date: 2026-06-10
Records: the founder's ratification of the W.6 Consent Governance Memo and its filing as
in-repo canonical doctrine. Engine HEAD at authoring: `5184b9d`.
Chain: brief `c441c75` -> Fable v1.2 DRAFT -> Section 0 independently verified `5184b9d`
-> founder ratification (this memo).

## What was ratified

The founder adopted all six numbered decisions as recommended:

- D-S: five separate consent categories (2a-2e), independently grantable/revocable, no
  bundles; 2e scoped per rendering class; archival(2a)-vs-derived(2c) boundary KEPT.
- D-T: one grant event per (member, category); uses gated by current-state reads at
  capture/derivation/publication; no per-use re-prompting (except 2e per-class grants).
- D-U: (b) artifact-integrity - sealed artifacts reproduce intact, new derivation forbidden;
  display withdrawal a separate commissioner-ratified act; death does not revoke.
- D-V: new frontend `member_consent_events` table, append-only via RLS default-deny
  (SELECT/INSERT policies only); member-only authorship; engine consumes derived allowlists.
- D-W: member-level grants per category; item-level acts read grants; objections via
  display withdrawal.
- D-X: reinterpret `founding_sessions.consent` as league-defaults layer (unmodified);
  W.6 events are the per-member system of record.

## Authority discipline (the cert-relevant point)

Ratification is a FOUNDER constitutional act, not the session's. Per Charter v1.0 section
2.4 ("never Opus for constitutional adjudication"), Claude Code did NOT make these picks:
it surfaced the recommendations and the two genuine forks (D-S boundary, D-U fork), the
founder selected, and the session recorded the selection. This is the "AI assists; humans
approve" law applied to a constitutional decision - a cert-5/closure exhibit that the
publication-approval discipline held for the consent frame itself.

## What was filed (this commit series)

- `docs/SquadVault_W6_Consent_Governance_Memo_v1_2.md` - ratified canonical memo (full text;
  status flipped DRAFT -> RATIFIED; decision register filled).
- `docs/map_patch_2026_06_10_w6_consent_governance.md` - Map v1.7 registration (new top-level
  docs/ file; satisfies the docs-Map gate).
- DoR `..._v2_1.md` - v2.1.1 supersession note correcting the "extends
  `founding_sessions.consent`" claim per the memo's Section 0 / D-X.
- `docs/STATE.md` - W.6 discharged; downstream items opened.

## Downstream items now OPEN (the memo unlocks, does not build)

1. Frontend doc-note recording the `founding_sessions.consent` reinterpretation (frontend
   repo `weichert/squadvault-frontend`; per memo 7.1). NOT this engine repo.
2. `member_consent_events` implementation unit (frontend; per D-V) - the table + member
   ratification surface + commissioner read-only views. Predecessor for any consent read.
3. Standing rule now BINDING (memo 7.2): every future four-memo chain / SAT contract card
   must declare (a) which section-2 categories it reads, (b) at which gate, (c) revocation
   behavior. W.1, W.4, W.8, L.1, L.3, L.4 inherit this immediately.

## Scope

- Doc-only in the engine repo. No code, no schema migrated (the memo itself migrates nothing;
  D-V's table is a frontend implementing unit).
- Not edited after commit; corrections are new dated memos.
