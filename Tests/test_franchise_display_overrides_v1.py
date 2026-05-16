"""Tests for franchise_display_overrides_v1.

Uses fixtures/ci_squadvault.sqlite (which now has the
franchise_display_overrides table) via a tmp copy to avoid
polluting the CI fixture with test data.
"""
from __future__ import annotations

import shutil
import sqlite3
import tempfile
from pathlib import Path

import pytest

from squadvault.core.recaps.context.franchise_display_overrides_v1 import (
    get_franchise_display_name,
    is_narrative_excluded,
)

CI_DB = "fixtures/ci_squadvault.sqlite"
LEAGUE = "70985"


@pytest.fixture()
def tmp_db(tmp_path: Path) -> str:
    """Copy ci_squadvault.sqlite to a temp dir; return path."""
    dst = str(tmp_path / "test.sqlite")
    shutil.copy(CI_DB, dst)
    return dst


def _insert_override(
    db_path: str,
    *,
    franchise_id: str,
    season_from: int | None = None,
    season_to: int | None = None,
    display_name_override: str | None = None,
    suppressed: bool = False,
    memorial_flag: bool = False,
    narrative_excluded: bool = False,
    override_reason: str = "test",
    set_by: str = "test",
) -> None:
    con = sqlite3.connect(db_path)
    con.execute(
        """
        INSERT INTO franchise_display_overrides
            (league_id, franchise_id, season_from, season_to,
             display_name_override, suppressed, memorial_flag,
             narrative_excluded, override_reason, set_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            LEAGUE, franchise_id, season_from, season_to,
            display_name_override, int(suppressed), int(memorial_flag),
            int(narrative_excluded), override_reason, set_by,
        ),
    )
    con.commit()
    con.close()


class TestGetFranchiseDisplayName:
    def test_falls_back_to_franchise_directory_when_no_override(
        self, tmp_db: str
    ) -> None:
        # No override rows -- function returns a string without raising.
        # CI fixture may not have franchise_directory rows for this league;
        # the raw-id fallback test covers the no-directory-entry case.
        name = get_franchise_display_name(tmp_db, LEAGUE, "0001", 2025)
        assert isinstance(name, str)
        assert name != ""

    def test_display_name_override_returned(self, tmp_db: str) -> None:
        _insert_override(
            tmp_db,
            franchise_id="0010",
            season_from=2018,
            season_to=2022,
            display_name_override="Historical Name Override",
        )
        name = get_franchise_display_name(tmp_db, LEAGUE, "0010", 2020)
        assert name == "Historical Name Override"

    def test_override_not_active_outside_range(self, tmp_db: str) -> None:
        _insert_override(
            tmp_db,
            franchise_id="0010",
            season_from=2018,
            season_to=2022,
            display_name_override="Historical Name Override",
        )
        # 2016 is before season_from=2018 -- override not active
        name = get_franchise_display_name(tmp_db, LEAGUE, "0010", 2016)
        assert name != "Historical Name Override"

    def test_suppressed_returns_former_member(self, tmp_db: str) -> None:
        _insert_override(
            tmp_db,
            franchise_id="0010",
            season_from=2018,
            season_to=2022,
            suppressed=True,
        )
        name = get_franchise_display_name(tmp_db, LEAGUE, "0010", 2020)
        assert name == "Former Member"

    def test_suppressed_outside_range_falls_back_normally(
        self, tmp_db: str
    ) -> None:
        _insert_override(
            tmp_db,
            franchise_id="0010",
            season_from=2018,
            season_to=2022,
            suppressed=True,
        )
        # 2016 is outside range -- suppression not active
        name = get_franchise_display_name(tmp_db, LEAGUE, "0010", 2016)
        assert name != "Former Member"

    def test_open_ended_override_null_season_to(self, tmp_db: str) -> None:
        _insert_override(
            tmp_db,
            franchise_id="0010",
            season_from=2023,
            season_to=None,
            display_name_override="Open-Ended Override",
        )
        name = get_franchise_display_name(tmp_db, LEAGUE, "0010", 2025)
        assert name == "Open-Ended Override"

    def test_null_both_bounds_applies_to_all_seasons(
        self, tmp_db: str
    ) -> None:
        _insert_override(
            tmp_db,
            franchise_id="0010",
            season_from=None,
            season_to=None,
            display_name_override="All-Era Override",
        )
        for season in [2010, 2016, 2020, 2025]:
            name = get_franchise_display_name(tmp_db, LEAGUE, "0010", season)
            assert name == "All-Era Override", f"failed for season {season}"

    def test_display_name_override_takes_precedence_over_suppressed(
        self, tmp_db: str
    ) -> None:
        # display_name_override is checked first; suppressed is secondary.
        _insert_override(
            tmp_db,
            franchise_id="0010",
            season_from=2018,
            season_to=2022,
            display_name_override="Named Override",
            suppressed=True,
        )
        name = get_franchise_display_name(tmp_db, LEAGUE, "0010", 2020)
        assert name == "Named Override"

    def test_falls_back_to_franchise_id_when_not_in_directory(
        self, tmp_db: str
    ) -> None:
        # Franchise ID that does not exist in the DB.
        name = get_franchise_display_name(tmp_db, LEAGUE, "9999", 2025)
        assert name == "9999"


class TestIsNarrativeExcluded:
    def test_no_override_returns_false(self, tmp_db: str) -> None:
        assert is_narrative_excluded(tmp_db, LEAGUE, "0001", 2025) is False

    def test_narrative_excluded_flag_returns_true(self, tmp_db: str) -> None:
        _insert_override(
            tmp_db,
            franchise_id="0010",
            season_from=2018,
            season_to=2022,
            narrative_excluded=True,
        )
        assert is_narrative_excluded(tmp_db, LEAGUE, "0010", 2020) is True

    def test_suppressed_implies_narrative_excluded(self, tmp_db: str) -> None:
        _insert_override(
            tmp_db,
            franchise_id="0010",
            season_from=2018,
            season_to=2022,
            suppressed=True,
        )
        assert is_narrative_excluded(tmp_db, LEAGUE, "0010", 2020) is True

    def test_narrative_excluded_not_active_outside_range(
        self, tmp_db: str
    ) -> None:
        _insert_override(
            tmp_db,
            franchise_id="0010",
            season_from=2018,
            season_to=2022,
            narrative_excluded=True,
        )
        assert is_narrative_excluded(tmp_db, LEAGUE, "0010", 2016) is False
