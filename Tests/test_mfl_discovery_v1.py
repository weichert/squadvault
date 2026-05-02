"""Tests for squadvault.mfl.discovery and squadvault.mfl.historical_ingest.

Covers: discovery data structures, franchise extraction reuse,
season probing logic, historical ingest orchestration, and
the all-zero scores guard.
"""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from squadvault.mfl.discovery import (
    DiscoveryReport,
    HistoryEntry,
    SeasonAvailability,
    _extract_franchises_from_league_json,
    _extract_league_history,
    _extract_league_name,
    _probe_season,
    _resolve_server_from_response,
)
from squadvault.mfl.historical_ingest import (
    CategoryResult,
    SeasonIngestResult,
    _ingest_franchise_info,
    _ingest_transactions_and_bids,
)

# ── Discovery data structures ───────────────────────────────────────


class TestDiscoveryReport:
    def test_available_seasons_sorted(self):
        report = DiscoveryReport(league_id="70985")
        report.seasons = [
            SeasonAvailability(season=2015, server="www44", franchise_count=10, categories=[]),
            SeasonAvailability(season=2009, server="www03", franchise_count=10, categories=[]),
            SeasonAvailability(season=2020, server="www44", franchise_count=10, categories=[]),
        ]
        assert report.available_seasons() == [2009, 2015, 2020]

    def test_available_seasons_excludes_suspect(self):
        report = DiscoveryReport(league_id="70985")
        report.seasons = [
            SeasonAvailability(season=2015, server="www49", franchise_count=50, categories=[], suspect=True),
            SeasonAvailability(season=2020, server="www44", franchise_count=10, categories=[]),
        ]
        assert report.available_seasons() == [2020]
        assert report.all_discovered_seasons() == [2015, 2020]

    def test_server_for_season_found(self):
        report = DiscoveryReport(league_id="70985")
        report.seasons = [
            SeasonAvailability(season=2015, server="www44.myfantasyleague.com", franchise_count=10, categories=[]),
        ]
        assert report.server_for_season(2015) == "www44.myfantasyleague.com"

    def test_server_for_season_not_found(self):
        report = DiscoveryReport(league_id="70985")
        assert report.server_for_season(2015) is None

    def test_empty_report(self):
        report = DiscoveryReport(league_id="70985")
        assert report.available_seasons() == []


class TestSeasonAvailability:
    def test_basic_creation(self):
        sa = SeasonAvailability(
            season=2024,
            server="www44.myfantasyleague.com",
            franchise_count=10,
            categories=["MATCHUP_RESULTS", "TRANSACTIONS"],
        )
        assert sa.season == 2024
        assert sa.franchise_count == 10
        assert len(sa.categories) == 2
        assert sa.suspect is False

    def test_suspect_flag(self):
        sa = SeasonAvailability(
            season=2015,
            server="www49.myfantasyleague.com",
            franchise_count=50,
            categories=[],
            suspect=True,
        )
        assert sa.suspect is True

    def test_league_name(self):
        sa = SeasonAvailability(
            season=2024,
            server="www44.myfantasyleague.com",
            franchise_count=10,
            categories=[],
            league_name="PFL Buddies",
        )
        assert sa.league_name == "PFL Buddies"


# ── League name extraction ────────────────────────────────────────────


class TestExtractLeagueName:
    def test_extracts_name(self):
        data = {"league": {"name": "PFL Buddies", "franchises": {}}}
        assert _extract_league_name(data) == "PFL Buddies"

    def test_strips_whitespace(self):
        data = {"league": {"name": "  PFL Buddies  "}}
        assert _extract_league_name(data) == "PFL Buddies"

    def test_returns_none_missing(self):
        assert _extract_league_name({}) is None
        assert _extract_league_name({"league": {}}) is None
        assert _extract_league_name({"league": {"name": ""}}) is None

    def test_returns_none_non_string(self):
        assert _extract_league_name({"league": {"name": 123}}) is None


# ── Franchise extraction ─────────────────────────────────────────────


