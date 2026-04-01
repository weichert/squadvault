#!/usr/bin/env python3
"""
Repair 2025 WEEKLY_MATCHUP_RESULT occurred_at timestamps.

Root cause: matchup results were ingested before lock events were
canonicalized, so all 78 events got NULL occurred_at.  Lock events
now exist and window_for_week_index computes correctly.

This script:
  1. Reads the week number from each matchup event's payload
  2. Looks up the correct window_start for that week
  3. Updates occurred_at in both memory_events and canonical_events

Run:
  PYTHONPATH=src python scripts/repair_2025_matchup_timestamps.py

Dry-run (default) prints what would change.  Pass --apply to commit.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from squadvault.core.storage.session import DatabaseSession
from squadvault.core.recaps.selection.weekly_windows_v1 import window_for_week_index

DB_PATH = str(Path(".local_squadvault.sqlite"))
LEAGUE_ID = "70985"
SEASON = 2025
MAX_WEEKS = 18

APPLY = "--apply" in sys.argv


def main() -> None:
    # Step 1: Build week -> occurred_at mapping from lock windows
    print("=== Building week -> timestamp mapping ===")
    week_ts: dict[int, str] = {}
    for w in range(1, MAX_WEEKS + 1):
        win = window_for_week_index(DB_PATH, LEAGUE_ID, SEASON, w)
        if win.mode != "UNSAFE" and win.window_start:
            week_ts[w] = win.window_start
            print(f"  Week {w:2d}: {win.window_start}  ({win.mode})")
        else:
            print(f"  Week {w:2d}: UNAVAILABLE  ({win.mode}, reason={win.reason})")

    if not week_ts:
        print("\nERROR: No valid week timestamps found. Aborting.")
        return

    with DatabaseSession(DB_PATH) as conn:
        # Step 2: Find all 2025 matchup events with NULL occurred_at
        rows = conn.execute(
            """
            SELECT me.id AS memory_id, me.payload_json
            FROM memory_events me
            WHERE me.league_id = ?
              AND me.season = ?
              AND me.event_type = 'WEEKLY_MATCHUP_RESULT'
              AND me.occurred_at IS NULL
            """,
            (LEAGUE_ID, SEASON),
        ).fetchall()

        print(f"\n=== Found {len(rows)} matchup events with NULL occurred_at ===")

        updates: list[tuple[str, int]] = []  # (timestamp, memory_event_id)
        skipped = 0

        for row in rows:
            payload = json.loads(row["payload_json"])
            week = payload.get("week")
            if week is None:
                print(f"  WARNING: memory_event id={row['memory_id']} has no week in payload — skipping")
                skipped += 1
                continue

            week = int(week)
            ts = week_ts.get(week)
            if ts is None:
                print(f"  WARNING: No timestamp for week {week} (memory_event id={row['memory_id']}) — skipping")
                skipped += 1
                continue

            updates.append((ts, row["memory_id"]))

        print(f"\n=== Repair plan ===")
        print(f"  Events to update: {len(updates)}")
        print(f"  Skipped: {skipped}")

        # Show by-week breakdown
        from collections import Counter
        by_week: Counter[int] = Counter()
        for ts, _ in updates:
            for w, wts in week_ts.items():
                if wts == ts:
                    by_week[w] += 1
                    break
        for w in sorted(by_week):
            print(f"    Week {w:2d}: {by_week[w]} events -> {week_ts[w]}")

        if not APPLY:
            print("\n  DRY RUN — no changes made.  Pass --apply to commit.")
            return

        # Step 3: Apply updates to memory_events
        print("\n=== Applying updates to memory_events ===")
        mem_updated = 0
        for ts, mem_id in updates:
            conn.execute(
                "UPDATE memory_events SET occurred_at = ? WHERE id = ?",
                (ts, mem_id),
            )
            mem_updated += 1

        # Step 4: Apply updates to canonical_events (joined via best_memory_event_id)
        print("=== Applying updates to canonical_events ===")
        can_updated = 0
        for ts, mem_id in updates:
            result = conn.execute(
                """
                UPDATE canonical_events
                SET occurred_at = ?
                WHERE best_memory_event_id = ?
                  AND event_type = 'WEEKLY_MATCHUP_RESULT'
                  AND occurred_at IS NULL
                """,
                (ts, mem_id),
            )
            can_updated += result.rowcount

        conn.commit()

        print(f"\n=== Results ===")
        print(f"  memory_events updated: {mem_updated}")
        print(f"  canonical_events updated: {can_updated}")

        # Step 5: Verify
        remaining = conn.execute(
            """
            SELECT COUNT(*) as cnt
            FROM canonical_events
            WHERE league_id = ? AND season = ? AND event_type = 'WEEKLY_MATCHUP_RESULT'
              AND occurred_at IS NULL
            """,
            (LEAGUE_ID, SEASON),
        ).fetchone()
        print(f"  Remaining NULL occurred_at in canonical_events: {remaining['cnt']}")


if __name__ == "__main__":
    main()
