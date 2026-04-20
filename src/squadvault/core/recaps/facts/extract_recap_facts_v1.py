"""Extract structured facts from canonical events for recap rendering.

S10-pattern canonical-first reads. Each type-specific extractor prefers
canonical payload fields (promoted at ingest in
``src/squadvault/ingest/transactions.py``) and falls back to parsing
``raw_mfl_json`` only for pre-promotion historical events. The fallback
is retained deliberately: silently under-representing historical
transactions would produce visibly degraded recaps on archived weeks,
which is the same class of regression cost that kept b26e93f's
trade-loader fallback alive. See
``_observations/OBSERVATIONS_2026_04_18_S10_SCOPE_CORRECTION.md``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from squadvault.core.storage.session import DatabaseSession


@dataclass(frozen=True)
class EventFact:
    canonical_id: int
    event_type: str
    occurred_at: str | None
    # Minimal common fields; everything else goes in details.
    details: dict[str, Any]


_SQL = """
SELECT
  ce.id AS canonical_id,
  ce.event_type AS event_type,
  me.occurred_at AS occurred_at,
  me.payload_json AS payload_json
FROM canonical_events ce
JOIN memory_events me ON me.id = ce.best_memory_event_id
WHERE ce.league_id = ?
  AND ce.season = ?
  AND ce.id IN ({placeholders})
