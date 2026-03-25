#!/usr/bin/env python3
"""
SquadVault: Batch Historical Ingest — All Seasons (Multi-ID Aware)

PFL Buddies has been on MFL since 2009 with different server assignments
and league IDs each year. This script maps each historical year to the
correct MFL server + league_id for API calls, while storing ALL events
under the canonical SquadVault league_id (70985).

This is architecturally correct: SquadVault's league_id represents the
logical league. MFL's per-year league_id is an external system artifact
used only for API calls.

Usage (from repo root):
    pip install anthropic requests python-dotenv
    ./scripts/recap.sh migrate --db .local_squadvault.sqlite
    python ingest_all_seasons.py --dry-run   # preview
    python ingest_all_seasons.py             # execute

Env vars (set in .env or export):
    MFL_USERNAME   — optional (for private leagues)
    MFL_PASSWORD   — optional
    SQUADVAULT_DB  — optional (default: .local_squadvault.sqlite)
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Bootstrap: ensure we can import squadvault ─────────────────────────
REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

from squadvault.core.storage.sqlite_store import SQLiteStore
from squadvault.core.storage.session import DatabaseSession
from squadvault.core.storage.migrate import apply_migrations
from squadvault.core.canonicalize.run_canonicalize import canonicalize
from squadvault.mfl.client import MflClient
from squadvault.ingest.matchup_results import derive_matchup_result_envelopes
from squadvault.ingest.transactions import derive_transaction_event_envelopes
from squadvault.ingest.auction_draft import derive_auction_event_envelopes_from_transactions
from squadvault.ingest.waiver_bids import derive_waiver_bid_event_envelopes_from_transactions


# ── PFL Buddies: Historical MFL Configuration ─────────────────────────
# Each year has a potentially different server and MFL league_id.
# All data is stored under CANONICAL_LEAGUE_ID in SquadVault.

CANONICAL_LEAGUE_ID = "70985"

SEASON_CONFIG = [
    # (year, mfl_server, mfl_league_id)
    (2009, "48", "50536"),
    (2010, "46", "78078"),
    (2011, "49", "36134"),
    (2012, "45", "15389"),
    (2013, "49", "34148"),
    (2014, "45", "43138"),
    (2015, "44", "26884"),
    (2016, "44", "47199"),
    (2017, "44", "70985"),
    (2018, "44", "70985"),
    (2019, "44", "70985"),
    (2020, "44", "70985"),
    (2021, "44", "70985"),
    (2022, "44", "70985"),
    (2023, "44", "70985"),
    (2024, "44", "70985"),
]


# ── HTTP helpers ───────────────────────────────────────────────────────

def _mfl_json(url: str, timeout: int = 30) -> Dict[str, Any]:
    """Fetch JSON from MFL API."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "SquadVault/0.1 (+https://squadvault.local)",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ── Franchise directory ingest ─────────────────────────────────────────

def ingest_franchises(
    *,
    db_path: str,
    mfl_server: str,
    mfl_league_id: str,
    canonical_league_id: str,
    season: int,
) -> int:
    """Fetch franchise directory from MFL and upsert under canonical league_id."""
    host = f"www{mfl_server}.myfantasyleague.com"
    url = f"https://{host}/{season}/export?TYPE=league&L={mfl_league_id}&JSON=1"

    try:
        data = _mfl_json(url)
    except Exception as e:
        print(f"    FETCH ERROR: {e}")
        return 0

    franchises = data.get("league", {}).get("franchises", {}).get("franchise", [])
    if isinstance(franchises, dict):
        franchises = [franchises]

    if not franchises:
        print(f"    No franchises found")
        return 0

    with DatabaseSession(db_path) as conn:
        count = 0
        for f in franchises:
            fid = str(f.get("id", "")).strip()
            name = str(f.get("name", "")).strip() or fid
            owner = str(f.get("owner_name", "") or f.get("ownerName", "") or "").strip()
            if not fid:
                continue

            conn.execute("""
                INSERT INTO franchise_directory
                    (league_id, season, franchise_id, name, owner_name, raw_json)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(league_id, season, franchise_id) DO UPDATE SET
                    name=excluded.name,
                    owner_name=excluded.owner_name,
                    raw_json=excluded.raw_json,
                    updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
            """, (canonical_league_id, season, fid, name, owner, json.dumps(f)[:2000]))
            count += 1

        conn.commit()

    return count


# ── Player directory ingest ────────────────────────────────────────────

def ingest_players(
    *,
    db_path: str,
    mfl_server: str,
    mfl_league_id: str,
    canonical_league_id: str,
    season: int,
) -> int:
    """Fetch player directory from MFL and upsert under canonical league_id."""
    host = f"www{mfl_server}.myfantasyleague.com"
    url = f"https://{host}/{season}/export?TYPE=players&L={mfl_league_id}&JSON=1"

    try:
        data = _mfl_json(url)
    except Exception as e:
        print(f"    FETCH ERROR: {e}")
        return 0

    players = data.get("players", {}).get("player", [])
    if isinstance(players, dict):
        players = [players]

    if not players:
        print(f"    No players found")
        return 0

    with DatabaseSession(db_path) as conn:
        count = 0
        for p in players:
            pid = str(p.get("id", "")).strip()
            if not pid:
                continue
            name = str(p.get("name", "")).strip()
            pos = str(p.get("position", "")).strip()
            team = str(p.get("team", "")).strip()

            conn.execute("""
                INSERT INTO player_directory
                    (league_id, season, player_id, name, position, team, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(league_id, season, player_id) DO UPDATE SET
                    name=excluded.name,
                    position=excluded.position,
                    team=excluded.team,
                    raw_json=excluded.raw_json,
                    updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
            """, (canonical_league_id, season, pid, name, pos, team, json.dumps(p)[:2000]))
            count += 1

        conn.commit()

    return count


# ── Matchup results ingest ─────────────────────────────────────────────

def ingest_matchups(
    *,
    db_path: str,
    mfl_server: str,
    mfl_league_id: str,
    canonical_league_id: str,
    season: int,
    max_weeks: int = 18,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> tuple[int, int]:
    """Fetch matchup results for all weeks and store under canonical league_id."""
    client = MflClient(
        server=mfl_server,
        league_id=mfl_league_id,
        username=username,
        password=password,
    )

    store = SQLiteStore(db_path)
    total_inserted = 0
    total_skipped = 0

    for week in range(1, max_weeks + 1):
        try:
            raw_json, source_url = client.get_weekly_results(year=season, week=week)
        except Exception:
            continue

        events = derive_matchup_result_envelopes(
            year=season,
            week=week,
            league_id=canonical_league_id,
            weekly_results_json=raw_json,
            source_url=source_url,
        )

        if events:
            inserted, skipped = store.append_events(events)
            total_inserted += inserted
            total_skipped += skipped

    return total_inserted, total_skipped


# ── Transactions ingest ────────────────────────────────────────────────

def ingest_transactions(
    *,
    db_path: str,
    mfl_server: str,
    mfl_league_id: str,
    canonical_league_id: str,
    season: int,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> tuple[int, int]:
    """Fetch transactions and store under canonical league_id."""
    client = MflClient(
        server=mfl_server,
        league_id=mfl_league_id,
        username=username,
        password=password,
    )

    try:
        raw_json, source_url = client.get_transactions(year=season)
    except Exception as e:
        print(f"    FETCH ERROR: {e}")
        return 0, 0

    transactions = raw_json.get("transactions", {}).get("transaction", [])
    if isinstance(transactions, dict):
        transactions = [transactions]

    events: list[dict] = []
    events += derive_auction_event_envelopes_from_transactions(
        year=season,
        league_id=canonical_league_id,
        transactions=transactions,
        source_url=source_url,
    )
    events += derive_transaction_event_envelopes(
        year=season,
        league_id=canonical_league_id,
        transactions=transactions,
        source_url=source_url,
    )
    events += derive_waiver_bid_event_envelopes_from_transactions(
        year=season,
        league_id=canonical_league_id,
        transactions=transactions,
        source_url=source_url,
    )

    if events:
        inserted, skipped = store.append_events(events)
        return inserted, skipped

    return 0, 0


# ── Season orchestration ──────────────────────────────────────────────

def ingest_season(
    *,
    season: int,
    mfl_server: str,
    mfl_league_id: str,
    canonical_league_id: str,
    db_path: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> dict:
    """Ingest all data for one season. Returns status dict."""
    print(f"\n{'='*60}")
    print(f"  SEASON {season} (MFL: server=www{mfl_server}, id={mfl_league_id})")
    print(f"  → stored as league_id={canonical_league_id}")
    print(f"{'='*60}")

    result = {
        "year": season,
        "mfl_server": mfl_server,
        "mfl_league_id": mfl_league_id,
        "franchises": 0,
        "players": 0,
        "matchups_inserted": 0,
        "txn_inserted": 0,
        "canonicalized": False,
    }

    # 1. Franchises
    print(f"  [franchises]")
    n = ingest_franchises(
        db_path=db_path,
        mfl_server=mfl_server,
        mfl_league_id=mfl_league_id,
        canonical_league_id=canonical_league_id,
        season=season,
    )
    result["franchises"] = n
    print(f"    {n} franchises")

    # 2. Players
    print(f"  [players]")
    n = ingest_players(
        db_path=db_path,
        mfl_server=mfl_server,
        mfl_league_id=mfl_league_id,
        canonical_league_id=canonical_league_id,
        season=season,
    )
    result["players"] = n
    print(f"    {n} players")

    # 3. Matchups
    print(f"  [matchups]")
    ins, skip = ingest_matchups(
        db_path=db_path,
        mfl_server=mfl_server,
        mfl_league_id=mfl_league_id,
        canonical_league_id=canonical_league_id,
        season=season,
        username=username,
        password=password,
    )
    result["matchups_inserted"] = ins
    print(f"    {ins} inserted, {skip} skipped")

    # 4. Transactions
    print(f"  [transactions]")
    ins, skip = ingest_transactions(
        db_path=db_path,
        mfl_server=mfl_server,
        mfl_league_id=mfl_league_id,
        canonical_league_id=canonical_league_id,
        season=season,
        username=username,
        password=password,
    )
    result["txn_inserted"] = ins
    print(f"    {ins} inserted, {skip} skipped")

    # 5. Canonicalize
    print(f"  [canonicalize]")
    try:
        canonicalize(
            league_id=canonical_league_id,
            season=season,
            db_path=db_path,
        )
        result["canonicalized"] = True
        print(f"    OK")
    except Exception as e:
        print(f"    ERROR: {e}")

    # Brief pause to be polite to MFL servers
    time.sleep(1.5)

    return result


# ── Main ──────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Batch ingest all PFL Buddies historical seasons from MFL."
    )
    ap.add_argument("--db", default=os.environ.get("SQUADVAULT_DB", ".local_squadvault.sqlite"))
    ap.add_argument("--start-year", type=int, default=2009, help="First season (default: 2009)")
    ap.add_argument("--end-year", type=int, default=2024, help="Last season (default: 2024)")
    ap.add_argument("--dry-run", action="store_true", help="Print plan without executing")
    args = ap.parse_args()

    db_path = str(Path(args.db).resolve())
    username = os.environ.get("MFL_USERNAME")
    password = os.environ.get("MFL_PASSWORD")

    # Filter to requested year range
    configs = [(y, s, lid) for y, s, lid in SEASON_CONFIG
               if args.start_year <= y <= args.end_year]

    if not configs:
        print(f"No seasons configured for {args.start_year}–{args.end_year}")
        return 1

    print("\n" + "=" * 60)
    print("  SquadVault: PFL Buddies Historical Ingest")
    print("=" * 60)
    print(f"  DB:              {args.db}")
    print(f"  Canonical ID:    {CANONICAL_LEAGUE_ID}")
    print(f"  Seasons:         {configs[0][0]}–{configs[-1][0]} ({len(configs)} seasons)")
    print(f"  Auth:            {'yes' if username else 'no'}")

    print(f"\n  {'Year':<6} {'Server':<10} {'MFL ID':<8}")
    print(f"  {'----':<6} {'------':<10} {'------':<8}")
    for year, server, mfl_id in configs:
        marker = "" if mfl_id == CANONICAL_LEAGUE_ID else " ← remapped"
        print(f"  {year:<6} www{server:<7} {mfl_id:<8}{marker}")

    if args.dry_run:
        print(f"\n  DRY RUN — would ingest {len(configs)} seasons.")
        print("  Per season: franchises → players → matchups → transactions → canonicalize")
        print(f"  All stored under canonical league_id={CANONICAL_LEAGUE_ID}")
        return 0

    # Ensure schema exists
    schema_path = REPO_ROOT / "src" / "squadvault" / "core" / "storage" / "schema.sql"
    if not Path(db_path).exists():
        print("\n--- Initializing database ---")
        schema_sql = schema_path.read_text(encoding="utf-8")
        con = sqlite3.connect(db_path)
        con.executescript(schema_sql)
        con.close()
        print("  Created fresh DB from schema.sql")

    print("\n--- Applying migrations ---")
    applied = apply_migrations(db_path)
    if applied:
        for v in applied:
            print(f"  applied: {v}")
    else:
        print("  up to date")

    # Ingest each season
    all_results = []
    for year, server, mfl_id in configs:
        result = ingest_season(
            season=year,
            mfl_server=server,
            mfl_league_id=mfl_id,
            canonical_league_id=CANONICAL_LEAGUE_ID,
            db_path=db_path,
            username=username,
            password=password,
        )
        all_results.append(result)

    # Summary
    print("\n" + "=" * 60)
    print("  INGEST SUMMARY")
    print("=" * 60)
    print(f"  {'Year':<6} {'Franch':<8} {'Players':<9} {'Match':<8} {'Txn':<8} {'Canon':<6}")
    print(f"  {'----':<6} {'------':<8} {'-------':<9} {'-----':<8} {'---':<8} {'-----':<6}")

    for r in all_results:
        print(
            f"  {r['year']:<6} "
            f"{r['franchises']:<8} "
            f"{r['players']:<9} "
            f"{r['matchups_inserted']:<8} "
            f"{r['txn_inserted']:<8} "
            f"{'OK' if r['canonicalized'] else 'FAIL':<6}"
        )

    total_matchups = sum(r["matchups_inserted"] for r in all_results)
    total_txn = sum(r["txn_inserted"] for r in all_results)
    print(f"\n  Total matchups inserted: {total_matchups}")
    print(f"  Total transactions inserted: {total_txn}")

    # Show DB stats
    print("\n--- Post-ingest DB stats ---")
    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT season, COUNT(*) FROM canonical_events
               WHERE league_id=? AND event_type='WEEKLY_MATCHUP_RESULT'
               GROUP BY season ORDER BY season""",
            (CANONICAL_LEAGUE_ID,),
        ).fetchall()
        print(f"\n  Matchups per season (canonical):")
        for season, count in rows:
            print(f"    {season}: {count}")

        rows = con.execute(
            """SELECT event_type, COUNT(*) FROM canonical_events
               WHERE league_id=?
               GROUP BY event_type ORDER BY COUNT(*) DESC""",
            (CANONICAL_LEAGUE_ID,),
        ).fetchall()
        print(f"\n  Canonical events by type:")
        for etype, count in rows:
            print(f"    {etype:<30} {count:>6}")

        fc = con.execute(
            "SELECT COUNT(*) FROM franchise_directory WHERE league_id=?",
            (CANONICAL_LEAGUE_ID,),
        ).fetchone()[0]
        pc = con.execute(
            "SELECT COUNT(*) FROM player_directory WHERE league_id=?",
            (CANONICAL_LEAGUE_ID,),
        ).fetchone()[0]
        seasons = con.execute(
            "SELECT COUNT(DISTINCT season) FROM canonical_events WHERE league_id=?",
            (CANONICAL_LEAGUE_ID,),
        ).fetchone()[0]
        print(f"\n  franchise_directory: {fc} rows")
        print(f"  player_directory:   {pc} rows")
        print(f"  seasons with data:  {seasons}")

    print("\n--- Next steps ---")
    print("  1. Review the summary above")
    print("  2. Archive this script: mv ingest_all_seasons.py scripts/_archive/delivery/")
    print("  3. Regenerate 2024 recaps with full historical context:")
    print(f"     ./scripts/recap.sh regen --db {args.db} \\")
    print(f"       --league-id {CANONICAL_LEAGUE_ID} --season 2024 --week-index 6 \\")
    print(f'       --reason "historical backfill" --created-by steve --force')
    print("  4. Read the output — does it feel like it knows your league?")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
