from __future__ import annotations

import json
import hashlib
import logging
from typing import Any, Dict, List, Optional, Tuple

from squadvault.utils.time import unix_seconds_to_iso_z

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _safe_get(d: Dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in d:
            return d[k]
    return None


def _stable_external_id(*parts: str) -> str:
    raw = "|".join([p or "" for p in parts])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _truncate_raw_json(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "...(truncated)"


def _extract_type(txn: Dict[str, Any]) -> str:
    return str(_safe_get(txn, "@type", "type") or "").upper().strip()


def _extract_franchise_id(txn: Dict[str, Any]) -> str:
    return str(_safe_get(txn, "@franchise", "franchise") or "")


def _extract_timestamp_unix(txn: Dict[str, Any]) -> Optional[int]:
    v = _safe_get(txn, "@timestamp", "timestamp")
    try:
        return int(v) if v is not None else None
    except Exception:
        return None


def _extract_bid_amount(txn: Dict[str, Any]) -> Optional[float]:
    for k in ("@bid", "bid", "@amount", "amount", "@bbid", "bbid"):
        v = txn.get(k)
        if v is None:
            continue
        try:
            return float(v)
        except Exception:
            pass
    return None


def _parse_mfl_transaction_field(txn: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """
    Parses compact MFL transaction strings.

    Examples:
      FREE_AGENT: "16207,|14108,"
      BBID_WAIVER: "14108,|16.00|12676,"
    """
    raw = txn.get("transaction") or txn.get("@transaction")
    if not isinstance(raw, str) or not raw:
        return ([], [])

    parts = raw.split("|")

    def split_ids(s: str) -> List[str]:
        return [x for x in s.split(",") if x]

    adds = split_ids(parts[0]) if len(parts) >= 1 else []
    drops = split_ids(parts[-1]) if len(parts) >= 2 else []

    return adds, drops


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

def derive_transaction_event_envelopes(
    *,
    year: int,
    league_id: str,
    transactions: List[Dict[str, Any]],
    source_url: str,
    raw_json_truncate_chars: int = 2000,
) -> List[Dict[str, Any]]:
    """
    Produces canonical TRANSACTION_* event envelopes.

    DEDUPE GUARANTEE:
    - external_id is based ONLY on stable MFL facts:
      league + season + type + franchise + timestamp + raw transaction string
    - Parsing improvements will never create duplicates again.
    """
    events: List[Dict[str, Any]] = []

    # Handled elsewhere
    EXCLUDE_TYPES = {"AUCTION_WON", "BBID_WAIVER", "BBID_WAIVER_REQUEST"}

    for idx, txn in enumerate(transactions):
        t = _extract_type(txn)
        if not t or t in EXCLUDE_TYPES:
            continue

        ts_unix = _extract_timestamp_unix(txn)
        occurred_at = unix_seconds_to_iso_z(ts_unix) if ts_unix else None

        franchise_id = _extract_franchise_id(txn)

        # Parse players
        added_ids, dropped_ids = _parse_mfl_transaction_field(txn)
        involved_ids = added_ids + dropped_ids
        primary_player_id = added_ids[0] if added_ids else (dropped_ids[0] if dropped_ids else None)

        # Some transaction feeds (and unit tests) provide a single player directly,
        # without the compact pipe-delimited "transaction" field.
        if primary_player_id is None:
            direct_player_id = txn.get("player_id") or txn.get("player")
            if isinstance(direct_player_id, str) and direct_player_id:
                primary_player_id = direct_player_id


        bid_amount = _extract_bid_amount(txn)

        # TRUE MFL IDENTITY
        transaction_raw = str(txn.get("transaction") or txn.get("@transaction") or "")
        ts_key = str(ts_unix) if ts_unix is not None else f"idx{idx}"

        external_id = _stable_external_id(
            league_id,
            str(year),
            t,
            franchise_id,
            ts_key,
            transaction_raw,
        )

        raw_json = _truncate_raw_json(
            json.dumps(txn, separators=(",", ":"), sort_keys=True),
            raw_json_truncate_chars,
        )

        events.append(
            {
                "event_type": f"TRANSACTION_{t}",
                "occurred_at": occurred_at,
                "external_source": "MFL",
                "external_id": external_id,
                "league_id": league_id,
                "season": year,
                "payload": {
                    "mfl_type": t,
                    "franchise_id": franchise_id,
                    "player_id": primary_player_id,
                    "players_added_ids": added_ids,
                    "players_dropped_ids": dropped_ids,
                    "player_ids_involved": involved_ids,
                    "bid_amount": bid_amount,
                    "source_url": source_url,
                    "raw_mfl_json": raw_json,
                },
            }
        )

    return events