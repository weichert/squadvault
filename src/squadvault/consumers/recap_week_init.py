#!/usr/bin/env python3
"""
Initialize weekly recap (v1) deterministically.

Behavior:
- Computes deterministic weekly selection (canonical ids) from a safe weekly window.
- If the window is unsafe or missing bounds, WITHHOLD immediately.
- Otherwise, upserts recap_runs trace in DRAFTED state.
- Ensures recap v1 record exists (legacy integration).

Note:
- Empty selection (0 canonical ids) is valid: a quiet week can still produce a summary-only recap.
"""

from __future__ import annotations

import argparse
from typing import Optional

from squadvault.core.recaps.recap_runs import RecapRunRecord, upsert_recap_run
from squadvault.core.recaps.selection.weekly_selection_v1 import select_weekly_recap_events_v1

# Keep your existing import if this is correct in your codebase.
from squadvault.core.recaps.recap_store import insert_recap_v1_if_missing


SAFE_WINDOW_MODES = {"LOCK_TO_LOCK", "LOCK_TO_SEASON_END", "LOCK_PLUS_7D_CAP"}

# Deterministic fallback reason if window did not provide one.
WINDOW_UNSAFE_TO_COMPUTE = "WINDOW_UNSAFE_TO_COMPUTE"


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Initialize weekly recap (v1) deterministically.")
    p.add_argument("--db", required=True, help="Path to SQLite DB")
    p.add_argument("--league-id", required=True, help="League ID")
    p.add_argument("--season", required=True, type=int, help="Season year")
    p.add_argument("--week-index", required=True, type=int, help="Week index (module-defined)")
    p.add_argument(
        "--season-end",
        default=None,
        help="Optional ISO cap for final-week windowing, e.g. 2024-01-07T18:00:00Z",
    )
    return p


def _is_safe_window(mode: Optional[str], start: Optional[str], end: Optional[str]) -> bool:
    return (mode in SAFE_WINDOW_MODES) and bool(start) and bool(end)


def main() -> None:
    args = build_arg_parser().parse_args()

    # 1) Deterministic selection (+ optional season_end cap for the last week)
    sel = select_weekly_recap_events_v1(
        args.db,
        args.league_id,
        args.season,
        args.week_index,
    )

    # 2) HARD GATE: unsafe window => WITHHELD immediately
    if not _is_safe_window(sel.window.mode, sel.window.window_start, sel.window.window_end):
        # Persist a deterministic reason code for auditability.
        # Prefer the window's own reason code; fall back to a stable generic code.
        reason = getattr(sel.window, "reason", None) or WINDOW_UNSAFE_TO_COMPUTE

        upsert_recap_run(
            args.db,
            RecapRunRecord(
                league_id=args.league_id,
                season=args.season,
                week_index=args.week_index,
                state="WITHHELD",
                window_mode=getattr(sel.window, "mode", None),
                window_start=getattr(sel.window, "window_start", None),
                window_end=getattr(sel.window, "window_end", None),
                selection_fingerprint=sel.fingerprint,
                canonical_ids=sel.canonical_ids,
                counts_by_type=sel.counts_by_type,
                reason=reason,
            ),
        )
        print(f"recap_init: WITHHELD ({reason})")
        return

    # 3) Otherwise: record deterministic inputs and allow drafting (even if selection is empty)
    upsert_recap_run(
        args.db,
        RecapRunRecord(
            league_id=args.league_id,
            season=args.season,
            week_index=args.week_index,
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

    # 4) Initialize recap v1 record if missing (existing behavior)
    inserted = insert_recap_v1_if_missing(
        db_path=args.db,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
        selection_fingerprint=sel.fingerprint,
        window_start=sel.window.window_start,
        window_end=sel.window.window_end,
    )

    print("recap_init: INSERTED v1" if inserted else "recap_init: SKIPPED (already exists)")


if __name__ == "__main__":
    main()
