from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class EventFact:
    canonical_id: int
    event_type: str
    occurred_at: Optional[str]
    # Minimal common fields; everything else goes in details.
    details: Dict[str, Any]


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


def _json_load(payload: str) -> Dict[str, Any]:
    try:
        obj = json.loads(payload) if payload else {}
        return obj if isinstance(obj, dict) else {"_raw": obj}
    except Exception:
        return {"_parse_error": True, "_raw": payload}


def _parse_raw_mfl_json(payload: Dict[str, Any]) -> Dict[str, Any]:
    raw = payload.get("raw_mfl_json")
    if not raw or not isinstance(raw, str):
        return {}
    try:
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else {"_raw": obj}
    except Exception:
        return {"_parse_error": True, "_raw": raw}


def _extract_bbid_waiver_fields(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    raw example:
      {"franchise":"0004","timestamp":"1726102800","transaction":"14138,|0.50|16149,","type":"BBID_WAIVER"}

    transaction encoding is league/system specific; v1 parsing:
    - split on '|'
    - middle chunk is bid amount if parseable float
    - left/right chunks contain comma-separated player ids (may include trailing commas)
    """
    out: Dict[str, Any] = {}

    tx = raw.get("transaction")
    if isinstance(tx, str) and tx:
        parts = tx.split("|")
        # Expected: [adds, bid, drops] but keep defensive
        if len(parts) >= 1:
            adds = [p for p in parts[0].split(",") if p]
            if adds:
                out["add_player_ids"] = adds
        if len(parts) >= 2:
            try:
                out["bid_amount"] = float(parts[1])
            except Exception:
                out["bid_amount"] = parts[1]
        if len(parts) >= 3:
            drops = [p for p in parts[2].split(",") if p]
            if drops:
                out["drop_player_ids"] = drops

    # Timestamp as int if possible
    ts = raw.get("timestamp")
    try:
        out["mfl_timestamp"] = int(ts) if ts is not None else None
    except Exception:
        out["mfl_timestamp"] = ts

    return out


def _extract_details(event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    v2 extraction:
    - always include source_url, franchise_id, mfl_type when present
    - parse raw_mfl_json (if string JSON)
    - add event-type specific normalized fields
    - keep full payload for audit under payload
    """
    d: Dict[str, Any] = {}

    # Common stable fields if present
    for key in ("source_url", "franchise_id", "player_id", "mfl_type"):
        if key in payload:
            d[key] = payload[key]

    raw = _parse_raw_mfl_json(payload)
    if raw:
        d["raw_mfl"] = raw

        # Determine transaction type
        raw_type = raw.get("type") if isinstance(raw, dict) else None
        tx_type = str(raw_type or payload.get("mfl_type") or event_type)

        # BBID_WAIVER and WAIVER_BID_AWARDED
        if tx_type == "BBID_WAIVER":
            if event_type == "WAIVER_BID_AWARDED":
                d["normalized"] = _extract_waiver_bid_awarded_fields(payload, raw)
            else:
                d["normalized"] = _extract_bbid_waiver_fields(raw)

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
    canonical_ids: List[int],
) -> List[EventFact]:
    if not canonical_ids:
        return []

    placeholders = ",".join(["?"] * len(canonical_ids))
    sql = _SQL.format(placeholders=placeholders)

    params: List[Any] = [league_id, season, *canonical_ids]

    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(sql, params).fetchall()
    finally:
        con.close()

    facts: List[EventFact] = []
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

def _extract_waiver_bid_awarded_fields(payload: Dict[str, Any], raw: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}

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

    # Timestamp from raw if available
    ts = raw.get("timestamp") if isinstance(raw, dict) else None
    try:
        out["mfl_timestamp"] = int(ts) if ts is not None else None
    except Exception:
        out["mfl_timestamp"] = ts

    return out

def _extract_free_agent_fields(payload: Dict[str, Any], raw: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}

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

    # Timestamp from raw
    ts = raw.get("timestamp") if isinstance(raw, dict) else None
    try:
        out["mfl_timestamp"] = int(ts) if ts is not None else None
    except Exception:
        out["mfl_timestamp"] = ts

    return out

def _split_csv_ids(s: Any) -> List[str]:
    if s is None:
        return []
    if not isinstance(s, str):
        s = str(s)
    parts = [p.strip() for p in s.split(",")]
    return [p for p in parts if p]


def _extract_trade_fields(payload: Dict[str, Any], raw: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}

    f1 = raw.get("franchise") if isinstance(raw, dict) else None
    f2 = raw.get("franchise2") if isinstance(raw, dict) else None

    if f1 is not None:
        out["franchise1_id"] = str(f1)
    if f2 is not None:
        out["franchise2_id"] = str(f2)

    f1_gave = raw.get("franchise1_gave_up") if isinstance(raw, dict) else None
    f2_gave = raw.get("franchise2_gave_up") if isinstance(raw, dict) else None

    out["franchise1_gave_up_player_ids"] = _split_csv_ids(f1_gave)
    out["franchise2_gave_up_player_ids"] = _split_csv_ids(f2_gave)

    # Optional fields (keep if present)
    if isinstance(raw, dict) and raw.get("comments") is not None:
        out["comments"] = str(raw.get("comments"))
    if isinstance(raw, dict) and raw.get("expires") is not None:
        try:
            out["expires_timestamp"] = int(raw.get("expires"))
        except Exception:
            out["expires_timestamp"] = raw.get("expires")

    # Timestamp
    ts = raw.get("timestamp") if isinstance(raw, dict) else None
    try:
        out["mfl_timestamp"] = int(ts) if ts is not None else None
    except Exception:
        out["mfl_timestamp"] = ts

    return out

