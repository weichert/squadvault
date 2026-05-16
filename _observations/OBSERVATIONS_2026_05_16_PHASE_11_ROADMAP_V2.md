# Phase 11 Surface Roadmap v2
## SquadVault | Phase 11 | 2026-05-16

**Supersedes:** OBSERVATIONS_2026_05_10_PHASE_11_ROADMAP.md (ba8b58a)
**Supersession basis:** Roadmap section 8.6 -- append-only; new dated memo
**Also incorporates:** OBSERVATIONS_2026_05_14_PHASE_11_ROADMAP_SEASONS_COUNT_REVISION.md
**Status:** Active -- revision-point NFL Week 1 (~2026-09-08)
**HEAD at authoring:** 3a35308

Per section 8.6 of v1, the v1 Roadmap text is not silently patched. This memo
supersedes v1 in full. v1 remains as the historical record. This memo is
readable standalone; v1 is the predecessor.

---

## 1. What changed from v1 and why a full v2

Four structural criteria, all true:

1. The section 2.1/2.2 shipped-vs-admissible split is stale. Cluster A
   (A1/A2/A3) is exhausted -- all three surfaces shipped. The admissible set
   is now E3 and F1, not A1/A2/A3. The split needs a structural update.

2. New surfaces have landed since v1: E2-light (spec fa57056, shipped),
   E3 (found already-implemented; Phase B shim 6ae691a), F1 (Rivalry Chronicle;
   substrate-readiness at 96d937b). All need to be inventoried in section 2.

3. Standing-items inventory (section 7.3) needs D50 and D39 entries, plus the
   2021 DRAFT_PICK gap characterization (Finding B confirmed at 3a35308).

4. The per-surface revision anchor-election distinction needs recording: each
   surface elects its own anchor; there is no shared constant.

A supersession-of-reference addendum would be more complex than re-authoring.
The 2026-05-14 seasons-count revision memo (section 7) had deferred this
decision; the accumulation since then resolves it.

---

## 2. Surface inventory

### 2.1 Shipped surfaces

All surfaces below have a committed specification memo and at least one
committed archive. They are no longer admissible candidates -- they are shipped.

E1 -- Weekly Recap Distribution
  Spec: 9093a07. Revision anchor: D4.2-Alpha (NFL W1). v1 scope unchanged.
  Status: Live. The E-track entry point; generates and distributes weekly
  recaps to the league. Revision-point gates Phase 11 Closure Memo (section 6).

A1 -- Hall of Fame and Shame
  Spec: cddcfb5. Archive: 642d6dc ("16 seasons, 2010-2025"). Anchor: D4.2-Alpha.
  Status: Shipped. Scope: 16 seasons (full digital era, 2010-2025).
  Constitutional memo: OBSERVATIONS_2026_05_12_PHASE_11_PER_SURFACE_CONSTITUTIONAL_MEMO_TEMPLATE_V1.md

A2 -- Draft History Vault
  Spec: ee671da. Archive: 9189a7d ("7 seasons, 2018-2025"). Anchor: D4.2-Alpha.
  Status: Shipped. Scope: 7 seasons (auction era 2018-2025, minus 2021 gap).
  Note: Cavallini/Mahomes 2018 anchor revoked (OBSERVATIONS_2026_05_14_PHASE_11_A2_ANCHOR_REVOCATION.md).
  Actual overall record: $76 Barkley (player 13604) by Cavallini in 2019.
  Test rename (test_cavallini_mahomes_2018_qb_anchor_regression) pending.

A3 -- Championship Timeline
  Spec: 38ddcd2. Archive: committed. Anchor: D4.2-Beta (elected; per-surface
  election, not shared constant -- see section 7.2). Status: Shipped.
  Scope: 16 seasons (full digital era, 2010-2025); splits 11 pre-2021
  (3-round bracket) + 5 post-2021 (4-round bracket).

E2-light -- Weekly Recap Archive
  Spec: fa57056. Initial archive: b1ce21e. Anchor: D4.2-Alpha (inherited from E1).
  Status: Shipped. Scope: archive of E1 output; no independent substrate scope.

E3 -- Editorial Review
  Found already-implemented at selection-prep. Phase B shim: 6ae691a.
  No per-surface constitutional memo authored (not needed; already-implemented
  variant does not require the four-memo chain). Status: Shipped (shim form).

### 2.2 Admissible set (post-cluster-A)

