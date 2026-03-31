#!/usr/bin/env python3
"""
SquadVault: MFL Historical Ingestion

Discovers available seasons and ingests historical data into the SquadVault
memory ledger. Combines discovery + multi-season ingestion into one operator flow.

Usage (recommended — uses MFL history chain for automatic league ID resolution):
  ./scripts/py -u src/squadvault/mfl/_run_historical_ingest.py \
    --db .local_squadvault.sqlite \
    --league-id 70985 \
    --use-history-chain

Usage (manual range — probes each year on the same server):
  ./scripts/py -u src/squadvault/mfl/_run_historical_ingest.py \
    --db .local_squadvault.sqlite \
    --league-id 70985 \
    --start-year 2017 \
    --end-year 2023 \
    --expected-franchises 10

Usage (specific categories only):
  ./scripts/py -u src/squadvault/mfl/_run_historical_ingest.py \
    --db .local_squadvault.sqlite \
    --league-id 70985 \
    --use-history-chain \
    --categories FRANCHISE_INFO MATCHUP_RESULTS
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from squadvault.core.canonicalize.run_canonicalize import canonicalize
from squadvault.core.storage.session import DatabaseSession
from squadvault.core.storage.sqlite_store import SQLiteStore
from squadvault.mfl.discovery import discover_mfl_league, discover_mfl_league_via_history
from squadvault.mfl.historical_ingest import ingest_mfl_seasons


SCHEMA_PATH = Path("src/squadvault/core/storage/schema.sql")

ALL_CATEGORIES = [
    "FRANCHISE_INFO",
    "MATCHUP_RESULTS",
    "TRANSACTIONS",
    "FAAB_BIDS",
    "DRAFT_PICKS",
    "PLAYER_INFO",
    "PLAYER_SCORES",
    "NFL_BYE_WEEKS",
]


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for MFL historical ingestion."""
    ap = argparse.ArgumentParser(
        description=(
            "Discover and ingest historical MFL league data into SquadVault."
        )
    )
    ap.add_argument(
        "--db",
        default=os.environ.get("SQUADVAULT_DB", ".local_squadvault.sqlite"),
        help="Path to SQLite DB (default: .local_squadvault.sqlite)",
    )
    ap.add_argument(
        "--league-id",
        default=os.environ.get("MFL_LEAGUE_ID"),
        required="MFL_LEAGUE_ID" not in os.environ,
        help="MFL league identifier (e.g. 70985)",
    )
    ap.add_argument(
        "--start-year",
        type=int,
        default=2009,
        help="First year to discover/ingest (default: 2009)",
    )
    ap.add_argument(
        "--end-year",
        type=int,
        default=2024,
        help="Last year to discover/ingest (default: 2024)",
    )
    ap.add_argument(
        "--known-server",
        default=os.environ.get("MFL_SERVER", "www44.myfantasyleague.com"),
        help="Starting MFL server (default: www44.myfantasyleague.com)",
    )
    ap.add_argument(
        "--categories",
        nargs="+",
        choices=ALL_CATEGORIES,
        default=None,
        help="Specific categories to ingest (default: all)",
    )
    ap.add_argument(
        "--max-weeks",
        type=int,
        default=18,
        help="Max weeks per season for matchup results (default: 18)",
    )
    ap.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="Seconds between API calls (default: 1.5)",
    )
    ap.add_argument(
        "--skip-canonicalize",
        action="store_true",
        help="Skip canonicalization after ingestion",
    )
    ap.add_argument(
        "--discovery-only",
        action="store_true",
        help="Run discovery only, do not ingest",
    )
    ap.add_argument(
        "--use-history-chain",
        action="store_true",
        help="Use MFL's built-in history chain for discovery (recommended). "
        "Automatically resolves league IDs and servers for all prior seasons "
        "with a single API call. Ignores --start-year/--end-year.",
    )
    ap.add_argument(
        "--expected-franchises",
        type=int,
        default=None,
        help="Expected franchise count (flag mismatches as suspect, exclude from ingest)",
    )
    ap.add_argument(
        "--expected-name",
        default=None,
        help="Expected league name substring (flag mismatches as suspect)",
    )
    ap.add_argument(
        "--mfl-username",
        default=os.environ.get("MFL_USERNAME"),
        help="MFL username (optional, for private leagues)",
    )
    ap.add_argument(
        "--mfl-password",
        default=os.environ.get("MFL_PASSWORD"),
        help="MFL password (optional, for private leagues)",
    )
    args = ap.parse_args(argv)

    db_path = Path(args.db)
    league_id = str(args.league_id)

    print("=" * 70)
    print("  SquadVault MFL Historical Ingestion")
    print("=" * 70)
    print(f"  DB       : {db_path}")
    print(f"  League   : {league_id}")
    if args.use_history_chain:
        print("  Mode     : history-chain (automatic league ID resolution)")
    else:
        print(f"  Range    : {args.start_year}--{args.end_year}")
    print(f"  Server   : {args.known_server}")
    print(f"  Delay    : {args.delay}s")
    if args.categories:
        print(f"  Categories: {', '.join(args.categories)}")
    else:
        print("  Categories: ALL")
    print()

    # -- Phase 1: Discovery ------------------------------------------------

    print("Phase 1: Discovery")
    print("-" * 40)

    if args.use_history_chain:
        report = discover_mfl_league_via_history(
            league_id=league_id,
            known_server=args.known_server,
            current_year=args.end_year,
            request_delay_s=args.delay,
        )
    else:
        report = discover_mfl_league(
            league_id=league_id,
            start_year=args.start_year,
            end_year=args.end_year,
            known_server=args.known_server,
            request_delay_s=args.delay,
            expected_franchise_count=args.expected_franchises,
            expected_league_name=args.expected_name,
        )

    report.print_summary()

    if not report.seasons:
        print("No active seasons found. Nothing to ingest.")
        return 0

    if args.discovery_only:
        print("Discovery-only mode — skipping ingestion.")
        return 0

    # ── Ensure DB exists with schema ────────────────────────────────

    if not db_path.exists() or db_path.stat().st_size == 0:
        print(f"Initializing database: {db_path}")
        schema_sql = SCHEMA_PATH.read_text()
        store = SQLiteStore(db_path)
        store.init_db(schema_sql)
    else:
        print(f"Using existing database: {db_path}")

    # ── Phase 2: Ingestion ──────────────────────────────────────────

    print("\nPhase 2: Ingestion")
    print("-" * 40)

    results = ingest_mfl_seasons(
        league_id=league_id,
        discovery=report,
        db_path=str(db_path),
        categories=args.categories,
        max_weeks=args.max_weeks,
        request_delay_s=args.delay,
        username=args.mfl_username,
        password=args.mfl_password,
    )

    # ── Phase 3: Canonicalization (optional) ─────────────────────────

    if not args.skip_canonicalize:
        print("\nPhase 3: Canonicalization")
        print("-" * 40)

        for season_result in results:
            if season_result.total_inserted > 0:
                print(f"  Canonicalizing season {season_result.season}...")
                try:
                    canonicalize(
                        league_id=league_id,
                        season=season_result.season,
                        db_path=str(db_path),
                    )
                except TypeError:
                    # Backward-compatible call
                    canonicalize(
                        league_id=league_id,
                        season=season_result.season,
                    )
    else:
        print("\nSkipping canonicalization (--skip-canonicalize)")

    # ── Phase 4: Summary ─────────────────────────────────────────────

    print("\n" + "=" * 60)
    print("  Final Summary")
    print("=" * 60)

    with DatabaseSession(str(db_path)) as conn:
        total_memory = conn.execute(
            "SELECT COUNT(*) FROM memory_events WHERE league_id = ?",
            (league_id,),
        ).fetchone()[0]

        total_canonical = conn.execute(
            "SELECT COUNT(*) FROM canonical_events WHERE league_id = ?",
            (league_id,),
        ).fetchone()[0]

        seasons_in_db = conn.execute(
            "SELECT DISTINCT season FROM memory_events WHERE league_id = ? ORDER BY season",
            (league_id,),
        ).fetchall()

        event_types = conn.execute(
            """
            SELECT event_type, COUNT(*) AS n
            FROM canonical_events
            WHERE league_id = ?
            GROUP BY event_type
            ORDER BY n DESC
            """,
            (league_id,),
        ).fetchall()

        franchise_seasons = conn.execute(
            "SELECT COUNT(DISTINCT season) FROM franchise_directory WHERE league_id = ?",
            (league_id,),
        ).fetchone()[0]

        player_seasons = conn.execute(
            "SELECT COUNT(DISTINCT season) FROM player_directory WHERE league_id = ?",
            (league_id,),
        ).fetchone()[0]

    print(f"  memory_events  : {total_memory}")
    print(f"  canonical_events: {total_canonical}")
    print(f"  seasons in DB  : {[r[0] for r in seasons_in_db]}")
    print(f"  franchise_dir  : {franchise_seasons} seasons")
    print(f"  player_dir     : {player_seasons} seasons")
    print()
    print("  Canonical events by type:")
    for et, n in event_types:
        print(f"    {et:<45s} {n:>6d}")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
