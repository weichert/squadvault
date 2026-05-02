"""Tests for squadvault.core.queries.narrative_filters.

Covers: filter_events_for_narrative, allow/exclude logic, default types.
"""
from __future__ import annotations

from squadvault.core.queries.narrative_filters import (
    DEFAULT_EXCLUDE_EVENT_TYPES,
    DEFAULT_NARRATIVE_EVENT_TYPES,
    filter_events_for_narrative,
)


def _evt(event_type: str) -> dict:
    return {"event_type": event_type}


class TestFilterEventsForNarrative:
    def test_allows_narrative_types(self):
        """Narrative event types pass through by default."""
        events = [_evt("DRAFT_PICK"), _evt("TRANSACTION_TRADE"), _evt("WAIVER_BID_AWARDED")]
        result = filter_events_for_narrative(events)
        assert len(result) == 3

    def test_excludes_system_types(self):
        """System/maintenance events are excluded by default."""
        events = [
            _evt("TRANSACTION_LOCK_ALL_PLAYERS"),
            _evt("TRANSACTION_AUTO_PROCESS_WAIVERS"),
            _evt("DRAFT_PICK"),
        ]
        result = filter_events_for_narrative(events)
        assert len(result) == 1
        assert result[0]["event_type"] == "DRAFT_PICK"

    def test_unknown_types_excluded(self):
        """Types not in the allow set are excluded."""
        events = [_evt("SOME_UNKNOWN_TYPE")]
        result = filter_events_for_narrative(events)
        assert result == []

    def test_custom_allow_list(self):
        """Custom allow set overrides defaults."""
        events = [_evt("CUSTOM_TYPE"), _evt("DRAFT_PICK")]
        result = filter_events_for_narrative(events, allow_event_types={"CUSTOM_TYPE"})
        assert len(result) == 1
        assert result[0]["event_type"] == "CUSTOM_TYPE"

    def test_custom_exclude_list(self):
        """Custom exclude set overrides defaults."""
        events = [_evt("DRAFT_PICK"), _evt("TRANSACTION_TRADE")]
        result = filter_events_for_narrative(events, exclude_event_types={"DRAFT_PICK"})
        assert len(result) == 1
        assert result[0]["event_type"] == "TRANSACTION_TRADE"

    def test_exclude_takes_priority(self):
        """Even if a type is in allow, exclude removes it."""
        events = [_evt("DRAFT_PICK")]
        result = filter_events_for_narrative(
            events,
            allow_event_types={"DRAFT_PICK"},
            exclude_event_types={"DRAFT_PICK"},
        )
        assert result == []

    def test_empty_input(self):
        assert filter_events_for_narrative([]) == []

    def test_default_sets_nonempty(self):
        """Default allow and exclude sets are non-empty."""
        assert len(DEFAULT_NARRATIVE_EVENT_TYPES) > 0
        assert len(DEFAULT_EXCLUDE_EVENT_TYPES) > 0

    def test_no_overlap_in_defaults(self):
        """Default allow and exclude sets don't overlap."""
        assert DEFAULT_NARRATIVE_EVENT_TYPES & DEFAULT_EXCLUDE_EVENT_TYPES == set()
