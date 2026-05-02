"""Tests for franchise directory ingest normalization."""

from squadvault.ingest.franchises._run_franchises_ingest import (
    _normalize_apostrophes,
    _normalize_row,
)


class TestNormalizeApostrophes:
    """Curly apostrophes in franchise names are normalized to straight."""

    def test_right_curly_to_straight(self):
        assert _normalize_apostrophes("Miller\u2019s") == "Miller's"

    def test_left_curly_to_straight(self):
        assert _normalize_apostrophes("\u2018twas") == "'twas"

    def test_straight_unchanged(self):
        assert _normalize_apostrophes("Ben's Gods") == "Ben's Gods"

    def test_no_apostrophe_unchanged(self):
        assert _normalize_apostrophes("Purple Haze") == "Purple Haze"

    def test_empty_string(self):
        assert _normalize_apostrophes("") == ""


class TestNormalizeRow:
    """_normalize_row normalizes curly apostrophes in name and owner."""

    def test_curly_apostrophe_in_name(self):
        row = _normalize_row({"id": "0004", "name": "Miller\u2019s Genuine Draft"})
        assert row is not None
        assert row.name == "Miller's Genuine Draft"

    def test_curly_apostrophe_in_owner(self):
        row = _normalize_row({"id": "0004", "name": "Team", "owner_name": "O\u2019Brien"})
        assert row is not None
        assert row.owner_name == "O'Brien"

    def test_straight_apostrophe_unchanged(self):
        row = _normalize_row({"id": "0001", "name": "Ben's Gods"})
        assert row is not None
        assert row.name == "Ben's Gods"

    def test_missing_id_returns_none(self):
        assert _normalize_row({"name": "No ID"}) is None

    def test_empty_id_returns_none(self):
        assert _normalize_row({"id": "", "name": "Empty ID"}) is None
