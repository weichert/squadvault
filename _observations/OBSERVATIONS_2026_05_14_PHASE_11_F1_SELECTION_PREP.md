# Phase 11 F1 (Rivalry Chronicle) -- Selection-Prep

**Date:** 2026-05-14
**Status:** Provisional / observational. No tier. Not registered in Documentation Map.
First memo in the four-memo F1 chain (selection-prep -> decision-readiness ->
specification -> registration).
**Filing precedent:** Tier 5 Live Observation Cadence Doctrine at `1cf4142`.

**HEAD at authoring:** `4a71d53` (F1 convenience shim; substrate-readiness arc complete).

**Predecessors (chain order, most-proximate last):**

- `bb0f325` -- Reset Memo v1.0 (doctrinal source)
- `ac96447` -- Documentation Map v1.6 (registry; v1.7 at `83201d9` is current)
- `1cf4142` -- Tier 5 Live Observation Cadence Doctrine v1.0 (filing precedent)
- `5a865a1` -- Phase 11 surface-selection memo (F1 admissibility source; parent)
- `a1f4624` -- Phase 11 decision-readiness memo (F1 D1 gap registered; now closed)
- `ba8b58a` -- Phase 11 Surface Roadmap (F1 section 2.3; substrate-readiness arc
  section 4.5)
- `9093a07` -- E1 specification (first registered Phase 11 surface; distribution
  channel owner; approval lifecycle precedent)
- `Rivalry_Chronicle_v1_Contract_Card.md` -- **Tier 2; governs F1's output structure,
  inputs, invariants, and approval gate**
