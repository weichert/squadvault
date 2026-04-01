"""Franchise-scoped event query helpers."""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

from squadvault.core.queries.event_queries import fetch_all_events
from squadvault.core.queries.narrative_filters import filter_events_for_narrative
from squadvault.core.storage.sqlite_store import SQLiteStore


def _franchise_ids_from_payload(event: dict[str, Any]) -> set[str]:
    """
    Extract all franchise IDs involved in an event.

    - Uses payload["franchise_id"] when present
    - Also parses raw_mfl_json for keys like franchise2, franchise3 (trades)
    """
    payload = event.get("payload") or {}
    out: set[str] = set()

    fid = payload.get("franchise_id")
    if isinstance(fid, str) and fid:
        out.add(fid)
    elif isinstance(fid, (list, tuple, set)):
        out.update([x for x in fid if isinstance(x, str) and x])

    raw = payload.get("raw_mfl_json")
    if isinstance(raw, str) and raw:
        try:
            obj = json.loads(raw)
            for k, v in obj.items():
                if isinstance(k, str) and k.startswith("franchise") and isinstance(v, str) and v:
                    out.add(v)
        except (ValueError, TypeError):
            pass

    return out


def events_for_franchise(
    store: SQLiteStore,
    *,
    league_id: str,
    season: int,
    franchise_id: str,
    narrative_only: bool = True,
    limit: int = 10000,
) -> list[dict[str, Any]]:
    """Fetch all events involving a specific franchise."""
    events = fetch_all_events(store, league_id=league_id, season=season, limit=limit)

    if narrative_only:
        events = filter_events_for_narrative(events)

    return [e for e in events if franchise_id in _franchise_ids_from_payload(e)]


def _filter_type(events: Iterable[dict[str, Any]], event_type: str) -> list[dict[str, Any]]:
    """Filter event list to only those matching event_type prefix."""
    return [e for e in events if e.get("event_type") == event_type]


def draft_picks_for_franchise(
    store: SQLiteStore,
    *,
    league_id: str,
    season: int,
    franchise_id: str,
) -> list[dict[str, Any]]:
    """Fetch draft pick events for a specific franchise."""
    return _filter_type(
        events_for_franchise(store, league_id=league_id, season=season, franchise_id=franchise_id),
        "DRAFT_PICK",
    )


def waiver_awards_for_franchise(
    store: SQLiteStore,
    *,
    league_id: str,
    season: int,
    franchise_id: str,
) -> list[dict[str, Any]]:
    """Fetch waiver award events for a specific franchise."""
    return _filter_type(
        events_for_franchise(store, league_id=league_id, season=season, franchise_id=franchise_id),
        "WAIVER_BID_AWARDED",
    )


def free_agent_moves_for_franchise(
    store: SQLiteStore,
    *,
    league_id: str,
    season: int,
    franchise_id: str,
) -> list[dict[str, Any]]:
    """Fetch free agent events for a specific franchise."""
    return _filter_type(
        events_for_franchise(store, league_id=league_id, season=season, franchise_id=franchise_id),
        "TRANSACTION_FREE_AGENT",
    )


def trades_for_franchise(
    store: SQLiteStore,
    *,
    league_id: str,
    season: int,
    franchise_id: str,
) -> list[dict[str, Any]]:
    """Fetch trade events involving a specific franchise."""
    return _filter_type(
        events_for_franchise(store, league_id=league_id, season=season, franchise_id=franchise_id),
        "TRANSACTION_TRADE",
    )
