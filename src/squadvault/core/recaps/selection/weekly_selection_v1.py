from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence
import hashlib
import json
import sqlite3

from squadvault.core.recaps.selection.weekly_windows_v1 import RecapWindow, window_for_week_index


# Conservative v1 allowlist based on observed event_type values.
RECAP_EVENT_ALLOWLIST_V1: Sequence[str] = (
    "TRANSACTION_TRADE",
    "TRANSACTION_FREE_AGENT",
    "TRANSACTION_WAIVER",
    "TRANSACTION_BBID_WAIVER",
    "WAIVER_BID_AWARDED",
    "TRANSACTION_AUCTION_WON",
)


@dataclass(frozen=True)
class SelectionResult:
    week_index: int
    window: RecapWindow
    canonical_ids: List[int]               # ordered
    counts_by_type: Dict[str, int]
    fingerprint: str                       # sha256 of ordered canonical_ids

_SELECT_SQL_TEMPLATE = """
SELECT
  ce.id,
  ce.event_type,
  ce.action_fingerprint,
  ce.best_memory_event_id,
  me.occurred_at,
  me.payload_json
FROM canonical_events ce
JOIN memory_events me ON me.id = ce.best_memory_event_id
WHERE
  ce.league_id = ?
  AND ce.season = ?
  AND me.occurred_at >= ?
  AND me.occurred_at < ?
  AND ce.event_type IN (?,?,?,?,?,?)
ORDER BY
  me.occurred_at ASC,
  ce.event_type ASC,
  ce.id ASC;
"""

def _fingerprint_from_ids(ids: Sequence[int]) -> str:
    payload = ",".join(str(i) for i in ids).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

def select_weekly_recap_events_v1(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
) -> SelectionResult:
    """
    Deterministically selects recap-worthy canonical events for a given week_index
    using lock-to-lock windows and a conservative allowlist.

    - Window: [start_lock, next_lock)
    - Ordering: occurred_at, event_type, canonical_id
    - Fingerprint: sha256 of ordered canonical_ids
    """
    window = window_for_week_index(db_path, league_id, season, week_index)

    # Conservative v1: if we can't compute a safe window, return empty selection.
    if window.mode != "LOCK_TO_LOCK" or not window.window_start or not window.window_end:
        return SelectionResult(
            week_index=week_index,
            window=window,
            canonical_ids=[],
            counts_by_type={},
            fingerprint=_fingerprint_from_ids([]),
        )

    params = [
        league_id,
        season,
        window.window_start,
        window.window_end,
        *RECAP_EVENT_ALLOWLIST_V1,
    ]

    con = sqlite3.connect(db_path)
    try:
        cur = con.execute(_SELECT_SQL_TEMPLATE, params)
        rows = cur.fetchall()
    finally:
        con.close()

    canonical_ids: List[int] = []
    counts: Dict[str, int] = {}
    seen_trade_sig: Dict[str, int] = {}

    for canonical_id, event_type, _action_fp, _memory_id, _occurred_at, payload_json in rows:
        cid = int(canonical_id)
        et = str(event_type)
        keep = True

        # Deduplicate trades by hashing payload.raw_mfl_json (deterministic)
        if et == "TRANSACTION_TRADE":
            try:
                payload = json.loads(payload_json or "{}")
            except Exception:
                payload = {}

            raw = payload.get("raw_mfl_json") or ""
            sig = hashlib.sha256(str(raw).encode("utf-8")).hexdigest()

            prev = seen_trade_sig.get(sig)
            if prev is None:
                seen_trade_sig[sig] = cid
            else:
                # deterministic: lowest canonical_id wins
                if cid < prev:
                    seen_trade_sig[sig] = cid
                    try:
                        canonical_ids.remove(prev)
                        counts[et] = max(0, counts.get(et, 0) - 1)
                    except ValueError:
                        pass
                else:
                    keep = False

        if keep:
            canonical_ids.append(cid)
            counts[et] = counts.get(et, 0) + 1

    fp = _fingerprint_from_ids(canonical_ids)

    return SelectionResult(
        week_index=week_index,
        window=window,
        canonical_ids=canonical_ids,
        counts_by_type=counts,
        fingerprint=fp,
    )

