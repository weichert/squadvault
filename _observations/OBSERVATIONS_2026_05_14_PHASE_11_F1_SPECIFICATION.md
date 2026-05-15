# Phase 11 F1 (Rivalry Chronicle) -- Specification

**Date:** 2026-05-14
**Status:** Provisional / observational. No tier. Not registered in Documentation Map.
Fourth memo in the four-memo F1 chain (selection-prep -> decision-readiness Step 1 ->
Step 2 -> **specification** -> registration). **Fourth empirical exercise of per-surface
constitutional-memo template v1.0 at `5291c46`** (A2, A3, E2-light were the first three).
**Filing precedent:** Tier 5 Live Observation Cadence Doctrine at `1cf4142`.

**HEAD at authoring:** `cb6a796` (F1 decision-readiness Step 2).

**Predecessors (chain order, most-proximate last):**

- `bb0f325` -- Reset Memo v1.0 (doctrinal source)
- `ac96447` -- Documentation Map v1.6 (registry; v1.7 at `83201d9` current)
- `1cf4142` -- Tier 5 Live Observation Cadence Doctrine v1.0 (filing precedent)
- `ba8b58a` -- Phase 11 Surface Roadmap (F1 section 2.3 / section 4.5)
- `5a865a1` -- Phase 11 surface-selection memo (F1 admissibility source)
- `9093a07` -- E1 specification (distribution channel precedent)
- `Rivalry_Chronicle_v1_Contract_Card.md` -- **Tier 2 (governs output structure)**
- `5291c46` -- Per-surface constitutional-memo template v1.0 + skeleton
- `8abdff8` -- F1 substrate-readiness assessment
- `96d937b` -- Chronicle verifier v1
- `4338c96` -- F1 selection-prep
- `97bfd83` -- F1 decision-readiness Step 1
- `cb6a796` -- F1 decision-readiness Step 2 (five elections; seven gaps; this memo's
  direct predecessor)

**Output:** F1 (Rivalry Chronicle) is registered as the sixth Phase 11 product surface
in the chain's provisional `_observations/` location. The five settled Step 2
inheritances are operationalized against template v1.0's twelve-section structure.
The seven spec-session gaps (G1-G7) are adjudicated. Section 11 records template
adaptations (expected: none substantive -- fourth clean exercise).

---

## 1. Section 9.2 election

Per Step 2 (`cb6a796`) joint spec-session shape, founder-confirmed by chain
continuation:

**Election: Reading 1 -- open-trigger, commissioner-elected.**
F1 is specified as a single Phase 11 surface. Any two of the 10 PFL Buddies franchises,
any season in the digital era (2010-present), may be the subject of a chronicle at
commissioner operational judgment. The gated-trigger alternative (generate only at
registered notable moments) was considered in Step 2 section 2 and rejected: the
Contract Card does not require it, and it adds governance overhead inconsistent with
the artisan-frame model.

**Election: D3-Alpha.** F1's chronicles are derived from canonical WEEKLY_MATCHUP_RESULT
events only. No commissioner-curated annotation at v1. The EAL-governed narrative layer
is derived prose -- not a new fact.

**Election: D2-alpha + D2-beta.** Full-season (W1 through final week) as the primary
scope; specific-window available via `--weeks` / `--week-range` / `--start-week/--end-week`
CLI flags. No new code required for D2-beta; it uses the existing consumer CLI.

**Election: Manual distribution at v1.** No automated distribution script. Commissioner
generates, approves, and pastes rendered text to group text manually. Automated
distribution is a named v1.1 follow-on.

**Election: recap_artifacts as canonical store.** No single archive file. Each chronicle
is a distinct versioned RIVALRY_CHRONICLE_V1 artifact.

**Confidence on elections: high** (founder-confirmed inheritance from Step 2 chain).

---

## 2. Section-content verification block

Per E1 spec section 2 / A1-E2-light chain carry-forward: doctrinal section-substance
is source-anchored in the predecessor chain. Reset Memo sections 2.3 / 4.4 / 8.2 /
8.4 / 9.2 / 10.2 substance was source-verified at Roadmap section 6.1 (`bb0f325`
direct read); parent memo section 4 F-cluster screen applied that substance; Steps 1
and 2 confirmed no fresh section-claim surfaced.

**Carry-forward applies. Confidence: medium-high.**

---

## 3. Identity and scope

### 3.1 What F1 is

**F1 -- Rivalry Chronicle** is a registered Phase 11 product surface producing
commissioner-elected narrative artifacts documenting the competitive history between
two PFL Buddies franchises over a defined season scope, grounded strictly in canonical
matchup events and the approved window structure.

