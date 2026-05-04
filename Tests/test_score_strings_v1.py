"""Tests for score_strings_v1 helper and the three render-site call paths.

Covers:
- Helper format correctness across typical / tied / zero / high / negative scores.
- Helper float-coerce edge cases the deterministic_bullets call site
  passes through (string inputs, integer-valued floats, large floats).
- _ascii_punct interaction: " to " passes through unchanged.
- Behavioral: synthetic deterministic_bullets matchup-result bullet
  renders with the new format.
- Behavioral: synthetic UPSET narrative angle's detail string renders
  with the new format.
"""

from __future__ import annotations

from squadvault.core.recaps.render.deterministic_bullets_v1 import (
    CanonicalEventRow,
    _ascii_punct,
    render_deterministic_bullets_v1,
)
from squadvault.core.recaps.render.score_strings_v1 import format_matchup_score_str


# =====================================================================
# Helper format correctness
# =====================================================================

def test_format_typical_scores() -> None:
    assert format_matchup_score_str(107.65, 65.40) == "107.65 to 65.40"


def test_format_tied_scores() -> None:
    # Format does not encode tie/no-tie semantics; the caller does.
    assert format_matchup_score_str(100.50, 100.50) == "100.50 to 100.50"


def test_format_zero_loser() -> None:
    assert format_matchup_score_str(120.00, 0.00) == "120.00 to 0.00"


def test_format_zero_winner_tied_zero_zero() -> None:
    # Edge: 0-0 tie. Format renders both as 0.00.
    assert format_matchup_score_str(0.0, 0.0) == "0.00 to 0.00"


def test_format_high_scores() -> None:
    assert format_matchup_score_str(199.99, 198.50) == "199.99 to 198.50"


def test_format_three_digit_scores() -> None:
    # Fantasy scores can hit 200+. Format does not pad.
    assert format_matchup_score_str(215.30, 100.05) == "215.30 to 100.05"


def test_format_negative_score() -> None:
    # Penalties can produce negative scores. Format renders literally.
    assert format_matchup_score_str(-2.50, -10.00) == "-2.50 to -10.00"


# =====================================================================
# Float-coerce edge cases (mirrors deterministic_bullets:290 call shape)
# =====================================================================

def test_format_accepts_integer_input() -> None:
    # int → float is implicit in Python's f-string formatting.
    assert format_matchup_score_str(100, 50) == "100.00 to 50.00"


def test_format_accepts_integer_valued_float() -> None:
    assert format_matchup_score_str(100.0, 50.0) == "100.00 to 50.00"


def test_format_accepts_large_float() -> None:
    # Sanity: no overflow at fantasy-football-realistic magnitudes.
    assert format_matchup_score_str(999.99, 0.01) == "999.99 to 0.01"


def test_format_rounds_to_two_decimals() -> None:
    # Inputs with > 2 decimals get rounded by f-string formatting.
    # Note: exact rounding behavior depends on IEEE 754 representation
    # of the input. We pick values whose .2f rounding is unambiguous
    # (avoiding edge cases like 65.405 which stores slightly > .405).
    assert format_matchup_score_str(107.123, 65.456) == "107.12 to 65.46"


# =====================================================================
# _ascii_punct interaction
# =====================================================================

def test_ascii_punct_leaves_to_format_unchanged() -> None:
    """The bullet pipeline runs _ascii_punct on the final string.

    The "to" format contains no curly-apostrophe, en-dash, or em-dash
    characters, so it must pass through unchanged. This is a guard
    against future expansion of _ascii_punct's replacement set.
    """
    formatted = format_matchup_score_str(107.65, 65.40)
    assert _ascii_punct(formatted) == formatted
    # Also test with surrounding bullet context.
    bullet = f"Winner beat Loser {formatted}."
    assert _ascii_punct(bullet) == bullet


# =====================================================================
# Behavioral: deterministic_bullets matchup-result bullet
# =====================================================================

