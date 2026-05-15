# Phase 11 E2-light (Weekly Recap Archive) -- Selection-Prep

**Date:** 2026-05-14
**Status:** Provisional / observational. No tier. Not registered in Documentation Map.
First memo in the four-memo E2-light chain (selection-prep -> decision-readiness ->
specification -> registration).
**Filing precedent:** Tier 5 Live Observation Cadence Doctrine at `1cf4142`. Matches
predecessor memo filings at `5a865a1` / `a1f4624` / `9093a07` / `ba8b58a` / `ba44ba4` /
`3e9065f` / `24e63fa`.

**HEAD at authoring:** `f28be4d` (Phase 11 template v1.0 promotion: Map Tier 4
registration patch; template promotion arc complete; cluster A exhausted).

**Predecessors (chain order, most-proximate last):**

- `bb0f325` -- Reset Memo v1.0 (doctrinal source)
- `ac96447` -- Documentation Map v1.6 (registry; Tier 0V -- Vision Source)
- `1cf4142` -- Tier 5 Live Observation Cadence Doctrine v1.0 (filing precedent)
- `5a865a1` -- Phase 11 surface-selection memo (E-cluster admissibility source; parent)
- `a1f4624` -- Phase 11 decision-readiness memo (Disposition A; Reading 1 shape precedent)
- `ba8b58a` -- Phase 11 Surface Roadmap (E2-light admissibility framing section 2.2;
  sequencing framing section 4.4)
- `9093a07` -- E1 specification (E-cluster first surface; E2-light's direct predecessor
  surface; stabilization condition source)
- `cddcfb5` -- A1 specification (cluster-A Reading 1 election; chain pattern precedent)
- `ee671da` -- A2 specification (chain pattern precedent)
- `38ddcd2` -- A3 specification (cluster-A last surface; section 9.1 cluster exhaustion;
  section 9.2 E2-light carry-forward; direct structural precedent for this memo)
- `ce65310` -- A3 initial archive generation (cluster A operationally complete)
- `5291c46` -- Per-surface constitutional-memo template v1.0 (binds the downstream spec
  at chain step 3; does not bind this selection-prep)

**Output:** E2-light (Weekly Recap Archive) is registered as the fifth Phase 11 surface
chain's first memo. The admissibility carry-forward from `5a865a1` / `ba8b58a` is
confirmed; the E1-stabilization condition is assessed; five diagnostics (D1-D5) are
registered with leading hypotheses; the leading hypothesis for the surface sub-shape
and the section 9.2 framing question are named. The decision-readiness Step 1 session
inherits these diagnostics as its empirical-probe targets.

---

## 1. Chain-step framing

The Roadmap at `ba8b58a` section 2.2 registers E2-light as admissible, sequenced
post-E1 stabilization. Four conditions gate this selection-prep:

1. **Cluster A exhausted.** A1 / A2 / A3 all shipped (specifications at `cddcfb5` /
   `ee671da` / `38ddcd2`; implementation arcs complete). No within-cluster successor
   remains. Confirmed at A3 spec section 9.1.
2. **E1 stabilization assessed.** E1's operational baseline has been running since
   `78a1aff` / `2f7d583`. The `recap_artifacts` table is populated; the verifier is
   running; the archive structure (`archive/weekly_recaps/`) is established; the weekly
   recap lifecycle is mature across multiple operational cycles. Stabilization condition:
   **met** for selection-prep purposes. Decision-readiness Step 1 can revise this
   assessment if a stability concern surfaces during probes.
3. **Template v1.0 promoted.** The per-surface constitutional-memo template that will
   bind E2-light's specification is now at
   `docs/templates/per_surface_constitutional_memo_template_v1.md` (promoted at `acf55ee`).
4. **No higher-priority blocking item.** Pre-commit gate and Map v1.7 are standing items
   but not sequencing gates for surface selection.

**E2-light is selection-prep-eligible. This memo opens the chain.**

**Confidence on predecessor-state:** **High** (all four conditions confirmed by direct
git log read at HEAD `f28be4d`).

---

## 2. Section-content load-bearing flags

Per E1 spec section 2 / A1-A3 chain carry-forward: doctrinal section-substance is
source-anchored in the predecessor chain. No fresh section-claim surfaces in this
selection-prep. Carry-forward applies. The six load-bearing sections (section 2.3 /
4.4 / 8.2 / 8.4 / 9.2 / 10.2) have been source-verified or cross-anchor-confirmed
across the four-chain predecessor arc; A3 selection-prep section 2 is the immediate
upstream.

**Confidence on carry-forward: medium-high.** Multiple anchors; not first-hand re-read.

---

## 3. E2-light identity carry-forward

Per Roadmap section 2.2:

