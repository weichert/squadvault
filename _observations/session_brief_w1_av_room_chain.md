# Session brief - W.1 Mr. Herlth's A/V Room: four-memo chain kickoff (Fable DECIDE)

Authored: 2026-06-10 (Claude Code, Opus), engine HEAD `e237438`, frontend `main` `248895c`.
Consumer: a Fable chat DECIDE session. W.1 is the FIRST BUILD of Track W and "genuine SAT
exercise #1" - it enters via the four-memo chain; Opus builds against the resulting spec.
This brief is the chain's kickoff, NOT a build brief. Paste the block below into Fable.

## Why this is a chain, not a direct build (the gate Opus must not skip)

DoR Part 3 line 109: "All new surfaces enter via the four-memo chain; new fact classes via
the Manual Fact Import constitutional frame; anything touching likeness/voice/words via W.6
consent governance." W.1 trips ALL THREE: it is a new surface, it introduces the
governed-testimony fact class (member captions), and it reads consent. DoR line 111: "Four-memo
chain (genuine SAT exercise #1). Opus builds against spec." No spec exists, so there is nothing
to build against yet - the chain produces it. (Contrast member_consent_events, which was
EXECUTE against already-ratified W.6; W.1's constitutional admission is still ahead.)

---

SquadVault - Fable DECIDE session - Unit W.1: Mr. Herlth's A/V Room (four-memo chain, SAT #1)

ROLE & ROUTING. Fable DECIDE session (Charter 2.1). Output = the W.1 four-memo chain
(constitutional/spec/contract-card/archive per the chain convention) admitting the surface via
the Surface Admission Test. Opus builds against the ratified spec afterward. Distrust this
brief; verify before proposing.

START PROTOCOL (in order):
1. Read CLAUDE.md (Charter v1.0).
2. Read docs/STATE.md; DoR `docs/SquadVault_Product_Document_of_Record_v2_1.md` (Part 3 Unit
   W.1 + the Track W/L standing law at line 109, decisions D-G, and Part 8); the ratified W.6
   memo `docs/SquadVault_W6_Consent_Governance_Memo_v1_2.md` (the consent bindings); and the
   Manual Fact Import constitutional frame
   `_observations/OBSERVATIONS_2026_06_06_MANUAL_FACT_IMPORT_CONSTITUTIONAL_DECISION_FRAME.md`.
3. Verify against git. Anchors: engine `e237438`, frontend `main` `248895c`. Git wins over any
   unverified brief claim.

THE THREE ADMISSION GATES (all must be satisfied in the chain):
- (a) Four-memo chain / SAT - this IS SAT exercise #1; the chain is the admission.
- (b) Manual Fact Import constitutional frame - member captions are a NEW fact class
  (governed testimony: a fact-about-what-was-said, attributed, consented, append-only; it never
  contaminates the event ledger). Formalize the class through the frame.
- (c) W.6 consent governance - W.1 touches likeness and words. A mandatory 7.2 contract-card
  declaration: which section-2 categories W.1 READS, at which of the three gates (capture /
  derivation / publication), and its behavior on revocation. Expected: media_appearance (2a)
  for member tagging/identified display; attributed_quotes (2d) for captions and any
  marginalia kept as testimony. Reads `member_consent_current`; absence = ungranted (no
  display). Revocation-forward: a withdrawn grant stops future identified display / new
  caption use; the past record stands (W.6 section 4).

THE MANDATE (verbatim scope, DoR W.1). Archival photo/video room for the existing media corpus:
Supabase Storage; append-only media entries; HUMAN-RATIFIED provenance tags (contributor /
date / season / event - NEVER AI-guessed); room-level consent ratification; member captions =
first arrival of the governed-testimony fact class; marginalia on items = asynchronous communal
reveling (NO synchronous watch-party in v1). D-G: photo+video read paths, photo-first tooling.
Opus builds against the spec; the founder ingests media via an Opus-built upload/tagging surface.

SUBSTRATE REALITY (verified in the frontend at `248895c` - design against this, do not assume):
- NO Supabase Storage code or buckets exist yet (greenfield: the chain defines the bucket, its
  access/RLS, and the upload path).
- NO media/photo/video tables exist (the chain defines the append-only media-entries table +
  provenance-tag shape; sibling pattern = approval_events / migration 010: RLS enabled,
  SELECT+INSERT only, no UPDATE/DELETE = append-only via default-deny; human-ratified, so an
  edit is a new event, never a mutation).
- MEMBER IDENTITY IS NOT LINKED. `franchises.member_user_id` is populated by no flow; the only
  resolvable authenticated identity today is the commissioner (E2.3 onboarding is the
  prerequisite for the ten members). The chain MUST scope v1 accordingly: founder/commissioner
  media ingest + human-ratified provenance tagging + room-level consent + display are buildable
  now; MEMBER captions, member tagging-of-self, and marginalia (the member-testimony features)
  are gated on E2.3 - decide whether v1 ships read+ingest and defers member testimony, or waits.

OPEN DECISIONS THE CHAIN SHOULD ADJUDICATE (frame as D-x; founder picks - never assume):
1. v1 scope vs the E2.3 member-identity gap (above): ship founder-ingest + display now, member
   testimony later? (Recommended unless the founder wants to pair with onboarding.)
2. Storage bucket model: one league bucket vs per-season; access (signed URLs? authed read via
   the login-gated /league/* tree?); photo+video read, photo-first tooling (D-G).
3. Provenance-tag taxonomy (contributor/date/season/event) and the human-ratification surface;
   reaffirm tags are NEVER AI-guessed.
4. Room-level consent ratification mechanics (commissioner ratifies the corpus is shared with
   the league) vs the per-member W.6 grants captions read - keep the two layers distinct
   (room-scope is W.1's; member-scope is W.6's).
5. Caption / marginalia model as testimony: how a caption becomes an attributed_quotes fact;
   how the 2d gate is read at capture and publication.

FOUNDER PRE-CHAIN LEANING on decision 1 (stated 2026-06-10; still a formal D-x pick in the
chain, recorded here so the chain inherits it): ship founder/commissioner ingest + display in
v1, defer the member-facing testimony half (member captions / self-tagging / marginalia) to
E2.3. Rationale: (a) the buildable half is the FOUNDATION half - bucket, append-only media
entries, human-ratified provenance, room-level consent, display - none of it is redesigned
when members arrive; testimony layers on top. (b) Calendar: W.1 is the first build and L.3's
August clock runs behind it; waiting on E2.3 puts member-onboarding on a media-archive's
critical path for no structural gain. (c) Better product: members arriving to a furnished room
beats an empty one. KEY NUANCE: the chain should still FULLY SPECIFY the governed-testimony
fact class now (the Manual Fact Import formalization and the 7.2 declaration do not need live
members); only the member-facing BUILD defers. That yields constitutional completeness (SAT #1
admits the complete class) without calendar coupling.

BOUNDARIES (non-negotiable): human-ratified provenance, never AI-asserted; no synchronous
watch-party in v1; member behavior is never measured; no telemetry, no autonomous publication,
no engagement loops (Track W/L standing law + Part 8). Verified facts and remembered captions
render as visibly distinct layers (W.6 / L.1 testimony shape).

ESCALATION / OUT OF SCOPE: this is the chain, not the build - no code, no migration, no bucket
created in this session. Don't re-litigate adjudicated framings. Founder ratifies the chain
before Opus builds; numbered decisions get explicit founder picks.

OUTPUT: the W.1 four-memo chain artifacts (admission via SAT #1), including the 7.2 consent
declaration and the Manual-Fact-Import formalization of the governed-testimony class, ready for
founder ratification. Opus then builds against the spec (frontend repo `~/squadvault`).

---

Author's note (engine session, not part of the paste block): W.1 is greenfield (no Storage, no
media tables at `248895c`) and trips all three admission gates, so a direct Opus build would
skip constitutional admission - hence this chain kickoff rather than a build brief. The
E2.3 member-identity gap (same one surfaced in the consent build) is the key v1-scoping input.
Design choices are surfaced for Fable + founder, not pre-decided here.
