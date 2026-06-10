# SquadVault — W.6 Consent Governance Memo — v1.2 (RATIFIED)

**Date:** 2026-06-10
**Authored by:** Claude Fable 5 (DECIDE session per Charter v1.0 section 2.1)
**Status:** RATIFIED 2026-06-10 — binding. The founder ratified all six numbered decisions
(D-S through D-X) as recommended; Claude Code (Opus 4.8) recorded the ratification and filed
this canonical copy. Per Charter v1.0 section 2.1/2.4 the founder is the ratifying authority
and the constitutional adjudicator — the session is the scribe, not the decider.
**Supersedes:** v1.1 DRAFT (same session, never ratified) — Section 0 made self-evidencing
(Appendix A: file/line evidence for every frontend claim at `4e44bb3`); D-V's sibling-
discipline mechanism corrected from "no-UPDATE/no-DELETE policies" to the repo's actual
posture, RLS default-deny (Appendix A, rows 3-4 and note). v1.1 absorbed the sharpened brief
at engine `28e6b62`/`c441c75` (W.8 consumer, default-posture law, consistency statements,
L.3 critical path, DoR-term correspondence in D-S); v1.0 was the original frame.
**Verified anchors at authoring:** engine HEAD `c441c75` · frontend HEAD `4e44bb3`
**Independent verification:** Section 0's frontend claims were independently re-read from the
engine workspace at frontend `4e44bb3` (all 8 Appendix A claims confirmed; one non-load-bearing
A8 table-count imprecision noted) — memo `_observations/OBSERVATIONS_2026_06_10_W6_SECTION0_FRONTEND_VERIFICATION.md`, engine `5184b9d`.
**Sequencing note:** W.6 is on the critical path to L.3 (The Vault), which carries the
track's hardest calendar anchor — live before the 2026 draft (August). Ratification of this
memo is what starts that clock's buildable portion.
**Authority:** Constitutional (Track W/L governing frame). Where this memo conflicts with any
Tier 0-2 canonical document, the canonical document governs.

---

## 0. Substrate finding (corrects DoR Part 3, Unit W.6)

The DoR states W.6 "extends `founding_sessions.consent`." Verified at both repos:

- Engine (`c441c75`): no consent state exists anywhere — confirmed independently by the Opus
  workspace session (grep over core/storage empty) and by this session.
- Frontend (`4e44bb3`): `founding_sessions.consent` exists in the founding-session machinery,
  as the brief locates it [A1]. But its current shape is **mutable** — written via UPDATE
  [A2], under an UPDATE-permitting RLS policy [A3], with no event history and no append-only
  protection on the field [A4] — **league-level** (one value per founding-session row, keyed
  to the commissioner; no member dimension) [A5], and a **three-boolean bundle** (`photos`,
  `voice_recording`, `text_likeness`) [A6]. The consent-panel UI itself promises the
  per-member layer that was never built [A7], and no other consent store exists anywhere in
  the repo [A8].

Every bracketed claim is pinned to file and line in **Appendix A**; this section asserts
nothing the appendix does not evidence.

