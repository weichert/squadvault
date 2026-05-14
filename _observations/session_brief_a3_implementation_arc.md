# Session Brief — Phase 11 A3 (Championship Timeline) Implementation Arc

**Date prepared:** 2026-05-14
**Prepared at HEAD:** `8852a98` (Narrative_Angles_v2 anchor correction record)
**Status:** Session-priming brief. Not a constitutional memo, not tier-registered. Use as the next session's prompt.

---

## 1. Objective

Build A3 (Championship Timeline) per its specification — the implementation work that completes cluster A at the implementation level. Cluster A currently stands: A1 specified-and-built, A2 specified-and-built, **A3 specified-but-not-built.** This arc closes that gap.

The deliverable is a browseable `archive/championship_timeline/` archive plus its aggregation layer, render layer, generation script, and test coverage — produced across a **three-commit arc**, exactly mirroring the A1 and A2 implementation arcs.

This is real code: ruff + mypy + pytest gated. Plan for a session, possibly two.

---

## 2. Input contract

**The A3 specification is the input contract: `38ddcd2`** (`_observations/OBSERVATIONS_2026_05_14_PHASE_11_A3_SPECIFICATION.md`). It is Mode B — it specifies the operational shape the implementation produces. Read it in full at session start. The load-bearing sections for implementation:

- **§3.1** — the three v1 sub-shapes and their substrate sources.
- **§3.3** — v1 content scope: the trio ships; §4.2.3 / almost-leg / repeat-meetings do NOT.
- **§3.6** — W17/W18 collapse-by-content rule + scope-declaration framing copy.
- **§3.7** — Bridesmaids ships the runner-up leg ONLY; the almost leg (D50) is dropped from v1.
- **§3.8** — Cross-Season Playoff Records: four dimensions, all four ship; per-season set semantics.
- **§5.1–§5.5** — the Mode B operational shape: archive layout, update events, approval lifecycle, test baseline.
- **§6.2 / §6.3 / §6.7** — the three A3-specific invariants that bind the implementation (see §8 below — these are the hazards).
- **§5.5** — derivation-function naming (implementer-elected), the likely layout-test name.

The six inherited elections (Reading 1, D3-Alpha, D4.1-Gamma, D4.2-Beta, D4.3, D5-Gamma) and the eight landed Step-2 gaps are settled — the implementation operationalizes them, it does not reopen them.

---

## 3. Starting state — confirm at session start

**Pre-session preamble (run before touching anything):**

- `git rev-parse HEAD` — expect `8852a98` (or later if intervening work landed; verify thread status from git log).
- `PYTHONPATH=src pytest -q` — expect **2095 passed / 2 skipped** (the session that prepared this brief was doc-only plus the A2 test rename, which kept the count flat). Confirm; do not assume.
- `ruff check .` — expect clean.
- `mypy` across `src/squadvault/core/` — expect clean (64 source files).

**What exists:**

- The A3 spec (`38ddcd2`).
- The substrate: `WEEKLY_MATCHUP_RESULT` events in `canonical_events`, complete across the 16-season digital era (A3 Step 1 §4.1 confirmed: 1,182 matchups, no gaps).
- `compute_championship_roll` and the playoff-detection helper `_regular_season_matchup_count` in `src/squadvault/core/recaps/context/hall_of_fame_aggregations_v1.py` (317 lines) — A1's aggregation module.
- D39 `detect_championship_history` and D50 `detect_the_almost` in `src/squadvault/core/recaps/context/franchise_deep_angles_v1.py` (1606 lines).
- `load_all_matchups` and the `HistoricalMatchup` dataclass in `src/squadvault/core/recaps/context/league_history_v1.py` (837 lines).
- `Tests/test_playoff_detection_v1.py` — existing playoff-detection-trick coverage (9 tests).
- The A1 and A2 archives + their full implementation stacks — the concrete templates (see §4).

**What does NOT exist (this arc creates it):**

- `archive/championship_timeline/` — no directory.
- Any A3 aggregation, render, or script layer.
- Any A3 test files.

---

## 4. The three-commit arc — the A1/A2 template made concrete

A1 and A2 followed an **identical** three-commit structure. A3 follows it exactly. File-by-file precedent:

### Commit 1 — aggregation layer

