# OBSERVATIONS 2026-06-10 - W.1 Mr. Herlth's A/V Room: Constitutional Admission Memo
## Four-memo chain, memo 1 of 4 (SAT exercise #1, native admission)

**Date:** 2026-06-10
**Session:** Fable DECIDE (Charter v1.0 section 2.1). Authored in chat; filed by the Opus
filing session on founder ratification.
**Status:** RATIFIED 2026-06-10 - founder ratified decisions D-W1-1 through D-W1-6 AS
RECOMMENDED (option (a) each); filed this session. The chain now binds.
**Verified anchors at authoring:** engine HEAD `1782e3b` - frontend `main` HEAD `248895c`.
Both match the kickoff brief (`93c2f3a` filed it; `1782e3b` added the founder pre-chain
leaning). All substrate claims below were independently re-verified this session against
the repos of record, not carried from the brief.
**Chain artifacts (this memo names its siblings):**
1. This memo - constitutional admission (the three-gate adjudication).
2. `OBSERVATIONS_2026_06_10_W1_AV_ROOM_SPECIFICATION.md` - the per-surface constitutional
   memo per template v1.0 (twelve sections, Mode B).
3. `W1_AV_Room_Contract_Card_v1_0.md` - the contract card, carrying the mandatory W.6
   section 7.2 consent declaration.
4. `OBSERVATIONS_2026_06_10_W1_AV_ROOM_ADMISSION_RECORD.md` - the admission record and
   registration instructions (the archive memo).

**Predecessors (chain order, most-proximate last):**
- Canonical Operating Constitution v1.0 (Tier 0)
- `bb0f325` - Reset Memo v1.0 (Artisan frame; section 8.2 No-New-Foundations)
- DoR v2.1 (`58b498a` in-repo; Part 3 Unit W.1, Track W/L standing law, D-G, Part 8;
  v2.1.1 supersession note)
- `8e572f9` - Surface Admission Test v1 (provisional, `_observations/`)
- Per-surface constitutional-memo template v1.0 (promoted, `docs/templates/`)
- `docs/SquadVault_W6_Consent_Governance_Memo_v1_2.md` - RATIFIED 2026-06-10 (D-S..D-X)
- `_observations/OBSERVATIONS_2026_06_06_MANUAL_FACT_IMPORT_CONSTITUTIONAL_DECISION_FRAME.md`
  (status OPEN - see section 4.3, which is precise about what this chain does and does not
  take from it)
- Frontend migration `010_member_consent_events.sql` + `approval_events` (001) - the
  append-only sibling pattern (RLS default-deny; SELECT+INSERT policies only)
- `93c2f3a` / `1782e3b` - W.1 chain kickoff brief + founder pre-chain leaning

---

## 1. What is being admitted

**Mr. Herlth's A/V Room** (Unit W.1): the archival photo/video room for the league's
existing media corpus. The first build of Track W. Verbatim mandate (DoR Part 3 W.1):
Supabase Storage; append-only media entries; human-ratified provenance tags
(contributor / date / season / event - never AI-guessed); room-level consent ratification;
member captions as the first arrival of the governed-testimony fact class; marginalia on
items as asynchronous communal reveling; no synchronous watch-party in v1. D-G: photo+video
read paths, photo-first tooling.

The admission is **native admission** in the SAT v1 sense (SAT sections 2.2 and 4.1): a new
surface admitting its own content classes via its per-surface constitutional memo. This
four-memo chain IS the admission record. SAT section 4.2 (cross-surface admission) is not
invoked - see section 6 for the precise E1.7 disposition.

## 2. Substrate findings (verified this session, frontend `248895c`)

These are the facts the chain designs against. Each was re-derived from the repo, not
trusted from the brief:

- **F1 - Storage is greenfield.** Zero Supabase Storage API usage, zero bucket references
  anywhere in `supabase/` or `src/`. The only "storage" strings are two comments
  (`001_core_schema.sql:18-19` - `seal_svg_url`/`seal_png_url` text columns described as
  "Supabase Storage signed URL", never wired to Storage; `005_office_brief.sql:2` - the
  word in a header comment). The chain defines the bucket, access model, and upload path.
- **F2 - No media tables.** No `CREATE TABLE` matching media/photo/video in migrations
  001-010. The chain defines the media-entry and tag-event shapes.
