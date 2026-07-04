"""CLI smoke test for the manual auction import ops tool (Unit A8, T4.1 end-to-end).

Exercises the governed founder-act path against a SCRATCH db seeded with a LOAD_ROSTERS anchor:
  - without --approve and with no recorded approval -> REFUSED (exit 3), nothing written.
  - with --approve -> the KP fixture lands as ATTESTED (external_source MANUAL:<tag>); an off-roster
    row is held absent by the section 6.4 anchor.
"""
from __future__ import annotations

import importlib.util
import json
import sqlite3
from pathlib import Path

REPO = Path(__file__).parent.parent
SCHEMA_PATH = REPO / "src" / "squadvault" / "core" / "storage" / "schema.sql"
CLI_PATH = REPO / "scripts" / "manual_import_auction_v1.py"


def _load_cli():
    spec = importlib.util.spec_from_file_location("manual_import_auction_v1", CLI_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def _scratch_with_seed(tmp_path):
    db = str(tmp_path / "scratch.sqlite")
    con = sqlite3.connect(db)
    con.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    # 2021 LOAD_ROSTERS anchor: franchise 0002 owns player 14136 (mirrors the real seed shape).
    payload = json.dumps({"franchise_id": "0002", "players_added_ids": ["14136", "13671"]})
    con.execute(
        "INSERT INTO memory_events (league_id, season, external_source, external_id, event_type, "
        "occurred_at, ingested_at, payload_json) VALUES (?,?,?,?,?,?,?,?)",
        ("70985", 2021, "MFL", "lr_0002", "TRANSACTION_LOAD_ROSTERS",
         "2021-08-01T00:00:00Z", "2021-08-01T00:00:00Z", payload),
    )
    con.commit()
    con.close()
    return db


def _fixtures(tmp_path):
    artifact = tmp_path / "kp_2021.xlsx"
    artifact.write_bytes(b"kp-2021-workbook-bytes")
    rows = tmp_path / "rows.json"
    rows.write_text(json.dumps([
        {"franchise_id": "0002", "player_id": "14136", "bid_amount": 50},   # on roster -> admitted
        {"franchise_id": "0002", "player_id": "99999", "bid_amount": 30},   # off roster -> held absent
    ]))
    return str(artifact), str(rows)


def _base_args(db, artifact, rows):
    return ["--db", db, "--league", "70985", "--season", "2021", "--tag", "KP-AUCTION-2021",
            "--artifact", artifact, "--rows", rows, "--actor", "founder"]


def _manual_count(db):
    con = sqlite3.connect(db)
    n = con.execute("SELECT COUNT(*) FROM memory_events WHERE external_source LIKE 'MANUAL:%'").fetchone()[0]
    con.close()
    return n


def test_refused_without_approval(tmp_path):
    cli = _load_cli()
    db = _scratch_with_seed(tmp_path)
    artifact, rows = _fixtures(tmp_path)
    rc = cli.main(_base_args(db, artifact, rows))  # no --approve
    assert rc == 3
    assert _manual_count(db) == 0  # nothing written (no silent ingestion)


def test_attested_entry_with_approval(tmp_path):
    cli = _load_cli()
    db = _scratch_with_seed(tmp_path)
    artifact, rows = _fixtures(tmp_path)
    rc = cli.main(_base_args(db, artifact, rows) + ["--approve"])
    assert rc == 0
    assert _manual_count(db) == 1  # the on-roster pick landed ATTESTED; off-roster held absent
    con = sqlite3.connect(db)
    src = con.execute(
        "SELECT external_source FROM memory_events WHERE external_source LIKE 'MANUAL:%'"
    ).fetchone()[0]
    con.close()
    assert src == "MANUAL:KP-AUCTION-2021"