Cluster A is exhausted. A1/A2/A3 are all shipped. The admissible set entering
the post-A3 phase is:

F1 -- Rivalry Chronicle
  Substrate-readiness landed: 96d937b and predecessors. Full infrastructure
  committed. Spec: committed (Rivalry_Chronicle_v1_Contract_Card.md).
  Surface Admission Test v1 (provisional, 8e572f9) applies.
  Status: Admissible. Next gate: SAT cross-surface admission (requires F1 G2
  automated distribution as pre-requisite).

  Admissibility screens (section 2.2 of v1, carried forward unchanged):
  - Tone Engine boundary: pass (Rivalry Chronicle uses existing tone substrate)
  - Social-surface-vs-network: pass (not a social network feature)
  - No-New-Foundations: pass (substrate already exists)
  - Certifications: pass (no new certifications required)
  - Section 9.2 fit: pass

No other surfaces are currently in the admissible set. Surfaces not named
above are not admitted and are not candidates for this session or the
immediate roadmap horizon.

---

## 3. Sequencing hypothesis

The cluster-A leading hypothesis from v1 stands in substance: a browseable
digital-era archive demonstrates what SquadVault IS to a first-time observer.
Figure correction only: "17 seasons" (v1 line 101) -> "16 seasons."

Per the seasons-count revision memo (section 5): no single number describes
cluster A. The surfaces render 16 (A1), 7 (A2), and 16 (A3) seasons
respectively, per their distinct substrate scopes. "16 seasons rendered
browseably" refers to the A1/A3 scope; A2's 7-season scope is an accurate
sub-window of the auction era, not an error.

Sequencing axis I (cluster A leading) delivered. Post-A3, sequencing shifts
to Axis II: E-track expansion (E2-light shipped; E3 shim shipped) and F-track
entry (F1 admissible). The sequencing hypothesis is not re-adjudicated here;
it is recorded that cluster A delivered on its hypothesis.

---

## 4. Chain pattern and framework artifacts

### 4.1 Four-memo chain pattern (unchanged from v1)

Each admitted surface produces four memos in sequence:
  (1) Selection-prep -- scope, sub-shapes, readiness probes
  (2) Decision-readiness Step 1 -- data probes, empirical confirmation
  (3) Decision-readiness Step 2 -- framing adjudication
  (4) Specification -- the surface's governing document

E3 (already-implemented) is the only exception: no chain was required because
the surface was found implemented at selection-prep. The shim commit (6ae691a)
stands as the record.

### 4.2 Per-surface revision anchor election

Each surface elects its own revision anchor. There is no shared constant.
Current elections:

  D4.2-Alpha (NFL W1, ~2026-09-08): E1, A1, A2, E2-light
  D4.2-Beta (first game of NFL season): A3
  D4.2-Gamma (auction night): not elected by any current surface; remains
    a candidate for future A2 revision if the founder elects it

This distinction was surfaced as a side-finding in A3 Step 1 (registered in
OBSERVATIONS_2026_05_14_PHASE_11_ROADMAP_SEASONS_COUNT_REVISION.md section 8,
finding 1). It is recorded here for the first time in the Roadmap itself.

### 4.3 Framework artifacts

Template v1.0: promoted to docs/templates/ at acf55ee. Governs all current
and future surface specifications.

Surface Admission Test v1: authored provisional at 8e572f9. Promotes to docs/
at first cross-surface admission (F1 is the candidate). Until promotion,
it is a provisional framework artifact.

Doctrine-to-Product Translation Table: eligible, not yet authored. Recorded
as a standing item in section 7.3.

Pre-commit gate (docs/ Map registration): live at 143e65a. Fires on any new
top-level docs/ file staged for commit; requires Map registration before merge.

Commissioner display overrides table: committed at c9ad04d. Available for
correction of franchise display-name issues. Not wired into any surface v1.

---

## 5. Seasons-count reconciled figures

Authoritative source: OBSERVATIONS_2026_05_14_PHASE_11_ROADMAP_SEASONS_COUNT_REVISION.md.
Figures carried forward:

  Digital era: 16 seasons (2010-2025). Twice independently confirmed (A1 Step
    1 section 4.2; A3 Step 1 section 4.1 D2-alpha).
  A1 scope: 16 seasons (full digital era).
  A2 scope: 7 seasons (auction era 2018-2025, minus 2021 gap).
  A3 scope: 16 seasons (full digital era; 11 + 5 bracket-era split).
  Cross-substrate FAAB window: 4 seasons (2022-2025).

