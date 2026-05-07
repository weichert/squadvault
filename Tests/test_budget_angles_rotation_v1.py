"""Tests for _budget_angles rotation-hash behavior at NOTABLE pass.

Covers Commit 2 of NOTABLE-saturation Step 1 (Direction B): rotation-hash
tiebreak within strength=2 tier prevents alphabetical lockout of
late-alphabet categories (STREAK, REVENGE_GAME, etc.) when 6+ strength-2
angles compete for the 6-slot NOTABLE cap.

Mirrors the existing MINOR rotation-hash domain `category:season:week`.
"""
from __future__ import annotations

from squadvault.core.recaps.context.narrative_angles_v1 import NarrativeAngle
from squadvault.recaps.weekly_recap_lifecycle import _budget_angles


def _angle(
    category: str,
    *,
    strength: int,
    headline: str | None = None,
    franchise_ids: tuple[str, ...] = ("F1",),
) -> NarrativeAngle:
    """Construct a synthetic NarrativeAngle for testing."""
    return NarrativeAngle(
        category=category,
        headline=headline if headline is not None else f"{category} headline",
        detail=f"{category} detail",
        strength=strength,
        franchise_ids=franchise_ids,
    )


def _sorted(angles: list[NarrativeAngle]) -> list[NarrativeAngle]:
    """Apply the precondition sort that callers must satisfy."""
    return sorted(angles, key=lambda a: (-a.strength, a.category, a.headline))


# 8 strength-2 categories with STREAK alphabetically last, matching the
# saturation-probe corpus shape (probe showed STREAK as one of the
# late-alphabet categories systematically evicted under alphabetical
# tiebreak — see scripts/notable_saturation_probe.py).
_S2_CATEGORIES_8 = [
    "FAAB_FRANCHISE_EFFICIENCY",
    "FRANCHISE_ALLTIME_SCORING",
    "POSITIONAL_STRENGTH",
    "REVENGE_GAME",
    "RIVALRY",
    "SCHEDULE_STRENGTH",
    "SEASON_TRAJECTORY_MATCH",
    "STREAK",
]


def _make_8_strength_2_angles() -> list[NarrativeAngle]:
    return _sorted([_angle(c, strength=2) for c in _S2_CATEGORIES_8])


# ── Edge cases ────────────────────────────────────────────────────────


def test_empty_input_returns_empty():
    """Empty input -> empty budget. No error."""
    assert _budget_angles([], season=2024, week_index=1) == []


def test_single_headline_only():
    """One strength-3 angle -> one-element budget. No NOTABLE rotation."""
    angles = _sorted([_angle("STREAK", strength=3)])
    result = _budget_angles(angles, season=2024, week_index=1)
    assert len(result) == 1
    assert result[0].category == "STREAK"
    assert result[0].strength == 3


def test_headline_cap_respected():
    """4 strength-3 angles -> only 3 land in budget (cap=3)."""
    cats = ["A", "B", "C", "D"]
    angles = _sorted([_angle(c, strength=3) for c in cats])
    result = _budget_angles(angles, season=2024, week_index=1)
    assert len(result) == 3
    assert all(a.strength == 3 for a in result)
    assert sorted(a.category for a in result) == ["A", "B", "C"]


# ── Determinism ──────────────────────────────────────────────────────


def test_determinism_same_week_same_output():
    """Same (season, week_index) -> identical output across calls."""
    angles = _make_8_strength_2_angles()
    result1 = _budget_angles(angles, season=2024, week_index=5)
    result2 = _budget_angles(angles, season=2024, week_index=5)
    assert result1 == result2


# ── Rotation behavior at NOTABLE ────────────────────────────────────


def test_notable_cap_respected():
    """8 strength-2 angles -> exactly 6 land in NOTABLE (cap=6)."""
    angles = _make_8_strength_2_angles()
    result = _budget_angles(angles, season=2024, week_index=1)
    assert len(result) == 6
    assert all(a.strength == 2 for a in result)


def test_streak_appears_at_w1_2024():
    """At (season=2024, week_index=1), STREAK appears in NOTABLE under
    rotation hash, despite being alphabetically last of 8 categories
    (where pre-fix alphabetical tiebreak would have locked it out).
    Empirically determined; deterministic given the fixed rotation hash
    domain `category:season:week`.
    """
    angles = _make_8_strength_2_angles()
    result = _budget_angles(angles, season=2024, week_index=1)
    cats = {a.category for a in result}
    assert "STREAK" in cats, (
        f"At W1 2024, STREAK should appear in NOTABLE under rotation hash. "
        f"Got NOTABLE={sorted(cats)}. Hash domain may have changed."
    )


def test_streak_evicted_at_w12_2024():
    """At (season=2024, week_index=12), STREAK is rotated OUT of NOTABLE.
    Empirically determined; deterministic given the fixed rotation hash
    domain. Proves rotation actually rotates (vs. constant lift) — the
    alphabetically-last category sometimes loses, just not always.
    """
    angles = _make_8_strength_2_angles()
    result = _budget_angles(angles, season=2024, week_index=12)
    cats = {a.category for a in result}
    assert "STREAK" not in cats, (
        f"At W12 2024, STREAK should be evicted under rotation hash. "
        f"Got NOTABLE={sorted(cats)}. Hash domain may have changed."
    )


def test_cross_week_orderings_differ():
    """Different (season, week_index) inputs produce different NOTABLE
    compositions. Proves rotation actually rotates (vs. constant order).
    """
    angles = _make_8_strength_2_angles()
    distinct_cat_sets: set[tuple[str, ...]] = set()
    for week in range(1, 13):
        result = _budget_angles(angles, season=2024, week_index=week)
        cat_tuple = tuple(sorted(a.category for a in result))
        distinct_cat_sets.add(cat_tuple)
    # 8 strength-2 angles competing for 6 slots = C(8,6) = 28 possible
    # 6-of-8 subsets. Across 12 weeks, expect multiple distinct subsets.
    # Lower bound of 2 is the absolute minimum to prove rotation; current
    # empirical count at season=2024 weeks 1-12 is 9.
    assert len(distinct_cat_sets) >= 2, (
        f"NOTABLE composition should vary across weeks; only "
        f"{len(distinct_cat_sets)} distinct subset(s) observed in 12 weeks. "
        f"Rotation hash may be producing identical orderings."
    )


# ── Headline + NOTABLE interaction ──────────────────────────────────


def test_headline_unaffected_by_notable_rotation():
    """HEADLINE selection is week-independent — same 3 strength-3 angles
    appear regardless of (season, week_index). Only NOTABLE rotates.
    """
    s3 = [_angle(f"H{i}", strength=3) for i in range(3)]
    s2 = [_angle(c, strength=2) for c in _S2_CATEGORIES_8]
    angles = _sorted(s3 + s2)

    week1 = _budget_angles(angles, season=2024, week_index=1)
    week2 = _budget_angles(angles, season=2024, week_index=7)

    h1 = sorted(a.category for a in week1 if a.strength == 3)
    h2 = sorted(a.category for a in week2 if a.strength == 3)
    assert h1 == h2 == ["H0", "H1", "H2"]


def test_headline_precedes_notable():
    """Strength order preserved in budgeted list: HEADLINE before NOTABLE."""
    s3 = [_angle(f"H{i}", strength=3) for i in range(3)]
    s2 = [_angle(c, strength=2) for c in _S2_CATEGORIES_8]
    angles = _sorted(s3 + s2)

    result = _budget_angles(angles, season=2024, week_index=1)

    strengths = [a.strength for a in result]
    assert strengths == [3, 3, 3, 2, 2, 2, 2, 2, 2]
