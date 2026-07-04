#!/usr/bin/env python3
"""Ops entry tool: governed manual auction import (Unit A8, Manual Source Adapter).

The explicit, auditable FOUNDER ACT that admits commissioner-attested auction facts into the
append-only ledger under COMMISSIONER_ATTESTED provenance (external_source="MANUAL:<tag>"). It
never modifies canonical data; it derives DRAFT_PICK envelopes per the ratified contract v1.0 and
appends them (idempotent). Attestation is per-import and explicit: without --approve, and without a
prior recorded approval, the import is REFUSED (no silent ingestion).

Defaults to whatever --db it is handed; the calibration/acceptance path runs against a SCRATCH db.
Production entry remains a separate founder act (run against the prod db, post KP-sheet confirmation).

Usage (scratch calibration):
  python scripts/manual_import_auction_v1.py \
      --db /tmp/scratch.sqlite --league 70985 --season 2021 \
      --tag KP-AUCTION-2021 --artifact /path/to/kp_workbook.xlsx \
      --rows rows.json --actor founder --approve

rows.json: a JSON list of {"franchise_id","player_id","bid_amount"} already extracted from and
reconciled against the retained workbook (structure-aware extraction + budget guard live upstream;
this tool enforces the identity/roster gates and the governance envelope).
"""
from __future__ import annotations

import argparse
import json
import sys

from squadvault.core.storage.sqlite_store import SQLiteStore
from squadvault.ingest.manual_auction import (
    AttestedAuctionRow,
    build_roster_seed_index,
    derive_manual_auction_envelopes,
    manual_external_source,
    sha256_file,
)
from squadvault.ingest.manual_import import (
    ApprovalRequiredError,
    import_manual_events,
    record_approval,
)


def _load_load_rosters(store: SQLiteStore, league_id: str, season: int) -> list[dict]:
    """Read the season's TRANSACTION_LOAD_ROSTERS rows (the adapter-grade integrity anchor seed)."""
    with store.connect() as conn:
        rows = conn.execute(
            """SELECT payload_json FROM memory_events
               WHERE league_id = ? AND season = ? AND event_type = 'TRANSACTION_LOAD_ROSTERS'""",
            (league_id, int(season)),
        ).fetchall()
    return [{"payload": json.loads(r["payload_json"])} for r in rows]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Governed manual auction import (Unit A8).")
    ap.add_argument("--db", required=True, help="SQLite db path (SCRATCH for calibration).")
    ap.add_argument("--league", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--tag", required=True, help="artifact tag, e.g. KP-AUCTION-2021")
    ap.add_argument("--artifact", required=True, help="path to the retained workbook (content-addressed)")
    ap.add_argument("--rows", required=True, help="JSON file: [{franchise_id, player_id, bid_amount}]")
    ap.add_argument("--actor", required=True, help="who is attesting (the founder act)")
    ap.add_argument("--approve", action="store_true", help="record the C3 approval as this founder act")
    ap.add_argument("--notes", default=None)
    args = ap.parse_args(argv)

    store = SQLiteStore(args.db)
    external_source = manual_external_source(args.tag)  # validates tag form (T4.3)
    sha = sha256_file(args.artifact)
    ref = f"cas/{sha}"

    with open(args.rows, encoding="utf-8") as fh:
        raw_rows = json.load(fh)
    rows = [
        AttestedAuctionRow(
            franchise_id=str(r["franchise_id"]),
            player_id=str(r["player_id"]),
            bid_amount=float(r["bid_amount"]),
        )
        for r in raw_rows
    ]

    seed = build_roster_seed_index(_load_load_rosters(store, args.league, args.season))
    if not seed:
        print(
            f"STOP: no LOAD_ROSTERS seed for {args.league}/{args.season}; the integrity anchor "
            f"cannot be waived (contract section 6.4). Ingest the roster seed first.",
            file=sys.stderr,
        )
        return 2

    envelopes, held = derive_manual_auction_envelopes(
        league_id=args.league, season=args.season, tag=args.tag, rows=rows,
        source_artifact_sha256=sha, source_artifact_ref=ref, roster_seed=seed,
    )

    if args.approve:
        record_approval(
            store, league_id=args.league, season=args.season, external_source=external_source,
            source_artifact_sha256=sha, actor=args.actor, notes=args.notes,
        )

    try:
        result = import_manual_events(
            store, league_id=args.league, season=args.season, external_source=external_source,
            source_artifact_sha256=sha, envelopes=envelopes,
        )
    except ApprovalRequiredError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 3

    print(f"provenance: {external_source}")
    print(f"artifact:   sha256={sha[:16]}... ref={ref}")
    print(f"admitted:   {result.inserted} inserted, {result.skipped} skipped (re-import no-op)")
    print(f"held absent (C4/anchor): {len(held)}")
    for h in held:
        print(f"  - {h.row.franchise_id}/{h.row.player_id}/${h.row.bid_amount:g}: {h.reason}")
    print(f"conflicts surfaced (canonical wins, unmutated): {len(result.conflicts)}")
    for c in result.conflicts:
        print(
            f"  - {c.franchise_id}/{c.player_id}: manual ${c.manual_bid:g} vs "
            f"canonical ${c.canonical_bid:g} [{c.canonical_external_source}]"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