Per-member, append-only, revocable-forward consent cannot be produced by extending that
field; mutability and subject-level are structural, not additive. **This memo therefore
establishes a new append-only event class as the consent system of record** (section 5), and
reinterprets `founding_sessions.consent` as the league-defaults layer (section 7.1, D-X). The
DoR sentence is honored in spirit: the founding trio is the seed, and its own UI copy ("each
member can adjust their own when they join") is precisely the promise this memo keeps.

## 1. Constitutional position

1. **A consent grant is a fact.** It is attributed, timestamped, append-only, and enters the
   record by ratification — the Manual Fact Import constitutional frame applies. Current
   consent state is a **derived read over the event log, never stored mutable state** (the
   same law W.5 binds for trophy custody).
2. **The subject of consent is the person, not the franchise.** Franchise slots change hands
   (0010 is the documented case); a person's likeness, voice, and words are theirs across any
   slot they ever held. Consent events anchor to the member's auth identity.
3. **Only the member can grant.** The commissioner cannot proxy a grant for another member —
   not during onboarding, not for the deceased, not "to get the feature working." The
   commissioner ratifies *uses* (tags, pitches, publications); only members ratify *grants*.
4. **DEFAULT-POSTURE LAW: in the absence of an explicit current grant, the system makes no
   use — no capture, no derivation, no publication.** Every category, every member, every
   rendering class defaults to ungranted. A member who has not yet onboarded has no grants,
   and consent-requiring surfaces simply show nothing for them. Silence over speculation is
   the consent posture, not just the narrative posture. No future session may treat absence
   of objection, presence in the league, or a league default as a grant.
5. **Consent state is never telemetry.** Who has granted what is admission-gating data read at
   the moment of use. It is never aggregated, scored, reported on, or used to prompt members.
   "7 of 10 members have opted in" appears nowhere in any surface, ever.

## 2. Category taxonomy — D-S

**D-S: Five separate consent categories matching the DoR's five named surfaces, each
independently grantable and revocable. Granting one never implies another. No bundles.**
(Recommended; the one boundary refinement vs. the DoR's informal mapping is flagged below.)

| # | Category | DoR term | Governs | Consumers |
|---|---|---|---|---|
| 2a | `media_appearance` | MEDIA APPEARANCES | The member's presence in archival corpus items being **identified and displayed as them** (ratified tags on photos/video) | W.1 tagging, W.8 candidate-photo surfacing |
| 2b | `recorded_voice` | RECORDED VOICE | Capture and playback of the member's actual voice | L.4 Answering Machine, W.1 video audio |
| 2c | `likeness_derived` | LIKENESS | Use of the member's image **in derived/rendered artifacts** — Gazette art, W.4 press-conference renderings, W.8 generated-art contexts | W.4 classes, W.8, L.8 |
| 2d | `attributed_quotes` | ATTRIBUTED QUOTES | The governed-testimony fact class: captions (W.1), interview accounts (L.1), letters at reveal (L.3), answering-machine transcriptions (L.4), press-conference words (W.4), **W.8 tappable wall-provenance receipts** ("hung here because Robb told the historian, March 2026") | W.1, W.4, W.8, L.1, L.3, L.4 |
| 2e | `synthesized_voice` | SYNTHESIZED VOICE | Any rendering of a voice presented as the member's that the member did not speak | post-W.6 audio rendering classes only (e.g., league radio) |

**Boundary refinement (founder may collapse):** the DoR's informal mapping put W.1 tagging
under LIKENESS and the raw corpus under MEDIA APPEARANCES. This memo draws the line at
**archival vs. derived**: 2a governs being identified in real archival media; 2c governs the
image's use in *new, rendered* artifacts. The refinement exists because the risk profiles
differ — appearing tagged in a real 1998 photo is not the same act as one's face in generated
Gazette art — and because W.8's D-R boundary ("no member likeness in generated art ahead of
W.6") needs 2c to be its named gate. **[Ratified 2026-06-10: kept separate — boundary stands.]**

Boundary clauses:

- **2e is the strictest gate in the product.** A `synthesized_voice` grant is scoped **per
  rendering class** (e.g., "league radio readings of approved artifacts"), not blanket. A new
  synthesis class requires both its own SAT admission and a fresh per-member grant for that
  class. Default OPT_OUT, never pre-checked, never bundled with 2b, never inferred from it.
  Part 8's "no likeness or voice synthesis ahead of W.6" resolves here: this memo authorizes
  **no synthesis**; it defines the only gate through which a future class may ever be
  considered (section 8).
- **Names in the factual record are not a W.6 category.** Owner display names in recaps,
  standings, and archives are the factual record itself, governed by the existing
  `text_likeness` league default. W.6 does not retroactively gate them, and no future session
  may cite this memo to strip names from verified facts.
- Raw group media in the corpus (a team photo nobody is tagged in) is governed by W.1's
  room-level ratification; 2a governs the **identification** of a member in it and
  member-focused display.

## 3. Lifecycle: "captured once, ratified per-member" — D-T

**D-T: Grant events are captured once per (member, category[, rendering-class for 2e]) and
stand until superseded by a later event. Ordinary uses do not require per-use member
ratification; every use is gated by a read of current state at the moment of use.**
(Recommended.)

- "Captured once" means the member is asked once, at a natural moment (Member Office settings;
  the L.1 interview intro; L.3 letter compose; L.4 first recording), not re-prompted per
  artifact. Re-prompting at volume is notification pressure wearing consent's clothes.
- "Ratified per-member" means each member's own affirmative act creates the event. League
  defaults (section 7.1) configure features; they grant nothing on a member's behalf.
- The event stream is append-only: a later GRANT or REVOKE supersedes; nothing is edited or
  deleted. Re-grant after revocation is a new event, fully legal, fully ordinary.
- **Gate placement:** consent is read at three gates — **capture** (may this testimony/media
  be taken in), **derivation** (may a generator use it as input), and **publication** (may the
  approved artifact render it). All three read the same derived current-state; a revocation
  between gates takes effect at whichever gates remain.
- **Composition with the four-memo chain / SAT:** the chain clause in section 7.2 makes the
  category-and-gate declaration a mandatory contract-card field, so admission of a new surface
  is where its consent reads are adjudicated — once, structurally, not per artifact.

## 4. Revocable-forward semantics — D-U

Revocation at time T stops future use and never rewrites the past record. Precisely:

1. **Capture stops at T.** No new testimony/media/recording in the revoked category.
2. **Derivation stops at T.** No new artifact may take the revoked material as input. For W.4,
   in-flight pitches that depend on it are killed; killing a pitch is the docket working. For
   W.8, no new placement proposals draw on it; items already placed are governed by clause 4.
3. **The past record stands.** Consent events before T, the material captured under them, and
   artifacts already approved and published remain in the record unmodified. The
   grant-at-time provenance is what makes the past use legitimate forever; revocation does not
   retroactively delegitimize it. Nothing in this memo creates a path that mutates the
   immutable factual ledger — revocation writes a new event; it never edits an old one.
4. **Already-published artifacts — D-U, the one genuine fork:**
   - **(a) Strict-exclusion:** future compilations (Almanac, Gazette reprints, archive
     re-renders) exclude any artifact containing revoked material. Rejected as recommended
     option: it rewrites the presentation of history and makes the Almanac's contents a
     function of the consent table — the past becomes editable through the side door.
   - **(b) Artifact-integrity (RATIFIED 2026-06-10):** an approved, published artifact is
     sealed. It may be reproduced **intact** in compilations and continues to render in the
     archive. What revocation forbids is **new derivation** — extracting the revoked
     quote/image into new prose, new art, a new placement, or a new artifact class.
   - Independent of the pick: a member may additionally request **display withdrawal** of a
     specific published artifact or item (including a W.8 wall placement) — a separate,
     commissioner-ratified, append-only act that removes it from forward-rendering surfaces
     while it remains in the permanent record. Withdrawal is a courtesy mechanism, never
     automatic, and never deletion.
5. **Death does not revoke.** Standing grants persist (the Permanence promise: the memory
   outlives members). Family/estate requests are handled through display withdrawal,
   commissioner-ratified, with the record itself untouched. No one inherits the power to grant
   on the deceased member's behalf — categories they never granted stay ungranted forever.

## 5. Record shape and ratification surface — D-V

**D-V: System of record is a new frontend (Supabase) table, `member_consent_events`,
append-only under the sibling discipline — RLS enabled, SELECT and INSERT policies only,
**no UPDATE or DELETE policy granted** (the repo's actual no-rewrite mechanism is RLS
default-deny: migration 003 enables RLS on all thirteen tables and contains zero DELETE
policies anywhere — see Appendix A, rows 3-4 and note).** (Recommended. Rationale: consent is
granted, read, and displayed where members live — the Clubhouse; the engine has no member
auth identity. The engine consumes a derived allowlist, section 7.3.)

Event form (binding shape; exact DDL is the implementing unit's work):

- `member_user_id` (the subject — and, per section 1.3, the only legal author of GRANT
  events; REVOKE likewise member-only)
- `event_type` — `GRANT` | `REVOKE`
- `category` — enum of section 2
- `rendering_class` — required for 2e, null otherwise
- `context` — where captured (`member_office_settings`, `l1_interview`, `l3_compose`,
  `l4_recording`, ...)
- `note` — optional member text
- `recorded_at` — timestamptz

Plus a sibling append-only class for section 4's display withdrawals (member-requested,
commissioner-ratified, item- or artifact-scoped).

**Ratification surface:**

- **Member sees:** plain-language category descriptions (the consent-panel copy register, not
  legalese), their own current state, their own full event history, and one-tap grant/revoke.
  Lives in the Member Office. Capture moments inside L.1/L.3/L.4 flows present only the
  categories that flow requires, linking to the full panel.
- **Commissioner sees:** per-member current state, **read-only**, surfaced at the admission
  gates (Office review checklist, W.1 tag ratification, W.4/W.8 pitch review). The
  commissioner never edits consent state and is never shown aggregate consent statistics
  (section 1.5).

## 6. Granularity: member-level grants, item-level reads — D-W

**D-W: Consent grants are member-level per category (per rendering class for 2e). Item-level
acts — tagging a member in a photo, attributing a caption, placing a W.8 receipt — are
ratifications that READ the member-level grant; they are not themselves consent events. No
per-item consent matrices.** (Recommended.)

- W.1's room-level consent ratification (commissioner ratifies the corpus is shared with the
  league) is a **league-scope** act and remains W.1's own; it grants nothing about any
  individual member. The layering is: room-level (corpus exists) → member-level (W.6 grant)
  → item-level (ratified tag/caption/placement that reads the grant).
- A member's objection to a specific item is handled by display withdrawal (section 4), not by
  inventing item-scoped revocation events.

## 7. Interoperation bindings

**7.1 Disposition of `founding_sessions.consent` — D-X.** Reinterpreted, unmodified, as the
**league-defaults layer**: commissioner-set feature posture (are photos/voice features enabled
for this league at all). It grants nothing per-member. No migration, no jsonb extension. The
commissioner's own W.6 grants are captured fresh through the member surface like everyone
else's — the founding trio does not seed them. A doc-only note in the frontend repo records
this reinterpretation; DoR Part 3 W.6 text is corrected by supersession note.

**7.2 Surface Admission Test / four-memo chain clause (binding on every future chain).** Any
surface or artifact class touching member likeness, voice, or attributed words must declare in
its contract card: (a) which section-2 categories it reads, (b) at which of the three gates
(capture / derivation / publication), and (c) its behavior on revocation mid-flight. A chain
missing this clause is returned, not guessed at. W.1, W.4, W.8, L.1, L.3, L.4, and every audio
rendering class inherit this immediately.

**7.3 Engine read path (invariant, not implementation).** The engine has no consent state and
gains none. Generation that would use consent-gated material receives a **deterministic
allowlist derived from current consent state** in its input context (the FAAB-allowlist
pattern), and verification gates check attributed material against it at the output layer.
Plumbing is the implementing unit's brief; the invariant is: no consent-requiring material
enters a generation input, and none survives to publication, without a current grant.

**7.4 Per-unit gates this memo unlocks once ratified.**

- **W.1:** member-tags require 2a; captions require 2d; tag-ratification UI shows the grant
  state read-only.
- **W.4:** press-conference class requires 2d (the member's words) and 2c if rendered with
  likeness; any class rendering likeness requires 2c.
- **W.8:** candidate-photo surfacing of a tagged member reads 2a; tappable wall-provenance
  receipts quote testimony and read 2d; the D-R generated-art boundary is gated by 2c — no
  member likeness in generated ephemera without a current 2c grant, ever.
- **L.1:** interview intro is a capture moment for 2d (and only 2d); no grant, no interview —
  offered warmly, declined without consequence, never re-prompted on a schedule.
- **L.3:** consent captured at writing (2d), as the DoR specifies; reveal reads current state
  at reveal time — a letter whose author revoked 2d before reveal stays sealed (capture
  happened; publication gate fails closed). Sealed-stays-sealed is silence over speculation.
  Calendar note: L.3 must ship before the August draft; this memo's ratification is its
  consent predecessor.
- **L.4:** recording requires 2b; transcription into the quote record additionally requires
  2d; no synthesis here, ever (DoR boundary restated).

## 8. Consistency statements (deliverable f — read at every consuming chain's kickoff)

1. **Against standing law (DoR Part 3):** every consent event is a member's words becoming a
   fact — attributed, consented, append-only. Nothing in this model measures member behavior:
   no consent-completion tracking, no opt-in funnels, no reminder cadences, no aggregate
   reporting (sections 1.5, 3). No telemetry, no autonomous publication, no engagement loops
   are created or enabled by any clause herein.
2. **Against Part 8 ("no likeness or voice synthesis ahead of W.6"):** this memo authorizes
   zero synthesis. It defines 2e as the only gate through which a synthesis rendering class
   may ever be considered: SAT admission of the class + fresh per-member per-class grants +
   the standard human-approval publication path. Absent all three, Part 8's prohibition
   remains in full force. Likeness in generated art is identically gated by 2c.
3. **Against L.1's testimony shape (testimony never contaminates the ledger):** consent
   governs the testimony layer and the use of likeness/voice; it creates **no path that
   mutates the immutable factual ledger**. Grants and revocations are new appended events;
   revocation forbids future use (section 4) and never edits, deletes, or re-renders past
   facts. Verified facts and remembered accounts remain visibly distinct layers; consent state
   gates whether testimony may be captured/derived/published, never what the factual record
   says.
4. **Against the publication constitution (AI assists, humans approve):** AI may propose
   consent-reading uses (tags, placements, pitches); every grant is a human member's act,
   every use-ratification is a human commissioner's act, every publication passes the existing
   approval path. Nothing herein creates autonomous publication.
5. **Against silence-over-speculation:** the default-posture law (section 1.4) is its consent
   form — no grant, no use, no inference from absence.

## 9. What this memo deliberately does not do

No schema is migrated and no surface is built by this memo. No consent analytics, completion
nudges, reminder cadences, or opt-in funnels — ever. No commissioner proxy grants. No
item-level consent matrices. No retroactive gating of names in the verified factual record.
No voice synthesis authorization — 2e defines the gate a future class must pass; it admits
none. No re-litigation of adjudicated Part 4A framings.

---

## Decision register — RATIFIED

Ratified by founder: **2026-06-10** — all six decisions adopted as recommended. Recorded by
Claude Code (Opus 4.8) per Charter v1.0 section 2.1; the founder is the ratifying authority.

| # | Decision | Ratified pick |
|---|---|---|
| D-S | Category taxonomy | Five separate categories mapped 1:1 to the DoR's five terms (2a-2e), independently grantable/revocable; no bundles; 2e scoped per rendering class; archival-vs-derived boundary between 2a and 2c KEPT (not collapsed) |
| D-T | Capture-once mechanics | One grant event per (member, category); uses gated by current-state reads at capture/derivation/publication; no per-use re-prompting except 2e's per-class grants |
| D-U | Published artifacts after revocation | (b) Artifact-integrity: sealed artifacts reproduce intact; new derivation prohibited; display withdrawal available as separate commissioner-ratified act; death does not revoke |
| D-V | Record shape & home | `member_consent_events` in Supabase, append-only via RLS default-deny (SELECT/INSERT policies only; no UPDATE/DELETE policy granted), matching sibling posture per Appendix A; member-only authorship; engine consumes derived allowlists |
| D-W | Grant granularity | Member-level per category; item-level acts read grants; objections via display withdrawal |
| D-X | Disposition of `founding_sessions.consent` | Reinterpret as league-defaults layer, unmodified; W.6 events are the per-member system of record; DoR Part 3 W.6 text corrected by supersession note |

---

## Appendix A — Section 0 evidence register (frontend `weichert/squadvault-frontend` @ `4e44bb3`)

Verification discipline: every Section 0 frontend claim below was read from the repo of
record at the stated HEAD by the Fable session; engine-side claims were independently confirmed
by the Opus workspace session at `c441c75`, and the full appendix was independently re-read at
`4e44bb3` from the engine workspace (memo `OBSERVATIONS_2026_06_10_W6_SECTION0_FRONTEND_VERIFICATION.md`,
engine `5184b9d`). Excerpts are minimal anchors, not summaries — a challenger should re-run the
reads, not trust this table.

| # | Claim | File : line(s) | Anchor |
|---|---|---|---|
| A1 | The field exists, in the founding-session machinery | `supabase/migrations/001_core_schema.sql:137` (table definition spans 129-144) | `consent jsonb NOT NULL DEFAULT '{}'` inside `CREATE TABLE founding_sessions` |
| A2 | Written via UPDATE — mutable in practice | `src/app/api/founding/[sessionId]/consent/route.ts:84-87` | `const update: FoundingSessionUpdate = { consent, state: nextState };` ... `.update(update as never)` |
| A3 | UPDATE permitted by RLS | `supabase/migrations/003_rls_policies.sql:216-220` | `CREATE POLICY "founding_sessions_update" ON founding_sessions FOR UPDATE USING (commissioner_user_id = auth.uid() OR is_admin())` |
| A4 | No append-only protection on the field | `002_constraints_and_triggers.sql` + `003_rls_policies.sql`, full-file greps | Only column-immutability precedent in the repo is `is_demo` (`002:138` comment); zero consent-specific triggers/protections; sole other hit is the `CONSENT_COLLECTION` state-enum entry (`002:59`) |
| A5 | League-level, commissioner-set; no member dimension | `001_core_schema.sql:132` + `003:216-220` | `commissioner_user_id uuid REFERENCES auth.users(id) NOT NULL`; the UPDATE policy keys on commissioner identity; one consent value per session row |
| A6 | Three-boolean bundle | `src/lib/supabase/types.ts:239-243` | `export interface ConsentRecord { photos: 'OPT_IN' \| 'OPT_OUT' \| null; voice_recording: ...; text_likeness: ...; }` |
| A7 | UI promises the unbuilt per-member layer | `src/components/founding/consent-panel.tsx:54` (also `:16`) | "These are the league defaults — each member can adjust their own when they join" |
| A8 | No other consent store exists | repo-wide grep, `supabase/` + `src/` | `member_consent` / `consent_event`: zero hits; no consent table in migrations 002-009 |

**Note on the no-rewrite mechanism (drives D-V's corrected wording):** migration
`003_rls_policies.sql` enables RLS on all thirteen tables (lines 7-19) and contains **zero
DELETE policies and zero explicit deny policies**; deletion is denied by RLS default-deny —
the absence of a granted policy — not by an explicit "no-DELETE policy" object. The sibling
discipline for `member_consent_events` is therefore: enable RLS; grant SELECT and INSERT
policies; grant nothing else. v1.1's looser phrase "no-UPDATE and no-DELETE policies" could
have been implemented as explicit deny policies matching no sibling; corrected here.

**Independent-verification note (engine `5184b9d`, frontend `4e44bb3`):** A1-A7 reconfirmed
at the exact cited file:line; A4's no-rewrite mechanism reconfirmed (13x ENABLE RLS, 0 FOR
DELETE, 0 explicit-deny in `003`). A8's load-bearing claim ("no other consent store") holds —
`member_consent`/`consent_event` zero hits — with one non-load-bearing imprecision: there are
15 tables total, not 13 (migrations `008`/`009` each add a non-consent franchise table); the
"thirteen tables" figure is correct as of migration `003`'s authoring and is irrelevant to the
design, since `member_consent_events` enables its own RLS regardless.
