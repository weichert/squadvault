#!/usr/bin/env python3
# SV_CONTRACT_NAME: RIVALRY_CHRONICLE_OUTPUT
# SV_CONTRACT_DOC_PATH: docs/contracts/rivalry_chronicle_contract_output_v1.md


import argparse
import json
import sqlite3
import sys
from typing import Any, Dict


def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def fetch_approved_recap(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
) -> Dict[str, Any]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM recap_artifacts
        WHERE league_id = ?
          AND season = ?
          AND week_index = ?
          AND artifact_type = 'WEEKLY_RECAP'
          AND state = 'APPROVED'
        ORDER BY version DESC
        LIMIT 1
        """,
        (league_id, season, week_index),
    )
    row = cur.fetchone()
    conn.close()

    if row is None:
        raise RuntimeError(
            "No APPROVED recap artifact found. "
            "This fetcher refuses to return drafts or ready artifacts."
        )

    return row_to_dict(row)


def meta_view(a: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "league_id": a["league_id"],
        "season": a["season"],
        "week_index": a["week_index"],
        "artifact_type": a["artifact_type"],
        "version": a["version"],
        "state": a["state"],
        "approved_by": a["approved_by"],
        "approved_at": a["approved_at"],
        "window_start": a["window_start"],
        "window_end": a["window_end"],
        "selection_fingerprint": a["selection_fingerprint"],
        "supersedes_version": a["supersedes_version"],
        "withheld_reason": a["withheld_reason"],
    }


def main() -> None:
    p = argparse.ArgumentParser(
        description="Fetch APPROVED weekly recap artifact (read-only)"
    )
    p.add_argument("--db", required=True)
    p.add_argument("--league-id", required=True)
    p.add_argument("--season", type=int, required=True)
    p.add_argument("--week-index", type=int, required=True)

    out = p.add_mutually_exclusive_group()
    out.add_argument("--pretty", action="store_true", help="Pretty-print full JSON")
    out.add_argument("--text", action="store_true", help="Print only rendered_text")
    out.add_argument("--meta", action="store_true", help="Print only metadata JSON")

    args = p.parse_args()

    try:
        artifact = fetch_approved_recap(
            db_path=args.db,
            league_id=args.league_id,
            season=args.season,
            week_index=args.week_index,
        )
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if args.text:
        print(artifact["rendered_text"])
        return

    if args.meta:
        print(json.dumps(meta_view(artifact), indent=2, sort_keys=True))
        return

    if args.pretty:
        print(json.dumps(artifact, indent=2, sort_keys=True))
    else:
        print(json.dumps(artifact))


if __name__ == "__main__":
    main()
    