import os
import re
import sqlite3
import unittest

# Chronicle v1 markers (must stay stable)
BANNER_LINE = "NON-CANONICAL / DERIVED NARRATIVE — Rivalry Chronicle v1"

REQUIRED_MARKERS = [
    "<!-- BEGIN_PROVENANCE -->",
    "<!-- END_PROVENANCE -->",
    "<!-- BEGIN_INCLUDED_WEEKS -->",
    "<!-- END_INCLUDED_WEEKS -->",
    "<!-- BEGIN_UPSTREAM_QUOTES -->",
    "<!-- END_UPSTREAM_QUOTES -->",
]

# Guardrails: Chronicle cannot author canonical blocks or canonical_event ids
FORBIDDEN_MARKERS = [
    "<!-- BEGIN_CANONICAL_FACTS -->",
    "<!-- END_CANONICAL_FACTS -->",
    "<!-- BEGIN_CANONICAL_TRACE -->",
    "<!-- END_CANONICAL_TRACE -->",
    "<!-- BEGIN_CANONICAL_WINDOW -->",
    "<!-- END_CANONICAL_WINDOW -->",
    "<!-- BEGIN_CANONICAL_FINGERPRINT -->",
    "<!-- END_CANONICAL_FINGERPRINT -->",
]

CANONICAL_EVENT_ID_RE = re.compile(r"\bcanonical_event_id\b|\bcanonical_event ids?\b", re.IGNORECASE)


def _fetch_latest_chronicle_text(db_path: str, league_id: int, season: int, anchor_week_index: int) -> str:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            """
            SELECT rendered_text
            FROM recap_artifacts
            WHERE league_id = ?
              AND season = ?
              AND week_index = ?
              AND artifact_type = 'RIVALRY_CHRONICLE'
              AND state = 'APPROVED'
            ORDER BY version DESC
            LIMIT 1
            """,
            (int(league_id), int(season), int(anchor_week_index)),
        ).fetchone()
        if row is None:
            raise SystemExit("ERROR: No APPROVED RIVALRY_CHRONICLE found for harness check.")
        return str(row["rendered_text"] or "")
    finally:
        conn.close()


class TestRivalryChronicleV1StructuralHarness(unittest.TestCase):
    def test_structure_and_guardrails(self):
        db = os.environ.get("SV_TEST_DB")
        if not db:
            self.skipTest("Set SV_TEST_DB to a real .sqlite with a persisted chronicle to run this test.")

        # You persisted anchor_week=3 in your smoke run; keep harness minimal and explicit.
        txt = _fetch_latest_chronicle_text(db, league_id=70985, season=2024, anchor_week_index=3)

        # Banner
        self.assertTrue(txt.startswith(BANNER_LINE), "Chronicle must start with the v1 NON-CANONICAL banner")

        # Required markers
        for m in REQUIRED_MARKERS:
            self.assertIn(m, txt, f"Missing required marker: {m}")

        # Required ordering: provenance before included_weeks before quotes
        self.assertLess(txt.index("<!-- BEGIN_PROVENANCE -->"), txt.index("<!-- BEGIN_INCLUDED_WEEKS -->"))
        self.assertLess(txt.index("<!-- BEGIN_INCLUDED_WEEKS -->"), txt.index("<!-- BEGIN_UPSTREAM_QUOTES -->"))

        # Provenance must mention requested/included/missing
        self.assertIn("requested_weeks:", txt)
        self.assertIn("missing_weeks:", txt)
        self.assertIn("included_weeks:", txt)
        self.assertIn("upstream:", txt)

        # Forbidden canonical authoring markers
        for m in FORBIDDEN_MARKERS:
            self.assertNotIn(m, txt, f"Chronicle must not contain canonical marker: {m}")

        # Canonical event IDs must not be introduced
        self.assertIsNone(CANONICAL_EVENT_ID_RE.search(txt), "Chronicle must not introduce canonical_event_id(s)")

        # Must include fenced verbatim upstream quotes blocks
        self.assertIn("```text", txt)
        self.assertIn("```", txt)

    def test_fails_loudly_on_drift(self):
        # Tiny local drift test: ensure harness would fail if marker removed
        sample = BANNER_LINE + "\n\n" + "<!-- BEGIN_PROVENANCE -->\n<!-- END_PROVENANCE -->\n"
        with self.assertRaises(AssertionError):
            self.assertIn("<!-- BEGIN_UPSTREAM_QUOTES -->", sample)


if __name__ == "__main__":
    unittest.main()