> **E2-light -- Reader-facing browseable archive of approved recaps with structured
> metadata.** Admissible per parent section 4 E-cluster screening at *light* shape
> (no member access management, no multi-tenant adjacency). Sequencing: post-E1
> stabilization. Heavy shape (member access management, web archive with auth) collides
> with Operational Plan section 11 multi-tenancy deferral; not admissible at Phase 11.

**The "light" constraint is structural, not a quality constraint.** It is derived from
section 8.2 No-New-Foundations: a reader-facing web archive with auth would require an
auth foundation the project does not currently have and Operational Plan section 11
explicitly defers. Light shape keeps E2-light within the existing foundation.

**"Structured metadata" leading interpretation:** a formatted index that exposes per-recap
metadata (season, week, franchise matchup, score range, featured notable moments) alongside
the recap text, enabling navigation by season and week. The exact form is a decision-
readiness adjudication.

**What E2-light is not:**
- Not E3 (Commissioner-facing review/approve UX) -- different audience, different surface.
- Not E1 (Weekly Recap Distribution) -- E1 distributes individual recaps via group text
  as they publish; E2-light archives them for retrospective browsing.
- Not a real-time tracker or live standings board -- retrospective archive only.
- Not a web application with auth -- the light constraint excludes this explicitly.
- Not A1/A2/A3 -- those surfaces archive structured derivations; E2-light archives the
  narrative output itself.

---

## 4. Diagnostic registration (D1-D5)

### D1 -- Substrate-readiness

**Question:** Is the `recap_artifacts` table (and associated provenance) sufficient
substrate for E2-light's v1 browseable archive without new ingestion, tables, or schema?

**Leading hypothesis: High substrate-readiness.** The `recap_artifacts` table holds
generated recap text, verification results, run provenance, and metadata. The archive
directory `archive/weekly_recaps/` already organizes recaps by season and week as
markdown files. E2-light at v1 is a pure consumer of existing outputs.

**D1 probe targets for Step 1:**
- Confirm `recap_artifacts` schema fields available for metadata display (season, week,
  franchise IDs, score range, verification status, approval status).
- Confirm the archive directory structure provides week-by-week organization suitable
  for D2-alpha navigation.
- Identify any metadata field E2-light needs that `recap_artifacts` does not currently
  expose as a structured field (vs. derivable from recap text).
- Confirm whether the `generate_*_archive.py` script pattern (A1/A2/A3) is the right
  implementation template or whether E2-light's generation step is simpler.

**Confidence on leading hypothesis: medium-high.** E1's implementation established the
archive infrastructure; E2-light extends it. The exact schema field inventory requires
direct probe.

### D2 -- Product-shape candidates

**Question:** What sub-shapes constitute E2-light's v1?

**Candidates:**

- **D2-alpha: By-season / by-week navigation.** Top-level index (all seasons) linking
  to per-season indexes (all weeks) linking to individual recap pages. The fundamental
  browseable-archive structure. Expected v1 include.

- **D2-beta: Structured per-recap metadata header.** Each recap page includes a metadata
  block: season, week, franchise matchup, final score, verification status. Turns the
  narrative archive into a structured record. Expected v1 include alongside D2-alpha.

