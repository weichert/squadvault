#!/usr/bin/env python3
"""
Diagnose why 2025 WEEKLY_MATCHUP_RESULT events have NULL occurred_at.

Run:
  PYTHONPATH=src python scripts/diagnose_2025_timestamps.py
"""
from __future__ import annotations

from pathlib import Path
from squadvault.core.storage.session import DatabaseSession

DB_PATH = str(Path(".local_squadvault.sqlite"))
LEAGUE_ID = "70985"
SEASON = 2025


def main() -> None:
    with DatabaseSession(DB_PATH) as conn:

        # 1. Check if TRANSACTION_LOCK_ALL_PLAYERS events exist for 2025
        print("=== 1. LOCK events in canonical_events for 2025 ===")
        locks = conn.execute(
            """
            SELECT occurred_at, action_fingerprint
            FROM canonical_events
            WHERE league_id=? AND season=? AND event_type='TRANSACTION_LOCK_ALL_PLAYERS'
              AND occurred_at IS NOT NULL
            ORDER BY occurred_at
            """,
            (LEAGUE_ID, SEASON),
        ).fetchall()
        print(f"  Found {len(locks)} lock events with non-NULL occurred_at")
        for lk in locks:
            print(f"    {lk['occurred_at']}")

        # Also check for locks with NULL occurred_at
        null_locks = conn.execute(
            """
            SELECT COUNT(*) as cnt
            FROM canonical_events
            WHERE league_id=? AND season=? AND event_type='TRANSACTION_LOCK_ALL_PLAYERS'
              AND occurred_at IS NULL
            """,
            (LEAGUE_ID, SEASON),
        ).fetchone()
        print(f"  Lock events with NULL occurred_at: {null_locks['cnt']}")

        # 2. Check WEEKLY_MATCHUP_RESULT events for 2025
        print("\n=== 2. WEEKLY_MATCHUP_RESULT in canonical_events for 2025 ===")
        matchups = conn.execute(
            """
            SELECT ce.occurred_at, me.payload_json
            FROM canonical_events ce
            JOIN memory_events me ON me.id = ce.best_memory_event_id
            WHERE ce.league_id=? AND ce.season=? AND ce.event_type='WEEKLY_MATCHUP_RESULT'
            ORDER BY ce.id
            """,
            (LEAGUE_ID, SEASON),
        ).fetchall()

        null_count = sum(1 for m in matchups if m["occurred_at"] is None)
        nonnull_count = len(matchups) - null_count
        print(f"  Total: {len(matchups)}")
        print(f"  NULL occurred_at: {null_count}")
        print(f"  Non-NULL occurred_at: {nonnull_count}")

        # 3. Check if locks also exist in memory_events (pre-canonicalization)
        print("\n=== 3. LOCK events in memory_events for 2025 ===")
        mem_locks = conn.execute(
            """
            SELECT occurred_at
            FROM memory_events
            WHERE league_id=? AND season=? AND event_type='TRANSACTION_LOCK_ALL_PLAYERS'
            ORDER BY occurred_at
            """,
            (LEAGUE_ID, SEASON),
        ).fetchall()
        null_mem = sum(1 for m in mem_locks if m["occurred_at"] is None)
        print(f"  Total: {len(mem_locks)}")
        print(f"  With timestamps: {len(mem_locks) - null_mem}")
        print(f"  NULL occurred_at: {null_mem}")

        # 4. Check memory_events for matchup results
        print("\n=== 4. WEEKLY_MATCHUP_RESULT in memory_events for 2025 ===")
        mem_matchups = conn.execute(
            """
            SELECT id, occurred_at
            FROM memory_events
            WHERE league_id=? AND season=? AND event_type='WEEKLY_MATCHUP_RESULT'
            ORDER BY id
            """,
            (LEAGUE_ID, SEASON),
        ).fetchall()
        null_mem_m = sum(1 for m in mem_matchups if m["occurred_at"] is None)
        print(f"  Total: {len(mem_matchups)}")
        print(f"  NULL occurred_at: {null_mem_m}")
        print(f"  Non-NULL occurred_at: {len(mem_matchups) - null_mem_m}")

        # 5. Window computation test — what does window_for_week_index return now?
        print("\n=== 5. Window computation for 2025 (current state) ===")
        from squadvault.core.recaps.selection.weekly_windows_v1 import window_for_week_index
        for w in range(1, 19):
            win = window_for_week_index(DB_PATH, LEAGUE_ID, SEASON, w)
            ts = win.window_start or "(None)"
            print(f"  Week {w:2d}: mode={win.mode:<20s} window_start={ts}")


if __name__ == "__main__":
    main()
