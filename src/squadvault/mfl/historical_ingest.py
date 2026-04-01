"""MFL multi-season historical ingestion.

Per the Platform Adapter Contract Card (v1.0):
- Adapters produce event envelopes only — never write to canonical_events or lifecycle tables
- Re-ingestion with identical platform data must produce zero new events
- Missing data must remain missing — adapters must never infer, estimate, or fabricate events
- All adapter behavior is operator-initiated

Recommended ingestion sequence per season:
    FRANCHISE_INFO → MATCHUP_RESULTS → TRANSACTIONS + FAAB_BIDS + DRAFT_PICKS → PLAYER_INFO → PLAYER_SCORES
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from squadvault.core.storage.session import DatabaseSession
from squadvault.core.storage.sqlite_store import SQLiteStore
from squadvault.ingest.auction_draft import (
    derive_auction_event_envelopes_from_transactions,
)
from squadvault.ingest.franchises._run_franchises_ingest import (
    _extract_franchises,
    _normalize_row,
)
from squadvault.ingest.franchises._run_franchises_ingest import (
    _upsert_rows as _upsert_franchise_rows,
)
from squadvault.ingest.matchup_results import derive_matchup_result_envelopes
from squadvault.ingest.player_scores import derive_player_score_envelopes
from squadvault.ingest.players._run_players_ingest import (
    _parse_players_json,
    _upsert_players,
)
from squadvault.ingest.transactions import derive_transaction_event_envelopes
from squadvault.ingest.waiver_bids import (
    derive_waiver_bid_event_envelopes_from_transactions,
)
from squadvault.mfl.client import MflClient
from squadvault.mfl.discovery import DiscoveryReport

logger = logging.getLogger(__name__)


# ── Data structures ──────────────────────────────────────────────────


@dataclass
class CategoryResult:
    """Result of ingesting one data category for one season."""

    category: str
    inserted: int = 0
    skipped: int = 0
    error: str | None = None


@dataclass
class SeasonIngestResult:
    """Result of ingesting all categories for one season."""

    league_id: str
    season: int
    server: str
    categories: list[CategoryResult] = field(default_factory=list)

    @property
    def total_inserted(self) -> int:
        return sum(c.inserted for c in self.categories)

    @property
    def total_skipped(self) -> int:
        return sum(c.skipped for c in self.categories)


# ── Category ingest functions ────────────────────────────────────────


def _ingest_franchise_info(
    client: MflClient,
    db_path: str,
    league_id: str,
    season: int,
    league_json: dict[str, Any] | None = None,
) -> CategoryResult:
    """Ingest franchise directory for a season.

    If league_json is provided (from discovery cache), uses it directly
    instead of making another API call.
    """
    result = CategoryResult(category="FRANCHISE_INFO")

    try:
        if league_json is None:
            league_json, _ = client.get_league_info(season)

        franchises = _extract_franchises(league_json)
        rows = [r for f in franchises if (r := _normalize_row(f)) is not None]

        if not rows:
            result.error = "No franchises found"
            return result

        with DatabaseSession(db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            with conn:
                written = _upsert_franchise_rows(conn, league_id, season, rows)
            result.inserted = written

    except Exception as e:
        result.error = str(e)
        logger.error(
            "FRANCHISE_INFO ingest failed for season %d: %s", season, e
        )

    return result


def _ingest_transactions_and_bids(
    client: MflClient,
    store: SQLiteStore,
    league_id: str,
    season: int,
) -> tuple[CategoryResult, CategoryResult, CategoryResult]:
    """Ingest TRANSACTIONS, FAAB_BIDS, and DRAFT_PICKS from one API call.

    All three categories are derived from the MFL transactions export.
    """
    txn_result = CategoryResult(category="TRANSACTIONS")
    faab_result = CategoryResult(category="FAAB_BIDS")
    draft_result = CategoryResult(category="DRAFT_PICKS")

    try:
        raw_json, source_url = client.get_transactions(year=season)

        transactions = raw_json.get("transactions", {}).get("transaction", [])
        if isinstance(transactions, dict):
            transactions = [transactions]

        if not transactions:
            # No transactions for this season — not an error, just empty
            return txn_result, faab_result, draft_result

        # TRANSACTIONS
        txn_events = derive_transaction_event_envelopes(
            year=season,
            league_id=league_id,
            transactions=transactions,
            source_url=source_url,
        )
        if txn_events:
            ins, skip = store.append_events(txn_events)
            txn_result.inserted = ins
            txn_result.skipped = skip

        # FAAB_BIDS
        faab_events = derive_waiver_bid_event_envelopes_from_transactions(
            year=season,
            league_id=league_id,
            transactions=transactions,
            source_url=source_url,
        )
        if faab_events:
            ins, skip = store.append_events(faab_events)
            faab_result.inserted = ins
            faab_result.skipped = skip

        # DRAFT_PICKS
        draft_events = derive_auction_event_envelopes_from_transactions(
            year=season,
            league_id=league_id,
            transactions=transactions,
            source_url=source_url,
        )
        if draft_events:
            ins, skip = store.append_events(draft_events)
            draft_result.inserted = ins
            draft_result.skipped = skip

    except Exception as e:
        error_msg = str(e)
        txn_result.error = error_msg
        faab_result.error = error_msg
        draft_result.error = error_msg
        logger.error(
            "Transactions ingest failed for season %d: %s", season, e
        )

    return txn_result, faab_result, draft_result


def _ingest_matchup_results(
    client: MflClient,
    store: SQLiteStore,
    league_id: str,
    season: int,
    max_weeks: int = 18,
    request_delay_s: float = 3.0,
) -> CategoryResult:
    """Ingest weekly matchup results for a season.

    Probes weeks 1 through max_weeks. Stops early on consecutive empty
    weeks. Skips weeks where all scores are 0.00 (unplayed).

    Adapts delay when 429 rate limits are encountered.
    """
    result = CategoryResult(category="MATCHUP_RESULTS")
    consecutive_empty = 0
    current_delay = request_delay_s

    try:
        for week in range(1, max_weeks + 1):
            # Always delay between requests (including after failures)
            if week > 1:
                time.sleep(current_delay)

            try:
                raw_json, source_url = client.get_weekly_results(
                    year=season, week=week
                )
            except Exception as e:
                err_str = str(e)
                # Detect 429 from the exception message and increase delay
                if "429" in err_str:
                    current_delay = min(current_delay * 2, 30.0)
                    print(
                        f"      week {week:2d}: 429 rate limited"
                        f" (delay now {current_delay:.1f}s)"
                    )
                    # Extra cooldown after 429 exhaustion
                    time.sleep(current_delay)
                else:
                    logger.debug("Week %d fetch failed: %s", week, e)

                consecutive_empty += 1
                if consecutive_empty >= 3:
                    logger.info(
                        "Season %d: 3 consecutive failures/empty at week %d, stopping",
                        season,
                        week,
                    )
                    break
                continue

            events = derive_matchup_result_envelopes(
                year=season,
                week=week,
                league_id=league_id,
                weekly_results_json=raw_json,
                source_url=source_url,
                occurred_at=None,  # Historical — no lock timestamps
            )

            if not events:
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    logger.info(
                        "Season %d: 3 consecutive empty weeks at week %d, stopping",
                        season,
                        week,
                    )
                    break
                continue

            # Check if all scores are 0.00 — likely means week hasn't been played
            all_zero = all(
                e["payload"].get("winner_score") == "0.00"
                and e["payload"].get("loser_score") == "0.00"
                for e in events
            )
            if all_zero:
                logger.info(
                    "Season %d week %d: all scores 0.00, skipping (unplayed)",
                    season,
                    week,
                )
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    break
                continue

            # Valid matchup data — reset counters
            consecutive_empty = 0
            # Gradually restore delay on success (min of base delay)
            current_delay = max(request_delay_s, current_delay * 0.8)

            ins, skip = store.append_events(events)
            result.inserted += ins
            result.skipped += skip

            label = "new" if ins > 0 else "exists"
            print(f"      week {week:2d}: {len(events)} matchups ({label})")

    except Exception as e:
        result.error = str(e)
        logger.error(
            "MATCHUP_RESULTS ingest failed for season %d: %s", season, e
        )

    return result


def _ingest_player_info(
    client: MflClient,
    db_path: str,
    league_id: str,
    season: int,
) -> CategoryResult:
    """Ingest player directory for a season."""
    result = CategoryResult(category="PLAYER_INFO")

    try:
        raw_json, _ = client.get_players(year=season)

        # Re-encode to bytes so the existing parser can handle it
        payload_bytes = json.dumps(raw_json).encode("utf-8")
        players = _parse_players_json(payload_bytes)

        if not players:
            result.error = "No players found"
            return result

        with DatabaseSession(db_path) as conn:
            _, total = _upsert_players(conn, league_id, season, players)
            result.inserted = total

    except Exception as e:
        result.error = str(e)
        logger.error(
            "PLAYER_INFO ingest failed for season %d: %s", season, e
        )

    return result


def _ingest_player_scores(
    client: MflClient,
    store: SQLiteStore,
    league_id: str,
    season: int,
    max_weeks: int = 18,
    request_delay_s: float = 3.0,
) -> CategoryResult:
    """Ingest per-player weekly scores for a season.

    Uses the weeklyResults endpoint (same as matchup results) which
    includes per-player scoring and lineup status within each franchise.
    Follows the same probing and rate-limit adaptation pattern as
    _ingest_matchup_results.
    """
    result = CategoryResult(category="PLAYER_SCORES")
    consecutive_empty = 0
    current_delay = request_delay_s

    try:
        for week in range(1, max_weeks + 1):
            if week > 1:
                time.sleep(current_delay)

            try:
                raw_json, source_url = client.get_weekly_results(
                    year=season, week=week
                )
            except Exception as e:
                err_str = str(e)
                if "429" in err_str:
                    current_delay = min(current_delay * 2, 30.0)
                    print(
                        f"      week {week:2d}: 429 rate limited"
                        f" (delay now {current_delay:.1f}s)"
                    )
                    time.sleep(current_delay)
                else:
                    logger.debug("Week %d weeklyResults fetch failed: %s", week, e)

                consecutive_empty += 1
                if consecutive_empty >= 3:
                    logger.info(
                        "Season %d: 3 consecutive failures at week %d (playerScores), stopping",
                        season, week,
                    )
                    break
                continue

            events = derive_player_score_envelopes(
                year=season,
                week=week,
                league_id=league_id,
                weekly_results_json=raw_json,
                source_url=source_url,
                occurred_at=None,
            )

            if not events:
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    logger.info(
                        "Season %d: 3 consecutive empty weeks at week %d (playerScores), stopping",
                        season, week,
                    )
                    break
                continue

            # Check if all scores are 0.0 — likely means week hasn't been played
            all_zero = all(
                e["payload"].get("score") == 0.0
                for e in events
            )
            if all_zero:
                logger.info(
                    "Season %d week %d: all player scores 0.0, skipping (unplayed)",
                    season, week,
                )
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    break
                continue

            # Valid data — reset counters
            consecutive_empty = 0
            current_delay = max(request_delay_s, current_delay * 0.8)

            ins, skip = store.append_events(events)
            result.inserted += ins
            result.skipped += skip

            label = "new" if ins > 0 else "exists"
            print(f"      week {week:2d}: {len(events)} player scores ({label})")

    except Exception as e:
        result.error = str(e)
        logger.error(
            "PLAYER_SCORES ingest failed for season %d: %s", season, e
        )

    return result


def _ingest_nfl_bye_weeks(
    client: MflClient,
    db_path: str,
    league_id: str,
    season: int,
) -> CategoryResult:
    """Ingest NFL bye week data for a season.

    Uses the nflByeWeeks endpoint on api.myfantasyleague.com (not the
    league shard). One API call per season. Reference metadata only.
    """
    result = CategoryResult(category="NFL_BYE_WEEKS")

    try:
        from squadvault.ingest.nfl_bye_weeks import ingest_nfl_bye_weeks_from_mfl
        raw_json, _ = client.get_nfl_bye_weeks(year=season)
        count = ingest_nfl_bye_weeks_from_mfl(
            db_path=db_path, league_id=league_id, season=season,
            raw_json=raw_json,
        )
        result.inserted = count
    except Exception as e:
        result.error = str(e)
        logger.error(
            "NFL_BYE_WEEKS ingest failed for season %d: %s", season, e
        )

    return result


def _ingest_scoring_rules(
    client: MflClient,
    db_path: str,
    league_id: str,
    season: int,
) -> CategoryResult:
    """Ingest league scoring rules for a season.

    Uses the league-specific rules endpoint. One API call per season.
    """
    result = CategoryResult(category="SCORING_RULES")

    try:
        from squadvault.ingest.scoring_rules import ingest_scoring_rules_from_mfl
        raw_json, _ = client.get_rules(year=season)
        count = ingest_scoring_rules_from_mfl(
            db_path=db_path, league_id=league_id, season=season,
            raw_json=raw_json,
        )
        result.inserted = count
    except Exception as e:
        result.error = str(e)
        logger.error(
            "SCORING_RULES ingest failed for season %d: %s", season, e
        )

    return result


# ── Public API ───────────────────────────────────────────────────────


_ALL_CATEGORIES = [
    "FRANCHISE_INFO",
    "MATCHUP_RESULTS",
    "TRANSACTIONS",
    "FAAB_BIDS",
    "DRAFT_PICKS",
    "PLAYER_INFO",
    "PLAYER_SCORES",
]


def ingest_mfl_season(
    league_id: str,
    season: int,
    server: str,
    db_path: str,
    *,
    mfl_league_id: str | None = None,
    categories: list[str] | None = None,
    max_weeks: int = 18,
    request_delay_s: float = 2.5,
    username: str | None = None,
    password: str | None = None,
    league_json: dict[str, Any] | None = None,
) -> SeasonIngestResult:
    """
    Ingest one MFL season across selected data categories.

    Follows the recommended ingestion sequence:
        FRANCHISE_INFO -> MATCHUP_RESULTS -> TRANSACTIONS + FAAB_BIDS + DRAFT_PICKS -> PLAYER_INFO -> PLAYER_SCORES

    Args:
        league_id: SquadVault league identifier (used for storage)
        season: Season year to ingest
        server: Resolved MFL server hostname for this season
        db_path: Path to the SQLite database
        mfl_league_id: MFL league ID for API calls (defaults to league_id if not set).
            Historical seasons may have different MFL IDs than the current season.
        categories: Which categories to ingest (default: all)
        max_weeks: Maximum weeks to probe for matchup results
        request_delay_s: Delay between API calls
        username: MFL username (optional, for private leagues)
        password: MFL password (optional, for private leagues)
        league_json: Cached TYPE=league response from discovery (optional)
    """
    # MFL league ID for API calls may differ from SquadVault league ID
    api_league_id = mfl_league_id or league_id

    if categories is None:
        categories = list(_ALL_CATEGORIES)

    result = SeasonIngestResult(
        league_id=league_id, season=season, server=server
    )

    client = MflClient(
        server=server,
        league_id=api_league_id,
        username=username,
        password=password,
    )

    store = SQLiteStore(Path(db_path))

    # 1. FRANCHISE_INFO (must be first — required for name resolution)
    if "FRANCHISE_INFO" in categories:
        cat_result = _ingest_franchise_info(
            client, db_path, league_id, season, league_json=league_json
        )
        result.categories.append(cat_result)
        _log_category(season, cat_result)
        time.sleep(request_delay_s)

    # 2. MATCHUP_RESULTS (the backbone — ~80% of narrative richness)
    if "MATCHUP_RESULTS" in categories:
        cat_result = _ingest_matchup_results(
            client,
            store,
            league_id,
            season,
            max_weeks=max_weeks,
            request_delay_s=request_delay_s,
        )
        result.categories.append(cat_result)
        _log_category(season, cat_result)
        time.sleep(request_delay_s)

    # 3. TRANSACTIONS + FAAB_BIDS + DRAFT_PICKS (single API call)
    txn_cats = {"TRANSACTIONS", "FAAB_BIDS", "DRAFT_PICKS"}
    if txn_cats & set(categories):
        txn_r, faab_r, draft_r = _ingest_transactions_and_bids(
            client, store, league_id, season
        )
        if "TRANSACTIONS" in categories:
            result.categories.append(txn_r)
            _log_category(season, txn_r)
        if "FAAB_BIDS" in categories:
            result.categories.append(faab_r)
            _log_category(season, faab_r)
        if "DRAFT_PICKS" in categories:
            result.categories.append(draft_r)
            _log_category(season, draft_r)
        time.sleep(request_delay_s)

    # 4. PLAYER_INFO (last — supports name resolution for transactions/draft)
    if "PLAYER_INFO" in categories:
        cat_result = _ingest_player_info(
            client, db_path, league_id, season
        )
        result.categories.append(cat_result)
        _log_category(season, cat_result)

    # 5. PLAYER_SCORES (uses weeklyResults endpoint — same as matchup results
    #    but extracts per-player scoring and lineup status)
    if "PLAYER_SCORES" in categories:
        cat_result = _ingest_player_scores(
            client,
            store,
            league_id,
            season,
            max_weeks=max_weeks,
            request_delay_s=request_delay_s,
        )
        result.categories.append(cat_result)
        _log_category(season, cat_result)

    # 6. NFL_BYE_WEEKS (NFL-wide data from api.myfantasyleague.com)
    if "NFL_BYE_WEEKS" in categories:
        cat_result = _ingest_nfl_bye_weeks(
            client, db_path, league_id, season,
        )
        result.categories.append(cat_result)
        _log_category(season, cat_result)

    # 7. SCORING_RULES (league configuration metadata)
    if "SCORING_RULES" in categories:
        cat_result = _ingest_scoring_rules(
            client, db_path, league_id, season,
        )
        result.categories.append(cat_result)
        _log_category(season, cat_result)

    return result


def _log_category(season: int, cat: CategoryResult) -> None:
    """Print a single category result line."""
    status = f"inserted={cat.inserted}, skipped={cat.skipped}"
    if cat.error:
        status += f"  ERROR: {cat.error}"
    print(f"    {cat.category:<20s} {status}")


def ingest_mfl_seasons(
    league_id: str,
    discovery: DiscoveryReport,
    db_path: str,
    *,
    seasons: list[int] | None = None,
    categories: list[str] | None = None,
    max_weeks: int = 18,
    request_delay_s: float = 1.5,
    username: str | None = None,
    password: str | None = None,
) -> list[SeasonIngestResult]:
    """
    Ingest multiple MFL seasons using a discovery report.

    Processes seasons in chronological order.
    Uses discovered servers and MFL league IDs per season.
    Reuses cached franchise data from discovery when available.

    For leagues with historical league ID changes (common on MFL),
    the discovery report provides the correct MFL league ID per season.
    All events are stored under the canonical SquadVault league_id.

    Args:
        league_id: SquadVault league identifier (used for storage)
        discovery: Discovery report with resolved servers per season
        db_path: Path to the SQLite database
        seasons: Which seasons to ingest (default: all discovered)
        categories: Which categories to ingest per season (default: all)
        max_weeks: Maximum weeks to probe for matchup results
        request_delay_s: Delay between API calls
        username: MFL username (optional)
        password: MFL password (optional)
    """
    if seasons is None:
        seasons = discovery.available_seasons()

    results: list[SeasonIngestResult] = []

    for season in sorted(seasons):
        server = discovery.server_for_season(season)
        if server is None:
            logger.warning("No server found for season %d, skipping", season)
            continue

        # Get MFL league ID for this season (may differ from SquadVault league_id)
        mfl_league_id = discovery.mfl_league_id_for_season(season)

        # Find cached franchise data from discovery
        disc_season = next(
            (s for s in discovery.seasons if s.season == season), None
        )
        league_json = None
        if disc_season and disc_season.raw_franchises:
            league_json = {
                "league": {
                    "franchises": {"franchise": disc_season.raw_franchises}
                }
            }

        mfl_id_note = ""
        if mfl_league_id and mfl_league_id != league_id:
            mfl_id_note = f"  [MFL ID: {mfl_league_id}]"
        print(f"\n{'='*60}")
        print(f"  Season {season} -- server: {server}{mfl_id_note}")
        print(f"{'='*60}")

        season_result = ingest_mfl_season(
            league_id=league_id,
            season=season,
            server=server,
            db_path=db_path,
            mfl_league_id=mfl_league_id,
            categories=categories,
            max_weeks=max_weeks,
            request_delay_s=request_delay_s,
            username=username,
            password=password,
            league_json=league_json,
        )

        results.append(season_result)

        print(
            f"  TOTAL: inserted={season_result.total_inserted},"
            f" skipped={season_result.total_skipped}"
        )

        # Inter-season cooldown (longer than inter-request to let rate limits reset)
        inter_season_wait = max(request_delay_s * 3, 5.0)
        print(f"  (cooling down {inter_season_wait:.0f}s before next season)")
        time.sleep(inter_season_wait)

    # Final summary
    total_inserted = sum(r.total_inserted for r in results)
    total_skipped = sum(r.total_skipped for r in results)
    print(f"\n{'='*60}")
    print(f"  GRAND TOTAL across {len(results)} seasons")
    print(f"  inserted={total_inserted}, skipped={total_skipped}")
    print(f"{'='*60}")

    return results