ORDER BY me.occurred_at ASC, ce.event_type ASC, ce.id ASC;
"""


def _json_load(payload: str) -> dict[str, Any]:
    """Parse JSON string, returning None on failure."""
    try:
        obj = json.loads(payload) if payload else {}
        return obj if isinstance(obj, dict) else {"_raw": obj}
    except (ValueError, TypeError):
        return {"_parse_error": True, "_raw": payload}


def _parse_raw_mfl_json(payload: dict[str, Any]) -> dict[str, Any]:
    """Parse possibly double-encoded MFL JSON payload.

    Retained for two purposes after the S10 canonical-first refactor:

    1. Fallback source for pre-promotion memory events whose canonical
       payload does not yet carry the promoted fields (``mfl_timestamp``,
       ``trade_franchise_a_gave_up``, ``trade_comments``, etc.).
    2. Local transaction-type dispatch in the caller: the per-type
       extractor is selected by ``raw.get("type")``.
    """
    raw = payload.get("raw_mfl_json")
    if not raw or not isinstance(raw, str):
        return {}
    try:
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else {"_raw": obj}
    except (ValueError, TypeError):
        return {"_parse_error": True, "_raw": raw}


def _mfl_timestamp_canonical_first(
    payload: dict[str, Any], raw: dict[str, Any]
) -> Any:
    """Canonical-first read of the Unix timestamp with raw fallback.

    Post-promotion: ``payload["mfl_timestamp"]`` is the canonical source
    (int or None). Pre-promotion: the key is absent; fall back to
    ``raw["timestamp"]`` with the same int-coercion behaviour the
    legacy code path used.
    """
    if "mfl_timestamp" in payload:
        return payload.get("mfl_timestamp")
    ts = raw.get("timestamp") if isinstance(raw, dict) else None
    try:
        return int(ts) if ts is not None else None
    except (ValueError, TypeError):
        return ts


def _extract_bbid_waiver_fields(
    payload: dict[str, Any], raw: dict[str, Any]
) -> dict[str, Any]:
    """
    Extract BBID_WAIVER normalized fields, canonical-first with raw fallback.

    Canonical fields on post-promotion events:
      - payload["players_added_ids"]:    list[str]  (pre-S10 promotion)
      - payload["players_dropped_ids"]:  list[str]  (pre-S10 promotion)
      - payload["bid_amount"]:           float | None  (pre-S10 promotion)
      - payload["mfl_timestamp"]:        int | None (S10 this-pass)

    Pre-promotion fallback: parses the compact pipe-delimited raw
    ``transaction`` string:

        "14138,|0.50|16149,"
         ^^^^^  ^^^^ ^^^^^^
         adds   bid  drops

    Each field reads canonical first, falls back independently so
    partially-promoted payloads are tolerated.
    """
    out: dict[str, Any] = {}

    # Parse raw["transaction"] once for fallback use.
    tx_parts: list[str] = []
    tx = raw.get("transaction") if isinstance(raw, dict) else None
    if isinstance(tx, str) and tx:
        tx_parts = tx.split("|")

    # adds: canonical-first
    if "players_added_ids" in payload:
        adds = payload.get("players_added_ids") or []
        if isinstance(adds, list) and adds:
            out["add_player_ids"] = [str(x) for x in adds if x is not None]
    elif len(tx_parts) >= 1:
        adds_legacy = [p for p in tx_parts[0].split(",") if p]
        if adds_legacy:
            out["add_player_ids"] = adds_legacy

    # drops: canonical-first
    if "players_dropped_ids" in payload:
        drops = payload.get("players_dropped_ids") or []
        if isinstance(drops, list) and drops:
            out["drop_player_ids"] = [str(x) for x in drops if x is not None]
    elif len(tx_parts) >= 3:
        drops_legacy = [p for p in tx_parts[2].split(",") if p]
        if drops_legacy:
            out["drop_player_ids"] = drops_legacy

    # bid_amount: canonical-first
    if "bid_amount" in payload:
        bid = payload.get("bid_amount")
        if bid is not None:
            out["bid_amount"] = bid
    elif len(tx_parts) >= 2:
        try:
            out["bid_amount"] = float(tx_parts[1])
        except (ValueError, TypeError):
            out["bid_amount"] = tx_parts[1]

    # mfl_timestamp: canonical-first (always written for shape stability,
    # preserving legacy behaviour of writing None when no source).
    out["mfl_timestamp"] = _mfl_timestamp_canonical_first(payload, raw)

    return out


def _extract_details(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    """
    v2 extraction:
    - always include source_url, franchise_id, mfl_type when present
    - parse raw_mfl_json (fallback source + render stash)
    - add event-type specific normalized fields (canonical-first)
    - keep full payload for audit under payload
    """
    d: dict[str, Any] = {}

    # Common stable fields if present
    for key in ("source_url", "franchise_id", "player_id", "mfl_type"):
        if key in payload:
            d[key] = payload[key]

    # Parse raw_mfl_json. Live uses: (a) transaction-type dispatch
    # below via raw.get("type"), (b) pre-promotion fallback when
    # per-type extractors need values absent from canonical keys.
    # The d["raw_mfl"] stash written below is retained pending scope
    # decision; former consumer render_recap_text_from_facts_v1 was
    # retired (see memo 0b280cb). No current reader.
    raw = _parse_raw_mfl_json(payload)
    if raw:
        d["raw_mfl"] = raw

        # Dispatch by transaction type. Precedence preserved from
        # pre-S10 behavior (raw["type"] first, then canonical mfl_type,
        # then event_type) — in practice the two type signals always
        # agree because payload["mfl_type"] is derived from raw["type"]
        # at ingest.
        raw_type = raw.get("type") if isinstance(raw, dict) else None
        tx_type = str(raw_type or payload.get("mfl_type") or event_type)

        # BBID_WAIVER and WAIVER_BID_AWARDED
        if tx_type == "BBID_WAIVER":
            if event_type == "WAIVER_BID_AWARDED":
                d["normalized"] = _extract_waiver_bid_awarded_fields(payload, raw)
            else:
                d["normalized"] = _extract_bbid_waiver_fields(payload, raw)

        # FREE_AGENT
        if tx_type == "FREE_AGENT":
            d["normalized"] = _extract_free_agent_fields(payload, raw)

        # TRADE
        if tx_type == "TRADE":
            d["normalized"] = _extract_trade_fields(payload, raw)

    # Always keep the full payload for audit
    d["payload"] = payload
    return d

def extract_recap_facts_v1(
    db_path: str,
    league_id: str,
    season: int,
    canonical_ids: list[int],
) -> list[EventFact]:
    """Extract structured facts from canonical events for a given week."""
    if not canonical_ids:
        return []

    placeholders = ",".join(["?"] * len(canonical_ids))
    sql = _SQL.format(placeholders=placeholders)

    params: list[Any] = [league_id, season, *canonical_ids]

    with DatabaseSession(db_path) as con:
        rows = con.execute(sql, params).fetchall()

    facts: list[EventFact] = []
    for canonical_id, event_type, occurred_at, payload_json in rows:
        payload = _json_load(payload_json)
        details = _extract_details(str(event_type), payload)
        facts.append(
            EventFact(
                canonical_id=int(canonical_id),
                event_type=str(event_type),
                occurred_at=str(occurred_at) if occurred_at is not None else None,
                details=details,
            )
        )
    return facts

def _extract_waiver_bid_awarded_fields(
    payload: dict[str, Any], raw: dict[str, Any]
) -> dict[str, Any]:
    """
    Extract WAIVER_BID_AWARDED normalized fields, canonical-first.

    All fields except ``mfl_timestamp`` were already canonical pre-S10
    (``bid_amount``, ``players_added_ids``, ``players_dropped_ids``,
    ``player_id``). This pass adds canonical-first resolution for
    ``mfl_timestamp`` with raw fallback.

    ``ingest/waiver_bids.py`` now also promotes ``mfl_timestamp`` on
    every WAIVER_BID_* envelope (S10 leak #4 follow-up), so the
    canonical-first path resolves directly for post-promotion events.
    The raw fallback remains active for pre-promotion events per the
    append-only ledger invariant.
    """
    out: dict[str, Any] = {}

    # Prefer already-normalized payload fields if present
    if "bid_amount" in payload:
        out["bid_amount"] = payload.get("bid_amount")

    adds = payload.get("players_added_ids")
    if isinstance(adds, list) and adds:
        out["add_player_ids"] = [str(x) for x in adds if x is not None]

    drops = payload.get("players_dropped_ids")
    if isinstance(drops, list) and drops:
        out["drop_player_ids"] = [str(x) for x in drops if x is not None]

    # Winner / primary player (if present)
    if payload.get("player_id"):
        out["player_id"] = str(payload.get("player_id"))

    # Timestamp canonical-first.
    out["mfl_timestamp"] = _mfl_timestamp_canonical_first(payload, raw)

    return out

def _extract_free_agent_fields(
    payload: dict[str, Any], raw: dict[str, Any]
) -> dict[str, Any]:
    """
    Extract FREE_AGENT normalized fields, canonical-first.

    All list/scalar fields were already canonical pre-S10. This pass
    adds canonical-first resolution for ``mfl_timestamp``.
    """
    out: dict[str, Any] = {}

    # Prefer already-normalized payload lists
    adds = payload.get("players_added_ids")
    if isinstance(adds, list) and adds:
        out["add_player_ids"] = [str(x) for x in adds if x is not None]

    drops = payload.get("players_dropped_ids")
    if isinstance(drops, list) and drops:
        out["drop_player_ids"] = [str(x) for x in drops if x is not None]

    # Primary player (if provided)
    if payload.get("player_id"):
        out["player_id"] = str(payload.get("player_id"))

    # Bid amount (often null for FREE_AGENT, but keep if present)
    if payload.get("bid_amount") is not None:
        out["bid_amount"] = payload.get("bid_amount")

    # Timestamp canonical-first.
    out["mfl_timestamp"] = _mfl_timestamp_canonical_first(payload, raw)

    return out

def _split_csv_ids(s: Any) -> list[str]:
    """Split a comma-separated ID string into a list of non-empty strings."""
    if s is None:
        return []
    if not isinstance(s, str):
        s = str(s)
    parts = [p.strip() for p in s.split(",")]
    return [p for p in parts if p]


def _extract_trade_fields(
    payload: dict[str, Any], raw: dict[str, Any]
) -> dict[str, Any]:
    """
    Extract TRADE normalized fields, canonical-first with raw fallback.

    Canonical fields on post-promotion events:
      - payload["franchise_ids_involved"]:         list[str]
            positions [0]=initiator (franchise A), [1]=counterparty (B).
            Promoted in 6eab1e0.
      - payload["trade_franchise_a_gave_up"]:      list[str]
      - payload["trade_franchise_b_gave_up"]:      list[str]
            Promoted in b26e93f. Empty lists on non-TRADE envelopes for
            shape stability.
      - payload["trade_comments"]:                 str | None
      - payload["trade_expires_timestamp"]:        int | None
            Promoted in this pass. ``None`` on non-TRADE envelopes.
      - payload["mfl_timestamp"]:                  int | None
            Promoted in this pass.

    Pre-promotion fallback paths read ``raw["franchise"]`` /
    ``raw["franchise2"]`` / ``raw["franchise{1,2}_gave_up"]`` /
    ``raw["comments"]`` / ``raw["expires"]`` / ``raw["timestamp"]``
    respectively. Each field falls back independently so partially-
    promoted historical payloads resolve correctly.
    """
    out: dict[str, Any] = {}

    # franchise1_id / franchise2_id: canonical-first via
    # franchise_ids_involved positions; pre-promotion fallback reads
    # raw["franchise"] / raw["franchise2"].
    involved = payload.get("franchise_ids_involved")
    f1: Any = None
    f2: Any = None
    if isinstance(involved, list) and len(involved) >= 2:
        f1, f2 = involved[0], involved[1]
    elif isinstance(involved, list) and len(involved) == 1:
        # Only the initiator resolvable at ingest (unusual for a valid
        # trade, but tolerated); counterparty falls back to raw.
        f1 = involved[0]
        if isinstance(raw, dict):
            f2_raw = raw.get("franchise2")
            if f2_raw is not None:
                f2 = f2_raw
    else:
        # Fully pre-promotion fallback.
        if isinstance(raw, dict):
            f1 = raw.get("franchise")
            f2 = raw.get("franchise2")

    if f1 is not None:
        out["franchise1_id"] = str(f1)
    if f2 is not None:
        out["franchise2_id"] = str(f2)

    # Trade gave-up lists: canonical-first (b26e93f), raw fallback.
    if "trade_franchise_a_gave_up" in payload:
        gave_a = payload.get("trade_franchise_a_gave_up") or []
        if isinstance(gave_a, list):
            out["franchise1_gave_up_player_ids"] = [
                str(x) for x in gave_a if x is not None
            ]
        else:
            out["franchise1_gave_up_player_ids"] = []
    else:
        f1_gave = raw.get("franchise1_gave_up") if isinstance(raw, dict) else None
        out["franchise1_gave_up_player_ids"] = _split_csv_ids(f1_gave)

    if "trade_franchise_b_gave_up" in payload:
        gave_b = payload.get("trade_franchise_b_gave_up") or []
        if isinstance(gave_b, list):
            out["franchise2_gave_up_player_ids"] = [
                str(x) for x in gave_b if x is not None
            ]
        else:
            out["franchise2_gave_up_player_ids"] = []
    else:
        f2_gave = raw.get("franchise2_gave_up") if isinstance(raw, dict) else None
        out["franchise2_gave_up_player_ids"] = _split_csv_ids(f2_gave)

    # Trade comments: canonical-first, raw fallback.
    if "trade_comments" in payload:
        comments = payload.get("trade_comments")
        if comments is not None:
            out["comments"] = str(comments)
    elif isinstance(raw, dict) and raw.get("comments") is not None:
        out["comments"] = str(raw.get("comments"))

    # Expires timestamp: canonical-first, raw fallback.
    if "trade_expires_timestamp" in payload:
        expires = payload.get("trade_expires_timestamp")
        if expires is not None:
            out["expires_timestamp"] = expires
    elif isinstance(raw, dict) and raw.get("expires") is not None:
        try:
            out["expires_timestamp"] = int(raw["expires"])
        except (ValueError, TypeError):
            out["expires_timestamp"] = raw["expires"]

    # mfl_timestamp: canonical-first.
    out["mfl_timestamp"] = _mfl_timestamp_canonical_first(payload, raw)

    return out