**Trigger model (G-open, adjudicated):** Commissioner-initiated at any time. The
commissioner selects any two of the 10 franchises and a season, generates a chronicle
via the pipeline, approves it, and distributes manually.

**Pair universe (G7 adjudicated):** All 45 unique franchise pairs (C(10,2)) are valid
chronicle subjects. Every pair faces every other pair at least once per season
(Step 1 F1-1: min=1 matchup per pair per season across all 16 digital-era seasons).
No pair filtering or ranking is imposed by the spec.

**Temporal scope (G6 adjudicated):** Chronicles cover the digital era (2010-present).
Pre-2010 substrate is incomplete and outside the digital era scope. A full-season
chronicle for season Y covers W1 through the final week of that season (W17 or W18
depending on format).

**Output structure (Contract Card-governed):** Header; Canonical Facts Block (mandatory,
one entry per matchup found); Narrative Layer (optional, EAL-governed derived prose);
Trace Block (mandatory, with deterministic hash); Disclosures. Structure is governed
by `Rivalry_Chronicle_v1_Contract_Card.md` (Tier 2) and rendered by
`format_rivalry_chronicle_v1.py`.

### 3.2 What F1 is not

- Not a weekly-cadenced surface. Chronicles are event-driven.
- Not a browseable archive of all matchups. Each chronicle is a discrete curated
  artifact for a specific rivalry at commissioner election.
- Not A1/A2/A3 -- those archive structural derivations across all franchises; F1
  produces a narrative artifact about a specific pair.
- Not E1 (which distributes weekly recaps automatically) or E2-light (which archives
  them for reading). F1 distributes chronicles manually at v1.
- Not a prediction or trend surface. Narrative restraint is a Contract Card invariant:
  no momentum claims, no trend attribution, no superlatives beyond what facts support.
- Not a social network or engagement surface.

### 3.3 V1.1 follow-on items (G1, G2 adjudicated here)

**G1 -- Multi-season chronicles (v1.1):** Cross-era rivalry history (all matchups
between two pairs across all 16 digital-era seasons) is a high-artisan-frame-fit
extension but requires multi-season window infrastructure not yet built. Deferred.

**G2 -- Automated distribution (v1.1):** `scripts/distribute_rivalry_chronicle.py`
wrapping `fetch_latest_approved_rivalry_chronicle_v1` + group-text send, analogous to
E1's Track A automation. Deferred. The manual model is correct for v1 cadence.

---

## 4. Doctrinal compliance (section-by-section trace)

### 4.1 Section 2.3 -- Five core principles

- **Facts immutable and append-only.** Chronicle generation reads canonical events
  and writes a new RIVALRY_CHRONICLE_V1 artifact (DRAFT state). This write is a
  **derived artifact creation**, not a canonical fact creation. The canonical facts
  (WEEKLY_MATCHUP_RESULT events) are never written or modified by the chronicle
  pipeline. The approval step transitions a DRAFT to APPROVED -- this is the same
  state machine as weekly recaps, and it is append-only (supersession creates a new
  APPROVED version; the prior version is not deleted). **Pass.**
- **Narratives derived, never fact-creating.** The EAL-governed narrative layer
  (`creative_layer_rivalry_v1.py`) produces 2-5 sentence prose derived strictly from
  the matchup facts. System prompt explicitly forbids adding scores, names, or events
  not in the facts. Temperature=0 for determinism. Silent fallback produces facts-only
  output. **Pass.**
- **AI assists, humans approve.** The chronicle pipeline produces a DRAFT; explicit
  human approval via `rivalry_chronicle_approve_v1.py` is the hard gate before any
  distribution. **Pass.**
- **Silence preferred over speculation.** The chronicle verifier's RESTRAINT category
  (soft) flags banned speculation phrases. The narrative layer uses
  AMBIGUITY_PREFER_SILENCE for 0-matchup cases and LOW_CONFIDENCE_RESTRAINT for 1-
  matchup cases. **Pass.**
- **No analytics, optimization, engagement loops, or prediction.** Chronicles are
  static artifacts; no engagement tracking; no recommendation engine; no predictions.
  **Pass.**

### 4.2 Section 4.4 -- Tone Engine boundary

F1 uses the existing Tone Engine (`creative_layer_rivalry_v1.py`) with the PFL
Buddies Voice Profile. No new tone mode. The rivalry-specific system prompt is an
application of the existing creative layer architecture, not an engine modification.
Social-surface-vs-social-network distinction: F1 is a push artifact distributed to
known recipients (the league group text); not a social network. **Pass.**

### 4.3 Section 8.2 -- No-New-Foundations

