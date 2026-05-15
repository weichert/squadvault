# Phase 11 F1 (Rivalry Chronicle) -- Decision-Readiness Step 1

**Date:** 2026-05-14
**Status:** Provisional / observational. No tier. Not registered in Documentation Map.
Second memo in the four-memo F1 chain.
**Filing precedent:** Tier 5 Live Observation Cadence Doctrine at `1cf4142`.

**HEAD at authoring:** `4338c96` (F1 selection-prep).

**Predecessors:** `4338c96` (F1 selection-prep; D2 + D4 probe targets named).

**Output:** Two empirical probes executed. D2 (product shape) and D4 (distribution)
leading hypotheses confirmed. Four findings registered for Step 2.

---

## 1. Methodology

Direct database probe against `.local_squadvault.sqlite`; direct source read of
`src/squadvault/core/exports/approved_rivalry_chronicle_export_v1.py`.

---

## 2. Empirical findings

### Finding F1-1 (D2): Every pair faces each other in every season.

Across all 16 digital-era seasons (2010-2025): exactly 45 unique head-to-head pairs
per season (C(10,2) = 45 -- every team faces every other team at least once). Matchups
per pair per season: min=1, max=3 (max=4 in 2021), avg=1.6-1.7. No pair goes an
entire season without facing each other.

**Implication:** Full-season scope (D2-alpha) always produces at least 1 matchup entry
in the facts block. No pair produces an empty chronicle at full-season scope.

**Cross-season richness:** 45 pairs * 16 seasons * 1.65 avg = ~1188 canonical
head-to-head matchup events in the substrate. The top pairs by seasons with data appear
in all 16 seasons (structurally guaranteed).

**D2-alpha confirmed:** Full-season is the right primary scope. D2-beta (specific
window) is available via existing CLI flags for playoff-only or custom windows.

**Confidence: high** (direct DB probe; structural guarantee from 10-team round-robin
schedule).

### Finding F1-2 (D2): No pair selection is needed in the spec.

Since every pair faces every other pair every season, the spec does not need to filter
or rank pairs. The commissioner selects any pair at operational judgment. The surface
admits all 45 pairs at any season in the digital era.

### Finding F1-3 (D4): Export function exists; no distribution consumer.

`src/squadvault/core/exports/approved_rivalry_chronicle_export_v1.py` exists with
`fetch_latest_approved_rivalry_chronicle_v1(db_path)` -- fetches the latest APPROVED
RIVALRY_CHRONICLE_V1 artifact globally (no team-pair filter). The function is
production-quality but fetches the most recent approved chronicle, not a specific pair.

No distribution consumer (`distribute_rivalry_chronicle.py` or equivalent) exists.
The consumers available are recap-specific: `recap_export_approved.py`,
`recap_export_narrative_assemblies_approved.py`, `recap_export_variants_approved.py`.

**D4 conclusion:** V1 distribution is manual. The commissioner: (1) generates and
approves a chronicle via the existing pipeline, (2) reads the `rendered_text` from the
DB or via `fetch_latest_approved_rivalry_chronicle_v1`, (3) pastes to group text. This
is the pre-automated model E1 used before Track A automated distribution. Automated
distribution (`distribute_rivalry_chronicle.py`) is a v1.1 item.

### Finding F1-4 (D4): Export function fetch-latest limitation.

The current `fetch_latest_approved_rivalry_chronicle_v1` fetches the most recently
approved chronicle regardless of team pair. For a commissioner who has approved multiple
chronicles, this may return the wrong one. The spec must address this: either (a) accept
the limitation at v1 (commissioner verifies which artifact they're distributing), or (b)
add team-pair filtering to the export function. Option (a) is sufficient at v1 since
the commissioner generates and immediately distributes.

---

## 3. Six findings for Step 2

| # | Finding | Step 2 disposition |
|---|---|---|
| F1-1 | Every pair faces every pair every season; min=1 matchup; D2-alpha confirmed | Inherit |
| F1-2 | No pair selection filtering needed; all 45 pairs are valid targets | Inherit |
| F1-3 | No distribution consumer; V1 distribution is manual copy-paste | Step 2 elects |
| F1-4 | Export fetch-latest has no team-pair filter; acceptable at v1 | Step 2 records |
| F1-5 | D3-Alpha unambiguous (from selection-prep; confirmed) | Inherit |
| F1-6 | Reading 1 (from selection-prep; confirmed; no SAT advancement) | Inherit |

---

## 4. Confidence labeling

### 4.1 Highest-confidence claims

- Every pair faces every other pair in every season. (F1-1)
- D2-alpha (full-season) confirmed; no empty chronicles at full-season scope. (F1-1)
- No distribution consumer exists at HEAD. (F1-3)

### 4.2 Claims this memo deliberately does not make

- No pre-authoring of the spec.
- No prescription of the "one full cycle" definition for F1.
- No characterization of the DRAFT artifact at week_index 18 in the live DB.

---

**Filing:** `_observations/OBSERVATIONS_2026_05_14_PHASE_11_F1_DECISION_READINESS_STEP_1.md`.
Provisional / observational. No tier. No Map registration.

**Next step:** Decision-readiness Step 2 -- four elections settled from F1-1 through
F1-6.
