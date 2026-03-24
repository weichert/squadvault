#!/usr/bin/env python3
"""Apply: Fix season_end kwarg mismatch + safe window modes + batch reprocessor.

Three bugs fixed:
1. select_weekly_recap_events_v1 did not accept season_end kwarg
   → recap_week_gating_check.py and recap_week_selection_check.py crashed with TypeError
2. select_weekly_recap_events_v1 only accepted LOCK_TO_LOCK as a safe window mode
   → LOCK_TO_SEASON_END and LOCK_PLUS_7D_CAP windows were silently treated as unsafe
3. season_end was not forwarded to window_for_week_index
   → final-week windowing was impossible through the selection function

Deliverables:
  src/squadvault/core/recaps/selection/weekly_selection_v1.py  (patched)
  Tests/test_selection_season_end_forwarding.py                (new, 4 tests)
  scripts/reprocess_full_season.py                             (new, batch operator)

Usage:
  cd squadvault
  python3 apply_season_end_fix.py
  PYTHONPATH=src python -m pytest Tests/ -q
"""

import pathlib

ROOT = pathlib.Path(__file__).parent


# ─────────────────────────────────────────────────────────────────────
# 1. Patch weekly_selection_v1.py
# ─────────────────────────────────────────────────────────────────────

sel_path = ROOT / "src" / "squadvault" / "core" / "recaps" / "selection" / "weekly_selection_v1.py"
sel_path.write_text('''\
"""
weekly_selection_v1.py

Deterministically selects recap-worthy canonical events for a given week_index.

Contract:
- Computes a weekly window via weekly_windows_v1.window_for_week_index
- Selects canonical_events inside [window_start, window_end) AND event_type is allowlisted
- Orders deterministically: occurred_at, event_type, canonical_id
- Fingerprint: sha256 of ordered canonical_ids (as strings) joined by commas

Safety:
- If window is UNSAFE or missing boundaries, returns empty selection.
- No inference; selection is purely DB-driven + allowlist.
"""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from squadvault.core.recaps.selection.weekly_windows_v1 import WeeklyWindow, window_for_week_index
from squadvault.core.storage.session import DatabaseSession
from squadvault.core.storage.db_utils import row_to_dict as _row_to_dict


# -------------------------
# Allowlist (v1)
# -------------------------

def _load_allowlist_event_types() -> List[str]:
    """
    Pull allowlist from config if present. Provide a conservative fallback.
    """
    # Preferred location in this repo (based on earlier work)
    try:
        from squadvault.config.recap_event_allowlist_v1 import ALLOWLIST_EVENT_TYPES  # type: ignore
        if isinstance(ALLOWLIST_EVENT_TYPES, (list, tuple)) and ALLOWLIST_EVENT_TYPES:
            return [str(x) for x in ALLOWLIST_EVENT_TYPES]
    except (ImportError, AttributeError):
        pass

    # Conservative fallback (must match your current MVP coverage)
    return [
        "TRANSACTION_FREE_AGENT",
        "TRANSACTION_TRADE",
        "TRANSACTION_BBID_WAIVER",
        "WAIVER_BID_AWARDED",
        "WEEKLY_MATCHUP_RESULT",
        # NOTE: lock events exist but should not be recap bullets; keep them out by default.
        # "TRANSACTION_LOCK_ALL_PLAYERS",
        # "TRANSACTION_BBID_AUTO_PROCESS_WAIVERS",
        # "DRAFT_PICK",
    ]


# -------------------------
# Selection result
# -------------------------

@dataclass(frozen=True)
class SelectionResult:
    week_index: int
    window: WeeklyWindow
    canonical_ids: List[str]
    counts_by_type: Dict[str, int]
    fingerprint: str



# Safe window modes that produce a usable [start, end) boundary.
# Must stay in sync with recap_week_gating_check.SAFE_WINDOW_MODES.
_SAFE_WINDOW_MODES = {"LOCK_TO_LOCK", "LOCK_TO_SEASON_END", "LOCK_PLUS_7D_CAP"}


def _fingerprint_from_ids(ids: List[str]) -> str:
    # sha256 of comma-joined canonical ids
    """Compute SHA-256 fingerprint from sorted canonical IDs."""
    s = ",".join(ids).encode("utf-8")
    return hashlib.sha256(s).hexdigest()


# _db_connect removed — use DatabaseSession instead


def select_weekly_recap_events_v1(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    *,
    allowlist_event_types: Optional[List[str]] = None,
    season_end: Optional[str] = None,
) -> SelectionResult:
    """
    Deterministically select recap-worthy canonical event IDs for a week.

    Parameters
    ----------
    season_end : optional ISO-8601 UTC cap for final-week windowing.
        Forwarded to window_for_week_index for weeks where the next lock
        is absent (e.g., the last week of the season).
    """
    window = window_for_week_index(
        db_path, str(league_id), int(season), int(week_index),
        season_end=season_end,
    )

    # Conservative: refuse to select if we can't compute a safe window.
    if window.mode not in _SAFE_WINDOW_MODES or not window.window_start or not window.window_end:
        return SelectionResult(
            week_index=week_index,
            window=window,
            canonical_ids=[],
            counts_by_type={},
            fingerprint=_fingerprint_from_ids([]),
        )

    # Degenerate lock-to-lock (start == end) is treated as unsafe upstream; but double-guard anyway.
    if window.window_start == window.window_end:
        return SelectionResult(
            week_index=week_index,
            window=window,
            canonical_ids=[],
            counts_by_type={},
            fingerprint=_fingerprint_from_ids([]),
        )

    allow = allowlist_event_types if allowlist_event_types is not None else _load_allowlist_event_types()
    allow = [str(x) for x in allow if x]

    with DatabaseSession(db_path) as conn:
        cur = conn.cursor()

        # Allowlist filter (parameterized IN)
        # If allowlist is empty, return empty selection (most conservative)
        if not allow:
            return SelectionResult(
                week_index=week_index,
                window=window,
                canonical_ids=[],
                counts_by_type={},
                fingerprint=_fingerprint_from_ids([]),
            )

        placeholders = ",".join(["?"] * len(allow))

        cur.execute(
            f"""
            SELECT
                action_fingerprint AS canonical_id,
                occurred_at,
                event_type
            FROM canonical_events
            WHERE league_id = ?
              AND season = ?
              AND occurred_at IS NOT NULL
              AND occurred_at >= ?
              AND occurred_at <  ?
              AND event_type IN ({placeholders})
            ORDER BY occurred_at ASC, event_type ASC, action_fingerprint ASC
            """,
            [str(league_id), int(season), window.window_start, window.window_end, *allow],
        )

        rows = [_row_to_dict(r) for r in cur.fetchall()]

    canonical_ids: List[str] = [str(r["canonical_id"]) for r in rows]
    counts: Dict[str, int] = {}
    for r in rows:
        et = str(r.get("event_type") or "")
        counts[et] = counts.get(et, 0) + 1

    fp = _fingerprint_from_ids(canonical_ids)

    return SelectionResult(
        week_index=week_index,
        window=window,
        canonical_ids=canonical_ids,
        counts_by_type=counts,
        fingerprint=fp,
    )


__all__ = ["SelectionResult", "select_weekly_recap_events_v1"]
''')
print(f"✓ Wrote {sel_path.relative_to(ROOT)}")


