# Surface Admission Test v1
## SquadVault | Phase 11 Framework Artifact

**Date:** 2026-05-16
**Status:** Provisional / observational. No tier. Not registered in Documentation Map.
Filing: `_observations/OBSERVATIONS_2026_05_16_SURFACE_ADMISSION_TEST_V1.md`.
**Filing precedent:** Tier 5 Live Observation Cadence Doctrine at `1cf4142`. Provisional
`_observations/` filing; promotion to `docs/` after empirical validation at the first
actual cross-surface admission event (see section 8).
**HEAD at authoring:** `951dea0` (A3 bridesmaids era-mapping fix; A3 implementation arc closed).

**Predecessors (chain order, most-proximate last):**

- `bb0f325` -- Reset Memo v1.0 (doctrinal source; section 10.2 names this artifact)
- `ba8b58a` -- Phase 11 Surface Roadmap (section 5.1 defines predecessor-state and purpose)
- `9093a07` -- E1 specification (section 6.6: first registration of the SAT as the
  content-class-expansion mechanism for a registered surface)
- `cddcfb5` -- A1 specification (section 3.4: first within-surface content-class admission
  decisions; the within-vs-cross-surface routing distinction first made explicit)
- `ee671da` -- A2 specification (D5-Gamma election; SAT predecessor-state carry-forward)
- `38ddcd2` -- A3 specification (D5-Gamma election; SAT predecessor-state carry-forward)
- `5291c46` -- Per-surface constitutional-memo template v1.0 (framework artifact precedent)
- `bdc83e5` -- E2-light selection-prep (D5 side finding: predecessor-state may remain
  perpetually unmet under Reading 1; SAT authoring session adjudicates)
- E2-light specification -- section 9.3: D5 side finding carried forward to spec
- F1 specification -- section 9.3: SAT predecessor-state unaffected; carry-forward
- `5291c46` / `OBSERVATIONS_2026_05_14_TEMPLATE_V1_PROMOTION.md` -- template promotion
  (section 7: SAT predecessor-state explicitly not addressed by template promotion)

**Output:** Surface Admission Test v1 -- the framework artifact governing content-class
admission to registered Phase 11 surfaces. The predecessor-state adjudication (section 1),
the content-class taxonomy (section 2), the admission criteria and mechanism (sections 3-4),
the current admission registry (section 5), and the governance (section 6) are authored
here. The cross-surface admission mechanism (section 4.2) is marked provisional pending the
first actual cross-surface admission event.

---

## 1. Predecessor-state adjudication

The Roadmap section 5.1 required two conditions before this authoring session:

**Condition 1 -- two or more registered per-surface constitutional memos.** Met. Six memos
exist at authoring: E1 (`9093a07`), A1 (`cddcfb5`), A2 (`ee671da`), A3 (`38ddcd2`),
E2-light, F1. Condition 1 has been met since A1 landed.

**Condition 2 -- one content-class admission attempted against an existing surface.**
Adjudicated here per the D5 delegation from E2-light selection-prep section 4 / spec
section 9.3: "the SAT authoring session adjudicates."

The Roadmap named two most-plausible examples: (a) admitting `rivalry_chronicle_v1` to E1
after F1 substrate work; (b) admitting an A-cluster artifact class to its own surface.

Example (a) has not occurred. `rivalry_chronicle_v1` has not been admitted to E1.

Example (b) has occurred in each A-cluster spec. A1 section 3.4 explicitly enumerated
"content classes admitted at v1" (Championship Roll; Worst-Season Tracking; Blowouts Hall),
considered additional candidates (D3-Beta annotation; Manager Records;
draft-history-or-trade-history sub-shapes), and routed them to revision-point -- while
explicitly distinguishing within-surface expansion (revision-point) from cross-surface
admission (SAT). A2 and A3 repeated this pattern. Each decision generated real friction:
what belongs in v1 vs revision-point; which candidates are within-surface vs cross-surface;
how the routing distinction is maintained.

Additionally, every spec in the chain (E1, A1, A2, A3, E2-light, F1) explicitly confronted
the content-class admission question (the D5 / Reading 1 election) and actively deferred it
to the SAT. That recurring confrontation is itself a form of friction -- not the friction of
a failed admission, but the friction of repeatedly discovering that the SAT's design is
needed and that the routing question is non-trivial.

**Adjudication verdict:** Condition 2 is met under the D5 flexible reading. The A-cluster
within-surface content-class admission decisions constitute "attempted" for grounding
purposes. The friction they generated -- the within-surface vs cross-surface distinction,
the revision-point vs SAT routing, the D3-Beta and Manager Records deferral decisions --
directly informs sections 3 and 4 of this document.

