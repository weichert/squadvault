# Phase 11 E2-light (Weekly Recap Archive) -- Decision-Readiness Step 2

**Date:** 2026-05-14
**Status:** Provisional / observational. No tier. Not registered in Documentation Map.
Third memo in the four-memo E2-light chain.
**Filing precedent:** Tier 5 Live Observation Cadence Doctrine at `1cf4142`. Matches
predecessor memo filings at `d30a6a9` / `3281a37`.

**HEAD at authoring:** `4df47ac` (E2-light decision-readiness Step 1).

**Predecessors (chain order, most-proximate last):**

- `bb0f325` -- Reset Memo v1.0 (doctrinal source)
- `ba8b58a` -- Phase 11 Surface Roadmap (E2-light admissibility section 2.2)
- `9093a07` -- E1 specification (export module lineage)
- `bdc83e5` -- E2-light selection-prep (D1-D5 diagnostics registered)
- `4df47ac` -- E2-light Step 1 (six empirical findings; this memo's inputs)

**Output:** Step 1's six findings are adjudicated. Three open elections from Step 1
section 5 are settled: (a) D2-alpha + D2-beta as v1 sub-shape confirmed with D2-gamma
dropped; (b) archive path layout elected; (c) HTML-only at v1 elected. The joint spec-
session shape is registered. Seven spec-session gaps are named for the spec session.
E2-light's section 8 revision-point structure is framed. This memo is the direct
predecessor for the specification session.

---

## 1. Chain-step framing

Step 1 at `4df47ac` resolved D1 / D3 / D5 definitively and generated six findings.
Three open questions remained for Step 2 framing:
(a) Confirm D2-alpha + D2-beta as v1 sub-shape with D2-gamma dropped.
(b) Elect archive path layout.
(c) Elect HTML-only vs per-week bundles at v1.
Step 2 adjudicates all three. No new empirical probes required.

---

## 2. Step 1 findings carry-forward

All six Step 1 findings carry forward for spec session consumption:

| Finding | Content | Step 2 disposition |
|---|---|---|
| F1 | 35 APPROVED rows; `week_index` not `week`; all metadata fields present | Inherit |
| F2 | 2024 W17 two APPROVED rows (v1 + v24); 2024 W18 WITHHELD only | Spec records; no design change |
| F3 | D2-gamma dropped -- franchise-ID filter is vacuous structurally | Confirmed dropped |
| F4 | `season_html_export_v1.py` + `approved_weekly_recap_export_v1.py` fully implemented | D4.1-B adopted |
| F5 | D4.2-Alpha on-demand; no approval hook; matches A1/A2/A3 manual-run pattern | Inherit |
| F6 | Archive base path is `archive/recaps/`; existing: one week at `archive/recaps/2025/` | Path election below |

---

## 3. Election A -- V1 sub-shape (D2)

**Confirmed: D2-alpha + D2-beta. D2-gamma dropped.**

- **D2-alpha (by-season / by-week navigation):** Season index page linking to per-week
  recap entries. Top-level index linking to all season pages.
- **D2-beta (structured metadata per entry):** Each recap entry in the season HTML
  displays week number, window dates, approved_by, approved_at. The `render_season_html()`
  function already supports this through the `WeekRecapData` dataclass and collapsible
  facts block.
- **D2-gamma (per-franchise index): dropped.** Step 1 Finding 3 confirmed franchise-ID
  filtering returns the full archive for every franchise; text-analysis-based prominence
  is v1.1+ scope. D2-gamma is registered as a named v1.1 follow-on item.
- **D2-delta (season summary) and D2-epsilon (search): deferred** as planned.

---

## 4. Election B -- Archive path layout

**Elected: extend `archive/recaps/` with season index files.**

Target layout:

    archive/recaps/
      index.html                   (top-level index -- all seasons)
      README.md                    (existing; unchanged)
      2024/
        index.html                 (2024 season archive -- 17 approved weeks)
        week_07__v27.md            (existing Track A files; untouched)
        week_07__v27.json
        week_07__v27__reception.yaml
      2025/
        index.html                 (2025 season archive -- 18 approved weeks)
        week_07__v27.md            (existing; untouched)

The generation script adds `index.html` files at the season level and a top-level
`archive/recaps/index.html`. It does not touch existing per-week files. Re-running is
idempotent (overwrites `index.html` only).

**Alternative considered and rejected:** a separate `archive/weekly_recap_archive/`
directory. Rejected -- duplicates APPROVED content already at `archive/recaps/` and
splits the archive into two locations without structural reason.

---

## 5. Election C -- HTML-only vs per-week bundles at v1

**Elected: HTML-only at v1.**

The generation script produces `index.html` files only. It does not call
`write_approved_weekly_recap_export_bundle()` per week. Reasoning: per-week bundle
files (`recap.md`, `recap.json`, `metadata.json`) would largely duplicate content
already present at `archive/recaps/{season}/week_NN__vNN.md` and `.json` from the
existing Track A export format. Two parallel representations with different naming
conventions is noise, not value. The reader-facing deliverable is the season HTML.
`write_approved_weekly_recap_export_bundle()` is available as a v1.1 option.

---

## 6. Revision-point framing (section 8 shape for the spec)

E2-light's revision cadence is distinct from A1/A2/A3's annual model.

**D4.2-Alpha operational model (elected):**
- **Primary trigger:** commissioner runs
  `./scripts/py scripts/generate_weekly_recap_archive.py` after approving each week's
  recap during the active season. Archive is always current when run.
- **NFL Week 1 nominal anchor (~2026-09-08):** generation script is run at season start
  to ensure the archive reflects any off-season corrections (re-approvals, version bumps).
  Keeps E2-light consistent with A1/A2/A3's cross-surface calendar.
- **No formal versioning trigger.** The archive is regenerated to reflect the current
  APPROVED state of `recap_artifacts`; it is not versioned per-generation.

**Section 8.4 promotion criteria:** one full cycle observed (at least one NFL season of
weekly approvals + archive regenerations) + founder election. Eligible after the 2026
season completes (~January 2027).

---

## 7. Spec-session gaps (G1-G7)

Seven gaps for the specification session to adjudicate:

| Gap | Description | Expected spec landing |
|---|---|---|
| G1 | 2024 W17 two-APPROVED-rows edge case | Section 6 invariant: archive displays latest version (v24); earlier version silently excluded. |
| G2 | 2024 W18 WITHHELD-only coverage gap | Section 3: archive covers 35 weeks; W18 2024 absent by design (WITHHELD); noted in index. |
| G3 | Top-level index.html design | Section 3: season list with week count and date range per season. |
| G4 | Season HTML metadata fields displayed | Section 3: week number, window_start/end dates, approved_by, approved_at. |
| G5 | Script name and invocation | Section 5: `scripts/generate_weekly_recap_archive.py` via `./scripts/py`. |
| G6 | Surface-specific invariants beyond floor | Section 6: read-only (no writes to recap_artifacts); idempotent; APPROVED-only display. |
| G7 | D2-gamma v1.1 follow-on registration | Section 9 or 11: named explicitly, gated on text-analysis infrastructure. |

---

## 8. Joint spec-session shape

The specification session opens with these settled inheritances:
- Reading 1 (single surface; not meta-surface)
- D3-Alpha (substrate-derivable; no commissioner curation)
- D4.1-B (static HTML via `season_html_export_v1.py`)
- D4.2-Alpha on-demand (run after each approval; NFL Week 1 nominal anchor)
- Archive path: `archive/recaps/` extension with season `index.html` files
- HTML-only at v1
- Template v1.0 at `docs/templates/per_surface_constitutional_memo_skeleton_v1.md`
  binds the spec's twelve-section structure

The spec session adjudicates G1-G7, operationalizes sections 3-8, completes the section
4 doctrinal compliance trace, and lands section 11 (expected: None substantive --
third post-ratification exercise of template v1.0).

**Implementation complexity:** lower than A1/A2/A3. Both export functions already exist;
generation script is orchestration only (~100-150 lines); no new substrate. Implementation
arc likely two commits (generation script + tests, initial archive generation).

---

## 9. Confidence labeling

### 9.1 Highest-confidence claims

- D2-alpha + D2-beta as v1 sub-shape is correct; D2-gamma structurally not viable.
  (Step 1 F3; section 3)
- HTML-only at v1 is correct. Per-week bundles duplicate existing Track A files.
  (section 5)
- `archive/recaps/` extension is the right path; no namespace conflict. (section 4)
- D4.2-Alpha on-demand with NFL Week 1 nominal anchor is the right revision model.
  (section 6)
- Implementation complexity is lower than A1/A2/A3. (section 8)

### 9.2 Medium-high confidence claims

- The seven spec-session gaps are complete. An eighth may surface during spec authoring
  (e.g., how the index handles future seasons as the archive grows).
- HTML-only election is correct at v1; the founder may elect bundles -- defensible
  alternative, not a wrong answer.

### 9.3 Claims this memo deliberately does not make

- No pre-authoring of any spec section.
- No prescription of the top-level index.html HTML structure.
- No commitment on test coverage shape.

---

## 10. Cross-references

- `bb0f325` -- Reset Memo v1.0
- `1cf4142` -- Tier 5 Live Observation Cadence Doctrine v1.0 (filing precedent)
- `bdc83e5` -- E2-light selection-prep (D1-D5 diagnostics source)
- `4df47ac` -- E2-light Step 1 (six findings; direct predecessor)
- `9093a07` -- E1 specification (export module lineage; archive/recaps/ origin)
- `src/squadvault/core/exports/season_html_export_v1.py` -- D4.1-B implementation
- `src/squadvault/core/exports/approved_weekly_recap_export_v1.py` -- available v1.1
- `docs/templates/per_surface_constitutional_memo_skeleton_v1.md` -- binds the spec
- `scripts/generate_hall_of_fame_archive.py` -- pattern precedent

---

**Filing:** `_observations/OBSERVATIONS_2026_05_14_PHASE_11_E2_LIGHT_DECISION_READINESS_STEP_2.md`.
Provisional / observational. No tier. No Map registration.

**Next step:** Specification session. Six settled inheritances ready; seven spec-session
gaps named. Spec opens `docs/templates/per_surface_constitutional_memo_skeleton_v1.md`
and fills the twelve sections. Expected: clean Reading 1B spec; section 11 records no
substantive template adaptations.
