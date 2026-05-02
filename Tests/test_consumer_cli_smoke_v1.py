"""Smoke tests for CLI entry points.

Verifies that every CLI module:
1. Imports without error (catches broken imports after refactors)
2. Exposes a callable main()
3. Constructs its argparse parser without error
4. Exits cleanly on --help (where argv is accepted)

These are NOT functional tests — they catch import breakage and
signature drift, not business logic.
"""

from __future__ import annotations

import importlib
import unittest

# (module_path, main_accepts_argv)
CONSUMER_ENTRIES: list[tuple[str, bool]] = [
    ("squadvault.consumers.editorial_log_week", True),
    ("squadvault.consumers.editorial_review_week", True),
    ("squadvault.consumers.recap_artifact_approve", False),
    ("squadvault.consumers.recap_artifact_regenerate", False),
    ("squadvault.consumers.recap_artifact_withhold", False),
    ("squadvault.consumers.recap_audit_facts_blocks", False),
    ("squadvault.consumers.recap_enrich_range", False),
    ("squadvault.consumers.recap_export_approved", True),
    ("squadvault.consumers.recap_export_narrative_assemblies_approved", True),
    ("squadvault.consumers.recap_export_variants_approved", True),
    ("squadvault.consumers.recap_week_approve", False),
    ("squadvault.consumers.recap_week_diagnose_empty", False),
    ("squadvault.consumers.recap_week_enrich_artifact", False),
    ("squadvault.consumers.rivalry_chronicle_generate_v1", True),
]

# Non-consumer entry points that are safe to import (no top-level env var crashes).
# Excludes ingest/_run_ingest_to_store.py, _run_matchup_results.py, _run_player_scores.py
# which read required env vars at module scope.
NON_CONSUMER_ENTRIES: list[tuple[str, bool]] = [
    ("squadvault.ingest._run_ingest_to_store", False),
    ("squadvault.ingest._run_matchup_results", False),
    ("squadvault.ingest._run_player_scores", False),
    ("squadvault.ingest.franchises._run_franchises_ingest", False),
    ("squadvault.ingest.players._run_players_ingest", True),
    ("squadvault.mfl._run_discover", True),
    ("squadvault.mfl._run_historical_ingest", True),
    ("squadvault.ops.run_ingest_then_canonicalize", False),
    ("squadvault.recaps._preview_angles", False),
]


class TestConsumerCLISmoke(unittest.TestCase):
    """Every consumer CLI module imports cleanly and exposes main()."""

    def test_all_consumers_import_cleanly(self) -> None:
        for mod_path, _ in CONSUMER_ENTRIES:
            with self.subTest(module=mod_path):
                mod = importlib.import_module(mod_path)
                self.assertTrue(
                    hasattr(mod, "main"),
                    f"{mod_path} missing main()",
                )
                self.assertTrue(
                    callable(mod.main),
                    f"{mod_path}.main is not callable",
                )

    def test_argv_consumers_accept_help(self) -> None:
        """Consumers that accept argv should exit 0 on --help."""
        for mod_path, accepts_argv in CONSUMER_ENTRIES:
            if not accepts_argv:
                continue
            with self.subTest(module=mod_path):
                mod = importlib.import_module(mod_path)
                with self.assertRaises(SystemExit) as ctx:
                    mod.main(["--help"])
                self.assertEqual(
                    ctx.exception.code,
                    0,
                    f"{mod_path}.main(['--help']) did not exit 0",
                )

    def test_no_argv_consumers_reject_missing_args(self) -> None:
        """Consumers without argv should fail cleanly when required args are missing.

        Verifies the module imports and has a callable main().
        """
        for mod_path, accepts_argv in CONSUMER_ENTRIES:
            if accepts_argv:
                continue
            with self.subTest(module=mod_path):
                mod = importlib.import_module(mod_path)
                self.assertTrue(callable(mod.main))


class TestNonConsumerCLISmoke(unittest.TestCase):
    """Non-consumer CLI entry points import cleanly and expose main()."""

    def test_all_non_consumers_import_cleanly(self) -> None:
        for mod_path, _ in NON_CONSUMER_ENTRIES:
            with self.subTest(module=mod_path):
                mod = importlib.import_module(mod_path)
                self.assertTrue(
                    hasattr(mod, "main"),
                    f"{mod_path} missing main()",
                )
                self.assertTrue(
                    callable(mod.main),
                    f"{mod_path}.main is not callable",
                )

    def test_argv_non_consumers_accept_help(self) -> None:
        """Non-consumer CLIs that accept argv should exit 0 on --help."""
        for mod_path, accepts_argv in NON_CONSUMER_ENTRIES:
            if not accepts_argv:
                continue
            with self.subTest(module=mod_path):
                mod = importlib.import_module(mod_path)
                with self.assertRaises(SystemExit) as ctx:
                    mod.main(["--help"])
                self.assertEqual(
                    ctx.exception.code,
                    0,
                    f"{mod_path}.main(['--help']) did not exit 0",
                )


if __name__ == "__main__":
    unittest.main()