- `8abdff8` -- F1 substrate-readiness assessment (arc complete; gap inventory;
  this memo's immediate predecessor)
- `4a71d53` -- F1 convenience shim (substrate-readiness arc final commit)

**Output:** F1 (Rivalry Chronicle) is registered as the sixth Phase 11 surface
chain's first memo. Substrate-readiness gate is confirmed cleared. Five diagnostics
(D1-D5) are registered. The founding section 9.2 question is named. Decision-readiness
Step 1 probe targets are registered.

**Structural note:** F1 differs from all prior selection-preps in two ways: (1) the
substrate-readiness arc is already complete at selection-prep time, so D1 is confirmed
rather than uncertain; (2) the Tier 2 Contract Card pre-specifies much of the output
structure, invariants, and approval gate, compressing the governance questions the
spec session would otherwise need to invent from scratch.

---

## 1. Chain-step framing

The Roadmap at `ba8b58a` section 2.3 registers F1 as admissible contingent on substrate-
readiness. Four conditions gate this selection-prep:

1. **Substrate-readiness arc complete.** The arc assessed at `8abdff8` found the
   pipeline ~85% complete; this session added the chronicle verifier (`96d937b`) and
   convenience shim (`4a71d53`). All Roadmap section 4.5 components are now present.
   Gate: **met**.
2. **E-cluster exhausted for Phase 11.** E1 + E2-light shipped; E3 routed to Phase B.
   F1 is the only remaining admissible surface. Gate: **met**.
3. **Template v1.0 promoted.** Binds the downstream spec session. Gate: **met**.
4. **No higher-priority blocking item.** Gate: **met**.

**F1 is selection-prep-eligible. This memo opens the chain.**

**Confidence on predecessor-state: high.**

---

## 2. Section-content load-bearing flags

Per E1 spec section 2 / A1-E2-light chain carry-forward: doctrinal section-substance
is source-anchored in the predecessor chain. No fresh section-claim. Carry-forward
applies.

**Confidence: medium-high.**

---

## 3. F1 identity carry-forward

Per Roadmap section 2.3 and parent memo `5a865a1` section 4 F-cluster screening:

**F1 -- Rivalry Chronicle.** A second contracted artifact class (after WEEKLY_RECAP)
presenting the competitive history between two league franchises over a defined temporal
scope, grounded strictly in canonical matchup events and the approved window structure.

F1 is governed by `Rivalry_Chronicle_v1_Contract_Card.md` (Tier 2). The contract
pre-specifies:
- **Required inputs:** Team A ID, Team B ID, temporal scope, canonical matchup events,
  window metadata.
- **Output structure:** Header; Canonical Facts Block (mandatory, one entry per
  matchup); Narrative Layer (optional, derived); Trace Block (mandatory, with
  deterministic hash); Disclosures.
- **Invariants:** Fact immutability, window sovereignty, narrative restraint, full
  auditability. Silence is valid and preferred.
- **Approval gate:** Explicit human approval required. Approved artifacts are immutable.

**What F1 is not:**
- Not a weekly-cadenced surface (chronicles are event-driven, commissioner-initiated).
- Not a browseable archive of all matchups (it is a curated artifact for specific
  team pairs at commissioner election; the archive model is per-chronicle, not a single
  archive file like A1/A2/A3).
- Not a real-time tracker or standings board.
- Not a social surface or engagement surface.
- Not A1/A2/A3 (those archive structured derivations across all franchises; F1 produces
  a narrative artifact about a specific rivalry at commissioner election).

---

## 4. Diagnostic registration (D1-D5)

### D1 -- Substrate-readiness: CONFIRMED COMPLETE

Per `8abdff8` assessment and this session's arc completion. All contract-required
substrate components exist and are tested:
- `matchup_facts_v1.py` -- canonical WEEKLY_MATCHUP_RESULT query for team pair
- `generate_rivalry_chronicle_v1.py` -- contract-compliant generation pipeline
- `format_rivalry_chronicle_v1.py` -- all four mandatory output sections rendered
- `persist_rivalry_chronicle_v1.py` -- DRAFT state machine, idempotency, versioning
- `creative_layer_rivalry_v1.py` -- EAL-governed narrative, temperature=0, silent
  fallback
- `chronicle_verifier_v1.py` -- STRUCTURE / TRACE / SCORE_CLAIM / RESTRAINT checks
- Approval consumer and convenience shim operational
- Live APPROVED artifact in DB with correct structure

**D1 verdict: substrate-ready. No probes needed at Step 1 for this diagnostic.**

**Confidence: high.**

### D2 -- Product shape candidates

**Question:** What is the v1 surface shape? How does the commissioner elect a
chronicle, and what scope governs it?

**Candidate shapes:**

- **D2-alpha (full-season, commissioner-elected):** Commissioner selects any two
  franchises and a season; the script generates a full-season chronicle (W1-W17 or
  W1-W18 depending on season format). Output covers all head-to-head matchups between
  the pair in that season. This is the shape demonstrated by the live APPROVED artifact
  (Stu's Crew vs Paradis' Playmakers, 2024, W1-W17: 3 matchups found).

- **D2-beta (specific-window, commissioner-elected):** Commissioner specifies
  particular weeks or a week range. Enables "playoff-only" chronicles, "first half of
  season" chronicles, etc. Higher flexibility; slightly more invocation complexity.

- **D2-gamma (cross-season, commissioner-elected):** Multi-season rivalry history.
  Deferred to v1.1 per substrate assessment (single-season only at v1).

**Leading hypothesis for v1:** D2-alpha (full-season) as the primary mode, with
D2-beta (specific-window) available via the existing `--weeks` / `--week-range`
CLI flags. D2-gamma deferred. Step 1 confirms.

**D2 probe targets for Step 1:**
- How many unique head-to-head matchup pairs are available per season? (10 teams,
  5 matchups/week -- each pair meets ~1.7 times/season in a 17-week season.)
- Does the full-season scope (W1-W18) always find at least 1 matchup per pair?
  Or do some pairs not face each other in a given season?

### D3 -- Data authority: D3-Alpha

All content is canonical: matchup facts from `WEEKLY_MATCHUP_RESULT` events; scores
from canonical payload; team names from `franchise_directory`. No commissioner
curation required at v1. The narrative layer is EAL-governed AI prose -- derived, not
fact-creating. D3-Beta (commissioner-annotated chronicle with "historical notes" field)
is a v1.1 path.

**Confidence: high.**

### D4 -- Distribution and revision model

**D4.1 -- Distribution channel:** Push via E1's group-text channel at commissioner
election. Each approved chronicle is distributed as a standalone piece. Same
approval -> distribute model as weekly recaps; the approval consumer and lifecycle are
already implemented.

**D4.2 -- Trigger / cadence:** Event-driven, commissioner-initiated. No fixed calendar
anchor. Chronicles fire at notable moments: a team pair meets in the playoffs; a
longtime rivalry reaches a milestone; end-of-season reflection. The "when to generate"
is commissioner operational judgment, not a spec constraint.

**D4.3 -- Revision model:** Unlike A1/A2/A3 (which have a single archive file
re-generated at revision-points), F1 produces individual per-chronicle artifacts. Each
chronicle is its own versioned artifact in `recap_artifacts`. Revision of a specific
chronicle means generating a new DRAFT (e.g., if a re-approval is needed after a
score correction) -- the idempotency mechanism handles this via fingerprint comparison.
There is no single "F1 archive" to regenerate annually.

**D4 probe targets for Step 1:** Confirm the distribution channel (does E1's existing
group-text path handle RIVALRY_CHRONICLE_V1 artifact type, or does distribution require
a new script?). Confirm the export path for a distributed chronicle.

### D5 -- Surface Admission Test interaction

**Leading hypothesis: Reading 1.** F1 is a single surface. Each chronicle is a
commissioner-elected artifact for a specific team pair and season; there is no
content-class admission mechanism in v1. Reading 2 (F1 as a meta-surface admitting
different chronicle types as content classes) would require a content-class admission
mechanism not yet designed. Reading 1 is the clean default.

**SAT predecessor-state:** Unaffected. F1 under Reading 1 does not trigger content-
class admission. The SAT predecessor-state ("one content-class admission attempted")
remains unmet. The D5 side finding from prior specs (predecessor-state may remain
perpetually unmet under Reading 1 defaults) carries forward.

**Confidence on D5: high.**

---

## 5. The section 9.2 framing question

The founding question for F1's decision-readiness chain:

> Is F1's v1 trigger model "commissioner-elected at any time for any team pair and
> season" (open-trigger), or "commissioner-elected only at registered notable moments"
> (gated-trigger)?

**Open-trigger (leading hypothesis):** Any two of the 10 PFL Buddies franchises, any
season in the digital era, can be the subject of a chronicle at commissioner judgment.
The commissioner generates when they judge a rivalry narrative is appropriate. The spec
governs what the chronicle contains; the trigger timing is operational.

**Gated-trigger (alternative):** Chronicles are only generated when a specific
structural condition is met (e.g., two teams play each other in the playoffs; a pair's
season series is complete; a matchup is designated notable by commissioner). Higher
governance overhead; lower volume; potentially higher per-chronicle quality floor.

**Leading hypothesis: open-trigger.** The gated-trigger adds governance complexity
that the Contract Card does not require. The Contract Card governs output structure and
approval gate; it does not constrain when the commissioner generates. Open-trigger
matches the artisan-frame fit: the league remembers affectionately, and the commissioner
is the one who decides when to surface a memory.

---

## 6. Artisan-frame fit (section 9.2 primary success criterion)

Per Voice Profile section 5: "The league remembers mistakes and brings them back up
at the worst possible moment -- affectionately."

F1's artisan-frame fit is **high and distinctive**. The weekly recap (E1) covers the
current week's story; A1/A2/A3 cover structural history (champions, draft picks, playoff
brackets). F1 covers the *remembered competitive relationship* between two specific
franchises -- who has dominated whom, the close calls, the revenge games. That is
precisely the "affectionately remembered" pattern the Voice Profile anchors on. F1 is
the only Phase 11 surface that produces a narrative artifact (vs a structured data
archive), making it the closest analog to the weekly recap in terms of league experience.

