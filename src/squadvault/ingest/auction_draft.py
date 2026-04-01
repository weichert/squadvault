"""Derive canonical auction draft events from raw MFL transaction data."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from squadvault.utils.time import unix_seconds_to_iso_z

logger = logging.getLogger(__name__)
def _safe_get(d: dict[str, Any], *keys: str) -> Any:
    """Safely get a value from a dict with fallback."""
    for k in keys:
        if k in d:
            return d[k]
    return None


def _extract_type(txn: dict[str, Any]) -> str:
    """Extract MFL transaction type from raw data."""
    t = _safe_get(txn, "@type", "type", "@transactionType", "transactionType")
    return str(t) if t is not None else ""


def _extract_timestamp_unix(txn: dict[str, Any]) -> int | None:
    """Extract and validate Unix timestamp from raw data."""
    val = _safe_get(txn, "@timestamp", "timestamp", "@time", "time")
    if val is None:
        return None
    try:
        return int(str(val))
    except Exception as exc:
        logger.debug("%s", exc)
        return None


def _extract_franchise_id(txn: dict[str, Any]) -> str:
    """Extract franchise ID from raw transaction data."""
    val = _safe_get(txn, "@franchise", "franchise", "@franchise_id", "franchise_id")
    if isinstance(val, str):
        return val.strip()
    if isinstance(val, dict):
        v2 = _safe_get(val, "@id", "id", "@franchise", "franchise")
        return str(v2).strip() if v2 is not None else ""
    return ""


def _parse_transaction_field(txn: dict[str, Any]) -> tuple[str, float | None]:
    """
    MFL AUCTION_WON sample:
      transaction = "14223|1|"
      => player_id=14223, bid=1

    We defensively parse:
      parts[0] -> player_id
      parts[1] -> bid_amount (float) if parseable
    """
    raw = _safe_get(txn, "@transaction", "transaction")
    if not raw or not isinstance(raw, str):
        return "", None

    parts = raw.split("|")
    player_id = parts[0].strip() if len(parts) > 0 else ""

    bid_amount: float | None = None
    if len(parts) > 1 and parts[1].strip() != "":
        try:
            bid_amount = float(parts[1].strip())
        except Exception as exc:
            logger.debug("%s", exc)
            bid_amount = None

    return player_id, bid_amount


def _extract_player_id(txn: dict[str, Any]) -> str:
    # First try explicit fields (some endpoints/leagues may provide them)
    """Extract player ID from raw transaction data."""
    v = _safe_get(txn, "@player", "player", "@player_id", "player_id")
    if isinstance(v, str) and v.strip():
        return v.strip()
    if isinstance(v, dict):
        pid = _safe_get(v, "@id", "id", "@player", "player")
        if pid is not None and str(pid).strip():
            return str(pid).strip()

    # Fallback: parse pipe-delimited transaction field, e.g. "14223|1|"
    pid2, _ = _parse_transaction_field(txn)
    return pid2


def _extract_bid_amount(txn: dict[str, Any]) -> float | None:
    # First try explicit fields (if present)
    """Extract bid amount from raw transaction data."""
    for k in ("@bid", "bid", "@amount", "amount", "@price", "price"):
        v = txn.get(k)
        if v is None:
            continue
        try:
            return float(str(v))
        except Exception as exc:
            logger.debug("%s", exc)
            continue

    # Fallback: parse pipe-delimited transaction field, e.g. "14223|1|"
    _, bid2 = _parse_transaction_field(txn)
    return bid2


def _truncate_raw_json(text: str, limit: int) -> str:
    """Truncate raw JSON string for storage efficiency."""
    if len(text) <= limit:
        return text
    return text[:limit] + "...(truncated)"


def _stable_external_id(*parts: str) -> str:
    """Deterministic ID for dedupe. Avoids relying on MFL having a clean unique id."""
    raw = "|".join([p or "" for p in parts])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def derive_auction_event_envelopes_from_transactions(
    *,
    year: int,
    league_id: str,
    transactions: list[dict[str, Any]],
    source_url: str,
    raw_json_truncate_chars: int = 2000,
) -> list[dict[str, Any]]:
    """
    Produces canonical SquadVault "event envelopes" for auction/draft outcomes
    derived from MFL transactions.

    IMPORTANT:
    - Facts only (no narrative, no inference)
    - Append-only friendly
    - Deterministic external_id for dedupe
    """
    events: list[dict[str, Any]] = []

    for idx, txn in enumerate(transactions):
        t = _extract_type(txn).upper()

        # Conservative heuristic: only treat explicitly auction/draft-like types as auction events.
        if "AUCTION" not in t and "DRAFT" not in t:
            continue

        ts_unix = _extract_timestamp_unix(txn)
        occurred_at = unix_seconds_to_iso_z(ts_unix) if ts_unix is not None else None

        franchise_id = _extract_franchise_id(txn)
        player_id = _extract_player_id(txn)
        bid_amount = _extract_bid_amount(txn)

        # If we can't identify the player, skip (better silence than bad facts)
        if not player_id:
            continue

        # Deterministic ID: league + year + type + franchise + player + timestamp/index
        ts_part = str(ts_unix) if ts_unix is not None else f"idx{idx}"
        external_id = _stable_external_id(league_id, str(year), t, franchise_id, player_id, ts_part)

        raw_json = _truncate_raw_json(
            json.dumps(txn, separators=(",", ":"), sort_keys=True),
            raw_json_truncate_chars,
        )

        events.append({
            "event_type": "DRAFT_PICK",  # keep canonical; store original type in payload
            "occurred_at": occurred_at,
            "external_source": "MFL",
            "external_id": external_id,
            "league_id": league_id,
            "season": year,
            "payload": {
                "mfl_type": t,
                "franchise_id": franchise_id,
                "player_id": player_id,
                "bid_amount": bid_amount,
                "source_url": source_url,
                "raw_mfl_json": raw_json,
            },
        })

    return events