F1 introduces no new tables, ingest paths, or schemas. The chronicle pipeline uses
`recap_artifacts` (existing table, RIVALRY_CHRONICLE_V1 artifact type already
registered), `canonical_events` (existing), `memory_events` (existing),
`franchise_directory` (existing). The `src/squadvault/chronicle/` module is substrate
engineering work completed prior to this spec. **Pass.**

### 4.4 Section 8.4 -- Phase 11 Closure Memo certifications

Provisional posture per A1-E2-light precedent. F1's registration as the sixth Phase
11 surface advances the surface-evidence base for all six certifications. F1 is
particularly relevant to certification 1 (at least one Phase 11 surface) and
certification 3 (second contracted artifact class operational alongside WEEKLY_RECAP).

### 4.5 Section 9.2 -- Artisan-frame primary success criterion

Per Voice Profile section 5: "The league remembers mistakes and brings them back up
at the worst possible moment -- affectionately." F1's artisan-frame fit is the highest
in the Phase 11 set for narrative depth: it is the only surface that produces a
narrative artifact (vs structured data archive) about a specific relationship, and
that relationship is precisely the "affectionately remembered rivalry" pattern. The
live APPROVED artifact (2024 Stu's Crew vs Paradis' Playmakers, 3 matchups, governed
narrative summary) demonstrates the fit concretely. **High fit. Pass.**

### 4.6 Section 10.2 -- Surface choice is the specification session's call

Discharged by this memo's filing. F1 is specified here as the sixth Phase 11 surface.

---

## 5. Operational shape (Mode B -- specified-shape)

F1 has not yet shipped as an officially distributed surface artifact at HEAD `cb6a796`.
The pipeline exists; two artifacts are in `recap_artifacts` (one APPROVED, one DRAFT).
The APPROVED artifact was generated before the surface specification; this spec
governs the surface's ongoing operation.

**Standard invocation (full-season):**

    ./scripts/py scripts/generate_rivalry_chronicle.py \
        --team-a-id 0001 --team-b-id 0002 \
        --season 2025 --start-week 1 --end-week 18

**Review + approve:**

    ./scripts/py src/squadvault/consumers/rivalry_chronicle_approve_v1.py \
        --db .local_squadvault.sqlite --league-id 70985 \
        --season 2025 --week-index 18 --approved-by steve

