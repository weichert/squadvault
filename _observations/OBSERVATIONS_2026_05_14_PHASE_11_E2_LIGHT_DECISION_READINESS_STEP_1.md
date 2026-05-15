# Phase 11 E2-light (Weekly Recap Archive) -- Decision-Readiness Step 1

**Date:** 2026-05-14
**Status:** Provisional / observational. No tier. Not registered in Documentation Map.
Second memo in the four-memo E2-light chain.
**Filing precedent:** Tier 5 Live Observation Cadence Doctrine at `1cf4142`. Matches
predecessor memo filings at `5a865a1` / `ba8b58a` / `9093a07` / `2da7f21` / `1e7b59d`.

**HEAD at authoring:** `bdc83e5` (Phase 11 E2-light selection-prep memo).

**Predecessors (chain order, most-proximate last):**

- `bb0f325` -- Reset Memo v1.0 (doctrinal source)
- `ac96447` -- Documentation Map v1.6 (registry)
- `1cf4142` -- Tier 5 Live Observation Cadence Doctrine v1.0 (filing precedent)
- `ba8b58a` -- Phase 11 Surface Roadmap (E2-light admissibility section 2.2)
- `9093a07` -- E1 specification (substrate source; `approved_weekly_recap_export_v1.py`
  and `season_html_export_v1.py` lineage)
- `bdc83e5` -- E2-light selection-prep (five diagnostics registered; this memo's targets)

**Output:** Five empirical probes against D1-D5 leading hypotheses are executed and
reported. D1 substrate-readiness is confirmed high. D2-gamma (per-franchise index) is
revised to dropped-for-v1 (key finding). D3-Alpha is confirmed. D4.1 is resolved: static
HTML is already fully implemented in `core/exports/`; E2-light's generation script calls
existing functions. Section 9.2 framing question is resolved: Reading 1B (distinct
generation script). Six findings are registered for Step 2.

---

## 1. Chain-step framing

Per selection-prep `bdc83e5`, five diagnostic probe targets for Step 1:
(a) `recap_artifacts` schema field inventory for metadata display;
(b) `archive/weekly_recaps/` structure for D2-alpha navigation shape;
(c) D2-gamma per-franchise index implementation cost;
(d) No-New-Foundations assessment of D4.1-Candidate-B (static HTML);
(e) lifecycle integration point for D4.2-Alpha continuous accumulation.

All five are probed empirically this session. Results follow.

---

## 2. Methodology

Direct database reads against `.local_squadvault.sqlite`. Direct source file reads of
`src/squadvault/core/exports/approved_weekly_recap_export_v1.py`,
`src/squadvault/core/exports/season_html_export_v1.py`, and
`src/squadvault/consumers/recap_week_approve.py`. Direct filesystem inspection of
`archive/`. All findings are first-hand; no carry-forward applied to empirical claims.

---

## 3. Empirical findings

### 3.1 D1 -- Substrate-readiness: CONFIRMED HIGH

**Finding D1-alpha: `recap_artifacts` schema is rich and sufficient.**

Columns confirmed: `id`, `league_id`, `season`, `week_index`, `artifact_type`, `version`,
`state`, `selection_fingerprint`, `window_start`, `window_end`, `rendered_text`,
`created_at`, `created_by`, `approved_at`, `approved_by`, `withheld_reason`,
`supersedes_version`. Note: the week column is `week_index`, not `week` (selection-prep
assumed `week`; corrected here).

All fields needed for E2-light's structured metadata display are present as first-class
structured columns: `season`, `week_index`, `approved_at`, `approved_by`, `window_start`,
`window_end`, `state`. No text mining required to produce the archive index.

**Finding D1-beta: 35 APPROVED (season, week_index) pairs available.**

Coverage:
- 2024: W1-W17 all have exactly one APPROVED row (17 weeks). W18 has no APPROVED row
  (WITHHELD only). Exception: W17 has two APPROVED rows (version 1 at '2026-03-24' and
  version 24 at '2026-04-09'). The export function handles this correctly via
  `ORDER BY version DESC LIMIT 1`, fetching version 24.
- 2025: W1-W18 all have exactly one APPROVED row (18 weeks).
- Total: 35 unique (season, week_index) pairs with APPROVED recaps.
- `rendered_text` is populated for all 35 rows (text_len ranges 718-5741 chars).
- `window_start` / `window_end` are populated for all rows except 2024 W17 version 1
  (the earlier approval, which is superseded by version 24 in practice).

**D1 verdict: high substrate-readiness confirmed.** E2-light at v1 is a pure consumer
of existing `recap_artifacts` output. No new ingestion, tables, or schema required.

**Confidence: high** (direct schema and data probe; zero inference).

### 3.2 D2 -- Product-shape: D2-gamma REVISED TO DROPPED

**Finding D2-alpha: archive directory is `archive/recaps/`, not `archive/weekly_recaps/`.**

Selection-prep assumed `archive/weekly_recaps/`; the actual path is `archive/recaps/`.
Current contents: `archive/recaps/README.md` and one week's files at
`archive/recaps/2025/` (`week_07__v27.md`, `week_07__v27.json`,
`week_07__v27__reception.yaml`). The directory structure is season-based, not flat.
E2-light's generation script writes to `archive/recaps/` (extends the existing
structure) or to a new path (e.g., `archive/weekly_recap_archive/`). The spec session
elects the target path; both are within the existing archive layout.

