# SquadVault Architectural Audit — 2026-04-16

**Repo:** github.com/weichert/squadvault
**HEAD at audit:** `04dc70a` (*Phase 10 observation: Writing Room surfacing audit*)
**Auditor note:** The originating prompt referenced `b9f495c` as HEAD. Actual HEAD is ~20 commits ahead, including verifier categories 7 (PLAYER_FRANCHISE) and 8 (FAAB_CLAIM), migration `0009_add_prompt_text_to_prompt_audit`, and tenure-scoped rivalry changes. This audit reflects actual HEAD.

---

## Preface — scope, confidence, method

This is a read-only audit. No code was modified. Findings distinguish **sport-specific** (would be thrown away or rewritten for a second module, e.g., fantasy golf) from **sport-agnostic** (would be reused as-is by any future fantasy module), with **MIXED** for files that contain both and **INFRASTRUCTURE** for governance plumbing that sits above both.

Confidence levels are noted inline per section. Where classification is uncertain, **UNCLEAR** is used rather than a guess. Where there is no clean answer, the finding says so plainly rather than manufacturing one.

The most important meta-finding, stated up front so it cannot be missed: **the sport-specific/sport-agnostic boundary in SquadVault is organizational, not architectural.** Package names and docstrings invoke "platform" and "module" language, but there is no runtime seam — no adapter protocol, no module registry, no dependency inversion — that would let a second module be plugged in without direct edits to `core/` code. The contract cards describe a platform. The code is a carefully-governed fantasy football monolith. This is not necessarily wrong; it may be the right state for a project that has been explicit about YAGNI and about prioritizing governance over abstraction. But it should not be confused with having done platformization work that has not been done.

---

## Section 1 — Directory-level map

### Top-level repo

| Path | What lives here | Tag | Notes |
|---|---|---|---|
| `src/squadvault/` | All application code | — | See below for breakdown |
| `Tests/` | 116 test files + `Tests/recaps/writing_room/` subdir | INFRASTRUCTURE | Tests are mostly named after the module they cover; a few are cross-cutting gates (`test_architecture_gates_v1`, `test_governance_gates_v1`, `test_immutability_violation_gate_v1`) |
| `scripts/` | 129 top-level entries: 26 diagnose/verify/render scripts, ~60 CI gate/check shell and Python scripts, plus `_archive/`, `_graveyard/`, `_retired/` | MIXED | Diagnostic scripts are mostly football-shaped (`diagnose_purple_haze_series.py` is named after a PFL franchise). CI gates are generic. `_archive/patches/` and `_archive/shell_patches/` hold dozens of single-use patches from prior sessions — see Surprises |
| `fixtures/` | Test fixtures (not inspected in depth) | INFRASTRUCTURE | |
| `docs/` | Documentation directory | UNCLEAR | Not inspected; project knowledge documents are canonical |
| `_observations/` | Phase 10 observation reports (recently moved here per commit `4f73f0a`) | INFRASTRUCTURE | Governance observation archive — sport-agnostic concept |
| `artifacts/` | Generated artifact outputs | UNCLEAR | Not inspected |
| `.github/` | CI workflows | INFRASTRUCTURE | Not inspected in depth |
| `pyproject.toml`, `Makefile`, `requirements.txt` | Build config | INFRASTRUCTURE | |

### `src/squadvault/` top-level packages

| Path | LOC | What lives here | Tag |
|---|---:|---|---|
| `_retired/` | ~32K | `_retired/notion/` — Notion integration scaffolding (client, properties, schema_specs, schema_validator) | MODULE (dead/retired) |
| `ai/` | ~36K, 2 files | `creative_layer_v1.py` (496 LOC), `creative_layer_rivalry_v1.py` (244 LOC). System prompts and Anthropic API wrappers. | MIXED — the "governed LLM call" skeleton is platform-general; every voice rule, every banned phrase, and the entire tone of the system prompt is fantasy football |
| `chronicle/` | ~43K, 6 files | Rivalry chronicle generation: input_contract, matchup_facts, generate, format, persist, approved_recap_refs | MODULE — "rivalry between two franchises with cross-season matchup history" is a head-to-head competition concept; fantasy golf has no rivalries in this shape |
| `config/` | ~7.5K | Presumably the `recap_event_allowlist_v1` referenced from `weekly_selection_v1.py` | UNCLEAR — not deeply inspected, but event-type allowlist is MODULE-scoped |
| `consumers/` | ~180K, 21 files | CLI entry-point wrappers: `recap_generate.py`, `recap_artifact_approve.py`, `recap_artifact_regenerate.py`, `recap_artifact_withhold.py`, `editorial_actions.py`, `recap_export_*.py`, `rivalry_chronicle_*_v1.py`, etc. | MIXED — the CLI shell + argparse + artifact/editorial workflow vocabulary is platform-general; the `recap_export_variants_approved.py` and `rivalry_chronicle_*` consumers are module-specific |
| `core/` | ~715K, largest package | See breakdown below | MIXED at the top level; see subdirs |
| `ingest/` | ~92K, 14 files at top + `franchises/`, `mfl/`, `players/` subdirs | Envelope derivation from MFL API payloads (auction_draft, matchup_results, player_scores, transactions, waiver_bids, nfl_bye_weeks, scoring_rules) | MODULE — every one of these files is named for an MFL endpoint or a football data type. Note `ingest/mfl/` is an empty-`__init__` package with no substance |
| `mfl/` | ~72K, 5 files | `client.py` (309 LOC), `discovery.py` (540 LOC), `historical_ingest.py` (760 LOC), plus two `_run_*` CLI wrappers | MODULE — MFL-platform-specific API client and orchestration |
| `ops/` | ~22K, 3 files | `approval_authority_v1.py` (lifecycle action validation), `contract_validation_strategy_v1.py`, `run_ingest_then_canonicalize.py` | PLATFORM for the first two; MODULE for the third (MFL-specific orchestration) |
| `recaps/` | ~131K | `weekly_recap_lifecycle.py` (1346 LOC), `preflight.py`, `dng_reasons.py`, `writing_room/` subdir, `_preview_angles.py` | MIXED — lifecycle is heavily fused with fantasy football detectors (Section 6); `writing_room/` is architected as platform-general but see Section 9 for its orphan status |
| `testing/` | ~5.5K | Test helper utilities | INFRASTRUCTURE |
| `utils/` | ~7.5K | General utilities including `http.py` retry helper | PLATFORM |
| `validation/` | ~20K, `signals/` subdir | `signal_taxonomy_type_a_v1.py` | UNCLEAR — Signal Scout adjacent; not used on the main lifecycle path |
| `errors.py` | ~1K | `RecapDataError`, `RecapNotFoundError`, `RecapStateError` | MIXED — names are "Recap" (module-shaped), purposes are platform-general |

### `core/` breakdown

| Path | What lives here | Tag |
|---|---|---|
| `core/storage/` | SQLite store, session, migrations, schema.sql, db_utils | PLATFORM for infrastructure; the canonical schema itself is MIXED (Section 2) |
| `core/canonicalize/` | `run_canonicalize.py` — memory→canonical deduplication runner | PLATFORM (the dedup algorithm is generic event-ledger behavior) |
| `core/eal/` | Editorial Attunement Layer — `editorial_attunement_v1.py`, `consume_v1.py`, `eal_calibration_v1.py` | PLATFORM — restraint-on-expression is sport-agnostic governance |
| `core/exports/` | `approved_weekly_recap_export_v1.py`, `approved_rivalry_chronicle_export_v1.py`, `season_html_export_v1.py` | MIXED — "export approved artifacts" is platform-general; the shapes being exported are module-specific. **Path note:** these sit under `core/` but are fantasy-football-module concerns. Probably a misplacement |
| `core/queries/` | `event_queries.py`, `franchise_queries.py`, `narrative_filters.py` | MIXED — `event_queries` is generic; `franchise_queries` and `narrative_filters` contain football-shaped assumptions. See Section 8 for `franchise_queries._franchise_ids_from_payload` reaching into `raw_mfl_json` |
| `core/recaps/` | Context/facts/render/selection/verification subpackages — the heart of the system | MIXED, heavily; see below |
| `core/recaps/context/` | 11 files, 8433 LOC — **every detector in the system** | MODULE (heavy) — see Section 3 |
| `core/recaps/facts/` | `extract_recap_facts_v1.py` | MIXED |
| `core/recaps/render/` | Deterministic bullet renderers | MIXED |
| `core/recaps/selection/` | `weekly_selection_v1.py`, `weekly_windows_v1.py`, `recap_selection_store.py` | MIXED — "weekly" cadence and the event-type allowlist are module assumptions, but the windowing + fingerprint machinery is generic |
| `core/recaps/verification/` | `recap_verifier_v1.py` (2843 LOC) | MIXED — see Section 4 |
| `core/tone/` | `tone_engine_v1.py`, `tone_profile_v1.py`, `voice_profile_v1.py` | PLATFORM — tone/voice governance is sport-agnostic, though banned phrases embedded in prompts are football-flavored |
| `core/versioning/` | `version_presentation_navigation_v1.py` | PLATFORM |
| `core/resolvers.py` | `FranchiseResolver`, `PlayerResolver`, `NameFn`, `identity` | MIXED — structure is generic (string→string name lookups) but `Franchise`/`Player` terminology is module-shaped |