# ─────────────────────────────────────────────────────────────────────
# 2. Create test file
# ─────────────────────────────────────────────────────────────────────

test_path = ROOT / "Tests" / "test_selection_season_end_forwarding.py"
test_path.write_text('''\
"""Test that select_weekly_recap_events_v1 forwards season_end to window_for_week_index.

This validates the fix for the kwarg mismatch that caused
recap_week_gating_check.py and recap_week_selection_check.py to crash.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from squadvault.core.recaps.selection.weekly_selection_v1 import (
    select_weekly_recap_events_v1,
)

SCHEMA_PATH = Path(__file__).parent.parent / "src" / "squadvault" / "core" / "storage" / "schema.sql"
LEAGUE = "test_league"
SEASON = 2024


@pytest.fixture
def db_with_two_locks(tmp_path):
    """DB with exactly two lock events — week 1 has a window, week 2 needs season_end."""
    db = str(tmp_path / "test.sqlite")
    con = sqlite3.connect(db)
    con.executescript(SCHEMA_PATH.read_text())

    locks = [
        ("2024-09-05T12:00:00Z", "lock_w1"),
        ("2024-09-12T12:00:00Z", "lock_w2"),
    ]
    for occurred_at, ext_id in locks:
        con.execute(
            """INSERT INTO memory_events
               (league_id, season, external_source, external_id, event_type, occurred_at, ingested_at, payload_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (LEAGUE, SEASON, "test", ext_id, "TRANSACTION_LOCK_ALL_PLAYERS",
             occurred_at, "2024-09-01T00:00:00Z", "{}"),
        )

    for i, (occurred_at, ext_id) in enumerate(locks, 1):
        me_id = con.execute("SELECT id FROM memory_events WHERE external_id=?", (ext_id,)).fetchone()[0]
        con.execute(
            """INSERT INTO canonical_events
               (league_id, season, event_type, action_fingerprint, best_memory_event_id,
                best_score, selection_version, updated_at, occurred_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (LEAGUE, SEASON, "TRANSACTION_LOCK_ALL_PLAYERS", ext_id, me_id,
             100, 1, "2024-09-01T00:00:00Z", occurred_at),
        )

    # Add a recap-eligible event between lock_w2 and the season_end cap
    con.execute(
        """INSERT INTO memory_events
           (league_id, season, external_source, external_id, event_type, occurred_at, ingested_at, payload_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (LEAGUE, SEASON, "test", "trade_after_lock2", "TRANSACTION_TRADE",
         "2024-09-15T08:00:00Z", "2024-09-01T00:00:00Z", "{}"),
    )
    me_id = con.execute("SELECT id FROM memory_events WHERE external_id=?", ("trade_after_lock2",)).fetchone()[0]
    con.execute(
        """INSERT INTO canonical_events
           (league_id, season, event_type, action_fingerprint, best_memory_event_id,
            best_score, selection_version, updated_at, occurred_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (LEAGUE, SEASON, "TRANSACTION_TRADE", "trade_after_lock2", me_id,
         100, 1, "2024-09-01T00:00:00Z", "2024-09-15T08:00:00Z"),
    )

    con.commit()
    con.close()
    return db


class TestSeasonEndForwarding:
    """select_weekly_recap_events_v1 must forward season_end to window_for_week_index."""

    def test_season_end_kwarg_accepted(self, db_with_two_locks):
        """Function accepts season_end without TypeError."""
        result = select_weekly_recap_events_v1(
            db_with_two_locks, LEAGUE, SEASON, 1,
            season_end="2024-09-19T12:00:00Z",
        )
        assert result is not None

    def test_week2_without_season_end_uses_7d_cap(self, db_with_two_locks):
        """Week 2 has no third lock — without season_end, falls back to LOCK_PLUS_7D_CAP."""
        result = select_weekly_recap_events_v1(
            db_with_two_locks, LEAGUE, SEASON, 2,
        )
        # LOCK_PLUS_7D_CAP is a safe mode, so the trade is found
        assert result.window.mode == "LOCK_PLUS_7D_CAP"
        assert len(result.canonical_ids) == 1

    def test_week2_with_season_end_returns_events(self, db_with_two_locks):
        """Week 2 with season_end cap should produce a valid window and find the trade event."""
        result = select_weekly_recap_events_v1(
            db_with_two_locks, LEAGUE, SEASON, 2,
            season_end="2024-09-19T12:00:00Z",
        )
        assert len(result.canonical_ids) == 1
        assert "trade_after_lock2" in result.canonical_ids
        assert result.window.mode == "LOCK_TO_SEASON_END"

    def test_season_end_combined_with_allowlist(self, db_with_two_locks):
        """season_end + allowlist_event_types both work together."""
        result = select_weekly_recap_events_v1(
            db_with_two_locks, LEAGUE, SEASON, 2,
            season_end="2024-09-19T12:00:00Z",
            allowlist_event_types=["TRANSACTION_TRADE"],
        )
        assert len(result.canonical_ids) == 1

        # With an allowlist that excludes TRANSACTION_TRADE
        result2 = select_weekly_recap_events_v1(
            db_with_two_locks, LEAGUE, SEASON, 2,
            season_end="2024-09-19T12:00:00Z",
            allowlist_event_types=["TRANSACTION_FREE_AGENT"],
        )
        assert result2.canonical_ids == []
''')
print(f"✓ Wrote {test_path.relative_to(ROOT)}")


