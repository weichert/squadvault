from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

from squadvault.utils.time import unix_seconds_to_iso_z


def _truncate_raw_json(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "...(truncated)"


def _stable_external_id(*parts: str) -> str:
    """Deterministic ID for dedupe."""
    raw = "|".join([p or "" for p in parts])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _safe_get(d: Dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in d:
            return d[k]
    return None


def _extract_type(txn: Dict[str, Any]) -> str:
    t = _safe_get(txn, "@type", "type")
    return str(t) if t is not None else ""


def _extract_franchise_id(txn: Dict[str, Any]) -> str:
    v = _safe_get(txn, "@franchise", "franchise", "@franchise_id", "franchise_id")
    return str(v) if v is not None else ""


def _extract_timestamp_unix(txn: Dict[str, Any]) -> Optional[int]:
    v = _safe_get(txn, "@timestamp", "timestamp", "@time", "time")
    if v is None:
        return None
    try:
        return int(str(v))
    except Exception:
        return None


def _parse_mfl_transaction_field(txn: Dict[str, Any]) -> Tuple[List[str], Optional[float], List[str]]:
    """
    Parses MFL's compact 'transaction' field.

    Observed patterns in your league:
      - BBID_WAIVER:  "<add_ids>|<bid>|<drop_ids>"
        example: "14108,|16.00|12676,"
      - FREE_AGENT:  "<add_ids>|<drop_ids>" (handled elsewhere)
        example: "16207,|14108,"

    Returns (added_ids, bid_amount, dropped_ids).
    """
    raw = _safe_get(txn, "transaction", "@transaction")
    if not isinstance(raw, str) or not raw:
        return ([], None, [])

    parts = raw.split("|")
    while len(parts) < 3:
        parts.append("")

    add_part = parts[0]
    bid_part = parts[1] if len(parts) >= 2 else ""
    drop_part = parts[2] if len(parts) >= 3 else ""

    def split_ids(s: str) -> List[str]:
        items = [x.strip() for x in s.split(",")]
        return [x for x in items if x]

    added = split_ids(add_part)
    dropped = split_ids(drop_part)

    bid_amount: Optional[float] = None
    if bid_part:
        try:
            bid_amount = float(bid_part)
        except Exception:
            bid_amount = None

    return (added, bid_amount, dropped)


def derive_waiver_bid_event_envelopes_from_transactions(
    *,
    year: int,
    league_id: str,
    transactions: List[Dict[str, Any]],
    source_url: str,
    raw_json_truncate_chars: int = 2000,
) -> List[Dict[str, Any]]:
    """
    Produces WAIVER_BID_* event envelopes from the MFL transactions export.

    In your league, waiver winners appear as:
      - type == BBID_WAIVER

    Some leagues also emit:
      - BBID_WAIVER_REQUEST

    Dedupe rule (IMPORTANT):
    - external_id is based on stable invariants:
      league_id + season + event_type + franchise_id + timestamp
    - it does NOT include parsed values like player_id or bid_amount, so improving parsing later
      will not inflate the ledger.

    IMPORTANT QUALITY GUARARD:
    - We do NOT emit WAIVER_BID_AWARDED/REQUEST if we cannot parse any semantics
      from the compact 'transaction' field. This prevents "stub awards" (blank player/bid/add/drop)
      from polluting the append-only ledger.
    """
    events: List[Dict[str, Any]] = []

    for idx, txn in enumerate(transactions):
        t = _extract_type(txn).upper().strip()
        if t not in ("BBID_WAIVER", "BBID_WAIVER_REQUEST"):
            continue

        ts_unix = _extract_timestamp_unix(txn)
        occurred_at = unix_seconds_to_iso_z(ts_unix) if ts_unix is not None else None

        franchise_id = _extract_franchise_id(txn)

        added_ids, bid_amount, dropped_ids = _parse_mfl_transaction_field(txn)

        # Prevent "stub" rows: if we can't parse any details, skip emitting an award/request event.
        if not added_ids and bid_amount is None and not dropped_ids:
            continue

        # If exactly one player added, treat that as the awarded player_id (most common case).
        player_id = added_ids[0] if len(added_ids) == 1 else ""

        raw_json = _truncate_raw_json(
            json.dumps(txn, separators=(",", ":"), sort_keys=True),
            raw_json_truncate_chars,
        )

        event_type = "WAIVER_BID_REQUEST" if t == "BBID_WAIVER_REQUEST" else "WAIVER_BID_AWARDED"

        # Stable timestamp key (never depends on parsing)
        ts_key = str(ts_unix) if ts_unix is not None else f"idx{idx}"

        external_id = _stable_external_id(
            league_id,
            str(year),
            event_type,
            franchise_id,
            ts_key,
        )

        payload: Dict[str, Any] = {
            "mfl_type": t,
            "franchise_id": franchise_id,
            "source_url": source_url,
            "raw_mfl_json": raw_json,
        }

        if player_id:
            payload["player_id"] = player_id
        if bid_amount is not None:
            payload["bid_amount"] = bid_amount

        # Store lists as comma-separated strings, and omit when empty.
        if added_ids:
            payload["players_added_ids"] = ",".join(added_ids)
        if dropped_ids:
            payload["players_dropped_ids"] = ",".join(dropped_ids)

        events.append(
            {
                "event_type": event_type,
                "occurred_at": occurred_at,
                "external_source": "MFL",
                "external_id": external_id,
                "league_id": league_id,
                "season": year,
                "payload": payload,
            }
        )

    return events


# -------------------------------------------------------------------
# Backwards-compat shim for Notion ingestion codepaths
# (transactions.py in this repo imports this symbol)
# -------------------------------------------------------------------
def derive_waiver_bids_from_transactions(*args, **kwargs):
    """
    Legacy/Notion-ingest shim.

    The SQLite-ledger pipeline uses:
      derive_waiver_bid_event_envelopes_from_transactions()

    This stub exists so older Notion ingestion modules can import successfully.
    """
    return []
