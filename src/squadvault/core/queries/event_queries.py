"""Memory event query helpers for common event type lookups.

# SV_DEFECT2_CANONICAL_DEFAULT
# These helpers default to use_canonical=True, reading from the deduplicated
# canonical view (v_canonical_best_events). Pass use_canonical=False explicitly
# to read from the raw memory_events ledger (audit/diagnostic only).
"""

from __future__ import annotations

from typing import Any

from squadvault.core.storage.sqlite_store import SQLiteStore


def fetch_all_events(
    store: SQLiteStore,
    *,
    league_id: str,
    season: int,
    limit: int = 5000,
    use_canonical: bool = True,
) -> list[dict[str, Any]]:
    """Fetch events for a league/season.

    use_canonical=True (default): reads from canonical view (deduplicated).
    use_canonical=False: reads from raw memory_events ledger.
    """
    return store.fetch_events(league_id=league_id, season=season, limit=limit, use_canonical=use_canonical)


def fetch_by_event_type(
    store: SQLiteStore,
    *,
    league_id: str,
    season: int,
    event_type: str,
    limit: int = 5000,
    use_canonical: bool = True,
) -> list[dict[str, Any]]:
    """Fetch events matching an exact event_type.

    use_canonical=True (default): reads from canonical view (deduplicated).
    use_canonical=False: reads from raw memory_events ledger.
    """
    events = store.fetch_events(league_id=league_id, season=season, limit=limit, use_canonical=use_canonical)
    return [e for e in events if e["event_type"] == event_type]


def fetch_by_event_type_prefix(
    store: SQLiteStore,
    *,
    league_id: str,
    season: int,
    prefix: str,
    limit: int = 5000,
    use_canonical: bool = True,
) -> list[dict[str, Any]]:
    """Fetch events whose event_type starts with prefix.

    use_canonical=True (default): reads from canonical view (deduplicated).
    use_canonical=False: reads from raw memory_events ledger.
    """
    events = store.fetch_events(league_id=league_id, season=season, limit=limit, use_canonical=use_canonical)
    return [e for e in events if e["event_type"].startswith(prefix)]


def draft_picks(store: SQLiteStore, *, league_id: str, season: int, use_canonical: bool = True) -> list[dict[str, Any]]:
    """Fetch DRAFT_PICK events for a league/season."""
    return fetch_by_event_type(store, league_id=league_id, season=season, event_type="DRAFT_PICK", use_canonical=use_canonical)


def waiver_awards(store: SQLiteStore, *, league_id: str, season: int, use_canonical: bool = True) -> list[dict[str, Any]]:
    """Fetch WAIVER_BID_AWARDED events for a league/season."""
    return fetch_by_event_type(store, league_id=league_id, season=season, event_type="WAIVER_BID_AWARDED", use_canonical=use_canonical)


def waiver_requests(store: SQLiteStore, *, league_id: str, season: int, use_canonical: bool = True) -> list[dict[str, Any]]:
    """Fetch waiver request events for a league/season."""
    return fetch_by_event_type(store, league_id=league_id, season=season, event_type="WAIVER_BID_REQUEST", use_canonical=use_canonical)


def trades(store: SQLiteStore, *, league_id: str, season: int, use_canonical: bool = True) -> list[dict[str, Any]]:
    """Fetch trade events for a league/season."""
    return fetch_by_event_type(store, league_id=league_id, season=season, event_type="TRANSACTION_TRADE", use_canonical=use_canonical)


def free_agent_transactions(store: SQLiteStore, *, league_id: str, season: int, use_canonical: bool = True) -> list[dict[str, Any]]:
    # MFL calls these FREE_AGENT in your observed data
    """Fetch free agent transaction events for a league/season."""
    return fetch_by_event_type(store, league_id=league_id, season=season, event_type="TRANSACTION_FREE_AGENT", use_canonical=use_canonical)