# ─────────────────────────────────────────────────────────────────────
# 3. Create batch operator script
# ─────────────────────────────────────────────────────────────────────

batch_path = ROOT / "scripts" / "reprocess_full_season.py"
batch_path.write_text('''\
#!/usr/bin/env python3
"""Batch reprocess all weeks for a season: re-select + regenerate drafts.

Usage:
    ./scripts/py scripts/reprocess_full_season.py \\
        --db path/to/squadvault.sqlite \\
        --league-id 70985 \\
        --season 2024 \\
        --start-week 1 \\
        --end-week 18

This script:
1. For each week, runs select_weekly_recap_events_v1 (includes all allowlisted
   event types, including WEEKLY_MATCHUP_RESULT)
2. Upserts recap_runs with the new selection data
3. Regenerates draft artifacts via generate_weekly_recap_draft
4. Weeks with zero eligible events are marked WITHHELD

Dry-run by default. Add --execute to actually write changes.
"""
from __future__ import annotations

import argparse
import json
import sys

from squadvault.core.recaps.selection.weekly_selection_v1 import select_weekly_recap_events_v1
from squadvault.core.recaps.recap_runs import RecapRunRecord, upsert_recap_run, get_recap_run_state
from squadvault.recaps.weekly_recap_lifecycle import generate_weekly_recap_draft


_SAFE_MODES = {"LOCK_TO_LOCK", "LOCK_TO_SEASON_END", "LOCK_PLUS_7D_CAP"}


def main() -> int:
    ap = argparse.ArgumentParser(description="Batch reprocess full season recaps.")
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--start-week", type=int, required=True)
    ap.add_argument("--end-week", type=int, required=True)
    ap.add_argument("--season-end", default=None,
                    help="Optional ISO cap for final-week windowing")
    ap.add_argument("--execute", action="store_true",
                    help="Actually write changes (default is dry-run)")
    ap.add_argument("--skip-regen", action="store_true",
                    help="Only update selections, skip draft regeneration")
    args = ap.parse_args()

    mode = "EXECUTE" if args.execute else "DRY-RUN"
    print(f"=== Batch reprocess: {mode} ===")
    print(f"DB       : {args.db}")
    print(f"League   : {args.league_id}")
    print(f"Season   : {args.season}")
    print(f"Weeks    : {args.start_week}-{args.end_week}")
    if args.season_end:
        print(f"Season end: {args.season_end}")
    print()

    summary = {"drafted": [], "withheld": [], "errors": []}

    for w in range(args.start_week, args.end_week + 1):
        # 1. Re-select with full allowlist (includes WEEKLY_MATCHUP_RESULT)
        sel = select_weekly_recap_events_v1(
            args.db, args.league_id, args.season, w,
            season_end=args.season_end,
        )

        window_ok = (
            sel.window.mode in _SAFE_MODES
            and sel.window.window_start
            and sel.window.window_end
            and sel.window.window_start != sel.window.window_end
        )

        has_events = len(sel.canonical_ids) > 0

        if not window_ok or not has_events:
            reason = "no_safe_window" if not window_ok else "zero_eligible_events"
            print(f"  week {w:2d}: WITHHELD ({reason}) "
                  f"window={sel.window.mode} events={len(sel.canonical_ids)}")
            if args.execute:
                upsert_recap_run(
                    args.db,
                    RecapRunRecord(
                        league_id=args.league_id,
                        season=args.season,
                        week_index=w,
                        state="WITHHELD",
                        window_mode=sel.window.mode,
                        window_start=sel.window.window_start,
                        window_end=sel.window.window_end,
                        selection_fingerprint=sel.fingerprint,
                        canonical_ids=sel.canonical_ids,
                        counts_by_type=sel.counts_by_type,
                        reason=reason,
                    ),
                )
            summary["withheld"].append(w)
            continue

        # 2. Upsert recap_run with updated selection
        print(f"  week {w:2d}: DRAFT    events={len(sel.canonical_ids):3d} "
              f"types={sel.counts_by_type} fp={sel.fingerprint[:12]}...")
        if args.execute:
            upsert_recap_run(
                args.db,
                RecapRunRecord(
                    league_id=args.league_id,
                    season=args.season,
                    week_index=w,
                    state="DRAFTED",
                    window_mode=sel.window.mode,
                    window_start=sel.window.window_start,
                    window_end=sel.window.window_end,
                    selection_fingerprint=sel.fingerprint,
                    canonical_ids=sel.canonical_ids,
                    counts_by_type=sel.counts_by_type,
                    reason=None,
                ),
            )

        # 3. Regenerate draft
        if args.execute and not args.skip_regen:
            try:
                res = generate_weekly_recap_draft(
                    db_path=args.db,
                    league_id=args.league_id,
                    season=args.season,
                    week_index=w,
                    reason="batch_reprocess_with_matchup_results",
                    force=True,
                    created_by="batch_reprocess",
                )
                print(f"           regen OK: artifact_id={getattr(res, 'artifact_id', '?')}")
            except Exception as e:
                print(f"           regen ERROR: {e}")
                summary["errors"].append((w, str(e)))

        summary["drafted"].append(w)

    print()
    print(f"=== Summary ({mode}) ===")
    print(f"  Drafted : {len(summary['drafted'])} weeks {summary['drafted']}")
    print(f"  Withheld: {len(summary['withheld'])} weeks {summary['withheld']}")
    if summary["errors"]:
        print(f"  Errors  : {len(summary['errors'])}")
        for w, e in summary["errors"]:
            print(f"    week {w}: {e}")

    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
''')
batch_path.chmod(0o755)
print(f"✓ Wrote {batch_path.relative_to(ROOT)}")


print()
print("Apply complete. Verify:")
print("  PYTHONPATH=src python -m pytest Tests/ -q")
print()
print("Then process the full season against your real DB:")
print("  # Dry-run first:")
print("  ./scripts/py scripts/reprocess_full_season.py \\")
print("      --db path/to/squadvault.sqlite \\")
print("      --league-id 70985 --season 2024 \\")
print("      --start-week 1 --end-week 18")
print()
print("  # Then execute:")
print("  ./scripts/py scripts/reprocess_full_season.py \\")
print("      --db path/to/squadvault.sqlite \\")
print("      --league-id 70985 --season 2024 \\")
print("      --start-week 1 --end-week 18 --execute")
