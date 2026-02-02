#!/usr/bin/env python3
"""
recap_audit_facts_blocks.py

Audits whether "What happened (facts)" is present for each week’s latest WEEKLY_RECAP artifact,
and compares that to the deterministic selection size for that week.

Because canonical_events does NOT have week_index in this schema, we compute selected_events
by calling select_weekly_recap_events_v1(...) per week.

Outputs a compact per-week report + a summary.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


FACTS_HEADER = "What happened (facts)"


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def _fetch_latest_weekly_recap_artifact(
    conn: sqlite3.Connection,
    league_id: str,
    season: int,
    week_index: int,
) -> Optional[Dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT *
        FROM recap_artifacts
        WHERE league_id = ?
          AND season = ?
          AND week_index = ?
          AND artifact_type = 'WEEKLY_RECAP'
        ORDER BY version DESC
        LIMIT 1
        """,
        (league_id, season, week_index),
    )
    row = cur.fetchone()
    return None if row is None else _row_to_dict(row)


def _has_facts_block(rendered_text: str) -> bool:
    # Strong-ish: look in first ~40 lines to match enrich script semantics.
    prefix = "\n".join((rendered_text or "").splitlines()[:40])
    return FACTS_HEADER in prefix or prefix.startswith(FACTS_HEADER)


@dataclass(frozen=True)
class WeekAudit:
    week_index: int
    version: Optional[int]
    selected_events: int
    has_facts: bool
    expected_has_facts: bool
    status: str  # "OK", "MISMATCH", "NO_ARTIFACT"


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit facts blocks across a week range.")
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--start-week", type=int, required=True)
    ap.add_argument("--end-week", type=int, required=True)
    ap.add_argument(
        "--min-events-for-facts",
        type=int,
        default=None,
        help="Expected gating threshold. If omitted, uses deterministic_bullets_v1.QUIET_WEEK_MIN_EVENTS.",
    )
    ap.add_argument(
        "--show-only-mismatches",
        action="store_true",
        help="Only print weeks that mismatch expectation (or missing artifact).",
    )

    args = ap.parse_args()

    # Import here so PYTHONPATH=src works and we stay aligned with the live selection logic.
    from squadvault.core.recaps.selection.weekly_selection_v1 import select_weekly_recap_events_v1
    from squadvault.recaps.deterministic_bullets_v1 import QUIET_WEEK_MIN_EVENTS

    threshold = QUIET_WEEK_MIN_EVENTS if args.min_events_for_facts is None else int(args.min_events_for_facts)

    conn = sqlite3.connect(args.db)

    audits: List[WeekAudit] = []
    mismatch_count = 0
    no_artifact_count = 0

    for wk in range(args.start_week, args.end_week + 1):
        sel = select_weekly_recap_events_v1(
            db_path=args.db,
            league_id=args.league_id,
            season=args.season,
            week_index=wk,
        )
        selected_events = len(sel.canonical_ids)
        expected_has_facts = selected_events >= threshold

        art = _fetch_latest_weekly_recap_artifact(conn, args.league_id, args.season, wk)
        if art is None:
            status = "NO_ARTIFACT"
            audits.append(
                WeekAudit(
                    week_index=wk,
                    version=None,
                    selected_events=selected_events,
                    has_facts=False,
                    expected_has_facts=expected_has_facts,
                    status=status,
                )
            )
            no_artifact_count += 1
            continue

        version = int(art.get("version"))
        rendered_text = art.get("rendered_text") or ""
        has_facts = _has_facts_block(rendered_text)

        status = "OK" if has_facts == expected_has_facts else "MISMATCH"
        if status != "OK":
            mismatch_count += 1

        audits.append(
            WeekAudit(
                week_index=wk,
                version=version,
                selected_events=selected_events,
                has_facts=has_facts,
                expected_has_facts=expected_has_facts,
                status=status,
            )
        )

    conn.close()

    # Print
    def _maybe_print(a: WeekAudit) -> None:
        if args.show_only_mismatches and a.status == "OK":
            return
        v = "-" if a.version is None else str(a.version)
        print(
            f"wk={a.week_index:>2}  v={v:>2}  selected={a.selected_events:>3}  "
            f"has_facts={int(a.has_facts)}  expected={int(a.expected_has_facts)}  {a.status}"
        )

    for a in audits:
        _maybe_print(a)

    print("", file=sys.stderr)
    print(
        f"Audit complete: weeks {args.start_week}-{args.end_week} "
        f"| threshold={threshold} "
        f"| mismatches={mismatch_count} "
        f"| missing_artifacts={no_artifact_count}",
        file=sys.stderr,
    )

    # Non-zero exit on mismatch (useful for CI / scripts)
    return 2 if (mismatch_count > 0 or no_artifact_count > 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
