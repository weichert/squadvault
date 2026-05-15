# Phase 11 E2-light (Weekly Recap Archive) -- Specification

**Date:** 2026-05-14
**Status:** Provisional / observational. No tier. Not registered in Documentation Map.
Fourth memo in the four-memo E2-light chain (selection-prep -> decision-readiness
Step 1 -> Step 2 -> **specification** -> registration). **Third empirical exercise of
per-surface constitutional-memo template v1.0 at `5291c46`** (A2 spec at `ee671da`
was the first; A3 spec at `38ddcd2` was the second).
**Filing precedent:** Tier 5 Live Observation Cadence Doctrine at `1cf4142`. Matches
predecessor memo filings at `9093a07` / `cddcfb5` / `ee671da` / `38ddcd2`.

**HEAD at authoring:** `db38077` (E2-light decision-readiness Step 2).

**Predecessors (chain order, most-proximate last):**

- `bb0f325` -- Reset Memo v1.0 (doctrinal source)
- `ac96447` -- Documentation Map v1.6 (registry; Tier 0V -- Vision Source)
- `1cf4142` -- Tier 5 Live Observation Cadence Doctrine v1.0 (filing precedent)
- `ba8b58a` -- Phase 11 Surface Roadmap (section 2.2 admissibility; section 4.4
  subsequent-surface conditions)
- `9093a07` -- E1 specification (first registered per-surface constitutional memo;
  export module lineage; `archive/recaps/` origin)
- `cddcfb5` -- A1 specification (cluster-A Reading 1 election; chain pattern precedent)
- `ee671da` -- A2 specification (first post-ratification template exercise; structural
  precedent for this memo)
- `38ddcd2` -- A3 specification (second post-ratification template exercise; anchor-
  election-agnosticism finding precedent)
