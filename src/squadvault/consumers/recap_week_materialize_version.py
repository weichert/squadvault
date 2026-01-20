from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Sequence


JSON_COL_CANDIDATES = (
    "recap_json",
    "recap_json_text",
    "recap_payload_json",
    "payload_json",
    "artifact_json",
    "artifact_json_text",
    "json",
    "data_json",
)

TABLE_CANDIDATES = ("recaps",)


def _die(msg: str, code: int = 2) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return code


def _recap_dir(base_dir: str, league_id: str, season: int, week_index: int) -> Path:
    return Path(base_dir) / "recaps" / str(league_id) / str(season) / f"week_{int(week_index):02d}"


def _recap_json_path(base_dir: str, league_id: str, season: int, week_index: int, version: int) -> Path:
    return _recap_dir(base_dir, league_id, season, week_index) / f"recap_v{int(version):02d}.json"


def _table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    rows = conn.execute(f"PRAGMA table_info({table});").fetchall()
    return [str(r[1]) for r in rows]  # (cid, name, type, notnull, dflt, pk)


def _choose_json_column(cols: Sequence[str]) -> Optional[str]:
    # Prefer known names
    for c in JSON_COL_CANDIDATES:
        if c in cols:
            return c
    # Heuristic fallback: any column containing 'json'
    for c in cols:
        if "json" in c.lower():
            return c
    return None


def _fetch_recap_json_from_db(
    conn: sqlite3.Connection,
    *,
    league_id: str,
    season: int,
    week_index: int,
    version: int,
) -> Dict[str, Any]:
    # Locate table + json column
    chosen_table = None
    chosen_col = None

    for t in TABLE_CANDIDATES:
        try:
            cols = _table_columns(conn, t)
        except sqlite3.OperationalError:
            continue
        jc = _choose_json_column(cols)
        if jc:
            chosen_table = t
            chosen_col = jc
            break

    if not chosen_table or not chosen_col:
        raise RuntimeError("Could not locate a recap JSON column in table 'recaps'. Run: sqlite3 DB \".schema recaps\"")

    # Try common key shapes: some schemas store as (league_id, season, week_index, version)
    # We build a query dynamically based on available columns.
    cols = _table_columns(conn, chosen_table)
    where = []
    params = []

    def add(col: str, val: Any) -> None:
        if col in cols:
            where.append(f"{col}=?")
            params.append(val)

    add("league_id", league_id)
    add("season", int(season))
    add("week_index", int(week_index))
    add("version", int(version))
    add("artifact_version", int(version))
    add("recap_version", int(version))

    if not where:
        raise RuntimeError(f"recaps table schema unexpected; cannot form WHERE clause (cols={cols})")

    sql = f"""
    SELECT {chosen_col}
    FROM {chosen_table}
    WHERE {" AND ".join(where)}
    LIMIT 1;
    """

    row = conn.execute(sql, tuple(params)).fetchone()
    if not row or row[0] is None:
        raise RuntimeError(
            f"No recap JSON found in {chosen_table} for league={league_id} season={season} week={week_index} version={version}"
        )

    raw = row[0]
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", errors="replace")

    return json.loads(raw)


def _run_script(py_path: str, args: list[str]) -> int:
    cmd = [sys.executable, "-u", py_path] + args
    return subprocess.call(cmd)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Materialize recap_vXX.json to disk from DB (recaps table)")
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week-index", type=int, required=True)
    ap.add_argument("--version", type=int, required=True)
    ap.add_argument("--base-dir", default="artifacts")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite recap_vXX.json if it exists.")
    ap.add_argument("--enrich", action="store_true", help="Also run recap_week_enrich_artifact.py after materialize.")
    args = ap.parse_args(argv)

    out_path = _recap_json_path(args.base_dir, args.league_id, args.season, args.week_index, args.version)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if out_path.exists() and not args.overwrite:
        print(f"materialize: SKIPPED (exists) {out_path}")
        return 0

    conn = sqlite3.connect(args.db)
    try:
        payload = _fetch_recap_json_from_db(
            conn,
            league_id=args.league_id,
            season=args.season,
            week_index=args.week_index,
            version=args.version,
        )
    finally:
        conn.close()

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"materialize: OK {out_path}")

    if args.enrich:
        py = "src/squadvault/consumers/recap_week_enrich_artifact.py"
        rc = _run_script(
            py,
            [
                "--db", args.db,
                "--league-id", args.league_id,
                "--season", str(args.season),
                "--week-index", str(args.week_index),
                "--version", str(args.version),
                "--base-dir", args.base_dir,
            ],
        )
        return rc

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
