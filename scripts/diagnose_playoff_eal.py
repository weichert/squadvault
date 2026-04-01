#!/usr/bin/env python3
"""
Diagnose playoff EAL state for 2025 weeks 15-18.

Checks whether the timestamp repair resolved the EAL threshold issue
by examining included_count and the resulting directive for each
playoff week.

Run:
  PYTHONPATH=src python scripts/diagnose_playoff_eal.py
"""
from __future__ import annotations

import json
from pathlib import Path

from squadvault.core.eal.editorial_attunement_v1 import EALMeta, evaluate_editorial_attunement_v1
from squadvault.core.storage.session import DatabaseSession

DB_PATH = str(Path(".local_squadvault.sqlite"))
LEAGUE_ID = "70985"
SEASON = 2025


def main() -> None:
    print("=== 2025 Playoff EAL Diagnosis ===\n")

    with DatabaseSession(DB_PATH) as conn:
        for week in range(1, 19):
            row = conn.execute(
                """SELECT canonical_ids_json, editorial_attunement_v1,
                          window_mode, window_start, window_end,
                          counts_by_type_json
                   FROM recap_runs
                   WHERE league_id=? AND season=? AND week_index=?""",
                (LEAGUE_ID, SEASON, week),
            ).fetchone()

            if not row:
                print(f"  Week {week:2d}: NO RECAP RUN")
                continue

            # Parse included_count
            included_count = None
            ids_json = row["canonical_ids_json"]
            if ids_json:
                try:
                    ids = json.loads(ids_json)
                    if isinstance(ids, list):
                        included_count = len(ids)
                except (ValueError, TypeError):
                    pass

            # Parse counts by type
            counts_str = ""
            if row["counts_by_type_json"]:
                try:
                    counts = json.loads(row["counts_by_type_json"])
                    if isinstance(counts, dict):
                        counts_str = ", ".join(
                            f"{k}={v}" for k, v in sorted(counts.items())
                        )
                except (ValueError, TypeError):
                    pass

            # Compute what EAL would say now
            meta = EALMeta(
                has_selection_set=True,
                has_window=True,
                included_count=included_count,
            )
            directive = evaluate_editorial_attunement_v1(meta)

            stored_directive = row["editorial_attunement_v1"] or "(none)"
            window_mode = row["window_mode"] or "(none)"

            is_playoff = week >= 15
            marker = " *** PLAYOFF" if is_playoff else ""

            print(f"  Week {week:2d}: included={included_count or 0:4d}  "
                  f"stored_eal={stored_directive:<30s}  "
                  f"computed_eal={directive:<30s}  "
                  f"window={window_mode}{marker}")
            if is_playoff and counts_str:
                print(f"           types: {counts_str}")


if __name__ == "__main__":
    main()