- **F3 - Member identity is not linked.** `franchises.member_user_id`
  (`001_core_schema.sql:48`) is nullable and populated by no flow; the consent page's own
  comment (`src/app/league/[id]/consent/page.tsx:8`) names E2.3 as the linking event. The
  only resolvable authenticated identity today is the commissioner. Combined with the W.6
  default-posture law (section 1.4: absence of a grant = no use), this means **no member
  has any consent grant in any category until E2.3 onboarding occurs.**
- **F4 - The append-only sibling pattern is established.** `approval_events` (001) and
  `member_consent_events` (010): RLS enabled, SELECT + INSERT policies only, no UPDATE or
  DELETE policy granted - append-only via RLS default-deny (W.6 Appendix A note). An edit
  is a new event, never a mutation. W.1's event classes inherit this pattern exactly.
- **F5 - The derived consent read exists.** `member_consent_current` view (migration
  010:72), security_invoker, latest event per (member, category, rendering_class); absence
  of a row = ungranted. W.1's gates read this view (or its server-side equivalent), never
  the raw event table semantics.
- **F6 - The display tree is login-gated.** All league surfaces live under
  `src/app/league/[id]/` (trophy-room, office, members, consent, archive, approve). The
  A/V Room joins this tree; there is no public render path to extend.

## 3. The three admission gates

DoR Part 3 standing law: "All new surfaces enter via the four-memo chain; new fact classes
via the Manual Fact Import constitutional frame; anything touching likeness/voice/words via
W.6 consent governance." W.1 trips all three. Each gate's satisfaction:

### 3.1 Gate (a) - the four-memo chain / SAT

Satisfied by this chain itself. One reconciliation is recorded rather than glossed:

The kickoff brief names the chain "constitutional / spec / contract-card / archive." The
registered convention (template v1.0 section 3.10) names it "selection-prep /
decision-readiness / specification / registration." **The substance maps; the naming is the
brief author's gloss.** For W.1, the selection function was performed upstream: DoR D-L
("W.7 + W.6 immediately; W.1 first build") is the founder-adjudicated selection, and the
kickoff brief plus this session's verification perform the decision-readiness function
(substrate probes = section 2 above; framing = sections 4-5). The chain's four artifacts
therefore are:

| Chain position | Convention name | W.1 artifact |
|---|---|---|
| 1 | selection-prep + decision-readiness (inherited/performed) | this memo (admission + adjudication) |
| 2 | specification | the per-surface constitutional memo (template v1.0) |
| 3 | (W.1-specific addition) | the contract card with the W.6 7.2 declaration |
| 4 | registration | the admission record memo |

The contract card is not in the Phase 11 A-cluster convention because the A-cluster
surfaces introduced no new fact class and read no consent. W.1 does both; the W.6 section
7.2 binding makes the declaration "a mandatory contract-card field," which requires a
contract card to exist. The addition is recorded as a template adaptation in the spec's
section 11.

### 3.2 Gate (b) - the Manual Fact Import constitutional frame

Satisfied by section 4 below, which formalizes the **governed-testimony fact class**
through the frame's admissibility theory - with section 4.3's precision about what is and
is not being decided.

### 3.3 Gate (c) - W.6 consent governance

Satisfied by the contract card's section 7.2 declaration (chain artifact 3), summarized in
section 5 below. **One finding against the brief:** the brief's expected declaration (2a +
2d) is incomplete. The ratified W.6 memo's own section 2 consumer table binds "W.1 video
audio" to **2b `recorded_voice`**. The chain adds 2b to the declaration, with the v1
consequence adjudicated in D-W1-1/D-W1-2 (section 8).

## 4. The governed-testimony fact class (formalized)

### 4.1 Definition

A **governed-testimony fact** is a fact-about-what-was-said: an attributed, consented,
append-only record that a specific member said a specific thing in a specific context. It
is a fact at the testimony layer. **It never contaminates the event ledger** - it asserts
nothing about scores, transactions, championships, or any verified event. Verified facts
and remembered testimony render as visibly distinct layers at every surface, always
(W.6 consistency statement 3; L.1 testimony shape).

W.1's instances of the class: **member captions** on media items, and **marginalia**
(item-anchored asynchronous comments kept as testimony). L.1 interview accounts, L.3
letters at reveal, and L.4 transcriptions are later instances of the same class; this
formalization is written to govern all of them so each later chain inherits rather than
re-derives it.