**Verify before distributing:**

    PYTHONPATH=src python3 -c "
    from squadvault.core.recaps.verification.chronicle_verifier_v1 import verify_chronicle_v1
    import sqlite3
    conn = sqlite3.connect('.local_squadvault.sqlite')
    text = conn.execute(
        \"SELECT rendered_text FROM recap_artifacts
         WHERE artifact_type='RIVALRY_CHRONICLE_V1' AND state='APPROVED'
         ORDER BY id DESC LIMIT 1\").fetchone()[0]
    r = verify_chronicle_v1(text)
    print('passed:', r.passed, 'hard:', r.hard_failure_count, 'soft:', r.soft_failure_count)
    "

**Distribute (manual at v1):** Commissioner reads the approved `rendered_text` and
pastes to the league group text channel.

**Export function note (G3 adjudicated):** `fetch_latest_approved_rivalry_chronicle_v1`
fetches the most recently approved chronicle globally. At v1 cadence the commissioner
generates and distributes in a single session, so the latest-approved is the correct
one. Commissioner verifies the pair before distributing. This limitation is named as a
v1.1 fix.

---

## 6. Surface-specific invariants (G4 adjudicated)

**Universal floor (per template section 3.6):**
- Append-only: no deletion of canonical facts; approval is a state transition, not
  a fact mutation.
- No engagement instrumentation.
- No follower graph or social network features.
- Spec governs live baseline.

**F1-specific invariants above the floor:**
- **Narrative restraint is mandatory.** The Contract Card invariant "narrative
  restraint" is not optional at v1. The chronicle verifier's RESTRAINT check (soft)
  and the creative layer's system prompt both enforce it. A chronicle with banned
  speculation phrases may be distributed but must be human-reviewed for the soft
  failure before approval.
- **Facts block is mandatory; narrative is optional.** If the LLM call fails or the
  EAL directive is AMBIGUITY_PREFER_SILENCE, the facts-only output is a valid and
  complete chronicle. The commissioner must not hold a chronicle for distribution solely
  because the narrative is absent.
- **Fingerprint integrity.** The trace block's `facts_block_hash` must match the
  canonical facts that were queried. The chronicle verifier's TRACE check enforces this
  structurally (fingerprint count match); the `facts_block_hash_v1()` function provides
  the deterministic hash.
- **recap_artifacts is the canonical store (G4 adjudicated).** The filesystem is
  optional. A commissioner may maintain `archive/rivalry_chronicles/` by copying
  approved rendered text files, but this is operational practice, not a spec
  requirement. `recap_artifacts` is the truth.
- **Distribution only of APPROVED artifacts.** No distribution of DRAFT artifacts.
  The approval gate (`rivalry_chronicle_approve_v1.py`) is the canonical mechanism.

---

## 7. Governance

- **Approval gate:** Explicit human approval via `rivalry_chronicle_approve_v1.py`
  before any distribution. The verifier (structural pass required) is the pre-approval
  automated check. Human judgment is the final gate.
- **Verifier is a pre-approval gate, not a publication gate.** Hard failures (STRUCTURE,
  TRACE, SCORE_CLAIM) block approval by operator practice; soft failures (RESTRAINT)
  are flagged for human review. The verifier itself does not block the DB write.
- **No self-publication.** Commissioner generates and distributes deliberately.
- **Revision authority.** Changes to chronicle content require a new DRAFT generation
  (re-run the script) and re-approval. Prior APPROVED versions are not deleted.

---

## 8. Revision-point

### 8.1 Primary anchor

**Event-driven; no fixed calendar anchor.** Chronicles are generated at commissioner
operational judgment: when a rivalry matchup is notable, when a season series is
complete between two teams, when a league member asks about a historical rivalry.

### 8.2 NFL Week 1 nominal anchor

At each season start (NFL Week 1, ~September), the commissioner may review the
prior season's chronicle opportunities and generate chronicles for notable season
series. This is the nominal "revision season" for F1. It does not gate generation;
it is a reminder to the commissioner to consider what chronicles are warranted.

### 8.3 One full cycle semantics (G5 adjudicated)

**One full cycle for F1 = at least 3 approved and distributed chronicles across at
least 2 different team pairs, within one NFL season elapsed.**

Reasoning: 3 chronicles demonstrates the pipeline operates reliably for multiple
commissioner use cases; 2 different pairs demonstrates the surface is not pair-specific;
one NFL season elapsed provides calendar grounding for the Closure Memo's certification.

### 8.4 Promotion criteria

F1 promotes from `_observations/` to Map registration when: (a) one full cycle
observed per section 8.3 definition, AND (b) founder election. The earliest this is
eligible: after the 2026 NFL season begins and the first 3 chronicles are generated
and distributed.

### 8.5 Alternative anchors (not elected)

Annual batch regeneration (analogous to A1/A2/A3) was considered and rejected: F1's
chronicles are per-rivalry snapshots, not annual league-wide derivations. There is
nothing to "batch regenerate" annually; each chronicle is a discrete historical record.

### 8.6 Triggered revision

This spec is revised on any finding that the pipeline doesn't anticipate: a Contract
Card amendment at Tier 2; a new artifact type admitted to the chronicle class; a
substrate change affecting matchup fact queries; any finding during operation that
the spec did not address.

---

## 9. Cluster / sequencing carry-forward

### 9.1 F1 exhausts the Phase 11 admissible set

With F1's registration, the Phase 11 admissible-surface-set is:
- **Shipped:** E1, A1, A2, A3, E2-light.
- **E3:** routed to Phase B.
- **F1:** this spec (sixth Phase 11 surface).
- **Admissible (pending):** none.

F1 is the last Phase 11 surface. All admissible surfaces are either shipped, Phase B,
or in-chain. The Phase 11 surface track is complete upon F1's implementation.

### 9.2 Phase 11 Closure Memo eligibility

Per Reset Memo section 8.4, the Closure Memo may be authored when:
- At least one Phase 11 surface has been used by the league for at least one full cycle.
- The founder judges that the six section 8.4 certifications can be honestly made.

F1's registration does not change the Closure Memo's earliest eligibility; that is
gated on E1's full-cycle completion (earliest: after the 2026 NFL season, when E1's
first post-spec revision-point fires). F1's "one full cycle" gate (section 8.3) may
or may not be met before the Closure Memo is authored; it gates F1's spec promotion,
not Phase 11 closure.

### 9.3 SAT predecessor-state

Unaffected. F1 under Reading 1 does not trigger content-class admission. The SAT
predecessor-state remains unmet. Noted per prior spec chain carry-forward.

---

## 10. Prior-attempt findings

No prior failed attempt at an F1 brief. The substrate-readiness arc + four-memo chain
proceeded cleanly.

**Confidence: high.**

---

## 11. Adaptations from template v1.0