No surface carries "17 seasons." The legacy approximation is fully retired.

---

## 6. Closure certifications (unchanged from v1)

Phase 11 Closure Memo requires six certifications, per section 8.4:

  C1: E1 revision-point delivered (NFL W1 ~2026-09-08)
  C2: All admitted surfaces have committed specifications
  C3: All admitted surfaces have committed archives
  C4: Gate suite clean at closure HEAD
  C5: Documentation Map current at closure HEAD
  C6: No open P0/P1 defects

C2 and C3 are met for all currently shipped surfaces. C1 gates the Closure
Memo; until NFL W1, the memo is not authored. C4, C5, C6 are verified at
closure time.

---

## 7. Anti-drift provisions (carried from v1 section 8)

### 7.1 Scope freeze

Architecture is frozen. No new foundations, no analytics, no optimization,
no engagement loops, no predictive features. Surfaces are presentation layers
over existing substrate; they do not extend the substrate.

### 7.2 Per-surface anchor election (clarification, not new provision)

Revision anchors are per-surface elections. A surface specification records
its elected anchor at authoring time. The Roadmap records the current election
set (section 4.2). Changes to a surface's elected anchor require a spec
amendment, not a Roadmap revision.

### 7.3 Standing items inventory

Items recorded here are open findings or deferred decisions that do not block
any current surface but warrant visibility.

D50 (detect_the_almost): has never fired in production across 16 seasons.
  The min_times=3 threshold produces zero angles in all observed cycles.
  Candidate for calibration revisit or unfit-for-purpose finding at the
  Phase 11 Closure Memo. No action this roadmap horizon.

D39 (detect_championship_history): playoff_appearances dict over-counts
  per-matchup rather than per-season. The over-counting is silent (no
  verifier catches it; no surface currently surfaces the raw count).
  Recorded for visibility. No action until a surface consumes the raw count.

2021 DRAFT_PICK gap: Finding B confirmed at storage layer (3a35308).
  get_transactions ran for 2021 (104 free-agent events prove it); zero auction
  events were stored. Finding A ruled out by founder confirmation (league has
  run auction drafts exclusively for longer than 2021). Finding C ruled out by
  free-agent transaction coverage. Sub-variant open: cannot distinguish whether
  MFL returned auction events under a non-matching type (Sub-B1, low confidence)
  or returned no auction data at all (Sub-B2, medium confidence) without a live
  re-fetch. Recovery path: operational re-fetch task, low priority, no session
  target set.

A2 anchor correction: test_cavallini_mahomes_2018_qb_anchor_regression rename
  pending. The Cavallini/Mahomes 2018 anchor was revoked
  (OBSERVATIONS_2026_05_14_PHASE_11_A2_ANCHOR_REVOCATION.md); player 9988 is
  Antonio Brown, not Mahomes. Actual A2 overall record: $76 Barkley (player
  13604) by Cavallini in 2019. The test still carries the old name; rename
  is low-priority cosmetic work.

Doctrine-to-Product Translation Table: eligible framework artifact, not yet
  authored. Low priority; no surface currently requires it.

Commissioner display overrides table (c9ad04d): live but not wired into any
  surface v1. Available for future surface revisions that surface franchise
  display names.

F1 G2 automated distribution: pre-requisite for SAT cross-surface admission.
  Not yet implemented. Blocks F1 from advancing through the SAT.

### 7.4 Revision-point

This v2 Roadmap's own revision-point is NFL Week 1 (~2026-09-08), matching
D4.2-Alpha. v3 at NFL Week 1 if warranted; otherwise the Closure Memo
supersedes the Roadmap at closure. This v2 supersedes v1 (ba8b58a) and the
seasons-count revision memo
(OBSERVATIONS_2026_05_14_PHASE_11_ROADMAP_SEASONS_COUNT_REVISION.md) as the
single active Roadmap record.

---

Filed: 2026-05-16
Predecessor: OBSERVATIONS_2026_05_10_PHASE_11_ROADMAP.md (ba8b58a)
Also supersedes figures in: OBSERVATIONS_2026_05_14_PHASE_11_ROADMAP_SEASONS_COUNT_REVISION.md
HEAD at authoring: 3a35308