- **D2-gamma: Per-franchise index.** A separate index organized by franchise showing all
  recaps in which that franchise appeared. High artisan-frame fit (members want to find
  their franchise's story across seasons). Step 1 probes implementation cost; v1 include
  if cost is low, v1.1 follow-on if not.

- **D2-delta: Season-summary roll-up.** A generated season capstone entry derived from
  component weekly recaps. Medium implementation cost; deferred to v1.1.

- **D2-epsilon: Full-archive search.** Excluded at light shape -- search infrastructure
  at non-trivial scale is a new foundation.

**Leading hypothesis for v1:** D2-alpha + D2-beta as core; D2-gamma as stretch goal
pending Step 1 implementation-cost probe; D2-delta and D2-epsilon deferred.

**Confidence: medium.** D2-alpha + D2-beta is well-grounded; D2-gamma's v1 inclusion
depends on Step 1 findings.

### D3 -- Data authority

**Leading hypothesis: D3-Alpha, unambiguous.** E2-light presents already-approved recap
text stored in `recap_artifacts`. No commissioner annotation layer at v1. D3-Beta
(commissioner "editor's note" field on selected recaps) is a v1.1 path.

**Confidence: high.**

### D4 -- Distribution mechanism and revision-point

**D4.1 -- Archive format:**

- **Candidate A: Markdown files + generated index.** E2-light extends the existing
  `archive/weekly_recaps/` structure with generated index files at each level. Lowest
  implementation cost; consistent with the existing archive writer.
- **Candidate B: Generated static HTML.** A single-page or multi-page HTML archive
  generated alongside the markdown files. More polished; still No-New-Foundations.
- **Candidate C: Hosted web archive.** Edges toward new-foundation territory; warrants
  No-New-Foundations assessment at Step 1. Not the leading hypothesis.

**Leading hypothesis for D4.1:** Candidate A or B -- Step 1 adjudicates based on
implementation cost and No-New-Foundations confirmation for B.

**D4.2 -- Revision cadence:**

- **D4.2-Alpha: Continuous accumulation.** Each approved recap is added to the archive
  immediately upon approval. Natural for a weekly-accumulating surface. Implementation:
  the recap lifecycle's approval step triggers an archive-update step.
- **D4.2-Beta: Batch at NFL Week 1.** Annual re-generation. Cross-surface consistency
  with A1/A2; but would leave the archive up to ~11 months stale during the active
  season. Poor fit for E2-light's weekly-accumulation nature.

**Leading hypothesis for D4.2:** D4.2-Alpha. E2-light accumulates continuously like E1,
not annually like A1/A2/A3.

**Confidence on D4: medium.** D4.1 candidate depends on No-New-Foundations confirmation;
D4.2-Alpha is well-grounded but lifecycle integration point requires Step 1 confirmation.

### D5 -- Surface Admission Test interaction

**Leading hypothesis: Reading 1.** E2-light at v1 presents one homogeneous content class
(approved weekly recaps). Reading 2 (meta-surface with content-class admission) is
premature -- the other content classes that would make Reading 2 coherent (player
spotlights, season summaries of a distinct structural type) do not yet exist as
substrate outputs.

**SAT predecessor-state under Reading 1:** unchanged. The gating predecessor ("one
content-class admission attempted") remains unmet. This is the same outcome as all four
prior specs under Reading 1.

**D5 side finding:** The SAT predecessor-state may remain perpetually unmet under the
Reading 1 default unless a future surface genuinely admits multiple content classes -- or
unless the SAT's authoring session defines "attempted" more flexibly than the current
predecessor-state language implies. Recorded here as a structural observation; the SAT
authoring session adjudicates.

**Confidence on D5 leading hypothesis: medium-high.** Reading 1 is well-grounded;
D5 side finding is recorded with medium confidence.

---

## 5. Section 9.2 framing question for decision-readiness

The framing question the decision-readiness chain must elect:

> Is E2-light's v1 a structured presentation layer added to the existing archive
> writer, or does it require a distinct generation step with its own script and
> lifecycle integration point?

**Reading 1A (presentation layer add-on):** E2-light adds an index-generation step to
the existing archive writer. The recap text is already at `archive/weekly_recaps/`;
E2-light adds a `README.md` or `index.md` at each hierarchy level. Minimal new code;
highest consistency with the existing pattern. Risk: the existing archive writer's
output may not carry the structured metadata E2-light's D2-beta requires as structured
fields (they may be derivable from recap text but not pre-computed).

**Reading 1B (distinct generation script):** E2-light is produced by a dedicated
`generate_weekly_recap_archive.py` script (analogous to A1/A2/A3 scripts) that reads
`recap_artifacts`, renders structured metadata headers, generates index pages, and writes
to a distinct output path. Slightly more code; cleaner separation; allows E2-light's
output to be versioned independently of the raw archive writer. Matches the established
`generate_*_archive.py` pattern.

**Leading hypothesis:** Reading 1B. The `generate_*_archive.py` pattern is established
and keeps E2-light's surface output cleanly scoped. Step 1 adjudicates.

---

## 6. E1 stabilization assessment

The Roadmap section 2.2 sequencing condition is "post-E1 stabilization."

**E1 operational state at HEAD `f28be4d`:** Track A code shipped at `78a1aff`; first
distribution archived at `2f7d583`; reception capture at `6537ef7` / `e15ddf8`. Recap
lifecycle is mature; verifier running; `recap_artifacts` populated. No production-blocking
bugs open. Post-Wave-1 drift findings (SCORE_VERBATIM, T9-LOSS) are tracked but neither
blocks E1's output quality. The W14 2025 recap was generated and archived as part of the
A2 implementation arc; the archive structure is functional.

**Assessment: stabilization condition met.** E2-light building on E1's output does not
require E1 to be revision-point-ready; it requires E1's output to be trustworthy enough
to archive, which it is.

**Confidence: medium-high.** Anchored on operational lifecycle state and absence of
production-blocking open defects. Step 1 can surface any E1 stability concern that
would revise this assessment.

---

## 7. Anti-drift

1. Does not author the decision-readiness brief.
2. Does not pre-determine the section 9.2 election (Reading 1A vs 1B). Named as
   leading hypothesis; Step 1 adjudicates.
3. Does not pre-commit D2-gamma as a v1 include. Named as stretch goal; Step 1 probes
   implementation cost.
4. Does not advance the SAT predecessor-state. Recorded as a D5 side finding.
5. Does not re-open E3's sequencing. E3 remains admissible and unaffected.
6. Does not commit to a specific archive directory path or file format.
7. Does not bind the template to this selection-prep. Template binds the spec (step 3).

---

## 8. Cluster / sequencing carry-forward

**E-cluster after E2-light:**
- E3 (Commissioner-facing review/approve UX) remains admissible. Roadmap note:
  "Operational judgment whether to spec E3 as a registered Phase 11 surface or to ship
  as Phase B operational tooling." E2-light's selection does not resolve this.

**Cross-cluster:**
- F1 -- admissible contingent on substrate-readiness; unaffected.
- Cluster A -- exhausted; unchanged.
- Cluster B -- not admissible; unchanged.

**SAT predecessor-state:** unaffected (D5 above).

**Roadmap admissible-surface-set after this selection-prep:**
- Shipped: E1, A1, A2, A3.
- In-chain (selection-prep filed): E2-light.
- Admissible, within Cluster E: E3.
- Admissible, contingent on substrate-readiness: F1.

---

## 9. Prior-attempt findings

No prior failed attempt at an E2-light brief. The four-memo chain is clean.

**Confidence: high.**

---

## 10. Confidence labeling

### 10.1 Highest-confidence claims

- E2-light is selection-prep-eligible. All four predecessor conditions confirmed. (section 1)
- D3-Alpha is the unambiguous election. Content is already-approved recap text. (D3)
- Reading 1 is the correct default. Content is homogeneous at v1. (D5)
- No new foundations required at v1. Light-shape constraint met by markdown-plus-index.

### 10.2 Medium-high confidence claims

- D1 substrate-readiness is high. Specific field inventory confirmed at Step 1. (D1)
- D4.2-Alpha (continuous accumulation) is the right revision cadence. (D4)
- E1 stabilization condition is met. (section 6)

### 10.3 Medium-confidence claims

- D2-gamma (per-franchise index) is a stretch goal, not a confirmed v1 include. (D2)
- Reading 1B (distinct generation script) is the right section 9.2 shape. (section 5)
- The D5 SAT side finding (predecessor-state may remain perpetually unmet under Reading 1
  defaults) is a real structural observation; SAT authoring session adjudicates. (D5)

### 10.4 Claims this memo deliberately does not make

- No characterization of the true QB-position record (A2 concern; out of scope).
- No commitment on E3 sequencing timing.
- No pre-determination of archive path or file format.
- No authoring of the decision-readiness brief.
- No advancement of the SAT predecessor-state.

---

## 11. Cross-references

- `bb0f325` -- Reset Memo v1.0
- `ac96447` -- Documentation Map v1.6
- `1cf4142` -- Tier 5 Live Observation Cadence Doctrine v1.0 (filing precedent)
- `5a865a1` -- Phase 11 surface-selection memo (E-cluster admissibility source)
- `a1f4624` -- Phase 11 decision-readiness memo (Reading 1 shape precedent)
- `ba8b58a` -- Phase 11 Surface Roadmap (E2-light section 2.2 / section 4.4)
- `9093a07` -- E1 specification (E2-light substrate source; stabilization condition)
- `cddcfb5` -- A1 specification (chain pattern precedent)
- `ee671da` -- A2 specification (chain pattern precedent)
- `38ddcd2` -- A3 specification (cluster-A exhaustion; E2-light carry-forward source)
- `ce65310` -- A3 initial archive generation (cluster A operationally complete)
- `5291c46` -- Per-surface constitutional-memo template v1.0 (binds downstream spec)
- `acf55ee` -- Template promotion git mv (template now at docs/templates/)
- `f28be4d` -- HEAD at authoring (Map Tier 4 registration patch)
- `PFL_Buddies_Voice_Profile_v1_0.md` section 5 -- artisan-frame anchor
- `SquadVault_Operational_Plan_v1_1.md` section 8 -- Phase B tracks
- `archive/weekly_recaps/` -- existing archive structure (E2-light starting point)

---

**Filing:** `_observations/OBSERVATIONS_2026_05_14_PHASE_11_E2_LIGHT_SELECTION_PREP.md`.
Provisional / observational. No tier. No Map registration. Matches Tier 5 doctrine
precedent at `1cf4142` and predecessor selection-prep filings at `ba44ba4` / `3e9065f` /
`24e63fa`.

**Next step:** Decision-readiness Step 1 -- empirical probes against D1-D5 leading
hypotheses. Primary targets: (a) `recap_artifacts` schema field inventory for metadata
display; (b) `archive/weekly_recaps/` structure for D2-alpha navigation shape;
(c) D2-gamma per-franchise index implementation cost; (d) No-New-Foundations assessment
of D4.1-Candidate-B (static HTML); (e) lifecycle integration point for D4.2-Alpha
continuous accumulation.