**Finding D2-beta: D2-gamma (per-franchise index) is NOT viable at v1 from structured
fields alone.**

This is the session's most significant revision to the selection-prep's leading
hypotheses. From `canonical_ids_json` in `recap_runs`: every recap window covers all 10
franchises (confirmed across every queried week; S2024 W1-W6 all return
`franchises=['0001','0002',...,'0010']`). This is structural: a 10-team league has 5
matchups per week; every franchise plays every week; every WEEKLY_MATCHUP_RESULT window
thus contains all 10 franchise IDs.

**Consequence:** a franchise filter on `canonical_ids_json` franchise IDs returns the
full archive for every franchise — it is not a useful filter. Franchise-level *prominence*
filtering (which recaps feature franchise X most centrally in the narrative) requires
text-level analysis of `rendered_text` to determine the focal franchise(es) of each
recap's narrative. That is new computational work — not a structured-field query and not
within E2-light's D3-Alpha (no commissioner curation) posture.

**D2-gamma disposition: dropped from v1. Reframed as v1.1+ item requiring text-level
analysis infrastructure.** The selection-prep's "stretch goal" characterization was
optimistic; the empirical finding changes the assessment from "cost-dependent" to
"structurally requires new work not in scope at v1."

**D2 v1 shape confirmed:** D2-alpha (by-season / by-week navigation) + D2-beta
(structured metadata header per recap). D2-delta (season summary) and D2-epsilon
(search) deferred as planned.

**Confidence on D2-gamma revision: high** (structural: every team plays every week in a
10-team league with no byes in the canonical window structure).

### 3.3 D3 -- Data authority: D3-ALPHA CONFIRMED

No finding revises D3-Alpha. All content is from `recap_artifacts.rendered_text` (the
approved recap text) plus structured metadata from the same table. No commissioner
annotation required.

**Confidence: high.**

### 3.4 D4 -- Distribution / generation: MAJOR POSITIVE FINDING

**Finding D4-alpha: `approved_weekly_recap_export_v1.py` is fully implemented.**

`src/squadvault/core/exports/approved_weekly_recap_export_v1.py` exists with:
- `fetch_latest_approved_weekly_recap(db_path, league_id, season, week_index)` -- fetches
  the latest APPROVED WEEKLY_RECAP from `recap_artifacts`, schema-resilient, handles
  evolving column names.
- `write_approved_weekly_recap_export_bundle(artifact, out_dir)` -- writes `recap.md`,
  `recap.json`, and `metadata.json` to an output directory. Already handles window
  metadata, approval provenance, and fingerprint fields.

This is production-quality code already in `core/exports/`. E2-light's generation script
calls this function for per-week bundle output; zero new export logic needed.

**Finding D4-beta: `season_html_export_v1.py` is fully implemented.**

`src/squadvault/core/exports/season_html_export_v1.py` exists with:
- `extract_shareable_parts(rendered_text)` -- extracts narrative and bullet facts from
  `rendered_text` using the SHAREABLE RECAP delimiters.
- `render_season_html(week_data, league_name, season)` -- renders a complete, self-
  contained HTML page with dark mode CSS, table of contents (week links), collapsible
  facts section per week, and footer. No external dependencies; stdlib `html` module only.