| A1 (`eb6042d`) | A2 (`87ebdad`) | A3 (this arc) |
|---|---|---|
| `context/hall_of_fame_aggregations_v1.py` (317 ln) | `context/draft_history_vault_aggregations_v1.py` (447 ln) | `context/championship_timeline_aggregations_v1.py` (name per A1/A2 pattern; implementer-elected per spec §5.5) |
| `Tests/test_hall_of_fame_aggregations_v1.py` (414 ln) | `Tests/test_draft_history_vault_aggregations_v1.py` (646 ln) | `Tests/test_championship_timeline_aggregations_v1.py` |
| +1 line to `Tests/recaps/writing_room/test_prompt_audit_v1.py` | +1 line to same | **+1 line to same — see §5, do not skip** |
| — | also modified `auction_draft_angles_v1.py` (loader promotion) | A3 may not need an underlying-module modification — its substrate primitives already exist |

### Commit 2 — render + script + tests

| A1 (`97c8bf0`) | A2 (`4f9c379`) | A3 (this arc) |
|---|---|---|
| `render/hall_of_fame_render_v1.py` (370 ln) | `render/draft_history_vault_render_v1.py` (398 ln) | `render/championship_timeline_render_v1.py` |
| `scripts/generate_hall_of_fame_archive.py` (198 ln) | `scripts/generate_draft_history_vault_archive.py` (217 ln) | `scripts/generate_championship_timeline_archive.py` |
| `Tests/test_hall_of_fame_render_v1.py` (352 ln) | `Tests/test_draft_history_vault_render_v1.py` (448 ln) | `Tests/test_championship_timeline_render_v1.py` |
| `Tests/test_hall_of_fame_archive_layout_v1.py` (105 ln) | `Tests/test_draft_history_vault_archive_layout_v1.py` (147 ln) | `Tests/test_championship_timeline_archive_layout_v1.py` (name per spec §5.5) |

### Commit 3 — initial archive generation

| A1 (`642d6dc`) | A2 (`9189a7d`) | A3 (this arc) |
|---|---|---|
| `archive/hall_of_fame_and_shame/` — index.md + championship_roll.md + worst_seasons.md + blowouts_hall.md | `archive/draft_history_vault/` — index.md + bargain_hall.md + bust_hall.md + most_expensive.md | `archive/championship_timeline/` — index.md + playoff_brackets.md + playoff_records.md + bridesmaids.md (per spec §5.1) |

Commit 3 is produced by **running the generation script** against `.local_squadvault.sqlite` and committing the output — it is not hand-authored.

**The commit-message model: A1's `eb6042d` message.** Read it (`git show eb6042d`) before writing A3's commit-1 message. It is the template: what ships, public functions with signatures + lift origins, new dataclasses, the registry touch, section-by-section spec compliance, an explicit "what this commit does NOT ship," test baseline before/after, predecessors.

---

## 5. Commit 1 detail — aggregation layer

Three public derivation functions, one per v1 sub-shape. Names are implementer-elected per spec §5.5; the spec's working names are `compute_playoff_bracket`, `compute_cross_season_playoff_records`, `compute_bridesmaids`.

### 5.1 Per-Season Playoff Bracket — `compute_playoff_bracket`

**Generalizes `compute_championship_roll`** (`hall_of_fame_aggregations_v1.py`). `compute_championship_roll` narrows each season to the championship-week singleton (one `ChampionshipResult` per season). A3's bracket function uses the *same* playoff-detection trick — `_regular_season_matchup_count` gives the regular-season mode; weeks with fewer matchups than the mode are playoff weeks — but **emits all playoff-week matchups per season**, not just the championship week. Output: per season, the full bracket across all playoff rounds (preliminary → semifinal → championship).

**Bind: the W17/W18 collapse-by-content rule (spec §3.6 / §6.2).** Post-2021 seasons (2021-2025) carry DUPLICATE verbatim-identical W17/W18 championship rows in the substrate. The rule: **when two consecutive playoff weeks have identical `(winner_id, loser_id, winner_score, loser_score)` tuples, treat the later week as a duplicate and emit only the earlier week as the "Championship" round.** This is content-based, NOT era-based — do not hardcode "post-2021, suppress W18." Under collapse-by-content both eras present as a clean 3-round bracket. The rule must be robust to substrate change (re-ingestion removing the duplication; a genuine two-week structure with different scores appearing).

### 5.2 Cross-Season Playoff Records — `compute_cross_season_playoff_records`

**Lifts D39 `detect_championship_history`** (`franchise_deep_angles_v1.py`) — D39 already operates cross-season within its playoff-week branch. Four dimensions, **all four ship** (spec §3.8):

- per-franchise playoff-season appearances
- per-franchise championship-matchup appearances
- longest playoff-active streak
- longest playoff-drought streak