---

## 7. Anti-drift

1. Does not pre-author the decision-readiness brief.
2. Does not pre-determine the section 9.2 election (open vs gated trigger).
3. Does not pre-commit the distribution channel confirmation to D1.
4. Does not advance the SAT predecessor-state.
5. Does not commit to multi-season scope (v1.1 path).
6. Template v1.0 at `docs/templates/` binds the spec (step 3), not this prep.

---

## 8. Cluster / sequencing carry-forward

**Phase 11 admissible-surface-set after F1 selection-prep:**
- Shipped: E1, A1, A2, A3, E2-light.
- E3: routed to Phase B (not a Phase 11 surface).
- In-chain (selection-prep filed): F1 (this memo).
- Admissible: none beyond F1.

**F1 is the last Phase 11 surface in the admissible set.** After F1's specification
and one full cycle, Phase 11 Closure Memo eligibility is gated only on founder
election and the six section 8.4 certifications.

---

## 9. Prior-attempt findings

No prior failed attempt at an F1 brief. The substrate-readiness arc (assessment +
verifier + shim) is clean; this selection-prep opens the four-memo chain without
intermediate failures.

**Confidence: high.**

---

## 10. Confidence labeling

### 10.1 Highest-confidence claims

- F1 substrate-readiness gate is met. (section 1, D1)
- D3-Alpha is unambiguous. (D3)
- Reading 1 is the correct default. (D5)
- F1's artisan-frame fit is high and distinctive. (section 6)
- F1 is the last Phase 11 admissible surface. (section 8)

