# Phase 11 A3 (Championship Timeline) Selection-Prep Memo

**Date:** 2026-05-14
**Status:** Provisional / observational. No tier. Not registered in Documentation Map. First memo in the four-memo chain for the fourth Phase 11 surface specification (selection-prep → decision-readiness → specification → registration).
**Filing precedent:** Tier 5 Live Observation Cadence Doctrine at `1cf4142` — `_observations/` provisional, promoted to `docs/` after empirical validation. Matches predecessor memo filings at `5a865a1` / `a1f4624` / `9093a07` / `ba8b58a` / `ba44ba4` / `cddcfb5` / `5291c46` / `3e9065f` / `ee671da`.

**HEAD at memo-write:** `9189a7d` (A2 initial archive generation; A2 implementation arc complete). The A2 follow-on commits named in memory edit #27 (Cavallini/Mahomes anchor revocation memo; rename of `test_cavallini_mahomes_2018_qb_anchor_regression`) and in the brief's Standing Backlog (script docstring update; template v1.0 promotion) have **not** landed yet. They are independent of this chain and do not block.

**Predecessors:**

- `bb0f325` — Reset Memo v1.0 (doctrinal source; §8.4 source-verified at Roadmap §6.1)
- `ac96447` — Documentation Map v1.6 (registry; Tier 0V — Vision Source)
- `46736a0` — Map v1.6 §4.2 patch (binding-vision cite corrected)
- `1cf4142` — Tier 5 Live Observation Cadence Doctrine v1.0 (filing precedent)
- `5a865a1` — Phase 11 surface-selection memo (parent; Cluster A admissibility source)
- `a1f4624` — Phase 11 decision-readiness memo (Disposition A confirmed; Cluster A carry-forward language)
- `9093a07` — Phase 11 first-surface specification for E1 (chain pattern precedent)
- `ba8b58a` — Phase 11 Surface Roadmap (A3 admissibility carry-forward; §2.2 admissible set; §4.1 four-memo chain pattern; §4.4 subsequent-surface conditions)
- `ba44ba4` — Phase 11 A1 selection-prep memo (structural precedent)
- `fb4f827` / `582c3cf` — A1 decision-readiness Step 1 + Step 2 (chain-step shape precedent)
- `cddcfb5` — Phase 11 A1 specification (Reading 1 election; cluster-A meta-surface question settled at §1; **A3 framing-shift source at §3.3 / §9.1**)
- `eb6042d` / `97c8bf0` / `642d6dc` — A1 implementation arc (A1's championship roll now lives at `archive/hall_of_fame_and_shame/championship_roll.md` — substrate-validation for A3's framing)
- `5291c46` — Per-surface constitutional-memo template v1.0 + skeleton (binds A3's specification at chain step 3; does **not** bind this selection-prep)
- `3e9065f` — Phase 11 A2 selection-prep memo (**direct structural precedent — this memo mirrors its shape**)
- `2da7f21` / `d30a6a9` — A2 decision-readiness Step 1 + Step 2 (chain-step shape precedent within cluster A)
- `ee671da` — Phase 11 A2 specification (second registered per-surface constitutional memo; cluster-A within-cluster sub-question collapses to A3 per §9.1)
- `87ebdad` / `4f9c379` / `9189a7d` — A2 implementation arc (A2 operationally complete; cluster A is now two-thirds shipped)
- `PFL_Buddies_Voice_Profile_v1_0.md` §5 — championship and playoff-bracket language patterns (A3 §9.2 anchor)
- `Platform_and_Writers_Room_Compact_v1_0.md` — niche-generality framing for the D4.2-Beta end-of-NFL-season anchor
- `ARCHITECTURAL_AUDIT_2026_04_16.md` §8 entanglement hotspot #3 — playoff-detection trick characterization (three call sites: `franchise_deep_angles_v1`, `weekly_recap_lifecycle`, `season_context_v1`)
- `Narrative_Angles_v2_Definitive_Scope.md` Dimension 9 — D36–D50 franchise-history detector family
- `src/squadvault/core/recaps/context/franchise_deep_angles_v1.py` — D39 CHAMPIONSHIP_HISTORY (lines 1248–1333), D45 REGULAR_SEASON_VS_PLAYOFF (lines 1339–1401), D50 THE_ALMOST (lines 1407–1468). Structural reads this memo
- `src/squadvault/core/recaps/context/hall_of_fame_aggregations_v1.py` — A1's pure-derivation companion; `compute_championship_roll` (lines 220–317) lifts the playoff-detection trick into a per-season tuple form; structural read this memo
- `archive/hall_of_fame_and_shame/championship_roll.md` (`642d6dc`) — A1's live championship roll; A3 framing-shift substrate

**Output:** Candidate sub-shape enumeration for A3 grounded in (a) the playoff-detection trick's empirical maturity across PFL Buddies' 16-season digital era, (b) the D39 / D45 / D46 / D50 detector family scope, and (c) the A1-A3 absorption finding made concrete against `championship_roll.md`'s actual content. A registered set of diagnostics that gate decision-readiness. A leading hypothesis for which A3 v1 sub-shape combination should ship first under the Reading-1-inherited single-surface posture and the D3-Alpha-inherited substrate-derivability discipline, paired with deferral on diagnostics whose resolution requires Step 1 / Step 2 session work. The decision-readiness session adjudicates. The memo does not author the per-surface constitutional memo, does not re-open A1's Reading 1 / D3-Alpha / D4-elections inheritance (also inherited by A2 at `ee671da` §1), and does not run the diagnostics it names.

---

## 1. What this memo is, and is not

This memo is the **selection-prep** artifact for A3 (Championship Timeline), the remaining admissible Cluster A surface per Roadmap §2.2 and A2 spec §9.1. The chain that produced E1 (`5a865a1` → `a1f4624` → `9093a07`), A1 (`ba44ba4` → `fb4f827` + `582c3cf` → `cddcfb5`), and A2 (`3e9065f` → `2da7f21` + `d30a6a9` → `ee671da`) is being repeated for A3. The four-memo chain shape is registered at Roadmap §4.1; this memo is step 1 of 4.

**What this memo does:**

- Carries forward (without re-authoring) the doctrinal §-content load-bearing on A3 selection.
- Characterizes the **A1-A3 absorption finding**: A1 spec §3.1 included Championship Roll as a v1 sub-shape that has now shipped to `archive/hall_of_fame_and_shame/championship_roll.md` (`642d6dc`). A3's framing post-A1-shipping per A1 spec §9.1 and A2 spec §9.1 is "the full playoff-bracket presentation A1's Championship Roll column did not cover." This memo makes that boundary concrete against A1's actual archive content.
- Enumerates A3's candidate sub-shapes against substrate-coverage as characterized in the Architectural Audit §8 entanglement hotspot #3 (the playoff-detection trick) and a structural read of `franchise_deep_angles_v1.py` D39 / D45 / D46 / D50.
- Records the cluster-A surface-vs-meta-surface question as **closed by A1 Reading 1 inheritance** (not deferred). Same posture as A2 selection-prep §5.
- Identifies the diagnostics whose resolution gates A3's decision-readiness session.
- Lands a leading hypothesis on the within-A3 v1 sub-shape combination, paired with deferral on the four substantive diagnostics that require Step 1 / Step 2 session work.
- Frames the operational-rhythm question for a playoff-bracket-derived browseable-archival surface — same browse-cadenced shape as A1 and A2, with one A3-specific substance-honesty argument at the D4.2 cadence-anchor election (end-of-NFL-season as a Beta candidate).
- Surfaces the **cluster-A exhaustion finding**: after A3 ships, the admissible-set within Cluster A reduces to none. This is registered as carry-forward fact, not founder commitment.

**What this memo does not do** (per Anti-Drift §10 below):

- Author A3's per-surface constitutional memo. That is two sessions downstream (the spec session is the second empirical exercise of template v1.0 at `5291c46`; this selection-prep does not exercise the template).
- Re-author or amend A1's Reading 1 election (`cddcfb5` §1), D3-Alpha election, D4.1-Gamma / D4.2-Alpha election, or D5-Gamma dissolution. These inherit by precedent. A2's spec at `ee671da` §1 re-confirmed the same inheritances; A3 inherits them in turn unless explicit founder direction reopens.
- Run the diagnostics it names. Decision-readiness Step 1 (D1 + D2 empirical) and Step 2 (D3 + D4 framing) are downstream sessions.
- Pre-author E2-light / E3 / F1 selection-prep. Each is its own selection chain when next-eligible.
- Re-derive A3's admissibility from doctrine. Roadmap §2.2 is the admissible-set source; A1 spec §9.1 and A2 spec §9.1 carry A3 forward; this memo consumes all three.
- Author any Roadmap correction. Real findings recorded in §10 for a future Roadmap revision sweep; not selection-prep-session scope.
- Smuggle in any new framework artifacts.
- Pre-decide content commitments for A3 beyond what the candidate-set characterization supports. The §7.1 leading hypothesis is anchor, not forcing.
- Advance, foreclose, or condition on the template v1.0 promotion-eligibility flag raised in A2 spec §12.5 side-finding. Template promotion is its own framework-artifact-promotion session; this memo's chain-step 1 work proceeds against the template-v1.0 snapshot at `5291c46` regardless of whether promotion happens before, alongside, or after this chain's spec session.

The memo's value-add to the chain: a substrate-grounded candidate-set characterization for A3; the A1-A3 absorption finding made concrete against A1's live archive content; a registered diagnostic list for decision-readiness; the D4.2-Beta A3-specific substance-honesty argument surfaced before A3's spec session re-derives it under time pressure; the cluster-A exhaustion finding registered as carry-forward fact for the post-A3 admissible-set framing.

**Confidence on the memo's role:** **High** (the value proposition is candidate-set characterization plus diagnostic registration, not surface specification; chain step 1 of 4).

---

## 2. §-content verification block

The doctrinal sections load-bearing on A3 selection are §4.4, §8.2, §8.4, §9.2, and §10.2 of the Reset Memo. Each was source-verified or substance-verified in the preceding chain — most recently in A2 selection-prep §2, A2 Step 2 framing memo, and A2 spec §2. This memo's posture is full carry-forward:

- **§8.4** — Source-verified at Roadmap §6.1 (direct working-tree read of `_observations/OBSERVATIONS_2026_05_07_RESET_MEMO_V1_0.md`; six certifications enumerated verbatim). **Reference, not re-verification.** A3's posture against the six certifications is addressed structurally at §3 (identity and scope) and §6.1 (D1 substrate-coverage diagnostic); specific certification trace deferred to the per-surface constitutional memo (two sessions downstream).
- **§4.4, §8.2, §9.2, §10.2** — Substance applied to Cluster A in parent memo `5a865a1` §4 doctrinal screen, carried forward in the decision-readiness memo `a1f4624` §3, E1 spec `9093a07` §4, A1 selection-prep `ba44ba4` §2, A1 spec `cddcfb5` §4, A2 selection-prep `3e9065f` §2, and A2 spec `ee671da` §4. **No fresh §-claim emerges in this memo that the predecessor chain has not already source-anchored.** The Cluster A doctrinal screening grid applies to A3 by the same logic that anchored it for A1 and A2: all three sub-candidates passed parent §4 cluster screening on §4.4 / §8.2 / §8.4 (diagnostic) / engine boundary, with high §9.2 artisan-frame fit.

The Roadmap §7.5 source-access procedure (founder runs `git show bb0f325 --name-only` and pastes `_observations/...RESET_MEMO_V1_0.md` content) remains the canonical fallback if a fresh §-claim surfaces during this memo's authoring. **No fresh §-claim has surfaced.** This memo does not request §7.5 access.

**Substance applied to A3, by section:**

| § | Substance | A3 posture |
|---|---|---|
| §4.4 Tone Engine boundary | Surfaces consume the engine; do not modify it. | **Pass.** A3 is a browseable archive with at most light connective prose; no new tone work. The D39 / D45 / D50 detectors already generate playoff-derived angles for weekly-recap context consumption; A3 lifts the same playoff-detection primitives into render-ready archive presentation. No engine modification. |
| §4.4 social-surface vs. social-network | A surface is a presentation layer; a network has follower graphs, engagement loops, recommendation. | **Pass.** A3 is a browseable archive of league playoff history. No follower graph. No engagement loop. No recommendation. League members view; they do not "follow" each other through it. Same boundary as A1 and A2. |
| §8.2 No-New-Foundations | New foundations not admissible at Phase 11. | **Pass.** The playoff-detection trick is empirically validated across PFL Buddies' 16-season digital era (A1 Step 1 §3.1 confirmed; A1's `compute_championship_roll` at `hall_of_fame_aggregations_v1.py:220` operationally derives championships across 2010-2025). A3's sub-shape candidates either lift existing detectors (D39, D45, D50 already cross-season-scoped) or perform computational extensions of single-season-scoped detectors (the bridesmaid runner-up cross-season aggregation is the only candidate sub-shape requiring genuine new-aggregation work, structurally analogous to A1's blowouts-hall extension). All sub-shapes consume existing canonical events (`WEEKLY_MATCHUP_RESULT` only). |
| §8.4 (six certifications) | Source-verified at Roadmap §6.1. | **Mostly satisfiable** per parent §4 diagnostic-read for Cluster A as a whole; specific certification trace deferred to A3's per-surface constitutional memo. **Note:** the playoff-detection trick's empirical maturity (16 seasons of validated playoff-week and championship-week detection) makes A3's §8.4 "one full cycle" claim particularly defensible at the spec session — A3's substrate is the most-empirically-exercised of any Phase 11 surface candidate at the moment of its selection-prep, because A1's shipping has already used the trick at production scale. |
| §9.2 artisan-frame primary success criterion | The test a candidate surface must pass to be elected. | **High.** Anchored on Voice Profile §5 "the league remembers mistakes and brings them back up at the worst possible moment — affectionately." Playoff brackets ARE the canonical "the moment the season turned" content. The bridesmaid pattern (runner-up multiple times) is the playoff analog of A2's "auction bust" pattern — the affectionately-remembered close-but-no-cigar story. THE_ALMOST (one game out of playoffs N times) is the playoff analog of A1's worst-season tracking — the structurally-derivable "shame" dimension. Roadmap §2.2's framing of A3 ("playoff brackets and outcomes across the 17 seasons") is itself Voice-Profile-§5-shaped. **Different §9.2 emphasis than A1 (matchup-derived) and A2 (auction-derived)**: A3 leans on the playoff-derived "the moment that defined the season" pattern. Same league memory; different facet. |
| §10.2 surface choice is the specification session's call | First-surface (and any subsequent-surface) selection is the surface-selection session's adjudication, not pre-determined by doctrine. | **Confirmed.** A3 is the remaining admissible Cluster A surface per A2 spec §9.1; the within-cluster sub-question collapses to A3 only after A2 ships (which it has, at `9189a7d`). The founder elects A3 as the fourth Phase 11 surface at the surface-selection moment that this memo's chain culminates in (the spec session at chain step 3, gated by Roadmap §4.4 subsequent-surface conditions); A3 selection is not foreclosed by this memo. |