### 4.2 Admissibility, stated as the frame's four conditions

The Manual Fact Import frame's contribution is its admissibility theory: a fact class is
trustworthy if auditable to a source, with load-bearing provenance, attributed human
approval at ingest, and partial truth without gap-filling. The governed-testimony class
satisfies the four conditions in analogue form:

- **C1 analogue - load-bearing provenance class.** Every testimony row carries, never
  strippably: the author's auth identity (`member_user_id` from `auth.uid()`, the W.6
  pattern - the person, not the franchise), the capture timestamp, the capture context,
  and its class marker (testimony, not verified fact). Every downstream consumer - render
  surfaces today, any future Writer's Room read - sees the class. Testimony can never
  masquerade as a verified fact; the visible two-layer rendering is the provenance made
  legible.
- **C2 analogue - retained source.** The testimony IS its own source: the member's words
  are stored verbatim, append-only, in full. (For the media entries themselves, the
  retained source is the original uploaded file - stored unmodified; provenance tags are
  claims about it, ratified by humans, never edits to it.)
- **C3 analogue - attributed human approval as the ingest act.** The member's own
  authenticated act of writing the caption/marginalium is the ingest approval for
  testimony (enforced as `member_user_id = auth.uid()` at INSERT, the migration-010
  discipline). The commissioner's authenticated upload and tag-ratification acts are the
  ingest approvals for media entries and provenance tags. Who, when, and against which
  item are all in the row.
- **C4 analogue - partial truth, never gap-filling.** Untagged provenance axes stay empty.
  A photo whose year is unknown carries no year - not a guessed one, not a "circa" the
  human did not assert. Date precision is honest (year-only and season-only are legal
  precisions). No AI fills any axis - in v1 there is no AI proposal path at all (W.8 will
  later propose matches for human ratification; that is W.8's chain, not this one).

Determinism's analogue: a testimony row is identified by (author, item, content, captured
timestamp); re-rendering never re-derives or mutates it.

### 4.3 What this formalization does NOT decide (precision against the frame's open status)

