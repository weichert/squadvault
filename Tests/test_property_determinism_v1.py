"""Property tests for determinism invariants.

Property: identical inputs always produce identical outputs for
bullets, directive fingerprints, and selection fingerprints.
"""
from __future__ import annotations

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from squadvault.core.eal.eal_calibration_v1 import (
    compute_directive_fingerprint,
)
from squadvault.core.recaps.render.deterministic_bullets_v1 import (
    CanonicalEventRow,
    render_deterministic_bullets_v1,
)

EVENT_TYPES = st.sampled_from([
    "MATCHUP_RESULT", "WEEKLY_MATCHUP_RESULT",
    "TRANSACTION_TRADE", "TRADE",
    "WAIVER_BID_AWARDED",
    "TRANSACTION_FREE_AGENT",
    "DRAFT_PICK",
    "TRANSACTION_BBID_WAIVER",
    "TRANSACTION_NOISE",
    "LEAGUE_EXPANSION",
])

canonical_event_rows = st.lists(
    st.builds(
        CanonicalEventRow,
        canonical_id=st.text(alphabet="abcdef0123456789", min_size=1, max_size=8),
        occurred_at=st.from_regex(r"2024-10-[0-2][0-9]T12:00:00Z", fullmatch=True),
        event_type=EVENT_TYPES,
        payload=st.fixed_dictionaries({
            "winner_franchise_id": st.text(min_size=1, max_size=5),
            "loser_franchise_id": st.text(min_size=1, max_size=5),
            "from_franchise_id": st.text(min_size=1, max_size=5),
            "to_franchise_id": st.text(min_size=1, max_size=5),
            "player_id": st.text(min_size=1, max_size=5),
            "franchise_id": st.text(min_size=1, max_size=5),
            "bid": st.integers(min_value=0, max_value=200),
            "round": st.integers(min_value=1, max_value=15),
            "pick": st.integers(min_value=1, max_value=200),
            "winner_score": st.integers(min_value=50, max_value=200),
            "loser_score": st.integers(min_value=50, max_value=200),
        }),
    ),
    min_size=0,
    max_size=25,
)


@given(rows=canonical_event_rows)
@settings(max_examples=50, deadline=2000)
def test_bullets_deterministic(rows):
    """Same rows always produce the same bullets."""
    result1 = render_deterministic_bullets_v1(rows)
    result2 = render_deterministic_bullets_v1(rows)
    assert result1 == result2


@given(rows=canonical_event_rows)
@settings(max_examples=50, deadline=2000)
def test_bullets_order_independent_of_input_order(rows):
    """Output is the same regardless of input order (function sorts internally)."""
    import random
    # Only test with unique sort keys to avoid undefined stable-sort ordering
    keys = [(r.occurred_at, r.event_type, r.canonical_id) for r in rows]
    assume(len(keys) == len(set(keys)))
    shuffled = list(rows)
    random.shuffle(shuffled)
    result_original = render_deterministic_bullets_v1(rows)
    result_shuffled = render_deterministic_bullets_v1(shuffled)
    assert result_original == result_shuffled


@given(
    window_id=st.text(min_size=1, max_size=10),
    cal_id=st.text(min_size=1, max_size=10),
    directive=st.sampled_from(["high_restraint", "prefer_silence", "neutral"]),
    signal_count=st.integers(min_value=0, max_value=100),
)
@settings(max_examples=50, deadline=2000)
def test_fingerprint_deterministic(window_id, cal_id, directive, signal_count):
    """Same inputs always produce the same fingerprint."""
    inputs = {"signal_count": signal_count}
    fp1 = compute_directive_fingerprint(
        window_id=window_id, source_calibration_id=cal_id,
        restraint_directive=directive, inputs=inputs,
    )
    fp2 = compute_directive_fingerprint(
        window_id=window_id, source_calibration_id=cal_id,
        restraint_directive=directive, inputs=inputs,
    )
    assert fp1 == fp2
    assert len(fp1) == 64  # SHA-256 hex digest
