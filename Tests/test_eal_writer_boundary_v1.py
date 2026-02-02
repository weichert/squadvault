from __future__ import annotations
import os

import sqlite3
import unittest

from squadvault.recaps.weekly_recap_lifecycle import generate_weekly_recap_draft
from squadvault.recaps.weekly_recap_lifecycle import _get_recap_run_trace
from squadvault.recaps.weekly_recap_lifecycle import get_recap_run_state


def _try_insert_eal_directives(
    db_path: str,
    recap_run_id: str,
    directives_json: str,
) -> None:
    """
    Insert directives if the table exists.
    If the DB has no eal_directives_v1 table yet, treat as "no directives" (neutral).
    """
    con = sqlite3.connect(db_path)
    try:
        try:
            con.execute(
                """
                INSERT INTO eal_directives_v1 (
                    recap_run_id,
                    created_at_utc,
                    directives_json
                ) VALUES (?, '2026-01-01T00:00:00Z', ?)
                """,
                (recap_run_id, directives_json),
            )
            con.commit()
        except sqlite3.OperationalError:
            # Table missing → acceptable; neutral semantics
            return
    finally:
        con.close()


def _ensure_recap_runs_row(db_path: str, league_id: str, season: int, week_index: int) -> None:
    import sqlite3

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()

        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='recap_runs' LIMIT 1"
        )
        if cur.fetchone() is None:
            raise AssertionError("recap_runs table missing in test DB")

        cur.execute(
            "SELECT 1 FROM recap_runs WHERE league_id=? AND season=? AND week_index=? LIMIT 1",
            (league_id, season, week_index),
        )
        if cur.fetchone() is not None:
            return

        cur.execute("PRAGMA table_info(recap_runs)")
        cols = cur.fetchall()
        if not cols:
            raise AssertionError("PRAGMA table_info(recap_runs) returned no columns")

        by_name = {c[1]: c for c in cols}

        def has(name: str) -> bool:
            return name in by_name

        values = {}

        if has("league_id"):
            values["league_id"] = league_id
        if has("season"):
            values["season"] = int(season)
        if has("week_index"):
            values["week_index"] = int(week_index)

        if has("selection_fingerprint"):
            values["selection_fingerprint"] = "test-fingerprint"

        for nm in list(by_name.keys()):
            low = nm.lower()
            if "window" in low and "start" in low:
                values[nm] = int(week_index)
            if "window" in low and "end" in low:
                values[nm] = int(week_index)

        for _, name, typ, notnull, dflt, _pk in cols:
            if notnull != 1:
                continue
            if dflt is not None:
                continue
            if name in values:
                continue

            t = (typ or "").upper()
            lname = name.lower()

            if "INT" in t:
                values[name] = 0
            elif "REAL" in t or "FLOA" in t or "DOUB" in t:
                values[name] = 0.0
            else:
                if "time" in lname or "created_at" in lname or "updated_at" in lname:
                    values[name] = "1970-01-01T00:00:00Z"
                elif "id" == lname or lname.endswith("_id"):
                    values[name] = "test-id"
                else:
                    values[name] = ""

        if not values:
            raise AssertionError("could not derive any insert values for recap_runs")

        col_names = sorted(values.keys())
        placeholders = ",".join(["?"] * len(col_names))
        sql = f"INSERT INTO recap_runs ({','.join(col_names)}) VALUES ({placeholders})"
        cur.execute(sql, tuple(values[c] for c in col_names))
        conn.commit()
    finally:
        conn.close()


class TestEALWriterBoundaryV1(unittest.TestCase):
    def test_eal_writer_does_not_affect_selection_or_facts(self) -> None:
        db_path = os.environ.get("SQUADVAULT_TEST_DB", ".local_squadvault.sqlite")
        league_id = "70985"
        season = 2024
        week_index = 6

        _ensure_recap_runs_row(db_path, league_id, season, week_index)

        # --- Run 1: baseline ---
        generate_weekly_recap_draft(
            db_path=db_path,
            league_id=league_id,
            season=season,
            week_index=week_index,
            reason="eal-guardrail-baseline",
            force=True,
        )

        fp1, wstart1, wend1 = _get_recap_run_trace(db_path, league_id, season, week_index)

        # This is the same token weekly_recap_lifecycle uses for EAL lookup.
        state = get_recap_run_state(db_path, league_id, season, week_index)
        self.assertIsNotNone(state, "Expected recap run state token to exist")
        recap_run_id = str(state)

        # --- Inject directives (if supported by this DB) ---
        _try_insert_eal_directives(
            db_path=db_path,
            recap_run_id=recap_run_id,
            directives_json='{"tone_guard":"restrained","rivalry_heat_cap":1}',
        )

        # --- Run 2: with directives present (or neutral if table absent) ---
        generate_weekly_recap_draft(
            db_path=db_path,
            league_id=league_id,
            season=season,
            week_index=week_index,
            reason="eal-guardrail-with-directives",
            force=True,
        )

        fp2, wstart2, wend2 = _get_recap_run_trace(db_path, league_id, season, week_index)

        # --- Invariants: must not change under EAL ---
        self.assertEqual(fp1, fp2, "Selection fingerprint changed under EAL")
        self.assertEqual(wstart1, wstart2, "Window start changed under EAL")
        self.assertEqual(wend1, wend2, "Window end changed under EAL")