**Bind: per-season set semantics (spec §3.8 / §6.3).** D39's internal `playoff_appearances` dict increments **per-matchup** — a franchise in 2 playoff weeks of one season gets `+= 2`. This over-counting is silent in D39's production behavior (D39's surfaced angles never read the dict). A3's lift **must NOT consume D39's internal `playoff_appearances` dict.** Build the count with a per-season `set[str]` of playoff participants — one increment per franchise per season. This invariant is stated explicitly in spec §6.3 precisely so a future maintainer does not "fix" the count by importing D39's internal logic and inheriting the over-counting.

### 5.3 Bridesmaids — `compute_bridesmaids`

**Runner-up leg ONLY** (spec §3.7). A clean group-by aggregation over `compute_championship_roll(...)`'s output: aggregate the `runner_up_id` field of the `ChampionshipResult` tuples by franchise, across the 16-season digital era. A3's Bridesmaids does NOT re-derive championships — it consumes A1's existing `compute_championship_roll` results.

**The almost leg (D50 `detect_the_almost`) is DROPPED from v1** — substrate-thin (D50's `min_times=3` threshold produces zero PFL angles; the full leaderboard at `min_times=1` is a 4-row table with max count 2). Do not implement the almost leg. The drop is a scope decision recorded in spec §3.7; the almost leg is a preserved future-expansion path, not a v1 deliverable.

### 5.4 The `_NON_EMITTING_CONTEXT_MODULES` registry touch — DO NOT SKIP

Both A1's commit 1 (`eb6042d`) and A2's commit 1 (`87ebdad`) included a +1-line change to `Tests/recaps/writing_room/test_prompt_audit_v1.py`: adding the new aggregations module's filename to the `_NON_EMITTING_CONTEXT_MODULES` set. The new module is an aggregation layer — it does NOT emit narrative angles for weekly-recap prompt consumption — so it belongs in that set. **If you skip this, the "Audit Surprise S2 drift detector" fails on the first test run.** Add `championship_timeline_aggregations_v1.py` (or the elected name) to `_NON_EMITTING_CONTEXT_MODULES` as part of commit 1.

### 5.5 The playoff-detection-helper decision

`_regular_season_matchup_count` currently exists in **two** places — `franchise_deep_angles_v1.py` and `hall_of_fame_aggregations_v1.py` — deliberately duplicated (A1's commit message: "avoiding a cross-module import of a private function"; both must remain semantically identical). A3's aggregation module needs this helper too. A3 becoming the **fourth consumer** of the playoff-detection trick (spec §4.3 noted the trick already has three call sites) means a third duplication starts to smell.

**This is a genuine design decision for the implementation — the brief flags it, does not pre-decide it.** Options: (a) duplicate again per the established private-helper pattern, with the same docstring note; (b) cross-import from `hall_of_fame_aggregations_v1` (it is a sibling in `context/`, though the helper is private); (c) promote the helper to a shared non-private location. The diagnostic-first instinct applies: characterize the cost of each before choosing; the entanglement-hotspot reality (four consumers) is the relevant signal.

---

## 6. Commit 2 detail — render + script + tests

- **Render module** (`render/championship_timeline_render_v1.py`) — markdown renderers for the three sub-shapes. Precedent: `hall_of_fame_render_v1.py` (370 ln) / `draft_history_vault_render_v1.py` (398 ln). The scope-declaration framing copy (spec §3.6) and the bracket-shape framing copy (the two-era week-label shift) render here.
- **Generation script** (`scripts/generate_championship_timeline_archive.py`) — wires aggregation + render into one operational unit, reads `.local_squadvault.sqlite`, writes `archive/championship_timeline/*.md`. Precedent: `generate_hall_of_fame_archive.py` (198 ln) / `generate_draft_history_vault_archive.py` (217 ln). **Write the `Default invocation:` docstring block correctly the first time** — `./scripts/py scripts/generate_championship_timeline_archive.py`, with the explanatory sentence about the shim. Commits `1b7ab36` and `72087d5` this session existed solely to fix A1's and A2's scripts, which shipped with the bare-form invocation. Do not repeat that.
- **Render test** (`Tests/test_championship_timeline_render_v1.py`) — precedent: `test_hall_of_fame_render_v1.py` (352 ln) / `test_draft_history_vault_render_v1.py` (448 ln).
- **Layout test** (`Tests/test_championship_timeline_archive_layout_v1.py`, name per spec §5.5) — enforces the archive layout invariants (spec §6.4): `index.md` is the entry point with the scope-declaration header; the three sub-shape files are siblings; `playoff_brackets.md` cross-links to A1's `archive/hall_of_fame_and_shame/championship_roll.md` (the §3.1 absorption boundary — A3 does NOT re-render A1's championship-roll content). Precedent: `test_hall_of_fame_archive_layout_v1.py` (105 ln) / `test_draft_history_vault_archive_layout_v1.py` (147 ln).

**Bind: the not-a-real-time-tracker invariant (spec §6.7).** A3's archive updates **once per year at end-of-NFL-season** — not incrementally per playoff round. The Per-Season Playoff Bracket *could* technically be regenerated mid-playoffs as each round resolves; the spec forbids this. The generation script regenerates all three sub-shapes from the completed substrate; there is no incremental in-season mode. This is the anti-engagement-loop posture — the script's design should not invite per-round regeneration.

---

## 7. Commit 3 detail — initial archive generation

Run `./scripts/py scripts/generate_championship_timeline_archive.py` against `.local_squadvault.sqlite`. Review the generated `archive/championship_timeline/*.md` via `git diff` (per spec §5.4 the commit IS the approval event). Commit the four markdown files.

Sanity-check against known facts before committing: the bracket reconstruction should match league memory (A3 Step 1 §4.5 confirmed the 2025 bracket against league memory); the 16-season digital era should be fully represented; post-2021 seasons should show a clean 3-round bracket (W17/W18 collapse working); franchise 0008's perennial-bridesmaid pattern (3 runner-ups, 0 titles per A3 Step 1 §3.3) should be visible in `bridesmaids.md`.

The commit subject follows the A1/A2 pattern: `Phase 11 A3: initial archive generation (16 seasons, 2010-2025)`.

---

## 8. A3-specific implementation hazards — consolidated

The three spec invariants plus two structural traps. Each is a place the implementation can silently go wrong:

1. **W17/W18 collapse-by-content (§3.6 / §6.2)** — post-2021 seasons have duplicate verbatim-identical championship rows. Collapse by *content equality* of the `(winner_id, loser_id, winner_score, loser_score)` tuple, not by era. Robust to substrate change. Test it explicitly: a post-2021 fixture's duplicate must collapse to one Championship round.
2. **Per-season set semantics (§3.8 / §6.3)** — do NOT consume D39's internal per-matchup `playoff_appearances` dict. Build per-season counts with a `set[str]`. Test it explicitly: a franchise in 2 playoff weeks of one season counts as 1 playoff-season appearance, not 2.
3. **Not-a-real-time-tracker (§6.7)** — once-per-year end-of-season regeneration; no incremental in-season mode.
4. **Bridesmaids = runner-up leg only (§3.7)** — the almost leg (D50) is dropped from v1. Do not implement it.
5. **Playoff-detection-trick fourth-consumer entanglement (§5.5 above)** — the duplicate-private-helper pattern is at its limit; make the duplicate-vs-cross-import-vs-promote decision deliberately, characterizing cost first.

Standing project principle that applies throughout: **diagnostic-first** — no production code without prior empirical grounding. A3's grounding already exists (the A3 Step 1 probes, `1e7b59d`); re-read Step 1 §3 / §4 if any derivation behavior is unclear, rather than guessing.

---

## 9. What the spec deliberately leaves to the implementation

Per A3 spec §5.5 / §6.8 — these are open at implementation time and are NOT load-bearing on the spec; the implementation elects them freely within the spec's invariants:

- Exact file and function names (the §4/§5 tables use the A1/A2-pattern names; the implementer may elect others).
- Top-N values within the cross-season leaderboards.
- Per-sub-shape markdown structure and rendering detail.
- The playoff-detection-helper duplicate-vs-cross-import-vs-promote decision (§5.5).
- Whether a `notable championships` sidebar surfaces the substrate-density facts (2013's 1-point championship, 2019's 1.45-point, 2014's anomalously-low-scoring) — spec §3.9 says this is an implementation-elected presentation detail, not load-bearing.
- Whether a per-A3 push script is specified (spec §5.1 secondary channel — optional at v1).

Do not treat these as spec gaps; they are deliberate implementation latitude.

---

## 10. Session discipline

Carried forward from established practice — non-negotiable:

- **One topic per commit; one file per pass for most changes.** The three-commit arc is the topic structure: aggregation / render+script+tests / archive. Do not collapse commits.
- **Separate paste turns for gates vs commit.** Run `ruff` + `mypy` + `pytest` as their own paste turn; `git add` + `git commit` as a separate turn. NEVER chain a gate with `&&` before a commit — the pre-commit hooks (banner-paste, no-xtrace, repo-root allowlist) do NOT run ruff or pytest; a failed gate chained with `&&` lands a broken commit.
- **Commit messages: write to `/tmp/*_msg.txt`, then `git commit -F`.** ASCII-only in commit messages — substitute `-` for em-dash and `section X` for the section sign. Artifact bodies keep rich typography.
- **No inline `#` comments in paste-intended shell blocks** (zsh `if>` continuation hazard).
- **`.md` filenames auto-link in chat and corrupt copy-paste** — verify on-disk filenames via `git status` / `git log`, not the chat-rendered echo.
- **Apply-then-verify** — any patch/generation step must actually execute (`git diff` to confirm) before running gates.
- **Pre-session preamble AND post-change verification** — pytest count, ruff clean, mypy clean, before and after.
- **The full pytest run is ~10 minutes.** Plan paste turns around it: one full `pytest` after commit 1's code lands, one after commit 2's. Commit 3 (archive markdown only) does not change test behavior but run pytest once more to confirm the layout test passes against the generated archive.
- **Multi-commit sequencing hazard** — this session's run nearly skipped a commit at a seam between doc and code commits. Number the paste blocks explicitly (1-of-N) when delivering the arc.

**Test baseline expectation:** the baseline grows monotonically — commit 1 adds aggregation tests, commit 2 adds render + layout tests, commit 3 adds none. Expect roughly +30-40 tests per code commit (A1 commit 1 was +30; A2 commit 1 was larger). Zero regressions on existing tests; ruff and mypy stay clean. If the row-level pytest count regresses, stop and diagnose before proceeding.

---

## 11. Cross-references

- `38ddcd2` — **A3 specification** (the input contract; `_observations/OBSERVATIONS_2026_05_14_PHASE_11_A3_SPECIFICATION.md`)
- `1e7b59d` — A3 decision-readiness Step 1 (empirical grounding — §3 / §4 probe findings; the W17/W18 duplication at §4.3, the per-season-semantics finding at §6.3, the bridesmaid density at §3.3)
- `eb6042d` / `97c8bf0` / `642d6dc` — **the A1 implementation arc** (the concrete three-commit template; `eb6042d`'s commit message is the commit-message model)
- `87ebdad` / `4f9c379` / `9189a7d` — the A2 implementation arc (second instance of the same template)
- `1b7ab36` / `72087d5` — the archive-script `./scripts/py` docstring fixes (the lesson: write the script's invocation docstring correctly the first time)
- `src/squadvault/core/recaps/context/hall_of_fame_aggregations_v1.py` — `compute_championship_roll` (lines ~234-317; the function A3's bracket sub-shape generalizes), `_regular_season_matchup_count` (lines ~92-117; the playoff-detection helper), the `ChampionshipResult` dataclass (A3's Bridesmaids consumes its `runner_up_id`)
- `src/squadvault/core/recaps/context/franchise_deep_angles_v1.py` — D39 `detect_championship_history` (~lines 1248-1333; the cross-season lift source for §3.8; carries the per-matchup over-counting trap), D50 `detect_the_almost` (~lines 1407-1468; the dropped-from-v1 almost leg — do NOT implement)
- `src/squadvault/core/recaps/context/league_history_v1.py` — `load_all_matchups` (~lines 214-271), `HistoricalMatchup` dataclass (~lines 44-54)
- `Tests/recaps/writing_room/test_prompt_audit_v1.py` — the `_NON_EMITTING_CONTEXT_MODULES` set; add the new aggregation module's filename here in commit 1
- `Tests/test_playoff_detection_v1.py` — existing playoff-detection-trick coverage (9 tests); A3's implementation should confirm the generalized bracket derivation does not regress it
- `archive/hall_of_fame_and_shame/championship_roll.md` — A3's `playoff_brackets.md` cross-links to this; A3 does not re-render it (the §3.1 absorption boundary)

---

## 12. Definition of done

- Three commits landed and pushed: aggregation layer, render + script + tests, initial archive generation.
- `archive/championship_timeline/` exists with `index.md` + `playoff_brackets.md` + `playoff_records.md` + `bridesmaids.md`, generated by the script.
- Test baseline grew monotonically; zero regressions; ruff + mypy clean.
- The three A3-specific invariants (W17/W18 collapse, per-season set semantics, not-a-real-time-tracker) are each explicitly tested.
- The generated archive sanity-checks against known facts (2025 bracket matches league memory; 16 seasons represented; post-2021 clean 3-round brackets; franchise 0008's bridesmaid pattern visible).
- Cluster A is complete at the implementation level: A1, A2, A3 all specified and built.

Post-arc, the standing backlog is: template v1.0 promotion (eligible now); cluster-E (E2-light / E3) or F1 substrate-readiness arc; the Surface Admission Test (predecessor-state still needs one content-class admission attempted); the `Narrative_Angles_v2` repo/Map documentation-architecture gap (recorded in `8852a98` §8). None of those block this arc.
