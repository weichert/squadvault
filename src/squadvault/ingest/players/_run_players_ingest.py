#!/usr/bin/env python3
"""
SquadVault: Players Directory Ingest (MFL TYPE=players)

Downloads the MFL players directory for a given league/season and upserts into SQLite.

Expected table:
  player_directory(
    league_id TEXT NOT NULL,
    season INTEGER NOT NULL,
    player_id TEXT NOT NULL,
    name TEXT,
    position TEXT,
    team TEXT,
    raw_json TEXT,
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    PRIMARY KEY (league_id, season, player_id)
  )

Run:
  ./scripts/py -u src/squadvault/ingest/players/_run_players_ingest.py \
    --db .local_squadvault.sqlite \
    --server www44.myfantasyleague.com \
    --league-id 70985 \
    --season 2024
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class PlayerRow:
    player_id: str
    name: Optional[str]
    position: Optional[str]
    team: Optional[str]
    raw_json: Optional[str]


def _now_iso_z() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _build_players_url(server: str, season: int, league_id: str, json_mode: bool) -> str:
    q = {"TYPE": "players", "L": league_id}
    if json_mode:
        q["JSON"] = "1"
    return f"https://{server}/{season}/export?{urllib.parse.urlencode(q)}"


def _fetch_url(url: str, timeout_s: int = 30) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "SquadVault/players-ingest (python urllib)",
            "Accept": "*/*",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return resp.read()


def _parse_players_json(payload: bytes) -> List[PlayerRow]:
    data = json.loads(payload.decode("utf-8", errors="replace"))

    players_node = data.get("players") or data.get("Players") or data
    player_list = None

    if isinstance(players_node, dict):
        player_list = players_node.get("player") or players_node.get("Player")
    if player_list is None and isinstance(data, dict):
        player_list = data.get("player")

    if player_list is None:
        raise ValueError("JSON parse: could not find players.player list in payload")

    if isinstance(player_list, dict):
        player_list = [player_list]
    if not isinstance(player_list, list):
        raise ValueError(f"JSON parse: unexpected player_list type: {type(player_list)}")

    out: List[PlayerRow] = []
    for p in player_list:
        if not isinstance(p, dict):
            continue

        pid = str(p.get("id") or p.get("player_id") or p.get("playerId") or "").strip()
        if not pid:
            continue

        name = p.get("name") or p.get("player_name") or p.get("playerName")
        if isinstance(name, str):
            name = name.strip() or None

        pos = p.get("position") or p.get("pos") or p.get("Position")
        if isinstance(pos, str):
            pos = pos.strip() or None

        team = p.get("team") or p.get("Team")
        if isinstance(team, str):
            team = team.strip() or None

        raw = json.dumps(p, ensure_ascii=False, separators=(",", ":"))
        out.append(PlayerRow(player_id=pid, name=name, position=pos, team=team, raw_json=raw))

    if not out:
        raise ValueError("JSON parse: extracted 0 players (unexpected)")

    return out


def _parse_players_xml(payload: bytes) -> List[PlayerRow]:
    root = ET.fromstring(payload.decode("utf-8", errors="replace"))

    out: List[PlayerRow] = []
    for el in root.findall(".//player"):
        pid = (el.get("id") or el.get("player_id") or "").strip()
        if not pid:
            continue
        name = (el.get("name") or "").strip() or None
        pos = (el.get("position") or el.get("pos") or "").strip() or None
        team = (el.get("team") or "").strip() or None

        raw = ET.tostring(el, encoding="unicode")
        out.append(PlayerRow(player_id=pid, name=name, position=pos, team=team, raw_json=raw))

    if not out:
        raise ValueError("XML parse: extracted 0 players (unexpected)")

    return out


def _ensure_table_exists(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS player_directory (
          league_id   TEXT    NOT NULL,
          season      INTEGER NOT NULL,
          player_id   TEXT    NOT NULL,
          name        TEXT,
          position    TEXT,
          team        TEXT,
          raw_json    TEXT,
          updated_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
          PRIMARY KEY (league_id, season, player_id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_player_directory_lookup
          ON player_directory (league_id, season, player_id)
        """
    )
    conn.commit()


def _upsert_players(
    conn: sqlite3.Connection,
    league_id: str,
    season: int,
    players: Iterable[PlayerRow],
) -> Tuple[int, int]:
    now = _now_iso_z()

    sql = """
    INSERT INTO player_directory (
      league_id, season, player_id,
      name, position, team,
      raw_json, updated_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(league_id, season, player_id) DO UPDATE SET
      name = excluded.name,
      position = excluded.position,
      team = excluded.team,
      raw_json = excluded.raw_json,
      updated_at = excluded.updated_at
    """

    rows = [
        (league_id, season, p.player_id, p.name, p.position, p.team, p.raw_json, now)
        for p in players
    ]

    with conn:
        conn.executemany(sql, rows)

    return (len(rows), len(rows))


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Ingest MFL TYPE=players into player_directory (SQLite).")
    ap.add_argument("--db", required=True, help="Path to SQLite DB (e.g. .local_squadvault.sqlite)")
    ap.add_argument("--server", required=True, help="MFL server host (e.g. www44.myfantasyleague.com)")
    ap.add_argument("--league-id", required=True, help="MFL league id (e.g. 70985)")
    ap.add_argument("--season", required=True, type=int, help="Season year (e.g. 2024)")
    ap.add_argument("--timeout", type=int, default=30, help="HTTP timeout seconds (default: 30)")
    args = ap.parse_args(argv)

    db_path = args.db
    server = args.server
    league_id = str(args.league_id)
    season = int(args.season)

    print("=== SquadVault Players Ingest ===")
    print(f"DB      : {db_path}")
    print(f"Server  : {server}")
    print(f"League  : {league_id}")
    print(f"Season  : {season}")
    print()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        _ensure_table_exists(conn)

        url_json = _build_players_url(server, season, league_id, json_mode=True)
        url_plain = _build_players_url(server, season, league_id, json_mode=False)

        players: List[PlayerRow] = []

        # Try JSON first
        try:
            print(f"Fetching (JSON): {url_json}")
            payload = _fetch_url(url_json, timeout_s=args.timeout)
            players = _parse_players_json(payload)
            print(f"Parsed players (JSON): {len(players)}")
        except Exception as e_json:
            print(f"JSON fetch/parse failed, falling back to XML. Reason: {e_json}")
            print(f"Fetching (XML): {url_plain}")
            payload = _fetch_url(url_plain, timeout_s=args.timeout)
            players = _parse_players_xml(payload)
            print(f"Parsed players (XML): {len(players)}")

        _, total = _upsert_players(conn, league_id, season, players)

        print()
        print("=== Results ===")
        print(f"players_parsed  : {len(players)}")
        print(f"rows_written    : {total}")
        print()

        cur = conn.execute(
            """
            SELECT player_id, name, position, team, updated_at
            FROM player_directory
            WHERE league_id=? AND season=?
            ORDER BY name
            LIMIT 5
            """,
            (league_id, season),
        )
        sample = cur.fetchall()
        if sample:
            print("Sample (first 5 by name):")
            for r in sample:
                print(f"  {r['player_id']:>6}  {r['name'] or '?':<28}  {r['position'] or '?':<5}  {r['team'] or '?':<4}")
        else:
            print("No rows found in player_directory after ingest (unexpected).")

        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
