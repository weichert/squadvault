#!/usr/bin/env python3
"""Diagnose TRANSACTION_TRADE event structure in canonical events.

Answers the question: why does ``detect_trade_outcome`` (D4) fire zero
times when ``THE_ONE_THAT_GOT_AWAY`` (also D4, same module) fires
74-100+ times per season?

Hypothesis under test:
    ``_load_season_trades`` reads ``players_added_ids`` and
    ``players_dropped_ids`` from canonical trade event payloads, but
    those structured arrays are empty for TRANSACTION_TRADE events --
    the actual player IDs live in ``franchise1_gave_up`` and
    ``franchise2_gave_up`` inside ``raw_mfl_json``. If true, every
    trade row gets silently skipped at the loader before any pairing
    logic runs.

This script is read-only. It does not modify the database, generate
any LLM output, or touch any external API.

Usage::

    ./scripts/py -u scripts/diagnose_trade_events.py \\
        --db .local_squadvault.sqlite \\
        --league-id 70985 \\
        --season 2024 --season 2025

    # Show full payloads for the first N trades per season:
    ./scripts/py -u scripts/diagnose_trade_events.py \\
        --db .local_squadvault.sqlite \\
        --league-id 70985 \\
        --season 2025 --samples 2
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter

from squadvault.core.storage.session import DatabaseSession


def _parse_payload(raw: object) -> dict | None:
    """Parse a canonical payload_json column into a dict, or None on failure."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            obj = json.loads(raw)
        except (ValueError, TypeError):
            return None
        return obj if isinstance(obj, dict) else None
    return None


def _list_or_csv_count(val: object) -> int:
    """Count IDs in a value that may be a list, CSV string, or empty."""
    if isinstance(val, list):
        return sum(1 for x in val if str(x).strip())
    if isinstance(val, str) and val.strip():
        return sum(1 for x in val.split(",") if x.strip())
    return 0


