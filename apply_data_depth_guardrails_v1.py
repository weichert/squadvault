#!/usr/bin/env python3
"""Apply script: Data Depth Guardrails v1

Prevents overclaiming when only a single season of data is ingested.

Problem: With only 2024 ingested, "all-time league win streak record"
really means "longest streak this season." The narrative angles module,
league history renderer, and creative layer all lacked depth awareness.

Changes:
1. narrative_angles_v1.py — suppress streak records, ALL-TIME scoring
   promotion, and rivalry angles when single-season
2. league_history_v1.py — add DATA DEPTH WARNING + relabel headings
3. creative_layer_v1.py — system prompt hard rule against all-time on
   single-season data
4. New test file: test_data_depth_guardrails_v1.py (7 tests)

Governance: Creativity must never compensate for missing context.
Test baseline: 1090 passed, 3 skipped (1083 existing + 7 new).
"""

import os

REPO = os.getcwd()


def write(relpath, content):
    path = os.path.join(REPO, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    print(f"  wrote {relpath}")


def patch(relpath, old, new):
    path = os.path.join(REPO, relpath)
    with open(path) as f:
        content = f.read()
    if old not in content:
        raise RuntimeError(f"Anchor not found in {relpath}:\n{old[:120]}...")
    if content.count(old) > 1:
        raise RuntimeError(f"Anchor appears multiple times in {relpath}")
    content = content.replace(old, new)
    with open(path, "w") as f:
        f.write(content)
    print(f"  patched {relpath}")


def main():
    print("Applying data depth guardrails v1...\n")

    # =====================================================================
    # 1. narrative_angles_v1.py — suppress streak records on single-season
    # =====================================================================
    patch(
        "src/squadvault/core/recaps/context/narrative_angles_v1.py",
        # OLD
        'def _detect_streak_records(\n'
        '    ctx: SeasonContextV1,\n'
        '    history: Optional[LeagueHistoryContextV1],\n'
        ') -> List[NarrativeAngle]:\n'
        '    """Detect when a current streak matches or approaches the league record."""\n'
        '    if not history:\n'
        '        return []',
        # NEW
        'def _detect_streak_records(\n'
        '    ctx: SeasonContextV1,\n'
        '    history: Optional[LeagueHistoryContextV1],\n'
        ') -> List[NarrativeAngle]:\n'
        '    """Detect when a current streak matches or approaches the league record.\n'
        '\n'
        '    Suppressed entirely when only a single season is ingested: with one\n'
        '    season of data, every sufficiently long streak IS the "record" by\n'
        '    definition, which is meaningless. Governance: creativity must never\n'
        '    compensate for missing context.\n'
        '    """\n'
        '    if not history:\n'
        '        return []\n'
        '\n'
        '    # Guard: single-season data makes "league record" claims meaningless\n'
        '    if not history.is_multi_season:\n'
        '        return []',
    )

    # =====================================================================
    # 2. narrative_angles_v1.py — no ALL-TIME scoring promotion on single-season
    # =====================================================================
    patch(
        "src/squadvault/core/recaps/context/narrative_angles_v1.py",
        # OLD
        '            # Check if it\'s also an all-time record\n'
        '            if (history and history.all_time_high\n'
        '                    and wh_score >= history.all_time_high.score):\n'
        '                strength = 3\n'
        '                headline = f"{wh_fid} set an ALL-TIME scoring record: {wh_score:.2f}"',
        # NEW
        '            # Check if it\'s also an all-time record (multi-season only —\n'
        '            # with single-season data, season high IS the all-time high by\n'
        '            # definition, which is not meaningful).\n'
        '            if (history and history.is_multi_season\n'
        '                    and history.all_time_high\n'
        '                    and wh_score >= history.all_time_high.score):\n'
        '                strength = 3\n'
        '                headline = f"{wh_fid} set an ALL-TIME scoring record: {wh_score:.2f}"',
    )

    # =====================================================================
    # 3. narrative_angles_v1.py — suppress rivalry angles on single-season
    # =====================================================================
    patch(
        "src/squadvault/core/recaps/context/narrative_angles_v1.py",
        # OLD
        'def _detect_rivalry_angles(\n'
        '    ctx: SeasonContextV1,\n'
        '    history: Optional[LeagueHistoryContextV1],\n'
        '    all_matchups: Optional[Sequence[HistoricalMatchup]],\n'
        ') -> List[NarrativeAngle]:\n'
        '    """Detect notable rivalry angles when this week\'s opponents have history."""\n'
        '    if not history or not all_matchups or not ctx.has_this_week_data:\n'
        '        return []',
        # NEW
        'def _detect_rivalry_angles(\n'
        '    ctx: SeasonContextV1,\n'
        '    history: Optional[LeagueHistoryContextV1],\n'
        '    all_matchups: Optional[Sequence[HistoricalMatchup]],\n'
        ') -> List[NarrativeAngle]:\n'
        '    """Detect notable rivalry angles when this week\'s opponents have history.\n'
        '\n'
        '    Suppressed when only a single season is ingested: with one season of\n'
        '    data, head-to-head records are too thin for meaningful rivalry claims.\n'
        '    """\n'
        '    if not history or not all_matchups or not ctx.has_this_week_data:\n'
        '        return []\n'
        '\n'
        '    # Guard: single-season data produces thin h2h — suppress rivalry framing\n'
        '    if not history.is_multi_season:\n'
        '        return []',
    )

    # =====================================================================
    # 4. league_history_v1.py — data depth warning + relabel headings
    # =====================================================================
    patch(
        "src/squadvault/core/recaps/context/league_history_v1.py",
        # OLD
        '    lines: List[str] = []\n'
        '\n'
        '    season_str = ", ".join(str(s) for s in ctx.seasons_available)\n'
        '    lines.append(f"League history ({len(ctx.seasons_available)} season(s): {season_str}):")\n'
        '    lines.append(f"Total matchups all-time: {ctx.total_matchups_all_time}")\n'
        '\n'
        '    # All-time standings\n'
        '    lines.append("")\n'
        '    lines.append("All-time records:")',
        # NEW
        '    lines: List[str] = []\n'
        '\n'
        '    season_str = ", ".join(str(s) for s in ctx.seasons_available)\n'
        '    lines.append(f"League history ({len(ctx.seasons_available)} season(s): {season_str}):")\n'
        '    lines.append(f"Total matchups: {ctx.total_matchups_all_time}")\n'
        '\n'
        '    # Data depth caveat — prominent warning for the LLM\n'
        '    if not ctx.is_multi_season:\n'
        '        lines.append("")\n'
        '        lines.append(\n'
        '            "** DATA DEPTH WARNING: Only one season of data is available. "\n'
        '            "All records below reflect THIS SEASON ONLY. Do NOT describe "\n'
        '            "these as \'all-time\', \'league history\', or \'league record\' — "\n'
        '            "they are single-season observations. **"\n'
        '        )\n'
        '\n'
        '    # Standings\n'
        '    scope_label = "All-time" if ctx.is_multi_season else f"Season {ctx.seasons_available[0]}"\n'
        '    lines.append("")\n'
        '    lines.append(f"{scope_label} records:")',
    )

    # Relabel scoring records
    patch(
        "src/squadvault/core/recaps/context/league_history_v1.py",
        # OLD
        '    # Scoring records\n'
        '    if ctx.all_time_high or ctx.all_time_low:\n'
        '        lines.append("")\n'
        '        lines.append("All-time scoring records:")\n'
        '        if ctx.all_time_high:\n'
        '            name = _name(ctx.all_time_high.franchise_id)\n'
        '            lines.append(\n'
        '                f"  Highest score ever: {name} — {ctx.all_time_high.score:.2f}"\n'
        '                f" (Season {ctx.all_time_high.season}, Week {ctx.all_time_high.week})"\n'
        '            )\n'
        '        if ctx.all_time_low:\n'
        '            name = _name(ctx.all_time_low.franchise_id)\n'
        '            lines.append(\n'
        '                f"  Lowest score ever: {name} — {ctx.all_time_low.score:.2f}"\n'
        '                f" (Season {ctx.all_time_low.season}, Week {ctx.all_time_low.week})"\n'
        '            )\n'
        '        if ctx.all_time_avg_score is not None:\n'
        '            lines.append(f"  League all-time average: {ctx.all_time_avg_score:.2f}")',
        # NEW
        '    # Scoring records\n'
        '    if ctx.all_time_high or ctx.all_time_low:\n'
        '        lines.append("")\n'
        '        scoring_label = "All-time scoring records:" if ctx.is_multi_season else "Season scoring records:"\n'
        '        lines.append(scoring_label)\n'
        '        if ctx.all_time_high:\n'
        '            name = _name(ctx.all_time_high.franchise_id)\n'
        '            score_label = "Highest score ever" if ctx.is_multi_season else "Season high"\n'
        '            lines.append(\n'
        '                f"  {score_label}: {name} — {ctx.all_time_high.score:.2f}"\n'
        '                f" (Season {ctx.all_time_high.season}, Week {ctx.all_time_high.week})"\n'
        '            )\n'
        '        if ctx.all_time_low:\n'
        '            name = _name(ctx.all_time_low.franchise_id)\n'
        '            score_label = "Lowest score ever" if ctx.is_multi_season else "Season low"\n'
        '            lines.append(\n'
        '                f"  {score_label}: {name} — {ctx.all_time_low.score:.2f}"\n'
        '                f" (Season {ctx.all_time_low.season}, Week {ctx.all_time_low.week})"\n'
        '            )\n'
        '        if ctx.all_time_avg_score is not None:\n'
        '            avg_label = "League all-time average" if ctx.is_multi_season else "Season average"\n'
        '            lines.append(f"  {avg_label}: {ctx.all_time_avg_score:.2f}")',
    )

    # Relabel streak records
    patch(
        "src/squadvault/core/recaps/context/league_history_v1.py",
        # OLD
        '    # Streak records\n'
        '    if ctx.longest_win_streak or ctx.longest_loss_streak:\n'
        '        lines.append("")\n'
        '        lines.append("Streak records:")',
        # NEW
        '    # Streak records\n'
        '    if ctx.longest_win_streak or ctx.longest_loss_streak:\n'
        '        lines.append("")\n'
        '        streak_label = "Streak records:" if ctx.is_multi_season else "Season streak records:"\n'
        '        lines.append(streak_label)',
    )

    # =====================================================================
    # 5. creative_layer_v1.py — system prompt data-depth hard rule
    # =====================================================================
    patch(
        "src/squadvault/ai/creative_layer_v1.py",
        # OLD
        'Hard rules (non-negotiable):\n'
        '- NEVER invent facts, scores, player names, or events not in the provided data.',
        # NEW
        'Hard rules (non-negotiable):\n'
        '- NEVER claim "all-time," "league history," or "league record" when the context \\\n'
        '  shows only one season of data. Use "this season" or "season record" instead. \\\n'
        '  If the data depth warning says single-season, take it seriously.\n'
        '- NEVER invent facts, scores, player names, or events not in the provided data.',
    )

    # =====================================================================
    # 6. Test file
    # =====================================================================
    write("Tests/test_data_depth_guardrails_v1.py", TEST_CONTENT)

    print("\nDone. Run: PYTHONPATH=src python -m pytest Tests/ -q")


# ── Test file content ────────────────────────────────────────────────

TEST_CONTENT = r'''"""Tests for data depth guardrails — single-season overclaim suppression.

Verifies that narrative angles, league history rendering, and the creative
layer prompt correctly suppress "all-time" and "league record" claims
when only a single season of data is ingested.

Governance: Creativity must never compensate for missing context.
"""

import sqlite3
from pathlib import Path
from typing import Optional

import pytest

from squadvault.core.recaps.context.season_context_v1 import (
    SeasonContextV1,
    derive_season_context_v1,
)
from squadvault.core.recaps.context.league_history_v1 import (
    LeagueHistoryContextV1,
    derive_league_history_v1,
    load_all_matchups,
    render_league_history_for_prompt,
)
from squadvault.core.recaps.context.narrative_angles_v1 import (
    NarrativeAngle,
    _detect_streak_records,
    _detect_season_records,
    _detect_rivalry_angles,
    detect_narrative_angles_v1,
    render_angles_for_prompt,
)

LEAGUE = "TEST_DEPTH"
SEASON = 2024


def _fresh_db(tmp_path):
    db_path = str(tmp_path / "depth.sqlite")
    schema = (Path(__file__).resolve().parent.parent / "src" / "squadvault"
              / "core" / "storage" / "schema.sql").read_text()
    con = sqlite3.connect(db_path)
    con.executescript(schema)
    con.close()
    return db_path


def _insert_matchup(con, *, league_id, season, week, winner_id, loser_id,
                     winner_score, loser_score):
    import json
    occurred_at = f"{season}-10-{week:02d}T12:00:00Z"
    payload = {
        "week": week,
        "winner_franchise_id": winner_id,
        "loser_franchise_id": loser_id,
        "winner_score": f"{winner_score:.2f}",
        "loser_score": f"{loser_score:.2f}",
        "is_tie": False,
    }
    payload_json = json.dumps(payload, sort_keys=True)
    ext_id = f"depth_{league_id}_{season}_{week}_{winner_id}_{loser_id}"
    con.execute(
        """INSERT INTO memory_events
           (league_id, season, external_source, external_id, event_type,
            occurred_at, ingested_at, payload_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, "test", ext_id, "WEEKLY_MATCHUP_RESULT",
         occurred_at, occurred_at, payload_json),
    )
    me_id = con.execute("SELECT last_insert_rowid()").fetchone()[0]
    fp = f"fp_{ext_id}"
    con.execute(
        """INSERT INTO canonical_events
           (league_id, season, event_type, action_fingerprint,
            best_memory_event_id, best_score, updated_at, occurred_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (league_id, season, "WEEKLY_MATCHUP_RESULT",
         fp, me_id, 100, occurred_at, occurred_at),
    )
    con.commit()


def _build_single_season_with_streak(tmp_path):
    """Single season, 6 weeks. Team A wins all 6 (creates a streak 'record')."""
    db_path = _fresh_db(tmp_path)
    con = sqlite3.connect(db_path)
    games = [
        (1, "A", "B", 120, 100), (2, "A", "C", 115, 95),
        (3, "A", "D", 125, 90), (4, "A", "E", 110, 105),
        (5, "A", "F", 130, 70), (6, "A", "B", 135, 110),
        (1, "C", "D", 95, 90), (2, "B", "D", 100, 85),
        (3, "B", "E", 102, 97), (4, "C", "F", 98, 72),
        (5, "B", "C", 100, 95), (6, "C", "D", 95, 88),
        (1, "E", "F", 88, 70), (2, "E", "F", 90, 65),
        (3, "C", "F", 95, 60), (4, "B", "D", 108, 88),
        (5, "D", "E", 92, 88), (6, "E", "F", 95, 70),
    ]
    for w, winner, loser, ws, ls in games:
        _insert_matchup(con, league_id=LEAGUE, season=SEASON, week=w,
                        winner_id=winner, loser_id=loser,
                        winner_score=ws, loser_score=ls)
    con.close()
    return db_path


def _build_multi_season(tmp_path):
    """Two seasons of data — enough for real cross-season claims."""
    db_path = _fresh_db(tmp_path)
    con = sqlite3.connect(db_path)
    for season in (2023, 2024):
        games = [
            (1, "A", "B", 120, 100), (2, "A", "C", 115, 95),
            (3, "A", "D", 125, 90), (1, "C", "D", 95, 90),
            (2, "B", "D", 100, 85), (3, "B", "C", 102, 97),
        ]
        for w, winner, loser, ws, ls in games:
            _insert_matchup(con, league_id=LEAGUE, season=season, week=w,
                            winner_id=winner, loser_id=loser,
                            winner_score=ws, loser_score=ls)
    con.close()
    return db_path


# ── Streak record suppression ────────────────────────────────────────


class TestStreakRecordSuppression:
    """_detect_streak_records must suppress when single-season."""

    def test_single_season_suppresses_streak_records(self, tmp_path):
        """With one season, no streak 'league record' angles should appear."""
        db_path = _build_single_season_with_streak(tmp_path)
        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=6,
        )
        history = derive_league_history_v1(db_path=db_path, league_id=LEAGUE)

        assert not history.is_multi_season
        # A has a 6-game win streak — but with single season, this is suppressed
        angles = _detect_streak_records(ctx, history)
        assert angles == [], (
            f"Single-season streak record angles should be empty, got: "
            f"{[a.headline for a in angles]}"
        )

    def test_multi_season_allows_streak_records(self, tmp_path):
        """With multiple seasons, streak records are allowed."""
        db_path = _build_multi_season(tmp_path)
        history = derive_league_history_v1(db_path=db_path, league_id=LEAGUE)
        assert history.is_multi_season


# ── Scoring record suppression ───────────────────────────────────────


class TestScoringRecordDepth:
    """_detect_season_records must not promote to ALL-TIME on single season."""

    def test_single_season_no_alltime_headline(self, tmp_path):
        """With one season, no angle headline should contain 'ALL-TIME'."""
        db_path = _build_single_season_with_streak(tmp_path)
        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=6,
        )
        history = derive_league_history_v1(db_path=db_path, league_id=LEAGUE)

        assert not history.is_multi_season
        angles = _detect_season_records(ctx, history)
        for a in angles:
            assert "ALL-TIME" not in a.headline, (
                f"Single-season data should never produce ALL-TIME headlines: "
                f"{a.headline}"
            )


# ── Rivalry suppression ──────────────────────────────────────────────


class TestRivalrySuppression:
    """_detect_rivalry_angles must suppress on single-season data."""

    def test_single_season_no_rivalry_angles(self, tmp_path):
        """With one season, rivalry angles should be suppressed entirely."""
        db_path = _build_single_season_with_streak(tmp_path)
        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=6,
        )
        history = derive_league_history_v1(db_path=db_path, league_id=LEAGUE)
        all_matchups = load_all_matchups(db_path, LEAGUE)

        assert not history.is_multi_season
        angles = _detect_rivalry_angles(ctx, history, all_matchups)
        assert angles == [], (
            f"Single-season rivalry angles should be empty, got: "
            f"{[a.headline for a in angles]}"
        )


# ── Full pipeline integration ────────────────────────────────────────


class TestFullPipelineDepthGuards:
    """End-to-end: single-season detect_narrative_angles_v1 has no overclaims."""

    def test_no_alltime_in_single_season_angles(self, tmp_path):
        """Full pipeline with single season produces no 'all-time' angles."""
        db_path = _build_single_season_with_streak(tmp_path)
        ctx = derive_season_context_v1(
            db_path=db_path, league_id=LEAGUE, season=SEASON, week_index=6,
        )
        history = derive_league_history_v1(db_path=db_path, league_id=LEAGUE)
        all_matchups = load_all_matchups(db_path, LEAGUE)

        result = detect_narrative_angles_v1(
            season_ctx=ctx, history_ctx=history, all_matchups=all_matchups,
        )

        for a in result.angles:
            assert "all-time" not in a.headline.lower(), (
                f"Single-season angle has 'all-time' overclaim: {a.headline}"
            )
            assert "league record" not in a.headline.lower(), (
                f"Single-season angle has 'league record' overclaim: {a.headline}"
            )


# ── Render guardrails ────────────────────────────────────────────────


class TestRenderDepthCaveat:
    """render_league_history_for_prompt must warn on single-season data."""

    def test_single_season_includes_depth_warning(self, tmp_path):
        db_path = _build_single_season_with_streak(tmp_path)
        history = derive_league_history_v1(db_path=db_path, league_id=LEAGUE)

        rendered = render_league_history_for_prompt(history)

        assert "DATA DEPTH WARNING" in rendered, (
            "Single-season render must include DATA DEPTH WARNING"
        )
        assert "All-time" not in rendered, (
            f"Single-season render should not contain 'All-time': {rendered}"
        )

    def test_multi_season_no_depth_warning(self, tmp_path):
        db_path = _build_multi_season(tmp_path)
        history = derive_league_history_v1(db_path=db_path, league_id=LEAGUE)

        rendered = render_league_history_for_prompt(history)

        assert "DATA DEPTH WARNING" not in rendered, (
            "Multi-season render should NOT include DATA DEPTH WARNING"
        )
        assert "All-time" in rendered, (
            "Multi-season render should contain 'All-time'"
        )
'''


if __name__ == "__main__":
    main()