**Adaptations from template v1.0: None substantive.** F1 is the fourth post-
ratification exercise of template v1.0 (A2 at `ee671da`, A3 at `38ddcd2`, E2-light
at `fa57056` were the first three). All twelve sections are exercised without structural
deviation.

**One observation worth recording (not an adaptation):**

F1 is the first spec where section 5's Mode B covers a pipeline that *writes* to
`recap_artifacts` (generating DRAFT artifacts and approving them), unlike A1/A2/A3/
E2-light which are read-only consumers. The template's Mode B classification handles
this correctly -- Mode B is "specified-shape for an unshipped surface" regardless of
whether the pipeline has canonical writes. The observation is that F1 surfaces a
previously untested Mode B shape (write-enabled pipeline) and the template accommodated
it without structural change. Recorded as a confirmation of template flexibility, not
an adaptation.

**Template promotion-eligibility note:** F1 is the fourth clean post-ratification
exercise. Template v1.0 is already promoted at `acf55ee` and Tier 4-registered at
`83201d9`. The observation is for the record; no promotion action is needed.

---

## 12. Confidence labeling

### 12.1 Highest-confidence claims

- **The pipeline is complete and produces correct output.** The live APPROVED artifact
  (2024 Stu's Crew vs Paradis' Playmakers) has all four mandatory contract sections.
  18 tests pass covering verifier, generation, persistence, governance. (section 5)
- **D3-Alpha is unambiguous.** All content from canonical events. (section 4.1)
- **Artisan-frame fit is the highest in the Phase 11 set for narrative depth.** Voice
  Profile section 5 anchor confirmed. (section 4.5)
- **F1 is the last Phase 11 admissible surface.** (section 9.1)
- **Template v1.0 fits F1 with no substantive adaptations.** Fourth clean exercise.
  (section 11)

### 12.2 Medium-high confidence claims

- One full cycle at 3 chronicles / 2 pairs / 1 season is appropriately calibrated.
  (section 8.3)
- Manual distribution is correct at v1; the pre-automated model is the right starting
  point. (section 5)

### 12.3 Medium-confidence claims

- The "write-enabled Mode B" observation (section 11) will not surface as a future
  template revision trigger; the template's Mode B classification is robust enough
  to cover it. Medium confidence because this is the first write-enabled spec; a
  future write-enabled surface may surface a nuance the template did not anticipate.

### 12.4 Limitations and deliberate silences

- No prescription of which team pairs to chronicle first. That is operational judgment.
- No prescription of when to generate chronicles during the 2026 season.
- No characterization of the DRAFT artifact currently in the live DB (week_index 18,
  version 1). That artifact predates this spec; its content is not reviewed here.
- No commitment on v1.1 timing (multi-season; automated distribution).

---

## 13. Cross-references

- `bb0f325` -- Reset Memo v1.0
- `ac96447` -- Documentation Map v1.6 / `83201d9` -- Map v1.7
- `1cf4142` -- Tier 5 Live Observation Cadence Doctrine v1.0
- `ba8b58a` -- Phase 11 Surface Roadmap (F1 section 2.3)
- `9093a07` -- E1 specification (distribution channel precedent)
- `Rivalry_Chronicle_v1_Contract_Card.md` -- Tier 2 (governs output structure)
- `5291c46` -- Per-surface constitutional-memo template v1.0
- `8abdff8` -- F1 substrate-readiness assessment
- `96d937b` -- Chronicle verifier v1 (18 tests)
- `4338c96` -- F1 selection-prep
- `97bfd83` -- F1 decision-readiness Step 1
- `cb6a796` -- F1 decision-readiness Step 2
- `src/squadvault/chronicle/` -- complete pipeline
- `src/squadvault/core/recaps/verification/chronicle_verifier_v1.py` -- verifier
- `scripts/generate_rivalry_chronicle.py` -- convenience shim
- `PFL_Buddies_Voice_Profile_v1_0.md` section 5 -- artisan-frame anchor

---

**Filing:** `_observations/OBSERVATIONS_2026_05_14_PHASE_11_F1_SPECIFICATION.md`.
Provisional / observational. No tier. No Map registration. Matches Tier 5 doctrine
precedent at `1cf4142` and predecessor per-surface constitutional memo filings at
`9093a07` / `cddcfb5` / `ee671da` / `38ddcd2` / `fa57056`.

**Next step:** F1 is the last Phase 11 admissible surface. After 3 approved chronicles
are distributed (one full cycle per section 8.3), the spec is promotion-eligible. The
Phase 11 Closure Memo becomes authorable after E1's 2026-season revision-point fires
and the six section 8.4 certifications can be honestly made.