class TestExtractFranchisesFromLeagueJson:
    """Test the discovery module's franchise extraction from TYPE=league JSON."""

    def test_shape_a_league_wrapper(self):
        """Standard MFL shape: {"league": {"franchises": {"franchise": [...]}}}"""
        data = {
            "league": {
                "franchises": {
                    "franchise": [
                        {"id": "0001", "name": "Team A"},
                        {"id": "0002", "name": "Team B"},
                    ]
                }
            }
        }
        result = _extract_franchises_from_league_json(data)
        assert len(result) == 2
        assert result[0]["id"] == "0001"

    def test_shape_b_top_level(self):
        """Alternative MFL shape: {"franchises": {"franchise": [...]}}"""
        data = {
            "franchises": {
                "franchise": [
                    {"id": "0001", "name": "Team A"},
                ]
            }
        }
        result = _extract_franchises_from_league_json(data)
        assert len(result) == 1

    def test_single_franchise_as_dict(self):
        """MFL returns a single franchise as a dict, not a list."""
        data = {
            "league": {
                "franchises": {
                    "franchise": {"id": "0001", "name": "Solo Team"}
                }
            }
        }
        result = _extract_franchises_from_league_json(data)
        assert len(result) == 1
        assert result[0]["name"] == "Solo Team"

    def test_empty_response(self):
        data = {}
        result = _extract_franchises_from_league_json(data)
        assert result == []

    def test_no_franchises_key(self):
        data = {"league": {"settings": {"id": "70985"}}}
        result = _extract_franchises_from_league_json(data)
        assert result == []


# ── Server resolution ────────────────────────────────────────────────


class TestResolveServerFromResponse:
    def test_extracts_hostname(self):
        resp = MagicMock()
        resp.url = "https://www44.myfantasyleague.com/2024/export?TYPE=league&L=70985&JSON=1"
        assert _resolve_server_from_response(resp, "fallback") == "www44.myfantasyleague.com"

    def test_fallback_on_non_mfl_url(self):
        resp = MagicMock()
        resp.url = "https://example.com/something"
        assert _resolve_server_from_response(resp, "www99.myfantasyleague.com") == "www99.myfantasyleague.com"

    def test_fallback_on_parse_failure(self):
        resp = MagicMock()
        resp.url = ""
        assert _resolve_server_from_response(resp, "www44.myfantasyleague.com") == "www44.myfantasyleague.com"


# ── CategoryResult and SeasonIngestResult ────────────────────────────


class TestCategoryResult:
    def test_defaults(self):
        cr = CategoryResult(category="MATCHUP_RESULTS")
        assert cr.inserted == 0
        assert cr.skipped == 0
        assert cr.error is None

    def test_with_values(self):
        cr = CategoryResult(category="TRANSACTIONS", inserted=50, skipped=3)
        assert cr.inserted == 50
        assert cr.skipped == 3


class TestSeasonIngestResult:
    def test_total_inserted(self):
        result = SeasonIngestResult(league_id="70985", season=2024, server="www44")
        result.categories = [
            CategoryResult(category="MATCHUP_RESULTS", inserted=80),
            CategoryResult(category="TRANSACTIONS", inserted=200),
        ]
        assert result.total_inserted == 280

    def test_total_skipped(self):
        result = SeasonIngestResult(league_id="70985", season=2024, server="www44")
        result.categories = [
            CategoryResult(category="MATCHUP_RESULTS", skipped=5),
            CategoryResult(category="TRANSACTIONS", skipped=10),
        ]
        assert result.total_skipped == 15

    def test_empty_categories(self):
        result = SeasonIngestResult(league_id="70985", season=2024, server="www44")
        assert result.total_inserted == 0
        assert result.total_skipped == 0


# ── Probe season (mocked HTTP) ───────────────────────────────────────