**Net:** §-substance load-bearing on A3 selection is anchored on the predecessor chain. No fresh §-verification required.

**Confidence on §-substance:** **Medium-high** for the four non-source-verified sections (anchored on parent memo + chain-trace source-verification of substance through three preceding chains); **high** for §8.4 (Roadmap §6.1 direct read; one cycle of removal expected at spec session).

---

## 3. A3 — identity carry-forward

Per Roadmap §2.2:

> **A3 — Championship Timeline.** Playoff brackets and outcomes across the 17 seasons. Admissible. Within-cluster sub-question.

The Cluster A parent §4 screening (parent `5a865a1` §4) records A3 (and A1, A2) as full-pass on §4.4 / §8.2 / §8.4 (diagnostic) / engine boundary, with **high** §9.2 artisan-frame fit.

### 3.1 The A1-A3 absorption finding (the most consequential framing shift)

A1 spec §3.1 includes "Championship Roll — per-season list of league champions across the 16-season digital window (2010-2025), with championship-week record and PF/PA for the championship matchup" as a v1 sub-shape. A1's selection-prep §9.1, A1 spec §9.1, and A2 spec §9.1 all carry this finding forward identically: **A3's framing post-A1-shipping is "the full playoff-bracket presentation A1's Championship Roll column did not cover."**

The finding is now substantiated against A1's actual archive content. Working-tree read of `archive/hall_of_fame_and_shame/championship_roll.md` at HEAD `9189a7d`:

- **Two tables ship in A1's championship roll v1:**
  1. *Champions by Season*: per-season row showing Champion, Runner-Up, Week, Score (e.g., "2025 | Paradis' Playmakers | Weichert's Warmongers | 18 | 139.40 to 118.65"). Sixteen rows; one per digital-era season.
  2. *Titles by Franchise*: title-count + listed-seasons-won per franchise (e.g., "Paradis' Playmakers | 4 | 2012, 2019, 2020, 2025"; nine franchise rows).

- **A1 absorbed:** the championship matchup itself (week, scores), the champion identity, the runner-up identity, the per-franchise title count, the per-franchise title-season list.

- **A1 did NOT absorb:** preliminary playoff-round matchups (the semifinal pairings); the bracket structure itself (who played whom across the playoff weeks, not just the championship week); manager records cross-tabulated to playoff-vs-regular-season splits; repeat-bracket-meeting patterns (which franchises faced each other in playoffs across multiple seasons); never-made-it-to-the-championship patterns; one-game-out-of-playoffs patterns; cross-season playoff appearance / semifinal appearance counts.

**The A1-A3 boundary post-shipping:**

- **A1's territory (now shipped):** championship-as-bracket-final — the last-week-of-playoffs matchup, the champion identity, the per-franchise title-count aggregation.
- **A3's territory (this surface):** the full bracket structure (preliminary rounds, semifinals, the bracket as a sequential view); cross-season playoff aggregations beyond the championship dimension; playoff-record splits.

The boundary is **substrate-clean** — A1's championship-roll content is fully derivable from `compute_championship_roll` (which extracts only the championship-week matchup per season); A3's bracket-and-aggregation content is derivable from the same playoff-detection trick applied to **all** playoff weeks (not just the championship week). The substrate primitives overlap (both use `_regular_season_matchup_count` to identify playoff weeks; both consume `WEEKLY_MATCHUP_RESULT` events); the *presentation scopes* are disjoint.

A3's identity in this memo is therefore declared at:

> **A3 — Championship Timeline.** A browseable archive of PFL Buddies' digital-era playoff history. The archive surfaces the per-season playoff bracket structure (preliminary rounds + semifinals + the championship cross-link to A1) and cross-season playoff aggregations (appearance counts, splits, runner-up patterns, never-quite-made-it patterns) derived from `WEEKLY_MATCHUP_RESULT` events filtered through the playoff-detection trick. Content is substrate-derivable per the D3-Alpha disposition inherited from A1 (see §6.3 below). The cross-link to A1's championship roll is **referential** (e.g., "see Championship Roll for the championship matchup") — A3 does not re-render championship-roll content.

This scope declaration is the A3 analog of A1 spec §3.1's "16-season digital window" framing and A2 spec §3.1's "auction era 2018-2025" framing. A3's framing copy at the spec session will declare both the temporal scope (16-season digital era; same as A1) and the A1 cross-link explicitly at the header level. The A1 spec §3.6 framing-copy precedent applies.

### 3.2 What A3 is

A3 is the Phase 11 admissible surface that **presents the substrate's playoff-bracket and playoff-aggregation data as a browseable record of league playoff memory across the digital era.** The surface's content is composed of substrate-derived facts (per-playoff-week matchups; cross-season counts of playoff appearances, runner-up appearances, just-missed-playoffs counts; per-franchise regular-season-vs-playoff splits) with at most light connective prose. The narrative footprint is small by comparison with the weekly recap, same as A1 and A2; the cross-link to A1's championship roll keeps A3's render-side concise rather than duplicating A1's table.

The candidate sub-shapes enumerated in Roadmap §2.2 — *"playoff brackets and outcomes"* — are the parent enumeration. This memo expands the enumeration (§4 below) to cover the full plausible set so the decision-readiness session has a complete candidate-space to choose against.

### 3.3 What A3 is not

- A3 is not the substrate. The substrate produces `WEEKLY_MATCHUP_RESULT` events and the `_regular_season_matchup_count` + playoff-detection primitives at `franchise_deep_angles_v1` and `hall_of_fame_aggregations_v1`; A3 consumes them. (Same shape distinction as A1 spec §3.2 and A2 spec §3.2.)
- A3 is not the artisan-frame. §9.2's artisan-frame is the primary success criterion A3 must pass; A3 is what gets specified.
- A3 is not A1. A1 ships the championship matchup per season + title counts; A3 ships the full bracket structure + cross-season playoff aggregations beyond championship-as-final. **The substrate primitives overlap; the presentation scopes are disjoint.** Same posture as A2 spec §3.3's "A2 is not A1" framing, with the additional A3-specific cross-link consideration (A3 references A1 rather than re-rendering).
- A3 is not A2. A2 is auction-derived (`DRAFT_PICK` substrate; D20-D28 detectors; 2018-2025 window); A3 is playoff-bracket-derived (`WEEKLY_MATCHUP_RESULT` substrate filtered to playoff weeks; D39 / D45 / D50 detectors; 16-season digital era window). The substrates are **substantively disjoint**.
- A3 is not the Surface Admission Test. Per A1 Reading 1 inheritance (carried through A2 at `ee671da` §1 and inherited again here at §5 below), A3 ships as a single Phase 11 surface; the Surface Admission Test's predecessor-state (Roadmap §5.1: "two registered per-surface constitutional memos AND one content-class admission attempted") is **partially advanced** by A3's registration (the three-spec count grows; the one-content-class-admission-attempted requirement still gates).

The carry-forward from Roadmap §3 is intact. A3 is the remaining admissible Cluster A surface; the A1-A3 absorption finding refines but does not unseat the admissibility.