The CSS is polished: system font stack, dark mode via `prefers-color-scheme`, card-based
layout, accent color, 680px max-width. This is the archive presentation layer E2-light's
identity describes. It already exists.

**D4.1 resolution: static HTML (Candidate B) is already fully implemented in
`core/exports/`. No-New-Foundations holds completely.** The concern about Candidate B
requiring new work was unfounded; the work is done. E2-light's generation script is
the thin orchestration layer that calls these two existing functions.

**Finding D4-gamma: D4.2-Alpha (continuous accumulation) shape is confirmed but
on-demand, not event-triggered.**

`recap_week_approve.py` calls `approve_latest_weekly_recap()` from the lifecycle. No
archive-generation hook is triggered at approval time. The three existing
`generate_*_archive.py` scripts (A1/A2/A3) are all run manually on demand. E2-light's
script follows the same pattern: run `./scripts/py scripts/generate_weekly_recap_archive.py`
after each approval cycle. This is D4.2-Alpha in behavior (always current when run)
without event-driven wiring. Event-driven wiring (calling the script from within the
approval consumer) is a v1.1 operational improvement, not a v1 requirement.

**Confidence on D4 findings: high** (direct source reads; zero inference).

### 3.5 D5 -- SAT interaction: Reading 1 confirmed

No finding revises the Reading 1 default. D5 side finding from the selection-prep
(SAT predecessor-state may remain perpetually unmet under Reading 1 defaults) stands.
No new empirical data revises it.

**Confidence: high.**

---

## 4. Section 9.2 framing question: RESOLVED

The selection-prep registered the framing question:

> Is E2-light's v1 a structured presentation layer added to the existing archive writer,
> or does it require a distinct generation script?

**Resolution: Reading 1B (distinct generation script), confirmed.**

The generation script `scripts/generate_weekly_recap_archive.py` will:
1. Query all APPROVED recaps from `recap_artifacts` ordered by season and week_index.
2. For each season: call `render_season_html()` with the week's data extracted via
   `extract_shareable_parts()`. Write `archive/recaps/{season}/index.html`.
3. Optionally: call `write_approved_weekly_recap_export_bundle()` for per-week bundles
   alongside the season HTML (or write only the HTML -- spec session elects).
4. Write a top-level `archive/recaps/index.html` linking to each season's page.

Estimated implementation: 100-150 lines. Both export functions already exist; the script
is pure orchestration. This matches the `generate_*_archive.py` pattern exactly.

**No new foundations.** Both export modules (`approved_weekly_recap_export_v1.py` and
`season_html_export_v1.py`) are already in `core/exports/`. The Python stdlib `html`
module is already used. No new dependencies, no build tooling, no server.

---

## 5. Six findings registered for Step 2

**Finding 1 (D1):** `recap_artifacts` schema confirmed; column is `week_index` not
`week`; 35 APPROVED (season, week_index) pairs covering 2024 W1-W17 and 2025 W1-W18;
all metadata fields present as structured columns. **Inherit for Step 2.**

**Finding 2 (D1 edge case):** 2024 W17 has two APPROVED rows (version 1 and version 24).
`fetch_latest_approved_weekly_recap()` handles correctly. 2024 W18 has no APPROVED row
(WITHHELD only). The archive covers 35 weeks, not 36. **Step 2 / spec records the
coverage gap; no design change required.**

**Finding 3 (D2-gamma, key revision):** Per-franchise index dropped from v1. Every recap
features all 10 franchises structurally; franchise-ID-based filtering returns the full
archive for every franchise and is therefore not a useful filter. Franchise-level
prominence requires text analysis -- v1.1+ scope. **Step 2 inherits: v1 is D2-alpha +
D2-beta only; D2-gamma reframed as v1.1+ feature.**

**Finding 4 (D4.1, key positive):** `season_html_export_v1.py` and
`approved_weekly_recap_export_v1.py` are both fully implemented in `core/exports/`.
Static HTML (D4.1-Candidate-B) is already built. E2-light's implementation is a
~100-150 line generation script calling existing functions. **Step 2 inherits:
D4.1-Candidate-B adopted as the v1 output format; No-New-Foundations confirmed.**

