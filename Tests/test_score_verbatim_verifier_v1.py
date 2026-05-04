"""Tests for verify_score_strings_verbatim (Policy A, HARD verbatim).

Step 5 of the four-step plan documented in d76e71b. Policy selected
per _observations/OBSERVATIONS_2026_05_03_SCORE_RENDERING_POST_FIX_CORRECTION.md:
post-fix evidence shows 100% verbatim compliance, the brief's
selection rule (>= 95% VERBATIM -> Policy A) cleanly applies.

The check is additive to verify_scores. The existing decimal-pair
verifier in verify_scores remains format-agnostic across Step 2's
format change (per brief Preamble check 1), and continues to enforce
decimal correctness. This new check enforces the verbatim FORMAT
of the canonical score string.
"""

from __future__ import annotations

from squadvault.core.recaps.verification.recap_verifier_v1 import (
    VerificationFailure,
    _MatchupFact,
    verify_score_strings_verbatim,
)

# Canonical fixture: W13 2025 KP-vs-Brandon style matchup. Same shape
# as the prose evidence in the Step 4 correction memo.
_PAIR = _MatchupFact(
    season=2025, week=13,
    winner_id="0001", loser_id="0002",
    winner_score=107.65, loser_score=65.40,
)


# =====================================================================
# Pass conditions
# =====================================================================

def test_passes_when_winner_first_verbatim_present() -> None:
    """Verbatim string in 'X to Y' order — the canonical post-Step-2 form."""
    prose = "Paradis' Playmakers took down Brandon 107.65 to 65.40 in a rout."
    failures = verify_score_strings_verbatim(prose, [_PAIR], week=13)
    assert failures == []


def test_passes_when_loser_first_verbatim_present() -> None:
    """Verbatim string in reverse order — model may write 'X fell to Y A.AA to B.BB'."""
    prose = "Brandon fell to Paradis' Playmakers 65.40 to 107.65 in a tough one."
    failures = verify_score_strings_verbatim(prose, [_PAIR], week=13)
    assert failures == []


def test_passes_when_verbatim_embedded_in_clause() -> None:
    """The verbatim string can be flanked by player attribution / margin clauses."""
    prose = (
        "Paradis' Playmakers extended their streak with a 107.65 to 65.40 "
        "victory, fueled by Patrick Mahomes' 28-point afternoon."
    )
    failures = verify_score_strings_verbatim(prose, [_PAIR], week=13)
    assert failures == []


def test_passes_with_multiple_matchups_all_verbatim() -> None:
    """All five W13 pairs verbatim — exactly the post-fix observed pattern."""
    pairs = [
        _PAIR,
        _MatchupFact(season=2025, week=13, winner_id="0003", loser_id="0004",
                     winner_score=149.95, loser_score=105.10),
        _MatchupFact(season=2025, week=13, winner_id="0005", loser_id="0006",
                     winner_score=112.15, loser_score=100.95),
    ]
    prose = (
        "Paradis' Playmakers handled Brandon 107.65 to 65.40. "
        "Cavallini crushed Eddie 149.95 to 105.10. "
        "Miller squeaked past Ben 112.15 to 100.95."
    )
    failures = verify_score_strings_verbatim(prose, pairs, week=13)
    assert failures == []


# =====================================================================
# HARD-fail conditions
# =====================================================================

def test_fails_HARD_on_paraphrase_other() -> None:
    """Both decimals present but not in verbatim paired form — Policy A rejects."""
    prose = (
        "Paradis' Playmakers put up 107.65 in the week's biggest rout, while "
        "Brandon's 65.40 was nowhere close to enough."
    )
    failures = verify_score_strings_verbatim(prose, [_PAIR], week=13)
    assert len(failures) == 1
    assert failures[0].category == "SCORE_VERBATIM"
    assert failures[0].severity == "HARD"
    assert "0001" in failures[0].claim
    assert "0002" in failures[0].claim
    assert "107.65 to 65.40" in failures[0].evidence


def test_fails_HARD_on_rounded_only() -> None:
    """The brief's targeted hazard: model rounds and uses hyphen separator."""
    prose = "Paradis' Playmakers took down Brandon 108-65 in a rout."
    failures = verify_score_strings_verbatim(prose, [_PAIR], week=13)
    assert len(failures) == 1
    assert failures[0].severity == "HARD"


def test_fails_HARD_on_margin_only() -> None:
    """Model elides scores entirely in narrative voice."""
    prose = "Paradis' Playmakers took down Brandon by 42 points in a rout."
    failures = verify_score_strings_verbatim(prose, [_PAIR], week=13)
    assert len(failures) == 1
    assert failures[0].severity == "HARD"


