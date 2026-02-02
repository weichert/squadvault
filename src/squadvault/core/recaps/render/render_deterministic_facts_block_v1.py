from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List

from squadvault.recaps.deterministic_bullets_v1 import (
    CanonicalEventRow,
    QUIET_WEEK_MIN_EVENTS,
    render_deterministic_bullets_v1,
)


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def _fetch_canonical_events_by_ids(
    db_path: str,
    league_id: str,
    season: int,
    canonical_ids: List[int],
) -> List[Dict[str, Any]]:
    if not canonical_ids:
        return []

    CHUNK = 500
    out: List[Dict[str, Any]] = []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    for i in range(0, len(canonical_ids), CHUNK):
        chunk = canonical_ids[i : i + CHUNK]
        placeholders = ",".join(["?"] * len(chunk))
        cur.execute(
            f"""
            SELECT
              id AS canonical_id,
              occurred_at,
              event_type,
              best_memory_event_id
            FROM canonical_events
            WHERE league_id = ?
              AND season = ?
              AND id IN ({placeholders})
            """,
            [league_id, season, *chunk],
        )
        out.extend(_row_to_dict(r) for r in cur.fetchall())

    conn.close()
    return out


def _fetch_memory_payloads_by_ids(
    db_path: str,
    memory_event_ids: List[int],
) -> Dict[int, Dict[str, Any]]:
    if not memory_event_ids:
        return {}

    CHUNK = 500
    out: Dict[int, Dict[str, Any]] = {}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    for i in range(0, len(memory_event_ids), CHUNK):
        chunk = memory_event_ids[i : i + CHUNK]
        placeholders = ",".join(["?"] * len(chunk))
        cur.execute(
            f"""
            SELECT id, payload_json
            FROM memory_events
            WHERE id IN ({placeholders})
            """,
            list(chunk),
        )
        for r in cur.fetchall():
            d = _row_to_dict(r)
            raw = d.get("payload_json") or ""
            payload: Dict[str, Any] = {}
            if isinstance(raw, str) and raw.strip():
                try:
                    val = json.loads(raw)
                    payload = val if isinstance(val, dict) else {}
                except Exception:
                    payload = {}
            out[int(d["id"])] = payload

    conn.close()
    return out


def _norm_id(raw: Any) -> str:
    s = "" if raw is None else str(raw).strip()
    if not s:
        return ""
    if s.isdigit():
        return s.lstrip("0") or "0"
    return s


class _NameLookup:
    """
    Deterministic DB-backed name lookups.
    Uses franchise_directory + player_directory (written by ingest scripts).
    Tries exact id, then normalized id (strip leading zeros).
    """

    def __init__(self, db_path: str, league_id: str, season: int):
        self.db_path = db_path
        self.league_id = league_id
        self.season = season
        self._player_cache: Dict[str, str] = {}
        self._franchise_cache: Dict[str, str] = {}

    def franchise_name(self, fid_raw: Any) -> str:
        key = "" if fid_raw is None else str(fid_raw).strip()
        if not key:
            return "Unknown team"
        if key in self._franchise_cache:
            return self._franchise_cache[key]

        name = self._query_franchise_name(key)
        if not name:
            alt = _norm_id(key)
            if alt and alt != key:
                name = self._query_franchise_name(alt)

        out = name or key
        self._franchise_cache[key] = out
        return out

    def player_name(self, pid_raw: Any) -> str:
        key = "" if pid_raw is None else str(pid_raw).strip()
        if not key:
            return "Unknown player"
        if key in self._player_cache:
            return self._player_cache[key]

        name = self._query_player_name(key)
        if not name:
            alt = _norm_id(key)
            if alt and alt != key:
                name = self._query_player_name(alt)

        out = name or key
        self._player_cache[key] = out
        return out

    def _query_franchise_name(self, fid: str) -> str:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT name
            FROM franchise_directory
            WHERE league_id = ?
              AND season = ?
              AND franchise_id = ?
            LIMIT 1
            """,
            (self.league_id, self.season, fid),
        )
        row = cur.fetchone()
        conn.close()
        return "" if row is None else (row["name"] or "")

    def _query_player_name(self, pid: str) -> str:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT name
            FROM player_directory
            WHERE league_id = ?
              AND season = ?
              AND player_id = ?
            LIMIT 1
            """,
            (self.league_id, self.season, pid),
        )
        row = cur.fetchone()
        conn.close()
        return "" if row is None else (row["name"] or "")


def build_deterministic_facts_block_v1(
    *,
    db_path: str,
    league_id: str,
    season: int,
    canonical_ids: List[int],
) -> str:
    """
    Returns a deterministic bullet block or "".
    Intended for non-quiet weeks only.
    """
    if len(canonical_ids) < QUIET_WEEK_MIN_EVENTS:
        return ""

    canon_rows = _fetch_canonical_events_by_ids(db_path, league_id, season, canonical_ids)

    mem_ids = sorted(
        {
            int(r["best_memory_event_id"])
            for r in canon_rows
            if r.get("best_memory_event_id") is not None
        }
    )
    mem_payload_by_id = _fetch_memory_payloads_by_ids(db_path, mem_ids)

    rows: list[CanonicalEventRow] = []
    for r in canon_rows:
        mid = r.get("best_memory_event_id")
        payload = mem_payload_by_id.get(int(mid), {}) if mid is not None else {}
        rows.append(
            CanonicalEventRow(
                canonical_id=str(r["canonical_id"]),
                occurred_at=r.get("occurred_at") or "",
                event_type=r["event_type"],
                payload=payload,
            )
        )

    lookup = _NameLookup(db_path=db_path, league_id=league_id, season=season)

    bullets = render_deterministic_bullets_v1(
        rows,
        team_resolver=lookup.franchise_name,
        player_resolver=lookup.player_name,
    )

    if not bullets:
        return ""

    return "What happened (facts)\n" + "\n".join(f"- {b}" for b in bullets) + "\n\n"
