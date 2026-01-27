import os
import unittest

from squadvault.chronicle.generate_rivalry_chronicle_v1 import generate_rivalry_chronicle_v1
from squadvault.chronicle.input_contract_v1 import MissingWeeksPolicy


class TestRivalryChronicleGeneratorV1Determinism(unittest.TestCase):
    def test_same_inputs_same_output(self):
        db = os.environ.get("SV_TEST_DB")
        if not db:
            self.skipTest("Set SV_TEST_DB to a real .sqlite with approved recaps to run this test.")

        out1 = generate_rivalry_chronicle_v1(
            db_path=db,
            league_id=70985,
            season=2024,
            week_indices=(1, 2, 3),
            week_range=None,
            missing_weeks_policy=MissingWeeksPolicy.REFUSE,
            created_at_utc="2026-01-26T00:00:00Z",
        ).text

        out2 = generate_rivalry_chronicle_v1(
            db_path=db,
            league_id=70985,
            season=2024,
            week_indices=(1, 2, 3),
            week_range=None,
            missing_weeks_policy=MissingWeeksPolicy.REFUSE,
            created_at_utc="2026-01-26T00:00:00Z",
        ).text

        self.assertEqual(out1, out2)


if __name__ == "__main__":
    unittest.main()