def test_fails_HARD_on_old_hyphen_format() -> None:
    """Pre-Step-2 hyphen-paired format is NOT accepted under Policy A.

    Step 2 changed the data layer's emitted format. The verifier
    enforces the new format; old-format prose is a fault.
    """
    prose = "Paradis' Playmakers took down Brandon 107.65-65.40 in a rout."
    failures = verify_score_strings_verbatim(prose, [_PAIR], week=13)
    assert len(failures) == 1
    assert failures[0].severity == "HARD"


def test_fails_for_each_missing_pair_independently() -> None:
    """Multi-matchup recap with one verbatim hit and one miss reports one failure."""
    pair_a = _PAIR
    pair_b = _MatchupFact(season=2025, week=13, winner_id="0003", loser_id="0004",
                          winner_score=149.95, loser_score=105.10)
    prose = (
        "Paradis' Playmakers took down Brandon 107.65 to 65.40. "
        "Cavallini routed Eddie by nearly 45 points."  # no verbatim score string
    )
    failures = verify_score_strings_verbatim(prose, [pair_a, pair_b], week=13)
    assert len(failures) == 1
    assert "0003" in failures[0].claim
    assert "0004" in failures[0].claim


# =====================================================================
# Defensive / scope behavior
# =====================================================================

def test_skips_matchups_from_other_weeks() -> None:
    """A pair with .week=12 is not flagged when called with week=13."""
    pair_w12 = _MatchupFact(season=2025, week=12, winner_id="X", loser_id="Y",
                            winner_score=100.0, loser_score=80.0)
    prose = "X took down Y by 20 points."  # no verbatim score string for w12 pair
    failures = verify_score_strings_verbatim(prose, [pair_w12], week=13)
    # Even though the prose lacks the w12 verbatim score, week=13 invocation
    # should not flag the w12 pair.
    assert failures == []


def test_returns_empty_on_empty_week_matchups() -> None:
    """No canonical matchups -> nothing to verify -> [] (matches verify_scores
    pattern at line 610-611)."""
    failures = verify_score_strings_verbatim("any prose", [], week=13)
    assert failures == []


def test_returns_empty_when_all_matchups_filtered_out() -> None:
    """All matchups in another week -> still []."""
    pair_w12 = _MatchupFact(season=2025, week=12, winner_id="X", loser_id="Y",
                            winner_score=100.0, loser_score=80.0)
    failures = verify_score_strings_verbatim("any prose", [pair_w12], week=13)
    assert failures == []


# =====================================================================
# Integration with format_matchup_score_str helper (single source of truth)
# =====================================================================

def test_uses_format_helper_so_format_changes_track() -> None:
    """If format_matchup_score_str ever changes, the verifier's expectation
    changes with it. We verify this by constructing the expected string via
    the helper, then asserting the verifier accepts that exact string."""
    from squadvault.core.recaps.render.score_strings_v1 import format_matchup_score_str

    expected = format_matchup_score_str(_PAIR.winner_score, _PAIR.loser_score)
    prose = f"Result: {expected}."
    failures = verify_score_strings_verbatim(prose, [_PAIR], week=13)
    assert failures == []


def test_evidence_string_quotes_canonical_format() -> None:
    """Failure evidence references the verbatim string the model should have
    produced — quoting it back lets the reviewer see exactly what was expected."""
    prose = "Paradis' Playmakers won big."  # neither score nor verbatim form
    failures = verify_score_strings_verbatim(prose, [_PAIR], week=13)
    assert len(failures) == 1
    # Evidence should contain the helper's output for both orderings
    assert "107.65 to 65.40" in failures[0].evidence
    assert "65.40 to 107.65" in failures[0].evidence


# =====================================================================
# VerificationFailure shape (sanity check)
# =====================================================================

def test_failure_uses_dedicated_category() -> None:
    """SCORE_VERBATIM is its own category, distinct from SCORE.
    Lets the review surface and telemetry distinguish format-of-score
    failures from value-of-score failures."""
    prose = "no scores here at all"
    failures = verify_score_strings_verbatim(prose, [_PAIR], week=13)
    assert len(failures) == 1
    assert failures[0].category == "SCORE_VERBATIM"
    assert failures[0].category != "SCORE"


def test_failure_is_VerificationFailure_instance() -> None:
    """Defensive: ensure the function returns the canonical type."""
    prose = "no scores here"
    failures = verify_score_strings_verbatim(prose, [_PAIR], week=13)
    assert isinstance(failures[0], VerificationFailure)
