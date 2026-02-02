import argparse
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence

from squadvault.core.storage.sqlite_store import SQLiteStore


# =========================
# Verdict model (Phase 2C)
# =========================

class VerdictStatus(str, Enum):
    WITHHELD = "WITHHELD"
    GENERATED = "GENERATED"  # eligible; generation not implemented yet


class DNGReason(str, Enum):
    DNG_INCOMPLETE_WEEK = "DNG_INCOMPLETE_WEEK"
    DNG_DATA_GAP_DETECTED = "DNG_DATA_GAP_DETECTED"


@dataclass(frozen=True)
class GenerationVerdict:
    status: VerdictStatus
    reason_code: Optional[DNGReason] = None
    evidence: Optional[Dict[str, Any]] = None


# =========================
# Helpers
# =========================

def _ledger_count_in_range(
    conn: sqlite3.Connection,
    *,
    league_id: str,
    season: int,
    occurred_at_min: str,
    occurred_at_max: str,
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
        (league_id, season, occurred_at_min, occurred_at_max),
    ).fetchone()
    return int(row[0] or 0)


def _inputs_hash(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def recap_generation_verdict(
    *,
    conn: sqlite3.Connection,
    league_id: str,
    season: int,
    start: str,
    end: str,
    canonical_events: List[Dict[str, Any]],
) -> GenerationVerdict:
    """
    Phase 2C promotion rules (LOCKED):

    PR-01: ledger_count > canonical_count → WITHHELD (DATA_GAP)
    PR-02: canonical_count == 0 → WITHHELD (INCOMPLETE)
    Else → GENERATED (eligible only)
    """
    ledger_count = _ledger_count_in_range(
        conn,
        league_id=league_id,
        season=season,
        occurred_at_min=start,
        occurred_at_max=end,
    )
    canonical_count = len(canonical_events)

    if ledger_count > canonical_count:
        return GenerationVerdict(
            status=VerdictStatus.WITHHELD,
            reason_code=DNGReason.DNG_DATA_GAP_DETECTED,
            evidence={
                "league_id": league_id,
                "season": season,
                "range_start": start,
                "range_end": end,
                "ledger_event_count": ledger_count,
                "canonical_event_count": canonical_count,
                "gap": ledger_count - canonical_count,
            },
        )

    if canonical_count == 0:
        return GenerationVerdict(
            status=VerdictStatus.WITHHELD,
            reason_code=DNGReason.DNG_INCOMPLETE_WEEK,
            evidence={
                "league_id": league_id,
                "season": season,
                "range_start": start,
                "range_end": end,
                "ledger_event_count": ledger_count,
                "canonical_event_count": 0,
            },
        )

    return GenerationVerdict(
        status=VerdictStatus.GENERATED,
        evidence={
            "league_id": league_id,
            "season": season,
            "range_start": start,
            "range_end": end,
            "ledger_event_count": ledger_count,
            "canonical_event_count": canonical_count,
            "gap": 0,
        },
    )


# =========================
# Persistence (verdict only)
# =========================

def ensure_verdict_table(conn: sqlite3.Connection, table: str) -> None:
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
    *,
    conn: sqlite3.Connection,
    table: str,
    league_id: str,
    season: int,
    start: str,
    end: str,
    verdict_payload: Dict[str, Any],
) -> None:
    ensure_verdict_table(conn, table)

    inputs_hash = _inputs_hash(
        {
            "league_id": league_id,
            "season": season,
            "start": start,
            "end": end,
        }
    )

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
            verdict_payload["status"],
            verdict_payload.get("reason"),
            inputs_hash,
            json.dumps(verdict_payload, sort_keys=True),
        ),
    )
    conn.commit()


# =========================
# main
# =========================

def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Recap Generator (Phase 2C gated)")
    parser.add_argument("--db", required=True)
    parser.add_argument("--league-id", required=True)
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)

    parser.add_argument("--json", action="store_true")
    parser.add_argument("--persist-verdict", action="store_true")
    parser.add_argument("--verdict-table", default="recap_verdicts")

    args = parser.parse_args(argv)

    store = SQLiteStore(args.db)
    canonical_events = store.fetch_events_in_range(
        league_id=str(args.league_id),
        season=int(args.season),
        occurred_at_min=str(args.start),
        occurred_at_max=str(args.end),
    )

    conn = sqlite3.connect(args.db)
    try:
        verdict = recap_generation_verdict(
            conn=conn,
            league_id=str(args.league_id),
            season=int(args.season),
            start=str(args.start),
            end=str(args.end),
            canonical_events=canonical_events,
        )
    finally:
        conn.close()

    payload = {
        "status": verdict.status.value,
        "reason": verdict.reason_code.value if verdict.reason_code else None,
        "evidence": verdict.evidence or {},
        "note": "GENERATION STUB: eligible means gates passed; no recap content generated.",
    }

    if args.persist_verdict:
        conn = sqlite3.connect(args.db)
        try:
            persist_verdict(
                conn=conn,
                table=args.verdict_table,
                league_id=str(args.league_id),
                season=int(args.season),
                start=str(args.start),
                end=str(args.end),
                verdict_payload=payload,
            )
        finally:
            conn.close()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("=== Recap Generation Verdict ===")
        print(payload)

    return 0 if verdict.status == VerdictStatus.GENERATED else 2


if __name__ == "__main__":
    raise SystemExit(main())
