# OBSERVATIONS 2026-06-19 - L.3 The Vault: Specification
## Light chain, build surface - per-surface constitutional memo per template v1.0

**Date:** 2026-06-19
**Session:** DECIDE (Charter rhythm). Founder sole adjudicator.
**Status:** Specification of record - RATIFIED 2026-06-19. D-L3-4 RATIFIED in-session
(option 2 - `sealed_testimony` consent category). D-L3-1/2/3/5 RATIFIED as recommended.
Republication scope HELD in-ceremony-only (founder, 2026-06-19). Authored against
template v1.0 (`docs/templates/`, `acf55ee`), Mode B (specified shape). Opus builds
against this document; acceptance criteria derive from sections 5 and 6.
**Verified anchors (this session, git):** engine `0f20fec` - frontend `2c5ae6f`.
Both remotes main-only after the branch sweep recorded below.
**Predecessors (chain order, most-proximate last):**
- `df09a5e` - Product Document of Record v2.1 (DoR section L.3 - the spec source) +
  W.6 Consent Governance Memo v1.2 + W.6 ratification record.
- `acf55ee` - per-surface constitutional-memo template v1.0 (binds this memo's structure).
- `0c33087` - W.1 A/V Room specification (build-surface structural precedent;
  append-only-table + RLS-gate idiom this memo inherits).
- `e908863` - D-SEQ Tahoe sequencing ruling (docket: E2.3-min -> **L.3** -> L.1 -> Inc2;
  D-SEQ-4 = the L.3 clock, AMENDED below).
- `9f5d0fb` - D-SEQ date-pin 2026-08-15 (carries the stale "~4-4.5 wk" L.3 window figure
  this memo corrects).
- frontend `d58191b` - W.6 migration `010_member_consent_events` (the consent system of
  record `sealed_testimony` extends; confirmed LIVE on prod `qcaxemuydxlzpzgnnnoa`
  2026-06-19 via object-existence probe).
- `0f20fec` - E2.3-minimal DISCHARGED (member<->franchise linkage; the auth substrate L.3
  capture rides; the L.3 trigger event).

**Output:** L.3 The Vault is specified as a **capture-only** build surface for the
2026 draft (D-O hard anchor). The minimal admissible slice is compose + seal + the
RLS seal guarantee + consent-at-writing via the new `sealed_testimony` category. The
reveal half (ceremony page, reveal artifact class) is deferred to a season-end unit that
pairs with L.5. Migration `017` (the sealed-letter fact class) and one `010`-adjacent
consent migration are named here; both build against this spec.

---

## 0. Branch-sweep + prod-parity record (2026-06-19)

- Engine remote main-only at `0f20fec`. Frontend remote main-only at `2c5ae6f` after the
  stale fully-merged branch `feat/e2-3-minimal-member-onboarding @ 6e49c26` was
  tag-and-deleted (tag `archive/e2-3-minimal-merged-6e49c26` preserves the tip;
  re-swept and confirmed gone).
- **Standing prod-parity check PASSED.** Object-existence probe against
  `qcaxemuydxlzpzgnnnoa` returned non-NULL for `member_consent_events`,
  `member_consent_current` (W.6 `010`), and `franchise_member_links` (`016`). Parity at
  `016` confirmed. No migration gap; L.3 is cleared to add `017`. (Probe is
  object-existence, not the `schema_migrations` ledger, because `010` was applied via the
  Supabase SQL editor 2026-06-18 and does not write a ledger row - the repo-Done != prod
  hazard from `0f20fec`.)

## 1. Section 9.2 election

The framing question: **what is the smallest L.3 build that honors the D-O anchor and is
exercisable end-to-end, and what defers?** This is D-L3-1.

**Election (D-L3-1): capture-only.** The 08-15 deadline is hard only for the *capture* of
this season's letters - you cannot retroactively capture a letter written before a season
that has already started. The DoR mechanic (juxtapose each letter with what the ledger
recorded) is a *reveal*-time artifact, and the reveal lands at season's end (DoR section
L.3 + line 231: "Season's end (Jan): L.5 Awards Night + L.3 reveal as the Season Finale
ceremony"). The reveal therefore carries no draft-day pressure. v1 ships: compose, seal,
the RLS seal guarantee, consent-at-writing, and the sealed-letter fact class. v1 does NOT
ship the reveal ceremony page or the letter-vs-ledger reveal artifact class (section 5.5).

**The constitutional payload** (the L.3 analogue of E2.3's first live 2a-silence): **a
sealed letter that no role - commissioner and admin included - can read until reveal,
enforced at the data layer, not by policy or honor.** The first live exercise must
demonstrate the seal fails closed (section 7 probe).

**Confidence: high** for capture-only (the DoR's own reveal=season-end mechanic forces the
split). **RATIFIED as recommended 2026-06-19**; the reveal half is registered as a
season-end successor (section 5.5), not pulled into the August slice.

## 2. Section-content verification block

The doctrinal section-substance load-bearing on L.3 is source-anchored in the DoR section
L.3 (`df09a5e`, fresh read this session) and the W.6 consent memo v1.2 (`df09a5e`). The
five-principles substance (section 2.3) and the consent model (member-level, append-only,
revocable-forward, commissioner-cannot-proxy) were source-verified at the W.6 ratification
and are carried forward here. No fresh section-claim surfaced during specification. Roadmap
section 7.5 source-access procedure remains the canonical fallback; not invoked.

**Carry-forward applies. Confidence: high.**

## 3. Identity and scope

### 3.1 What L.3 is

A sealed-letter / time-capsule capture surface. At (or in a window before) the 2026 draft,
each linked member composes a private message - trash talk, bold claims, a note to their
December self - and **seals** it. A sealed letter is timestamped, immutable, and unreadable
by any role until the scheduled reveal. At reveal (season-end, a later unit), letters become
**testimony-class facts** juxtaposed against the verified ledger. The system predicts
nothing; it preserves human words and keeps honest books, and the comedy is the collision.

### 3.2 What L.3 is not

- Not a draft-hour live feature. The live draft hour is permanently OUT OF SCOPE (D-SEQ /
  Draft Weekend protocol). L.3 capture is asynchronous around the draft, not a live-room
  feature.
- Not commissioner-readable. The commissioner hosts the ritual; the commissioner cannot
  read sealed bodies. There is no "to get it working" exception (W.6 section 1.3 idiom).
- Not predictive. A letter is a human claim, never a system forecast. No scoring, ranking,
  or likelihood is attached to any letter at capture or reveal.
- Not mutable. A correction is a new sealed letter, never an edit (section 6).

### 3.3 Fact class and consent class

- **Fact class:** sealed-letter testimony. Pre-reveal it is a sealed datum (existence +
  seal timestamp are facts; the body is withheld). At reveal it becomes a testimony-class
  fact in the permanent record. Migration `017` (section 5.2).
- **Consent class:** the new **`sealed_testimony`** category on `member_consent_events`
  (D-L3-4, RATIFIED option 2). Consent is captured at writing, member-authored only,
  append-only, revocable-forward (a REVOKE before reveal withholds the letter from reveal;
  it never rewrites the sealed record). See section 5.1 and the contract card (chain memo).

### 3.4 Temporal scope

Capture is scoped to a single season (2026). The letter carries the season it belongs to;
reveal is the corresponding season-end ceremony. The 2026 capture window opens on
surface-ship and closes at the draft-table capture moment (D-L3-2, section 8 revision note).

### 3.5 The capture / reveal split (the D-L3-1 shape)

- **Capture (this slice, by 08-15):** compose + seal + consent-at-writing + the sealed
  fact class. Acceptance from sections 5 and 6.
- **Reveal (deferred, season-end, pairs with L.5):** reveal ceremony page; the
  letter-vs-ledger juxtaposition artifact class (engine, via the W.4 reveal-artifact
  docket); the scheduled reveal job. Registered here, built later (section 5.5).

## 4. Doctrinal compliance trace

- **Section 2.3 - five core principles.**
  - *Facts immutable / append-only:* the letters table and the consent category are both
    append-only; correction = new event; reveal does not mutate the sealed row, it changes
    its readability (section 6).
  - *Narratives derived, never fact-creating:* the reveal artifact (later unit) derives
    juxtaposition from two pre-existing fact sources (the sealed letter + the ledger). It
    creates no fact; the letter was the fact, captured at writing.
  - *AI assists; humans approve:* no AI touches the capture path. A member writes their own
    words; nothing is generated. (The reveal artifact, when built, renders human words
    beside ledger facts; any prose framing passes the standard verifier path and founder
    approval.)
  - *Silence over speculation:* the seal IS silence made structural - the system holds the
    words and says nothing, predicts nothing, until the member's chosen reveal moment.
  - *No analytics / optimization / engagement loops / prediction:* no counts surfaced back
    to members, no nudges to write, no streaks, no open-rate. Capture is a single
    deliberate act.
- **Section 4.4 - Tone Engine boundary; social-surface vs social-network.** L.3 is a
  capture surface with no follower graph, no reactions, no visibility of others' letters.
  It is a private deposit into the archive, not a social feed.
- **Section 8.2 - No-New-Foundations.** L.3 adds no new architectural layer. It is one
  append-only fact table + one append-only consent category on the existing
  `member_consent_events` substrate, gated by existing RLS primitives
  (`is_commissioner`, `auth.uid()`). Reuses E2.3's member<->franchise linkage for identity.
- **Section 8.4 - closure certifications.** L.3 is a Window pre-draft build, not a Phase 11
  closure surface; the six closure-cert certifications are not triggered by this
  registration. Recorded as carry-forward, not advanced.
- **Section 9.2 - artisan-frame primary success criterion.** Success is one member's
  sealed letter, provably private, captured before their league's draft - joy-per-hour, not
  reach. DoR: "Small build, enormous joy-per-hour."
- **Section 10.2 - surface-choice is the spec session's call.** This memo is the DECIDE
  session's call for L.3's capture-only registration. Confidence: high.

## 5. Operational shape - Mode B (specified shape)

### 5.1 Consent: the `sealed_testimony` category (`010`-adjacent migration)

Add `sealed_testimony` to the `member_consent_events.category` CHECK set (currently
`media_appearance`, `recorded_voice`, `likeness_derived`, `attributed_quotes`,
`synthesized_voice`). `sealed_testimony` carries **no** `rendering_class` - the existing
biconditional CHECK (`(category='synthesized_voice') = (rendering_class IS NOT NULL)`)
holds unchanged. No other column or policy changes: member-only INSERT, append-only,
revocable-forward, `member_consent_current` view picks it up for free.

- **Republication scope (D-SEQ-6-required, narrowed by default).** The `sealed_testimony`
  write-time GRANT covers **in-ceremony reveal only**. Republication of a revealed letter
  outside the reveal gate (e.g. into a Season-Finale artifact, Almanac, or any surface
  beyond the ceremony) is a **distinct future consent act**, adjudicated at the reveal /
  republication build, never inherited from the capture grant. This is the conservative
  default under append-only: a narrower grant can always be widened later by a new event;
  it honors D-SEQ-6 ("in-room display vs artifact republication are distinct consent
  surfaces, adjudicated separately"). **This is the one section-4 line the founder may
  widen at ratification.** The narrowing is *definitional* (fixed in the contract card),
  not a schema column - no scope column is added now.
- **Escalation note.** This migration touches live consent infra on prod, the same class as
  the `010` apply. It is a Charter section-7 founder-escalation, applied deliberately, not
  silently. Sequence it BEFORE `017`.

### 5.2 The sealed-letter fact class (`017_vault_sealed_letters`, append-only)

Engine/frontend migration `017`. An append-only table; supersession-by-append, the
`015`/`016` idiom (no UPDATE, no DELETE policy). Minimal columns the build resolves:
`id`, `league_id`, `member_user_id` (author, references `auth.users`), `season`,
`franchise_id` (display), `sealed_at`, and the letter body held such that it is **not
SELECT-able pre-reveal** (section 5.3). A SEAL is a terminal event; a correction is a new
row, never an edit.

### 5.3 The seal (RLS-enforced, per DoR)

The DoR is explicit: "Sealed (commissioner cannot read; **enforce at RLS layer**)." The seal
is enforced at the data layer, not by encryption-key custody and not by application code.

- **Specified shape:** the sealed body is held where no SELECT policy grants it to anyone -
  author, commissioner, or admin - while `sealed = true AND reveal not yet fired`. A
  metadata projection (existence + `sealed_at`, no body) is the only pre-reveal read.
  Because RLS gates rows not columns, the build resolves the exact split (body-row vs
  metadata-row, or a body-omitting view); the **acceptance criterion is fixed**: a
  commissioner SELECT of a sealed body returns no body (section 7 probe). Pre-seal, the
  author may read/edit their own draft; SEAL is the point of no return.
- The reveal mechanism (what flips readability) is a season-end concern and is NOT built in
  this slice (section 5.5). This slice must only guarantee the *closed* state is closed.

### 5.4 Routes and surfaces (frontend)

- A compose+seal surface for the authenticated, franchise-linked member (rides E2.3
  linkage; `get_user_league_id()` scoping). Draft autosave pre-seal; an explicit, confirmed
  SEAL action.
- The consent grant (`sealed_testimony`) is captured inline at writing - the member grants
  before sealing; no commissioner proxy.
- No surface exposes any other member's letter or its existence-count.

### 5.5 What this slice explicitly does NOT build

- The reveal ceremony page.
- The letter-vs-ledger juxtaposition reveal artifact class (engine; via W.4
  reveal-artifact docket).
- The scheduled-reveal job / the readability flip.
- Any republication-scope consent beyond the in-ceremony grant (section 5.1).

These are registered as the **L.3 reveal unit**, season-end, pairing with L.5 into the
Season Finale ceremony if the founder elects (DoR line 231).

## 6. Surface-specific invariants

1. **The seal fails closed.** No role - commissioner, admin included - can obtain a sealed
   body pre-reveal. Default-deny; a missing/!ambiguous policy must deny, never expose
   (the inverse of the G11 false-pass: a missing object must not read as a granted SELECT).
2. **Append-only at every surface.** Letters and consent events are insert-only. A
   correction is a NEW sealed letter. A consent change is a NEW GRANT/REVOKE. Reveal changes
   readability, never the stored row.
3. **Seal timestamp is itself a fact.** `sealed_at` is immutable and is the provenance of
   the testimony at reveal.
4. **Member authorship only.** The commissioner cannot author, seal, edit, or read a
   member's letter, and cannot proxy the consent grant (W.6 section 1.3).
5. **No engagement surface.** No counts, nudges, streaks, reminders, open-rates, or
   visibility of others' participation. Capture is a single deliberate act.
6. **Revoke is forward-only.** A REVOKE before reveal withholds the letter from reveal; it
   never deletes or rewrites the sealed record.

## 7. Governance

- **Migrations:** the `010`-adjacent `sealed_testimony` consent migration (section 5.1,
  founder-escalated, sequenced first), then `017_vault_sealed_letters` (section 5.2). Both
  applied with the same verify-at-the-layer-the-claim-is-about discipline; confirm on prod,
  do not trust repo-Done.
- **Governance probe (the seal-fails-closed gate),** analogue of G21/G11: seed a sealed
  letter; assert a commissioner-context SELECT of the body returns no body; assert anon and
  non-author member likewise; assert the metadata projection returns existence +
  `sealed_at` only. This probe is the acceptance gate for the slice and must run green on
  prod-shaped RLS, not only local.
- **Predecessors:** W.6 (`010`, consent at writing) - confirmed live. E2.3 (`016`, linkage)
  - confirmed live. No other predecessor outstanding.
- **Chain siblings (light chain):** this specification (the build spec + decision register);
  a contract card (the binding `sealed_testimony` consent declaration, including the
  in-ceremony-only republication scope of section 5.1); the discharge record at acceptance.

## 8. Revision point and the D-SEQ-4 amendment

**D-SEQ-4 amendment (supersedes the line carried in `9f5d0fb`).** E2.3-minimal landed
2026-06-18; D-SEQ-4's trigger ("opens when E2.3-minimal lands") is satisfied. Corrections:

- The L.3 **build / collection-eligibility window is ~8.3 weeks (06-18 -> 08-15)**, not the
  "~4-4.5 wk" the pin computed off a mid-July landing estimate.
- The **08-15 draft table is the WRITE/SEAL capture moment**, not a reveal. The pin/ruling
  wording "reveal at draft table" is corrected: **reveal is the season-end ceremony
  (~Jan 2027), paired with L.5** (DoR line 231).
- The practical near-term gate is the **L.3 surface build**, not the trigger (met) or member
  auth (live).

**D-L3-2 (collection window):** open composition on surface-ship; no artificial mid-July
hold; draft day is the capture focal point / close. **D-L3-3 (build before collection):**
yes - the build can and should land ahead of 08-15; do not wait. **RATIFIED as recommended
2026-06-19.**

## 9. Track sequencing carry-forward

Docket (per `e908863`, date-pinned `9f5d0fb`): E2.3-min DISCHARGED -> **L.3 (this memo,
-> in-flight)** -> L.1 first wave (Aug sweep, D-N) -> W.1 Inc 2. Overflow only: W.2 / W.3 /
W.5-taxonomy. The L.3 reveal unit is registered as a season-end successor (pairs with L.5).
Runbook trigger PARKED 2026-07-18.

## 10. Adaptations from template v1.0

Light-chain compression: the admission/decision register (normally a separate chain memo)
is folded inline (section 1 election + the D-L3 register) because L.3 is the DoR-predicted
"four-memo chain (light - likely the fastest chain yet run)." The closure-cert sections
(section 4.4 certifications) are recorded as not-triggered rather than exercised - L.3 is a
Window build, not a closure surface.

## 11. Confidence labeling

- D-L3-4 (`sealed_testimony` category): **RATIFIED** (founder, in-session, option 2).
- D-L3-1 (capture-only) / D-L3-2 (window) / D-L3-3 (build-first) / D-L3-5 (reveal defers):
  **RATIFIED as recommended** (founder, 2026-06-19).
- Republication scope (section 5.1): **HELD in-ceremony-only** (founder-ratified
  2026-06-19); republication outside the gate is a distinct future consent act.
- Seal mechanism (section 5.3): invariant fixed (fails-closed); exact RLS row/column split
  is a build-resolved detail with a fixed acceptance criterion.

---

**Ratified 2026-06-19 (founder, DECIDE session).** All D-L3 decisions settled: D-L3-4 =
`sealed_testimony`; D-L3-1/2/3/5 as recommended; republication scope held in-ceremony-only.
First EXECUTE unit (this slice): the `010`-adjacent `sealed_testimony` consent migration
(sequenced first), then `017_vault_sealed_letters`, the compose/seal surface, and the
seal-fails-closed governance probe. Acceptance derives from sections 5 and 6. STATE flips
docket item 2 -> in-flight in this commit series.