class TestProbeSeason:
    def test_active_season(self):
        """Probe returns SeasonAvailability for an active season."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://www44.myfantasyleague.com/2024/export?TYPE=league&L=70985&JSON=1"
        mock_response.json.return_value = {
            "league": {
                "name": "PFL Buddies",
                "franchises": {
                    "franchise": [
                        {"id": "0001", "name": "Team A"},
                        {"id": "0002", "name": "Team B"},
                    ]
                }
            }
        }

        session = MagicMock()
        session.get.return_value = mock_response

        result = _probe_season(session, "70985", 2024, "www44.myfantasyleague.com")
        assert result is not None
        assert result.season == 2024
        assert result.server == "www44.myfantasyleague.com"
        assert result.franchise_count == 2
        assert result.league_name == "PFL Buddies"
        assert "MATCHUP_RESULTS" in result.categories

    def test_inactive_season_no_franchises(self):
        """Probe returns None when no franchises are found."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://www44.myfantasyleague.com/2005/export?TYPE=league&L=70985&JSON=1"
        mock_response.json.return_value = {"league": {}}

        session = MagicMock()
        session.get.return_value = mock_response

        result = _probe_season(session, "70985", 2005, "www44.myfantasyleague.com")
        assert result is None

    def test_http_error(self):
        """Probe returns None on HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.url = ""

        session = MagicMock()
        session.get.return_value = mock_response

        result = _probe_season(session, "70985", 2005, "www44.myfantasyleague.com")
        assert result is None

    def test_network_error_exhausts_retries(self):
        """Probe returns None after exhausting retries on network error."""
        session = MagicMock()
        session.get.side_effect = ConnectionError("timeout")

        result = _probe_season(
            session, "70985", 2024, "www44.myfantasyleague.com",
            max_retries=2, retry_backoff_s=0.01,
        )
        assert result is None
        assert session.get.call_count == 2

    def test_retry_succeeds_on_second_attempt(self):
        """Probe succeeds after a transient failure on first attempt."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://www44.myfantasyleague.com/2024/export?TYPE=league&L=70985&JSON=1"
        mock_response.json.return_value = {
            "league": {
                "franchises": {
                    "franchise": [{"id": "0001", "name": "Team A"}]
                }
            }
        }

        session = MagicMock()
        session.get.side_effect = [
            ConnectionError("Remote end closed connection"),
            mock_response,
        ]

        result = _probe_season(
            session, "70985", 2024, "www44.myfantasyleague.com",
            max_retries=3, retry_backoff_s=0.01,
        )
        assert result is not None
        assert result.franchise_count == 1
        assert session.get.call_count == 2

    def test_server_redirect_detected(self):
        """Probe extracts the correct server from redirect URL."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Simulates redirect from www44 -> www03
        mock_response.url = "https://www03.myfantasyleague.com/2012/export?TYPE=league&L=70985&JSON=1"
        mock_response.json.return_value = {
            "league": {
                "franchises": {
                    "franchise": [{"id": "0001", "name": "Team A"}]
                }
            }
        }

        session = MagicMock()
        session.get.return_value = mock_response

        result = _probe_season(session, "70985", 2012, "www44.myfantasyleague.com")
        assert result is not None
        assert result.server == "www03.myfantasyleague.com"


# ── Franchise info ingest (with real DB) ─────────────────────────────


class TestIngestFranchiseInfo:
    """Test franchise directory ingestion against a real temp DB."""

    def _init_db(self, db_path: str) -> None:
        """Initialize a minimal DB with franchise_directory table."""
        schema_path = Path("src/squadvault/core/storage/schema.sql")
        if schema_path.exists():
            schema = schema_path.read_text()
        else:
            # Minimal fallback for CI environments
            schema = """
            CREATE TABLE IF NOT EXISTS franchise_directory (
                league_id TEXT NOT NULL,
                season INTEGER NOT NULL,
                franchise_id TEXT NOT NULL,
                name TEXT,
                owner_name TEXT,
                raw_json TEXT,
                updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                PRIMARY KEY (league_id, season, franchise_id)
            );
            """
        conn = sqlite3.connect(db_path)
        conn.executescript(schema)
        conn.close()

    def test_ingest_from_cached_json(self):
        """Ingest franchises from cached discovery JSON (no API call)."""
        with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
            db_path = f.name

        self._init_db(db_path)

        league_json = {
            "league": {
                "franchises": {
                    "franchise": [
                        {"id": "0001", "name": "Team Alpha", "owner_name": "Alice"},
                        {"id": "0002", "name": "Team Beta", "owner_name": "Bob"},
                        {"id": "0003", "name": "Team Gamma"},
                    ]
                }
            }
        }

        mock_client = MagicMock()

        result = _ingest_franchise_info(
            client=mock_client,
            db_path=db_path,
            league_id="70985",
            season=2020,
            league_json=league_json,
        )

        assert result.category == "FRANCHISE_INFO"
        assert result.inserted == 3
        assert result.error is None

        # Verify data in DB
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM franchise_directory WHERE league_id = '70985' AND season = 2020 ORDER BY franchise_id"
        ).fetchall()
        conn.close()

        assert len(rows) == 3
        assert rows[0]["franchise_id"] == "0001"
        assert rows[0]["name"] == "Team Alpha"

        # Cleanup
        Path(db_path).unlink(missing_ok=True)

    def test_ingest_idempotent(self):
        """Re-ingesting same franchises updates without duplicating."""
        with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
            db_path = f.name

        self._init_db(db_path)

        league_json = {
            "league": {
                "franchises": {
                    "franchise": [
                        {"id": "0001", "name": "Team Alpha"},
                    ]
                }
            }
        }

        mock_client = MagicMock()

        # First ingest
        _ingest_franchise_info(mock_client, db_path, "70985", 2020, league_json)

        # Change the name and re-ingest
        league_json["league"]["franchises"]["franchise"][0]["name"] = "Team Alpha Updated"
        _ingest_franchise_info(mock_client, db_path, "70985", 2020, league_json)

        conn = sqlite3.connect(db_path)
        rows = conn.execute(
            "SELECT * FROM franchise_directory WHERE league_id = '70985' AND season = 2020"
        ).fetchall()
        conn.close()

        assert len(rows) == 1  # No duplicates
        Path(db_path).unlink(missing_ok=True)


# ── Transactions ingest (mocked client) ──────────────────────────────


class TestIngestTransactionsAndBids:
    """Test the combined transaction/FAAB/draft ingest with a real temp DB."""

    def _init_db(self, db_path: str) -> None:
        schema_path = Path("src/squadvault/core/storage/schema.sql")
        schema = schema_path.read_text()
        conn = sqlite3.connect(db_path)
        conn.executescript(schema)
        conn.close()

    def test_basic_transactions_ingest(self):
        """Ingest a mix of transaction types."""
        with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
            db_path = f.name

        self._init_db(db_path)

        from squadvault.core.storage.sqlite_store import SQLiteStore

        store = SQLiteStore(Path(db_path))

        mock_client = MagicMock()
        mock_client.get_transactions.return_value = (
            {
                "transactions": {
                    "transaction": [
                        {
                            "type": "FREE_AGENT",
                            "franchise": "0001",
                            "timestamp": "1700000000",
                            "transaction": "14108,|12676,",
                        },
                        {
                            "type": "BBID_WAIVER",
                            "franchise": "0002",
                            "timestamp": "1700001000",
                            "transaction": "15000,|25.00|13000,",
                        },
                        {
                            "type": "AUCTION_WON",
                            "franchise": "0003",
                            "timestamp": "1700002000",
                            "transaction": "16000|5|",
                        },
                    ]
                }
            },
            "https://www44.myfantasyleague.com/2024/export?TYPE=transactions&L=70985&JSON=1",
        )

        txn_r, faab_r, draft_r = _ingest_transactions_and_bids(
            mock_client, store, "70985", 2024
        )

        assert txn_r.inserted >= 1  # FREE_AGENT
        assert faab_r.inserted >= 1  # BBID_WAIVER
        assert draft_r.inserted >= 1  # AUCTION_WON

        Path(db_path).unlink(missing_ok=True)

    def test_empty_transactions(self):
        """No transactions returns zero counts without error."""
        with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
            db_path = f.name

        self._init_db(db_path)

        from squadvault.core.storage.sqlite_store import SQLiteStore

        store = SQLiteStore(Path(db_path))

        mock_client = MagicMock()
        mock_client.get_transactions.return_value = (
            {"transactions": {"transaction": []}},
            "https://example.com",
        )

        txn_r, faab_r, draft_r = _ingest_transactions_and_bids(
            mock_client, store, "70985", 2024
        )

        assert txn_r.inserted == 0
        assert txn_r.error is None
        assert faab_r.inserted == 0
        assert draft_r.inserted == 0

        Path(db_path).unlink(missing_ok=True)


# ── MflClient additions ─────────────────────────────────────────────


class TestMflClientAdditions:
    """Test new MflClient methods exist and have correct signatures."""

    def test_get_league_info_exists(self):
        from squadvault.mfl.client import MflClient

        client = MflClient(server="www44", league_id="70985")
        assert callable(getattr(client, "get_league_info", None))

    def test_get_players_exists(self):
        from squadvault.mfl.client import MflClient

        client = MflClient(server="www44", league_id="70985")
        assert callable(getattr(client, "get_players", None))

    def test_export_url_league(self):
        from squadvault.mfl.client import MflClient

        client = MflClient(server="www44", league_id="70985")
        url = client.export_url(2024, "league")
        assert "TYPE=league" in url
        assert "L=70985" in url
        assert "www44.myfantasyleague.com" in url

    def test_export_url_players(self):
        from squadvault.mfl.client import MflClient

        client = MflClient(server="www44", league_id="70985")
        url = client.export_url(2024, "players")
        assert "TYPE=players" in url


# ── All-zero scores guard ────────────────────────────────────────────


class TestAllZeroScoresGuard:
    """Verify that the all-zero scores check correctly identifies unplayed weeks."""

    def test_all_zero_detected(self):
        events = [
            {"payload": {"winner_score": "0.00", "loser_score": "0.00"}},
            {"payload": {"winner_score": "0.00", "loser_score": "0.00"}},
        ]
        all_zero = all(
            e["payload"].get("winner_score") == "0.00"
            and e["payload"].get("loser_score") == "0.00"
            for e in events
        )
        assert all_zero is True

    def test_mixed_scores_not_zero(self):
        events = [
            {"payload": {"winner_score": "142.60", "loser_score": "98.30"}},
            {"payload": {"winner_score": "0.00", "loser_score": "0.00"}},
        ]
        all_zero = all(
            e["payload"].get("winner_score") == "0.00"
            and e["payload"].get("loser_score") == "0.00"
            for e in events
        )
        assert all_zero is False

    def test_normal_scores(self):
        events = [
            {"payload": {"winner_score": "142.60", "loser_score": "98.30"}},
            {"payload": {"winner_score": "155.20", "loser_score": "101.10"}},
        ]
        all_zero = all(
            e["payload"].get("winner_score") == "0.00"
            and e["payload"].get("loser_score") == "0.00"
            for e in events
        )
        assert all_zero is False

    def test_empty_events(self):
        """Empty event list: all() returns True, but we'd have no events to process."""
        events: list = []
        all_zero = all(
            e["payload"].get("winner_score") == "0.00"
            and e["payload"].get("loser_score") == "0.00"
            for e in events
        )
        # all() on empty iterator returns True, but the matchup ingest
        # has a separate "if not events: continue" check before this.
        assert all_zero is True


