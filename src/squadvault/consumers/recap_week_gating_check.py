import argparse
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from squadvault.core.canonicalize.run_canonicalize import action_fingerprint, safe_json_loads
from squadvault.core.recaps.recap_runs import RecapRunRecord, upsert_recap_run
from squadvault.core.recaps.selection.weekly_selection_v1 import select_weekly_recap_events_v1
from squadvault.core.storage.sqlite_store import SQLiteStore
from squadvault.core.recaps.recap_runs import (
    RecapRunRecord,
    upsert_recap_run,
    get_recap_run_state,
    update_recap_run_state,
)

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


def _fetch_memory_rows_in_range(
    conn: sqlite3.Connection,
    league_id: str,
    season: int,
    start: str,
    end: str,
) -> List[Dict[str, Any]]:
    """
    Fetch minimal memory_events fields needed for action_fingerprint().
    """
    rows = conn.execute(
        """
        SELECT
          id,
          league_id,
          season,
          external_source,
          external_id,
          event_type,
          occurred_at,
          ingested_at,
          payload_json
        FROM memory_events
        WHERE league_id = ?
          AND season = ?
          AND occurred_at >= ?
          AND occurred_at < ?
        ORDER BY occurred_at, event_type, id
        """,
        (league_id, season, start, end),
    ).fetchall()

    out: List[Dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "id": int(r[0]),
                "league_id": str(r[1]),
                "season": int(r[2]),
                "external_source": str(r[3]),
                "external_id": str(r[4]),
                "event_type": str(r[5]),
                "occurred_at": str(r[6]) if r[6] is not None else None,
                "ingested_at": str(r[7]),
                "payload_json": str(r[8]),
            }
        )
    return out


def _ledger_unique_actions_in_range(
    conn: sqlite3.Connection,
    league_id: str,
    season: int,
    start: str,
    end: str,
) -> int:
    """
    Count unique logical actions in memory_events using the same action_fingerprint()
    logic as canonicalization. This prevents false "data gap" signals when multiple
    ledger rows represent the same underlying action.
    """
    rows = _fetch_memory_rows_in_range(conn, league_id, season, start, end)
    fps: Set[str] = set()

    # action_fingerprint expects a MemoryEventRow-like object. We'll use a tiny shim.
    class _RowShim:
        def __init__(self, d: Dict[str, Any]) -> None:
            self.id = d["id"]
            self.league_id = d["league_id"]
            self.season = d["season"]
            self.external_source = d["external_source"]
            self.external_id = d["external_id"]
            self.event_type = d["event_type"]
            self.occurred_at = d["occurred_at"]
            self.ingested_at = d["ingested_at"]
            self.payload_json = d["payload_json"]

    for d in rows:
        payload = safe_json_loads(d["payload_json"])
        fp = action_fingerprint(_RowShim(d), payload)

        # canonicalize.py skips empty fingerprints; do the same here
        if not fp:
            continue

        fps.add(fp)

    return len(fps)


def _canonical_count_in_range(
    store: SQLiteStore,
    league_id: str,
    season: int,
    start: str,
    end: str,
) -> int:
    canonical_events = store.fetch_events_in_range(
        league_id=str(league_id),
        season=int(season),
        occurred_at_min=start,
        occurred_at_max=end,
    )
    return len(canonical_events)


def generation_verdict_unique_actions(
    conn: sqlite3.Connection,
    store: SQLiteStore,
    league_id: str,
    season: int,
    start: str,
    end: str,
) -> Verdict:
    ledger_unique = _ledger_unique_actions_in_range(conn, league_id, season, start, end)
    canonical = _canonical_count_in_range(store, league_id, season, start, end)

    if ledger_unique > canonical:
        return Verdict(
            status=VerdictStatus.WITHHELD,
            reason=DNGReason.DNG_DATA_GAP_DETECTED,
            evidence={
                "league_id": league_id,
                "season": season,
                "range_start": start,
                "range_end": end,
                "ledger_unique_action_count": ledger_unique,
                "canonical_event_count": canonical,
                "gap": ledger_unique - canonical,
                "note": "gap is based on unique action_fingerprint() count, not raw ledger rows",
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
                "ledger_unique_action_count": ledger_unique,
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
            "ledger_unique_action_count": ledger_unique,
            "canonical_event_count": canonical,
            "gap": 0,
        },
    )

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Lock-to-lock gating check that can WITHHOLD a week (unique action-aware)."
    )
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week-index", type=int, required=True)
    args = ap.parse_args()

    sel = select_weekly_recap_events_v1(
        args.db, args.league_id, args.season, args.week_index
    )

    # 1) Unsafe window → WITHHELD immediately
    if sel.window.mode != "LOCK_TO_LOCK" or not sel.window.window_start or not sel.window.window_end:
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
                reason="unsafe_window_or_missing_lock",
            ),
        )
        print("gating_check: WITHHELD (unsafe_window_or_missing_lock)")
        return

    store = SQLiteStore(args.db)
    conn = sqlite3.connect(args.db)
    try:
        v = generation_verdict_unique_actions(
            conn,
            store,
            str(args.league_id),
            int(args.season),
            sel.window.window_start,
            sel.window.window_end,
        )
    finally:
        conn.close()

    # 2) Verdict says WITHHELD → persist and stop
    if v.status == VerdictStatus.WITHHELD:
        upsert_recap_run(
            args.db,
            RecapRunRecord(
                league_id=args.league_id,
                season=args.season,
                week_index=args.week_index,
                state="WITHHELD",
                window_mode="LOCK_TO_LOCK",
                window_start=sel.window.window_start,
                window_end=sel.window.window_end,
                selection_fingerprint=sel.fingerprint,
                canonical_ids=sel.canonical_ids,
                counts_by_type=sel.counts_by_type,
                reason=str(v.reason),
            ),
        )

        ev = v.evidence
        print(
            "gating_check: WITHHELD",
            v.reason,
            f"(ledger_unique={ev.get('ledger_unique_action_count')}, "
            f"canonical={ev.get('canonical_event_count')}, "
            f"gap={ev.get('gap', 0)})",
        )
        return

    # 3) Verdict is OK → clear stale WITHHELD so driver can proceed
    prior = get_recap_run_state(
        args.db, args.league_id, args.season, args.week_index
    )
    if prior == "WITHHELD":
        update_recap_run_state(
            args.db, args.league_id, args.season, args.week_index, "SUPERSEDED"
        )

    print("gating_check: OK (no gap detected; unique action-aware)")

if __name__ == "__main__":
    main()
