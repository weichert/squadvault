"""Tests for chronicle_verifier_v1 -- RIVALRY_CHRONICLE_V1 verification gate."""
from __future__ import annotations

from squadvault.core.recaps.verification.chronicle_verifier_v1 import (
    ChronicleVerificationResult,
    verify_chronicle_v1,
)

_VALID = """# Rivalry Chronicle v1
## Stu's Crew vs Paradis' Playmakers

League: 70985
Season: 2024

## Head-to-Head Results

- Season 2024, Week 5: Stu's Crew def. Paradis' Playmakers 121.10-120.25
- Season 2024, Week 10: Stu's Crew def. Paradis' Playmakers 143.70-96.80
- Season 2024, Week 15: Paradis' Playmakers def. Stu's Crew 134.90-131.60

## Chronicle

Stu's Crew holds a 2-1 advantage over Paradis' Playmakers in their 2024 matchups.

## Trace

team_a_id: 0001
team_b_id: 0002
facts_block_hash: abc123
weeks_requested: [1, 2, 3]
weeks_with_matchups: [5, 10, 15]
canonical_event_fingerprints:
  - WEEKLY_MATCHUP_RESULT:70985:2024:W5:0001:0002
  - WEEKLY_MATCHUP_RESULT:70985:2024:W10:0001:0002
  - WEEKLY_MATCHUP_RESULT:70985:2024:W15:0001:0002

## Disclosures

This chronicle covers head-to-head matchups between the two teams.
"""


class TestStructure:
    def test_valid_passes(self) -> None:
        r = verify_chronicle_v1(_VALID)
        assert r.passed
        assert r.hard_failure_count == 0

    def test_missing_hh_section_fails(self) -> None:
        text = _VALID.replace("## Head-to-Head Results", "## Other")
        r = verify_chronicle_v1(text)
        assert not r.passed
        assert any(f.category == "STRUCTURE" for f in r.hard_failures)

    def test_missing_trace_fails(self) -> None:
        text = _VALID.replace("## Trace", "## NotTrace")
        r = verify_chronicle_v1(text)
        assert not r.passed
        assert any(f.category == "STRUCTURE" for f in r.hard_failures)

    def test_missing_disclosures_fails(self) -> None:
        text = _VALID.replace("## Disclosures", "## NotDisclosures")
        r = verify_chronicle_v1(text)
        assert not r.passed
        assert any(f.category == "STRUCTURE" for f in r.hard_failures)


class TestTrace:
    def test_missing_team_a_id_fails(self) -> None:
        text = _VALID.replace("team_a_id: 0001", "")
        r = verify_chronicle_v1(text)
        assert not r.passed
        assert any("team_a_id" in f.claim for f in r.hard_failures)

    def test_missing_facts_block_hash_fails(self) -> None:
        text = _VALID.replace("facts_block_hash: abc123", "")
        r = verify_chronicle_v1(text)
        assert not r.passed
        assert any("facts_block_hash" in f.claim for f in r.hard_failures)

    def test_fingerprint_count_mismatch_fails(self) -> None:
        text = _VALID.replace(
            "  - WEEKLY_MATCHUP_RESULT:70985:2024:W15:0001:0002\n", ""
        )
        r = verify_chronicle_v1(text)
        assert not r.passed
        assert any(f.category == "TRACE" for f in r.hard_failures)

    def test_zero_matchups_zero_fingerprints_ok(self) -> None:
        text = """# Rivalry Chronicle v1

## Head-to-Head Results

No head-to-head matchups found in the requested scope.

## Trace

team_a_id: 0001
team_b_id: 0003
facts_block_hash: 000

## Disclosures

No matchups found.
"""
        r = verify_chronicle_v1(text)
        count_failures = [f for f in r.hard_failures
                          if f.category == "TRACE" and "count" in f.claim]
        assert not count_failures


class TestScoreClaims:
    def test_no_scores_in_narrative_passes(self) -> None:
        text = _VALID.replace(
            "Stu's Crew holds a 2-1 advantage over Paradis' Playmakers in their 2024 matchups.",
            "These two teams have met three times this season.",
        )
        r = verify_chronicle_v1(text)
        score_failures = [f for f in r.hard_failures if f.category == "SCORE_CLAIM"]
        assert not score_failures

    def test_fabricated_score_in_narrative_fails(self) -> None:
        text = _VALID.replace(
            "Stu's Crew holds a 2-1 advantage over Paradis' Playmakers in their 2024 matchups.",
            "Stu's Crew won one game 150.00-90.00.",
        )
        r = verify_chronicle_v1(text)
        assert not r.passed
        score_failures = [f for f in r.hard_failures if f.category == "SCORE_CLAIM"]
        assert score_failures
        assert "150.00-90.00" in score_failures[0].claim

    def test_score_present_in_hh_and_narrative_passes(self) -> None:
        text = _VALID.replace(
            "Stu's Crew holds a 2-1 advantage over Paradis' Playmakers in their 2024 matchups.",
            "Stu's Crew won 121.10-120.25 in Week 5.",
        )
        r = verify_chronicle_v1(text)
        score_failures = [f for f in r.hard_failures if f.category == "SCORE_CLAIM"]
        assert not score_failures

    def test_no_narrative_section_skips_score_check(self) -> None:
        import re
        text = re.sub(r"## Chronicle.*?(?=## Trace)", "", _VALID, flags=re.DOTALL)
        r = verify_chronicle_v1(text)
        score_failures = [f for f in r.hard_failures if f.category == "SCORE_CLAIM"]
        assert not score_failures


class TestRestraint:
    def test_clean_narrative_no_soft_failures(self) -> None:
        r = verify_chronicle_v1(_VALID)
        assert r.soft_failure_count == 0

    def test_trending_is_soft_not_hard(self) -> None:
        text = _VALID.replace(
            "Stu's Crew holds a 2-1 advantage over Paradis' Playmakers in their 2024 matchups.",
            "Stu's Crew is trending upward this season.",
        )
        r = verify_chronicle_v1(text)
        assert any(f.category == "RESTRAINT" for f in r.soft_failures)
        assert r.passed  # soft only -- no hard failure

    def test_momentum_is_soft(self) -> None:
        text = _VALID.replace(
            "Stu's Crew holds a 2-1 advantage over Paradis' Playmakers in their 2024 matchups.",
            "Stu's Crew has all the momentum going into the playoffs.",
        )
        r = verify_chronicle_v1(text)
        assert any(f.category == "RESTRAINT" for f in r.soft_failures)


class TestReturnType:
    def test_returns_correct_type(self) -> None:
        r = verify_chronicle_v1(_VALID)
        assert isinstance(r, ChronicleVerificationResult)
        assert isinstance(r.hard_failures, tuple)
        assert isinstance(r.soft_failures, tuple)

    def test_checks_run_positive(self) -> None:
        r = verify_chronicle_v1(_VALID)
        assert r.checks_run > 0

    def test_deterministic(self) -> None:
        r1 = verify_chronicle_v1(_VALID)
        r2 = verify_chronicle_v1(_VALID)
        assert r1 == r2
