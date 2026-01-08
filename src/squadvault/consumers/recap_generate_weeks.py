import argparse
import hashlib
import json
import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from squadvault.core.storage.sqlite_store import SQLiteStore


# Keep codes identical to recap_generate.py
class VerdictStatus:
    WITHHELD = "WITHHELD"
    GENERATED = "GENERATED"


class DNGReason:
    DNG_INCOMPLETE_WEEK = "DNG_INCOMPLETE_WEEK"
    DNG_DATA_GAP_DETECTED = "DNG_DATA_GAP_DETECTED"


@dataclass(frozen=True)
class Verdict:
    status: str
    reason: Optional[str]
    evidence: Dict[str, Any]


def _ledger_count_in_range(
    conn: sqlite3.Connection,
    league_id: str,
    season: int,
    start: str,
    end: str,
) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM memory_events
        WHERE league_id = ?
          AND season = ?
          AND occurred_at >= ?
          AND occurred_at <= ?
        """,
        (league_id, season, start, end),
    ).fetchone()
    return int(row[0] or 0)


def generation_verdict(
    conn: sqlite3.Connection,
    league_id: str,
    season: int,
    start: str,
    end: str,
    canonical_events: List[Dict[str, Any]],
) -> Verdict:
    ledger = _ledger_count_in_range(conn, league_id, season, start, end)
    canonical = len(canonical_events)

    if ledger > canonical:
        return Verdict(
            status=VerdictStatus.WITHHELD,
            reason=DNGReason.DNG_DATA_GAP_DETECTED,
            evidence={
                "league_id": league_id,
                "season": season,
                "range_start": start,
                "range_end": end,
                "ledger_event_count": ledger,
                "canonical_event_count": canonical,
                "gap": ledger - canonical,
            },
        )

    if canonical == 0:
        return Verdict(
            status=VerdictStatus.WITHHELD,
            reason=DNGReason.DNG_INCOMPLETE_WEEK,
            evidence={
                "league_id": league_id,
                "season": season,
                "range_start": start,
                "range_end": end,
                "ledger_event_count": ledger,
                "canonical_event_count": 0,
            },
        )

    return Verdict(
        status=VerdictStatus.GENERATED,
        reason=None,
        evidence={
            "league_id": league_id,
            "season": season,
            "range_start": start,
            "range_end": end,
            "ledger_event_count": ledger,
            "canonical_event_count": canonical,
            "gap": 0,
        },
    )


def _inputs_hash(league_id: str, season: int, start: str, end: str) -> str:
    raw = json.dumps(
        {"league_id": league_id, "season": season, "start": start, "end": end},
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def ensure_verdict_table(conn: sqlite3.Connection, table: str) -> None:
    # Must match recap_generate.py schema
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            league_id TEXT NOT NULL,
            season INTEGER NOT NULL,
            range_start TEXT NOT NULL,
            range_end TEXT NOT NULL,
            status TEXT NOT NULL,
            reason TEXT,
            inputs_hash TEXT NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    conn.commit()


def persist_verdict(
    conn: sqlite3.Connection,
    table: str,
    league_id: str,
    season: int,
    start: str,
    end: str,
    payload: Dict[str, Any],
) -> None:
    ensure_verdict_table(conn, table)
    ih = _inputs_hash(league_id, season, start, end)

    conn.execute(
        f"""
        INSERT INTO {table} (
            created_at,
            league_id,
            season,
            range_start,
            range_end,
            status,
            reason,
            inputs_hash,
            payload_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now(timezone.utc).isoformat(),
            league_id,
            season,
            start,
            end,
            payload["status"],
            payload.get("reason"),
            ih,
            json.dumps(payload, sort_keys=True),
        ),
    )
    conn.commit()


def _parse_iso_z(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s).astimezone(timezone.utc)


def _iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def week_windows(start: str, end: str) -> List[Tuple[str, str]]:
    start_dt = _parse_iso_z(start)
    end_dt = _parse_iso_z(end)
    windows: List[Tuple[str, str]] = []

    cur = start_dt
    while cur < end_dt:
        nxt = cur + timedelta(days=7)
        win_end = min(nxt, end_dt)
        windows.append((_iso_z(cur), _iso_z(win_end)))
        cur = nxt

    return windows


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Batch recap gating by 7-day windows (Phase 2D)")
    p.add_argument("--db", required=True)
    p.add_argument("--league-id", required=True)
    p.add_argument("--season", type=int, required=True)
    p.add_argument("--season-start", required=True)
    p.add_argument("--season-end", required=True)
    p.add_argument("--persist-verdicts", action="store_true")
    p.add_argument("--verdict-table", default="recap_verdicts")

    args = p.parse_args(argv)

    store = SQLiteStore(args.db)
    conn = sqlite3.connect(args.db)

    rows: List[Dict[str, Any]] = []
    reason_counts = Counter()
    eligible = 0

    try:
        for (ws, we) in week_windows(args.season_start, args.season_end):
            canonical_events = store.fetch_events_in_range(
                league_id=str(args.league_id),
                season=int(args.season),
                occurred_at_min=ws,
                occurred_at_max=we,
            )

            v = generation_verdict(conn, str(args.league_id), int(args.season), ws, we, canonical_events)
            payload = {
                "status": v.status,
                "reason": v.reason,
                "evidence": v.evidence,
                "note": "BATCH GATING: verdict only; no recap generation.",
            }

            rows.append(payload)

            if v.status == VerdictStatus.GENERATED:
                eligible += 1
            else:
                reason_counts[v.reason or "UNKNOWN"] += 1

            if args.persist_verdicts:
                persist_verdict(
                    conn,
                    args.verdict_table,
                    str(args.league_id),
                    int(args.season),
                    ws,
                    we,
                    payload,
                )

    finally:
        conn.close()

    # Summary
    print("=== Batch Recap Gating Summary (Phase 2D) ===")
    print(f"Total windows : {len(rows)}")
    print(f"Eligible      : {eligible}")
    print(f"Withheld      : {len(rows) - eligible}")

    if reason_counts:
        print("\nWithheld by reason:")
        for k, v in reason_counts.most_common():
            print(f"- {k}: {v}")

    # Top gaps
    gaps = [r for r in rows if r["evidence"].get("gap", 0) > 0]
    gaps.sort(key=lambda r: r["evidence"]["gap"], reverse=True)
    if gaps:
        print("\nTop gaps:")
        for r in gaps[:10]:
            ev = r["evidence"]
            print(
                f"- {ev['range_start']} → {ev['range_end']} | gap={ev['gap']} "
                f"(ledger={ev.get('ledger_event_count')}, canonical={ev.get('canonical_event_count')})"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