---

## Section 2 — The data model

The canonical schema lives in `src/squadvault/core/storage/schema.sql` (391 lines) and is extended by nine numbered migrations in `core/storage/migrations/`. The schema.sql comment explicitly states: "This schema must match the fixture DB … Changes require versioned migration scripts." I compared the two and schema.sql reflects the state after migration 0009 (the `prompt_text` column on `prompt_audit` is present in both paths).

### Table-by-table assessment

| Table | Columns of note | Tag | Reasoning |
|---|---|---|---|
| `memory_events` | `league_id`, `season`, `external_source`, `external_id`, `event_type`, `occurred_at`, `payload_json` | **PLATFORM** | Pure append-only event ledger. Event-type vocabulary is not baked into the schema — it is a `TEXT` field. This is a clean, sport-agnostic memory layer. |
| `canonical_events` | `league_id`, `season`, `event_type`, `action_fingerprint`, `best_memory_event_id` | **PLATFORM** | Same reasoning. The deduplication semantics are content-agnostic. |
| `canonical_membership` | Join table | **PLATFORM** | |
| `v_canonical_best_events` (view) | | **PLATFORM** | |
| `franchise_directory` | `league_id`, `season`, `franchise_id`, `name`, `owner_name`, `raw_json` | **MIXED (leaning PLATFORM)** | The column names say "franchise" but the shape is generic: a per-season name-resolution table for team-like entities. A fantasy golf module would need the same shape with "team" or "entry" semantics. The name itself is MODULE-language, but the structure transfers. |
| `player_directory` | `league_id`, `season`, `player_id`, `name`, `position`, `team`, `raw_json` | **MIXED (leaning PLATFORM)** | `position` and `team` are neutral strings but carry clear football semantics ("QB" / "DAL"). Fantasy golf would reuse the shape but the semantics of `team` would need reinterpretation (tour? league affiliation?). |
| `recap_artifacts` | `artifact_type`, `state` (DRAFT/APPROVED/WITHHELD/SUPERSEDED), `version`, `selection_fingerprint`, `rendered_text`, `approved_at`, `withheld_reason` | **PLATFORM** | The governance state machine (draft→approve→supersede, withhold over speculate) is the sport-agnostic core. `WEEKLY_RECAP` is hardcoded as a default `artifact_type` value but the column tolerates other types. |
| `recap_runs` | `league_id`, `season`, `week_index`, `state`, `window_mode`, `selection_fingerprint`, `canonical_ids_json`, `counts_by_type_json`, `editorial_attunement_v1` | **MIXED** | `week_index` in the primary key hard-codes a weekly cadence. A module with a different cadence (daily fantasy, tournament-based fantasy golf) would not fit this table without schema change. |
| `recap_selections` | `week_index`, `selection_version`, `window_mode`, `fingerprint` | **MIXED** | Same reasoning — weekly cadence baked in. |
| `editorial_actions` | `artifact_kind`, `action` (OPEN/APPROVE/REGENERATE/WITHHOLD/NOTES), `actor`, `notes_md` | **PLATFORM** | The editorial workflow vocabulary is sport-agnostic. |
| `recap_verdicts` | `range_start`, `range_end`, `status`, `inputs_hash`, `payload_json` | **PLATFORM** | Generic decision ledger. |
| `league_tone_profiles` | `league_id`, `tone_preset` (TRASH_TALK/POINTED/BALANCED/FRIENDLY) | **PLATFORM** | Tone vocabulary is sport-agnostic. |
| `league_voice_profiles` | `league_id`, `profile_text`, `approved_by` | **PLATFORM** | |
| `nfl_bye_weeks` | `league_id`, `season`, `nfl_team`, `bye_week` | **MODULE** | Explicitly NFL. Feeds D51-D53 in `bye_week_context_v1.py`. Would not exist in any non-NFL module. |
| `league_scoring_rules` | `league_id`, `season`, `rules_json` | **MODULE** | Column name is neutral but the only consumer (`league_rules_context_v1.py`) parses it assuming PPR / passing-TD / scoring-position concepts. The JSON shape is MFL's scoring-rules export. |
| `prompt_audit` | `league_id`, `season`, `week_index`, `attempt`, `angles_summary_json`, `narrative_draft`, `verification_result_json`, `prompt_text` | **MIXED** | Same as `recap_runs`: `week_index` bakes in weekly cadence. Content of `angles_summary_json` refers to categories like `PLAYER_BOOM_BUST` which are football-specific. Shape transfers; content does not. |
| `prompt_audit_reverify` | `prompt_audit_id`, `verifier_tag`, `hard_failure_count`, `soft_failure_count` | **PLATFORM** | |

### Summary of schema mixing

- **Clean PLATFORM:** 10 tables / 1 view (memory/canonical/membership/view, editorial_actions, recap_verdicts, league_tone_profiles, league_voice_profiles, prompt_audit_reverify, recap_artifacts, v_canonical_best_events).
- **Clean MODULE:** 2 tables (`nfl_bye_weeks`, `league_scoring_rules`).
- **MIXED (shape PLATFORM, content or PK MODULE):** 5 tables (`franchise_directory`, `player_directory`, `recap_runs`, `recap_selections`, `prompt_audit`).

**Key structural finding:** The `week_index` primary-key convention in `recap_runs`, `recap_selections`, and `prompt_audit` is the schema-level expression of the "weekly cadence" assumption. Any module that does not process weekly (e.g., tournament-by-tournament, day-by-day, race-by-race) would either need new tables or these tables would need a generalized `period_index` column.

---

## Section 3 — The detector suite

This is the largest and most consequential section. The authoritative mapping lives in `src/squadvault/recaps/writing_room/prompt_audit_v1.py` as `CATEGORY_TO_DETECTOR`, which maps 50 detector categories (D1–D50, with D41 explicitly disabled) to source files. Three additional detector files emit categories that are **not** in this map — see Surprises (Section 9).

### Detector file assignment (by D-id)

The drift-detection test `test_category_to_detector_drift_detector` (in `Tests/recaps/writing_room/test_prompt_audit_v1.py`) scans **only three** files:

1. `core/recaps/context/player_narrative_angles_v1.py` (2188 LOC) → owns **D1–D19** (player scoring, cross-season lookups, player×matchup, trade, FAAB)
2. `core/recaps/context/auction_draft_angles_v1.py` (908 LOC) → owns **D20–D28** (auction)
3. `core/recaps/context/franchise_deep_angles_v1.py` (1584 LOC) → owns **D29–D50** (franchise scoring, bench/lineup, history/identity)

Plus, emitting categories with no D-id:

