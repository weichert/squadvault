"""Generate recap artifacts for a range of weeks."""

import argparse
import hashlib
import json
import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from squadvault.core.storage.session import DatabaseSession
from squadvault.core.storage.sqlite_store import SQLiteStore
from squadvault.recaps.dng_reasons import DNGReason

# =========================
# Verdict model (Phase 2C)
# =========================

class VerdictStatus(str, Enum):
    WITHHELD = "WITHHELD"
    GENERATED = "GENERATED"  # eligible; generation not implemented yet


@dataclass(frozen=True)
class GenerationVerdict:
    status: VerdictStatus
    reason_code: DNGReason | None = None
    evidence: dict[str, Any] | None = None


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
    """Count memory events in a date range."""
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


def _inputs_hash(payload: dict[str, Any]) -> str:
    """Compute deterministic hash of generation inputs."""
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def recap_generation_verdict(
    *,
    conn: sqlite3.Connection,
    league_id: str,
    season: int,
    start: str,
    end: str,
    canonical_events: list[dict[str, Any]],
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
    """Verify verdict table exists.

    The recap_verdicts table is defined in schema.sql.
    Schema is the sole authority for table structure — no runtime
    DDL permitted (Phase 2: Eliminate Runtime Schema Mutation).
    """
    # No-op: table creation is handled by schema.sql and migrations.
    pass


def persist_verdict(
    *,
    conn: sqlite3.Connection,
    table: str,
    league_id: str,
    season: int,
    start: str,
    end: str,
    verdict_payload: dict[str, Any],
) -> None:
    """Persist a generation verdict to the database."""
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

def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint: generate recaps for a date range."""
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

    with DatabaseSession(args.db) as conn:
        verdict = recap_generation_verdict(
            conn=conn,
            league_id=str(args.league_id),
            season=int(args.season),
            start=str(args.start),
            end=str(args.end),
            canonical_events=canonical_events,
        )

    payload = {
        "status": verdict.status.value,
        "reason": verdict.reason_code.value if verdict.reason_code else None,
        "evidence": verdict.evidence or {},
        "note": "GENERATION STUB: eligible means gates passed; no recap content generated.",
    }

    if args.persist_verdict:
        with DatabaseSession(args.db) as conn:
            persist_verdict(
                conn=conn,
                table=args.verdict_table,
                league_id=str(args.league_id),
                season=int(args.season),
                start=str(args.start),
                end=str(args.end),
                verdict_payload=payload,
            )

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("=== Recap Generation Verdict ===")
        print(payload)

    return 0 if verdict.status == VerdictStatus.GENERATED else 2


if __name__ == "__main__":
    raise SystemExit(main())
