#!/usr/bin/env python3
"""
SquadVault: Franchise Directory Ingest (MFL TYPE=league)

Fetches:
  https://{server}/{season}/export?TYPE=league&L={league_id}&JSON=1

Parses:
  payload["franchises"]["franchise"] -> list of franchises

Upserts into:
  franchise_directory(league_id, season, franchise_id, name, owner_name, raw_json, updated_at)

Usage:
  ./scripts/py -u src/squadvault/ingest/franchises/_run_franchises_ingest.py \
    --db .local_squadvault.sqlite \
    --server www44.myfantasyleague.com \
    --league-id 70985 \
    --season 2024
"""

import argparse
import json
import re
import sqlite3
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _clean_html(s: Any) -> str:
    """MFL franchise names can contain HTML. Strip tags conservatively."""
    if s is None:
        return ""
    txt = str(s)
    txt = _HTML_TAG_RE.sub("", txt)
    return txt.strip()


def _http_get_json(url: str, timeout_s: int = 30) -> Dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "SquadVault/0.1 (+https://squadvault.local)",
            "Accept": "application/json",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        raw = resp.read()
    obj = json.loads(raw.decode("utf-8", errors="replace"))
    return obj if isinstance(obj, dict) else {}


def _extract_franchises(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    MFL TYPE=league franchise list is commonly nested under:
      payload["league"]["franchises"]["franchise"]

    Supported shapes:
      A) {"franchises": {"franchise": [...]}}
      B) {"league": {"franchises": {"franchise": [...]}}}
    """

    def from_container(container: Any) -> List[Dict[str, Any]]:
        if isinstance(container, dict):
            f = container.get("franchise")
            if isinstance(f, list):
                return [x for x in f if isinstance(x, dict)]
            if isinstance(f, dict):
                return [f]
        return []

    # A) top-level
    out = from_container(payload.get("franchises"))
    if out:
        return out

    # B) under league
    league = payload.get("league")
    if isinstance(league, dict):
        out = from_container(league.get("franchises"))
        if out:
            return out

    return []


@dataclass
class Row:
    franchise_id: str
    name: str
    owner_name: str
    raw_json: str


def _normalize_row(fr: Dict[str, Any]) -> Optional[Row]:
    fid = fr.get("id")
    if fid is None:
        return None
    fid_s = str(fid).strip()
    if not fid_s:
        return None

    name = _clean_html(fr.get("name"))
    owner = _clean_html(fr.get("owner_name"))

    raw_json = json.dumps(fr, ensure_ascii=False, sort_keys=True)

    return Row(franchise_id=fid_s, name=name, owner_name=owner, raw_json=raw_json)


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS franchise_directory (
          league_id     TEXT    NOT NULL,
          season        INTEGER NOT NULL,
          franchise_id  TEXT    NOT NULL,

          name          TEXT,
          owner_name    TEXT,

          raw_json      TEXT,
          updated_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),

          PRIMARY KEY (league_id, season, franchise_id)
        );
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_franchise_directory_lookup
          ON franchise_directory (league_id, season, franchise_id);
        """
    )


def _upsert_rows(conn: sqlite3.Connection, league_id: str, season: int, rows: List[Row]) -> int:
    sql = """
    INSERT INTO franchise_directory (
      league_id, season, franchise_id, name, owner_name, raw_json, updated_at
    ) VALUES (
      ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now')
    )
    ON CONFLICT(league_id, season, franchise_id) DO UPDATE SET
      name       = excluded.name,
      owner_name = excluded.owner_name,
      raw_json   = excluded.raw_json,
      updated_at = excluded.updated_at;
    """
    cur = conn.cursor()
    cur.executemany(
        sql,
        [(league_id, season, r.franchise_id, r.name, r.owner_name, r.raw_json) for r in rows],
    )
    return cur.rowcount if cur.rowcount is not None else len(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description="SquadVault franchise directory ingest (MFL TYPE=league).")
    ap.add_argument("--db", required=True, help="Path to SQLite DB (e.g. .local_squadvault.sqlite)")
    ap.add_argument("--server", required=True, help="MFL server (e.g. www44.myfantasyleague.com)")
    ap.add_argument("--league-id", required=True, help="League ID (e.g. 70985)")
    ap.add_argument("--season", type=int, required=True, help="Season year (e.g. 2024)")
    args = ap.parse_args()

    db_path = Path(args.db)
    league_id = str(args.league_id)
    season = int(args.season)
    server = str(args.server)

    print("=== SquadVault Franchise Ingest ===")
    print(f"DB      : {db_path}")
    print(f"Server  : {server}")
    print(f"League  : {league_id}")
    print(f"Season  : {season}")

    url = f"https://{server}/{season}/export?TYPE=league&L={league_id}&JSON=1"
    print(f"\nFetching (JSON): {url}")

    payload = _http_get_json(url)
    franchises = _extract_franchises(payload)
    print(f"Parsed franchises (JSON): {len(franchises)}")

    rows: List[Row] = []
    for fr in franchises:
        r = _normalize_row(fr)
        if r:
            rows.append(r)

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        _ensure_table(conn)

        with conn:
            written = _upsert_rows(conn, league_id=league_id, season=season, rows=rows)

        print("\n=== Results ===")
        print(f"franchises_parsed : {len(rows)}")
        print(f"rows_written      : {written}")

        _print_header("Sample (first 10 by franchise_id)")
        cur = conn.cursor()
        for fid, name, owner in cur.execute(
            """
            SELECT franchise_id, name, owner_name
            FROM franchise_directory
            WHERE league_id=? AND season=?
            ORDER BY franchise_id
            LIMIT 10
            """,
            (league_id, season),
        ).fetchall():
            print(f"  {fid}  {name or ''}  |  {owner or ''}")

    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