4. `core/recaps/context/narrative_angles_v1.py` (622 LOC) → emits UPSET, STREAK, SCORING_ANOMALY, BLOWOUT, NAIL_BITER, SCORING_RECORD, RIVALRY, STANDINGS_SHIFT — **the primordial matchup detectors**, not D-numbered.
5. `core/recaps/context/bye_week_context_v1.py` (341 LOC) → emits BYE_WEEK_IMPACT, BYE_WEEK_CONFLICT, FRANCHISE_BYE_WEEK_RECORD (labeled D51–D53 in the file's own docstring, but **not in** `CATEGORY_TO_DETECTOR`).
6. `core/recaps/context/league_rules_context_v1.py` (234 LOC) → emits SCORING_STRUCTURE_CONTEXT (not in map).

### Full inventory with gating-logic classification

Legend for *Gating*:
- **GEN** — Generalizable: the detector operates on sport-agnostic primitives (scores, outcomes, streaks, head-to-head). Would work for any head-to-head fantasy competition with minor work.
- **FB-DATA** — Football-shaped by data: the detector requires football-specific data (positions, lineup slots, bye weeks, auction budgets) but the algorithm is structurally generic.
- **FB-HARD** — Football-hardcoded: the detector contains hardcoded NFL-specific literals (position strings like QB/RB/WR/TE, or NFL-scoring language).

#### `narrative_angles_v1.py` — primordial matchup detectors (no D-id)

| Category | Gating | Notes |
|---|---|---|
| UPSET | GEN | Operates on `SeasonContextV1.standings` and `week_matchups`. "Lower-ranked beats higher-ranked" generalizes to any head-to-head ranking system. |
| STREAK | GEN | Operates on `TeamRecord.current_streak`. Pure win/loss streaks. Generalizes. |
| SCORING_ANOMALY | GEN | z-score-style detection against `ctx.season_avg_score`. Generalizes. |
| BLOWOUT | GEN | Margin vs season average. Generalizes. |
| NAIL_BITER | GEN | Margin vs season average. Generalizes. |
| SCORING_RECORD | GEN | Compares against `season_high`/all-time. Generalizes. |
| RIVALRY | GEN | Head-to-head history. Tenure-scoping (recent commit `a68a6e0`) adds franchise-tenure filtering, which is also generalizable. |
| STANDINGS_SHIFT | GEN | Mentioned in docstring but I did not find an emitting call for it in my scan — may be a docstring-implemented-not-shipped case; worth confirming. |

**Assessment:** This file is the most platform-clean detector file in the system. If a second module reused nothing else, it could reuse the concepts here directly given an equivalent `SeasonContextV1` shape.

#### `player_narrative_angles_v1.py` — D1–D19

| D-id | Category | Gating | Notes |
|---|---|---|---|
| D1 | PLAYER_HOT_STREAK | FB-DATA | `is_starter` flag + 25-point threshold. Threshold is sport-specific; concept (consecutive high scores) is generalizable. |
| D2 | PLAYER_COLD_STREAK | FB-DATA | `is_starter` + 8-point threshold. Same. |
| D3 | PLAYER_SEASON_HIGH | FB-DATA | Per-player season high. Generalizable. |
| D4 | PLAYER_BOOM_BUST | FB-DATA | Per-week anomaly. Generalizable. One of two explicit audit anchors per `prompt_audit_v1.py`. |
| D5 | PLAYER_BREAKOUT | FB-DATA | Generalizable. |
| D6 | ZERO_POINT_STARTER | FB-DATA | "Zero points" is sport-specific but the concept (starter with no contribution) generalizes. |
| D7 | PLAYER_ALLTIME_HIGH | FB-DATA | Generalizable. |
| D8 | PLAYER_FRANCHISE_RECORD | FB-DATA | Generalizable. |
| D9 | CAREER_MILESTONE | FB-DATA | Generalizable (per-player cumulative score across seasons). |
| D10 | PLAYER_FRANCHISE_TENURE | FB-DATA | "How long player has been on this team." Generalizable. |
| D11 | PLAYER_JOURNEY | FB-DATA | Cross-franchise player movement. Generalizable. |
| D12 | PLAYER_VS_OPPONENT | FB-DATA | Matchup-indexed player performance. Recent commit `7d4cbc6` tightened the gating. Generalizable with matchup shape. |
| D13 | REVENGE_GAME | FB-DATA | Generalizable. |
| D14 | PLAYER_DUEL | FB-DATA | Two players competing at same position in same matchup. "Same position" requires a position concept, which is FB-shaped data but not code-hardcoded here. |
| D15 | TRADE_OUTCOME | FB-DATA | Trades require roster change events. Generalizable to any league with trades. |
| D16 | THE_ONE_THAT_GOT_AWAY | FB-DATA | Traded-away player's subsequent production. Generalizable. |
| D17 | FAAB_ROI_NOTABLE | FB-DATA | "Free Agent Acquisition Budget" terminology is MFL-specific. The concept (cost-to-acquire vs production) generalizes to any budget-based acquisition system. |
| D18 | FAAB_FRANCHISE_EFFICIENCY | FB-DATA | Same. |
| D19 | WAIVER_DEPENDENCY | FB-DATA | Same. |

**Assessment:** D1–D19 are all structurally generalizable but depend on data shapes (is_starter, score, player_id, franchise_id) and concepts (positions, FAAB, waivers) that are fantasy-football-idiomatic. No hardcoded position literals (QB/RB/WR) appear in this file; positions flow through as string data where they are used. Thresholds (25, 8 points) are football-specific defaults.

#### `auction_draft_angles_v1.py` — D20–D28

| D-id | Category | Gating | Notes |
|---|---|---|---|
| D20 | AUCTION_PRICE_VS_PRODUCTION | FB-DATA | `$` in headline string; budget-based bidding. |
| D21 | AUCTION_DOLLAR_PER_POINT | FB-DATA | Same. |
| D22 | AUCTION_BUST | FB-DATA | Same. |
| D23 | AUCTION_BUDGET_ALLOCATION | FB-DATA | `budget: float = 200.0` default — PFL-specific value as a parameter default. |
| D24 | AUCTION_POSITIONAL_SPENDING | FB-DATA | Uses `position` strings as data; no hardcoded position literals. |
| D25 | AUCTION_STRATEGY_CONSISTENCY | FB-DATA | Year-over-year spending pattern. Generalizable to any auction-style draft. |
| D26 | AUCTION_LEAGUE_INFLATION | FB-DATA | Generalizable. |
| D27 | AUCTION_DRAFT_TO_FAAB_PIPELINE | FB-DATA | Cross-references auction and FAAB. Generalizable to any draft+mid-season-bidding system. |
| D28 | AUCTION_MOST_EXPENSIVE_HISTORY | FB-DATA | Generalizable. |

**Assessment:** This file is the cleanest of the three D-numbered files in terms of avoiding hardcoded sport-specific literals. `$` appears in headline prose but detector logic treats `bid_amount` and `position` as generic data. The $200 default budget is PFL-specific but parameterized. Auction scoring concepts transfer to any budget-based acquisition contest.

#### `franchise_deep_angles_v1.py` — D29–D50

| D-id | Category | Gating | Notes |
|---|---|---|---|
| D29 | SCORING_CONCENTRATION | FB-DATA | Per-franchise concentration of points in top starters. Generalizable. |
| D30 | SCORING_VOLATILITY | FB-DATA | Variance of weekly scores. Generalizable. Recent commit `fc922be` improved headline rendering. |
| D31 | STAR_EXPLOSION_COUNT | FB-DATA | Count of 30+-point individual performances. Generalizable. |
| **D32** | POSITIONAL_STRENGTH | **FB-HARD** | **Line 329: `if pos not in ("QB", "RB", "WR", "TE"): continue`** — hardcoded NFL position literals. This is the clearest FB-HARD detector in the codebase. |
| D33 | BENCH_COST_GAME | FB-DATA | Bench points left on table. Generalizable to any sport with lineup decisions. |
| D34 | CHRONIC_BENCH_MISMANAGEMENT | FB-DATA | Same. |
| D35 | PERFECT_LINEUP_WEEK | FB-DATA | Same. |
| D36 | CLOSE_GAME_RECORD | FB-DATA | Generalizable. |
| D37 | SEASON_TRAJECTORY_MATCH | FB-DATA | Generalizable. |
| D38 | SECOND_HALF_SURGE_COLLAPSE | FB-DATA | Assumes a split-season shape; generalizable. |
| D39 | CHAMPIONSHIP_HISTORY | FB-DATA | Playoff-aware (playoff derived from matchup count drop). Generalizable to any head-to-head format with playoffs. |
| D40 | FRANCHISE_ALLTIME_SCORING | FB-DATA | Generalizable. |
| **D41** | TRANSACTION_VOLUME_IDENTITY | — | **Currently disabled** per `prompt_audit_v1.py` comment; detector code emits the category in-file but is gated out. |
| D42 | LUCKY_RECORD | FB-DATA | Win% vs points-for correlation. Generalizable. |
| D43 | WEEKLY_SCORING_RANK_DOMINANCE | FB-DATA | Per-week rank within the league. Generalizable. |
| D44 | SCHEDULE_STRENGTH | FB-DATA | Generalizable. |
| D45 | REGULAR_SEASON_VS_PLAYOFF | FB-DATA | Playoff-aware; same detection trick as D39. Generalizable. |
| D46 | THE_BRIDESMAID | FB-DATA | "Finished 2nd repeatedly." Generalizable. |
| D47 | POINTS_AGAINST_LUCK | FB-DATA | Generalizable. |
| D48 | REPEAT_MATCHUP_PATTERN | FB-DATA | Generalizable. |
| D49 | SCORING_MOMENTUM_IN_STREAK | FB-DATA | Second explicit audit anchor per `prompt_audit_v1.py`. Recent commit `7d4cbc6` touches this. |
| D50 | THE_ALMOST | FB-DATA | "Finished one game out of playoffs." Generalizable. |

**Assessment:** One FB-HARD detector (D32). The rest are structurally generalizable. The playoff-detection trick (count matchups per week; regular season has N/2; playoffs have fewer) is clever and sport-agnostic-within-head-to-head — it would fail for a tournament or season-long-cumulative format.

#### `bye_week_context_v1.py` — D51–D53 (unnamed in map)

| Category (self-labeled D-id) | Gating | Notes |
|---|---|---|
| BYE_WEEK_IMPACT (D51) | **FB-HARD** | Reads `nfl_bye_weeks` table, which only exists for NFL. |
| BYE_WEEK_CONFLICT (D52) | **FB-HARD** | Same. |
| FRANCHISE_BYE_WEEK_RECORD (D53) | **FB-HARD** | Same. |

**Assessment:** Entirely NFL. Would not exist in any other module. Also the only detector file not tracked by the drift-detector test.

#### `league_rules_context_v1.py` — no D-id

| Category | Gating | Notes |
|---|---|---|
| SCORING_STRUCTURE_CONTEXT | **FB-HARD** | Contains literal `"QB"`, `"WR"`, and `"PPR"` logic (lines 166, 182, 185, 186). Computes things like "full PPR" vs fractional PPR and QB/WR positional emphasis. Deeply NFL-specific. |

### Detector suite summary

- **Structurally generalizable (GEN or FB-DATA with pluggable data):** 48 of the 50 D-numbered detectors plus all 8 primordial matchup detectors.
- **Football-hardcoded (FB-HARD) by literal position strings or NFL-only tables:** D32 (POSITIONAL_STRENGTH), all three bye-week detectors, and SCORING_STRUCTURE_CONTEXT.
- **Disabled:** D41 (TRANSACTION_VOLUME_IDENTITY).
- **Untracked by drift test:** ~12 categories (the 8 primordial, 3 bye-week, 1 scoring-structure). Not caught by the test that is named "drift detector."

The detector *algorithms* are largely platform-generalizable. The detector *data schemas* (what goes in `_PlayerWeekRecord`, `_AuctionPick`, etc.) and *threshold defaults* are football-shaped. An aspirational extraction would separate (a) detection primitives — compute season highs, streaks, concentrations, volatilities — from (b) sport-specific data producers, and let modules plug in their own data producers to feed the shared primitives. That is not the current shape.

---

## Section 4 — The verifier

Located in `src/squadvault/core/recaps/verification/recap_verifier_v1.py`. 2843 LOC, single file. The orchestrator (`verify_recap_v1`, lines 2724–2843) runs 8 categories in a fixed order.

### Category inventory

| # | Category | Severity | Entry point | Where | Purpose |
|---|---|---|---|---|---|
| 1 | SCORE | HARD | `verify_scores` | L484 | Extract numeric scores from prose, match against `WEEKLY_MATCHUP_RESULT` canonical. |
| 2 | SUPERLATIVE | HARD | `verify_superlatives` | L918 | Detect "season high" / "all-time record" claims and validate against `MAX`/`MIN` of matchup or player-score data. Contains V4, V5, V6, V7 guard subfunctions (ordinal/possessive/frequency/forward-lookback) to suppress false positives. |
| 3 | STREAK | HARD | `verify_streaks` | L1207 | Match "X-game streak" / "snapped" / "extended" claims against computed streaks. |
| 4 | SERIES | HARD | `verify_series_records` | L1633 | Match head-to-head series claims ("leads the series 7-3") against computed H2H history. |
| 5 | BANNED_PHRASE (+ SPECULATION) | SOFT | `verify_banned_phrases` | L1792 | Match against 8-item banned phrase list and 6 speculation regexes. Emits 2 distinct `category` strings (`BANNED_PHRASE` and `SPECULATION`). |
| 6 | PLAYER_SCORE | HARD | `verify_player_scores` | L2137 | Validate per-player scores in prose against canonical `WEEKLY_PLAYER_SCORE`. |
| 7 | PLAYER_FRANCHISE | HARD | `verify_player_franchise` | L2410 | Validate that a named player is attributed to the correct franchise for that week. Added recently (commit `a91fc72`). |
| 8 | FAAB_CLAIM | HARD | `verify_faab_claims` | L2609 | Validate FAAB dollar amounts against canonical `WAIVER_BID_AWARDED`. Added recently (commit `5b119b6`). |
| — | CROSS_WEEK_CONSISTENCY | — (batch-only) | `verify_cross_week_consistency` | L1926 | Compare streak and series claims across weekly artifacts in a batch. Not wired into the orchestrator; called only from `scripts/verify_season.py`. |

### Sport-specific content in verifier

Most of the verifier is pattern-extraction machinery (regex, fuzzy name matching, apostrophe normalization, windowing) that is structurally sport-agnostic. The sport-specific content is concentrated in:

- **`_BANNED_PHRASES` list** (L1769–1778): 8 phrases. Two are football-specific (`"the kind of chaos that makes fantasy football"`, `"stings when you lose by"`); the remaining 6 are generic sports-writing clichés that would apply to any fantasy module.
- **`_SPECULATION_PATTERNS`** (L1782–1789): 6 regex patterns for emotional attribution. Sport-agnostic.
- **Canonical event types hardcoded**: queries reference `WEEKLY_MATCHUP_RESULT`, `WEEKLY_PLAYER_SCORE`, `WAIVER_BID_AWARDED`. These event-type strings are MIXED — the event-type *concept* is platform-general but the specific strings are the fantasy football vocabulary.
- **Regex for monetary amounts** in FAAB verifier (not inspected at character level but the FAAB concept is football-idiomatic, though generalizable).

### Verifier summary

The verifier is **platform-shaped but module-filled**. The governing idea — extract claims, validate against canonical data, fail hard on factual contradictions, fail soft on style violations — is sport-agnostic. The event-type vocabulary, the banned-phrase list, and the claim-extraction regexes are tuned for football-recap prose. A second module would keep the skeleton and rewrite the category checks.

**Internal inconsistency noted** (for Section 9): the file contains two "Category 6" comment labels — L1829 labels `verify_cross_week_consistency` as "Category 6 (batch only)", and L2038 labels `verify_player_scores` as "Category 6 (Player Score Verification)". Numbering reuse. Does not affect behavior but is a small cleanliness debt.

---

## Section 5 — The platform adapter layer

I compared the Platform Adapter Contract Card v1.0 (from project knowledge) against the actual code in `src/squadvault/mfl/`, `src/squadvault/ingest/`, and `src/squadvault/ops/run_ingest_then_canonicalize.py`.

### Contract's claim

The contract specifies:

> The interface is defined by behavior contract, not by abstract base class — consistent with SquadVault's preference for boring, explicit code over clever patterns.
>
> - `discover(league_id, credentials) → DiscoveryReport`
> - `ingest(league_id, season, categories, credentials, db_path) → IngestResult`
>
> Each adapter must declare its `external_source` string (e.g., "MFL") and use it consistently in all event envelopes.

### What the code actually does

1. **There is one adapter and only one.** `MflClient` in `src/squadvault/mfl/client.py` is concrete and contains MFL-specific URL builders, login handling, and JSON-shape assumptions. There is no protocol, no ABC, no Duck-typed-"any object with these methods" check anywhere in `core/` that would let a second adapter swap in.
2. **`DiscoveryReport` exists and matches the contract** (`src/squadvault/mfl/discovery.py` L70–L128). It's a dataclass with `league_id`, `platform` (default `"MFL"`), `seasons: list[SeasonAvailability]`. This is good.
3. **`SeasonAvailability` has MFL-specific fields** (`server`, `mfl_league_id`) embedded in the generic data class. A second adapter couldn't produce these; the shape is MFL-flavored.
4. **`ingest_mfl_season` exists** (`historical_ingest.py` L517) with the correct signature shape — `(league_id, season, server, db_path, *, categories, ...)` — but it's named `ingest_mfl_season`, not `ingest`. The `server` positional argument is MFL-specific. There's no protocol it satisfies.
5. **`historical_ingest.py` imports directly** from `squadvault.ingest.auction_draft`, `squadvault.ingest.matchup_results`, `squadvault.ingest.player_scores`, `squadvault.ingest.transactions`, `squadvault.ingest.waiver_bids`, `squadvault.ingest.franchises._run_franchises_ingest`, `squadvault.ingest.players._run_players_ingest` (L24-L43). Each of these `ingest/*.py` files is an MFL→envelope transformer. **They are not behind an adapter interface; they are the adapter.** The directory called `ingest/` contains MFL-adapter code; the directory called `mfl/` contains MFL orchestration + discovery + HTTP client. This split does not reflect an adapter boundary.
6. **The category vocabulary is hardcoded** in `historical_ingest.py` L506–514 as `_ALL_CATEGORIES = ["FRANCHISE_INFO", "MATCHUP_RESULTS", "TRANSACTIONS", "FAAB_BIDS", "DRAFT_PICKS", "PLAYER_INFO", "PLAYER_SCORES"]`. The contract explicitly makes this a per-adapter declaration; here it lives inside MFL code.
7. **`external_source="MFL"` is set** in the discovery dataclass default (L75) and presumably per-envelope, but I did not trace every envelope creation to verify `external_source` is consistently set. Probably correct based on sampling.
8. **`ingest/mfl/` is a dead package.** It contains only `__init__.py` with no content. Historical artifact or stub for an intended cleanup; worth checking.

### Verdict

**The contract is real-as-document, aspirational-as-code.** The behavior it describes — two-phase discover/ingest, deterministic envelopes, append-only to memory ledger, zero writes outside memory — is what the code actually does. But the *interface that would let a second adapter substitute* is absent. A Sleeper adapter or ESPN adapter would need to:

- Build its own `DiscoveryReport`-shaped dataclass (or reuse `mfl.discovery.DiscoveryReport`, which has MFL-specific fields)
- Build its own `ingest_*_season` function matching the loose shape
- Inject calls to `core.storage.sqlite_store.SQLiteStore.append_events` directly
- Not break any code in `core/` — which it wouldn't, because no `core/` code calls back into the adapter

The last point is actually the good news: **`core/` does not depend on `mfl/`.** The coupling is one-way. `core/` reads from the canonical event ledger, which is platform-neutral at the schema level. This is the one seam where the contract's intent is honored structurally. The adapter boundary exists in the *flow of data* (platform → envelope → memory → canonical → core reads). It does not exist in *code*.

A second adapter is buildable today by copying `mfl/` and `ingest/` as siblings (e.g., `sleeper/`, `sleeper_ingest/`), not through extension of a platform. That's a workable starting point but it is not what the contract describes.

---

## Section 6 — The weekly recap lifecycle

`src/squadvault/recaps/weekly_recap_lifecycle.py`, 1346 LOC. The entry point for drafting is `generate_weekly_recap_draft` (L948). Reading this function top-to-bottom:

### The flow

1. **State load** (L964): `get_recap_run_state` — fetches from `recap_runs`. **Weekly-PK.**
2. **EAL load** (L969): `load_eal_directives_v1` — reads previously-persisted directives. Sport-agnostic.
3. **Base render** (L975): `_render_text_from_recap_runs` — renders deterministic facts block from canonical events. Sport-agnostic structure; content is football.
4. **Selection fingerprint** (L987): `_get_recap_run_trace`.
5. **EAL evaluate** (L993–L1046): counts included canonical events, detects playoff via matchup-count-drop trick (raw SQL inlined L1011–L1033), calls `evaluate_editorial_attunement_v1`. The playoff detection is football-flavored (weekly cadence + head-to-head).
6. **EAL persist** (L1050): writes `editorial_attunement_v1` JSON to `recap_runs`.
7. **Duplicate matchup preflight** (L1070): `check_duplicate_matchup_week`. Football-flavored — MFL-specific quirk.
8. **Deterministic bullets render** (L1114): `render_deterministic_bullets_v1`. Football-flavored.
9. **Prompt context derivation** (L1123): `_derive_prompt_context` — this is the fused detector-to-context layer. Pulls season_context, league_history, narrative_angles, writer_room, player_highlights. Every one of these is football-shaped.
10. **Retry loop** (L1137–L1270): 3 attempts, each:
    - Call `draft_narrative_v1` (creative layer)
    - Call `verify_recap_v1` (8-category verifier)
    - Capture to `prompt_audit` sidecar
    - On pass: break. On fail: build correction feedback, decay temperature, retry.
    - On exhaustion: fall back to facts-only (silence over fabrication).
11. **Artifact mint** (not shown above but elsewhere in file): creates a new `recap_artifacts` DRAFT row via `_create_recap_artifact_draft_always_new` (L171).

### Where the general pipeline lives vs where the fantasy football shape lives

**Platform-general (keep as-is):**

- The retry-with-feedback-until-verifier-passes pattern. This is the core governance contribution and is sport-agnostic.
- EAL evaluation and persistence.
- Artifact minting, state transitions (DRAFT→APPROVED), `supersedes_version` handling.
- Temperature decay on retry (L1136: `_retry_temperatures: list[float | None] = [None, 0.5, 0.3]`).
- The shape of `GenerateDraftResult` and the separation of "create a new draft version" from "approve a version."

**Fused with football (would need extraction):**

- Every import of a `core/recaps/context/*` function (L14–L52) pulls in football-specific detector code.
- The playoff detection SQL inlined at L1011–L1033 assumes weekly head-to-head cadence.
- `check_duplicate_matchup_week` is MFL-specific.
- `_derive_prompt_context` (L573, not shown in depth) assembles football-module context blocks — SEASON CONTEXT, LEAGUE HISTORY, NARRATIVE ANGLES, WRITER ROOM, PLAYER HIGHLIGHTS. These are content types for fantasy football recaps.
- The system prompt string in `creative_layer_v1.py` (see Section 9) is explicitly fantasy-football.

**The fusion shape:** The lifecycle is a sport-agnostic *state machine* (draft → verify → approve | withhold | regenerate) wrapped around a sport-specific *content pipeline* (detectors → prompt assembly → creative call). The state machine is ~20% of the code; the content pipeline is ~80% of what the lifecycle function actually does, because it imports, instantiates, renders, and assembles the football-specific context blocks inline.

**Extraction shape, if you wanted one:** The state machine could be parameterized by a `PromptAssembler` protocol (returns a list of context blocks + a system prompt) and a `Verifier` protocol (takes a draft, returns HARD/SOFT failures). The detectors, the creative layer prompt, and the verifier become a pluggable triplet. The lifecycle would then host any module's recap-equivalent artifact.

**I am not recommending that extraction.** I am naming the shape so the option is visible.

---

## Section 7 — Cross-cutting concerns

| Concern | Where it lives | Tag | Notes |
|---|---|---|---|
| **Constitution / governance principles** | `docs/` + project knowledge; enforced via CI gates in `Tests/` | INFRASTRUCTURE | Append-only, silence-over-speculation, AI-assists/human-approves are encoded in tests like `test_governance_gates_v1.py`, `test_immutability_violation_gate_v1.py`, `test_architecture_gates_v1.py`, `test_hygiene_gates_v1.py`, `test_data_depth_guardrails_v1.py` |
| **CI gates (guardrail registry, allowlist, patch-pair checks, etc.)** | `scripts/` — ~60 shell/python check/gate scripts | INFRASTRUCTURE | Topic-orthogonal; protects invariants regardless of module |
| **Editorial Attunement Layer (EAL)** | `core/eal/` | PLATFORM | Restraint-on-expression is sport-agnostic. The calibration module is larger (368 LOC) but logic is generic |
| **Tone + voice profiles** | `core/tone/` | PLATFORM | Governed voice presets table + engine |
| **Canonicalization** | `core/canonicalize/run_canonicalize.py` | PLATFORM | Memory→canonical dedup. Content-agnostic |
| **Selection / windowing** | `core/recaps/selection/` | MIXED | Window machinery is generic; event-type allowlist is module (`weekly_selection_v1._load_allowlist_event_types`) |
| **Prompt audit sidecar** | `recaps/writing_room/prompt_audit_v1.py` | PLATFORM | Observation-only, env-gated, no-op by default; append-only sidecar |
| **Observation directory** | `_observations/` + Phase 10 docs in project knowledge | INFRASTRUCTURE | "Observe, don't change" is a platform discipline, currently spending its credit on module-level findings |
| **Creative layer** | `ai/creative_layer_v1.py`, `ai/creative_layer_rivalry_v1.py` | MIXED | The API-call skeleton + EAL-gated early return + silent-fallback-on-error pattern is PLATFORM. Every string in the system prompt is MODULE |
| **Name resolution** | `core/resolvers.py`, `franchise_directory`, `player_directory` | MIXED | Cross-season franchise tenure (`league_history_v1.compute_franchise_tenures`) is used by the rivalry tier scoping — sport-agnostic concept, module-shaped terminology |
| **Verification framework** | `core/recaps/verification/` | MIXED | See Section 4 |
| **Approval Authority** | `ops/approval_authority_v1.py` | PLATFORM | Lifecycle action invariant validation |
| **Rivalry Chronicle** | `chronicle/`, `ai/creative_layer_rivalry_v1.py` | MODULE (but cleanly isolated) | Cleanly isolated into its own package; doesn't leak into core |
| **Writing Room intake** | `recaps/writing_room/intake_v1.py`, `selection_set_schema_v1.py`, and friends | UNCLEAR — see Surprises | Exists, is tested, is documented as canonical Tier-2 — but is not called by `generate_weekly_recap_draft` |

---

## Section 8 — Entanglement hotspots

Top places where sport-specific and sport-agnostic logic are most tightly coupled. Ranked by how expensive extraction would be.

### 1. `weekly_recap_lifecycle.generate_weekly_recap_draft` imports every detector module directly

`src/squadvault/recaps/weekly_recap_lifecycle.py` L14–L52.

```
from squadvault.core.recaps.context.auction_draft_angles_v1 import ...
from squadvault.core.recaps.context.bye_week_context_v1 import ...
from squadvault.core.recaps.context.franchise_deep_angles_v1 import ...
from squadvault.core.recaps.context.league_rules_context_v1 import ...
from squadvault.core.recaps.context.narrative_angles_v1 import ...
from squadvault.core.recaps.context.player_narrative_angles_v1 import ...
from squadvault.core.recaps.context.player_week_context_v1 import ...
from squadvault.core.recaps.context.season_context_v1 import ...
from squadvault.core.recaps.context.writer_room_context_v1 import ...
```

The lifecycle name-imports every football-specific context function it needs. There's no registry, no discovery, no protocol. Adding a new detector category to production requires editing the lifecycle. Removing the fantasy football module would delete 9 import lines and cascade into `_derive_prompt_context`.

**Cost of extraction:** Very high. Would need a `ContextAssembler` protocol and a per-module implementation; then the lifecycle imports the protocol and injects the football assembler at call site.

### 2. `core/queries/franchise_queries.py::_franchise_ids_from_payload` reaches into `raw_mfl_json`

`src/squadvault/core/queries/franchise_queries.py` line ~42:

```python
raw = payload.get("raw_mfl_json")
```

A query helper in `core/` reaches into a platform-adapter-specific payload field. The Platform Adapter Contract says raw platform responses are preserved in the payload for auditability; it does not say they are structured API for queries. This is a layer violation — the canonical layer should expose structured data through canonicalized fields, not by re-parsing MFL JSON inside a query helper.

**Cost of extraction:** Low to medium. Refactor `_franchise_ids_from_payload` to read only canonicalized payload fields and move MFL-specific parsing into ingest.

### 3. `weekly_recap_lifecycle` contains inline playoff-detection SQL with hardcoded shape

L1011–L1033, copied verbatim:

```python
"SELECT MAX(week) FROM ("
"  SELECT CAST(json_extract(payload_json, '$.week') AS INTEGER) as week,"
"         COUNT(*) as cnt"
"  FROM v_canonical_best_events"
"  WHERE league_id=? AND season=? AND event_type='WEEKLY_MATCHUP_RESULT'"
"  GROUP BY json_extract(payload_json, '$.week')"
"  HAVING cnt = ( ... )"
")"
```

Raw SQL in the lifecycle, assuming weekly cadence + head-to-head + WEEKLY_MATCHUP_RESULT event type. Duplicates similar logic in `season_context_v1` and `franchise_deep_angles_v1`. Three copies of the same playoff-detection rule across the codebase.

**Cost of extraction:** Medium. Extract to a single `detect_playoff_week(db_path, league_id, season, week)` helper; three call sites consolidate.

### 4. Event-type vocabulary is hardcoded in multiple places

- `core/recaps/selection/weekly_selection_v1.py` L44–L53: allowlist hardcoded (or read from `config/recap_event_allowlist_v1` — I did not verify)
- `core/queries/narrative_filters.py`: `DEFAULT_EXCLUDE_EVENT_TYPES` set
- `mfl/historical_ingest.py` L506–L514: `_ALL_CATEGORIES`
- `core/recaps/verification/recap_verifier_v1.py`: event-type string literals scattered throughout the SQL

No single source of truth for "what event types does this module emit?"

**Cost of extraction:** Medium. Centralize into a module-specific manifest (e.g., `fantasy_football/event_types.py`).

### 5. `core/exports/` sits under `core/` but is module-specific

`core/exports/approved_weekly_recap_export_v1.py`, `approved_rivalry_chronicle_export_v1.py`, `season_html_export_v1.py` — each exports a fantasy-football-specific artifact from the canonical tables. None of them belong in a `core/` that is supposed to be platform-scope.

**Cost of extraction:** Low. Move to `recaps/exports/` or a module-specific path. But this requires updating import paths project-wide; tests reference these paths.

### 6. `POSITIONAL_STRENGTH` detector hardcodes NFL positions

`core/recaps/context/franchise_deep_angles_v1.py` L329:

```python
if pos not in ("QB", "RB", "WR", "TE"):
    continue
```

The only literal-string NFL-position gate in the main detector files. `league_rules_context_v1.py` has similar literals (QB/WR/PPR) but that file is already named as league-rules-specific.

**Cost of extraction:** Low. Parameterize the "major positions" list as an arg or module constant. Not structural.

### 7. `prompt_audit_v1.CATEGORY_TO_DETECTOR` is a manually-maintained sport-specific registry in `recaps/writing_room/`

`src/squadvault/recaps/writing_room/prompt_audit_v1.py` L60–L120. A 50-entry hardcoded dict mapping football detector categories to D-ids. Lives in the Writing Room sidecar. Not in `core/`, not sourced from the detectors themselves (although a test partially enforces sync).

A platform-general approach would have detectors self-declare their IDs; here the mapping is maintained by hand and enforced by a drift test that, separately, doesn't scan all detector files (Section 9).

**Cost of extraction:** Medium. Requires each detector to self-attribute — a small but real API change across ~50 functions.

### 8. Creative layer system prompt is a 200+ line football-only string embedded in `ai/creative_layer_v1.py`

See Section 9. Not a code-entanglement hotspot in the structural sense, but it is load-bearing module content (banned phrases, voice rules, "NFL awareness" clause) living inside a file whose skeleton is otherwise platform-general.

**Cost of extraction:** Low. Move the system prompt to a module-owned resource file; have `creative_layer_v1.py` accept a system prompt as a parameter.

### 9. `mfl/historical_ingest.py` directly imports `ingest/*` modules rather than exposing a category contract

L24–L43. Orchestration is intertwined with derivation. Each category needs a matched pair: a `derive_*_envelopes` function in `ingest/` and an `_ingest_*` wrapper in `historical_ingest.py`. Adding a new category requires edits in two places.

**Cost of extraction:** Medium. Collapse each category's derivation + ingestion into a single function in `ingest/*` with a standard signature; `historical_ingest.py` dispatches by category name.

### 10. Name resolvers assume "franchise" and "player" as universal entities

`core/resolvers.py` exposes `FranchiseResolver`, `PlayerResolver`, `build_player_name_map`. These are referenced throughout the lifecycle and detectors. Fantasy golf has "entries" and "golfers"; fantasy chess has "teams" and "players" (coincidentally matching); fantasy Olympics has nothing like either.

**Cost of extraction:** Low structurally (rename to `EntityResolver`, `NameResolver`) but high in churn — hundreds of call sites.

---

## Section 9 — Surprises

Things worth naming plainly.

### S1. Recent git history past the stated HEAD

The prompt stated HEAD as `b9f495c` with "1,192 passing, 3 skipped." Actual HEAD is `04dc70a`, ~20 commits ahead. Changes since `b9f495c` include:

- **V7 and V8 verifier categories added** (commits `a91fc72` PLAYER_FRANCHISE, `5b119b6` FAAB_CLAIM, `fcffcf8` V8 matchup-line guard, `b58b1a2`/`b369ea8` V7 alias coverage)
- **Migration `0009_add_prompt_text_to_prompt_audit`** landed with commit `643b670`
- **Tenure-scoped rivalry** at commit `a68a6e0`
- **Several observation docs under `_observations/`** including `OBSERVATIONS_2026_04_16_WRITING_ROOM_SURFACING_AUDIT.md`

The test count in the prompt is therefore also stale. Test count was not rerun; based on the growth of the verifier and the migration, it is presumably ≥ 1,192 now.

### S2. `CATEGORY_TO_DETECTOR` does not cover ~12 live categories

`Tests/recaps/writing_room/test_prompt_audit_v1.py::_scan_live_categories` scans only three detector files:

```python
ANGLE_SOURCE_FILES = [
    "src/squadvault/core/recaps/context/player_narrative_angles_v1.py",
    "src/squadvault/core/recaps/context/franchise_deep_angles_v1.py",
    "src/squadvault/core/recaps/context/auction_draft_angles_v1.py",
]
```

It does **not** scan `narrative_angles_v1.py` (which emits UPSET, STREAK, SCORING_ANOMALY, BLOWOUT, NAIL_BITER, SCORING_RECORD, RIVALRY, STANDINGS_SHIFT), `bye_week_context_v1.py` (BYE_WEEK_IMPACT, BYE_WEEK_CONFLICT, FRANCHISE_BYE_WEEK_RECORD), or `league_rules_context_v1.py` (SCORING_STRUCTURE_CONTEXT).

The test's docstring calls itself the "drift detector" but its scan scope misses categories that are live in production. The `assert len(CATEGORY_TO_DETECTOR) == 50` in `test_category_to_detector_includes_audit_anchors` hard-pins a count that hides this gap.

Effect: if an angle emitted by one of the unscanned files reaches the prompt audit, `CATEGORY_TO_DETECTOR.get(cat, "UNMAPPED")` at prompt_audit_v1.py L167 will write `"UNMAPPED"` into the sidecar for those categories. The audit records would show UNMAPPED entries for existing detectors rather than flagging a drift.

### S3. Writing Room canonical intake is implemented but not on the main lifecycle path

Project knowledge documents list the Writing Room Intake Contract Card and Selection Set Schema as canonical Tier-2 contracts. The code implements both under `src/squadvault/recaps/writing_room/` with tests under `Tests/test_writing_room_intake_v1.py` and two sibling files.

Only one caller of `writing_room.intake_v1.build_selection_set_v1` exists in production code: `consumers/recap_writing_room_select_v1.py`, which is itself wrapped by `scripts/recap.py`. The main `generate_weekly_recap_draft` does **not** go through Writing Room intake. It goes direct: `recap_runs` row → canonical events → detectors → creative layer → verifier → artifact.

So the Writing Room exists, is canonical per documentation, and is orchestrationally orphaned from the lifecycle that actually produces weekly recaps. The `_observations/OBSERVATIONS_2026_04_16_WRITING_ROOM_SURFACING_AUDIT.md` document in the project knowledge presumably addresses this — the file title suggests the finding has been observed recently but not resolved.

This is the single largest drift between documentation-as-canonical and code-as-shipped.

### S4. `chronicle/input_contract_v1.py` is visibly AI-patched

The file contains 14 distinct `SV_PATCH_RC_*` comments documenting iterative fixes:

```
# SV_PATCH_RC_INPUT_CONTRACT_FIX_RESOLVE_V4
# SV_PATCH_RC_INPUT_CONTRACT_DELETE_ALL_IMPORT_TIME_BAD_BLOCKS_V1
# SV_PATCH_RC_INPUT_CONTRACT_DELETE_ALL_IMPORT_TIME_INP_BLOCKS_V1
# SV_PATCH_RC_INPUT_CONTRACT_DELETE_ORPHAN_INP_BLOCK_V2
# SV_PATCH_RC_INPUT_CONTRACT_DELETE_STRAY_RETURN_LINE154_V1
# SV_PATCH_RC_INPUT_CONTRACT_FIX_MISSING_IF_BODY_LINE149_V1
# SV_PATCH_RC_INPUT_CONTRACT_FIX_MISSING_IF_BODY_LINE141_V1
# SV_PATCH_RC_INPUT_CONTRACT_REPAIR_INDENT_WINDOW_V2
# SV_PATCH_RC_INPUT_CONTRACT_FIX_INDENT_LINE143_V2
# SV_PATCH_RC_INPUT_CONTRACT_EXPANDTABS_V7
# SV_PATCH_RC_INPUT_CONTRACT_SCRUB_TOPLEVEL_INDENT_V6
# SV_PATCH_RC_RESOLVED_INPUT_ADD_MISSING_WEEKS_V3
# SV_PATCH_RC_DEFINE_RESOLVED_INPUT_V2
# SV_PATCH_RC_INPUT_CONTRACT_DATACLASS_IMPORT_TOP_V1
```

Additional signs: `from typing import Any` appears on line 32, **after** a `@dataclass` on line 23 that uses `Any` in its annotations (works because annotations are lazy, but it's an ordering smell). All fields on `ResolvedChronicleInputV1` are typed `Any`.

The file is clearly the product of a patch-until-it-compiles session. It compiles, presumably tests pass, but the artifact is not the artifact a careful engineer would leave behind. Other files with `SV_PATCH` markers: `consumers/recap_export_narrative_assemblies_approved.py`, `consumers/rivalry_chronicle_approve_v1.py`. And dozens in `scripts/_archive/patches/` (retired). Not logging the archived ones — they are properly retired.

### S5. `ingest/mfl/` is an empty package

`src/squadvault/ingest/mfl/__init__.py` is empty, with no other files in the directory. Probably a vestige from an intended reorganization. Can be deleted.

### S6. Dual "Category 6" numbering in the verifier

`recap_verifier_v1.py` L1829 labels cross-week consistency as "Category 6 (batch only)"; L2038 labels player score verification as "Category 6". The comment numbering collides but the runtime category strings don't — `PLAYER_SCORE` is its own string and cross-week consistency is never wired into `verify_recap_v1`. Cosmetic.

### S7. "Banned phrase" verifier emits a category the name does not match

The function `verify_banned_phrases` emits **two** category strings: `BANNED_PHRASE` for the exact-phrase kill list, and `SPECULATION` for the speculation regex patterns. There is no distinct `verify_speculation` function, but the output treats them as distinct categories. The 8-category count in the orchestrator is correct; the docstring at the top of the file lists only 8 categories and folds SPECULATION into BANNED_PHRASE. Minor misalignment between docstring and emitted strings.

### S8. 129 scripts at scripts/ top level plus 3 retired/archive subdirs

`scripts/` has 129 direct entries. Many are single-purpose diagnostic tools for Phase 10 observation (`diagnose_purple_haze_series.py` — named for a PFL franchise — `diagnose_d12_threshold_sweep.py`, `diagnose_streak_momentum_gate.py`, etc.). About 60 are CI gate scripts (`check_*`, `gate_*`).

`scripts/_archive/patches/` contains dozens of retired single-use patch scripts. These are clearly already retired — that directory exists for exactly this purpose. No action needed; flagging for awareness of scale.

### S9. `_retired/notion/` is still in the tree

`src/squadvault/_retired/notion/` contains 4 files (`client.py`, `properties.py`, `schema_specs.py`, `schema_validator.py`). Per the Documentation Map, Notion integration has been retired. The code is in the correct retirement location. Whether it should be *deleted* vs *retained-as-archive* is a judgment call; I flag it because retired code that lives inside `src/` may confuse future contributors about whether it's still wired in.

### S10. `franchise_queries.py` is the only `core/` file that contains the substring `raw_mfl_json`

Quick grep confirms. Core is otherwise free of MFL-specific payload-field references. This is the lone leak.

### S11. `league_rules_context_v1.py` category SCORING_STRUCTURE_CONTEXT is fantasy football voice

Literal scoring-vocabulary detection — "full PPR" vs fractional PPR, QB vs WR emphasis in scoring — feeds directly into a context block labeled `SCORING_STRUCTURE_CONTEXT`. This is load-bearing for the model's ability to contextualize scores, and it is the most football-specific thing in the detector layer outside of bye weeks. Worth noting as a detector that doesn't really generalize even with parameterization — scoring structure as a narrative concept is a fantasy football phenomenon.

### S12. `check_duplicate_matchup_week` preflight gate is an MFL-specific workaround

`recaps/preflight.py` L ~, referenced from lifecycle L1070. The workaround exists because MFL occasionally records championship results in multiple week slots. If a second adapter were added, the preflight would need per-adapter quirks; currently it is unconditional.

### S13. The "Observation-first" discipline is honored in the code but also creates review debt

The `_observations/` directory and the Phase 10 documents contain careful observations with file/line precision (e.g., 11 distinct verifier false-positive patterns identified and named). This is exemplary governance discipline. It also means there are many open observations of the "we saw this pattern in a draft, need to decide what to do" variety that have documentation but no closure, held by a single commissioner-developer. This is not a code finding per se; it is a process finding that affects whether the codebase can absorb a contributor without a founder-walkthrough.

---

## Section 10 — Open design questions

Questions, not answers. Each represents a decision that would need a direction before a platform extraction could proceed. Ordered loosely by leverage.

### Q1. Is "platform" the right aspiration, or is "well-factored monolith" enough?

The code today is a well-factored fantasy football monolith with a clean memory layer. Many of the entanglement hotspots in Section 8 are only "entanglements" against an aspirational extraction that has not yet been scoped. If the second module is definitely-coming within 18 months, extraction work is investment. If the second module is speculative, the extraction work is speculative. This is an investment decision, not an architecture decision.

### Q2. What is the smallest viable second module?

If there is a specific second module in mind, its shape determines where extraction makes sense. Questions:

- Does it have matchups (head-to-head) or cumulative-period scoring?
- Does it have "players" (individually owned contributors) or just "entries" (the whole team is the unit)?
- Does it have waivers/FAAB-like acquisition?
- Does it have an auction/draft-like beginning-of-season event?
- What cadence — weekly, daily, tournament-by-tournament, season-long?

Answers to these determine which of the 50+ detector patterns transfer, which ~12 schema tables transfer as-is, and where the real extraction seams need to be.

### Q3. Where does the adapter interface live, if it becomes real?

Today there is no adapter protocol. If one is drawn:

- Should it be a `typing.Protocol`, an ABC, or a duck-typed convention?
- Does it live in `core/` (where a second adapter could implement against it) or in a separate `platform/` directory?
- Is `DiscoveryReport` shared or per-adapter?
- Is the category vocabulary (FRANCHISE_INFO, MATCHUP_RESULTS, etc.) part of the protocol or per-adapter?

The contract card says "behavior contract, not ABC." That rules out the explicit ABC path. It does not answer where the contract lives or who validates conformance.

### Q4. Does "module" mean "fantasy sport module" or "fantasy contest module"?

Fantasy football and fantasy basketball are very similar (different positions, same head-to-head weekly structure). Fantasy golf is different (no head-to-head, cumulative stroke-based scoring). Fantasy NASCAR is different again. If modules are one-per-sport, a lot of detector code generalizes within the head-to-head family. If modules are one-per-contest-shape (head-to-head vs cumulative vs tournament), then the shape determines which `core/recaps/context/*` content transfers.

### Q5. Does `week_index` become `period_index`?

The schema primary keys on `recap_runs`, `recap_selections`, `prompt_audit` encode weekly cadence. Generalizing to non-weekly modules requires either a migration to `period_index` or new per-module tables. The first is invasive; the second multiplies the schema. No obvious right answer without Q2 answered.

### Q6. Do detectors self-register, or does a registry map categories to detectors?

Today the mapping lives in `CATEGORY_TO_DETECTOR` and is hand-maintained with a partial drift test. If detectors self-declared their ID + dimension + gating-logic classification, the registry would be derived and the drift test would be trivially complete. But that touches ~60 detector functions' signatures.

### Q7. Where does the system prompt for the creative layer live?

Today: 200+ lines of fantasy-football-specific prose inside `ai/creative_layer_v1.py`. A second module needs its own. Options: (a) per-module .txt resource files loaded by path; (b) per-module Python module with a constant; (c) database-resident, commissioner-editable via the `league_voice_profiles` table pattern.

### Q8. Is the verifier one-per-module or one-per-platform-with-pluggable-checks?

Today's verifier (2843 LOC, 8 categories) is mostly claim-extraction infrastructure (regex, windowing, apostrophe normalization) with 8 category-specific check functions. The infrastructure generalizes. The check functions are module-specific. Choice: factor out the infrastructure into a `verifier_core/` and have per-module check modules; or have per-module verifiers that copy the infrastructure; or accept the current monolithic shape and namespace it per-module.

### Q9. What happens to the Writing Room on the main path?

Per S3, the canonical Tier-2 Writing Room intake is orchestrationally orphaned from the main lifecycle. Before extraction, decide: does the lifecycle move to routing through Writing Room intake (aligning code with contract), does Writing Room's canonical status get downgraded (aligning contract with code), or does it remain as a documented divergence? This is a platform-shape decision because the Writing Room is explicitly positioned as the platform-general selection-set producer.

### Q10. Where do the ~12 unmapped live categories go?

See S2. Before extraction, these categories need to either be integrated into `CATEGORY_TO_DETECTOR` (and the drift test's scan list expanded), or explicitly classified as "primordial / non-D-numbered" and handled separately. Shape-of-platform matters here because primordial matchup detectors (narrative_angles_v1.py) are the most platform-general detectors in the system and should probably be the template for a "platform tier" of detectors.

### Q11. Does `core/exports/` stay in `core/` or move to a module path?

See hotspot #5. Low mechanical cost. The question is whether `core/` should contain anything module-specific at all. A strict answer ("no, nothing") forces the move. A pragmatic answer ("for now, yes, until there's a second module") keeps the current layout.

### Q12. Are diagnostic scripts per-module or shared?

`scripts/diagnose_purple_haze_series.py` is a PFL-franchise-specific diagnostic. `scripts/diagnose_d12_threshold_sweep.py` is a detector-tuning tool. A second module would need its own diagnostics folder. Options: per-module `scripts/ff/`, `scripts/golf/` subdirectories; or flat `scripts/` with naming conventions. Low priority but worth deciding before the split.

---

## Closing note

This audit is ~17,000 words of description intended to be usable as a reference during a subsequent design session. It says nothing about what to do. The next conversation — if there is one — should take this document as input and answer the open questions in Section 10. The entanglement hotspots in Section 8 are a candidate agenda in rank order.

The most honest summary of SquadVault's current state: **it is an extraordinarily well-governed single-league fantasy football engine with exemplary observation discipline and a clear memory-layer seam that would make a second adapter tractable.** Extracting a second *module* (not adapter) is a larger undertaking than the current shape suggests, because every layer above the memory ledger — detectors, context assembly, verifier, creative layer, lifecycle — has absorbed fantasy-football assumptions by name and structure. None of those assumptions are wrong for the current scope; they are simply not what the contract cards describe as the platform's eventual shape.

End of audit.