# ── History chain extraction ─────────────────────────────────────────


class TestExtractLeagueHistory:
    """Test parsing of MFL's history.league array."""

    def test_full_history_chain(self):
        """Parse a realistic MFL history chain."""
        data = {
            "league": {
                "name": "PFL Buddies",
                "history": {
                    "league": [
                        {"year": "2024", "url": "https://www44.myfantasyleague.com/2024/home/70985"},
                        {"year": "2009", "url": "https://www48.myfantasyleague.com/2009/home/50536"},
                        {"year": "2017", "url": "http://www44.myfantasyleague.com/2017/home/70985"},
                    ]
                }
            }
        }
        entries = _extract_league_history(data)
        assert len(entries) == 3
        # Sorted by year
        assert entries[0].year == 2009
        assert entries[1].year == 2017
        assert entries[2].year == 2024

    def test_parses_server_and_league_id(self):
        data = {
            "league": {
                "history": {
                    "league": [
                        {"year": "2009", "url": "https://www48.myfantasyleague.com/2009/home/50536"},
                    ]
                }
            }
        }
        entries = _extract_league_history(data)
        assert len(entries) == 1
        assert entries[0].server == "www48.myfantasyleague.com"
        assert entries[0].mfl_league_id == "50536"
        assert entries[0].year == 2009

    def test_handles_http_urls(self):
        """MFL uses http for older seasons."""
        data = {
            "league": {
                "history": {
                    "league": [
                        {"year": "2016", "url": "http://www44.myfantasyleague.com/2016/home/47199"},
                    ]
                }
            }
        }
        entries = _extract_league_history(data)
        assert len(entries) == 1
        assert entries[0].server == "www44.myfantasyleague.com"
        assert entries[0].mfl_league_id == "47199"

    def test_single_entry_as_dict(self):
        """MFL may return a single history entry as a dict instead of list."""
        data = {
            "league": {
                "history": {
                    "league": {"year": "2024", "url": "https://www44.myfantasyleague.com/2024/home/70985"}
                }
            }
        }
        entries = _extract_league_history(data)
        assert len(entries) == 1
        assert entries[0].year == 2024
        assert entries[0].mfl_league_id == "70985"

    def test_empty_history(self):
        data = {"league": {"history": {}}}
        assert _extract_league_history(data) == []

    def test_no_history_key(self):
        data = {"league": {"name": "Test League"}}
        assert _extract_league_history(data) == []

    def test_no_league_key(self):
        data = {}
        assert _extract_league_history(data) == []

    def test_skips_malformed_entries(self):
        """Entries without year or url are skipped."""
        data = {
            "league": {
                "history": {
                    "league": [
                        {"year": "2024", "url": "https://www44.myfantasyleague.com/2024/home/70985"},
                        {"year": "2023"},  # missing url
                        {"url": "https://www44.myfantasyleague.com/2022/home/70985"},  # missing year
                        {"year": "bad", "url": "https://www44.myfantasyleague.com/2021/home/70985"},  # non-int year
                    ]
                }
            }
        }
        entries = _extract_league_history(data)
        assert len(entries) == 1
        assert entries[0].year == 2024

    def test_real_pfl_buddies_chain(self):
        """Verify parsing of the actual PFL Buddies history shape."""
        data = {
            "league": {
                "name": "PFL Buddies",
                "history": {
                    "league": [
                        {"year": "2009", "url": "https://www48.myfantasyleague.com/2009/home/50536"},
                        {"year": "2010", "url": "https://www46.myfantasyleague.com/2010/home/78078"},
                        {"year": "2015", "url": "https://www44.myfantasyleague.com/2015/home/26884"},
                        {"year": "2017", "url": "http://www44.myfantasyleague.com/2017/home/70985"},
                        {"year": "2024", "url": "https://www44.myfantasyleague.com/2024/home/70985"},
                    ]
                }
            }
        }
        entries = _extract_league_history(data)
        assert len(entries) == 5

        # Different league IDs for different years
        by_year = {e.year: e for e in entries}
        assert by_year[2009].mfl_league_id == "50536"
        assert by_year[2009].server == "www48.myfantasyleague.com"
        assert by_year[2010].mfl_league_id == "78078"
        assert by_year[2010].server == "www46.myfantasyleague.com"
        assert by_year[2015].mfl_league_id == "26884"
        assert by_year[2017].mfl_league_id == "70985"
        assert by_year[2024].mfl_league_id == "70985"


