import argparse
import json
import os
import sqlite3

from squadvault.core.recaps.facts.extract_recap_facts_v1 import extract_recap_facts_v1


def _get_active_artifact_path(db_path: str, league_id: str, season: int, week_index: int) -> str:
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            """
            SELECT artifact_path
            FROM recaps
            WHERE league_id=? AND season=? AND week_index=? AND status='ACTIVE'
            ORDER BY recap_version DESC
            LIMIT 1;
            """,
            (league_id, season, week_index),
        ).fetchone()
    finally:
        con.close()

    if not row or not row[0]:
        raise SystemExit("No ACTIVE recap with artifact_path found for that week.")
    return str(row[0])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week-index", type=int, required=True)
    args = ap.parse_args()

    path = _get_active_artifact_path(args.db, args.league_id, args.season, args.week_index)

    with open(path, "r", encoding="utf-8") as f:
        artifact = json.load(f)

    canonical_ids = artifact.get("selection", {}).get("canonical_ids", []) or []
    facts = extract_recap_facts_v1(args.db, args.league_id, args.season, list(canonical_ids))

    artifact["facts_version"] = 1
    artifact["facts_count"] = len(facts)
    artifact["facts"] = [
        {
            "canonical_id": x.canonical_id,
            "event_type": x.event_type,
            "occurred_at": x.occurred_at,
            "details": x.details,
        }
        for x in facts
    ]

    out_path = path.replace(".json", "_enriched.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2, sort_keys=True)
        f.write("\n")

    print("enriched_written:", out_path)
    print("facts_count:", len(facts))


if __name__ == "__main__":
    main()
