#!/usr/bin/env python3
"""
recap_week_diagnose_empty.py

Goal:
Diagnose WHY a given week ends up with an empty (or unexpectedly small) weekly recap selection.

Given your current schema (canonical_events has no week_index), this script relies on:
- select_weekly_recap_events_v1(...) for the authoritative week window + selection outcome
- direct SQL counts over memory_events + canonical_events within that computed window

It answers:
1) Did we compute a safe lock-to-lock window?
2) Were there memory_events in that window?
3) Were there canonical_events in that window?
4) If canonical_events exist but selection is empty/small, is it likely allowlist filtering?

Outputs are deterministic and safe (no inference beyond explicit comparisons).
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from typing import Any, Dict, List, Optional, Tuple


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def _q(
    conn: sqlite3.Connection, sql: str, params: Tuple[Any, ...]
) -> List[Dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql, params)
    return [_row_to_dict(r) for r in cur.fetchall()]


def _q_one(
    conn: sqlite3.Connection, sql: str, params: Tuple[Any, ...]
) -> Optional[Dict[str, Any]]:
    rows = _q(conn, sql, params)
    return rows[0] if rows else None


def _print_kv(title: str, pairs: List[Tuple[str, Any]]) -> None:
    print(title)
    for k, v in pairs:
        print(f"  - {k}: {v}")
    print("")


def _fmt_counts(rows: List[Dict[str, Any]], key_col: str, val_col: str) -> str:
    if not rows:
        return "  (none)\n"
    lines = []
    for r in rows:
        lines.append(f"  - {str(r.get(key_col)):>28}: {r.get(val_col)}")
    return "\n".join(lines) + "\n"


def _try_load_allowlist() -> Optional[set[str]]:
    """
    Best-effort: if your repo has a canonical allowlist module, load it.
    (We keep this tolerant so the script works even if names move.)
    """
    candidates = [
        ("squadvault.config.recap_event_allowlist_v1", "ALLOWLIST_EVENT_TYPES"),
        ("squadvault.config.recap_event_allowlist_v1", "ALLOWED_EVENT_TYPES"),
        ("squadvault.config.recap_event_allowlist_v1", "ALLOWLIST"),
        ("squadvault.core.recaps.selection.weekly_selection_v1", "ALLOWLIST_EVENT_TYPES"),
        ("squadvault.core.recaps.selection.weekly_selection_v1", "ALLOWED_EVENT_TYPES"),
    ]
    for mod, attr in candidates:
        try:
            m = __import__(mod, fromlist=[attr])
            v = getattr(m, attr, None)
            if isinstance(v, (set, list, tuple)):
                return set(str(x) for x in v)
        except Exception:
            continue
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Diagnose empty or unexpectedly-small weekly recap selection.")
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week-index", type=int, required=True)
    ap.add_argument(
        "--sample",
        type=int,
        default=10,
        help="How many sample rows to print from memory_events/canonical_events (default: 10).",
    )
    args = ap.parse_args()

    # Authoritative selection+window
    from squadvault.core.recaps.selection.weekly_selection_v1 import select_weekly_recap_events_v1

    sel = select_weekly_recap_events_v1(
        db_path=args.db,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
    )

    # SelectionResult + Window objects are internal; access defensively.
    window = getattr(sel, "window", None)
    mode = getattr(window, "mode", None)
    win_start = getattr(window, "window_start", None) or getattr(window, "start", None)
    win_end = getattr(window, "window_end", None) or getattr(window, "end", None)

    reason = getattr(window, "reason", None)
    if mode != "LOCK_TO_LOCK":
        print(f"Window UNSAFE/Nonstandard reason: {reason}\n")

    canonical_ids = list(getattr(sel, "canonical_ids", []) or [])
    counts_by_type = dict(getattr(sel, "counts_by_type", {}) or {})
    fingerprint = getattr(sel, "fingerprint", None)

    _print_kv(
        "=== Selection (authoritative) ===",
        [
            ("league_id", args.league_id),
            ("season", args.season),
            ("week_index", args.week_index),
            ("window.mode", mode),
            ("window.start", win_start),
            ("window.end", win_end),
            ("selected_events", len(canonical_ids)),
            ("fingerprint", fingerprint),
        ],
    )

    if counts_by_type:
        print("Selected counts_by_type:")
        for k in sorted(counts_by_type.keys()):
            print(f"  - {k}: {counts_by_type[k]}")
        print("")
    else:
        print("Selected counts_by_type: (none)\n")

    # If no safe window, stop early with explicit reason.
    if mode != "LOCK_TO_LOCK" or not win_start or not win_end:
        print("DIAGNOSIS: Selection window is not LOCK_TO_LOCK or is missing bounds.")
        print("This is a hard stop in v1 selection (empty selection is expected).\n")
        return 0

    conn = sqlite3.connect(args.db)

    # Memory events in window
    mem_total = _q_one(
        conn,
        """
        SELECT COUNT(*) AS c
        FROM memory_events
        WHERE league_id = ?
          AND season = ?
          AND occurred_at >= ?
          AND occurred_at <  ?
        """,
        (args.league_id, args.season, win_start, win_end),
    ) or {"c": 0}

    mem_by_type = _q(
        conn,
        """
        SELECT event_type, COUNT(*) AS c
        FROM memory_events
        WHERE league_id = ?
          AND season = ?
          AND occurred_at >= ?
          AND occurred_at <  ?
        GROUP BY event_type
        ORDER BY c DESC, event_type
        """,
        (args.league_id, args.season, win_start, win_end),
    )

    mem_samples = _q(
        conn,
        """
        SELECT id, occurred_at, event_type, external_source, external_id
        FROM memory_events
        WHERE league_id = ?
          AND season = ?
          AND occurred_at >= ?
          AND occurred_at <  ?
        ORDER BY occurred_at, event_type, id
        LIMIT ?
        """,
        (args.league_id, args.season, win_start, win_end, int(args.sample)),
    )

    _print_kv(
        "=== Memory events in window ===",
        [
            ("total", mem_total.get("c", 0)),
            ("sample_limit", args.sample),
        ],
    )
    print("Memory events by type:")
    print(_fmt_counts(mem_by_type, "event_type", "c"), end="")
    if mem_samples:
        print("Memory event samples:")
        for r in mem_samples:
            print(
                f"  - id={r.get('id')}  at={r.get('occurred_at')}  type={r.get('event_type')}  "
                f"src={r.get('external_source')}  ext_id={r.get('external_id')}"
            )
        print("")
    else:
        print("Memory event samples: (none)\n")

    # Canonical events in window (by occurred_at)
    canon_total = _q_one(
        conn,
        """
        SELECT COUNT(*) AS c
        FROM canonical_events
        WHERE league_id = ?
          AND season = ?
          AND occurred_at >= ?
          AND occurred_at <  ?
        """,
        (args.league_id, args.season, win_start, win_end),
    ) or {"c": 0}

    canon_by_type = _q(
        conn,
        """
        SELECT event_type, COUNT(*) AS c
        FROM canonical_events
        WHERE league_id = ?
          AND season = ?
          AND occurred_at >= ?
          AND occurred_at <  ?
        GROUP BY event_type
        ORDER BY c DESC, event_type
        """,
        (args.league_id, args.season, win_start, win_end),
    )

    canon_samples = _q(
        conn,
        """
        SELECT id, occurred_at, event_type, best_memory_event_id, selection_version
        FROM canonical_events
        WHERE league_id = ?
          AND season = ?
          AND occurred_at >= ?
          AND occurred_at <  ?
        ORDER BY occurred_at, event_type, id
        LIMIT ?
        """,
        (args.league_id, args.season, win_start, win_end, int(args.sample)),
    )

    _print_kv(
        "=== Canonical events in window ===",
        [
            ("total", canon_total.get("c", 0)),
            ("sample_limit", args.sample),
        ],
    )
    print("Canonical events by type:")
    print(_fmt_counts(canon_by_type, "event_type", "c"), end="")
    if canon_samples:
        print("Canonical event samples:")
        for r in canon_samples:
            print(
                f"  - id={r.get('id')}  at={r.get('occurred_at')}  type={r.get('event_type')}  "
                f"best_mem={r.get('best_memory_event_id')}  sel_v={r.get('selection_version')}"
            )
        print("")
    else:
        print("Canonical event samples: (none)\n")

    # Allowlist comparison (best-effort)
    allowlist = _try_load_allowlist()
    if allowlist is not None:
        canon_types = {str(r.get("event_type")) for r in canon_by_type if r.get("event_type") is not None}
        disallowed = sorted(t for t in canon_types if t not in allowlist)
        allowed = sorted(t for t in canon_types if t in allowlist)

        print("=== Allowlist coverage (best-effort) ===")
        print(f"Allowlist size: {len(allowlist)}")
        print(f"Canonical types in window: {len(canon_types)}")
        print(f"Types allowed (present in window): {', '.join(allowed) if allowed else '(none)'}")
        print(f"Types NOT allowed (present in window): {', '.join(disallowed) if disallowed else '(none)'}")
        print("")
    else:
        print("=== Allowlist coverage ===")
        print("(Could not import allowlist symbol; skipping allowlist comparison.)\n")

    conn.close()

    # Final deterministic diagnosis summary
    mem_c = int(mem_total.get("c", 0) or 0)
    canon_c = int(canon_total.get("c", 0) or 0)
    sel_c = len(canonical_ids)

    print("=== Deterministic diagnosis summary ===")
    if mem_c == 0:
        print("Result: No memory_events occurred in the computed window. Quiet week is expected.")
    elif canon_c == 0:
        print("Result: memory_events exist, but canonical_events in the window are 0.")
        print("Likely cause: canonicalization did not produce canonical events for those memory events (or occurred_at is missing).")
    elif sel_c == 0:
        print("Result: canonical_events exist in the window, but selection returned 0.")
        print("Likely cause: selection filters/allowlist removed everything (or selection version gating).")
    else:
        print("Result: selection is non-empty. (Use this script to explain why a week is 'quiet' or not.)")

    print("")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