def diagnose_season(
    *,
    db_path: str,
    league_id: str,
    season: int,
    sample_count: int,
) -> None:
    """Print a per-season diagnostic of TRANSACTION_TRADE event structure."""
    print(f"\n{'=' * 78}")
    print(f"  TRANSACTION_TRADE DIAGNOSTIC — Season {season}")
    print(f"{'=' * 78}")

    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """
            SELECT payload_json, occurred_at
              FROM v_canonical_best_events
             WHERE league_id = ? AND season = ?
               AND event_type = 'TRANSACTION_TRADE'
             ORDER BY occurred_at ASC NULLS LAST
            """,
            (str(league_id), int(season)),
        ).fetchall()

    total = len(rows)
    print(f"\n  Total TRANSACTION_TRADE rows: {total}")
    if total == 0:
        print("  (no trade events for this season)")
        return

    # Categorize each row by where its player IDs live.
    structured_only = 0       # populated players_added_ids/dropped_ids only
    raw_only = 0              # populated franchise1_gave_up/franchise2_gave_up only
    both_populated = 0        # both populated (consistent)
    neither_populated = 0     # neither populated (data anomaly)

    structured_ids_total = 0
    raw_ids_total = 0

    timestamp_groups: Counter[str] = Counter()
    sample_payloads: list[tuple[str, dict, dict]] = []  # (occurred_at, top, raw)

    for raw_row, occurred_at in rows:
        timestamp_groups[str(occurred_at or "")] += 1

        top = _parse_payload(raw_row) or {}
        added = top.get("players_added_ids", "")
        dropped = top.get("players_dropped_ids", "")
        n_structured = _list_or_csv_count(added) + _list_or_csv_count(dropped)

        raw_inner = top.get("raw_mfl_json", "")
        inner = _parse_payload(raw_inner) or {}
        f1_gave = inner.get("franchise1_gave_up", "")
        f2_gave = inner.get("franchise2_gave_up", "")
        n_raw = _list_or_csv_count(f1_gave) + _list_or_csv_count(f2_gave)

        structured_ids_total += n_structured
        raw_ids_total += n_raw

        if n_structured > 0 and n_raw > 0:
            both_populated += 1
        elif n_structured > 0:
            structured_only += 1
        elif n_raw > 0:
            raw_only += 1
        else:
            neither_populated += 1

        if len(sample_payloads) < sample_count:
            sample_payloads.append((str(occurred_at or ""), top, inner))

    # ── Player-ID source distribution ────────────────────────────────
    print("\n  Where do the player IDs live?")
    print(f"    {'Both populated (consistent)':<40s} {both_populated}")
    print(f"    {'Structured fields only':<40s} {structured_only}")
    print(f"    {'raw_mfl_json only (CURRENT BUG)':<40s} {raw_only}")
    print(f"    {'Neither populated (data anomaly)':<40s} {neither_populated}")
    print()
    print(f"    Total structured player IDs: {structured_ids_total}")
    print(f"    Total raw_mfl_json player IDs: {raw_ids_total}")

    # Loader simulation: how many rows would `_load_season_trades` keep?
    loader_kept = both_populated + structured_only
    loader_dropped = raw_only + neither_populated
    print()
    print("  What `_load_season_trades` sees today:")
    print(f"    Rows it would KEEP   (added or dropped non-empty): {loader_kept}")
    print(f"    Rows it would DROP   (both empty, hits `continue`): {loader_dropped}")

    # ── Timestamp pairing diagnostic ─────────────────────────────────
    # Even if the loader saw the rows, would the timestamp pairing produce
    # any pairs? Group sizes tell us.
    group_size_dist: Counter[int] = Counter()
    for _, count in timestamp_groups.items():
        group_size_dist[count] += 1

    print("\n  occurred_at group-size distribution (used by current pairing logic):")
    print(f"    {'group size':<12s} {'# of groups':<14s} {'# of rows'}")
    print(f"    {'─' * 12} {'─' * 14} {'─' * 12}")
    for size in sorted(group_size_dist.keys()):
        n_groups = group_size_dist[size]
        n_rows = size * n_groups
        marker = "  ← pairs" if size == 2 else ""
        print(f"    {size:<12d} {n_groups:<14d} {n_rows}{marker}")

    pairs_possible_today = 0
    for ts, cnt in timestamp_groups.items():
        if cnt == 2:
            pairs_possible_today += 1
    print()
    print(
        f"  Pairs the current logic could produce IF the loader kept the rows: "
        f"{pairs_possible_today}"
    )

    # ── Verdict ──────────────────────────────────────────────────────
    print()
    if total > 0 and loader_kept == 0 and raw_ids_total > 0:
        print("  VERDICT: Confirmed — every trade row is silently dropped at the")
        print("           loader because the structured player ID fields are empty.")
        print("           Player data exists in raw_mfl_json but is never extracted.")
    elif loader_kept > 0 and pairs_possible_today == 0:
        print("  VERDICT: Loader keeps rows but timestamp pairing produces 0 pairs.")
        print("           The bug is in the pairing strategy, not the loader.")
    elif loader_kept > 0 and pairs_possible_today > 0:
        print(f"  VERDICT: Loader keeps {loader_kept} rows and pairing would produce")
        print(f"           {pairs_possible_today} pairs. TRADE_OUTCOME silence has a different cause.")
    else:
        print("  VERDICT: Inconclusive — see counts above.")

    # ── Sample payloads ──────────────────────────────────────────────
    if sample_payloads:
        print(f"\n  Sample payloads (first {len(sample_payloads)}):")
        for i, (ts, top, inner) in enumerate(sample_payloads, start=1):
            print(f"\n  ── Sample {i} ── occurred_at={ts}")
            print("     Top-level (canonical fields):")
            for k in sorted(top.keys()):
                if k == "raw_mfl_json":
                    continue
                v = top[k]
                vs = repr(v)
                if len(vs) > 90:
                    vs = vs[:87] + "..."
                print(f"       {k}: {vs}")
            if inner:
                print("     raw_mfl_json (parsed):")
                for k in sorted(inner.keys()):
                    v = inner[k]
                    vs = repr(v)
                    if len(vs) > 90:
                        vs = vs[:87] + "..."
                    print(f"       {k}: {vs}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Diagnose TRANSACTION_TRADE event structure for D4 silence.",
    )
    ap.add_argument("--db", default=".local_squadvault.sqlite")
    ap.add_argument("--league-id", default="70985")
    ap.add_argument(
        "--season",
        type=int,
        action="append",
        required=True,
        help="Season to diagnose; pass multiple times to scan several seasons.",
    )
    ap.add_argument(
        "--samples",
        type=int,
        default=1,
        help="Show full payloads for the first N trades per season (default: 1).",
    )
    args = ap.parse_args()

    if not os.path.exists(args.db):
        print(f"ERROR: DB not found at {args.db}", file=sys.stderr)
        return 1

    for season in args.season:
        diagnose_season(
            db_path=args.db,
            league_id=args.league_id,
            season=season,
            sample_count=args.samples,
        )

    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
