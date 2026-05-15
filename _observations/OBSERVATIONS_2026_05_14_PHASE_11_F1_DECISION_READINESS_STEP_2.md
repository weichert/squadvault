# Phase 11 F1 (Rivalry Chronicle) -- Decision-Readiness Step 2

**Date:** 2026-05-14
**Status:** Provisional / observational. No tier. Not registered in Documentation Map.
Third memo in the four-memo F1 chain.
**Filing precedent:** Tier 5 Live Observation Cadence Doctrine at `1cf4142`.

**HEAD at authoring:** Step 1 commit (F1 decision-readiness Step 1).

**Predecessors:** Step 1 memo (six findings; this memo's inputs).

**Output:** Six Step 1 findings adjudicated. Five elections settled. Seven spec-session
gaps named. Joint spec-session shape registered.

---

## 1. Step 1 findings carry-forward

| Finding | Content | Step 2 disposition |
|---|---|---|
| F1-1 | Every pair / season: min=1 matchup; D2-alpha confirmed | Inherit |
| F1-2 | All 45 pairs valid; no filtering needed | Inherit |
| F1-3 | No distribution consumer; V1 is manual copy-paste | **Elected: manual at v1** |
| F1-4 | Export fetch-latest has no team-pair filter | **Recorded: acceptable at v1** |
| F1-5 | D3-Alpha confirmed | Inherit |
| F1-6 | Reading 1 confirmed | Inherit |

---

## 2. Election A -- Section 9.2 framing question

**Elected: open-trigger.** Any two of the 10 franchises, any season in the digital era
(2010-2025), may be the subject of a chronicle at commissioner operational judgment.
The spec governs what the chronicle contains; the timing of generation is operational.

The gated-trigger alternative (generate only at registered notable moments) was
considered and rejected: the Contract Card does not require it, and it adds governance
overhead inconsistent with the artisan-frame model (the commissioner decides what the
league remembers, not a structural gate).

---

## 3. Election B -- V1 sub-shape (D2)

**D2-alpha (full-season) as primary; D2-beta (specific window) via existing CLI.**

Full-season scope covers W1 through the final week of the season (W17 or W18 depending
on format). The existing CLI supports `--start-week`/`--end-week`, `--weeks`, and
`--week-range` flags -- D2-beta requires no new code. The spec registers both modes;
the primary mode is full-season at commissioner election.

**D2-gamma (cross-season / multi-season) deferred to v1.1.** Requires multi-season
window infrastructure not yet built. Explicitly named as a known v1.1 follow-on.

---

## 4. Election C -- Distribution model at v1 (D4)

**Elected: manual copy-paste at v1.** The commissioner generates and approves a
chronicle via `./scripts/py scripts/generate_rivalry_chronicle.py ...` and
`rivalry_chronicle_approve_v1.py`, then reads the `rendered_text` from the approved
artifact and distributes via group text manually.

The pre-automated model is correct at v1: it matches how E1 operated before Track A
automated distribution. Automated distribution (`scripts/distribute_rivalry_chronicle.py`
wrapping the export function + group-text send) is a v1.1 item named explicitly.

**Export function fetch-latest limitation (F1-4):** The commissioner generates and
immediately distributes; at v1 cadence there is at most one recently-approved chronicle
at a time. The limitation is acceptable at v1. The spec records it as a known gap for
v1.1.

---

## 5. Election D -- Archive model

F1's archive model differs from A1/A2/A3. There is no single "F1 archive file"
regenerated annually. Each chronicle is a distinct artifact in `recap_artifacts`
(RIVALRY_CHRONICLE_V1 state machine). The filesystem archive at v1 is optional:
the commissioner may maintain a `archive/rivalry_chronicles/` directory by copying
approved `rendered_text` files, but this is not a spec requirement. The spec registers
`recap_artifacts` as the canonical store; filesystem archiving is operational
commissioner practice.

---

## 6. Election E -- "One full cycle" semantics for section 8.4

F1 has no fixed calendar cadence (unlike E1's weekly cadence or A1/A2/A3's annual
cadence). "One full cycle" for promotion eligibility:

**Elected: at least 3 approved and distributed chronicles across at least 2 different
team pairs, within one NFL season elapsed.**

Reasoning: 3 chronicles demonstrates the pipeline operates reliably for multiple
pairs; 2 different pairs demonstrates it is not pair-specific; one NFL season elapsed
provides calendar grounding. This is a lower bar than E1's "one full season of weekly
recaps" but appropriate for an event-driven surface with no fixed cadence.

---

## 7. Spec-session gaps (G1-G7)

| Gap | Description | Expected spec landing |
|---|---|---|
| G1 | v1.1 follow-on: multi-season scope | Section 9 or 11: named explicitly, gated on multi-season window infrastructure. |
| G2 | v1.1 follow-on: automated distribution | Section 5 or 9: named explicitly, analogous to E1's Track A automation. |
| G3 | Export function team-pair filter gap | Section 6 invariant: commissioner verifies correct artifact before distributing at v1. |
| G4 | Archive model declaration | Section 5: recap_artifacts is canonical store; filesystem archive is optional practice. |
| G5 | One full cycle semantics | Section 8.3: 3 approved chronicles / 2 pairs / 1 season elapsed. |
| G6 | Digital era scope declaration | Section 3: chronicles cover the digital era (2010-present); pre-2010 data is incomplete. |
| G7 | 45-pair universe registered | Section 3: all 45 franchise pairs are valid chronicle subjects at v1. |

---

## 8. Joint spec-session shape

The specification session opens with these settled inheritances:
- Reading 1 (single surface; open-trigger; commissioner-elected)
- D3-Alpha (canonical events only; no commissioner annotation at v1)
- D2-alpha + D2-beta (full-season primary; specific-window via existing CLI)
- D4: manual distribution at v1; automated distribution is v1.1
- Archive: recap_artifacts canonical; filesystem archive optional
- One full cycle: 3 chronicles / 2 pairs / 1 season elapsed
- Template v1.0 at `docs/templates/per_surface_constitutional_memo_skeleton_v1.md`
  binds the spec's twelve-section structure

The spec session adjudicates G1-G7, operationalizes sections 3-8, completes section 4
doctrinal compliance trace. Section 11: fourth post-ratification exercise of template
v1.0 (expected: None substantive).

**Implementation complexity:** None -- implementation is complete. The spec is purely
governance documentation for the existing pipeline.

---

## 9. Confidence labeling

### 9.1 Highest-confidence claims

- Open-trigger is correct; gated-trigger rejected. (section 2)
- D2-alpha confirmed; D2-beta via existing CLI. (section 3)
- Manual distribution is appropriate at v1. (section 4)
- recap_artifacts is the canonical store; no single archive file. (section 5)

### 9.2 Medium-high confidence claims

- One full cycle at 3 chronicles / 2 pairs / 1 season is appropriately calibrated.
  The founder may adjust the threshold; 3 is the minimum for meaningful validation.
- Seven spec-session gaps are complete; an eighth may surface during spec authoring.

### 9.3 Claims this memo deliberately does not make

- No pre-authoring of any spec section.
- No prescription of which team pairs to chronicle first.
- No commitment on v1.1 timing.

---

**Filing:** `_observations/OBSERVATIONS_2026_05_14_PHASE_11_F1_DECISION_READINESS_STEP_2.md`.
Provisional / observational. No tier. No Map registration.

**Next step:** Specification session. Five settled inheritances; seven spec-session
gaps named. Opens `docs/templates/per_surface_constitutional_memo_skeleton_v1.md`.
