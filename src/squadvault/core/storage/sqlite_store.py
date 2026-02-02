import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _now_iso_z() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class SQLiteStore:
    db_path: Path

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self, schema_sql: str) -> None:
        with self.connect() as conn:
            conn.executescript(schema_sql)
            conn.commit()

    def append_events(self, events: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Append-only insert. Idempotent by (external_source, external_id).
        Returns (inserted_count, skipped_count).
        """
        inserted = 0
        skipped = 0

        with self.connect() as conn:
            for e in events:
                try:
                    conn.execute(
                        """
                        INSERT INTO memory_events (
                          league_id, season,
                          external_source, external_id,
                          event_type,
                          occurred_at, ingested_at,
                          payload_json
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            e["league_id"],
                            int(e["season"]),
                            e["external_source"],
                            e["external_id"],
                            e["event_type"],
                            e.get("occurred_at"),
                            _now_iso_z(),
                            json.dumps(e["payload"], separators=(",", ":"), sort_keys=True),
                        ),
                    )
                    inserted += 1
                except sqlite3.IntegrityError:
                    skipped += 1

            conn.commit()

        return inserted, skipped

    # IMPORTANT:
    # Downstream consumers must read from canonical (v_canonical_best_events).
    # memory_events is an internal ledger and must not be consumed directly.

    def fetch_events(
        self,
        *,
        league_id: str,
        season: int,
        occurred_at_min: Optional[str] = None,
        occurred_at_max: Optional[str] = None,
        limit: int = 1000,
        use_canonical: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Downstream consumer read surface.

        - use_canonical=True reads from v_canonical_best_events (preferred).
        - use_canonical=False reads from memory_events (ledger / audit).
        """
        source = "v_canonical_best_events" if use_canonical else "memory_events"

        q = f"""
        SELECT
          league_id, season,
          external_source, external_id,
          event_type,
          occurred_at, ingested_at,
          payload_json
        FROM {source}
        WHERE league_id = ? AND season = ?
        """
        params: List[Any] = [league_id, int(season)]

        if occurred_at_min is not None:
            q += " AND (occurred_at IS NOT NULL AND occurred_at >= ?)"
            params.append(occurred_at_min)

        if occurred_at_max is not None:
            q += " AND (occurred_at IS NOT NULL AND occurred_at <= ?)"
            params.append(occurred_at_max)

        # IMPORTANT:
        # - memory_events has `id`, but the canonical view may not.
        # - so we use different stable tie-breakers depending on the source.
        if use_canonical:
            q += " ORDER BY occurred_at ASC NULLS LAST, external_source ASC, external_id ASC LIMIT ?"
        else:
            q += " ORDER BY occurred_at ASC NULLS LAST, id ASC LIMIT ?"

        params.append(int(limit))

        with self.connect() as conn:
            rows = conn.execute(q, params).fetchall()

        out: List[Dict[str, Any]] = []
        for r in rows:
            out.append(
                {
                    "league_id": r["league_id"],
                    "season": r["season"],
                    "external_source": r["external_source"],
                    "external_id": r["external_id"],
                    "event_type": r["event_type"],
                    "occurred_at": r["occurred_at"],
                    "ingested_at": r["ingested_at"],
                    "payload": json.loads(r["payload_json"]),
                }
            )
        return out

    def fetch_events_in_range(
        self,
        *,
        league_id: str,
        season: int,
        occurred_at_min: str,
        occurred_at_max: str,
        limit: int = 5000,
    ) -> List[Dict[str, Any]]:
        """
        Convenience wrapper for canonical-only reads in a time range.
        occurred_at_* must be ISO8601 with trailing 'Z' (UTC).
        """
        return self.fetch_events(
            league_id=league_id,
            season=season,
            occurred_at_min=occurred_at_min,
            occurred_at_max=occurred_at_max,
            limit=limit,
            use_canonical=True,
        )
