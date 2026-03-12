"""Name resolution for players and franchises.

Canonical location for PlayerResolver and FranchiseResolver,
previously duplicated/embedded in consumer files.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from squadvault.core.storage.session import DatabaseSession


def _csv_ids(s: Any) -> List[str]:
    """Split a CSV string or list into stripped, non-empty ID strings."""
    if s is None:
        return []
    if isinstance(s, list):
        return [str(x).strip() for x in s if str(x).strip()]
    if isinstance(s, str):
        raw = s.strip()
        if not raw:
            return []
        return [x.strip() for x in raw.split(",") if x.strip()]
    sx = str(s).strip()
    return [sx] if sx else []


class PlayerResolver:
    """
    Resolve player_id -> "Name (Pos, Team)" using player_directory only.
    Fails safe: returns the raw id if not found.
    """

    def __init__(self, db_path: Path | str, league_id: str, season: int) -> None:
        self.db_path = Path(db_path)
        self.league_id = str(league_id)
        self.season = int(season)
        self._map: Dict[str, str] = {}
        self._loaded = False
        self._requested = 0
        self._resolved = 0

    @property
    def requested(self) -> int:
        """Return count of IDs requested for resolution."""
        return self._requested

    @property
    def resolved(self) -> int:
        """Return count of IDs successfully resolved."""
        return self._resolved

    def load_for_ids(self, player_ids: Set[str]) -> None:
        """Bulk-load name resolutions for a set of IDs from the database."""
        if self._loaded:
            return

        ids = {str(x).strip() for x in player_ids if str(x).strip()}
        self._requested = len(ids)

        if not ids:
            self._loaded = True
            return

        try:
            with DatabaseSession(str(self.db_path)) as conn:
                cur = conn.cursor()
                tables = {
                    r["name"]
                    for r in cur.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                }
                if "player_directory" not in tables:
                    self._loaded = True
                    return

                ids_list = sorted(ids)
                CHUNK = 900
                for i in range(0, len(ids_list), CHUNK):
                    chunk = ids_list[i : i + CHUNK]
                    placeholders = ",".join(["?"] * len(chunk))
                    rows = cur.execute(
                        f"""
                        SELECT player_id, name, position, team
                        FROM player_directory
                        WHERE league_id=? AND season=? AND player_id IN ({placeholders})
                        """,
                        [self.league_id, self.season, *chunk],
                    ).fetchall()

                    for r in rows:
                        pid = str(r["player_id"]).strip()
                        name = str(r["name"]).strip() if r["name"] is not None else ""
                        pos = str(r["position"]).strip() if r["position"] is not None else ""
                        team = str(r["team"]).strip() if r["team"] is not None else ""

                        extra = []
                        if pos:
                            extra.append(pos)
                        if team:
                            extra.append(team)

                        disp = f"{name} ({', '.join(extra)})" if (name and extra) else (name or pid)
                        if pid:
                            self._map[pid] = disp

            self._resolved = len(self._map)
            self._loaded = True

        except Exception:
            self._loaded = True

    def one(self, player_id: Any) -> str:
        """Resolve a single ID to its display name."""
        pid = str(player_id).strip() if player_id is not None else ""
        if not pid:
            return "<?>"
        return self._map.get(pid, pid)

    def many(self, ids: Any) -> List[str]:
        """Resolve a list of IDs to display names."""
        return [self.one(pid) for pid in _csv_ids(ids)]


class FranchiseResolver:
    """
    Resolve franchise_id -> franchise name using franchise_directory only.
    Fails safe: returns the raw id if not found.
    """

    def __init__(self, db_path: Path | str, league_id: str, season: int) -> None:
        self.db_path = Path(db_path)
        self.league_id = str(league_id)
        self.season = int(season)
        self._map: Dict[str, str] = {}
        self._loaded = False
        self._requested = 0
        self._resolved = 0

    @property
    def requested(self) -> int:
        """Return count of franchise IDs requested for resolution."""
        return self._requested

    @property
    def resolved(self) -> int:
        """Return count of franchise IDs successfully resolved."""
        return self._resolved

    def load_for_ids(self, franchise_ids: Set[str]) -> None:
        """Bulk-load franchise name resolutions from franchise_directory."""
        if self._loaded:
            return

        ids = {str(x).strip() for x in franchise_ids if str(x).strip()}
        self._requested = len(ids)

        if not ids:
            self._loaded = True
            return

        try:
            with DatabaseSession(str(self.db_path)) as conn:
                cur = conn.cursor()
                tables = {
                    r["name"]
                    for r in cur.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                }
                if "franchise_directory" not in tables:
                    self._loaded = True
                    return

                ids_list = sorted(ids)
                CHUNK = 900
                for i in range(0, len(ids_list), CHUNK):
                    chunk = ids_list[i : i + CHUNK]
                    placeholders = ",".join(["?"] * len(chunk))
                    rows = cur.execute(
                        f"""
                        SELECT franchise_id, name
                        FROM franchise_directory
                        WHERE league_id=? AND season=? AND franchise_id IN ({placeholders})
                        """,
                        [self.league_id, self.season, *chunk],
                    ).fetchall()

                    for r in rows:
                        fid = str(r["franchise_id"]).strip()
                        name = str(r["name"]).strip() if r["name"] is not None else ""
                        if fid:
                            self._map[fid] = name or fid

            self._resolved = len(self._map)
            self._loaded = True

        except Exception:
            self._loaded = True

    def one(self, franchise_id: Any) -> str:
        """Resolve a single franchise ID to its display name."""
        fid = str(franchise_id).strip() if franchise_id is not None else ""
        if not fid:
            return "?"
        return self._map.get(fid, fid)