**Honest limitation:** The friction accumulated is primarily within-surface. The SAT's
cross-surface admission mechanism (section 4.2) is authored from principle rather than
from a prior attempted cross-surface admission. Section 4.2 is therefore marked
provisional: it is the SAT's least-grounded section, and is subject to revision at the
first actual cross-surface admission event, which becomes the empirical validation event
for the SAT's own promotion from `_observations/` to `docs/`.

**Confidence on adjudication: medium-high.** The within-surface friction is real and
documented; the extension to Condition 2 is a judgment call authorized by the D5
delegation; the cross-surface limitation is recorded honestly.

---

## 2. Content-class taxonomy

### 2.1 What a content class is

A **content class** is a structurally distinct artifact-kind that a Phase 11 surface
produces or distributes. Two artifacts are in the same content class if they share
the same production contract (the same derivation path, the same verifier, the same
governance gate) and are structurally substitutable in a surface's distribution channel.
Two artifacts are in different content classes if their production contracts differ in
ways that require separate governance, separate verification, or separate channel
configuration.

Examples:
- `weekly_recap_v1` is one content class: structured markdown produced by the recap
  lifecycle, verified by `recap_verifier_v1.py`, approved via the editorial review gate.
- `rivalry_chronicle_v1` is a different content class: structured output governed by
  `Rivalry_Chronicle_v1_Contract_Card.md`, verified by the chronicle verifier, approved
  by `rivalry_chronicle_approve_v1.py`. Different contract, different verifier, different
  approval mechanism -- different content class.
- Championship Roll, Worst-Season Tracking, and Blowouts Hall (A1's sub-shapes) are
  sub-shapes within one surface, not separate content classes in the cross-surface sense.
  They share A1's production contract (derivation from canonical events, no approval gate,
  git-commit as the approval event) and are structurally homogeneous from the surface's
  governance perspective. A1 section 3.4 called them "content classes admitted at v1"
  in the within-surface sense; from the SAT's cross-surface perspective, they are one
  content class: the A1 archive artifact-kind.

### 2.2 The within-surface vs cross-surface distinction

**Within-surface content-class expansion** (a surface adding a new sub-shape or
extending its scope): governed by the surface's own spec section 8 revision-point
mechanism. Examples: A1 adding Manager Records at its revision-point; A3 admitting the
Bridesmaids almost-leg at its revision-point. Not governed by this document.