**Confidence on A3 identity carry-forward:** **High** for the Roadmap §2.2 admissibility carry-forward (direct quotation); **high** for the A1-A3 boundary substrate-clean characterization (working-tree read of A1's live `championship_roll.md` confirms the boundary content-side); **medium-high** that D1's empirical probe will confirm the bracket-presentation substrate-readiness as the structural-read prior characterizes (the playoff-detection trick has been A1-validated, but cross-season bracket *presentation* has not been render-validated).

---

## 4. Candidate sub-shape enumeration

### 4.1 Method

For each candidate sub-shape, this memo addresses:

- **Substrate-coverage** — what canonical event type(s) the sub-shape consumes; which D36-D50 detector(s) already do the aggregation work the sub-shape would consume; what cross-season scope the detector currently operates over (single-season vs already multi-season; cross-season-detector-already-cross-season vs single-season-detector-needing-cross-season-lift); whether the substrate-readiness prior is "favorable" (existing implementation directly addresses the sub-shape) or "favorable-with-extension" (existing implementation addresses the within-playoff-week pattern but cross-season aggregation needs new code).
- **Overlap with A1 / A2** — where the sub-shape's content could equivalently belong to A1 (championship-roll-absorbed) or A2 (auction-derived). Per §4.3 below, A3 is substantively disjoint from A2; the A1 boundary is the championship-roll-absorbed cross-link characterized at §3.1.
- **Initial product-criteria fit** — light gradient pass against demonstrates-what-SquadVault-IS, Sunday/Monday-night-use, implementation-risk, learning-value, §9.2 artisan-frame fit. This is a gradient read, not a screening test; decision-readiness Step 2 does the actual comparison.

The substrate-coverage characterization is anchored on the Architectural Audit §8 entanglement hotspot #3 (playoff-detection trick) and on the structural reads of `franchise_deep_angles_v1.py` (D39, D45, D46, D50) and `hall_of_fame_aggregations_v1.py` (`compute_championship_roll`) performed for this memo. Per Anti-Drift §10 #7 (silence over speculation on playoff-substrate specifics), the structural reads characterize detector scope and data dependencies; they do **not** run SQL probes against `canonical_events` to confirm playoff-week ingestion completeness — that is Step 1's job.

### 4.2 Sub-shape catalog

#### 4.2.1 Per-season playoff bracket presentation (playoff-detection trick lift to multi-playoff-week scope)

- **Description:** For each season in the digital era, the bracket structure: who played whom across all playoff weeks (semifinal pairings + championship; for seasons with more than two playoff weeks, the preliminary-round matchups as well), scores, advance vs eliminate. Per-season rendering at "Season N playoffs" granularity. **The cross-link to A1's championship roll handles the championship-week row; A3 surfaces the rounds A1 does not** (per §3.1 boundary).
- **Substrate-coverage:** The playoff-detection trick is already implemented and 16-season-empirically-validated. `hall_of_fame_aggregations_v1.compute_championship_roll` (lines 220-317) identifies championship weeks; the same playoff-week detection scaffold (lines 285-296) returns *all* playoff weeks per season — `compute_championship_roll` just narrows to the lowest-matchup-count week. **A3's bracket extraction is a generalization of the existing championship roll computation: same `_regular_season_matchup_count`, same week-counts filter, same anomaly-handler pattern, but emit per-playoff-week tuples rather than narrow to the championship week.** No new substrate; no new event type; pure computational extension. Most-direct lift in the catalog.
- **Substrate readiness:** **High.** Aggregation-primitive lift of an empirically-mature pattern. The "cleanest precedent" Architectural Audit §8 #3 explicitly identifies (the playoff-detection trick has three call sites already across the codebase; A3 becomes a fourth consumer of the same primitive).
- **Overlap with A1 / A2:** **Referential cross-link with A1** for the championship-week row (per §3.1 — A3 does not re-render A1's content; references it). None with A2.
- **Product-criteria gradient:** Demonstrates-what-SquadVault-IS — **highest** (the bracket structure is the literal Roadmap §2.2 framing of A3). Sunday/Monday-night-use — **low-medium** (browse-cadenced; spikes during the active playoff weeks and at end-of-season retrospective moments). Implementation-risk — **lowest in catalog** (aggregation-primitive lift; no D2 backfill dependency beyond what A1 already cleared). Learning-value — **medium-high** (the league experiences playoffs week-by-week; the cross-season bracket-view aggregates that experience into a once-per-season at-a-glance shape the league does not currently see at this resolution). §9.2 artisan-frame fit — **highest in catalog** (the bracket IS the moment-that-defined-the-season; the framing-canvas of Voice Profile §5 playoff narratives).

#### 4.2.2 Cross-season playoff records (D39 cross-season aggregation lift)

- **Description:** All-time leaderboards across the 16-season digital era: most playoff appearances; most semifinal appearances; most championship appearances (per D39 — cross-link to A1's title-count table for the won-championship-appearances dimension); longest playoff-active streak; longest playoff-drought streak. Aggregate cross-era counts of "who's been to the playoffs how often."
- **Substrate-coverage:** D39 (`detect_championship_history`) at `franchise_deep_angles_v1.py:1248` **already operates at cross-season scope** within the playoff-week branch (lines 1268-1298 count `champ_appearances` and `playoff_appearances` per franchise across all `completed_seasons`). The detector's playoff-only-week-rate-limiting (it only fires *during* the current season's playoff weeks for weekly-recap context consumption) is a *consumption-side gate*, not a primitive-side limitation — A3's archive consumer lifts the cross-season aggregation independent of any current-week gate. Streak detection (longest playoff-active / longest playoff-drought) is a small computational extension over the same per-season-playoff-participation matrix D39 already produces internally.
- **Substrate readiness:** **High** for the appearance-count dimension (D39 already does the work); **medium-high** for the streak dimensions (computational extension over D39's internal playoff-participation matrix). No D2 backfill dependency beyond what A1 already cleared.
- **Overlap with A1 / A2:** **Soft cross-link with A1's title-count table** for the won-championship-appearances dimension only (A1 surfaces titles-won; A3's playoff-appearance-count is a strict superset that includes appeared-but-lost). The cleanest co-existence is: A3 surfaces appearance-counts; A1's title-counts remain at A1; A3 cross-links the championship-appearance dimension to A1. None with A2.
- **Product-criteria gradient:** Demonstrates-what-SquadVault-IS — **high** (cross-era playoff records are canonical league-memory content; this is the cross-season aggregation analog of A1's worst-season tracking). Sunday/Monday-night-use — **low**. Implementation-risk — **low** (D39 already cross-season; streak extensions are small). Learning-value — **medium-high** (cross-era appearance-counts may surface patterns the league does not carry at this resolution; "Paradis has been to the championship matchup four times" is at A1 already, but "Paradis has been to the playoffs eleven of sixteen seasons" is new). §9.2 artisan-frame fit — **high** (the playoff-dynasty story and the playoff-drought story are both Voice-Profile-§5-resonant content).

#### 4.2.3 Regular-season vs playoff record splits (D45 cross-season lift, league-wide view)

- **Description:** Per-franchise regular-season W-L vs playoff W-L splits across the 16-season digital era. The "Italian Cavallini went 84-72 in regular-season games but 9-3 in playoff games" pattern (a clutch-postseason story); the inverse "this franchise has won the regular-season-points championship three times but never won a playoff game" pattern (a clutch-collapse story). League-wide cross-tabulation rather than per-franchise individual reporting.
- **Substrate-coverage:** D45 (`detect_regular_season_vs_playoff`) at `franchise_deep_angles_v1.py:1339` **already operates at cross-season scope per franchise** (lines 1362-1376 split all historical matchups into regular-season vs playoff buckets; lines 1381-1399 surface franchises whose split-divergence exceeds 20 percentage points). The detector is per-franchise individual-record-style; A3's lift is to render the league-wide table (every franchise, both columns visible, sortable by either dimension) rather than the divergence-threshold-filtered angle.
- **Substrate readiness:** **High.** Computational presentation-style extension of an already-cross-season-scoped detector. The presentation table is a strict view-side rendering of D45's internal split data.
- **Overlap with A1 / A2:** None substantive. (Soft conceptual overlap with A1's manager-records dimension — deferred from A1 v1 per A1 spec §3.3 — but A3's regular-season-vs-playoff *split* is per-franchise time-allocation rather than per-pair head-to-head.) None with A2.
- **Product-criteria gradient:** Demonstrates-what-SquadVault-IS — **high** (the split tells the affectionately-clutch-or-collapse story canonical to league memory). Sunday/Monday-night-use — **low**. Implementation-risk — **low** (D45 already cross-season; render-side extension only). Learning-value — **medium-high** (per-franchise playoff-clutch / playoff-collapse splits surface patterns the league experiences episode-by-episode but does not aggregate cleanly at this resolution). §9.2 artisan-frame fit — **medium-high** (the split has affectionate-narrative weight; less Voice-Profile-§5-anchored than §4.2.4 below).

#### 4.2.4 Bridesmaids and almosts (cross-season runner-up + D50 cross-season aggregation)

- **Description:** Two playoff-narrative-pattern sub-shapes that co-exist as a single Voice-Profile-§5-anchored content unit:
  - **Championship-runner-up cross-era count.** Franchises that appeared as the championship matchup loser multiple times. The "they made it to the finals four times and lost all four" pattern. Derivable from `compute_championship_roll`'s `runner_up_id` column aggregated across seasons. (Note: this is NOT a lift of D46 THE_BRIDESMAID — D46 is single-week-scoped, surfacing the second-highest-scoring franchise that lost *that week's matchup*; the cross-season championship-runner-up pattern is a genuine new aggregation derivable from the championship-roll primitive, structurally analogous to but distinct from D46.)
  - **One-game-out-of-playoffs cross-era count.** D50 (`detect_the_almost`) at `franchise_deep_angles_v1.py:1407` already operates at cross-season scope (lines 1431-1455 count almost_counts across `completed_seasons`); detector surfaces franchises with `min_times >= 3` finishes-one-game-out. A3's lift renders the cross-era leaderboard for any positive count.
- **Substrate-coverage:** **Mixed.** D50 is already cross-season-scoped; render-side lift only (parallel to §4.2.2 dimension). The championship-runner-up cross-era aggregation is a small new computation over `compute_championship_roll`'s output — structurally trivial (group by `runner_up_id`; count) but new.
- **Substrate readiness:** **Medium-high.** D50 lift is direct; runner-up cross-era count is a small new aggregation primitive. Anti-drift on D46 attribution: per Anti-Drift §10 #5 below, *D46 is weekly-scoped*; the brief's framing in §4.2.4 mentioned "Repeated runner-up patterns (D46 THE_BRIDESMAID)" but D46 does not actually implement that pattern; the cross-season championship-runner-up aggregation is a NEW computation, not a D46 lift. This is recorded as a brief-finding in §10.2 below.
- **Overlap with A1 / A2:** **Cross-link with A1 for the runner-up dimension** — A1's `championship_roll.md` "Champions by Season" table already lists Runner-Up per season. A3's cross-era runner-up *count* is a strict aggregation of A1's per-season runner-up column; the substrate primitive (`compute_championship_roll`) is shared between A1's table and A3's aggregation. **Substrate-clean (same primitive; different presentation aggregations).** None with A2.
- **Product-criteria gradient:** Demonstrates-what-SquadVault-IS — **highest** (the "you were SO close" pattern is canonical Voice-Profile-§5 content; the affectionately-remembered postseason heartbreak). Sunday/Monday-night-use — **low**. Implementation-risk — **medium** (one small new aggregation primitive; D50 lift direct). Learning-value — **high** (multi-time-bridesmaid and multi-time-just-missed patterns are league-memory content the league experiences season-by-season but does not aggregate at this resolution). §9.2 artisan-frame fit — **highest in catalog** (this IS the affectionately-remembered postseason-mistakes pattern; the A3 analog of A2's auction-bust hall).

#### 4.2.5 Repeat-bracket-meeting patterns (playoff-only meeting aggregation)

- **Description:** Which franchises have faced each other in playoffs repeatedly across the digital era. Cross-tabulated playoff-only meetings (e.g., "Paradis and Weichert have met in the playoffs five times; Paradis leads 3-2"). Per-pair cross-era playoff-only record.
- **Substrate-coverage:** No existing playoff-only meeting detector exists at the franchise_deep_angles layer. The RIVALRY primordial detector (referenced but not deep-read this memo per Anti-Drift §10 #7) operates on all-time matchups; the playoff-only subset is a filtering extension. The playoff-week filter is the same primitive used in §4.2.1 / §4.2.2 / §4.2.3 / §4.2.4 — `_regular_season_matchup_count` + per-week matchup-count comparison.
- **Substrate readiness:** **Medium.** New aggregation; new render shape. Cross-references RIVALRY detector family but scoped to playoff substrate only. The playoff-filter is shared infrastructure; the per-pair aggregation is new at the A3 archive layer.
- **Overlap with A1 / A2:** **Cross-link consideration with the RIVALRY detector family.** F1 (Rivalry Chronicle) is admissible-contingent-on-substrate-readiness per Roadmap §2.3 / §4.5; F1's substrate-readiness arc is independent of A3 per §9.3 below. If F1 ships post-A3, F1 may absorb or extend §4.2.5's playoff-only meeting content — a future-cross-surface coordination consideration, not a current-blocker. **A1 has no analog**; A2 has no analog.
- **Product-criteria gradient:** Demonstrates-what-SquadVault-IS — **medium-high** (per-pair playoff-meeting records are canonical league-memory content). Sunday/Monday-night-use — **low-medium**. Implementation-risk — **medium-high** (new aggregation; new render shape; the cross-tab requires N*(N-1)/2 pair handling). Learning-value — **medium** (the league knows the famous pairs; the long-tail of less-frequent pairs is the discovery dimension). §9.2 artisan-frame fit — **medium-high** (repeat-pairing rivalry-pattern; less Voice-Profile-§5-resonant than §4.2.4).

#### 4.2.6 Title-game opponent records and championship-closeness (subset of §4.2.2 / §4.2.4 framed differently)

- **Description:** Who appears in championships; who wins them; the closeness dimension (margin in championship matchups). Substantially a re-framing of §4.2.2 (cross-season-records) + §4.2.4 (bridesmaid count) restricted to the championship-week subset, with the margin dimension added.
- **Substrate-coverage:** The championship-margin dimension is derivable from `compute_championship_roll`'s `champion_score` and `runner_up_score` columns; new render dimension over existing primitive output. The opponent-count dimension is captured by §4.2.2 (championship-appearance count) and §4.2.4 (runner-up count).
- **Substrate readiness:** **High** (no new substrate; new render dimension on existing primitive).
- **Overlap with A1 / A2:** **Substantial overlap with A1's championship-roll table** — A1's *Champions by Season* table already shows champion-score and runner-up-score per championship matchup. The closeness-distribution view (which championships were blowouts vs nail-biters) is a strict re-aggregation of A1's per-row score data. **§4.2.6 is materially absorbed by A1.** Recording for the decision-readiness session.
- **Product-criteria gradient:** Demonstrates-what-SquadVault-IS — **medium** (the content is largely accessible from A1's table already; A3 would re-frame rather than add). Sunday/Monday-night-use — **low**. Implementation-risk — **low** (re-rendering primitive). Learning-value — **low-medium** (the league experiences championship closeness episodically; the cross-era closeness ranking is a small addition). §9.2 artisan-frame fit — **medium**.
- **Adjudication for decision-readiness:** §4.2.6 is **the weakest standalone candidate in the catalog** because A1's championship-roll table already exposes the substrate per-season; §4.2.6's incremental value over A1's table is a closeness-ranking re-aggregation. The cleanest disposition is: §4.2.6's closeness-margin dimension folds into §4.2.2 (cross-season records) as a sub-leaderboard ("closest championships ever" + "blowout championships ever"), if the founder wants the closeness dimension at v1; otherwise §4.2.6 defers to a future revision-point.

### 4.3 Cluster overlap summary

A3's candidate set is **substantively disjoint from A2** (auction-derived) and has a **substrate-clean shared-primitive cross-link with A1** (championship-roll-absorbed dimensions):

| A3 candidate sub-shape | Overlap with A1 (Hall of Fame & Shame) | Overlap with A2 (Draft History Vault) |
|---|---|---|
| Per-season playoff bracket presentation (§4.2.1) | Referential cross-link for championship-week row (A1 owns; A3 references) | None |
| Cross-season playoff records (§4.2.2) | Soft cross-link for championship-appearance dimension (A1 owns won-counts; A3 owns appearance-counts) | None |
| Regular-season vs playoff record splits (§4.2.3) | None substantive | None |
| Bridesmaids and almosts (§4.2.4) | Substrate-shared (runner-up dimension derived from A1's same primitive); presentation-disjoint | None |
| Repeat-bracket-meeting patterns (§4.2.5) | None | None (cross-link consideration with F1 if F1 ships post-A3) |
| Title-game records and closeness (§4.2.6) | **Substantial — largely absorbed by A1's table** | None |

**Net:** A3's substrate is playoff-derived; A1's is matchup-derived (championship-week subset shared at substrate level); A2's is auction-derived. The three are substantively disjoint at the presentation level. **The A1-A3 boundary is shared-substrate-different-presentation — substrate-clean, presentation-disjoint via the cross-link discipline characterized at §3.1.** This is materially different from A2's pure-disjoint substrate boundary with both A1 and A3; A3 introduces the cluster's first shared-primitive boundary case, which the spec session formalizes at the cross-link rendering convention.

**Confidence on the sub-shape catalog:** **High** for the already-cross-season-scoped sub-shapes (4.2.1 lift; 4.2.2 D39 dimension; 4.2.3 D45 dimension; 4.2.4 D50 dimension); **medium-high** for the new-aggregation sub-shapes (4.2.4 runner-up count; 4.2.5 playoff-only meetings) pending D1 confirmation that the cross-season aggregations are computational extensions rather than architectural new-foundations; **medium** for §4.2.6 (largely-A1-absorbed; weak standalone).

---

## 5. Surface-vs-meta-surface question — carry-forward by A1 Reading 1 inheritance (CLOSED, not deferred)

Per A1 spec §1 (`cddcfb5`) Reading 1 election and A2 spec §1 inheritance confirmation (`ee671da`): **cluster-A is specified as single-surface-per-spec, with A3 carrying forward as admissible-sequenced-behind-A2.** Per A1 selection-prep §10 anti-drift #3, A2 selection-prep §5, A2 spec §1, and the brief's Anti-Drift §3 binding against re-litigation: **the cluster-A surface-vs-meta-surface question is closed by precedent for cluster A.** A3 ships as a single Phase 11 surface.

The reasoning that closed the question for A1 and was re-confirmed for A2 applies symmetrically to A3 by inheritance: E1's structural precedent toward minimalism (Reading 1); the Surface Admission Test predecessor-state hazard under Reading 2 (Roadmap §5.1 chicken-and-egg); the framing-coherence argument for Reading 1 ("the digital archive" naming for A1, "the auction era archive" for A2). A3's equivalent framing — "the playoff archive of the digital era" — works under Reading 1 for the same structural reasons; the A1 cross-link discipline (§3.1) operates within Reading 1 because cross-linking between surfaces is presentation-layer coordination, not surface-vs-meta-surface conflation.

**If a genuine reason to reopen surfaces during this memo's authoring, it surfaces as a side finding in §10 — not as a re-litigation.** No such reason has surfaced. A3 selection-prep inherits Reading 1.

The cluster-A surface-vs-meta-surface question is now closed by **two-spec precedent** (A1 at `cddcfb5`, A2 at `ee671da`); the inheritance pattern is doctrinal-stable.

**Confidence on the carry-forward:** **High** (Reading 1 is the cluster-A election from `cddcfb5`; A2 spec re-confirmed at `ee671da`; the brief's Anti-Drift §3 binds against re-litigation; two-spec precedent makes the inheritance pattern doctrinal-stable).

---

## 6. Diagnostics that gate decision-readiness

Five diagnostics are named below. Each is what would need to be true (or characterized) before A3's decision-readiness session can confirm a disposition.

### 6.1 D1 — substrate-coverage detail per sub-shape

**What:** A per-sub-shape substrate-coverage probe. For each candidate sub-shape in §4.2, confirm: (a) the canonical event types the sub-shape consumes are present (`WEEKLY_MATCHUP_RESULT` for all six candidate sub-shapes); (b) the relevant D39 / D45 / D50 detector (or, for §4.2.4 runner-up count and §4.2.5 repeat-meeting, the small new aggregation primitive's input data) is present and aggregates correctly; (c) the cross-season reach extends across the 16-season digital window without gaps; (d) the playoff-detection trick fires cleanly per season (per A1 Step 1 §3.1's "rock-solid across 2010-2025" finding, the trick is empirically validated — D1's A3-specific probe is partial-confirmation of that finding under A3's bracket-presentation rather than just championship-week consumption).

**Why this matters:** §4.2 above characterizes substrate-coverage as "high" for the lift-direct sub-shapes (§4.2.1 generalizes `compute_championship_roll`; §4.2.2 lifts D39; §4.2.3 lifts D45) and "medium-high" for the new-aggregation sub-shapes (§4.2.4 runner-up count; §4.2.5 playoff-only meetings). These ratings are *structural-read priors*, not empirical confirmations. A3's bracket-presentation has not been render-validated; sample-output checks at Step 1 confirm or qualify.

**What to run, where:** A diagnostic-style query session, analogous to A1 Step 1 §3's matchup-substrate confirmation and A2 Step 1 §4.1's auction-substrate confirmation. Read the actual D39 / D45 / D50 detector implementations and `compute_championship_roll` (this memo did structural reads; Step 1 reads source AND runs SQL probes); confirm cross-season scope works against actual data; sample outputs against verification anchors (see D2 below for the 2025 playoff-bracket anchor specifically, which is the most-recent and best-substrate-validated season).

**What gates decision-readiness:** A "substrate supplies sub-shape X" finding for each sub-shape considered admissible-for-v1. Sub-shapes where the substrate does not supply cleanly are routed either upstream (substrate-readiness arc upstream of A3's spec, F1-style per Roadmap §4.5) or out of A3's v1 candidate set.

**Confidence this diagnostic is necessary:** **High** — substrate-coverage assessment at *sub-shape* resolution is needed before the spec session commits to a v1 trio (or quartet). Same logic as A1 D1 and A2 D1. **A3-specific note:** D1 expects to be largely confirmatory of the structural-read prior because of A1's two-pass substrate exercise (Step 1 + production rendering at `642d6dc`); A3 is the most-substrate-mature of any selection-prep candidate at its own selection-prep moment.

### 6.2 D2 — historical-data-completeness probe (playoff-week-specific framing)

**What:** A probe of whether `WEEKLY_MATCHUP_RESULT` coverage across the 16-season digital-era window is complete for playoff weeks specifically, with appropriate format-shift treatment.

**Largely confirmatory given preceding chain validation:**

- A1 Step 1 §3.1 confirmed the playoff-detection trick fires per season across 2010-2025; A1's `compute_championship_roll` produces a non-empty result for every digital-era season (16/16 rows in `archive/hall_of_fame_and_shame/championship_roll.md`).
- A1 Step 1 §3 also confirmed `WEEKLY_MATCHUP_RESULT` coverage across the 16-season window for the matchup-aggregation primitives.

**However**, A3-specific D2 retains two non-trivial probe dimensions:

1. **2021-format-shift carry-forward.** A1 Step 1 §6.2 / §6.3 and A1 spec §3.7 surfaced the 2021 W18-vs-W17 format-shift — 14 regular-season games per franchise pre-2021 vs 15 post-2021. The format shift moved the playoff-start week by one (championship week is W16 in pre-2021 seasons; W18 in post-2021 seasons per the `archive/hall_of_fame_and_shame/championship_roll.md` Week column). **For A3, the format-shift affects bracket-week placement, not just championship-week placement** — the semifinal and any preliminary-round weeks all shifted accordingly. A3's bracket-presentation must handle this. Probe at Step 1: confirm playoff-week placement per season; confirm the trick produces 2-week or 3-week playoff sets correctly across the era boundary; confirm the bracket-presentation can render era-mixed leaderboards (e.g., the §4.2.2 appearance-count leaderboard pools 2-week-playoff seasons and 3-week-playoff seasons).

2. **Playoff-week count distribution per season.** PFL Buddies' playoff format is 6-team (per A1 Step 1's standard-playoff-format-confirmation); the trick assumes the playoff weeks are detectable by matchup-count drop. Confirm distribution: how many playoff weeks per season (typically 2 in pre-2021 era — semifinal + championship — or 3 in some seasons); whether any season has a playoff-bye-week that complicates bracket-presentation.

**Specific open questions D2 surfaces** (Step 1 probes; this memo names; does not run):

- `SELECT season, week, COUNT(*) as cnt FROM v_canonical_best_events WHERE event_type='WEEKLY_MATCHUP_RESULT' AND league_id='70985' GROUP BY season, week ORDER BY season, week` — confirm full per-(season, week) matchup-count distribution; identify playoff weeks per season via the trick; confirm no season-internal gaps within 2010-2025.
- For each season, confirm the playoff-week set produced by the trick aligns with the championship-week row in A1's `championship_roll.md` (the W16 / W18 column shows the championship; the prior playoff weeks should be one week earlier with 3 matchups in the semifinal, and possibly two weeks earlier with 4 matchups in the preliminary round if applicable).
- For the 2021 transition specifically: confirm 2020 ends at W16 championship; confirm 2021 ends at W18 championship; confirm the playoff-week count shifts cleanly.

**Verification anchor:** the 2025 playoff bracket. A1 Step 1's "2025 was unusual in producing simultaneous top-1 updates in worst-season and blowouts" finding (cited in A1 spec §3.5) means 2025 is the most-attended-to recent season; Step 1's sample-bracket-validation should reconstruct 2025's full playoff bracket from `WEEKLY_MATCHUP_RESULT` events. Per A1's `championship_roll.md`: 2025 championship was W18, Paradis' Playmakers 139.40 vs Weichert's Warmongers 118.65. Step 1 confirms the semifinal pairings (W17 — 3 matchups expected per 6-team bracket) and the bracket-structure render matches league memory.

**Why this matters:** The format-shift and playoff-week-count distribution shape A3's bracket-presentation framing-copy and era-spanning aggregation discipline (analog to A1 spec §3.7's format-shift normalization). The bracket-week placement is the bracket-presentation's spine; getting it era-aware-but-coherent is the §6.x spec-stage normalization disposition for A3 (analog to A1 spec §3.7).

**What gates decision-readiness:** A coverage matrix confirming playoff-week extraction across 2010-2025 with format-shift treatment characterized.

**Confidence this diagnostic is necessary:** **High** — though largely confirmatory of A1 Step 1's prior validation, the A3-specific bracket-week placement and per-season-playoff-count distribution are render-side concerns A1 did not exercise (A1 only consumed the championship-week subset of the trick's output).

### 6.3 D3 — GAF / lore-pick canonicalization framing (playoff-specific)

**What:** A framing-decision diagnostic, structurally analog to A1 D3 and A2 D3 but playoff-specific. What does A3 do with culturally-significant playoff moments that live in league memory but interact with the canonical substrate differently than A1's matchup-derived GAF or A2's auction-derived lore?

**Three candidate dispositions, inheriting A1 D3 shape (and A2 D3 inheritance shape):**

- **D3-Alpha — Substrate-derivable proxies only.** A3 ships only playoff moments derivable from `WEEKLY_MATCHUP_RESULT` via the playoff-detection trick. The "famously close championship" surfaces as a top-N entry in the §4.2.6-folded-into-§4.2.2 closeness-leaderboard (if elected); the "they ALWAYS lose in the semifinals" pattern surfaces as a §4.2.3 split-divergence entry; the league's GAF label for a specific moment is *not* stored or surfaced. **Inherited as the leading default per A1 spec §1's D3-Alpha election and A2 spec §1's D3-Alpha inheritance** unless A3-specific friction surfaces.
- **D3-Beta — Commissioner-curated lore annotation layer.** A3 ships substrate-derived playoff moments PLUS a commissioner-curated annotation table tying specific playoff matchups to specific league-lore labels. Same admissibility-in-principle finding as A1 selection-prep §6.3 (`Narrative_Angles_v2_Definitive_Scope.md` Dimensions 10-11 reference-metadata precedent). A1 elected D3-Alpha; A2 inherited D3-Alpha; D3-Beta is preserved as a future-expansion path per A1 spec §1.
- **D3-Gamma — Defer the lore-moments dimension entirely.** Same shape as A1 D3-Gamma and A2 D3-Gamma; less load-bearing for A3 because A3's bracket presentation and cross-era leaderboards already capture the substrate-derivable lore-pattern at v1.

**A3-specific friction characterization:** the playoff substrate is **structurally cleaner than A1's matchup substrate** for D3-Alpha purposes — bracket structure is fully derivable; no lore-density question at the v1 timing because the bracket *is* the substrate-derived structure, and the cross-era leaderboards over playoff appearances / runner-ups / one-game-out finishes ARE the affectionately-remembered patterns. A2 spec §1's D3-Alpha-inheritance reasoning ("the auction-bust hall IS the substrate-derivable proxy for famously bad bids") applies symmetrically: "the cross-era bridesmaid count IS the substrate-derivable proxy for famously close-but-no-cigar finishes." Lower friction than A1 had on D3.

**What to run, where:** Step 2 framing analysis. Confirm or surface A3-specific friction. Expected: clean D3-Alpha inheritance.

**Gating criterion:** D3-Alpha confirmation, or surfaced A3-specific friction warranting D3-Beta consideration. **Leading hypothesis: D3-Alpha inheritance.**

**Confidence this diagnostic is necessary:** **Medium-high** — inherited by precedent; A3-specific friction is low-likelihood per the structural-read characterization above; Step 2 confirms.

### 6.4 D4 — operational rhythm (channel, cadence anchor, push-distribution)

**D4.1 channel:** Inherited from A1 (`cddcfb5` §1 D4.1-Gamma) and A2 (`ee671da` §1 D4.1-Gamma inheritance). A3 ships as archive-resident (browse-cadenced) + push at notable moments. Confirm or surface A3-specific friction. Expected: clean inheritance.

**D4.2 cadence anchor:** This is the A3-specific D4 dimension with the most substantive divergence-from-precedent argument. Three candidate anchors:

- **D4.2-Alpha — NFL Week 1 (~2026-09-08), shared with E1, A1, A2.** Pro: cross-surface consistency; one calendar moment for all Phase 11 revisions. Con: NFL Week 1 is a *consumption-layer* moment (the weekly cadence resumes); A3's relevance is anchored on *end-of-NFL-season* (when the new champion is crowned and the cross-era leaderboards may reorder) more than season-start moments. **Same con-shape as A2's D4.2-Alpha consideration but with a materially-stronger A3-specific Beta candidate** —

- **D4.2-Beta — End-of-NFL-season (~February 2027), when the new championship lands.** Pro: A3's substrate-side cycle is *complete* at end-of-season; the revision can incorporate the full new season's playoff bracket + reorder the cross-era leaderboards if the new championship landed a new appearance-count record or a new runner-up record. **Substantively the strongest anchor for A3's substance** because end-of-NFL-season IS the canonical A3 moment — the championship landing is the substrate-accumulation moment that defines A3's revision content.

- **D4.2-Gamma — Active playoff weeks (~December-January), when the bracket is being filled in.** Pro: the bracket-presentation is most relevant during the active playoff weeks. Con: the bracket is *incomplete* during active playoff weeks; revising A3 incrementally as each playoff round resolves creates a multi-revision in-season cadence that has no analog in E1, A1, or A2's operational rhythms. Likely too high-cadence for a browse-cadenced archive.

**A3-specific substance-honesty argument for Beta:** A2 selection-prep §8.2 surfaced D4.2-Gamma (auction-night) as a substantively-relevant A2-specific alternative; A2 spec elected D4.2-Alpha (NFL W1) for cross-surface consistency. **A3's D4.2-Beta substance-honesty argument is materially stronger than A2's D4.2-Gamma was**, because:

- A2's auction-night moment is a *new substrate-accumulation* event with no analog in A1's or E1's rhythms; the cross-surface-consistency argument for Alpha was that the consumption-resumption shape is the dominant rhythm. A3's end-of-NFL-season moment IS the consumption-resumption-and-revision moment for *both* A3 and A1 (A1's championship roll updates per new champion landing; A3's bracket archive and cross-era leaderboards update per the same event). **End-of-NFL-season has cross-surface coherence between A1 and A3 in a way auction-night did not have with A1.**

- The A3 substance-honesty argument has *symmetry with A1*'s end-of-season-revision flow (A1's championship-roll new-row falls in February per its Step 1 §6.5 cadence note about 2025 producing simultaneous top-1 updates clustered around end-of-season).

**Recommended Step 2 weighting:** the D4.2 election is genuinely open. **Leading hypothesis: D4.2-Alpha by inheritance default with D4.2-Beta named as the substantively-relevant A3-specific alternative the founder may elect at Step 2.** The chat-session recommendation is to inherit D4.2-Alpha for cross-surface consistency; the founder's product judgment may legitimately prefer D4.2-Beta for substance-honesty AND for cross-surface A1-A3 coherence (the strongest D4.2-Beta argument is that A3's substance-honesty moment aligns with A1's natural revision rhythm, not just A3's standalone substance). Step 2 adjudicates.

**D4.3 push-distribution triggers:** Bounded set scoped to v1 sub-shape combination. Mirroring A1 spec §3.5 and A2 spec §3.5 pattern. Expected trigger candidates:

- **A new championship is crowned.** Once per NFL season, ~February. Pre-existing A1 trigger per A1 spec §3.5; A3 references rather than re-trigger (the cross-link discipline at §3.1 means A1 owns the new-championship push event).
- **A new top-1 entry in cross-era playoff appearances (§4.2.2 dimension).** At most once per NFL season; rare given the 16-season substrate and the stability of multi-appearance leaders.
- **A new top-1 entry in cross-era bridesmaid count (§4.2.4 dimension).** At most once per NFL season; rare. Specific bracket-pattern findings (e.g., a franchise's third semifinal exit landing the runner-up-without-winning record) are sub-shape-specific.

**Explicitly NOT triggers** (per A1 spec §3.5 / A2 spec §3.5 precedent): per-bracket-fill-in pushes during active playoff weeks (would generate a push per round; couples to D4.2-Gamma's rejected-for-cadence-noise framing); per-franchise-specific bracket updates; browse-activity signals.

**Expected push cadence:** at most 1-2 events per NFL season per A3's standalone triggers (with A1 owning the new-championship push). Most NFL seasons will not trigger any A3 push (top-1 cross-era records are stable across most seasons; the new-championship event is A1's trigger). **A3's push cadence is sparser than A1's or A2's** because most cross-era records are stable; the bracket-presentation sub-shape is its own structural surface that doesn't generate "record falls" events.

**Gating criterion:** D4.1 inheritance confirmation; D4.2 election framing with the A3-specific Beta-vs-Alpha founder call surfaced explicitly; D4.3 enumeration scoped to elected v1 trio.

**Confidence on the D4 disposition:** **Medium-high** for D4.1 inheritance; **medium** for D4.2 election (Alpha vs Beta is the open call; substance-honesty argument for Beta is real and A3-specific); **medium-high** for D4.3 scoping per sub-shape.

### 6.5 D5 — meta-surface question (closed by A1 Reading 1 inheritance)

**What:** Closed by A1 Reading 1 inheritance per §5 above. The cluster-A meta-surface question is settled by two-spec precedent (A1 at `cddcfb5`, A2 at `ee671da`); A3 ships single-surface; the Surface Admission Test's predecessor-state-met condition is not advanced by A3's registration (the two-spec requirement was met at `cddcfb5`; the one-content-class-admission-attempted requirement still gates and is unaffected by A3).

**Recorded as carry-forward; not a fresh diagnostic.** No action at Step 1 or Step 2.

**Confidence this diagnostic is necessary:** **N/A** — diagnostic dissolved by Reading 1 inheritance (two-spec precedent).

---

## 7. Leading hypothesis and disposition

Per Anti-Drift §10 #2 (defer with leading hypothesis is a valid output): this memo lands a **two-tier disposition** — leading hypothesis on the within-A3 v1 sub-shape combination paired with **explicit deferral** on the four substantive diagnostics (D1, D2, D3, D4) that require Step 1 / Step 2 session work.

### 7.1 Leading hypothesis on within-A3 v1 sub-shape combination

**A3 v1 ships: Per-Season Playoff Bracket Presentation (§4.2.1) + Cross-Season Playoff Records (§4.2.2) + Bridesmaids and Almosts (§4.2.4).**

Reasoning:

- **The three together cover the structure / records / pattern dimensions of playoff history**, structurally analogous to:
  - A1's trio (championship roll = fame; worst-season tracking = shame; blowouts hall = spectacular-outlier)
  - A2's trio (auction-most-expensive history = fame; auction-bust hall = shame; auction-bargain hall = spectacular-outlier)
  - A3's trio (per-season playoff bracket = the canvas / canonical structure; cross-season records = the aggregate / appearance-counts; bridesmaids and almosts = the affectionately-remembered close-calls / the playoff analog of A1's blowouts hall and A2's auction-bust hall).
- **§4.2.1 IS the Roadmap §2.2 framing of A3** ("playoff brackets and outcomes"); shipping A3 without §4.2.1 would not be a Championship Timeline surface. **Forcing function at v1.**
- **All three exercise existing playoff-detection primitives and detector family.** §4.2.1 generalizes the playoff-detection trick from `compute_championship_roll`'s championship-week-only narrow to multi-playoff-week extraction (same primitive; broader output filter). §4.2.2 lifts D39 (already cross-season-scoped) plus the small streak extension. §4.2.4 lifts D50 (already cross-season-scoped) plus the small runner-up cross-era aggregation. The implementation pattern is the cleanest of the catalog combinations — lower implementation risk than A2's bust/bargain cross-season-lift (which required cross-season aggregation work on D21/D22's single-season-scoped logic).
- **§9.2 artisan-frame fit is high for the trio.** The per-season bracket presentation is the canonical playoff-canvas content. The cross-season records dimension surfaces playoff-dynasty / playoff-drought patterns (Voice-Profile-§5 affectionately-remembered league memory). The bridesmaids-and-almosts dimension is the strongest §9.2-anchor in the catalog (the playoff analog of A2's auction-bust hall; the "you were SO close" affectionately-remembered pattern).
- **Implementation-risk lowest among the candidate trios** that yield a defensible Championship Timeline. §4.2.3 (regular-season vs playoff splits) is also low-risk (D45 already cross-season) and could be added without backfill dependency; it's a within-Reading-1 expansion call at decision-readiness Step 2. §4.2.6 (title-game records / closeness) is largely A1-absorbed and weaker as a standalone candidate.
- **Substrate-readiness highest of any selection-prep at its own moment.** The playoff-detection trick has been production-validated by A1's shipping (`642d6dc`). A3 is the most-substrate-mature surface candidate at the moment of its selection-prep — the substrate has been exercised end-to-end already (Step 1 validation + production rendering). A1 had Step 1 validation only at its selection-prep moment; A2 had detector-suite implementation only.
- **No D2 backfill dependency beyond what A1 already cleared.** All three sub-shapes consume `WEEKLY_MATCHUP_RESULT` only; the 2021 format-shift is the only D2-side-concern, and A1 spec §3.7's "single-table-with-footnote" normalization disposition applies symmetrically to A3.

**This is anchor, not forcing.** Decision-readiness Step 2 may elect:

- **+ Regular-season vs playoff splits (§4.2.3)** — low marginal substrate cost (D45 already cross-season); medium-high §9.2 fit; adds the per-franchise time-allocation dimension. Defensible as a four-sub-shape v1.
- **+ Repeat-bracket-meeting patterns (§4.2.5)** — medium implementation cost (new aggregation; new render shape; cross-link consideration with F1 if F1 ships post-A3). Higher complexity v1; F1 coordination question worth deferring to F1's selection-prep when it becomes next-eligible.
- **− Cross-season records (§4.2.2)** — narrows the trio to bracket + bridesmaids; loses the cross-era appearance-count dimension. Defensible if Step 2 elects a tighter v1; unlikely given §4.2.2's substrate-readiness is high and its §9.2 fit is high.
- **Closeness-margin dimension folded in from §4.2.6** — adds the "closest championships" sub-leaderboard to §4.2.2; small-incremental render addition over an existing primitive. Step 2 election call.

**Counter-hypothesis consideration:** A four-sub-shape v1 (trio + §4.2.3 regular-season vs playoff splits) is the cleanest expansion candidate at decision-readiness — adds the per-franchise time-allocation frame the trio lacks; combined cost is low (D45 already cross-season; no additional D2 dependency). **Recommended Step 2 weighting:** trio first; regular-season-vs-playoff splits as a defensible Step 2 election if the founder wants the per-franchise time-allocation dimension. §4.2.6's closeness-margin sub-leaderboard is a defensible add-on within-§4.2.2 if the founder wants the closeness dimension.

Confidence on the within-A3 leading hypothesis: **Medium-high.** Reasoning is anchored on substrate-coverage characterization, the A1-A3 absorption boundary at §3.1, and parent §4 §9.2 framing; the trio is not foreclosed by this memo.

### 7.2 Carry-forward on surface-vs-meta-surface

Per §5 above: closed by A1 Reading 1 inheritance (now two-spec precedent at A2). A3 ships single-surface. No deferral; the question is settled, not deferred.

Confidence on the carry-forward: **High** — the cluster-A meta-surface question is settled at `cddcfb5` §1; A2 spec re-confirmed at `ee671da` §1; the brief's Anti-Drift §3 binds against re-litigation.

### 7.3 Deferral on diagnostics D1, D2, D3, D4

Per §6: the four substantive diagnostics are decision-readiness session work (Step 1 empirical for D1, D2; Step 2 framing for D3, D4), not selection-prep work. This memo registers them; the decision-readiness sessions run them.

The leading hypothesis above is **conditional on**:
- **D1 confirming substrate-coverage** for §4.2.1 / §4.2.2 / §4.2.4 as the structural-read prior characterizes (high-confidence expected; the playoff-detection trick is A1-production-validated);
- **D2 confirming playoff-week coverage** across 2010-2025 with 2021-format-shift treatment characterized;
- **D3 inheriting D3-Alpha** (no A3-specific friction surfaces at Step 2);
- **D4.1 inheriting D4.1-Gamma** (archive + push); **D4.2 founder-elected** between Alpha (NFL W1; cross-surface consistency) and Beta (end-of-NFL-season; A3-and-A1 substance-honesty coherence); **D4.3 push-triggers** scoped to elected v1.

If the probes surface unexpected findings, the disposition adjusts. Per A1 selection-prep §7.3 / A2 selection-prep §7.3 precedent: the diagnostic registration is structurally clean even when individual diagnostic outcomes are unknown.

Confidence on the diagnostic registration: **High** — five diagnostics, each with named gating criteria; no operational ambiguity about what decision-readiness adjudicates.

---

## 8. Operational rhythm and revision-point framing

A3 is not weekly-cadenced. Same shape as A1 spec §8 and A2 spec §8 (browse-and-event-cadenced) with one A3-specific dimension surfaced at §8.2 below.

### 8.1 The cadence shape

A3 is **event-and-browse-cadenced.** New `WEEKLY_MATCHUP_RESULT` events accumulate per the existing platform's weekly cycle; A3's *presentation* of those events updates at moments larger-grained than the substrate's update rate:

- **Annually at end-of-NFL-season (~February)** — when the new championship lands. The new playoff bracket extends the per-season presentation by one season; cross-era leaderboards recompute against the new playoff-week data; potentially a new top-1 entry falls in §4.2.2 (appearance-count) or §4.2.4 (bridesmaid count). **This is the canonical A3 revision moment.**
- **At notable in-season moments** — rare but possible (a mid-playoff trade or a playoff-substituted franchise might affect bracket presentation, though A3's substrate-derivable bracket structure is event-based, not roster-based, so most in-season moments don't trigger A3 updates).
- **On commissioner-curated occasions** — playoff retrospectives; cross-era playoff-pattern reflection moments.

The browse-cadence is **continuous** — league members may revisit at any time.

**A3's per-year update rhythm is roughly single-phase (end-of-NFL-season), structurally similar to A1's single-phase rhythm and structurally distinct from A2's two-phase rhythm (auction night + end-of-season).** The bracket-incremental-fill-in during active playoff weeks is *not* an A3 revision event — A3 is a retrospective archive, not a real-time bracket tracker; the active-bracket consumption is the weekly recap's territory (E1).

### 8.2 Revision-point options (the A3-specific D4.2 election)

Three candidate anchors for A3's revision-point (analog to A1 selection-prep §8.2 and A2 selection-prep §8.2):

- **Anchor 1 — NFL Week 1 (~2026-09-08), shared with E1, A1, A2.** Pro: cross-surface consistency; one calendar moment for all Phase 11 revisions. Con: NFL Week 1 is a *consumption-layer* moment (the weekly cadence resumes); A3's relevance is anchored on the championship-lands moment, not the season-start. **A3's NFL-W1-anchor con is structurally similar to A2's** — both surfaces have natural cycle-completion moments distinct from the consumption-resumption moment.
- **Anchor 2 — End-of-NFL-season (~February 2027), when the new championship and bracket land.** Pro: A3's substrate-side cycle is *complete* at end-of-season; the revision can incorporate the full new season's playoff bracket and reorder cross-era leaderboards if new top-1 records fall. **A3's strongest substance-honesty anchor.** Pro (cross-surface): end-of-NFL-season ALSO triggers A1's championship-roll-update; **A3 and A1 share a natural revision rhythm under this anchor.** Con: ~9-12 months after the spec session lands; the cross-surface-consistency-with-E1 dimension is weaker than under Alpha.
- **Anchor 3 — Active playoff weeks (~December-January).** Pro: bracket-presentation is most relevant during active playoffs. Con: the bracket is *incomplete* during active playoff weeks; multi-revision in-season cadence; couples to D4.2-Gamma's rejected-for-cadence-noise framing per A1 spec / A2 spec precedent. Excluded as too high-cadence for browse-cadenced archive (analog to A2's Gamma exclusion logic on niche-generality + cadence-noise grounds).

**Leading hypothesis on the anchor:** **D4.2-Alpha (NFL Week 1) by inheritance default, with D4.2-Beta (end-of-NFL-season) named as the substantively-relevant A3-specific alternative the founder may legitimately elect at Step 2.** This is the same outcome A2 reached at D4.2 in shape but with A3-specific substance-honesty weighting:

- A2's D4.2-Gamma (auction-night) was a *new substrate-accumulation* moment with no analog in A1's or E1's rhythms; A2 elected D4.2-Alpha for cross-surface consistency. A3's D4.2-Beta argument has **a non-equivalent cross-surface dimension** — end-of-NFL-season aligns with A1's natural revision rhythm. The Step 2 founder call is genuinely open in a way A2's was leaning-toward-Alpha.

The chat-session recommendation is **to surface the D4.2-Alpha-vs-Beta election as a genuine Step 2 call rather than a default-inheritance carry-forward.** The substance-honesty + A1-coherence argument for Beta is materially stronger than A2's Gamma was; the cross-surface-consistency-with-E1 argument for Alpha remains real but is weaker in A3's case because E1 is the only Alpha-aligned surface remaining (A1 and A2 elected Alpha previously, but A1's actual update rhythm per its spec is end-of-season-anchored).

Confidence on the anchor disposition: **Medium** — D4.2-Alpha is the cleanest cross-surface default with E1; D4.2-Beta is a defensibly-stronger A3-specific election with A1-coherence; the founder adjudicates with full knowledge that the precedent-inheritance default points to Alpha but the substance-honesty pull points to Beta.

### 8.3 "One full cycle" semantics for §8.4 closure-eligibility

Per A1 spec §8.3 inheritance (carried through A2 spec §8.3): **Reading C — one full cycle for A3 = one push distribution event observed AND one season-rollover incorporated.**

Operationally for A3:

- **One push distribution event observed** — at least one notable-moment push per §6.4 D4.3 triggers has fired (most likely the end-of-NFL-season cross-era leaderboard update if a new top-1 falls; or a one-time spec-session-shipping-event push).
- **One season-rollover incorporated** — the end-of-2026-NFL-season playoff bracket has resolved and been incorporated into A3's archive.

This is consistent with A1's §8.3 framing and A2's §8.3 framing. A3's first cycle is plausibly ~9-15 months from ship depending on whether the spec session lands in late 2026 or early 2027. **Under D4.2-Beta election**, A3's first full cycle exactly aligns with A1's first cycle (both update at end-of-2026-NFL-season); under D4.2-Alpha election, A3's first cycle aligns with E1's (NFL W1) but lags the substantive content-update by ~6 months.

Confidence on the "one full cycle" reading: **Medium-high** (inherits A1 spec §8.3 framing; A3's single-phase update rhythm is the simplest of the three Phase 11 surface candidates — A2's two-phase was the more ambiguous one).

---

## 9. Cluster-A admissibility carry-forward (post-A3 admissible-surface-set)

If A3 is selected and specified at the next two sessions (decision-readiness + specification), **Cluster A is exhausted.** Per A2 spec §9.1: cluster A's remaining admissible surface is A3; A3's shipping closes the cluster.

The Roadmap's admissible-surface-set after A3 ships:

- **Shipped:** E1, A1, A2, A3.
- **Admissible, within Cluster A:** (none; cluster exhausted)
- **Admissible, within Cluster E:** E2-light, E3.
- **Admissible, contingent on substrate-readiness:** F1.

### 9.1 Cluster-A exhaustion

Cluster A's three within-cluster sub-surfaces (A1, A2, A3) will all be shipped after A3's spec session lands. The within-cluster sequencing question that operated across the A1 / A2 / A3 selection-prep chain (Roadmap §2.2 within-cluster sub-question; resolved per Roadmap §4.3 / §4.4 + actual ordering as A1 → A2 → A3) **terminates with this chain.** No within-cluster sub-question remains.

**Post-A3 admissible-set framing:**

The founder elects what ships next after A3 at the post-A3-shipping moment per Roadmap §4.4 "Subsequent-surface conditions." Plausible candidates for the next chain are:

- **E2-light** (Reader-facing browseable archive of approved recaps) — admissible per Roadmap §2.2; sequenced post-E1 stabilization. Status-of-E1-stabilization is a separate question from cluster-A exhaustion; the founder's election at the post-A3-shipping moment considers E2-light alongside the other admissible candidates.
- **E3** (Commissioner-facing review-and-approve UX) — admissible per Roadmap §2.2; sequenced behind E2-light per Roadmap framing or independently per Roadmap §4.4 founder election.
- **F1** (Rivalry Chronicle) — admissible-contingent-on-substrate-readiness per Roadmap §2.3 / §4.5. F1 substrate-readiness arc (estimated 6-8 sessions per memory edit) is independent of A3's chain; F1 may be elected as next when its substrate-readiness is met, OR a non-F1 selection may be elected with F1 substrate-readiness work continuing in parallel.

**None of these is pre-decided by this memo.** The carry-forward is admissibility, not founder commitment.

### 9.2 Cross-cluster carry-forward unaffected

- **E2-light** — admissible-sequenced-behind-E1 per Roadmap §2.2; A3's shipping does not affect E2-light's sequencing beyond opening the next-chain founder-election window post-A3.
- **E3** — admissible-sequenced-behind-E1 per Roadmap §2.2; A3's shipping does not affect E3's sequencing.
- **F1** (Rivalry Chronicle) — admissible-contingent-on-substrate-readiness per Roadmap §2.3 / §4.5. F1 substrate-readiness arc is independent of A3 selection; A3's shipping does not advance or block F1.
- **Cluster B** — failed §8.2 + §4.4 per parent §4; carry-forward unchanged.

### 9.3 Surface Admission Test predecessor-state

The Surface Admission Test (Roadmap §5.1) requires *two registered per-surface constitutional memos PLUS one content-class admission attempted.* The two-spec requirement was met at `cddcfb5`; A2 brought the count to three at `ee671da`; A3's registration (when it lands) brings the count to four. The framework-artifact-grounding base widens with each registered spec. **The one-content-class-admission-attempted requirement is the gating predecessor; A3's shipping does not change this.** Per side finding in `5291c46` §7.1: the one-content-class-admission requirement is the gating predecessor; A3's shipping advances the framework-grounding base but not the gating predecessor-state.

Confidence on the carry-forward framing: **High** (framing is doctrinally anchored on parent §4 Cluster A admissibility, Roadmap §2.2 / §4.4, A1 spec §9 inheritance, A2 spec §9 inheritance, and template v1.0 §7.1 finding).

---

## 10. Anti-drift — what this memo does not do; side findings

Mirroring the brief's Anti-Drift section, with the relevant carry-forwards from the predecessor memos:

1. **The leading hypothesis (A3) is from the Roadmap and A2 spec §9.1, not from this brief.** A1 selection-prep §10 #1 / A2 selection-prep §10 #1 precedent. Within-A3 sub-shape leading hypothesis (§7.1) is from this memo's analysis but is **anchor, not forcing**.

2. **A3's substrate-readiness prior is "favorable" — and is the most-substrate-mature of any selection-prep candidate at its own moment** — but D1 / D2 are load-bearing diagnostics, not confirmatory ones. Per the brief's Anti-Drift §2: A1 shipped the playoff-detection trick at production at `642d6dc`, validating the substrate at the championship-week subset. A3's bracket-presentation broadens the consumption to all playoff weeks; the broadening has not been render-validated.

3. **Sub-shape selection is not prejudged.** §4 catalog is open; §7.1 leading hypothesis is anchor, not forcing.

4. **A1's Reading 1 election and the cluster-A inheritance chain are not reopened.** Cluster-A meta-surface question settled at `cddcfb5` §1, re-confirmed at `ee671da` §1 (two-spec precedent). Carry-forward by precedent.

5. **D46 is single-week-scoped, not cross-season-scoped.** The brief's framing in §4.2.4 mentioned "Repeated runner-up patterns (D46 THE_BRIDESMAID)" but a structural read of `franchise_deep_angles_v1.detect_the_bridesmaid` (lines 691-733) confirms D46 surfaces the second-highest-scoring franchise that LOST IN THAT WEEK's matchup — a single-week pattern, not a cross-season championship-runner-up pattern. A3's cross-season runner-up aggregation is a NEW small primitive over `compute_championship_roll`'s output, structurally adjacent to but distinct from D46. Recorded as a brief-attribution finding for §10.2 below.

6. **A2's elections are not reopened.** A2 spec §1 inheritance shape (Reading 1, D3-Alpha, D4.1-Gamma, D4.2-Alpha, D5-Gamma) carries forward unchanged.

7. **No template-v1.0 exercise smuggled in.** This selection-prep is `3e9065f`-shaped (which was `ba44ba4`-shaped with documented adaptations), not `9093a07`-shaped / `cddcfb5`-shaped / `ee671da`-shaped. Eleven-section selection-prep structure, not twelve-section spec template structure. Template v1.0 binds A3's specification at chain step 3, not this memo. Per template v1.0 §5.1: A3's spec session will record its §11 adaptations (if any). **This memo does not author or commit to that §11 record.**

8. **Silence over speculation on playoff-substrate specifics.** §4 characterized D39 / D45 / D46 / D50 + `compute_championship_roll` at structural level (data consumed, aggregation produced, cross-season scope). No SQL probes against `canonical_events` to confirm specific season-by-season playoff-week placement — Step 1's job.

9. **The 2025 playoff bracket verification anchor is named for the selection-prep memo as a Step 1 verification target; the verification has NOT yet happened.** Cited as documentary anchor from A1's `championship_roll.md` working-tree content (which shows 2025: Paradis 139.40 vs Weichert 118.65 at W18 championship); not stated as bracket-substrate-confirmed at the semifinal level.

10. **No new framework artifacts smuggled in.** This memo ships one artifact. Side findings during authoring fold into §10.2 below, not split into separate commits.

11. **Post-A3 admissible-set records cluster-A exhaustion as fact, not commitment.** The founder elects what ships next after A3 at the post-A3-shipping moment per Roadmap §4.4. Plausible candidates are E2-light, E3, F1 (with substrate-readiness arc); none is pre-decided here.

12. **No engagement metrics, ever.** §2.3 binding. A3 doesn't track read-rates, retention, audience segmentation, recommendation, growth-loops. Reception observations on A3 (when it ships) are voice-iteration data per Operational Plan §10 commitment #4.

13. **§4.4 social-surface boundary.** A3 is a surface, not a network.

14. **One topic per commit.** This memo is one commit per the brief.

15. **The Roadmap is the predecessor.** This memo reads it; doesn't ignore it; doesn't overwrite it. The compound seasons-count finding (§10.2 below) is recorded for a future Roadmap revision sweep; this memo does not amend the Roadmap.

16. **Pending follow-ons from the A2 session do NOT block this brief.** The two A2 follow-ons (Cavallini/Mahomes anchor revocation memo; rename of `test_cavallini_mahomes_2018_qb_anchor_regression`) and the script-docstring update are independent doc-only / test-naming commits and may land before, alongside, or after this selection-prep without affecting the chain. As of HEAD `9189a7d`, none of these follow-ons has landed.

17. **Template v1.0 promotion is NOT in scope for this brief.** Template promotion is its own framework-artifact-promotion session, not part of A3's selection-prep. Per A2 spec §12.5 side-finding: template v1.0 is promotion-eligible (three clean exercises against E1 / A1 / A2). The promotion election is the founder's call at any future session; this memo does not advance, foreclose, or condition on it.

### 10.1 Side-findings that emerged during authoring (folded here, not split)

- **The Roadmap §2.2 "17 seasons" framing for A3 carries the same 17 → 16 drift A1 surfaced at Step 1 §4.2.** Same drift A1 and A2 surfaced; same compound-seasons-count finding recorded in memory edit #26. Recorded for the next Roadmap revision sweep alongside the A1 16-vs-17 and A2 16-vs-8 findings.

- **The 2021 format-shift treatment now affects three surfaces (A1, A2, A3) — possibly a candidate for cross-surface common treatment rather than per-spec individual treatment.** A1 spec §3.7 disposed (single-table-with-footnote); A2 spec §3.7 disposed (similar pattern). A3 will need to dispose similarly at the spec session. **Cross-surface common-disposition is a candidate template v1.x revision finding** — the format-shift handling is recurring across surfaces. Recorded for template revision consideration; A3's spec session will still need to make its own §6.x disposition pending template revision.

- **A3 surfaces a "what defines a playoff round" question more explicitly than A1 / A2 did, because the bracket *structure* is the substrate-derived view.** A1 only consumed the championship-week (one week per season; trivial round-definition); A3's bracket-presentation must handle 2-week-playoff and 3-week-playoff seasons in the same render. Spec-session §6.x scope-disposition concern. Recorded for spec session.

- **D4.2-Beta (end-of-NFL-season) as the A3-specific substance-honesty cadence anchor has a materially-stronger argument than A2's D4.2-Gamma was**, because end-of-NFL-season has *cross-surface coherence with A1* (both A1 and A3 update at this moment). A2's auction-night Gamma argument was A2-specific-only with no cross-surface coherence dimension. **The Step 2 D4.2 election for A3 is more genuinely open than A2's was.** Recorded for Step 2.

- **Cluster A exhaustion after A3 ships changes the post-A3 admissible-set materially.** Roadmap §4.4 "Subsequent-surface conditions" framing previously had within-cluster + cross-cluster sub-questions; post-A3 it has only cross-cluster sub-questions (and the contingent-on-substrate-readiness F1 question). Recorded for the next surface-selection moment per Roadmap §4.4. The next selection chain after A3's spec session is the first chain that operates entirely on cross-cluster sub-questions.

- **A3's substrate-maturity at its selection-prep moment is the highest of any Phase 11 candidate — by structural feature of the chain.** A1 shipped first; A2 followed; A3 is third. A1's selection-prep had detector-suite implementation + Architectural-Audit-characterized substrate. A2's selection-prep had detector-suite implementation + Architectural-Audit characterization + A1's Step 1 substrate-validation indirectly applicable. A3's selection-prep has all of that PLUS A1's production rendering at `642d6dc`. **This is the natural maturation of the Phase 11 surface-track**: each selection-prep inherits more substrate-readiness than the prior; the chain compounds substrate confidence. Recorded as a positive structural finding; not actionable beyond the carry-forward.

### 10.2 Brief-attribution findings (small)

- **The brief cited "Architectural Audit §7 — playoff-detection trick characterization" but the actual location is Architectural Audit §8 entanglement hotspot #3** (`ARCHITECTURAL_AUDIT_2026_04_16.md` lines 431-449). §7 is "Cross-cutting concerns" (which characterizes selection / windowing, name resolution, etc., not the playoff-detection trick specifically). The substance the brief describes IS the correct substance; only the §-number is mis-cited. Memo §3.1 and §4.2.1 cite §8 #3 accurately. **Minor brief-attribution slip; no substantive impact.** Recorded for completeness.

- **The brief cited "D46 THE_BRIDESMAID" as the substrate basis for "Repeated runner-up patterns" in §4.2.4.** Per Anti-Drift §10 #5: a structural read of `franchise_deep_angles_v1.detect_the_bridesmaid` (lines 691-733) confirms D46 is single-week-scoped (second-highest-scoring franchise that lost IN THAT WEEK's matchup), not cross-season championship-runner-up. The cross-season championship-runner-up pattern is a NEW small aggregation primitive over `compute_championship_roll`'s `runner_up_id` output — derivable from the same primitive A1 uses but distinct from D46. Memo §4.2.4 attributes this correctly. **Minor brief-attribution slip; substantive impact on §4.2.4's implementation-risk characterization** (the runner-up sub-shape is a small new aggregation, not a lift; counted as "medium-high" substrate-readiness rather than "high"). Recorded for completeness.

---

## 11. Confidence labeling

### 11.1 Highest-confidence claims

- **A3's substrate is the 16-season digital-era window** (2010-2025), same as A1's window per A1 spec §3.1. The Roadmap §2.2 "17 seasons" framing carries the same 17→16 drift surfaced for A1 and A2. (§3.1, §10.1)
- **The A1-A3 boundary is substrate-clean: shared primitive (`compute_championship_roll`), disjoint presentation scopes (A1 owns championship-week-only; A3 owns all-playoff-weeks).** Working-tree-confirmed against `championship_roll.md` (`642d6dc`). (§3.1, §4.3)
- **The §-substance load-bearing on A3 selection is source-anchored in the predecessor chain.** No fresh §-verification required. (§2)
- **A3's identity carry-forward from Roadmap §2.2 is admissible-confirmed.** Direct quotation; consistent with parent §4 Cluster A and the chain. A2 spec §9.1 carry-forward. (§3)
- **A3's substrate is substantively disjoint from A2 (auction-derived) and shared-primitive-different-presentation with A1.** Recorded; the A1 cross-link discipline at §3.1 operationalizes the boundary. (§4.3)
- **The cluster-A meta-surface question is closed by two-spec precedent** (A1 at `cddcfb5`, A2 at `ee671da`). Carry-forward by precedent; no re-litigation. (§5)
- **Defer with leading hypothesis is a valid output per parent §6.1 and Roadmap §8.1.** This memo lands exactly that shape. (§7)
- **The four substantive diagnostics (D1, D2, D3, D4) are necessary decision-readiness work.** Each named with what to run and what gates next step. (§6)
- **Cluster A is exhausted after A3 ships.** No within-cluster sub-question remains. Cross-cluster carry-forwards unaffected. (§9)

### 11.2 Medium-high confidence claims

- **Per-season playoff bracket presentation (§4.2.1) + Cross-season playoff records (§4.2.2) + Bridesmaids and almosts (§4.2.4) is the leading-hypothesis within-A3 v1 sub-shape trio.** Lowest implementation risk among defensible Championship Timeline combinations; covers structure / records / pattern; exercises existing playoff-detection primitives plus minimal new aggregation work; high §9.2 fit; substrate-mature per A1 production validation. Anchor, not forcing. (§7.1)
- **D1 substrate-coverage probe will largely confirm the structural-read prior** for §4.2.1 (playoff-detection trick lift), §4.2.2 (D39 already cross-season), §4.2.4 (D50 already cross-season; runner-up count is a small new aggregation). (§4.2, §6.1)
- **NFL Week 1 (~2026-09-08) D4.2-Alpha is the inheritance default revision-point anchor** for cross-surface consistency with E1. (§6.4, §8.2)
- **D3-Alpha (substrate-derivable lore proxies) inherits from A1 spec §1 election and A2 spec §1 inheritance.** No A3-specific friction surfaces in this memo's analysis to warrant D3-Beta exception. Step 2 confirms. (§6.3)
- **D4.1-Gamma (archive + push at notable moments) inherits from A1 spec §1 election and A2 spec §1 inheritance.** A3's push triggers are sub-shape-specific (cross-era record updates) — distinct content from A1's and A2's triggers but same shape. (§6.4)
- **A3's per-year update rhythm is single-phase (end-of-NFL-season), structurally similar to A1's.** Cleaner than A2's two-phase rhythm. (§8.1)
- **A3's substrate-maturity at its selection-prep moment is the highest of any Phase 11 candidate.** A1 production-rendered at `642d6dc`; the playoff-detection trick is empirically validated end-to-end. (§10.1)

### 11.3 Medium-confidence claims

- **D4.2 election is genuinely open between Alpha (NFL W1; cross-surface consistency with E1) and Beta (end-of-NFL-season; A3-and-A1 substance-honesty coherence).** The chat-session recommendation surfaces both as legitimate election candidates rather than defaulting to Alpha inheritance silently. The substance-honesty argument for Beta is materially stronger than A2's analogous Gamma argument was, because end-of-NFL-season has cross-surface coherence with A1 that auction-night did not have. Founder elects at Step 2. (§6.4, §8.2)
- **Regular-season vs playoff splits (§4.2.3) is the most-defensible "+ extension" beyond the trio** if the founder wants a four-sub-shape v1. D45 already cross-season; no additional D2 dependency. (§7.1)
- **The 2021 format-shift now affects three surfaces (A1, A2, A3) — candidate for cross-surface common treatment.** Recorded as input for template v1.x revision; A3's spec session still does its own §6.x disposition pending. (§10.1)
- **Repeat-bracket-meeting patterns (§4.2.5) has cross-link consideration with F1's RIVALRY substrate.** Co-existence admissible; cross-surface presentation conventions worth coordinating at F1's selection-prep when it becomes next-eligible. (§4.2.5, §4.3)
- **§4.2.6 (title-game records / closeness) is materially absorbed by A1's championship-roll table.** The closeness-margin sub-leaderboard is the only defensibly-new dimension; folds into §4.2.2 as a sub-leaderboard at Step 2 election. (§4.2.6, §7.1)

### 11.4 Medium-low confidence claims / limitations to flag

- **A3's §9.2 artisan-frame fit at v1 trio is "highest in the catalog" for §4.2.4 (bridesmaids and almosts) specifically; "high" for the trio overall.** §9.2 fit for §4.2.3 / §4.2.5 / §4.2.6 is medium-high (per-franchise time-allocation; repeat-meeting patterns; closeness ranking are more analytical-than-affectionately-remembered). The trio's §9.2 fit is strong; the broader catalog's §9.2 fit is uneven. Worth flagging at decision-readiness as a tension if Step 2 elects an analytical-heavy "+ extension." (§4.2, §7.1)
- **D4.2-Beta substance-honesty argument may carry materially more weight at Step 2 than the chat-session recommendation positions.** A2's D4.2 election was for cross-surface consistency, and the A2 Step 2 framing-memo opted for Alpha; the founder may legitimately prioritize A3's substance-honesty + A1-coherence more highly. The chat-session's D4.2-Alpha-by-inheritance recommendation may be amended at Step 2. (§6.4, §8.2)
- **The runner-up cross-era aggregation in §4.2.4 is small new work, not a lift.** Substrate-readiness for §4.2.4 is "medium-high" rather than "high" because of this. D1 probe confirms or qualifies. (§4.2.4, §10.2)
- **A3's bracket-presentation must handle the 2-week-playoff and 3-week-playoff seasons in the same render.** Spec-session render-disposition concern; not blocking for selection-prep but recorded for spec session. (§10.1)
- **F1 cross-link consideration on §4.2.5 (repeat-bracket-meeting patterns) is a soft future-coordination question.** F1's selection-prep at next-eligibility will need to consider what §4.2.5 has shipped; this memo does not pre-decide F1's RIVALRY-substrate scope. (§4.2.5, §9.3)

---

## 12. The point

E1 shipped (`9093a07`). A1 shipped (`cddcfb5` + implementation arc through `642d6dc`). A2 shipped (`ee671da` + implementation arc through `9189a7d`). Template v1.0 shipped (`5291c46`). A3's selection-prep is the **first invocation of the chain pattern with three registered surface precedents AND the framework template in place AND the cluster's parent surface (A1) production-rendered at the substrate A3 depends on.**

What this memo adds to the Phase 11 surface-track:

- A **substrate-grounded candidate sub-shape enumeration** for A3 — six sub-shapes characterized against the D36-D50 detector family (specifically D39 / D45 / D46 / D50) plus the playoff-detection trick at Architectural Audit §8 #3, with overlap with A1 / A2 named explicitly. **A3 introduces the cluster's first shared-primitive-different-presentation boundary case** (with A1's championship roll), substrate-clean per the §3.1 absorption-finding characterization.
- **The A1-A3 absorption finding made concrete** against A1's live `championship_roll.md` content at HEAD `9189a7d`. A3's framing post-A1-shipping is no longer just "the full playoff-bracket presentation A1's column did not cover" in the abstract; the boundary is operationalized against the two specific tables A1 ships (Champions by Season; Titles by Franchise) and the substrate primitive (`compute_championship_roll`) both surfaces share.
- The **cluster-A surface-vs-meta-surface question carried forward by two-spec precedent** — A1 Reading 1 at `cddcfb5`, A2 inheritance at `ee671da`. The inheritance is doctrinal-stable; no re-litigation; explicit recording.
- A **registered set of five diagnostics** (D1 substrate-coverage; D2 playoff-week coverage with 2021-format-shift carry-forward; D3 GAF / lore-pick framing with D3-Alpha inheritance leading; D4 operational rhythm with the substantively-different D4.2-Beta end-of-NFL-season alternative; D5 meta-surface dissolved by inheritance) — each with named gating criteria for decision-readiness.
- A **two-tier disposition**: leading-hypothesis on the within-A3 v1 sub-shape trio (per-season playoff bracket + cross-season playoff records + bridesmaids-and-almosts); deferral on the four substantive diagnostics.
- An **operational rhythm framing** for a playoff-bracket-derived browseable-archival surface — same browse-cadenced shape as A1 and A2, single-phase update rhythm (end-of-NFL-season anchored), with the materially-stronger D4.2-Beta substance-honesty + A1-coherence argument surfaced for Step 2.
- **Cluster-A exhaustion as a structural carry-forward fact** — after A3 ships, no within-cluster Cluster A sub-question remains; the next selection chain operates entirely on cross-cluster sub-questions (E2-light / E3 / F1).
- **Side-findings registered** for future Roadmap revision (compound seasons-count drift), template revision (2021 format-shift cross-surface common treatment; D4.2 election as inheritance-vs-substance-honesty Step 2 dimension), and spec-session work (bracket-week-count disposition; F1 cross-link on §4.2.5 if F1 ships post-A3).

The chain advances. The Phase 11 surface track moves from "three surfaces shipped, template framework in place, two-spec cluster-A inheritance precedent" to "three surfaces shipped, candidate-set characterized and diagnostics registered for the fourth and final Cluster A surface." Next session in the chain: decision-readiness Step 1 (D1 + D2 empirical probes; structurally analogous to A2 Step 1 at `2da7f21`) and Step 2 (D3 + D4 framing; structurally analogous to A2 Step 2 at `d30a6a9`).

The Roadmap is not amended by this memo. The leading hypothesis (A3) carries forward. The within-A3 leading hypothesis (per-season bracket presentation + cross-season records + bridesmaids-and-almosts under Reading 1 inheritance) is anchor, not forcing — the founder's product judgment at decision-readiness Step 2 or specification adjudicates.

A3's specification session at chain step 3 will be **the second empirical exercise of template v1.0**. Per template §5.1, A3's spec records its §11 adaptations from template v1.0 (if any). If no adaptations, A3's spec advances template v1.0 promotion-eligibility per template §6 (combined with A2's spec at `ee671da`, A3's spec would make three clean exercises of template v1.0 — A2 spec §12.5 noted three clean exercises is the eligibility-marker). If substantive adaptations, a template v1.1 revision session sequences ahead of promotion. **This selection-prep does not author or commit to that §11 record; the spec session adjudicates.**

Build the fourth selection-prep. The pattern works; the template binds the spec downstream; the substrate is well-developed and A1-production-validated; the A1-A3 boundary is substrate-clean and operationalized against live archive content; the cluster's exhaustion is in view but not pre-committed.

---

## 13. Cross-references

- `bb0f325` — Reset Memo v1.0 (doctrinal source; §8.4 source-verified at Roadmap §6.1)
- `ac96447` — Documentation Map v1.6 (registry; Tier 0V — Vision Source)
- `46736a0` — Map v1.6 §4.2 patch
- `1cf4142` — Tier 5 Live Observation Cadence Doctrine v1.0 (filing precedent)
- `5a865a1` — Phase 11 surface-selection memo (parent; Cluster A admissibility source)
- `a1f4624` — Phase 11 decision-readiness memo (Cluster A carry-forward language)
- `9093a07` — Phase 11 first-surface specification for E1 (chain pattern precedent)
- `ba8b58a` — Phase 11 Surface Roadmap (A3 admissibility carry-forward; §4.1 four-memo chain pattern; §2.2 admissible-set source; §4.4 subsequent-surface conditions)
- `ba44ba4` — Phase 11 A1 selection-prep memo (structural precedent)
- `fb4f827` — A1 decision-readiness Step 1 (empirical probes; precedent for A3 Step 1; playoff-detection trick empirical validation source)
- `582c3cf` — A1 decision-readiness Step 2 (framing analysis; precedent for A3 Step 2)
- `cddcfb5` — Phase 11 A1 specification (Reading 1 election; D3-Alpha; D4.1-Gamma; D4.2-Alpha; D5-Gamma — all inherited by A3 unless explicit founder direction reopens; §1, §3.1, §3.3, §3.7, §9.1 precedents)
- `eb6042d` / `97c8bf0` / `642d6dc` — A1 implementation arc (A1 production-rendering source; `championship_roll.md` substrate for §3.1 absorption-finding)
- `5291c46` — Per-surface constitutional-memo template v1.0 + skeleton (binds A3's spec at chain step 3; does not bind this selection-prep)
- `3e9065f` — Phase 11 A2 selection-prep memo (**direct structural precedent**)
- `2da7f21` — A2 decision-readiness Step 1 (empirical probes; precedent for A3 Step 1)
- `d30a6a9` — A2 decision-readiness Step 2 (framing analysis; precedent for A3 Step 2)
- `ee671da` — Phase 11 A2 specification (Reading 1 inheritance re-confirmation; second registered per-surface constitutional memo; §9.1 A3 carry-forward; §1 inheritance shape)
- `87ebdad` / `4f9c379` / `9189a7d` — A2 implementation arc (A2 operationally complete; HEAD at memo-write)
- `PFL_Buddies_Voice_Profile_v1_0.md` §5 — A3 §9.2 anchor (playoff and championship-bracket language patterns)
- `Platform_and_Writers_Room_Compact_v1_0.md` — niche-generality framing for the D4.2-Beta end-of-NFL-season anchor
- `ARCHITECTURAL_AUDIT_2026_04_16.md` §8 entanglement hotspot #3 — playoff-detection trick characterization (three call sites already; A3 becomes the fourth consumer of the same primitive)
- `Narrative_Angles_v2_Definitive_Scope.md` Dimension 9 — D36-D50 franchise-history detector family scope source
- `src/squadvault/core/recaps/context/franchise_deep_angles_v1.py` lines 1248-1468 — D39 / D45 / D50 detector implementations; structural reads this memo
- `src/squadvault/core/recaps/context/hall_of_fame_aggregations_v1.py` lines 220-317 — `compute_championship_roll`; A1's playoff-detection-trick pure-derivation companion; structural read this memo; the substrate primitive A3 generalizes for §4.2.1 bracket presentation
- `archive/hall_of_fame_and_shame/championship_roll.md` (`642d6dc`) — A1's live championship roll; A3-A1 boundary substrate working-tree-confirmed for §3.1

---

*Filing: `_observations/OBSERVATIONS_2026_05_14_PHASE_11_A3_SELECTION_PREP.md`.*
*Provisional / observational per session-brief Shape. No tier. No Map registration. Matches Tier 5 doctrine precedent at `1cf4142` and predecessor memo filings at `5a865a1` / `a1f4624` / `9093a07` / `ba8b58a` / `ba44ba4` / `cddcfb5` / `5291c46` / `3e9065f` / `ee671da`.*
