# A3 Implementation -- Session Observation
## SquadVault | Phase 11 | 2026-05-16

**Predecessor:** Franchise era-mapping fix + commissioner override table (`c12b74d`, `c9ad04d`)
**Session type:** Inventory + gap analysis + residual fix
**Outcome:** A3 implementation arc closed

---

## 1. Pre-build finding

A3 infrastructure was substantially pre-built as part of the F1 arc
(commits `97bfd83` / `cb6a796` / `66265e0`) before this session. The
following existed at session start:

- `src/squadvault/core/recaps/context/championship_timeline_aggregations_v1.py` (531 lines)
- `src/squadvault/core/recaps/render/championship_timeline_render_v1.py`
- `scripts/generate_championship_timeline_archive.py`
- `archive/championship_timeline/` -- all four files (index.md, playoff_brackets.md, playoff_records.md, bridesmaids.md)
- `Tests/test_championship_timeline_aggregations_v1.py` -- comprehensive aggregation tests
- `Tests/test_championship_timeline_render_v1.py` -- render unit tests
- `Tests/test_championship_timeline_archive_layout_v1.py` -- layout-invariant test
  (different name from brief's expected `test_championship_timeline_layout_v1.py`; content equivalent)

---

## 2. Gap analysis results

### Already done (no gaps found)

- Spec section 5.1 required files -- all four archive files present
- Archive layout invariant test (`test_championship_timeline_archive_layout_v1.py`) --
  five assertions: file set, H1 titles, scope-declaration, non-empty content, cross-link
- W17/W18 collapse-by-content invariant (section 6.2) -- six explicit test cases
- Per-season set semantics invariant (section 6.3) -- explicit test
- Section 6.6 no engagement instrumentation -- confirmed absent

### Residual closed this session

**Bridesmaids era-mapping (slot 0010 "Brandon Knows Ball" -> "SS Express")**

Root cause: `render_bridesmaids_markdown` accepted `name_map: dict[str, str]`
(flat cross-season resolver) and called `_resolve(name_map, r.franchise_id)`.
The flat resolver returns the current-era name for slot 0010 (Brandon Knows Ball).
The 2013 runner-up season predates that name.

Structural assessment: `BridesmaidRecord` carries `runner_up_seasons: tuple[int, ...]`
-- per-season data is available. Fix is tractable with no aggregation-layer changes.

Fix: changed `render_bridesmaids_markdown` parameter from `name_map: dict[str, str]`
to `season_map: dict[tuple[str, int], str]`. Each row's Franchise column now resolves
via `_resolve_season(season_map, r.franchise_id, r.runner_up_seasons[0])` -- anchoring
to the franchise's earliest runner-up season. Same era-mapping mechanism
`render_playoff_brackets_markdown` already used; generation script already builds
`season_map` and now threads it to the bridesmaids render function.

### Residual NOT closed this session

playoff_records.md era-mapping: `FranchisePlayoffRecord` carries only aggregate
integers (no per-season context). The flat resolver is structurally correct for a
cross-season leaderboard. "Brandon Knows Ball" on playoff_records is correct
behavior -- it is the current franchise identity for that slot. No action required.

---

## 3. Test changes

- `test_surfaces_titles_column_for_bridesmaid_archetype`: map key updated
  from `{"C": "Charlie"}` to `{("C", 2014): "Charlie"}`
- `test_preserves_input_order`: updated to season-keyed map
- Added `test_era_correct_name_resolution`: directly tests the slot 0010 scenario --
  `("0010", 2013)` -> "SS Express"; asserts "SS Express" in output, "Brandon Knows Ball" not

---

## 4. Gate results

- Ruff: zero errors (68 source files)
- Mypy: no issues found (68 source files)
- Tests: 2222 passed / 3 skipped (baseline was 2221/3 -- net +1 for new test)

---

## 5. A3 spec compliance summary

| Spec requirement | Status |
|---|---|
| section 5.1 required files (4 archive pages) | Complete |
| section 5.5 archive layout-invariant test | Complete |
| section 5.5 W17/W18 collapse-by-content invariant test | Complete |
| section 5.5 per-season set semantics invariant test | Complete |
| section 6.2 W17/W18 collapse content-based | Complete |
| section 6.3 per-season set semantics | Complete |
| section 6.4 archive cross-link (playoff_brackets.md -> championship_roll.md) | Complete |
| section 6.6 no engagement instrumentation | Complete |
| Bridesmaids era-mapping residual (from predecessor section 8) | Closed this session |

---

## 6. Open items (carry forward)

- A2 anchor correction: test rename from `test_cavallini_mahomes_2018_qb_anchor_regression`
  (player 9988 is Antonio Brown, not Mahomes); correction memo pending
- Pre-commit gate (from reset arc)
- Documentation Map v1.6 registration sweep
- Roadmap seasons-count revision
- 2021 DRAFT_PICK zero-event characterization
- Surface Admission Test: four registered per-surface constitutional memos; one-content-class still gating
- Template v1.0 promotion: two clean post-ratification exercises now complete (A2 + A3)