**Cross-surface content-class admission** (an existing content class produced by one
surface being admitted to another surface's distribution channel): governed by this
document. Example: admitting `rivalry_chronicle_v1` to E1's distribution alongside
`weekly_recap_v1`. This is the SAT's primary territory.

**Native admission** (a new surface admitting its own content class via its spec):
governed by the per-surface constitutional memo (the four-memo chain). The SAT does
not re-adjudicate a surface's native content class; the spec is the native-admission
record. Examples: F1 admitting `rivalry_chronicle_v1`; E1 admitting `weekly_recap_v1`.

### 2.3 Known content classes

| Content class | Producing surface | Production contract | Verifier |
|---|---|---|---|
| `weekly_recap_v1` | E1 | Recap lifecycle + EAL | `recap_verifier_v1.py` |
| A1 archive artifact | A1 | Derivation from canonical events; git-commit as approval | None (archive; no verifier) |
| A2 archive artifact | A2 | Derivation from canonical events; git-commit as approval | None (archive; no verifier) |
| A3 archive artifact | A3 | Derivation from canonical events; git-commit as approval | None (archive; no verifier) |
| E2-light archive artifact | E2-light | Approved recaps as source; git-backed | None (re-presents E1 output) |
| `rivalry_chronicle_v1` | F1 | Chronicle lifecycle + EAL | Chronicle verifier |

---

## 3. Admission criteria

A content class is eligible for cross-surface admission to a registered surface when
all of the following hold:

**3.1 Doctrinal compliance (Reset Memo section 8.2 No-New-Foundations).** The content
class does not require new infrastructure that the receiving surface cannot support
without a new-foundations build. If the receiving surface's channel or archive
infrastructure requires new foundations to handle the content class, the foundations
build must land separately and upstream -- the SAT is not the mechanism for authorizing
new foundations.

**3.2 Production-contract compatibility.** The content class has a defined production
contract (derivation path, generation script, approval gate, verifier where applicable).
The contract must be complete and tested before admission -- not theoretical. A content
class that does not yet have a verifier or an approval gate is not admission-eligible
until those are in place. The receiving surface's governance must be compatible with the
content class's contract.

**3.3 Silence-over-speculation maintained.** The content class's production contract
must not introduce speculation, prediction, or engagement instrumentation absent from
the receiving surface's existing invariants. The admission must not lower the receiving
surface's verification bar.

**3.4 Channel fit.** If the cross-surface admission involves pushing the content class
through an existing distribution channel (e.g., E1's `group_text_paste_assist`), the
content class must be distributable through that channel without modification. If channel
modification is required, it is a channel-expansion decision under the receiving surface's
spec section 8 revision-point mechanism and is separate from the content-class admission.

**3.5 Founder election.** Cross-surface admission requires explicit founder election.
It is never a default. The election is recorded in a memo or spec section.

---

## 4. Admission mechanism

### 4.1 Native admission (per-surface constitutional memo)

When a new Phase 11 surface is specified, its per-surface constitutional memo is the
native-admission record. The memo's section 3 (operational shape) names the content
classes the surface admits at v1. No additional SAT process is required for native
admission. The SAT does not re-adjudicate native admissions.

The revision-point mechanism (per-surface constitutional memo section 8) governs
within-surface content-class expansion. That mechanism is also outside the SAT's scope.

### 4.2 Cross-surface admission (SAT-governed) [PROVISIONAL]

**This section is provisional.** It is authored from principle (the criteria in section 3
and the doctrinal constraints) rather than from a prior attempted cross-surface admission.
It is subject to revision at the first actual cross-surface admission event, which is also
the SAT's empirical validation event for promotion.

**The admission process:**

1. **Candidate identification.** The founder identifies a content class to admit to a
   receiving surface. The candidate is named explicitly: which content class, to which
   surface, via which channel. No implicit or bundle admissions.

2. **Criteria check (section 3).** Each of the five criteria (3.1 through 3.5) is checked
   against the candidate. The check is documented in a memo or a receiving-surface spec
   section. If any criterion fails, the admission is deferred with a finding. Failed
   criteria are not waived -- they are preconditions.

3. **Receiving surface spec amendment.** If criteria check passes, the receiving surface's
   spec is amended to register the admission: the admitted content class is added to the
   spec's section 3.4 (channels and content classes), the distribution runbook is updated
   as needed, and any per-content-class governance notes are recorded. The amendment is
   either (a) a triggered-revision addendum at the spec's section 8.1 mechanism, or (b)
   rolled into the next scheduled revision-point. The founder elects which.

4. **Admission record.** The admission memo or spec section constitutes the admission
   record. It registers: content class admitted, receiving surface, channel, date, HEAD at
   admission, criteria check results, any per-admission governance constraints.

5. **SAT update (this document).** Section 5 (current admission registry) is updated to
   reflect the new admission. The update may be via an addendum to this document or a
   SAT v2 at the founder's election.

**The canonical pending admission:** `rivalry_chronicle_v1` to E1. When F1's automated
distribution (G2, deferred to v1.1) lands, the natural next question is whether
`rivalry_chronicle_v1` distributes through E1's `group_text_paste_assist` channel
alongside `weekly_recap_v1`, or via a separate distribution event. That admission will
be the first cross-surface admission; it will also be the SAT's empirical validation event.
Section 4.2 is written to anticipate that admission without pre-deciding it.

---

## 5. Current admission registry

### 5.1 Native admissions (per-surface constitutional memos)

| Surface | Content class | Admitted at | Channels |
|---|---|---|---|
| E1 | `weekly_recap_v1` | E1 spec `9093a07` | `group_text_paste_assist` |
| A1 | A1 archive artifact (Championship Roll; Worst-Season Tracking; Blowouts Hall) | A1 spec `cddcfb5` | Archive browse |
| A2 | A2 archive artifact (Most-Expensive History; Bust Hall; Bargain Hall) | A2 spec `ee671da` | Archive browse |
| A3 | A3 archive artifact (Playoff Brackets; Playoff Records; Bridesmaids) | A3 spec `38ddcd2` | Archive browse |
| E2-light | Approved weekly recaps (E1 output re-presented) | E2-light spec | Archive browse |
| F1 | `rivalry_chronicle_v1` | F1 spec | Manual commissioner distribution |

### 5.2 Cross-surface admissions

None to date.

### 5.3 Pending (not yet admission-eligible)

| Content class | Target surface | Blocking condition |
|---|---|---|
| `rivalry_chronicle_v1` | E1 | F1 automated distribution (G2) not yet built; criteria check not yet run |

---

## 6. Governance

**Admission authority:** Founder. No default admissions. No admission-by-precedent
(a prior admission of content class X to surface A does not constitute admission of X
to surface B; each cross-surface admission is independent).

**Admission record:** memo or spec section, as described in section 4.2 step 4.

**SAT amendment authority:** Founder. This document may be amended by addendum (append-
only, dated) or by a versioned SAT v2 at the founder's election. Minor clarifications
(adding an admission to section 5; correcting a factual error) are addenda. Structural
changes (revising section 4.2 after the first cross-surface admission) warrant SAT v2
or a named SAT v1 revision addendum.

**This document does not govern:**
- Within-surface content-class expansion (governed by the receiving surface's section 8
  revision-point mechanism).
- Native admission (governed by the per-surface constitutional memo).
- New surface specification (governed by the four-memo chain and template v1.0).
- Architecture, schema, or substrate changes (governed by existing doctrine).
- Engagement instrumentation, prediction, or analytics (prohibited by doctrine; the SAT
  cannot admit content classes that violate these prohibitions regardless of criteria check).

---

## 7. Confidence labeling

**Highest-confidence claims:**

- Condition 1 (two+ memos) is met. Six memos exist. (section 1)
- The within-surface content-class admission decisions in A1/A2/A3 constitute real
  friction. The within-surface vs cross-surface routing distinction is a genuine design
  question the SAT needed to address, and does address in section 2.2. (section 1)
- The content-class taxonomy in section 2 correctly characterizes the known classes and
  the within-vs-cross-surface distinction as it has emerged in the surface chain. (section 2)
- The criteria in section 3 are grounded in existing doctrine (Reset Memo section 8.2,
  silence-over-speculation, No-New-Foundations, founder-election requirements). (section 3)
- The native-admission mechanism in section 4.1 is grounded in the six existing specs. (section 4.1)
- The current admission registry in section 5 is accurate at `951dea0`. (section 5)

**Medium-high-confidence claims:**

- The adjudication verdict (Condition 2 met under D5 flexible reading) is a judgment call.
  An alternative reading ("condition 2 is strictly unmet; defer until `rivalry_chronicle_v1`
  is attempted to E1") is defensible. The D5 delegation, the six-spec friction record, and
  the structural risk of perpetual deferral collectively support the verdict taken. (section 1)
- The cross-surface admission mechanism in section 4.2 is authored from principle. It will
  require revision after the first actual cross-surface admission. The revision is anticipated
  and the provisional marker is explicit. (section 4.2)

**Claims this document deliberately does not make:**

- No prediction of when `rivalry_chronicle_v1` will be admitted to E1.
- No pre-adjudication of whether `rivalry_chronicle_v1` passes the section 3 criteria
  check for E1 admission. That check runs when the admission is attempted.
- No commitment on SAT v2 timing.
- No amendment of any per-surface constitutional memo.
- No finding on the Doctrine-to-Product Translation Table.

---

## 8. Promotion criteria (SAT v1 to docs/)

This document promotes from `_observations/` to `docs/` when:

1. The first actual cross-surface admission has been completed via the section 4.2
   mechanism (criteria check documented, spec amended, admission registered in section 5).
2. The founder reviews section 4.2 against the friction encountered in that admission
   and either confirms section 4.2 as-authored or revises it.
3. The founder elects promotion.

At promotion, a Map registration addendum registers this document at **Tier 4
(Operational Control & Build Discipline)** -- same tier as the template, same
reasoning: governs process (the admission process), not system behavior.

---

## 9. Cross-references

- `bb0f325` -- Reset Memo v1.0 (section 10.2: SAT named as deferred framework artifact)
- `ba8b58a` -- Phase 11 Surface Roadmap (section 5.1: predecessor-state definition and purpose)
- `9093a07` -- E1 specification (section 6.6: first registration of SAT as content-class-
  expansion mechanism; first admission of `weekly_recap_v1`)
- `cddcfb5` -- A1 specification (section 3.4: first within-surface content-class admission
  decisions; within-vs-cross-surface routing distinction first explicit)
- `ee671da` -- A2 specification (D5-Gamma election; SAT predecessor-state carry-forward)
- `38ddcd2` -- A3 specification (D5-Gamma election; SAT predecessor-state carry-forward)
- E2-light selection-prep -- D5 side finding (predecessor-state may remain perpetually
  unmet under Reading 1; SAT authoring session adjudicates)
- E2-light specification -- section 9.3 (D5 carry-forward to spec)
- F1 specification -- section 9.3 (SAT predecessor-state unaffected)
- `5291c46` / `OBSERVATIONS_2026_05_14_TEMPLATE_V1_PROMOTION.md` -- template promotion
  (section 7: SAT predecessor-state explicitly not addressed)
- `1cf4142` -- Tier 5 Live Observation Cadence Doctrine v1.0 (filing precedent)
- `Rivalry_Chronicle_v1_Contract_Card.md` -- Tier 2 (F1's content class contract)
