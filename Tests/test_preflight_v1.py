"""Tests for squadvault.recaps.preflight

Covers: recap_preflight_verdict (generate OK, DNG on empty events),
PreflightVerdict defaults, evidence structure.
"""
from __future__ import annotations

from squadvault.recaps.dng_reasons import DNGReason
from squadvault.recaps.preflight import (
    PreflightVerdict,
    PreflightVerdictType,
    recap_preflight_verdict,
)


class TestPreflightVerdict:
    def test_generate_ok_with_events(self):
        v = recap_preflight_verdict(
            league_id="L1", season=2024, week=5,
            canonical_events=[{"id": 1}, {"id": 2}],
        )
        assert v.verdict == PreflightVerdictType.GENERATE_OK
        assert v.reason_code is None
        assert v.evidence["canonical_event_count"] == 2

    def test_dng_on_empty_events(self):
        v = recap_preflight_verdict(
            league_id="L1", season=2024, week=5,
            canonical_events=[],
        )
        assert v.verdict == PreflightVerdictType.DO_NOT_GENERATE
        assert v.reason_code == DNGReason.DNG_INCOMPLETE_WEEK
        assert v.evidence["canonical_event_count"] == 0

    def test_evidence_contains_context(self):
        v = recap_preflight_verdict(
            league_id="MyLeague", season=2023, week=10,
            canonical_events=[1],
        )
        assert v.evidence["league_id"] == "MyLeague"
        assert v.evidence["season"] == 2023
        assert v.evidence["week"] == 10

    def test_default_evidence_not_none(self):
        v = PreflightVerdict(verdict=PreflightVerdictType.GENERATE_OK)
        assert v.evidence == {}

    def test_frozen_dataclass(self):
        v = PreflightVerdict(verdict=PreflightVerdictType.GENERATE_OK)
        import pytest
        with pytest.raises(AttributeError):
            v.verdict = PreflightVerdictType.DO_NOT_GENERATE
