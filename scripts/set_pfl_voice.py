#!/usr/bin/env python3
"""set_pfl_voice.py -- install the curated PFL Buddies voice as the live engine row.

Writes the module constant PFL_BUDDIES_VOICE_PROFILE into the engine's
league_voice_profiles table for the canonical PFL league (70985), so PFL
recaps render in the curated league voice instead of the graceful default
tone. This is the engine-side counterpart to sync_voice_from_supabase.py:
that bridge wires FOUNDED leagues' voices from the frontend founding session;
this wires the home league's hand-curated voice, which has no founding session.

Closes finding #2 of _observations/OBSERVATIONS_2026_06_05_VOICE_BRIDGE_SHIPPED.md:
PFL_BUDDIES_VOICE_PROFILE existed as a module constant with zero references and
was never written to league_voice_profiles by any standard path, so PFL recaps
ran on default tone.

GOVERNANCE PROPERTIES:
  - Single governed write to league_voice_profiles only. Touches no facts, no
    recap_artifacts, no approval or audit state. This is narrative-shaping
    configuration, never fact creation.
  - The operator running this IS the commissioner approving the profile; the
    row is stamped approved_by="commissioner".
  - approved_by="commissioner" (NOT "founding-session") is load-bearing: it
    keeps the Supabase bridge's non-clobber guard (D5a) and engine-authoritative
    guard (D7b) correct, so the bridge continues to refuse to overwrite this row.
  - Non-clobber by default: if a voice row already exists for the league and its
    text differs from the curated constant, the script refuses unless --force.
  - Idempotent: re-running when the row already matches is a clean no-op (exit 0).
  - --dry-run reports the planned action and writes nothing.

PRECONDITION: the target DB must be a built engine DB that carries the
league_voice_profiles table. The script prechecks this and fails clearly
(exit 5) rather than relying on get_voice_profile -- which intentionally
swallows OperationalError so recap generation degrades to default tone -- so
a missing table cannot masquerade as "no row yet" in --dry-run.

EXIT CODES:
  0  installed, replaced, already-current, or dry-run reported
  2  DB file not found
  3  existing differing row, refused (use --force)
  4  post-write verification failed
  5  DB has no league_voice_profiles table (not built/migrated)

USAGE:
  ./scripts/py scripts/set_pfl_voice.py --dry-run
  ./scripts/py scripts/set_pfl_voice.py
  ./scripts/py scripts/set_pfl_voice.py --force          # replace a differing row
  ./scripts/py scripts/set_pfl_voice.py --db /path/db.sqlite --league-id 70985
"""
from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
from pathlib import Path

from squadvault.core.tone.voice_profile_v1 import (
    PFL_BUDDIES_VOICE_PROFILE,
    get_voice_profile,
    set_voice_profile,
)

logger = logging.getLogger("set_pfl_voice")

DEFAULT_ENGINE_DB = Path(".local_squadvault.sqlite")
DEFAULT_LEAGUE_ID = "70985"
APPROVED_BY = "commissioner"
VOICE_TABLE = "league_voice_profiles"


def _table_exists(db_path: str, table: str) -> bool:
    """Return True if the named table exists in the SQLite DB."""
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        return row is not None
    finally:
        con.close()


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Install the curated PFL Buddies voice as the live engine voice row."
        ),
    )
    parser.add_argument(
        "--db",
        default=str(DEFAULT_ENGINE_DB),
        help=f"Path to the engine SQLite DB (default: {DEFAULT_ENGINE_DB}).",
    )
    parser.add_argument(
        "--league-id",
        default=DEFAULT_LEAGUE_ID,
        help=f"Canonical league id (default: {DEFAULT_LEAGUE_ID}).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing voice row whose text differs from the constant.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report the planned action without writing.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = _parse_args(argv)

    db_path = args.db
    league_id = args.league_id
    desired = PFL_BUDDIES_VOICE_PROFILE.strip()

    if not Path(db_path).exists():
        logger.error("ERROR: engine DB not found: %s", db_path)
        logger.error("       Build or refresh the engine DB first, or pass --db.")
        return 2

    # Precondition: the DB must carry the voice table. get_voice_profile swallows
    # OperationalError (intentional: recaps degrade to default tone rather than
    # crash), so without this check a missing table would read as "no row yet"
    # and --dry-run would falsely report "would INSTALL".
    if not _table_exists(db_path, VOICE_TABLE):
        logger.error("ERROR: %s has no %s table.", db_path, VOICE_TABLE)
        logger.error("       The DB is not built/migrated. Build the engine DB")
        logger.error("       (ingest) or apply migrations before setting a voice.")
        return 5

    current = get_voice_profile(db_path, league_id)

    # Already current: clean no-op (idempotent).
    if current is not None and current == desired:
        logger.info(
            "Already current: %s carries the curated voice (%d chars). No-op.",
            league_id,
            len(desired),
        )
        return 0

    # Existing but differing row: refuse without --force.
    if current is not None and not args.force:
        if args.dry_run:
            logger.info(
                "[dry-run] existing voice row for %s differs (%d chars); "
                "would REFUSE without --force.",
                league_id,
                len(current),
            )
            return 0
        logger.error(
            "REFUSING to overwrite existing voice row for %s (%d chars).",
            league_id,
            len(current),
        )
        logger.error("       An existing profile differs from the curated constant.")
        logger.error("       Re-run with --force to replace it.")
        return 3

    action = "REPLACE" if current is not None else "INSTALL"

    if args.dry_run:
        logger.info(
            "[dry-run] would %s curated voice for %s (%d chars), approved_by=%s.",
            action,
            league_id,
            len(desired),
            APPROVED_BY,
        )
        return 0

    set_voice_profile(db_path, league_id, desired, approved_by=APPROVED_BY)

    verify = get_voice_profile(db_path, league_id)
    if verify != desired:
        logger.error("ERROR: post-write verification failed for %s.", league_id)
        return 4

    logger.info(
        "OK: %s curated voice for %s (%d chars), approved_by=%s.",
        action,
        league_id,
        len(desired),
        APPROVED_BY,
    )
    logger.info("    PFL recaps will now render in the curated league voice.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
