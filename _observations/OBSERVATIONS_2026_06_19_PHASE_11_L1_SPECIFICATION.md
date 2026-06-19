# OBSERVATIONS 2026-06-19 - Phase 11 L.1 Historian Interviews SPECIFICATION (first wave)

**Session type:** SPECIFICATION (four-memo chain; selection-prep + decision-readiness
discharged by the L.1 scope ruling 597103d). Authored to the per-surface constitutional
memo template v1 (docs/templates/per_surface_constitutional_memo_template_v1.md). Engine
doc-only; SKIPS prove_ci. Append-only; supersedes nothing.

**Anchors VERIFIED this session (git, not brief):** engine main 597103d (L.1 SCOPE RULED);
frontend main d298a2a; both main-only. Reuse source read this session: founding-session
machinery (frontend src/lib/founding/* + api/founding/*), member_consent_events (010),
sealed_testimony (017), vault_sealed_letters / vault_seal_probe (018), founding_sessions
RLS (003), protocol.ts topic/intent model. Mode-B election confirmed: no shipped L.1
operational state at HEAD.

**Ratified input (do not re-litigate):** scope D-L1-1..6 (ruling memo
OBSERVATIONS_2026_06_19_L1_FIRST_WAVE_SCOPE_RULING.md); spec decisions S1..S6 (this
session, founder-ratified): S1 provenance stamp; S2 separation probe; S3 topic pool with
no hard required-coverage gate; S4 GRANT-precedes-capture; S5 two-table append-only split
+ author/admin-only RLS; S6 W.8 register-only.

---

## 1. Section 9.2 election

Framing question surfaced by the scope ruling: does the L.1 first wave ship CAPTURE-ONLY,
or capture plus a first "as remembered by" display panel? ELECTION: Reading 1 (capture-
only), per ratified D-L1-1 and D-L1-5. Reading 2 (capture + first display) is the
defensible alternative, DEFERRED not foreclosed - it becomes the display successor unit.
Reasoning carried forward by reference from the scope ruling (capture-first mirrors the
L.3 pattern; display is its own constitutional surface where the two-layer RENDERING gets
exercised). Confidence: HIGH on the election; HIGH on the elected reading.

## 2. Section-content verification block

Methodology: CARRY-FORWARD + cross-anchor for Reset Memo sections (not directly accessible
this session), SOURCE-VERIFIED for the consent/founding substance read directly this
session. No Roadmap 7.5 source-access invoked.

| Doctrinal substance | Cross-anchor | Verdict |
|---|---|---|
| 2.3 five core principles | DoR v2.1; founder constitution (verbatim) | CONFIRM |
| 4.4 social-surface boundary | carry-forward (E1/A1 chain) | substance-consistent |
| 8.2 No-New-Foundations | this session: L.1 adds no layer (sibling + existing consent) | CONFIRM |
| 9.2 artisan-frame primary | carry-forward | substance-consistent |
| 10.2 surface choice = spec call | discharged by scope ruling 597103d | CONFIRM |
| W.6 supersedes founding_sessions.consent | migration 010 read this session | SOURCE-VERIFIED |

Drift findings: NONE new. Load-bearing substance finding (source-verified, not carry-
forward): founding_sessions.consent is the SUPERSEDED league-defaults layer (010 comment);
L.1 consent binds through member_consent_events, never an inline session field. Disposition:
governs S4/S5 below; no patch needed (it is a reuse-divergence, recorded, not a repo drift).

## 3. Identity and scope

### 3.1 What L.1 IS
A consented, attributed, append-only oral-history interview surface that extends the
founding-session pattern from the commissioner to the ten members. The engine conducts a
structured interview; each member's account is captured as TESTIMONY - a fact-about-what-
was-said, stored attributed and unmerged. The first wave is the pre-draft August sweep
(D-N), riding E2.3 outreach as the onboarding hook.

### 3.2 What L.1 is NOT
- NOT the event ledger. Testimony NEVER contaminates the canonical events ledger; it is a
  distinct layer (the payload invariant, section 6.2).
- NOT the substrate. This is the artisan surface for PFL Buddies; the substrate
  generalization (MFI; non-adapter groups) is a separate track.
- NOT the founding session. That surface is commissioner-keyed, mutable (in-place jsonb +
  UPDATE), and output-generating. L.1 is member-keyed, append-only, and capture-only.
- NOT L.3 (sealed letters; commissioner-cannot-read seal). L.1 testimony is display-
  DEFERRED, not sealed.
- NOT L.4 (audio testimony). L.1 first wave is TEXT-only; recorded_voice defers to L.4.
- NOT analytics or measurement of any kind.

### 3.3 Channel and content scope
Text testimony, member-identity-keyed via franchise_member_links (NOT flat franchise_id -
the slot-0010 multi-owner hazard). First wave: one member captured end-to-end is the
admissibility floor; the ten-member sweep is the target, not a gate.

### 3.4 The capture-only boundary (elected Reading 1)
The first wave builds capture + consent + the separation proof. All display ("as
remembered by" panels in archive surfaces and Member Offices) defers to a successor unit.

### 3.5 Audio defers
recorded_voice (audio testimony) is out of the first wave; L.4 The Answering Machine is
the dedicated audio-testimony unit.

## 4. Doctrinal compliance (section-by-section trace)

### 4.1 Reset Memo 2.3 - five core principles
- Facts immutable / append-only: testimony persists to an append-only child table (no
  UPDATE, no DELETE policy; the 010/018 idiom). Each exchange is an inserted, timestamped,
  attributed row.
- Narratives derived, never fact-creating: testimony is not a narrative and is never
  synthesized into consensus; accounts are stored attributed and unmerged.
- AI assists, humans approve: the engine interviews; the MEMBER consents and authors; no
  auto-publish (display defers; nothing renders without a future human-approved surface).
- Silence over speculation: NO hard required-coverage gate; partial testimony is valid;
  BOUNDARY is honored immediately and never revisited that session; absent members simply
  have no testimony.
- No analytics / optimization / engagement loops / prediction: no metrics on testimony;
  capture is lore/voice-iteration data, not engagement data (section 6.6).
Confidence: HIGH.

### 4.2 Reset Memo 4.4 - social-surface boundary
No follower graph, no engagement loop, no opt-in network mechanism. Captured testimony is
private to author + admin at capture (section 5, RLS); the eventual "as remembered by"
display is a curated archive surface, not a social feed. Confidence: HIGH (carry-forward
substance).

### 4.3 Reset Memo 8.2 - No-New-Foundations
L.1 adds NO new layer. It reuses: founding-session machinery (turn engine, intent classes,
topic tiers, exchange shape); the W.6 consent event log (a new category, not a new system);
franchise_member_links (E2.3). The two new tables are siblings under the existing schema,
not a new architectural foundation. Confidence: HIGH (source-verified this session).

### 4.4 Reset Memo 8.4 - Phase 11 Closure certifications
Provisional posture pending the source-verified enumeration at the Closure session. L.1
first wave is a Phase 11 docket item (item 3), not a closure event. Confidence: MEDIUM
(provisional per template).

### 4.5 Reset Memo 9.2 - artisan-frame primary
The first wave's success criterion is an exquisite oral-history capture for PFL Buddies
ahead of the August draft. The substrate/platform frame is conditional and not the measure
here. Confidence: HIGH (carry-forward).

### 4.6 Reset Memo 10.2 - surface choice is the spec session's call
Discharged by the scope ruling (597103d) and this specification's filing. Confidence: HIGH.

## 5. Operational shape (Mode B - specified)

Mode B: no shipped L.1 operational state at HEAD (git ls-files confirms no member_history /
historian / oral_history_session code). The following specifies what the EXECUTE build will
produce, against which it is measured. This is a FRONTEND build (the founding machinery is
frontend; the engine has no founding-session code).

### 5.1 Capture surface
Reuses src/lib/founding/* by composition: the intent classes (protocol.ts INTENT_CLASSES),
the turn-engine loop shape, the TopicTier vocabulary, and the immutable-mutator discipline
(every mutation returns a new object). The interview runs as a structured turn loop; the
historian opens with the onboarding hook ("the league historian would like a word").

### 5.2 Tables - the two-table append-only split (S5)
- member_history_sessions (metadata, INSERT-once): id, league_id, member_user_id (the
  PERSON, via franchise_member_links), franchise_id (era-correct at capture), state,
  recorded_at. No in-place exchange array.
- member_history_exchanges (append-only CHILD, one row per turn): id, session_id (FK),
  turn (int), speaker (HISTORIAN / MEMBER), content (text), intent_classified (nullable),
  topic_covered (nullable), provenance (the S1 stamp, NOT NULL), recorded_at.
Reuse the founding LOGIC (intent classification, turn shape, appendExchange's pure form)
but PERSIST each turn as an INSERTed row, not an in-place jsonb UPDATE. This makes testimony
append-only at the row level - stronger than the founding session's mutable array, and the
only shape that satisfies the ratified append-only mandate.

### 5.3 Consent binding (S4 - GRANT precedes capture)
The oral_history_testimony GRANT must exist in member_consent_events BEFORE any exchange is
stored. No grant, no capture (W.6 default-posture: absence = no grant). Mirrors L.3's
consent-GRANT-precedes-seal. Consent is NEVER an inline session field (founding_sessions.
consent is the superseded league-defaults layer).

### 5.4 Provenance stamp (S1)
Every exchange row carries a non-strippable provenance discriminator (fixed value, e.g.
MEMBER_TESTIMONY) plus the binding triple (member_user_id, session_id, recorded_at), NOT
NULL, no omittable default. This is the MFI external_source idea re-pointed to testimony:
visible to every consumer including the verifier; the thing that makes what-was-said
structurally distinct from an event fact.

### 5.5 Separation probe + governance gate (S2)
A SECURITY DEFINER testimony_separation_probe() returns booleans only (no content),
asserting: (i) both testimony tables exist; (ii) the provenance column is present NOT NULL;
(iii) NO foreign-key / trigger / write path connects the testimony tables to the canonical
events ledger; (iv) missing object -> FALSE (fails closed, inverse-of-G11, routed through
the helper because the catalog is unreachable via PostgREST). A new governance gate (G23-
class) calls it and FAILS when the structure is missing.

### 5.6 Topic pool (S3 - no hard required gate)
Re-authored for member memory (DoR seeds: how-they-joined, a championship, the 0-14 season,
the trade-everyone-argues-about), all tier RECOMMENDED / OPPORTUNISTIC. NO hard required-
coverage gate (member autonomy + BOUNDARY + silence-over-speculation). Coverage is
descriptive bookkeeping (topic_covered on the exchange), not a progression gate. The founder
ratifies the actual pool content (section 7).

### 5.7 Lifecycle
GRANT (member_consent_events, oral_history_testimony) -> member_history_sessions INSERT ->
per-turn member_history_exchanges INSERT through the interview -> the member ends the
session. NO output generation, NO COMPLETE-with-outputs state (the founding flow's
OUTPUT_GENERATION/COMPLETE does not apply). The captured exchanges ARE the durable record.

## 6. Surface-specific invariants

### 6.1 Append-only at every surface
Both testimony tables: no UPDATE policy, no DELETE policy; append-only by RLS default-deny.
A correction is a new exchange, never an edit. (Reset Memo 2.3.)

### 6.2 Testimony never contaminates the event ledger (THE PAYLOAD)
The two-layer separation is the constitutional payload, the analogue of L.3's seal. Enforced
STRUCTURALLY by 5.5 (no write path to the events ledger; fails-closed probe), not by prompt
guardrail. A remembered account provably cannot be read as, or merged into, an event fact.

### 6.3 No synthesized consensus, ever
Accounts are stored attributed and unmerged. The engine never reconciles two members'
accounts into one; the gap between accounts is preserved, never resolved.

### 6.4 GRANT precedes capture
No exchange is stored without a prior oral_history_testimony GRANT (W.6 default-posture).

### 6.5 Member-only authorship
INSERT on both tables is member-only (member_user_id = auth.uid()); the commissioner cannot
proxy a session, a consent, or an exchange (W.6 section 1.3 - not during onboarding, not for
the deceased, not to get the feature working).

### 6.6 Capture is lore/voice-iteration data, not engagement data
No engagement analytics, ever (Operational Plan section 10 commitment 4). Testimony is the
league's memory, not a measured behavior.

### 6.7 Specification governs live baseline
The live baseline does not silently revise this specification; divergence is a revision-point
event (section 8), not a quiet drift. (Universal; last invariant.)

## 7. Governance

| Decision | Authority | Mechanism |
|---|---|---|
| Author/consent to an interview | MEMBER only | member_consent_events GRANT + member-only INSERT (RLS) |
| Read testimony at capture | author + admin only | RLS SELECT (member_user_id=auth.uid() OR is_admin()); NO commissioner read this slice |
| Interview topic pool content | founder ratifies | the pool is data (protocol-sibling); founder names it pre-build |
| Display / "as remembered by" surface | DEFERRED | future spec (the display successor unit) adjudicates commissioner read + rendering |
| Revoke testimony (forward) | MEMBER only | member_consent_events REVOKE (revocable-forward; withholds future display, never rewrites the captured record) |
| Spec amendment at revision-point | founder | this memo's section 8 |
| Promotion _observations -> docs | founder | after first wave + probe green |
| Map registration tier | founder | Documentation Map |

Member-side rights: league members are not "users," not subjects of analytics, not
audience-segmentation targets. Their testimony is theirs - attributed, append-only,
revocable-forward. RLS narrower-by-default reason for L.1 differs from L.3: L.1 testimony is
not SEALED, it is DISPLAY-DEFERRED; commissioner read is withheld at capture because the
consuming surface is not yet specified, not because of a ceremony seal.

## 8. Revision-point

### 8.1 Primary anchor
The post-first-wave review, on the earlier of (a) the ten-member sweep substantially
captured, or (b) NFL Week 1 ~2026-09-08 (the shared-calendar pattern, Roadmap 4.3).

### 8.2 What it evaluates
Did capture work end-to-end; did the separation invariant hold under real testimony (probe
green across the wave); consent-flow fit (GRANT-precedes-capture friction); whether to
build the display successor next; topic-pool fit (did members hit BOUNDARY often; were the
seeds right).

### 8.3 "one full cycle"
One member captured end-to-end is the minimum cycle; the first wave's full cycle is the
pre-draft sweep (target: the ten members who consent, by the 08-15 soft anchor).

### 8.4 Promotion criteria
First wave captured (>=1 member end-to-end) AND testimony_separation_probe green across all
captured sessions AND the founder elects promotion. Then _observations -> docs.

### 8.5 Alternatives considered (not elected)
Pure calendar (08-15) - rejected as sole anchor: capture is per-member and may run past the
draft. Pure event (first member captured) - too thin to evaluate the wave. The hybrid in
8.1 is elected.

### 8.6 Triggered revision (anchor-independent)
ANY finding that the separation invariant is at risk, or that a write path to the event
ledger exists, triggers immediate revision regardless of anchor.

## 9. Cluster / sequencing carry-forward

### 9.1 L-cluster within-cluster sequencing
L.1 first wave (capture) ships. Carries forward: L.1 DISPLAY successor (the "as remembered
by" rendering); L.2 Ask the Historian (Phase 12 lead candidate, NOT summer work); L.4 audio
testimony (the recorded_voice path); L.5 (pairs with the L.3 reveal half, season-end).

### 9.2 W.8 Memorabilia Pipeline (S6 - REGISTER ONLY)
Registered here as a section-candidate consumer: lore items detected in testimony become
PROPOSED environmental artifacts (human-ratified placement), the L.1 chain as its first
fuel (DoR line 136). DO NOT BUILD. It rides the L.1 and W.4 chains; no build authority is
conferred by this registration.

### 9.3 Docket
Behind L.1 on the pre-Tahoe docket: W.1 Inc 2. Overflow only: W.2 / W.3 / W.5-taxonomy.

### 9.4 Roadmap admissible-surface-set update
Post-L.1-first-wave admissible set adds: the L.1 display successor; otherwise unchanged.

## 10. Prior-attempt findings (minimal)

No failed prior attempts; the chain proceeded cleanly per the four-memo discipline
(selection-prep + decision-readiness discharged as the DECIDE scope ruling 597103d;
specification = this memo; registration follows). Note: 006_oral_history_eligible is prior
ENABLING art (the founding session promotes a PRE_DIGITAL_HISTORY flag naming L.1 as its
consumer) - an anchor, not a failed attempt. Confidence: HIGH on absence-of-findings.

## 11. Adaptations from template v1

- Chain compression: selection-prep + decision-readiness were discharged as a single
  DECIDE scope ruling (anchor-class work under the August clock), so section 1's election
  records the ruling's election rather than re-deriving from separate upstream memos.
- Mode B at section 5 (no shipped operational state).
- Surface-specific divergence not present in E1/A1: the append-only CHILD-table persistence
  (5.2) replaces the founding session's in-place jsonb UPDATE - reuse the LOGIC, diverge on
  PERSISTENCE. Recorded as a section 6.1 invariant.
- Consent via the W.6 event log (5.3) rather than an inline session field - a reuse-
  divergence forced by the 010 supersession.
Confidence: HIGH.

## 12. Confidence labeling

### 12.1 Highest-confidence
- The two-layer separation is the payload and is STRUCTURALLY provable (5.5 / 6.2).
- W.6 supersedes founding_sessions.consent (source-verified, 010) - consent binds via the
  event log, not an inline field.
- Append-only child-table persistence is the correct shape for the ratified mandate.

### 12.2 Medium-high
- No hard required-coverage gate (member autonomy) - defensible alternative (a tiny
  REQUIRED set) named and not elected.
- A new dedicated oral_history_testimony consent category (revocation granularity over
  attributed_quotes), per L.3 precedent.

### 12.3 Medium
- Exact topic-pool content (founder ratifies pre-build).
- Whether the first wave reaches all ten consenting members by the 08-15 soft anchor.

### 12.4 Deliberate silences (silence over speculation)
- The display rendering shape, and commissioner read at display-time - the display
  successor unit's call, not pre-decided here.
- Audio testimony - L.4.
- Any path that promotes a remembered datum into the EVENT ledger - that is MFI territory,
  separately ruled, out of scope here (and per 6.2, never automatic).

---

**State at specification:** engine 597103d / frontend d298a2a (both VERIFIED main). L.1
SPECIFIED. First EXECUTE unit (frontend): oral_history_testimony consent migration ->
member_history_sessions + member_history_exchanges (append-only) -> capture surface reusing
lib/founding/* -> testimony_separation_probe() + G23 gate. STANDING: a FRESH prod object-
existence probe on qcaxemuydxlzpzgnnnoa precedes any migration apply (EXECUTE). Doc-only;
_observations placement; SKIP prove_ci; one topic.