def _matchup_event(payload: dict, occurred_at: str = "2025-12-01T10:00:00Z") -> CanonicalEventRow:
    return CanonicalEventRow(
        canonical_id=f"test-{occurred_at}",
        occurred_at=occurred_at,
        event_type="WEEKLY_MATCHUP_RESULT",
        payload=payload,
    )


def test_bullet_renders_score_in_to_format() -> None:
    """A WEEKLY_MATCHUP_RESULT event renders with " to " separator,
    not the historical hyphen-separated form."""
    rows = [_matchup_event({
        "winner_franchise_id": "0001",
        "loser_franchise_id": "0002",
        "winner_score": 107.65,
        "loser_score": 65.40,
        "is_tie": False,
    })]

    def resolver(fid: object) -> str:
        return {"0001": "Winners FC", "0002": "Losers FC"}.get(str(fid), "Unknown")

    bullets = render_deterministic_bullets_v1(rows, team_resolver=resolver)
    assert len(bullets) == 1
    assert "107.65 to 65.40" in bullets[0]
    # And critically, the old hyphen-paired form should NOT appear.
    assert "107.65-65.40" not in bullets[0]


def test_bullet_handles_tied_matchup() -> None:
    rows = [_matchup_event({
        "winner_franchise_id": "0001",
        "loser_franchise_id": "0002",
        "winner_score": 100.00,
        "loser_score": 100.00,
        "is_tie": True,
    })]

    def resolver(fid: object) -> str:
        return {"0001": "A", "0002": "B"}.get(str(fid), "Unknown")

    bullets = render_deterministic_bullets_v1(rows, team_resolver=resolver)
    assert len(bullets) == 1
    assert "100.00 to 100.00" in bullets[0]
    assert "tied" in bullets[0]


def test_bullet_skips_score_when_winner_score_missing() -> None:
    """Preserves _safe()-equivalent semantic: missing scores → no score in bullet."""
    rows = [_matchup_event({
        "winner_franchise_id": "0001",
        "loser_franchise_id": "0002",
        # winner_score deliberately absent
        "loser_score": 65.40,
        "is_tie": False,
    })]

    def resolver(fid: object) -> str:
        return {"0001": "A", "0002": "B"}.get(str(fid), "Unknown")

    bullets = render_deterministic_bullets_v1(rows, team_resolver=resolver)
    assert len(bullets) == 1
    # No score string in the bullet.
    assert "65.40" not in bullets[0]
    assert " to " not in bullets[0]


def test_bullet_skips_score_when_unparseable() -> None:
    """Malformed score values are skipped rather than rendered raw."""
    rows = [_matchup_event({
        "winner_franchise_id": "0001",
        "loser_franchise_id": "0002",
        "winner_score": "not_a_number",
        "loser_score": 65.40,
        "is_tie": False,
    })]

    def resolver(fid: object) -> str:
        return {"0001": "A", "0002": "B"}.get(str(fid), "Unknown")

    bullets = render_deterministic_bullets_v1(rows, team_resolver=resolver)
    assert len(bullets) == 1
    assert "not_a_number" not in bullets[0]
    assert " to " not in bullets[0]


def test_bullet_handles_string_score_input() -> None:
    """MFL-ingested scores can arrive as strings; float-coerce handles them."""
    rows = [_matchup_event({
        "winner_franchise_id": "0001",
        "loser_franchise_id": "0002",
        "winner_score": "107.65",
        "loser_score": "65.40",
        "is_tie": False,
    })]

    def resolver(fid: object) -> str:
        return {"0001": "A", "0002": "B"}.get(str(fid), "Unknown")

    bullets = render_deterministic_bullets_v1(rows, team_resolver=resolver)
    assert len(bullets) == 1
    assert "107.65 to 65.40" in bullets[0]


# =====================================================================
# Behavioral: narrative_angles UPSET-angle detail string
# =====================================================================

def _stub_team_record(fid: str, wins: int, losses: int) -> "TeamRecord":
    from squadvault.core.recaps.context.season_context_v1 import TeamRecord
    return TeamRecord(
        franchise_id=fid, wins=wins, losses=losses, ties=0,
        points_for=100.0 * (wins + losses), points_against=95.0 * (wins + losses),
        current_streak=0,
    )


