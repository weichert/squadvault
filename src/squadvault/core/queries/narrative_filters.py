from __future__ import annotations

from typing import Any, Dict, Iterable, List, Set


# These are "system/maintenance" events that should not appear in user-facing narratives by default.
DEFAULT_EXCLUDE_EVENT_TYPES: Set[str] = {
    "TRANSACTION_LOCK_ALL_PLAYERS",
    "TRANSACTION_AUTO_PROCESS_WAIVERS",
    "TRANSACTION_BBID_AUTO_PROCESS_WAIVERS",
}


# These are the "story-relevant" event types for v1 narrative generation.
DEFAULT_NARRATIVE_EVENT_TYPES: Set[str] = {
    "DRAFT_PICK",
    "WAIVER_BID_AWARDED",
    "WAIVER_BID_REQUEST",   # included for future-proofing even if your league currently yields 0
    "TRANSACTION_TRADE",
    "TRANSACTION_FREE_AGENT",
    "TRANSACTION_WAIVER",   # if your league uses this for standard waivers
}


def filter_events_for_narrative(
    events: Iterable[Dict[str, Any]],
    *,
    allow_event_types: Set[str] | None = None,
    exclude_event_types: Set[str] | None = None,
) -> List[Dict[str, Any]]:
    """
    Return only events considered narrative-relevant.

    - If allow_event_types is provided, it's a whitelist.
    - exclude_event_types always removes those types.
    """
    allow = allow_event_types if allow_event_types is not None else DEFAULT_NARRATIVE_EVENT_TYPES
    exclude = exclude_event_types if exclude_event_types is not None else DEFAULT_EXCLUDE_EVENT_TYPES

    out: List[Dict[str, Any]] = []
    for e in events:
        et = e.get("event_type", "")
        if et in exclude:
            continue
        if et not in allow:
            continue
        out.append(e)
    return out