**Finding 5 (D4.2):** D4.2-Alpha (continuous accumulation, on-demand) is the correct
shape and matches the A1/A2/A3 manual-run pattern. Event-driven wiring is v1.1.
**Inherit for Step 2.**

**Finding 6 (archive path):** `archive/recaps/` is the correct base path (not
`archive/weekly_recaps/` as the selection-prep assumed). Current contents: one week
at `archive/recaps/2025/`. E2-light's script writes season HTML to
`archive/recaps/{season}/index.html` and a top-level index to `archive/recaps/index.html`.
**Step 2 / spec elects the exact target path layout.**

---

## 6. Confidence labeling

### 6.1 Highest-confidence claims

- **D1 substrate-readiness is high.** 35 APPROVED rows, all metadata present, column
  names confirmed. (section 3.1)
- **D2-gamma is NOT viable at v1 from structured fields.** Every recap features all 10
  franchises; the filter is vacuous. This is structural, not a cost question. (section 3.2)
- **D3-Alpha holds.** All content from existing structured outputs. (section 3.3)
- **`season_html_export_v1.py` and `approved_weekly_recap_export_v1.py` are fully
  implemented.** Direct source read; no new export logic needed for v1. (section 3.4)
- **No-New-Foundations holds for static HTML.** The work is already in `core/exports/`;
  no new dependency, no build tooling, no server. (section 3.4)
- **Section 9.2 resolved: Reading 1B.** Generation script calling existing functions;
  ~100-150 lines; follows established pattern. (section 4)

### 6.2 Medium-high confidence claims

- **D4.2-Alpha on-demand matches A1/A2/A3 operational pattern.** No approval hook exists
  or is needed at v1; manual run after each approval cycle is the right model. (section 3.4)
- **`archive/recaps/{season}/index.html` is the right output path layout.** Extends
  existing `archive/recaps/` structure; spec session may elect a variant. (Finding 6)

### 6.3 Claims this memo deliberately does not make

- No pre-authoring of the generation script. That is implementation arc work.
- No characterization of how `season_html_export_v1.py` handles edge cases (e.g., the
  short W18 2025 recap at 718 chars, or the 2024 W16 recap at 1891 chars). Those are
  implementation-arc concerns; the function exists and handles the format.
- No pre-commitment on whether per-week bundle files (recap.md + recap.json +
  metadata.json) are written alongside the season HTML or only the HTML is produced. Spec
  session elects.
- No stance on the 2024 W17 two-APPROVED-rows edge case beyond noting the export function
  handles it correctly.

---

## 7. Cross-references

- `bb0f325` -- Reset Memo v1.0
- `1cf4142` -- Tier 5 Live Observation Cadence Doctrine v1.0 (filing precedent)
- `bdc83e5` -- E2-light selection-prep (parent; five probe targets source)
- `9093a07` -- E1 specification (export module lineage)
- `src/squadvault/core/exports/approved_weekly_recap_export_v1.py` -- confirmed
  fully implemented (D4 positive finding)
- `src/squadvault/core/exports/season_html_export_v1.py` -- confirmed fully
  implemented (D4 positive finding)
- `src/squadvault/consumers/recap_week_approve.py` -- approval trigger; no archive
  hook present (D4.2-Alpha on-demand shape confirmed)
- `recap_artifacts` -- 35 APPROVED rows; schema confirmed (D1)
- `archive/recaps/` -- correct base path (not `archive/weekly_recaps/`) (Finding 6)
- `scripts/generate_hall_of_fame_archive.py` -- pattern precedent for generation script

---

**Filing:** `_observations/OBSERVATIONS_2026_05_14_PHASE_11_E2_LIGHT_DECISION_READINESS_STEP_1.md`.
Provisional / observational. No tier. No Map registration.

**Next step:** Decision-readiness Step 2 -- framing analysis. Six findings from Step 1
are the inputs. Primary Step 2 questions: (a) confirm D2-alpha + D2-beta as v1 sub-shape
with D2-gamma dropped; (b) elect archive path layout (`archive/recaps/` extension vs new
path); (c) elect whether per-week bundles accompany season HTML or HTML-only at v1;
(d) confirm the joint spec-session shape. Implementation cost is low enough that Step 2
may be brief and the spec session may proceed quickly.
