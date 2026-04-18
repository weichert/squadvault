"""Derive canonical transaction events from raw MFL transaction data."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from squadvault.utils.time import unix_seconds_to_iso_z

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _safe_get(d: dict[str, Any], *keys: str) -> Any:
    """Safely get a value from a dict with fallback."""
    for k in keys:
        if k in d:
            return d[k]
    return None


def _stable_external_id(*parts: str) -> str:
    """Generate a stable external ID for deduplication."""
    raw = "|".join([p or "" for p in parts])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _truncate_raw_json(text: str, limit: int) -> str:
    """Truncate raw JSON string for storage efficiency."""
    if len(text) <= limit:
        return text
    return text[:limit] + "...(truncated)"


def _extract_type(txn: dict[str, Any]) -> str:
    """Extract MFL transaction type from raw data."""
    return str(_safe_get(txn, "@type", "type") or "").upper().strip()


def _extract_franchise_id(txn: dict[str, Any]) -> str:
    """Extract franchise ID (initiator) from raw transaction data."""
    return str(_safe_get(txn, "@franchise", "franchise") or "")


def _extract_all_franchise_ids(txn: dict[str, Any]) -> list[str]:
    """
    Extract every franchise ID referenced by a raw MFL transaction.

    For trades, MFL records counterparties as sibling keys: the
    initiator is under ``franchise`` (or ``@franchise``) and each
    counterparty is under ``franchise2``, ``franchise3``, ... (with or
    without the ``@`` prefix, depending on the feed shape). For non-trade
    transactions, only the initiator is present.

    Returns a deduplicated list with the initiator first (when
    resolvable) and counterparties in MFL key order. Empty/non-string
    values are skipped.

    Promotion of this structure into the canonical payload is what
    allows `core/queries/franchise_queries` to answer
    "which franchises does this event involve?" without reaching into
    raw_mfl_json — resolving the layer-boundary aspect of Audit
    Surprise S10.
    """
    out: list[str] = []
    seen: set[str] = set()

    def _push(v: Any) -> None:
        if isinstance(v, str) and v and v not in seen:
            seen.add(v)
            out.append(v)

    # Initiator first, using the same precedence as _extract_franchise_id
    # so the two helpers stay consistent on the "primary" franchise.
    _push(_safe_get(txn, "@franchise", "franchise"))

    # Then any franchise* / @franchise* keys in MFL's natural dict order.
    # Matches the semantic predicate of the prior query-side parser:
    # "any string key that starts with 'franchise'". Dedupe via `seen`
    # ensures the initiator is not duplicated when both "@franchise" and
    # "franchise" are present (or when the initiator's key is processed
    # in the loop).
    for k, v in txn.items():
        if not isinstance(k, str):
            continue
        bare = k[1:] if k.startswith("@") else k
        if bare.startswith("franchise"):
            _push(v)

    return out


def _extract_timestamp_unix(txn: dict[str, Any]) -> int | None:
    """Extract and validate Unix timestamp from raw data."""
    v = _safe_get(txn, "@timestamp", "timestamp")
    try:
        return int(v) if v is not None else None
    except Exception as exc:
        logger.debug("%s", exc)
        return None


def _extract_bid_amount(txn: dict[str, Any]) -> float | None:
    """Extract bid amount from raw transaction data."""
    for k in ("@bid", "bid", "@amount", "amount", "@bbid", "bbid"):
        v = txn.get(k)
        if v is None:
            continue
        try:
            return float(v)
        except Exception as exc:
            logger.debug("%s", exc)
            pass
    return None


def _parse_mfl_transaction_field(txn: dict[str, Any]) -> tuple[list[str], list[str]]:
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

    def split_ids(s: str) -> list[str]:
        """Split comma-separated ID string into list of non-empty strings."""
        return [x for x in s.split(",") if x]

    adds = split_ids(parts[0]) if len(parts) >= 1 else []
    drops = split_ids(parts[-1]) if len(parts) >= 2 else []

    return adds, drops


def _parse_trade_gave_up(txn: dict[str, Any]) -> tuple[list[str], list[str]]:
    """
    Parse trade-specific ``franchise1_gave_up`` / ``franchise2_gave_up`` lists.

    MFL encodes bilateral trade player movements as sibling keys on the
    raw transaction dict. ``franchise1_gave_up`` holds the player IDs
    given up by the initiator (the ``franchise`` key); ``franchise2_gave_up``
    holds the IDs given up by the counterparty (``franchise2``). The
    format is comma-separated with a trailing empty tail: e.g.
    ``"15648,15712,"``.

    Returns ``(franchise_a_gave_up, franchise_b_gave_up)``. Empty lists
    when the keys are absent or unparseable. Intended to be called only
    for TRANSACTION_TRADE events; non-trade transactions will return
    ``([], [])`` because the keys are not present on their raw dicts.

    Promotion of these lists into the canonical trade payload at ingest
    is the S10-pattern companion to ``_extract_all_franchise_ids``.
    Together they let consumer-layer code read trade structure from
    canonical fields without reaching into ``raw_mfl_json`` — resolving
    the layer-boundary aspect of Audit Surprise S10 for the trade case
    (see ``_observations/OBSERVATIONS_2026_04_18_S10_SCOPE_CORRECTION.md``).
    """
    def _split(s: Any) -> list[str]:
        if not isinstance(s, str):
            return []
        return [p for p in s.split(",") if p]

    return (
        _split(_safe_get(txn, "franchise1_gave_up", "@franchise1_gave_up")),
        _split(_safe_get(txn, "franchise2_gave_up", "@franchise2_gave_up")),
    )


def _extract_trade_comments(txn: dict[str, Any]) -> str | None:
    """
    Extract free-text trade commentary from a raw MFL trade dict.

    MFL TRADE transactions can carry a ``comments`` sibling key holding
    owner-authored notes about the deal (occasionally mirrored as
    ``@comments`` in some feed shapes). Returns the string verbatim,
    or None when the key is absent or the value is non-string.

    Promotion of this field into the canonical trade payload at ingest
    is the S10-pattern companion to ``_parse_trade_gave_up``. Consumer-
    layer code reads canonical ``trade_comments`` first and falls back
    to ``raw_mfl_json`` only for pre-promotion historical events.
    """
    v = _safe_get(txn, "comments", "@comments")
    if v is None:
        return None
    return str(v) if isinstance(v, str) else None


def _extract_trade_expires_timestamp(txn: dict[str, Any]) -> int | None:
    """
    Extract a trade's expiration Unix timestamp from a raw MFL trade dict.

    MFL encodes the trade's expiration window as a Unix-seconds string
    (or int) under the ``expires`` sibling key (occasionally mirrored
    as ``@expires``). Returns an int; unparseable or absent values
    yield None.

    Promotion of this field into the canonical trade payload at ingest
    is the S10-pattern companion to ``_parse_trade_gave_up``.
    """
    v = _safe_get(txn, "expires", "@expires")
    if v is None:
        return None
    try:
        return int(v)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

def derive_transaction_event_envelopes(
    *,
    year: int,
    league_id: str,
    transactions: list[dict[str, Any]],
    source_url: str,
    raw_json_truncate_chars: int = 2000,
) -> list[dict[str, Any]]:
    """
    Produces canonical TRANSACTION_* event envelopes.

    DEDUPE GUARANTEE:
    - external_id is based ONLY on stable MFL facts:
      league + season + type + franchise + timestamp + raw transaction string
    - Parsing improvements will never create duplicates again.
    """
    events: list[dict[str, Any]] = []

    # Handled elsewhere
    EXCLUDE_TYPES = {"AUCTION_WON", "BBID_WAIVER", "BBID_WAIVER_REQUEST"}

    for idx, txn in enumerate(transactions):
        t = _extract_type(txn)
        if not t or t in EXCLUDE_TYPES:
            continue

        ts_unix = _extract_timestamp_unix(txn)
        occurred_at = unix_seconds_to_iso_z(ts_unix) if ts_unix else None

        franchise_id = _extract_franchise_id(txn)
        franchise_ids_involved = _extract_all_franchise_ids(txn)

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

        # Trade-specific structure. For TRANSACTION_TRADE events, MFL
        # encodes player movements, commentary, and expiration under
        # sibling keys on the raw transaction dict rather than in the
        # compact "transaction" string parsed above. Promoting these
        # into the canonical payload at ingest is the S10-pattern
        # resolution for the trade case — see
        # _observations/OBSERVATIONS_2026_04_18_S10_SCOPE_CORRECTION.md.
        # Fields are always present on every envelope (with empty-list
        # / None defaults for non-trades) so consumers can rely on
        # key-presence as the post-promotion signal without per-type
        # branching.
        if t == "TRADE":
            trade_franchise_a_gave_up, trade_franchise_b_gave_up = _parse_trade_gave_up(txn)
            trade_comments = _extract_trade_comments(txn)
            trade_expires_timestamp = _extract_trade_expires_timestamp(txn)
        else:
            trade_franchise_a_gave_up = []
            trade_franchise_b_gave_up = []
            trade_comments = None
            trade_expires_timestamp = None

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
                    "mfl_timestamp": ts_unix,
                    "franchise_id": franchise_id,
                    "franchise_ids_involved": franchise_ids_involved,
                    "player_id": primary_player_id,
                    "players_added_ids": added_ids,
                    "players_dropped_ids": dropped_ids,
                    "player_ids_involved": involved_ids,
                    "trade_franchise_a_gave_up": trade_franchise_a_gave_up,
                    "trade_franchise_b_gave_up": trade_franchise_b_gave_up,
                    "trade_comments": trade_comments,
                    "trade_expires_timestamp": trade_expires_timestamp,
                    "bid_amount": bid_amount,
                    "source_url": source_url,
                    "raw_mfl_json": raw_json,
                },
            }
        )

    return events
