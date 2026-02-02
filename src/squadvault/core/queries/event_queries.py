from __future__ import annotations

from typing import Any, Dict, List, Optional

from squadvault.core.storage.sqlite_store import SQLiteStore


def fetch_all_events(store: SQLiteStore, *, league_id: str, season: int, limit: int = 5000) -> List[Dict[str, Any]]:
    return store.fetch_events(league_id=league_id, season=season, limit=limit)


def fetch_by_event_type(
    store: SQLiteStore,
    *,
    league_id: str,
    season: int,
    event_type: str,
    limit: int = 5000,
) -> List[Dict[str, Any]]:
    events = store.fetch_events(league_id=league_id, season=season, limit=limit)
    return [e for e in events if e["event_type"] == event_type]


def fetch_by_event_type_prefix(
    store: SQLiteStore,
    *,
    league_id: str,
    season: int,
    prefix: str,
    limit: int = 5000,
) -> List[Dict[str, Any]]:
    events = store.fetch_events(league_id=league_id, season=season, limit=limit)
    return [e for e in events if e["event_type"].startswith(prefix)]


def draft_picks(store: SQLiteStore, *, league_id: str, season: int) -> List[Dict[str, Any]]:
    return fetch_by_event_type(store, league_id=league_id, season=season, event_type="DRAFT_PICK")


def waiver_awards(store: SQLiteStore, *, league_id: str, season: int) -> List[Dict[str, Any]]:
    return fetch_by_event_type(store, league_id=league_id, season=season, event_type="WAIVER_BID_AWARDED")


def waiver_requests(store: SQLiteStore, *, league_id: str, season: int) -> List[Dict[str, Any]]:
    return fetch_by_event_type(store, league_id=league_id, season=season, event_type="WAIVER_BID_REQUEST")


def trades(store: SQLiteStore, *, league_id: str, season: int) -> List[Dict[str, Any]]:
    return fetch_by_event_type(store, league_id=league_id, season=season, event_type="TRANSACTION_TRADE")


def free_agent_transactions(store: SQLiteStore, *, league_id: str, season: int) -> List[Dict[str, Any]]:
    # MFL calls these FREE_AGENT in your observed data
    return fetch_by_event_type(store, league_id=league_id, season=season, event_type="TRANSACTION_FREE_AGENT")
