"""
Writing Room Signal Extractors v1.0 (Build Phase)

Purpose:
- Convert existing truth-layer data into Tier 1 dict-signals for Writing Room intake.
- This is an adapter boundary: Truth -> (opaque) Signals -> Writing Room intake.

Rules:
- Do NOT invent new data sources.
- Do NOT infer narrative fields.
- Keep output minimal: only what DictSignalAdapter needs.

Current extractor:
- canonical_events -> dict signals (one signal per canonical_event)

Later:
- richer extraction and redundancy keys (still deterministic)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import sqlite3


@dataclass(frozen=True, slots=True)
class CanonicalEventsSignalExtractorV1:
    """
    Extract dict-signals from canonical_events for a given window.

    Assumptions (current):
    - canonical_events table exists
    - has at least: id (or canonical_event_id), league_id, season, occurred_at, event_type
    """

    def extract_signals(
        self,
        *,
        db_path: str,
        league_id: str,
        season: int,
        window_start: str,
        window_end: str,
    ) -> List[dict]:
        con = sqlite3.connect(db_path)
        try:
            con.row_factory = sqlite3.Row
            cur = con.cursor()

            # NOTE: occurred_at is ISO-8601 UTC text in your system.
            # We rely on lexicographic ordering equivalence for ISO timestamps.
            rows = cur.execute(
                """
                SELECT id, occurred_at, event_type
                FROM canonical_events
                WHERE league_id = ?
                  AND season = ?
                  AND occurred_at >= ?
                  AND occurred_at < ?
                ORDER BY occurred_at ASC, id ASC
                """,
                (league_id, season, window_start, window_end),
            ).fetchall()

            signals: List[dict] = []
            for r in rows:
                # Stable id for the signal: prefix + canonical event id
                sid = f"ce:{r['id']}"

                # Minimal dict compatible with DictSignalAdapter
                signals.append(
                    {
                        "signal_id": sid,
                        "confidence": "A",            # v0: treat canonical events as high confidence
                        "lineage_complete": True,     # canonical_events are already normalized truth
                        "in_window": True,            # ensured by the query
                        "sensitive": False,           # v0 default
                        "ambiguous": False,           # v0 default
                        # optional redundancy_key could be added later
                        # "redundancy_key": ...
                        # keep a few debug-friendly fields (NOT used by adapter, but harmless):
                        "source": "canonical_events",
                        "event_type": r["event_type"],
                        "occurred_at": r["occurred_at"],
                    }
                )

            return signals
        finally:
            con.close()


__all__ = [
    "CanonicalEventsSignalExtractorV1",
]