The frame's decisions D1-D6 are **OPEN** - awaiting founder ratification - and **this chain
does not ratify them.** They govern the manual-source ADAPTER class: human-attested
artifacts (CSVs, FFLM files) entering the canonical EVENT ledger as platform-adapter-grade
facts. Governed testimony never enters the event ledger, so it does not require the
adapter class to exist and does not advance D1-D6 by precedent. What this chain takes from
the frame is its admissibility theory (the C1-C4 conditions), applied in analogue exactly
as the ratified W.6 memo already did for consent events (W.6 section 1.1: "A consent grant
is a fact... the Manual Fact Import constitutional frame applies"). W.6 is the precedent;
this chain follows it; D1-D6 remain exactly as open after this chain as before it.

### 4.4 Where testimony lives (layer boundary)

Per the W.6 D-V precedent: testimony is member-anchored and auth-resolvable, so its system
of record is the frontend (Supabase), under the F4 append-only sibling discipline. The
engine has no member auth identity and gains none. In v1 no engine generator consumes
testimony; if and when one does (W.4 press conferences, W.8 receipts, L.2), it receives a
deterministic allowlist derived from current consent state per W.6 section 7.3 - that
plumbing is the consuming unit's chain, not this one. This is decision D-W1-6.

## 5. Consent declaration summary (the card carries the binding form)

| Category | W.1 reads it at | Revocation behavior |
|---|---|---|
| 2a `media_appearance` | derivation (the tag-ratification act that identifies a member) and publication (identified display render) | identified display stops forward; tag events remain in the record; display withdrawal available (W.6 section 4, D-U(b)) |
| 2b `recorded_voice` | publication (playback of video audio containing a member's voice) | playback of affected items stops forward; files remain in the corpus |
| 2d `attributed_quotes` | capture (caption/marginalium submission requires a current grant) and publication (render reads current state) | no new capture; no new display derivation; published sealed artifacts intact per D-U(b); display withdrawal available |

Absence of a grant = ungranted = no use (W.6 section 1.4). Raw, un-identified group media
is governed by W.1's room-level ratification, not 2a (W.6 section 2 boundary clause);
identification is what 2a gates. Room-level ratification grants nothing per-member (W.6
D-W layering: room-scope -> member-grant -> item-level ratification that reads the grant).

## 6. SAT disposition (E1.7) - precise, not glossed

SAT v1 section 4.1: "When a new Phase 11 surface is specified, its per-surface
constitutional memo is the native-admission record. No additional SAT process is required
for native admission." Section 2.2 routes new-surface specification to "the four-memo
chain and template v1.0." W.1 is exactly that case. Therefore:

- W.1's admission is **native**, governed by this chain. SAT section 4.2's cross-surface
  process is not invoked and is not exercised.
- **SAT promotion does not trigger.** The SAT's own promotion gate (its section 8 framing
  and the Map patch at `8e572f9` registration) is the first actual CROSS-surface admission
  event. W.1 is not one. The SAT stays provisional in `_observations/`.
- **E1.7's discharge:** DoR E1.7 reads "Surface Admission Test first exercise
  (condition-gated; satisfied naturally by W.1 and W.5's four-memo chains - do not
  manufacture a candidate)." This chain is the SAT's first invocation as the governing
  reference for a genuinely new surface's admission - the first time the native-admission
  routing (SAT sections 2.2/4.1) has been exercised on a surface that did not predate the
  SAT. That satisfies E1.7's intent in the native sense without manufacturing a
  cross-surface candidate. The admission record (chain artifact 4) registers W.1's native
  content classes in the SAT section 5.1 registry by addendum, per SAT section 6 amendment
  rules (registry additions are addenda). E1.7 is recorded as DISCHARGED-NATIVE; the
  cross-surface validation event (and SAT promotion) remains pending, most plausibly at
  the `rivalry_chronicle_v1`-to-E1 admission the SAT itself anticipates.

## 7. Boundaries restated (non-negotiable, inherited)

- Human-ratified provenance, never AI-asserted. v1 contains no AI proposal path of any
  kind.
- No synchronous watch-party in v1.
- Member behavior is never measured. No telemetry, no view counts, no engagement loops,
  no notification pressure. The corkboard announcement pattern (W.3/W.8 "ceremonial
  accumulation") is the only push-adjacent mechanism, and it is not W.1's to build.
- No autonomous publication. Every ingest, tag, and display posture is a human act.
- Verified facts and testimony render as visibly distinct layers, always.
- Facts are immutable and append-only; an edit is a superseding event; nothing is deleted.
- Silence over speculation: empty provenance axes stay empty; absent grants mean no use;
  an empty room section renders honestly empty.

## 8. Decision register - AWAITING FOUNDER RATIFICATION

Numbered decisions per Charter section 3.6. Recommendations are stated; the founder picks.
The founder's pre-chain leaning on D-W1-1 (recorded at `1782e3b`) is inherited as the
recommendation, not as a made decision.

**D-W1-1 - v1 scope vs the E2.3 member-identity gap.**
(a) **[RECOMMENDED - matches the founder's recorded leaning]** v1 ships the foundation
    half: bucket, append-only media entries, human-ratified provenance tagging, room-level
    consent ratification, commissioner upload/tagging surface, and display in the
    Clubhouse. The member-testimony half (member captions, self-tagging, marginalia) is
    FULLY SPECIFIED by this chain but its build is gated on E2.3. Constitutional
    completeness now; calendar decoupling now; members arrive to a furnished room.
    **Folded-in consequence (the 2b finding):** until E2.3 grants exist, video items
    containing a member's voice store and preserve but do not play back; videos the
    commissioner attests contain no member voice may play. Photos are unaffected -
    which is exactly D-G's photo-first posture made concrete.
(b) Wait for E2.3 and ship both halves together (puts member onboarding on a media
    archive's critical path; rejected by the leaning's rationale).

**D-W1-2 - Storage model and access.**
(a) **[RECOMMENDED]** One private league-scoped bucket, `league-media`. Object path
    `{league_id}/{media_entry_id}/original.{ext}` (seasons are tag metadata, not path
    structure - a photo's season can be ratified later or corrected by superseding event;
    paths cannot). No public access. Reads via short-TTL signed URLs issued server-side
    only inside the login-gated `/league/[id]` tree. Photo+video read paths per D-G;
    upload/tagging tooling photo-first (image MIME first-class; video accepted for
    storage and, post-grant, playback). Storage RLS/policies follow the same default-deny
    discipline as the tables: no public policy, no client-direct write path; uploads go
    through the authenticated commissioner surface.
(b) Per-season buckets (rejected: era boundaries are provenance claims, not storage
    structure, and 17 seasons of buckets multiplies policy surface for nothing).

**D-W1-3 - Provenance-tag taxonomy and ratification surface.**
(a) **[RECOMMENDED]** Tags are append-only ratification events against a media entry, in
    five kinds: the four DoR axes - `contributor`, `date` (honest partial precision:
    exact / year-only / season-only), `season`, `event` (free-text occasion, e.g. "2016
    championship party") - plus `member_identification` (tagging a member as appearing),
    which is the 2a-gated kind: the tag event may be recorded by the commissioner, but
    identified display renders only against a current 2a grant (inert until E2.3 for
    everyone but the commissioner). A correction is a new superseding tag event, never an
    edit. The ratification surface is the commissioner's upload/tagging tool; every tag
    row carries who ratified and when (C3). Never AI-guessed - no proposal path exists
    in v1.
(b) Founder amends the taxonomy (axes added/removed) before ratification.

**D-W1-4 - Room-level consent ratification mechanics.**
(a) **[RECOMMENDED]** A single append-only room-ratification event class, commissioner-
    authored: the initial event ratifies that the corpus room is shared with the league;
    each upload-approval act is itself the per-item attributed ingest approval (C3) and
    needs no separate ceremony. Room-scope and member-scope stay strictly distinct per
    W.6 D-W: the room ratification grants nothing about any individual member, ever.
(b) Per-batch explicit room re-ratification ceremonies (rejected: ceremony without
    governance content; the upload approval already carries the attribution).

**D-W1-5 - Caption / marginalia testimony model.**
(a) **[RECOMMENDED]** One fact class, media testimony, two shapes: `caption` and
    `marginalium`, both item-anchored, both 2d-gated at capture and publication, both
    append-only, both rendered visibly distinct from ratified provenance tags and from
    any verified fact. Marginalia render chronologically, finite, unthreaded in v1; no
    reactions, no counters, no unread badges, no notification mechanics - communal
    reveling is asynchronous presence, not engagement machinery. Revocation per W.6
    section 4 with D-U(b) artifact-integrity semantics; display withdrawal available
    per item.
(b) Captions only in v1's specification, marginalia deferred to their own admission
    (rejected: same class, same gates, same table shape; splitting them manufactures a
    second chain for zero governance gain).

**D-W1-6 - System of record / layer boundary.**
(a) **[RECOMMENDED]** Frontend Supabase is the system of record for media entries,
    provenance-tag events, room ratifications, and media testimony (the W.6 D-V
    precedent: member-anchored, auth-resolvable, sibling append-only discipline). The
    engine gains no media or testimony state in v1. Any future engine-side consumption
    rides W.6 section 7.3 derived allowlists, declared by the consuming unit's own chain.
(b) Mirror media facts into the engine ledger now (rejected: no consumer exists; it
    would couple the event ledger to a class that constitutionally never enters it).

## 9. Confidence labeling

- **Highest:** the three gates are correctly identified and each is satisfied by a named
  chain artifact (sections 3-5); the substrate findings F1-F6 (independently re-derived);
  the native-admission routing under SAT sections 2.2/4.1 (the SAT's own text).
- **Medium-high:** the C1-C4 analogue formalization (grounded in the W.6 section 1.1
  precedent; the frame's author wrote the conditions for adapter facts, and the analogue
  mapping is this session's judgment, recorded for the founder to ratify or amend); the
  E1.7 DISCHARGED-NATIVE disposition (DoR E1.7's text says "satisfied naturally by W.1
  and W.5's four-memo chains," which supports it, but the founder may prefer to hold
  E1.7 open until W.5's chain or until a cross-surface event).
- **Medium:** the 2b video-playback consequence's v1 ergonomics (constitutionally forced
  by the default-posture law given F3; the product cost is judged acceptable under
  photo-first D-G, but that is product judgment the founder owns).
- **Deliberately not decided:** frame D1-D6 (open, untouched); W.8's match-proposal
  mechanics; any W.2 aesthetic; any DDL (the spec binds shapes; Opus writes migrations).