def _stub_matchup(
    winner_id: str, loser_id: str, winner_score: float, loser_score: float
) -> "WeekMatchupContext":
    from squadvault.core.recaps.context.season_context_v1 import WeekMatchupContext
    return WeekMatchupContext(
        winner_id=winner_id, loser_id=loser_id,
        winner_score=winner_score, loser_score=loser_score,
        margin=winner_score - loser_score, is_tie=False,
        winner_record_after=None, loser_record_after=None,
    )


def _make_context(matchups: tuple, standings_order: list[tuple[str, int, int]]):
    """Build a minimal SeasonContextV1 with the given matchups and a
    standings list. standings_order is [(franchise_id, wins, losses), ...]
    in rank order (best first); the rank is the list position + 1."""
    from squadvault.core.recaps.context.season_context_v1 import SeasonContextV1
    standings = tuple(_stub_team_record(fid, w, l) for fid, w, l in standings_order)
    return SeasonContextV1(
        league_id="test_league",
        season=2025,
        through_week=13,
        standings=standings,
        week_matchups=matchups,
        week_high_scorer=None,
        week_low_scorer=None,
        week_closest_game=None,
        week_biggest_blowout=None,
        season_high=None,
        season_low=None,
        season_avg_score=None,
        total_matchups_through_week=len(matchups) * 13,
        matchups_this_week=len(matchups),
        playoff_info=None,
    )


def test_narrative_angles_upset_gap_3_branch_uses_to_format() -> None:
    """The deep-upset branch (gap >= 3) renders score in the new format."""
    from squadvault.core.recaps.context.narrative_angles_v1 import _detect_upsets

    matchup = _stub_matchup("F1", "F2", 107.65, 65.40)
    # Standings: F2 ranked 1st, F1 ranked 8th → gap = 8 - 1 = 7, hits gap >= 3 branch.
    # _detect_upsets requires >= 4 standings entries.
    standings_order = [
        ("F2", 12, 0),  # rank 1
        ("FA", 11, 1),  # rank 2
        ("FB", 10, 2),  # rank 3
        ("FC",  9, 3),  # rank 4
        ("FD",  8, 4),  # rank 5
        ("FE",  7, 5),  # rank 6
        ("FF",  6, 6),  # rank 7
        ("F1",  4, 8),  # rank 8 (winner — the upset)
    ]
    ctx = _make_context((matchup,), standings_order)

    angles = _detect_upsets(ctx)
    upset_angles = [a for a in angles if a.category == "UPSET"]
    assert len(upset_angles) == 1, f"Expected 1 UPSET angle, got: {upset_angles}"
    detail = upset_angles[0].detail
    assert "107.65 to 65.40" in detail, f"Expected 'to' format in: {detail}"
    assert "107.65-65.40" not in detail, f"Old hyphen form leaked into: {detail}"


def test_narrative_angles_upset_gap_2_branch_uses_to_format() -> None:
    """The shallower-upset branch (gap >= 2 but < 3) also uses the new format."""
    from squadvault.core.recaps.context.narrative_angles_v1 import _detect_upsets

    matchup = _stub_matchup("F1", "F2", 99.50, 95.25)
    # Standings: F2 rank 2, F1 rank 4 → gap = 2, hits gap >= 2 (but not gap >= 3) branch.
    standings_order = [
        ("FA", 12, 0),  # rank 1
        ("F2", 11, 1),  # rank 2 (loser — favored)
        ("FB", 10, 2),  # rank 3
        ("F1",  9, 3),  # rank 4 (winner — slight upset)
    ]
    ctx = _make_context((matchup,), standings_order)

    angles = _detect_upsets(ctx)
    upset_angles = [a for a in angles if a.category == "UPSET"]
    assert len(upset_angles) == 1, f"Expected 1 UPSET angle, got: {upset_angles}"
    detail = upset_angles[0].detail
    assert "99.50 to 95.25" in detail, f"Expected 'to' format in: {detail}"
    assert "99.50-95.25" not in detail, f"Old hyphen form leaked into: {detail}"
