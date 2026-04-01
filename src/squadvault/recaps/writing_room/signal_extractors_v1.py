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

Enhancement:
- Add deterministic redundancy_key when possible to collapse obvious duplicates.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from squadvault.core.storage.db_utils import table_columns as _table_columns
from squadvault.core.storage.session import DatabaseSession


def _redundancy_key_for_row(
    *,
    event_type: str,
    occurred_at: str | None,
    action_fingerprint: str | None,
) -> str | None:
    """
    Deterministic redundancy keys.

    Priority:
    1) action_fingerprint when present: groups multi-row composites that share an action.
    2) timestamp bucketing for known noisy event types (LOCK duplicates):
       event_type + occurred_at.
    """
    if action_fingerprint:
        return f"rk:af:{action_fingerprint}"

    if occurred_at and event_type in {"TRANSACTION_LOCK_ALL_PLAYERS"}:
        return f"rk:ts:{event_type}:{occurred_at}"

    return None


@dataclass(frozen=True, slots=True)
class CanonicalEventsSignalExtractorV1:
    """
    Extract dict-signals from canonical_events for a given window.

    Assumptions:
    - canonical_events exists.
    - minimum columns: id, league_id, season, occurred_at, event_type
    - optional column: action_fingerprint
    """

    def extract_signals(
        self,
        *,
        db_path: str,
        league_id: str,
        season: int,
        window_start: str,
        window_end: str,
    ) -> list[dict]:
        """Extract canonical signals from DB for a league/season/week."""
        with DatabaseSession(db_path) as con:
            con.row_factory = sqlite3.Row
            cols = _table_columns(con, "canonical_events")

            select_cols: list[str] = ["id", "occurred_at", "event_type"]
            if "action_fingerprint" in cols:
                select_cols.append("action_fingerprint")

            cur = con.cursor()

            rows = cur.execute(
                f"""
                SELECT {", ".join(select_cols)}
                FROM canonical_events
                WHERE league_id = ?
                  AND season = ?
                  AND occurred_at >= ?
                  AND occurred_at < ?
                ORDER BY occurred_at ASC, id ASC
                """,
                (league_id, season, window_start, window_end),
            ).fetchall()

            signals: list[dict] = []
            for r in rows:
                sid = f"ce:{r['id']}"

                occurred_at = r["occurred_at"]
                event_type = r["event_type"]
                action_fingerprint = r["action_fingerprint"] if "action_fingerprint" in r.keys() else None

                rk = _redundancy_key_for_row(
                    event_type=str(event_type),
                    occurred_at=str(occurred_at) if occurred_at is not None else None,
                    action_fingerprint=str(action_fingerprint) if action_fingerprint else None,
                )

                payload = {
                    # Required adapter keys
                    "signal_id": sid,
                    "confidence": "A",
                    "lineage_complete": True,
                    "in_window": True,
                    "sensitive": False,
                    "ambiguous": False,

                    # Optional: used by intake_v1 redundancy collapse
                    "redundancy_key": rk,

                    # Debug-friendly fields (ignored by adapter)
                    "source": "canonical_events",
                    "event_type": str(event_type),
                    "occurred_at": str(occurred_at) if occurred_at is not None else None,
                }

                # Keep output minimal: drop redundancy_key if None.
                if payload["redundancy_key"] is None:
                    payload.pop("redundancy_key")

                signals.append(payload)

            return signals


__all__ = [
    "CanonicalEventsSignalExtractorV1",
]