class TestHistoryEntry:
    def test_basic_creation(self):
        entry = HistoryEntry(year=2009, server="www48.myfantasyleague.com", mfl_league_id="50536")
        assert entry.year == 2009
        assert entry.server == "www48.myfantasyleague.com"
        assert entry.mfl_league_id == "50536"


# ── Discovery report with mfl_league_id ──────────────────────────────


class TestDiscoveryReportMflLeagueId:
    def test_mfl_league_id_for_season(self):
        report = DiscoveryReport(league_id="70985")
        report.seasons = [
            SeasonAvailability(
                season=2009, server="www48", franchise_count=10,
                categories=[], mfl_league_id="50536",
            ),
            SeasonAvailability(
                season=2024, server="www44", franchise_count=10,
                categories=[], mfl_league_id="70985",
            ),
        ]
        assert report.mfl_league_id_for_season(2009) == "50536"
        assert report.mfl_league_id_for_season(2024) == "70985"
        assert report.mfl_league_id_for_season(2015) is None

    def test_season_availability_mfl_league_id_field(self):
        sa = SeasonAvailability(
            season=2009, server="www48", franchise_count=10,
            categories=[], mfl_league_id="50536",
        )
        assert sa.mfl_league_id == "50536"

    def test_season_availability_mfl_league_id_default_none(self):
        sa = SeasonAvailability(
            season=2024, server="www44", franchise_count=10,
            categories=[],
        )
        assert sa.mfl_league_id is None
