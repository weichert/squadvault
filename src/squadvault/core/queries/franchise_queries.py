"""Franchise-scoped event query helpers.

Reads only canonical payload fields — never parses adapter-specific raw
payloads. Adapter-specific parsing (e.g. pulling franchise counterparties
out of an MFL raw transaction dict) belongs in ``ingest/`` and must be
promoted into the canonical payload by the ingest layer before query
helpers can consume it.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from squadvault.core.queries.event_queries import fetch_all_events
from squadvault.core.queries.narrative_filters import filter_events_for_narrative
from squadvault.core.storage.sqlite_store import SQLiteStore


def _franchise_ids_from_payload(event: dict[str, Any]) -> set[str]:
    """
    Extract every franchise ID involved in an event from canonical payload fields.

    Reads, in precedence order:

    - ``franchise_ids_involved`` (list[str]): the structured list
      written by ``ingest/transactions.py`` for events canonicalized
      after that field was promoted. For trades this carries the
      initiator plus each counterparty; for non-trade transactions it
      carries the initiator only.
    - ``franchise_id`` (str | list[str]): the scalar initiator. Used
      alongside the list above (merged into the set) so events that
      predate the new field still resolve to at least their initiator.

    Known limitation:
        Trade events ingested before ``franchise_ids_involved`` was
        promoted retain their counterparty IDs only inside the raw
        adapter payload. This helper deliberately does not parse
        that payload — the layer boundary (core/ reads canonical;
        ingest/ parses adapter payloads) is worth preserving, and a
        backfill pass over historical memory events is a separate,
        out-of-scope concern. For those historical trades, only the
        scalar initiator surfaces here; counterparty reads will be
        under-represented until a backfill is run or the affected
        rows are re-ingested.
    """
    payload = event.get("payload") or {}
    out: set[str] = set()

    # Preferred: the canonical list of all franchises involved.
    involved = payload.get("franchise_ids_involved")
    if isinstance(involved, (list, tuple)):
        out.update(x for x in involved if isinstance(x, str) and x)

    # Fallback / merge: the scalar initiator. Always unioned in — this
    # covers both the backward-compat case (no involved list at all)
    # and the defensive case (initiator listed via scalar but somehow
    # missing from the list).
    fid = payload.get("franchise_id")
    if isinstance(fid, str) and fid:
        out.add(fid)
    elif isinstance(fid, (list, tuple, set)):
        out.update(x for x in fid if isinstance(x, str) and x)

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
