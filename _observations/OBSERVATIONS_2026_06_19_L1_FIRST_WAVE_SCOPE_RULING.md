# OBSERVATIONS 2026-06-19 - Phase 11 L.1 First-Wave Scope Ruling (RATIFIED)

**Session type:** DECIDE (Charter rhythm). Founder is sole adjudicator; this memo
records the ratified ruling, append-only, superseding nothing. Engine doc-only;
SKIPS prove_ci (the MFI-frame / L.3-spec precedent for _observations rulings).

**Anchors VERIFIED this session (git, not brief):**
- Engine main = 3c39eb6 (L.3 capture DISCHARGED + STATE flip). Branch sweep: main-only.
- Frontend main = d298a2a (L.3 scrub ledger; PR #24 in history). Branch sweep: main-only.
- The authoring brief's anchors matched exactly; brief NOT stale; no in-flight branch.

**Predecessor state:** W.6 SATISFIED (010 member_consent_events live); E2.3-minimal
DISCHARGED (016 franchise_member_links live); L.3 capture DISCHARGED (017 + 018 live,
G22 green). All four recorded live on prod qcaxemuydxlzpzgnnnoa via object-existence
probe at their discharges. See STANDING CHECK below.

---

## 1. What this rules

The minimal admissible first wave of L.1 (The Historian Interviews) for the pre-draft
August sweep (D-N), per DoR v2.1 Unit L.1 (lines 144-150). Scope comes from the DoR
entry, not the brief. Display half and the heavy testimony-promotion case are out of
this slice by ruling, not omission.

## 2. The ruling (D-L1-1 .. D-L1-6, all ratified as recommended)

D-L1-1 MINIMAL FIRST-WAVE SLICE = CAPTURE-ONLY. Build member_history_sessions (a
  founding_sessions sibling: exchanges jsonb, covered_topics, pending_required_topics,
  consent reference, state, timestamps), KEYED TO MEMBER IDENTITY via
  franchise_member_links (NOT flat franchise_id - the slot-0010 multi-owner hazard).
  One member interviewed end-to-end; testimony stored attributed and unmerged. Append-
  only RLS default-deny; member-only INSERT (the 010/018 idiom). Display DEFERS.

D-L1-1 PAYLOAD (the constitutional thing proven on first exercise) = THE TWO-LAYER
  SEPARATION. A remembered account stored attributed and unmerged that PROVABLY cannot
  be read as, or merged into, an event fact. This is L.1's analogue of L.3's
  commissioner-cannot-read seal. Proven by a structural probe (the G22 analogue): a
  fails-closed check that the testimony store carries a non-strippable provenance stamp
  and has NO write path into the canonical events ledger. Missing object FAILS (inverse
  of a vacuous pass), routed through a SECURITY DEFINER helper if pg_policies is
  unreachable via PostgREST (the vault_seal_probe lesson).

D-L1-2 MANUAL FACT IMPORT = FOLDED, NOT A PREDECESSOR. Finding: L.1 testimony is a
  DISTINCT and SAFER fact class than the one MFI formalizes. MFI (status OPEN, D1-D6
  unratified) admits human-attested facts that PURPORT TO DESCRIBE EVENTS (auction
  prices; non-adapter group results) INTO the canonical ledger, audited by
  re-inspectability, with a verifier third path; MFI section 6 calls it the single most
  dangerous capability the product could add. L.1 testimony NEVER enters the event
  ledger - "as remembered by Robb, March 2026" is the complete fact; there is nothing
  to re-derive against ground truth and it can never masquerade as an event fact. The
  provenance disciplines MFI articulates (load-bearing non-strippable provenance;
  retained source; attributed approval; no gap-filling) are ALREADY satisfied for
  testimony by the founding-session machinery (exchanges retains the transcript; consent
  is the approval act) plus W.6 - so MFI rides in as DESIGN LINEAGE and a spec
  co-reference, and is NOT gating. MFI's D1-D6 govern the separate harder case (the 2021
  prices; the substrate-for-non-adapter-groups problem) on their own track. NON-CROSSING
  (binding): a remembered datum is NEVER automatically promoted into the event ledger;
  any such promotion would be an MFI act, separately ruled - and is out of scope for the
  first wave (and per the no-contamination invariant, arguably forever).

