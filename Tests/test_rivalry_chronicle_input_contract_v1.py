import os
import sqlite3
import tempfile
import unittest

from squadvault.chronicle.approved_recap_refs_v1 import load_latest_approved_recap_refs_v1
from squadvault.chronicle.input_contract_v1 import (
    ChronicleInputResolverV1,
    MissingWeeksPolicy,
    RivalryChronicleInputV1,
)

ARTIFACT_TYPE = "WEEKLY_RECAP"


def _mk_db():
    fd, path = tempfile.mkstemp(prefix="sv_chronicle_contract_", suffix=".sqlite")
    os.close(fd)
    con = sqlite3.connect(path)
    try:
        con.execute(
            """
            CREATE TABLE recap_artifacts (
                league_id INTEGER NOT NULL,
                season INTEGER NOT NULL,
                week_index INTEGER NOT NULL,
                artifact_type TEXT NOT NULL,
                version INTEGER NOT NULL,
                state TEXT NOT NULL,
                selection_fingerprint TEXT NOT NULL
            )
            """
        )
        con.commit()
    finally:
        con.close()
    return path


def _insert(con, league_id, season, week, artifact_type, version, state, fp):
    con.execute(
        """
        INSERT INTO recap_artifacts
        (league_id, season, week_index, artifact_type, version, state, selection_fingerprint)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (league_id, season, week, artifact_type, version, state, fp),
    )


class TestRivalryChronicleInputContractV1(unittest.TestCase):
    def test_refuse_on_missing_approved_weeks(self):
        db = _mk_db()
        try:
            con = sqlite3.connect(db)
            try:
                _insert(con, 1, 2024, 1, ARTIFACT_TYPE, 1, "WITHHELD", "fp_w1_v1")
                _insert(con, 1, 2024, 2, ARTIFACT_TYPE, 1, "APPROVED", "fp_w2_v1")
                con.commit()
            finally:
                con.close()

            def loader(league_id, season, weeks):
                return load_latest_approved_recap_refs_v1(
                    db_path=db, league_id=league_id, season=season, artifact_type=ARTIFACT_TYPE, week_indices=weeks
                )

            resolver = ChronicleInputResolverV1(loader)
            inp = RivalryChronicleInputV1(league_id=1, season=2024, week_range=(1, 2))
            with self.assertRaises(ValueError):
                resolver.resolve(inp)
        finally:
            os.remove(db)

    def test_acknowledge_missing_approved_weeks(self):
        db = _mk_db()
        try:
            con = sqlite3.connect(db)
            try:
                _insert(con, 1, 2024, 1, ARTIFACT_TYPE, 1, "WITHHELD", "fp_w1_v1")
                _insert(con, 1, 2024, 2, ARTIFACT_TYPE, 1, "APPROVED", "fp_w2_v1")
                con.commit()
            finally:
                con.close()

            def loader(league_id, season, weeks):
                return load_latest_approved_recap_refs_v1(
                    db_path=db, league_id=league_id, season=season, artifact_type=ARTIFACT_TYPE, week_indices=weeks
                )

            resolver = ChronicleInputResolverV1(loader)
            inp = RivalryChronicleInputV1(
                league_id=1,
                season=2024,
                week_range=(1, 2),
                missing_weeks_policy=MissingWeeksPolicy.ACKNOWLEDGE_MISSING,
            )
            resolved = resolver.resolve(inp)
            self.assertEqual(resolved.week_indices, (1, 2))
            self.assertEqual(list(resolved.missing_weeks), [1])
            self.assertEqual(len(resolved.approved_recaps), 1)
            self.assertEqual(resolved.approved_recaps[0].week_index, 2)
            self.assertEqual(resolved.approved_recaps[0].version, 1)
            self.assertEqual(resolved.approved_recaps[0].selection_fingerprint, "fp_w2_v1")
        finally:
            os.remove(db)

    def test_latest_approved_version_is_selected(self):
        db = _mk_db()
        try:
            con = sqlite3.connect(db)
            try:
                _insert(con, 1, 2024, 2, ARTIFACT_TYPE, 1, "APPROVED", "fp_v1")
                _insert(con, 1, 2024, 2, ARTIFACT_TYPE, 2, "APPROVED", "fp_v2")
                con.commit()
            finally:
                con.close()

            refs = load_latest_approved_recap_refs_v1(
                db_path=db, league_id=1, season=2024, artifact_type=ARTIFACT_TYPE, week_indices=[2]
            )
            self.assertEqual(len(refs), 1)
            self.assertEqual(refs[0].version, 2)
            self.assertEqual(refs[0].selection_fingerprint, "fp_v2")
        finally:
            os.remove(db)


if __name__ == "__main__":
    unittest.main()