### 10.2 Medium-high confidence claims

- Open-trigger is the right section 9.2 election. (section 5)
- D2-alpha (full-season) + D2-beta (specific-window) as v1 shape. (D2)
- Distribution via E1's group-text channel. Step 1 confirms. (D4)

### 10.3 Claims this memo deliberately does not make

- No prescription of when the commissioner should generate a chronicle.
- No commitment on how many chronicles constitute a "full cycle" for promotion.
- No advancement of the SAT predecessor-state.
- No authoring of the decision-readiness brief.

---

## 11. Cross-references

- `bb0f325` -- Reset Memo v1.0
- `1cf4142` -- Tier 5 Live Observation Cadence Doctrine v1.0 (filing precedent)
- `5a865a1` -- Phase 11 surface-selection memo (F1 admissibility source)
- `ba8b58a` -- Phase 11 Surface Roadmap (F1 section 2.3 / section 4.5)
- `9093a07` -- E1 specification (distribution channel owner)
- `Rivalry_Chronicle_v1_Contract_Card.md` -- Tier 2 (binds output structure)
- `8abdff8` -- F1 substrate-readiness assessment
- `96d937b` -- Chronicle verifier v1
- `4a71d53` -- Convenience shim (HEAD at authoring)
- `83201d9` -- Documentation Map v1.7 (F1 in Provisional Artifacts)
- `PFL_Buddies_Voice_Profile_v1_0.md` section 5 -- artisan-frame anchor
- `src/squadvault/chronicle/` -- complete pipeline
- `src/squadvault/consumers/rivalry_chronicle_generate_v1.py` -- CLI

---

**Filing:** `_observations/OBSERVATIONS_2026_05_14_PHASE_11_F1_SELECTION_PREP.md`.
Provisional / observational. No tier. No Map registration.

**Next step:** Decision-readiness Step 1 -- empirical probes against D2 and D4
leading hypotheses. Primary targets: (a) unique pair matchup distribution across
seasons (how many matchups per pair per season on average?); (b) distribution channel
confirmation (does E1's export chain handle RIVALRY_CHRONICLE_V1, or is a new script
needed?).