D-L1-3 CONSENT SURFACE = NEW DEDICATED CATEGORY (e.g. oral_history_testimony), via the
  017 idiom: widen the member_consent_events category CHECK; member-only INSERT; no
  rendering_class (the existing biconditional holds unchanged); member_consent_current
  picks it up free; FOUNDER-APPLIED via the Supabase SQL editor (charter section 7
  founder-escalation, the 010/017 class). Rationale: W.6 is revocable-forward; mapping
  onto attributed_quotes would mean a member withdrawing their INTERVIEW nukes EVERY
  attributed quote of theirs (Gazette, captions, all of it) - an unintended blast
  radius. L.3 set the precedent of a dedicated category precisely to scope revocation.
  AUDIO (recorded_voice) DEFERS - text testimony first (the W.1 photo-first discipline
  analogue); L.4 The Answering Machine is the dedicated audio-testimony unit.

D-L1-4 SWEEP MECHANICS = PRE-DRAFT REMOTE WINDOW, riding E2.3 outreach. Hard W.6
  constraint observed: member_consent_events INSERT is MEMBER-ONLY; the commissioner
  cannot proxy a grant ("not during onboarding, not for the deceased, not to get the
  feature working", W.6 section 1.3). So no commissioner-driven in-person capture can
  consent-on-behalf. Each member authenticates (E2.3 live) and authors their own GRANT
  on their own device. Per-member cadence across ten; NOT gated on all-ten (absent
  members simply have no testimony yet - silence over speculation). 08-15 is the soft
  "first wave captured" target, not a hard all-ten deadline. The interview IS the
  onboarding hook (DoR line 148); L.1 STANDS AS ITS OWN SURFACE riding E2.3 auth +
  outreach, not subsumed into onboarding. Live draft hour permanently OUT OF SCOPE.

D-L1-5 DISPLAY = DEFERS (capture-first, the L.3 pattern). All "as remembered by" panels
  (archive surfaces + Member Offices) and the two-layer RENDERING are a successor unit
  (their own constitutional surface; verified-vs-remembered visible distinctness is
  where that invariant gets exercised). What can slip without breaking 08-15: all
  display. What cannot slip: capture machinery + consent + the separation proof.

D-L1-6 W.8 DOWNSTREAM = REGISTER ONLY. The Memorabilia Pipeline (W.8) is registered as
  a section-9 section-candidate consumer in the forthcoming L.1 spec (DoR line 136: L.1
  is its first fuel; rides the L.1 chain). DO NOT BUILD.

## 3. STANDING CHECK (repo-Done != prod-applied)

This ruling adds no migration and is not gated on a fresh prod probe. The
member_history_sessions migration and the oral_history_testimony consent-CHECK widen DO
require a fresh object-existence probe on prod qcaxemuydxlzpzgnnnoa BEFORE they apply,
in EXECUTE - the 010-false-pass / L.3-prod-ahead-of-repo hazard. Object-existence, not
the schema_migrations ledger (SQL-editor applies write no ledger row).

## 4. Boundaries (inherited, non-negotiable)

Facts append-only; narratives derived never fact-creating; AI assists humans approve;
silence over speculation; no analytics / optimization / engagement loops / prediction;
architecture frozen. Testimony NEVER contaminates the event ledger; verified and
remembered are distinct layers; no synthesized consensus ever. Live draft hour out of
scope.

## 5. Next step (the green-lit unit)

L.1 is anchor-class; the SPECIFICATION is its own Fable session (four-memo chain:
selection-prep + decision-readiness discharged here as the scope ruling; SPECIFICATION
next; registration follows). The spec is authored to the twelve-section per-surface
template (docs/templates/per_surface_constitutional_memo_template_v1.md) against this
ratified scope. The first EXECUTE unit it green-lights (mirroring L.3's "consent
migration + 017 + compose/seal surface + seal-fails-closed probe"):
  1. Founder-applied consent migration (new oral_history_testimony category, 017 idiom)
     - gated on a fresh prod object-existence probe first.
  2. member_history_sessions migration (founding_sessions sibling; member-identity-keyed;
     append-only RLS default-deny; member-only INSERT).
  3. The interview/capture surface (reuses the founding-session exchange loop + topic
     coverage), one member end-to-end.
  4. The separation probe (the payload proof): non-strippable provenance stamp + no
     write path to the canonical events ledger; fails-closed.

## 6. State at ruling

- Engine 3c39eb6 / frontend d298a2a (both VERIFIED main). Docket item 3 (L.1 first
  wave) -> IN-FLIGHT. Items in order behind it: W.1 Inc 2.
- Prior art read this session: DoR v2.1 Unit L.1; the MFI constitutional decision frame
  (OPEN); founding_sessions schema (001); member_consent_events (010) + sealed_testimony
  (017); vault_sealed_letters / vault_seal_probe (018); 006_oral_history_eligible (the
  PRE_DIGITAL_HISTORY flag naming L.1 as its consumer); the per-surface template.
- Doc-only commit; _observations placement (NOT root - allowlist holds); SKIP prove_ci;
  one topic.