- `5291c46` -- Per-surface constitutional-memo template v1.0 + skeleton (binds this
  memo's structure; skeleton opened at `docs/templates/`)
- `bdc83e5` -- E2-light selection-prep (D1-D5 diagnostics registered)
- `4df47ac` -- E2-light decision-readiness Step 1 (six empirical findings)
- `db38077` -- E2-light decision-readiness Step 2 (three elections; seven spec gaps)

**Output:** E2-light (Weekly Recap Archive) is registered as the fifth Phase 11 product
surface in the chain's provisional `_observations/` location. The six settled Step 2
inheritances are operationalized against template v1.0's twelve-section structure. The
seven spec-session gaps (G1-G7) are adjudicated across sections 3, 5, 6, and 9. Section
11 records template-v1.0 adaptations (expected: none substantive).

---

## 1. Section 9.2 election

Per Step 2 (`db38077`) joint spec-session shape, founder-confirmed by chain continuation:
E2-light's six settled inheritances are the settled inheritance for this spec.

**Election: Reading 1.** E2-light is specified as a single Phase 11 surface. Its v1
content is structurally homogeneous (one content type: APPROVED weekly recaps). Reading 2
(meta-surface with content-class admission) was considered in D5 and found premature --
the other content types that would make Reading 2 coherent do not yet exist as substrate
outputs. The Reading 1 vs Reading 2 question is not foreclosed for future E-cluster
surfaces; it is simply not the right answer at E2-light's v1 timing.

**Election: D3-Alpha.** E2-light's v1 surfaces substrate-derivable APPROVED recap text
only. No commissioner-curated annotation layer at v1.

**Election: D4.1-B + D4.2-Alpha.** Static HTML archive generated on-demand via
`scripts/generate_weekly_recap_archive.py`. NFL Week 1 nominal anchor for consistency
with A1/A2/A3 cross-surface calendar.

**Confidence on the elections: high** (founder-confirmed inheritance from Step 2 chain).

---

## 2. Section-content verification block

Per E1 spec section 2 / A1-A3 chain carry-forward: doctrinal section-substance is
source-anchored in the predecessor chain. The Reset Memo sections 2.3 / 4.4 / 8.2 /
8.4 / 9.2 / 10.2 substance was source-verified at Roadmap section 6.1 (`bb0f325` direct
read); parent memo section 4 Cluster E doctrinal screen applied that substance to E2-light
by the same logic that anchored it for A1/A2/A3. Selection-prep section 2, Step 1 section
2, Step 2 section 1 all confirmed no fresh section-claim surfaced.

**Carry-forward applies. No re-authoring of section-verification this memo.**

**Confidence on carry-forward: medium-high** (multiple anchors; not first-hand re-read).

---

## 3. Identity and scope

### 3.1 What E2-light is

**E2-light -- Weekly Recap Archive** is a registered Phase 11 product surface presenting
a reader-facing browseable HTML archive of all APPROVED weekly recaps, organized by
season and week, with structured metadata per entry.

The archive is generated on-demand by `scripts/generate_weekly_recap_archive.py` from
the `recap_artifacts` table. It produces self-contained HTML files at
`archive/recaps/index.html` (top-level season index) and
`archive/recaps/{season}/index.html` (per-season recap archive). Both levels use the
existing `season_html_export_v1.py` renderer: dark mode CSS, table of contents, narrative
display, collapsible facts block.

**Coverage at v1 (G2 adjudicated):** 35 APPROVED (season, week_index) pairs across two
seasons: 2024 W1-W17 (17 weeks) and 2025 W1-W18 (18 weeks). 2024 W18 has no APPROVED
row (WITHHELD only) and is absent from the archive by design. The season index for 2024
notes "17 weeks" and does not reference the WITHHELD status of W18 (silence over
speculation; the archive presents what was approved, not what was withheld).

**Top-level index design (G3 adjudicated):** `archive/recaps/index.html` presents a
season list. Each season entry shows: season year, week count (e.g., "17 weeks"), and
the season's date range derived from `window_start` of W1 and `window_end` of the final
week. Each entry links to `archive/recaps/{season}/index.html`.

**Per-recap metadata displayed (G4 adjudicated):** Each week entry in the season HTML
displays: week number, window dates (formatted from `window_start` / `window_end`),
approved by (`approved_by`), approval date (`approved_at`). These are all present as
structured columns in `recap_artifacts` (Step 1 F1 confirmed). The narrative and
collapsible facts block follow the existing `render_season_html()` output.

**Path layout (Step 2 Election B):**

    archive/recaps/
      index.html                   (generated; top-level season index)
      README.md                    (existing; unchanged by generation script)
      2024/
        index.html                 (generated; 17-week 2024 season archive)
        week_07__v27.md            (existing Track A per-week files; untouched)
        ...
      2025/
        index.html                 (generated; 18-week 2025 season archive)
        week_07__v27.md            (existing; untouched)
        ...

### 3.2 What E2-light is not

- Not E1 (Weekly Recap Distribution) -- E1 distributes individual recaps via group text
  at publish time; E2-light archives them for retrospective browsing. E1 and E2-light
  are complementary, not competing: E1 is the push surface, E2-light is the pull surface.
- Not E3 (Commissioner-facing review/approve UX) -- E3 is commissioner-facing; E2-light
  is reader-facing. Different audiences, different surfaces.
- Not A1/A2/A3 -- those surfaces archive structured derivations (hall of fame records,
  draft prices, playoff brackets); E2-light archives the narrative output itself.
- Not a real-time or live tracker -- E2-light is a static retrospective archive.
  It does not update automatically on approval; it is regenerated on demand.
- Not a web application with auth -- no member access management, no multi-tenant
  adjacency (the "light" constraint per Roadmap section 2.2).
- Not a search engine -- D2-epsilon (full-archive search) is deferred; the v1 archive
  is browseable by season and week, not keyword-searchable.

### 3.3 D2-gamma v1.1 follow-on (G7 adjudicated here)

The per-franchise index (D2-gamma) was considered and dropped from v1. Every recap
features all 10 franchises structurally (a 10-team league has 5 matchups per week; all
10 franchise IDs appear in every `canonical_ids_json`). A franchise-ID filter therefore
returns the full archive for every franchise and is not useful. Franchise-level prominence
filtering requires text-level analysis of `rendered_text` to identify the focal
franchise(es) of each week's narrative -- new computational work not in scope at v1
under D3-Alpha.

**D2-gamma is registered as a named v1.1 follow-on item**, gated on text-analysis
infrastructure (a franchise-prominence scorer over `rendered_text`). This is a genuine
product improvement with real artisan-frame value (league members want to find their
franchise's story across seasons); it is deferred, not foreclosed.

---

## 4. Doctrinal compliance (section-by-section trace)

### 4.1 Section 2.3 -- Five core principles

- **Facts immutable and append-only.** E2-light reads `recap_artifacts`; it writes no
  rows. The generation script is read-only against the database. **Pass.**
- **Narratives derived, never fact-creating.** E2-light presents already-approved
  narrative text; it generates no new narrative. The HTML renderer (`render_season_html`)
  formats existing `rendered_text`; it does not alter it. **Pass.**
- **AI assists, humans approve.** The recaps in the archive are all in `state = APPROVED`;
  they went through the human approval step before entering the archive. E2-light's
  generation step has no AI involvement. **Pass.**
- **Silence preferred over speculation.** 2024 W18 WITHHELD: the archive is silent on
  this week (does not display it, does not reference its WITHHELD status). **Pass.**
- **No analytics, optimization, engagement loops, or prediction.** The archive is a
  static read-only HTML file. No engagement tracking, no personalization, no
  recommendation engine. **Pass.**

### 4.2 Section 4.4 -- Tone Engine boundary and social-surface distinction

E2-light does not touch the Tone Engine. It presents existing approved output; it does
not invoke the recap generation pipeline, the EAL, or any creative layer component. The
Tone Engine boundary is not at issue.

E2-light is a browseable archive, not a social network. It has no follower graph, no
comment mechanism, no reaction surface. It is a read-only presentation of approved
historical content. Social-surface-vs-social-network distinction: **pass.**

### 4.3 Section 8.2 -- No-New-Foundations

E2-light introduces no new tables, ingest paths, detector classes, lifecycle states, or
schemas. It is a pure consumer of `recap_artifacts` (existing table) via
`season_html_export_v1.py` and `approved_weekly_recap_export_v1.py` (both existing in
`core/exports/`). The generation script writes HTML files to `archive/recaps/` (existing
directory). No new Python dependencies. No build tooling. No server. **Pass.**

### 4.4 Section 8.4 -- Six Phase 11 Closure Memo certifications

Provisional posture pending source-verified enumeration at the Closure session (per A1
spec section 4.4 precedent). E2-light's registration as the fifth Phase 11 surface
advances the surface-evidence base for Closure Memo certification 1 (at least one Phase
11 surface) and widens the empirical foundation for the other certifications. Certification
posture: consistent with provisional as registered.

### 4.5 Section 9.2 -- Artisan-frame primary success criterion

The artisan-frame fit for E2-light is grounded on the "I had no idea" discovery mode
the Voice Profile section 5 names. A league member who wants to re-read the recap from
a particular week three seasons ago -- the week of a key trade, a playoff run, a historic
blowout -- has no current way to find it except scrolling through group texts. E2-light
makes that moment browseable. The surface serves retrospective engagement with the
league's own story: not passive consumption but active re-discovery.

The artisan-frame fit is medium (not the highest in the Phase 11 set -- A1/A2/A3's
"league remembers" moments are more acutely artisan-frame-shaped), but solidly present
and differentiated. E2-light's fit is "completion of the E-cluster loop": E1 distributes
the story; E2-light makes it retrievable.

### 4.6 Section 10.2 -- Surface choice is the specification session's call

Discharged by this memo's filing. E2-light is specified here as the fifth Phase 11
surface. The selection-prep / decision-readiness chain adjudicated the surface choice;
this memo records and operationalizes it.

---

## 5. Operational shape (Mode B -- specified-shape)

E2-light has not yet shipped operational state at HEAD `db38077`. This section specifies
the operational shape that implementation will produce (Mode B per template section 3.5).

**Generation script (G5 adjudicated):**
`scripts/generate_weekly_recap_archive.py`, invoked via `./scripts/py`. The script:

1. Opens a `DatabaseSession` against the configured DB path.
2. Queries all `recap_artifacts` rows where `state = 'APPROVED'` and
   `artifact_type = 'WEEKLY_RECAP'`, ordered by `season ASC, week_index ASC`.
3. Groups rows by season. For each season:
   a. Calls `extract_shareable_parts(rendered_text)` per week to extract narrative
      and bullet facts.
   b. Builds a `list[WeekRecapData]` for the season.
   c. Calls `render_season_html(week_data, league_name='PFL Buddies', season=season)`.
   d. Writes the HTML to `archive/recaps/{season}/index.html`.
4. Generates and writes `archive/recaps/index.html` (top-level season index) listing
   each season with week count and date range.
5. Prints a summary (seasons processed, weeks archived, output paths).

**2024 W17 two-APPROVED-rows edge case (G1 adjudicated):** The query uses
`ORDER BY version DESC` and deduplicates per (season, week_index) before grouping,
selecting the latest version. Version 24 (approved 2026-04-09) is displayed; version 1
(approved 2026-03-24) is silently excluded. This matches `fetch_latest_approved_weekly_recap()`'s
behavior.

**Idempotency:** Re-running the script overwrites `index.html` files only. Existing
per-week Track A files (`week_NN__vNN.md`, `.json`, `.yaml`) are never written or deleted
by the generation script.

**On-demand invocation pattern:** The commissioner runs the script after approving each
week's recap. At season start (NFL Week 1 nominal anchor, ~2026-09-08), the script is
run to ensure the archive reflects any off-season corrections.

**Reception:** No structured reception mechanism at v1. Reader access is via the local
filesystem or a shared drive. No web hosting, no URL, no auth.

---

## 6. Surface-specific invariants (G6 adjudicated)

**Universal floor (per template section 3.6):**
- Append-only: no writes to `recap_artifacts` or any canonical table.
- No engagement instrumentation: no view counts, no click tracking, no personalization.
- No follower graph or social network features.
- Spec governs live baseline: this memo is the reference for what the implementation
  produces. Changes require a revision-point session or triggered-revision addendum.

**E2-light-specific invariants above the floor:**
- **Read-only generation.** The generation script reads from `recap_artifacts` only;
  it writes HTML files to `archive/recaps/` only. Any code path that writes to the
  database in the generation script is a violation.
- **APPROVED-state-only display.** The archive displays only rows where
  `state = 'APPROVED'`. DRAFT, WITHHELD, and SUPERSEDED rows are never rendered or
  referenced in the archive HTML.
- **Latest-version-only per (season, week_index).** Where multiple APPROVED rows exist
  for the same (season, week_index) -- currently only 2024 W17 -- only the highest
  `version` is displayed. Earlier approved versions are silently excluded.
- **Idempotent generation.** Running the script N times produces the same output as
  running it once. No state accumulates between runs.
- **No modification of existing Track A files.** Files at `archive/recaps/{season}/week_NN__vNN.*`
  are untouched by the generation script.
- **Silence on WITHHELD weeks.** A week with no APPROVED row (e.g., 2024 W18) does not
  appear in the archive and is not annotated as absent. The index simply omits it.

---

## 7. Governance

E2-light's governance follows the pattern established at A1/A2/A3:

- **Approval gate:** Only APPROVED recaps appear in the archive. The human approval step
  (via `recap_week_approve.py`) is the gate; the generation script is downstream of it.
  The archive cannot contain unapproved content by construction.
- **No self-publication:** The commissioner runs the generation script deliberately after
  each approval. The archive does not update automatically.
- **Revision authority:** Changes to the archive's structure, metadata display, or
  generation logic require a revision-point session (section 8) or a triggered-revision
  addendum per section 8.6. Silent changes are prohibited (append-only doctrine).
- **Archive integrity:** The `index.html` files are generated outputs, not canonical
  records. The canonical record is `recap_artifacts`. If an `index.html` file is
  corrupted or deleted, re-running the generation script restores it fully from the
  database.

---

## 8. Revision-point

### 8.1 Primary anchor

**D4.2-Alpha on-demand** -- the generation script is run after each weekly recap
approval during the active season. There is no fixed calendar revision-point for content
accumulation; the archive is always current-as-of-last-run.

### 8.2 Reasoning

E2-light accumulates content continuously during the active NFL season (W1-W18), unlike
A1/A2/A3 whose content updates at a single annual moment. An annual-batch anchor
(D4.2-Beta) would leave the archive up to ~11 months stale during an active season --
a poor fit for a surface whose primary value is "find this week's story after it happens."
D4.2-Alpha (on-demand, run after each approval) is the honest anchor for E2-light's
weekly-accumulation character.

### 8.3 One full cycle semantics

**One full cycle for E2-light = one complete NFL season of weekly approvals and archive
regenerations.** Concretely: W1 through the final approved week (W17 or W18 depending on
playoff structure) approved and archived, with the generation script run at least once
per week post-approval. The 2026 season (starting ~September 2026) is E2-light's first
full cycle under v1 spec.

### 8.4 Promotion criteria

E2-light promotes from `_observations/` to Map registration when: (a) one full cycle
observed (one complete NFL season of weekly generation operations), AND (b) founder
election. Eligible ~January 2027 after the 2026 season completes.

### 8.5 Alternative anchor (not elected)

**D4.2-Beta: batch at NFL Week 1 (~2026-09-08).** Consistent with A1/A2/A3's cross-
surface calendar; simpler operationally (one run per year). Rejected: leaves the archive
up to 11 months stale during the active season; misaligned with E2-light's weekly-
accumulation nature.

**NFL Week 1 is retained as a nominal secondary anchor:** the generation script is run
at season start to incorporate any off-season corrections (re-approvals, version bumps).
This is not the primary operational model but keeps E2-light synchronized with A1/A2/A3's
cross-surface calendar for consistency.

### 8.6 Triggered revision (anchor-independent)

E2-light's spec is revised (via a dated addendum or a new spec session) on any of:
- A structural change to `season_html_export_v1.py` that alters the archive's rendered
  output format.
- A change to `recap_artifacts` schema that adds or removes fields E2-light displays.
- A new content type approved for the archive (e.g., player spotlights, season summaries)
  that would require D2-gamma or a new sub-shape.
- Any finding during operation that the spec did not anticipate.

---

## 9. Cluster / sequencing carry-forward

### 9.1 E-cluster after E2-light

E2-light is the second E-cluster surface (after E1). E3 (Commissioner-facing review/
approve UX) remains admissible per Roadmap section 2.2. Roadmap note: "Operational
judgment whether to spec E3 as a registered Phase 11 surface or to ship as Phase B
operational tooling." E2-light's registration does not resolve this judgment; it carries
forward to the post-E2-light-spec founder election.

### 9.2 Cross-cluster carry-forward

- F1 (Rivalry Chronicle) -- admissible contingent on substrate-readiness; F1 substrate-
  readiness arc (~6-8 sessions) is independent of E2-light. Unaffected.
- Cluster A -- exhausted. Unchanged.
- Cluster B -- not admissible. Unchanged.

### 9.3 Surface Admission Test predecessor-state

Unaffected by E2-light's registration. E2-light under Reading 1 does not trigger content-
class admission. The gating predecessor ("one content-class admission attempted") remains
unmet. The D5 side finding from the selection-prep stands: the SAT predecessor-state may
remain perpetually unmet under the Reading 1 default unless a future surface elects
Reading 2 or the SAT authoring session defines "attempted" more flexibly. SAT authoring
session adjudicates.

### 9.4 Roadmap admissible-surface-set after E2-light

- Shipped: E1, A1, A2, A3, E2-light.
- Admissible, within Cluster E: E3.
- Admissible, contingent on substrate-readiness: F1.

---

## 10. Prior-attempt findings

No prior failed attempt at an E2-light brief. The four-memo chain proceeded cleanly:
selection-prep (`bdc83e5`) -> Step 1 (`4df47ac`) -> Step 2 (`db38077`) -> this spec.

**Confidence on absence-of-findings: high.**

---

## 11. Adaptations from template v1.0

**Adaptations from template v1.0: None substantive.**

E2-light exercises all twelve template sections without structural deviation. Two
observations worth recording as findings (not adaptations):

**Observation 1 -- D4.2-Alpha on-demand is the template's first continuous-cadence
surface.** E1/A1/A2/A3 all had fixed calendar anchors (NFL Week 1 for A1/A2, end-of-
NFL-season for A3, weekly distribution cadence for E1 but with a fixed revision-point).
E2-light's D4.2-Alpha on-demand model (run after each approval, no fixed anchor for
content accumulation) is distinct. The template's section 3.8 cadence-shape conditionality
("a surface with annual or event-driven cadence includes section 8.3; a weekly-cadenced
surface omits it") does not cleanly map onto E2-light's continuous-accumulation model.
E2-light includes section 8.3 (one full cycle semantics) because its cadence is non-
trivial to define. **This is within the template's anticipated variation** (section 8.3
is conditional on cadence shape; E2-light's cadence shape warrants it); it is not a
structural adaptation.

**Observation 2 -- Mode B spec for a surface with minimal implementation cost.** A1/A2/A3
were Mode B specs for surfaces requiring 3-5 sessions of implementation work. E2-light
is Mode B (specified-shape, not yet shipped) but its implementation arc is estimated at
2 commits (~100-150 lines of orchestration calling existing functions). The template's
Mode B classification fits regardless of implementation size; the observation is that
Mode B admits a wide cost range, which the template already anticipates.

Neither observation requires a template structural change. Both are within the template's
designed flexibility. **Template v1.0 promotes on the strength of three clean post-
ratification exercises (A2, A3, E2-light) -- this spec reinforces that finding.**

---

## 12. Confidence labeling

### 12.1 Highest-confidence claims

- **E2-light's substrate is complete and sufficient.** 35 APPROVED rows with all
  required metadata fields; `season_html_export_v1.py` and `approved_weekly_recap_export_v1.py`
  both fully implemented; no new foundations. (sections 3, 5, Step 1 F1/F4)
- **D3-Alpha is unambiguous.** Content is already-approved recap text; no curation
  needed. (section 4.1)
- **No-New-Foundations holds completely.** Both export functions exist; no new tables,
  dependencies, or build tooling. (section 4.3)
- **D2-gamma is correctly dropped at v1.** Franchise-ID filter is structurally vacuous
  in a 10-team league with no byes. (section 3.3, Step 1 F3)
- **Template v1.0 fits E2-light with no substantive structural adaptations** -- third
  clean post-ratification exercise. (section 11)

### 12.2 Medium-high confidence claims

- **D4.2-Alpha on-demand is the right revision model.** E2-light's weekly-accumulation
  nature makes annual-batch wrong; continuous on-demand matches the operational reality.
  (section 8)
- **HTML-only at v1 is correct.** Per-week bundles duplicate existing Track A files;
  no value added. `write_approved_weekly_recap_export_bundle()` is a clean v1.1 path.
  (section 5)
- **The section 11 observations are findings, not adaptations.** D4.2-Alpha's novelty
  and Mode B's cost range are within the template's designed flexibility; they do not
  require a template revision. (section 11)

### 12.3 Medium-confidence claims

- **Reception is via filesystem / shared drive at v1.** No more structured access
  mechanism is warranted at v1 given the light-shape constraint; the founder may elect
  a hosted option (e.g., GitHub Pages) at the revision-point if the operational context
  warrants. This is within the light-shape constraint IF the hosting requires no auth.
- **The seven spec-session gaps (G1-G7) are complete.** An eighth may surface during
  implementation (e.g., how the top-level index handles date ranges when window_start
  is NULL, as in 2024 W17 version 1). The generation script handles this in
  implementation; the spec records the design intent.

### 12.4 Limitations and deliberate silences

- **No characterization of the HTML's exact visual design.** `render_season_html()` owns
  the CSS; this spec does not prescribe it. The existing polished output (dark mode,
  card layout, TOC) is the v1 baseline.
- **No prescription of test coverage structure.** The implementation arc elects; the
  generate_*_archive.py pattern from A1/A2/A3 is the precedent.
- **No commitment on whether GitHub Pages or any other static hosting is used.** The
  spec records "filesystem / shared drive" as the v1 reception mechanism; the founder
  may amend at the revision-point.
- **No prescription of how future seasons beyond 2025 are handled.** The generation
  script reads all APPROVED rows; future seasons accumulate automatically. No design
  change is needed; this is a non-issue recorded here as a deliberate silence.

---

## 13. Cross-references

- `bb0f325` -- Reset Memo v1.0
- `ac96447` -- Documentation Map v1.6
- `1cf4142` -- Tier 5 Live Observation Cadence Doctrine v1.0 (filing precedent)
- `ba8b58a` -- Phase 11 Surface Roadmap (section 2.2 / section 4.4)
- `9093a07` -- E1 specification (export module lineage; archive/recaps/ origin)
- `cddcfb5` -- A1 specification (chain pattern precedent)
- `ee671da` -- A2 specification (first post-ratification template exercise)
- `38ddcd2` -- A3 specification (second post-ratification template exercise)
- `5291c46` -- Per-surface constitutional-memo template v1.0 + skeleton
- `bdc83e5` -- E2-light selection-prep
- `4df47ac` -- E2-light decision-readiness Step 1
- `db38077` -- E2-light decision-readiness Step 2
- `src/squadvault/core/exports/season_html_export_v1.py` -- D4.1-B renderer
- `src/squadvault/core/exports/approved_weekly_recap_export_v1.py` -- available v1.1
- `scripts/generate_hall_of_fame_archive.py` -- implementation pattern precedent
- `PFL_Buddies_Voice_Profile_v1_0.md` section 5 -- artisan-frame anchor
- `SquadVault_Operational_Plan_v1_1.md` section 8 -- Phase B / Track A relationship

---

**Filing:** `_observations/OBSERVATIONS_2026_05_14_PHASE_11_E2_LIGHT_SPECIFICATION.md`.
Provisional / observational. No tier. No Map registration. Matches Tier 5 doctrine
precedent at `1cf4142` and predecessor per-surface constitutional memo filings at
`9093a07` / `cddcfb5` / `ee671da` / `38ddcd2`.

**Next step:** Implementation arc -- `scripts/generate_weekly_recap_archive.py` + tests
+ initial archive generation. Two-commit arc expected (generation script + tests; initial
archive run). Template v1.0 section 8.4 promotion criteria: one full cycle observed +
founder election (~January 2027 after 2026 season completes).
