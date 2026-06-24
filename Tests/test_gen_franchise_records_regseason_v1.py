"""Regression guard for the franchise_season_records W-L + PF regular-season defect.

The defect (shipped, corrected 2026-06-24): build_records sourced W-L/ties/points_for from
compute_all_season_records over ALL matchups, so the championship final leaked into the two
finalists' W-L/PF every season (champion +1 win, runner-up +1 loss, both PF inflated by the
final's score) - while points_against already excluded it. Ratified-correct anchor
(adjudication 9.3): 2024 franchise 0005 = 10-6, not 11-6.

This is the guard whose absence let the defect ship green. It pins that build_records excludes
the championship week (>= _champ_week) from W-L AND points_for, keeps the full set for the
champion/runner-up labelling (compute_championship_roll), and leaves non-finalists untouched.
compute_all_season_records itself (shared with the hall-of-fame archive) is NOT modified - the
fix filters its input, which this test verifies.
"""
from __future__ import annotations

import scripts.gen_franchise_records as gfr


class _M:
    """Minimal HistoricalMatchup stand-in (the fields build_records' helpers read)."""

    def __init__(self, season, week, winner_id, loser_id, winner_score, loser_score, is_tie=False):
        self.season = season
        self.week = week
        self.winner_id = winner_id
        self.loser_id = loser_id
        self.winner_score = winner_score
        self.loser_score = loser_score
        self.is_tie = is_tie
        self.margin = winner_score - loser_score


def _season_2024():
    """Synthetic 2024 (champ week 17). Champion 0005 is 10-6 in the regular season then wins the
    title at wk17 (all-games would read 11-6). A separate pairing (0003 vs 0007) is a clean
    16-game regular season - the championship filter must be a no-op for them."""
    ms: list[_M] = []
    # 0005 vs 0002: regular season 10-6 for 0005 (wins wk1-10, loses wk11-16)
    for w in range(1, 11):
        ms.append(_M(2024, w, "0005", "0002", 120.0, 100.0))
    for w in range(11, 17):
        ms.append(_M(2024, w, "0002", "0005", 110.0, 90.0))
    # the championship final at wk17 (0005 beats 0002) - must NOT count in the record
    ms.append(_M(2024, 17, "0005", "0002", 148.9, 135.8))
    # a separate non-finalist pairing, weeks 1-16 (boundary: untouched by the filter)
    for w in range(1, 17):
        ms.append(_M(2024, w, "0003", "0007", 105.0, 95.0))
    return ms


def test_championship_excluded_from_wl_and_pf(monkeypatch):
    monkeypatch.setattr(gfr, "load_all_matchups", lambda db, lg: _season_2024())
    rows = gfr.build_records("ignored", "70985")
    d = {(r["franchise_id"], r["season"]): r for r in rows}

    champ = d[("0005", 2024)]
    # The wk17 title is excluded: 10-6, NOT 11-6 (the defect's signature).
    assert (champ["wins"], champ["losses"], champ["ties"]) == (10, 6, 0), champ
    # points_for excludes the 148.9 title game: 10*120 + 6*90 = 1740.0.
    assert champ["points_for"] == 1740.0, champ["points_for"]
    assert champ["result"] == "CHAMPION"

    runner = d[("0002", 2024)]
    # Runner-up's title loss is excluded: 6-10 (the +1 loss removed); PF excludes the 135.8 final.
    assert (runner["wins"], runner["losses"]) == (6, 10), runner
    assert runner["points_for"] == 100.0 * 10 + 110.0 * 6, runner["points_for"]
    assert runner["result"] == "RUNNER_UP"


def test_non_finalist_record_unchanged_by_filter(monkeypatch):
    monkeypatch.setattr(gfr, "load_all_matchups", lambda db, lg: _season_2024())
    rows = gfr.build_records("ignored", "70985")
    d = {(r["franchise_id"], r["season"]): r for r in rows}
    # 0003 never plays in the championship week, so the regular-season filter is a no-op.
    out = d[("0003", 2024)]
    assert (out["wins"], out["losses"]) == (16, 0), out
    assert out["points_for"] == 105.0 * 16, out["points_for"]
    assert out["result"] == ""
