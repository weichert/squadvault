# Phase 11 -- Franchise Era-Mapping Fix

**Date:** 2026-05-16
**Status:** Closed. Fix committed.
**Finding type:** Display-layer bug. Substrate (canonical_events, memory_events) was correct throughout.

---

## 1. Discovery

Identified during a late-night product session (2026-05-16 predecessor) while reviewing the console v2 build. The championship roll displayed "Brandon Knows Ball" as the 2016 champion. Brandon Knows Ball has not won a championship; he joined the league in 2023.

---

## 2. Root cause

`build_cross_season_name_resolver` in `league_history_v1.py` built a flat
`dict[str, str]` -- one display name per franchise_id -- using ORDER BY season
DESC with first-seen-wins semantics. For slot 0010, "Brandon Knows Ball"
(most recent occupant, joined 2023) won the map entry. Every historical result
attributed to slot 0010 -- including the 2016 championship (SS Express) and
the 2013 runner-up finish (SS Express) -- resolved to "Brandon Knows Ball."

The render layer had no season context: `_resolve(name_map, franchise_id)`
cannot distinguish eras.

The substrate was correct throughout. `franchise_directory` stores one row per
(franchise_id, season, league_id) and preserves the name as it existed in each
season. The bug was entirely in the display-layer name resolution.

---

## 3. Slot 0010 era history (confirmed from franchise_directory)

| Seasons | Franchise name | Championships |
|---|---|---|
| 2010-2017 | SS Express | 1 (2016) |
| 2018-2020 | Neal's Neat Guys | 0 |
| 2021-2022 | Baber's Barristers | 0 |
| 2023-present | Brandon Knows Ball | 0 |

---

## 4. Errors in committed archive before fix

- `archive/hall_of_fame_and_shame/championship_roll.md` -- 2016 champion shown as "Brandon Knows Ball" (wrong); 2013 runner-up shown as "Brandon Knows Ball" (wrong)
- `archive/championship_timeline/playoff_brackets.md` -- all slot 0010 playoff appearances labeled "Brandon Knows Ball" regardless of season

---

## 5. Fix

Added `build_season_scoped_name_map` to `league_history_v1.py`:
- Returns `dict[tuple[str, int], str]` -- one entry per (franchise_id, season)
- Preserves the name that existed in each specific season

Added `_resolve_season(season_map, franchise_id, season)` to both render modules:
- `hall_of_fame_render_v1.py`
- `championship_timeline_render_v1.py`

Updated `render_championship_roll_markdown` and `render_playoff_brackets_markdown`
to accept `season_map` instead of `name_map` and call `_resolve_season`.

Updated both archive generation scripts to build and pass `season_map`.

Updated title counts (Titles by Franchise section) to group by era-correct display
name rather than franchise_id, so SS Express and Brandon Knows Ball appear as
separate rows.

---

## 6. Corrected all-time champion roll (16 digital-era seasons)

| Season | Champion |
|---|---|
| 2025 | Paradis' Playmakers (KP) -- 4th title |
| 2024 | Weichert's Warmongers (Steve) |
| 2023 | Italian Cavallini (Michele) |
| 2022 | Miller's Genuine Draft (Miller) |
| 2021 | Stu's Crew (Stu) |
| 2020 | Paradis' Playmakers (KP) |
| 2019 | Paradis' Playmakers (KP) |
| 2018 | Stu's Crew (Stu) |
| 2017 | Purple Haze (Pat) |
| 2016 | SS Express (departed) |
| 2015 | Eddie & the Cruisers (Eddie) |
| 2014 | Stu's Crew (Stu) |
| 2013 | Italian Cavallini (Michele) |
| 2012 | Paradis' Playmakers (KP) |
| 2011 | Italian Cavallini (Michele) |
| 2010 | Robb's Raiders (Robb) |

---

## 7. Regression test

`Tests/test_franchise_era_display_scoped_by_season.py` -- 2 tests:
- `test_2016_champion_is_ss_express_not_brandon` -- direct regression against the specific failure
- `test_era_change_same_slot_different_names` -- verifies era-split produces two separate title rows

---

## 8. Known residual (not this session)

The bridesmaids page (`archive/championship_timeline/bridesmaids.md`) and
cross-season playoff records use cross-era aggregations without per-season
context -- they resolve franchise names via the flat `build_cross_season_name_resolver`.
Slot 0010 appearances in those aggregations still resolve to "Brandon Knows Ball."
Fixing those surfaces requires threading season context into the aggregation
layer, not just the render layer. Deferred to a future session.

---

## 9. Files changed

- `src/squadvault/core/recaps/context/league_history_v1.py` -- added `build_season_scoped_name_map`
- `src/squadvault/core/recaps/render/hall_of_fame_render_v1.py` -- added `_resolve_season`; updated `render_championship_roll_markdown`
- `src/squadvault/core/recaps/render/championship_timeline_render_v1.py` -- added `_resolve_season`; updated `render_playoff_brackets_markdown`
- `scripts/generate_hall_of_fame_archive.py` -- imports and uses `build_season_scoped_name_map`
- `scripts/generate_championship_timeline_archive.py` -- imports and uses `build_season_scoped_name_map`
- `Tests/test_franchise_era_display_scoped_by_season.py` -- new regression tests (2 passing)
- `Tests/test_hall_of_fame_render_v1.py` -- updated 3 call sites to season-scoped dict
- `Tests/test_championship_timeline_render_v1.py` -- updated 1 call site to season-scoped dict
- `archive/hall_of_fame_and_shame/championship_roll.md` -- regenerated; SS Express correct
- `archive/championship_timeline/playoff_brackets.md` -- regenerated; era-correct names throughout
