# Phase 11 Surface Roadmap — Seasons-Count Revision

**Date:** 2026-05-14
**Status:** Provisional / observational. No tier. Not registered in Documentation Map. **A Roadmap revision per Roadmap §8.5 / §8.6** — an append-only new dated memo that amends the Roadmap by supersession-of-reference, not a silent edit and not a Roadmap v-next. Filed alongside `OBSERVATIONS_2026_05_10_PHASE_11_ROADMAP.md`.
**Filing precedent:** Tier 5 Live Observation Cadence Doctrine at `1cf4142`; Roadmap §7.2's "finding recorded, not a pending edit" disposition (the structural precedent for this memo's shape).

**HEAD at authoring:** `38ddcd2` (A3 specification).

**Predecessors:**

- `ba8b58a` — Phase 11 Surface Roadmap (the memo this revision amends; §2.2 lines 61-62 and §3 line 101 carry the "17 seasons" figure)
- `fb4f827` — A1 decision-readiness Step 1 (§4.2 — first empirical correction: digital era is 16 seasons, not 17)
- `642d6dc` — A1 initial archive generation (committed as "16 seasons, 2010-2025" — the corrected count is already in the A1 archive commit)
- `3e9065f` — A2 selection-prep (§10.1 — A2's structural-read scope is 8 seasons, not the digital era's count)
- `2da7f21` — A2 decision-readiness Step 1 (§4.1 D2-α — A2's auction substrate is empirically 7 seasons; §4.4 D2-δ — FAAB substrate begins 2021, cross-substrate window is 4 seasons)
- `9189a7d` — A2 initial archive generation (committed as "7 seasons, 2018-2025")
- `24e63fa` — A3 selection-prep (§10.1 — added A3's data point to the seasons-count drift family)
- `1e7b59d` — A3 decision-readiness Step 1 (§4.1 D2-α — empirically confirmed the digital era is 16 seasons, 1,182 matchups, no gaps; §4.2 D2-β — the 16-season era splits 11 pre-2021 / 5 post-2021)
- `38ddcd2` — A3 specification (§11 anchor-election-agnosticism finding; §9.1 cluster-A exhaustion — both registered for the Roadmap's next full revision below)

**Output:** The Phase 11 Surface Roadmap (`ba8b58a`, 2026-05-10) carries the figure "17 seasons" in three places — §2.2 line 61 (A2), §2.2 line 62 (A3), and §3 line 101 (the cluster-A demo framing). The Roadmap was authored before the A1, A2, and A3 decision-readiness chains ran their empirical Step 1 probes; "17" was a legacy approximation that predated empirical verification. The empirically-confirmed figures are: **the digital era is 16 seasons (2010-2025)**; **A1's surface scope is 16 seasons**; **A2's surface scope is 7 seasons (2018-2025 minus the 2021 auction-substrate gap)**; **A3's surface scope is 16 seasons**; **the cross-substrate FAAB window is 4 seasons (2022-2025)**. This memo records the compound drift, the reconciled figures, the conceptual correction underneath the drift, and what is superseded — the three Roadmap "17 seasons" mentions. It also registers four A3-chain side-findings for the Roadmap's next full revision. The drift is confined to three descriptive mentions and affects no Roadmap decision or sequencing; this is a supersession-of-reference memo, not a Roadmap v-next.

---

## 1. What this memo is, and is not

**It is** a Roadmap revision per Roadmap §8.6: *"Roadmap revisions are append-only at the artifact layer — new dated memos that amend or supersede this one, not silent edits."* It supersedes three specific descriptive figures in the Roadmap by reference; the Roadmap text retains its original content with this memo as the superseding record.

**It is not** a Roadmap v-next. The drift is confined to three descriptive season-count mentions and affects no Roadmap decision, no sequencing axis, no admissibility screen, and no framework-artifact or closure provision (see §6). A full Roadmap re-authoring is not warranted. The structural precedent is Roadmap §7.2's "Re-classified — finding recorded, not a pending edit" disposition for the Operational Plan duration drift: a derivative-memo drift, with an append-only source that cannot be silently patched, affecting no decision, gets recorded as a finding rather than triggering a re-authoring. This memo is the same shape.

**It is not** a re-adjudication of any Phase 11 surface. E1, A1, A2, and A3 are all registered; their selections, scopes, and specifications stand. The seasons-count figures *within* the A1, A2, and A3 chains were already corrected memo-by-memo as the chains ran (see §2); this memo reconciles those per-chain corrections against the Roadmap, which predates all of them.

**Confidence on the framing:** **High.**

---

## 2. The compound drift

The Roadmap (`ba8b58a`) was authored 2026-05-10, at the start of the Phase 11 surface track, before any surface's decision-readiness Step 1 probe had run an empirical seasons-count. It carried "17 seasons" as the league's digital-history figure — a legacy approximation (the project's original framing was "~17 seasons of digital records," with the tilde signalling it was never an exact count).

As the A1, A2, and A3 chains ran, each chain's empirical work refined the count — but each refined it for a *different scope*, and none of the refinements propagated back to the Roadmap. The result is a compound drift: a sequence of per-chain corrections, each correct for its own scope, none reconciled against the Roadmap's flat "17."

| Chain memo | §-location | Correction made | Scope |
|---|---|---|---|
| A1 Step 1 (`fb4f827`) | §4.2 | 17 → **16** | The digital era (2010-2025) is 16 seasons, not 17. |
| A1 archive (`642d6dc`) | commit subject | "16 seasons, 2010-2025" | The corrected digital-era count is already in the A1 archive commit. |
| A2 selection-prep (`3e9065f`) | §10.1 | 16 → **8** | A2's *structural-read* scope is 8 seasons — A2 covers only the auction era (2018-2025), not the full digital era. |
| A2 Step 1 (`2da7f21`) | §4.1 (D2-α) | 8 → **7** (empirical) | A2's auction substrate is empirically 7 seasons — 2021 has zero `DRAFT_PICK` events (cause uncharacterized: snake-format-2021, a different event_type, or an ingest gap). |
| A2 Step 1 (`2da7f21`) | §4.4 (D2-δ) | — → **4** (cross-window) | The FAAB substrate begins 2021, narrowing the cross-substrate overlap window to 4 seasons (2022-2025). |
| A2 archive (`9189a7d`) | commit subject | "7 seasons, 2018-2025" | A2's corrected auction-era count is in the A2 archive commit. |
| A3 selection-prep (`24e63fa`) | §10.1 | — | Added A3's data point to the seasons-count drift family; flagged the Roadmap revision sweep as touched by every selection-prep. |
| A3 Step 1 (`1e7b59d`) | §4.1 (D2-α) | confirms **16** | Empirically confirmed the digital era is 16 seasons — 1,182 `WEEKLY_MATCHUP_RESULT` matchups, no inter-season gaps, no intra-season week gaps. |
| A3 Step 1 (`1e7b59d`) | §4.2 (D2-β) | 16 = **11 + 5** | The 16-season digital era splits into two bracket-shape eras: 11 seasons pre-2021 (3-round bracket) and 5 seasons post-2021 (4-round bracket). |

The drift is "compound" in the precise sense that it is not a single off-by-one — it is a set of distinct, individually-correct refinements for distinct scopes, none of which the Roadmap's flat "17" reconciles. Two independent confirmations (A1 Step 1 and A3 Step 1) establish the digital era at 16; A2's chain establishes that A2's *surface* scope is a different number (7) than the digital era because A2's substrate covers a sub-window.

**Confidence on the drift characterization:** **High.** Each correction is recorded in its chain memo at the §-location named; the A1 and A3 archive commits carry the corrected counts in their commit subjects.

---

## 3. The reconciled figures

The empirically-confirmed figures, as of HEAD `38ddcd2`:

- **The digital era: 16 seasons (2010-2025).** This is the league's substrate-derivable history — the span over which `canonical_events` carry data. Confirmed twice independently: A1 Step 1 §4.2 and A3 Step 1 §4.1 (D2-α). The "17" figure was a legacy approximation; the substrate-derivable digital era is 16 seasons (2010 through 2025 inclusive).

- **A1's surface scope: 16 seasons (2010-2025).** A1 (Hall of Fame & Shame) consumes `WEEKLY_MATCHUP_RESULT` substrate, which is complete across the full digital era. A1's archive commit (`642d6dc`) is titled "16 seasons, 2010-2025."

- **A2's surface scope: 7 seasons (2018-2025 minus 2021).** A2 (Draft History Vault) consumes `DRAFT_PICK` substrate, which exists only for the auction era (2018 onward) and has a confirmed gap at 2021 (zero `DRAFT_PICK` events; cause uncharacterized). A2's archive commit (`9189a7d`) is titled "7 seasons, 2018-2025." A2's *structural-read* scope was 8 (the nominal auction era 2018-2025); its *empirical* scope is 7 (the 2021 gap removes one season).

- **A3's surface scope: 16 seasons (2010-2025).** A3 (Championship Timeline) consumes `WEEKLY_MATCHUP_RESULT` substrate via the playoff-detection trick, which is complete across the full digital era. A3 Step 1 §4.1 (D2-α) confirmed 16 seasons with no gaps. The 16 splits 11 pre-2021 (3-round bracket) + 5 post-2021 (4-round bracket) per A3 Step 1 §4.2 (D2-β).

- **The cross-substrate FAAB window: 4 seasons (2022-2025).** The FAAB-waiver substrate begins 2021 (A2 Step 1 §4.4, D2-δ); combined with the 2018-onward auction substrate and the 2021 `DRAFT_PICK` gap, the window where auction and FAAB substrates overlap is 2022-2025 — 4 seasons. This figure is relevant only to cross-substrate sub-shapes (none in any current v1 scope; recorded for completeness).

**Confidence on the reconciled figures:** **High** for the digital-era count (16, twice-confirmed), A1's scope (16), A2's scope (7, with the archive commit as corroboration), and A3's scope (16). **Medium-high** for the cross-substrate FAAB window (4) — the figure follows arithmetically from D2-δ, but no current surface consumes it, so it has not been exercised.

---

## 4. What is superseded

The following three Roadmap figures are superseded. Per Roadmap §8.6, the Roadmap text is not silently patched; this memo supersedes the figures by reference.

- **Roadmap §2.2 line 61** — *"**A2 — Draft History Vault.** Auction prices, draft positions, value-vs-cost across 17 seasons of digital history."* **Superseded.** A2's surface scope is **7 seasons** (the auction era, 2018-2025, minus the 2021 gap). The league's digital era is 16 seasons, but A2's *surface* presents the 7-season auction era — A2 does not present "17 seasons of digital history," nor 16; it presents the auction sub-window.

- **Roadmap §2.2 line 62** — *"**A3 — Championship Timeline.** Playoff brackets and outcomes across the 17 seasons."* **Superseded.** A3's surface scope is **16 seasons** (the full digital era, 2010-2025) — the playoff-bracket substrate is complete across the digital era.

- **Roadmap §3 line 101** — *"Cluster A leads on 'demonstrates what SquadVault IS to a first-time observer' (17 seasons rendered browseably is the demo)."* **Superseded.** The demo is **16 seasons** rendered browseably — the digital era. More precisely: the cluster-A surfaces render 16 (A1), 7 (A2), and 16 (A3) seasons respectively, per their distinct substrate scopes (see §5). The "first-time observer" demo framing is unaffected in substance — a browseable 16-season archive is still the demo; only the figure is corrected from 17 to 16.

**Confidence on the supersession scope:** **High.** A `grep` for "17" against the Roadmap returns exactly these three lines; they are the complete set of superseded figures.

---

## 5. The conceptual correction underneath the drift

The drift is not only "17 should be 16." Underneath it is a conflation worth recording, because it is the kind of conflation that recurs.

The Roadmap attached **a single seasons-count number to all of cluster A** — "17 seasons" appears at A2 (line 61), A3 (line 62), and the cluster-A demo framing (line 101), as though one number described the cluster. But the cluster-A surfaces have **different substrate scopes**:

- A1 and A3 consume `WEEKLY_MATCHUP_RESULT` substrate, which is complete across the full 16-season digital era. Their surface scope is 16.
- A2 consumes `DRAFT_PICK` substrate, which exists only for the auction era and has a 2021 gap. Its surface scope is 7.

So the correction is two-layered:

1. **The digital-era figure is 16, not 17.** (A legacy-approximation correction.)
2. **No single seasons-count number describes cluster A.** Each surface's scope is set by *which canonical event type it consumes* and *how far back that substrate extends* — not by "the league's history" as a flat figure. A1 and A3 happen to share a scope (16) because they share a substrate family (`WEEKLY_MATCHUP_RESULT`); A2 differs (7) because it consumes a different, shorter-spanned substrate (`DRAFT_PICK`).

The Roadmap's flat "17 seasons" obscured both layers. This memo records the corrected digital-era figure (16) *and* the per-surface scopes (16 / 7 / 16) so that the per-surface distinction is explicit and does not have to be re-derived.

A note on provenance: this is one of two independent drift-corrections filed the same session (2026-05-14). The other — the A2 Cavallini/Mahomes anchor revocation (`OBSERVATIONS_2026_05_14_PHASE_11_A2_ANCHOR_REVOCATION.md`) — is a distinct topic (a player-identity misidentification within A2's content) and is not connected to the seasons-count drift. Both are recorded here only to note that 2026-05-14 was a correction-consolidation session; the two memos are independent and separately scoped.

**Confidence on the conceptual correction:** **High.** The per-surface-scope distinction is grounded in the substrate facts (which event type each surface consumes; how far back each substrate extends), all of which are empirically established in the A1/A2/A3 Step 1 probes.

---

## 6. What is NOT affected

The drift is confined to three descriptive figures. The following Roadmap content is unaffected — none of it depends on the seasons-count figure:

- **The surface inventory (§2).** A1, A2, A3 are correctly inventoried as cluster-A surfaces; E1 is correctly inventoried as shipped; the admissibility screens (§2.2 — Tone Engine boundary, social-surface-vs-network, No-New-Foundations, certifications, §9.2 fit) are unaffected. (The §2.1/§2.2 *shipped-vs-admissible split* should be refreshed at the Roadmap's next full revision to reflect that A1/A2/A3 are now all registered — but that is a registration-status update, not a seasons-count correction; it is registered in §8 below.)
- **The sequencing axes (§3).** The Axis I / Cluster A leading-hypothesis reasoning at line 101 is unaffected in substance — a browseable digital-era archive is still the "demonstrates-what-SquadVault-IS" demo; only the figure (17 → 16) is corrected.
- **The chain pattern (§4.1).** The four-memo chain pattern is unaffected.
- **The framework-artifact sequencing (§5).** Unaffected.
- **The closure certifications (§6).** Unaffected.
- **The anti-drift provisions (§8).** Unaffected — including, notably, §8.6, which is the provision *under which this memo is filed*.

The drift affected zero Roadmap decisions, zero sequencing, zero admissibility adjudications. It was three descriptive figures. This is precisely what bounds the revision to a supersession-of-reference memo rather than a Roadmap v-next.

**Confidence on the not-affected scope:** **High.**

---

## 7. Why supersession-of-reference, not a Roadmap v-next

Per Roadmap §8.6, Roadmap revisions are append-only new dated memos. The question is whether the seasons-count drift warrants a full Roadmap v-next (a re-authored Roadmap document) or a supersession-of-reference memo (this memo, amending three figures by reference).

The disposition is **supersession-of-reference**, on three grounds:

1. **The drift is confined to three descriptive figures** (§4) and affects no Roadmap decision, sequencing, or screen (§6). A re-authoring would reproduce the entire Roadmap to change three numbers.
2. **The structural precedent is Roadmap §7.2.** When the Roadmap found the Operational Plan duration drift, it recorded the disposition as "finding recorded, not a pending edit" — because the source was append-only, the drift affected no decision, and a re-authoring was not warranted. The seasons-count drift is the same shape: an append-only source (the Roadmap itself, per §8.6), a drift affecting no decision, no re-authoring warranted.
3. **The Roadmap's next scheduled revision-point folds it in.** Roadmap §8.5 sets the Roadmap's revision-point at NFL Week 1 (~2026-09-08). At that point — or at any future Roadmap v-next — the corrected figures from this memo (and the side-findings in §8 below) fold into the re-authored Roadmap. Until then, this memo is the superseding record for the three figures.

**Confidence on the disposition:** **High** — the §7.2 precedent is directly on point.

---

## 8. A3-chain side-findings registered for the Roadmap's next full revision

The A3 chain (`24e63fa` → `1e7b59d` → `3281a37` → `38ddcd2`) surfaced four findings that are **Roadmap-relevant but not seasons-count drift.** They are **registered here for the Roadmap's next full revision** — they are *not* superseded-by-reference like the §4 figures, because they touch Roadmap content that genuinely warrants a re-authoring-time decision rather than a figure-correction. They are recorded so the Roadmap's next full revision (NFL Week 1, or a v-next) does not have to rediscover them.

1. **Anchor-election-agnosticism (A3 spec §11).** A3 elected D4.2-Beta (end-of-NFL-season revision-point anchor) where E1, A1, and A2 elected D4.2-Alpha (NFL Week 1). The Roadmap §8.5 sets the *Roadmap's own* revision-point at NFL Week 1, which is unaffected — but the Roadmap's broader framing treats NFL Week 1 as a shared anchor across the surface track. A3 is the empirical proof that per-surface revision anchors may diverge. At the Roadmap's next full revision, the surface-track framing should note that per-surface revision anchors are a per-surface election, not a shared constant. (A3 spec §11 recorded this as a template-promotion-eligibility reinforcement — the per-surface constitutional-memo template's §8 structure is anchor-election-agnostic; the same finding is Roadmap-relevant for the surface-track framing.)

2. **D50 silent across production history (A3 Step 1 §6.2 / A3 spec §3.7).** D50 (`detect_the_almost`)'s production threshold (`min_times=3`) produces zero angles across PFL Buddies' entire 16-season substrate — the detector has never fired in production. A3's spec dropped the D50-derived "almost leg" from its v1 Bridesmaids sub-shape on substrate-thinness grounds. D50 is a candidate for either a calibration revisit or an unfit-for-purpose finding. Register for the Roadmap's standing-items (§7.3) at its next full revision — it is a substrate/detector finding, not a surface-track decision, but it belongs in the Roadmap's standing-items inventory.

3. **D39 per-matchup over-counting (A3 Step 1 §6.3 / A3 spec §6.3).** D39 (`detect_championship_history`)'s internal `playoff_appearances` dict increments per-matchup rather than per-season; the over-counting is silent because D39's surfaced angles never read the dict. A3's spec §6.3 binds A3's implementation against inheriting the over-counting. This is a substrate-side finding recorded for visibility; it is not Roadmap-load-bearing, but it belongs in the Roadmap's standing-items inventory at its next revision so the finding is not lost.

4. **Cluster A is exhausted (A3 spec §9.1).** With A3 registered, cluster A is complete — E1, A1, A2, A3 are all registered Phase 11 surfaces. The Roadmap's §2.1/§2.2 split (E1 shipped; A1/A2/A3 admissible-sequenced-behind-E1) is now stale: at the Roadmap's next full revision, A1/A2/A3 move from §2.2 (admissible) to §2.1 (shipped/registered), and the §2.2 admissible-set reduces to E2-light, E3 (cluster E), and F1 (substrate-readiness-gated). The post-A3 admissible-surface-set is **E2-light / E3 / F1** per A3 spec §9.5.

These four findings are **registered, not superseded** — they await the Roadmap's next full revision for the re-authoring-time decisions they imply. This memo records them so that revision does not have to rediscover them.

**Confidence on the registered side-findings:** **High** that each finding is correctly characterized and Roadmap-relevant; the disposition (register for next full revision, do not supersede-by-reference) is the §7.2-consistent call — these findings touch Roadmap structure (§2.1/§2.2 split, surface-track framing, standing-items inventory) that warrants a re-authoring-time decision, unlike the §4 figures which are pure descriptive corrections.

---

## 9. Confidence labeling

### 9.1 Highest-confidence claims

- The digital era is 16 seasons (2010-2025), not 17 — twice independently confirmed (A1 Step 1 §4.2, A3 Step 1 §4.1). (§3)
- A1's surface scope is 16 seasons; A3's surface scope is 16 seasons; A2's surface scope is 7 seasons — each grounded in which canonical event type the surface consumes and how far back that substrate extends. The A1 and A2 archive commits (`642d6dc`, `9189a7d`) carry the corrected counts in their commit subjects. (§3)
- The three superseded Roadmap figures (§2.2 lines 61-62, §3 line 101) are the complete set — a `grep` for "17" against the Roadmap returns exactly these three. (§4)
- The drift affects no Roadmap decision, sequencing, or screen — it is confined to three descriptive figures. (§6)
- The supersession-of-reference disposition (not a Roadmap v-next) is the §7.2-precedent-consistent call. (§7)

### 9.2 Medium-high confidence claims

- The cross-substrate FAAB window is 4 seasons (2022-2025) — the figure follows arithmetically from D2-δ, but no current surface consumes it, so it has not been exercised. (§3)
- "17" was a legacy approximation predating empirical verification — the project's original "~17 seasons" framing supports this, but the exact origin of the "17" (off-by-one, a pre-digital-inclusive count, or a loose approximation) is not characterized and does not need to be. (§2, §5)

### 9.3 Claims this memo deliberately does not make

- No Roadmap v-next. The Roadmap text is not re-authored; three figures are superseded by reference. (§1, §7)
- No silent edit of the Roadmap. Per §8.6, the Roadmap retains its original text with this memo as the superseding record. (§1)
- No re-adjudication of any Phase 11 surface. E1, A1, A2, A3 selections and specifications stand. (§1)
- No characterization of the 2021 `DRAFT_PICK` gap cause. The gap is empirically confirmed (A2 Step 1 §4.1); its cause (snake-format-2021, a different event_type, or an ingest gap) is uncharacterized and is not this memo's to resolve. (§2)
- No re-authoring-time decisions on the four registered side-findings (§8). They are registered for the Roadmap's next full revision; the decisions they imply belong to that revision.

### 9.4 Side-findings recorded within this memo

- **The conceptual correction underneath the drift** (§5) — no single seasons-count number describes cluster A; each surface's scope is set by its substrate. This is the reusable lesson; the figure-correction (17 → 16) is the surface symptom.
- **2026-05-14 was a correction-consolidation session** — two independent drift-corrections were filed (this memo and the A2 anchor revocation); they are separately scoped and not connected. (§5)
- **The Roadmap's §2.1/§2.2 shipped-vs-admissible split is stale** post-A3 (§8 finding 4) — registered for the next full revision; not superseded here because it is a structural update, not a figure-correction.

---

## 10. Cross-references

- `ba8b58a` — Phase 11 Surface Roadmap (the memo this revision amends; §2.2 lines 61-62 and §3 line 101 superseded; §7.2 the structural precedent for this memo's shape; §8.5 / §8.6 the revision discipline this memo is filed under)
- `fb4f827` — A1 decision-readiness Step 1 (§4.2 — first empirical correction, 17 → 16)
- `642d6dc` — A1 initial archive generation ("16 seasons, 2010-2025")
- `3e9065f` — A2 selection-prep (§10.1 — A2 structural-read scope is 8 seasons)
- `2da7f21` — A2 decision-readiness Step 1 (§4.1 D2-α — A2 empirical scope is 7 seasons; §4.4 D2-δ — FAAB cross-window is 4 seasons)
- `9189a7d` — A2 initial archive generation ("7 seasons, 2018-2025")
- `24e63fa` — A3 selection-prep (§10.1 — added A3's data point; flagged the Roadmap revision sweep)
- `1e7b59d` — A3 decision-readiness Step 1 (§4.1 D2-α — confirmed 16 seasons, 1,182 matchups, no gaps; §4.2 D2-β — 16 = 11 pre-2021 + 5 post-2021)
- `3281a37` — A3 decision-readiness Step 2
- `38ddcd2` — A3 specification (§11 anchor-election-agnosticism; §9.1 cluster-A exhaustion; §9.5 post-A3 admissible-set — all registered in §8 for the Roadmap's next full revision)
- `1cf4142` — Tier 5 Live Observation Cadence Doctrine v1.0 (filing precedent)
- `OBSERVATIONS_2026_05_14_PHASE_11_A2_ANCHOR_REVOCATION.md` — a companion 2026-05-14 correction memo addressing a separate, unconnected drift (the A2 Cavallini/Mahomes player-identity misidentification); filed the same session, distinct topic

---

*Filing: `_observations/OBSERVATIONS_2026_05_14_PHASE_11_ROADMAP_SEASONS_COUNT_REVISION.md`.*
*Provisional / observational. No tier. No Map registration. A Roadmap revision per Roadmap §8.5 / §8.6 — supersession-of-reference, not a v-next.*
