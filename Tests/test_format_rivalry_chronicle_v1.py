"""Tests for squadvault.chronicle.format_rivalry_chronicle_v1.

Covers: render_rivalry_chronicle_v1, UpstreamRecapQuoteV1, markers,
missing weeks handling, deterministic output.
"""
from __future__ import annotations

import pytest

from squadvault.chronicle.format_rivalry_chronicle_v1 import (
    MARK_PROVENANCE,
    MARK_QUOTES,
    MARK_WEEKS,
    UpstreamRecapQuoteV1,
    _nl,
    render_rivalry_chronicle_v1,
)


def _quote(week: int, text: str = "Recap content here.") -> UpstreamRecapQuoteV1:
    return UpstreamRecapQuoteV1(
        week_index=week,
        artifact_type="WEEKLY_RECAP",
        version=1,
        selection_fingerprint="a" * 64,
        rendered_text=text,
    )


# ── _nl helper ───────────────────────────────────────────────────────

class TestNl:
    def test_adds_newline(self):
        assert _nl("hello") == "hello\n"

    def test_already_has_newline(self):
        assert _nl("hello\n") == "hello\n"

    def test_empty_string(self):
        assert _nl("") == "\n"


# ── render_rivalry_chronicle_v1 ──────────────────────────────────────

class TestRenderRivalryChronicle:
    def test_basic_output(self):
        """Rendering with one quote produces valid output."""
        result = render_rivalry_chronicle_v1(
            league_id=70985,
            season=2024,
            week_indices_requested=[1, 2, 3],
            upstream_quotes=[_quote(1), _quote(2)],
            missing_weeks=[3],
            created_at_utc="2024-12-01T00:00:00Z",
        )
        assert "NON-CANONICAL" in result
        assert "League: 70985" in result
        assert "Season: 2024" in result

    def test_contains_all_markers(self):
        """Output must contain all structural markers."""
        result = render_rivalry_chronicle_v1(
            league_id=1, season=2024,
            week_indices_requested=[1],
            upstream_quotes=[_quote(1)],
            missing_weeks=[],
            created_at_utc="2024-12-01T00:00:00Z",
        )
        assert MARK_PROVENANCE[0] in result
        assert MARK_PROVENANCE[1] in result
        assert MARK_WEEKS[0] in result
        assert MARK_WEEKS[1] in result
        assert MARK_QUOTES[0] in result
        assert MARK_QUOTES[1] in result

    def test_missing_weeks_noted(self):
        """Missing weeks are explicitly called out."""
        result = render_rivalry_chronicle_v1(
            league_id=1, season=2024,
            week_indices_requested=[1, 2, 3],
            upstream_quotes=[_quote(1)],
            missing_weeks=[2, 3],
            created_at_utc="2024-12-01T00:00:00Z",
        )
        assert "Missing weeks: [2, 3]" in result
        assert "Some requested weeks are missing" in result

    def test_no_missing_weeks(self):
        """When all weeks present, no missing note."""
        result = render_rivalry_chronicle_v1(
            league_id=1, season=2024,
            week_indices_requested=[1],
            upstream_quotes=[_quote(1)],
            missing_weeks=[],
            created_at_utc="2024-12-01T00:00:00Z",
        )
        assert "All requested weeks had APPROVED recaps" in result
        assert "Missing weeks" not in result

    def test_quotes_included_verbatim(self):
        """Upstream recap text is included verbatim."""
        result = render_rivalry_chronicle_v1(
            league_id=1, season=2024,
            week_indices_requested=[1],
            upstream_quotes=[_quote(1, "This is the exact recap text.")],
            missing_weeks=[],
            created_at_utc="2024-12-01T00:00:00Z",
        )
        assert "This is the exact recap text." in result

    def test_quotes_ordered_by_week(self):
        """Quotes are sorted by week_index regardless of input order."""
        result = render_rivalry_chronicle_v1(
            league_id=1, season=2024,
            week_indices_requested=[3, 1, 2],
            upstream_quotes=[_quote(3, "Week 3"), _quote(1, "Week 1"), _quote(2, "Week 2")],
            missing_weeks=[],
            created_at_utc="2024-12-01T00:00:00Z",
        )
        pos_w1 = result.index("Week 1")
        pos_w2 = result.index("Week 2")
        pos_w3 = result.index("Week 3")
        assert pos_w1 < pos_w2 < pos_w3

    def test_provenance_includes_fingerprints(self):
        """Provenance section includes selection fingerprints."""
        fp = "b" * 64
        result = render_rivalry_chronicle_v1(
            league_id=1, season=2024,
            week_indices_requested=[1],
            upstream_quotes=[UpstreamRecapQuoteV1(
                week_index=1, artifact_type="WEEKLY_RECAP",
                version=2, selection_fingerprint=fp,
                rendered_text="text",
            )],
            missing_weeks=[],
            created_at_utc="2024-12-01T00:00:00Z",
        )
        assert fp in result
        assert "version: 2" in result

    def test_empty_quotes_list(self):
        """Empty quotes still produces valid structure."""
        result = render_rivalry_chronicle_v1(
            league_id=1, season=2024,
            week_indices_requested=[1, 2],
            upstream_quotes=[],
            missing_weeks=[1, 2],
            created_at_utc="2024-12-01T00:00:00Z",
        )
        assert MARK_QUOTES[0] in result
        assert MARK_QUOTES[1] in result
        assert "included_weeks: []" in result

    def test_deterministic(self):
        """Same inputs always produce identical output."""
        kwargs = dict(
            league_id=1, season=2024,
            week_indices_requested=[1, 2],
            upstream_quotes=[_quote(1), _quote(2)],
            missing_weeks=[],
            created_at_utc="2024-12-01T00:00:00Z",
        )
        assert render_rivalry_chronicle_v1(**kwargs) == render_rivalry_chronicle_v1(**kwargs)

    def test_created_at_in_output(self):
        ts = "2024-12-25T12:00:00Z"
        result = render_rivalry_chronicle_v1(
            league_id=1, season=2024,
            week_indices_requested=[],
            upstream_quotes=[],
            missing_weeks=[],
            created_at_utc=ts,
        )
        assert f"CreatedAtUTC: {ts}" in result


# ── UpstreamRecapQuoteV1 ─────────────────────────────────────────────

class TestUpstreamRecapQuoteV1:
    def test_frozen(self):
        q = _quote(1)
        with pytest.raises(AttributeError):
            q.week_index = 2

    def test_fields(self):
        q = _quote(5, "content")
        assert q.week_index == 5
        assert q.artifact_type == "WEEKLY_RECAP"
        assert q.version == 1
        assert q.rendered_text == "content"
        assert len(q.selection_fingerprint) == 64
