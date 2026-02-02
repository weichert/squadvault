import argparse
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from squadvault.core.storage.sqlite_store import SQLiteStore


FAAB_BUDGET = 100.00




from dataclasses import dataclass
from enum import Enum


class PreflightVerdictType(str, Enum):
    GENERATE_OK = "GENERATE_OK"
    DO_NOT_GENERATE = "DO_NOT_GENERATE"


class DNGReason(str, Enum):
    DNG_INCOMPLETE_WEEK = "DNG_INCOMPLETE_WEEK"
    DNG_DATA_GAP_DETECTED = "DNG_DATA_GAP_DETECTED"
    DNG_LOW_TRUST_OUTPUT_RISK = "DNG_LOW_TRUST_OUTPUT_RISK"
    DNG_SAFETY_CONFLICT = "DNG_SAFETY_CONFLICT"
    DNG_OUT_OF_SCOPE_REQUEST = "DNG_OUT_OF_SCOPE_REQUEST"


@dataclass(frozen=True)
class PreflightVerdict:
    verdict: PreflightVerdictType
    reason_code: DNGReason | None = None
    evidence: dict[str, Any] | None = None

    def __post_init__(self):
        if self.evidence is None:
            object.__setattr__(self, "evidence", {})


def recap_preflight_verdict(
    *,
    conn: sqlite3.Connection,
    league_id: str,
    season: int,
    start: str,
    end: str,
    canonical_events: List[Dict[str, Any]],
) -> PreflightVerdict:
    """Phase 2: Do-Not-Generate (DNG) gate.

    Must run before any recap formatting or narrative generation.
    """
    ledger_count = _ledger_count_in_range(
        conn,
        league_id=league_id,
        season=season,
        occurred_at_min=start,
        occurred_at_max=end,
    )
    canonical_count = len(canonical_events)

    # DNG-02: Ledger has events, but canonical is missing some => canonicalization gap.
    if ledger_count > canonical_count:
        return PreflightVerdict(
            verdict=PreflightVerdictType.DO_NOT_GENERATE,
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

    # DNG-01: Nothing to summarize => withhold.
    if canonical_count == 0:
        return PreflightVerdict(
            verdict=PreflightVerdictType.DO_NOT_GENERATE,
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

    return PreflightVerdict(
        verdict=PreflightVerdictType.GENERATE_OK,
        evidence={
            "league_id": league_id,
            "season": season,
            "range_start": start,
            "range_end": end,
            "ledger_event_count": ledger_count,
            "canonical_event_count": canonical_count,
        },
    )


def _parse_raw_mfl_json(raw: Any, omit_reasons: Dict[str, int]) -> Optional[dict]:
    """Best-effort parse of MFL raw JSON payloads.

    Handles cases where the DB stores:
      1) a JSON object string ("{...}")
      2) a JSON-encoded string that itself contains JSON ("\"{...}\"")
      3) strings with escape sequences that need decoding
    Returns a dict on success, else None (and increments omit_reasons counters).
    """
    if not raw or not isinstance(raw, str):
        omit_reasons["trade_raw_json_missing"] += 1
        return None

    def _try_load(s: str):
        try:
            return json.loads(s)
        except Exception:
            return None

    # Pass 1: direct
    v = _try_load(raw)
    if isinstance(v, dict):
        return v
    if isinstance(v, str):
        v2 = _try_load(v)
        if isinstance(v2, dict):
            return v2

    # Pass 2: strip outer quotes if present
    rs = raw.strip()
    if (rs.startswith('"') and rs.endswith('"')) or (rs.startswith("'") and rs.endswith("'")):
        inner = rs[1:-1]
        v = _try_load(inner)
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            v2 = _try_load(v)
            if isinstance(v2, dict):
                return v2

    # Pass 3: decode escape sequences
    try:
        decoded = rs.encode("utf-8").decode("unicode_escape")
    except Exception:
        decoded = None
    if decoded:
        v = _try_load(decoded)
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            v2 = _try_load(v)
            if isinstance(v2, dict):
                return v2
        # One more: strip quotes after decode
        ds = decoded.strip()
        if (ds.startswith('"') and ds.endswith('"')) or (ds.startswith("'") and ds.endswith("'")):
            inner = ds[1:-1]
            v = _try_load(inner)
            if isinstance(v, dict):
                return v

    omit_reasons["trade_raw_json_parse_failed"] += 1
    return None

# ----------------------------
# Small utilities

def _ledger_count_in_range(
    conn: sqlite3.Connection,
    *,
    league_id: str,
    season: int,
    occurred_at_min: str,
    occurred_at_max: str,
) -> int:
    """Count ledger (memory_events) rows in the given occurred_at range (inclusive)."""
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


# ----------------------------

def _as_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def _safe_json_loads(s: Any) -> Dict[str, Any]:
    """
    Best-effort parse for raw_mfl_json, returning {} on failure.
    """
    if not s or not isinstance(s, str):
        return {}
    try:
        obj = json.loads(s)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def _csv_ids(s: Any) -> List[str]:
    """
    MFL often stores ids as '15754,' (comma-terminated) or as a list.
    Normalize to a list of non-empty strings.
    """
    if s is None:
        return []
    if isinstance(s, list):
        out: List[str] = []
        for x in s:
            sx = str(x).strip()
            if sx:
                out.append(sx)
        return out
    if isinstance(s, str):
        parts = [p.strip() for p in s.split(",")]
        return [p for p in parts if p]
    sx = str(s).strip()
    return [sx] if sx else []


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


# ----------------------------
# Deep extraction (best-effort, non-breaking)
# ----------------------------

def _extract_player_ids_deep(obj: Any) -> Set[str]:
    """
    Deep-scan an object for common player-id keys. Non-breaking, best-effort.
    """
    ids: Set[str] = set()

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            for k, v in x.items():
                lk = str(k).lower()

                if lk in {
                    "player_id",
                    "playerid",
                    "players_added_ids",
                    "players_dropped_ids",
                    "franchise1_gave_up",
                    "franchise2_gave_up",
                    "gave_up",
                    "added",
                    "dropped",
                }:
                    for pid in _csv_ids(v):
                        if pid:
                            ids.add(pid)

                if lk in {"player", "players"} and isinstance(v, dict):
                    pid = v.get("id") or v.get("player_id") or v.get("playerId")
                    if pid is not None:
                        spid = str(pid).strip()
                        if spid:
                            ids.add(spid)

                if lk in {"players", "player_list", "playerlist"} and isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            pid = item.get("id") or item.get("player_id") or item.get("playerId")
                            if pid is not None:
                                spid = str(pid).strip()
                                if spid:
                                    ids.add(spid)

                walk(v)

        elif isinstance(x, list):
            for item in x:
                walk(item)

    walk(obj)
    return ids


def _collect_player_ids_from_events(events: List[Dict[str, Any]]) -> Set[str]:
    ids: Set[str] = set()
    for e in events:
        p = e.get("payload") or {}
        if isinstance(p, dict):
            ids |= _extract_player_ids_deep(p)
            raw = _safe_json_loads(p.get("raw_mfl_json"))
            if raw:
                ids |= _extract_player_ids_deep(raw)
    return ids


def _collect_franchise_ids_from_events(events: List[Dict[str, Any]]) -> Set[str]:
    ids: Set[str] = set()
    for e in events:
        p = e.get("payload") or {}
        if isinstance(p, dict):
            for k in ("franchise_id", "franchise2"):
                v = p.get(k)
                if v is not None:
                    s = str(v).strip()
                    if s:
                        ids.add(s)

            raw = _safe_json_loads(p.get("raw_mfl_json"))
            if raw:
                for k in ("franchise", "franchise_id", "franchise1", "franchise2", "franchise_id2", "franchise2_id"):
                    v = raw.get(k)
                    if v is not None:
                        s = str(v).strip()
                        if s:
                            ids.add(s)
    return ids


# ----------------------------
# Player resolution (ONLY player_directory)
# ----------------------------

class PlayerResolver:
    """
    Resolve player_id -> "Name (Pos, Team)" using player_directory only.
    Fails safe: returns the raw id if not found.
    """

    def __init__(self, db_path: Path, league_id: str, season: int) -> None:
        self.db_path = db_path
        self.league_id = str(league_id)
        self.season = int(season)

        self._map: Dict[str, str] = {}
        self._loaded = False
        self._requested = 0
        self._resolved = 0

    @property
    def requested(self) -> int:
        return self._requested

    @property
    def resolved(self) -> int:
        return self._resolved

    def load_for_ids(self, player_ids: Set[str]) -> None:
        if self._loaded:
            return

        ids = {str(x).strip() for x in player_ids if str(x).strip()}
        self._requested = len(ids)

        if not ids:
            self._loaded = True
            return

        conn: Optional[sqlite3.Connection] = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            tables = {
                r["name"]
                for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            }
            if "player_directory" not in tables:
                self._loaded = True
                return

            ids_list = sorted(ids)
            CHUNK = 900

            for i in range(0, len(ids_list), CHUNK):
                chunk = ids_list[i:i + CHUNK]
                placeholders = ",".join(["?"] * len(chunk))
                rows = cur.execute(
                    f"""
                    SELECT player_id, name, position, team
                    FROM player_directory
                    WHERE league_id=? AND season=? AND player_id IN ({placeholders})
                    """,
                    [self.league_id, self.season, *chunk],
                ).fetchall()

                for r in rows:
                    pid = str(r["player_id"]).strip()
                    name = str(r["name"]).strip() if r["name"] is not None else ""
                    pos = str(r["position"]).strip() if r["position"] is not None else ""
                    team = str(r["team"]).strip() if r["team"] is not None else ""

                    extra = []
                    if pos:
                        extra.append(pos)
                    if team:
                        extra.append(team)

                    disp = f"{name} ({', '.join(extra)})" if (name and extra) else (name or pid)
                    if pid:
                        self._map[pid] = disp

            self._resolved = len(self._map)
            self._loaded = True

        except Exception:
            self._loaded = True
        finally:
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass

    def one(self, player_id: Any) -> str:
        pid = str(player_id).strip() if player_id is not None else ""
        if not pid:
            return "<?>"
        return self._map.get(pid, pid)

    def many(self, ids: Any) -> List[str]:
        return [self.one(pid) for pid in _csv_ids(ids)]


# ----------------------------
# Franchise resolution (ONLY franchise_directory)
# ----------------------------

class FranchiseResolver:
    """
    Resolve franchise_id -> franchise name using franchise_directory only.
    Fails safe: returns the raw id if not found.
    """

    def __init__(self, db_path: Path, league_id: str, season: int) -> None:
        self.db_path = db_path
        self.league_id = str(league_id)
        self.season = int(season)

        self._map: Dict[str, str] = {}
        self._loaded = False
        self._requested = 0
        self._resolved = 0

    @property
    def requested(self) -> int:
        return self._requested

    @property
    def resolved(self) -> int:
        return self._resolved

    def load_for_ids(self, franchise_ids: Set[str]) -> None:
        if self._loaded:
            return

        ids = {str(x).strip() for x in franchise_ids if str(x).strip()}
        self._requested = len(ids)

        if not ids:
            self._loaded = True
            return

        conn: Optional[sqlite3.Connection] = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            tables = {
                r["name"]
                for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            }
            if "franchise_directory" not in tables:
                self._loaded = True
                return

            ids_list = sorted(ids)
            CHUNK = 900

            for i in range(0, len(ids_list), CHUNK):
                chunk = ids_list[i:i + CHUNK]
                placeholders = ",".join(["?"] * len(chunk))
                rows = cur.execute(
                    f"""
                    SELECT franchise_id, name
                    FROM franchise_directory
                    WHERE league_id=? AND season=? AND franchise_id IN ({placeholders})
                    """,
                    [self.league_id, self.season, *chunk],
                ).fetchall()

                for r in rows:
                    fid = str(r["franchise_id"]).strip()
                    name = str(r["name"]).strip() if r["name"] is not None else ""
                    if fid:
                        self._map[fid] = name or fid

            self._resolved = len(self._map)
            self._loaded = True

        except Exception:
            self._loaded = True
        finally:
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass

    def one(self, franchise_id: Any) -> str:
        fid = str(franchise_id).strip() if franchise_id is not None else ""
        if not fid:
            return "?"
        return self._map.get(fid, fid)


def _fid(franchise_resolver: Optional[FranchiseResolver], fid_raw: Any) -> str:
    return franchise_resolver.one(fid_raw) if franchise_resolver is not None else str(fid_raw)


# ----------------------------
# Event selection + scoring
# ----------------------------

def _score_event(e: Dict[str, Any]) -> float:
    et = e.get("event_type")
    p = e.get("payload") or {}

    if et == "TRANSACTION_TRADE":
        return 120.0

    if et == "WAIVER_BID_AWARDED":
        bid_f = _as_float(p.get("bid_amount"), 0.0)
        return 40.0 + min(60.0, bid_f * 2.0)

    if et == "TRANSACTION_WAIVER":
        return 35.0

    if et == "TRANSACTION_BBID_WAIVER":
        return 10.0

    if et == "TRANSACTION_FREE_AGENT":
        return 15.0

    if et == "TRANSACTION_AUCTION_WON":
        return 25.0

    return 0.0


def _dedupe_key(e: Dict[str, Any]) -> str:
    et = e.get("event_type")
    p = e.get("payload") or {}

    if et == "TRANSACTION_TRADE":
        raw = p.get("raw_mfl_json") or ""
        return f"TRADE:{raw}"

    return f'{e.get("external_source")}:{e.get("external_id")}'


def _pick_notable(events: List[Dict[str, Any]], max_items: int) -> List[Dict[str, Any]]:
    TYPE_PRIORITY = {
        "TRANSACTION_TRADE": 0,
        "WAIVER_BID_AWARDED": 1,
        "TRANSACTION_WAIVER": 2,
        "TRANSACTION_FREE_AGENT": 3,
        "TRANSACTION_AUCTION_WON": 4,
        "TRANSACTION_BBID_WAIVER": 5,
    }

    scored: List[Tuple[float, Dict[str, Any]]] = []
    for e in events:
        s = _score_event(e)
        if s > 0:
            scored.append((s, e))

    scored.sort(
        key=lambda t: (
            -t[0],
            TYPE_PRIORITY.get(t[1].get("event_type"), 99),
            t[1].get("occurred_at") or "",
            t[1].get("external_source") or "",
            t[1].get("external_id") or "",
        )
    )

    picked: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for _, e in scored:
        k = _dedupe_key(e)
        if k in seen:
            continue
        seen.add(k)
        picked.append(e)
        if len(picked) >= max_items:
            break

    return picked


# ----------------------------
# Trade parsing
# ----------------------------

def _extract_trade_fields(payload: Dict[str, Any]) -> Tuple[str, str, List[str], List[str]]:
    f1 = payload.get("franchise_id") or payload.get("franchise")
    f2 = payload.get("franchise2")
    gave1 = payload.get("franchise1_gave_up")
    gave2 = payload.get("franchise2_gave_up")

    def ok(v: Any) -> bool:
        return v is not None and str(v).strip() != ""

    if ok(f1) and ok(f2) and (gave1 is not None) and (gave2 is not None):
        return str(f1), str(f2), _csv_ids(gave1), _csv_ids(gave2)

    raw = _safe_json_loads(payload.get("raw_mfl_json"))
    if raw:
        rf1 = raw.get("franchise") or raw.get("franchise_id") or raw.get("franchise1")
        rf2 = raw.get("franchise2") or raw.get("franchise_id2") or raw.get("franchise2_id")
        rg1 = raw.get("franchise1_gave_up") or raw.get("franchise_gave_up")
        rg2 = raw.get("franchise2_gave_up") or raw.get("franchise2_gave_up_list")

        if not (rf1 or rf2 or rg1 or rg2):
            maybe_trade = raw.get("trade")
            if isinstance(maybe_trade, dict):
                rf1 = maybe_trade.get("franchise") or maybe_trade.get("franchise_id") or maybe_trade.get("franchise1")
                rf2 = maybe_trade.get("franchise2") or maybe_trade.get("franchise_id2") or maybe_trade.get("franchise2_id")
                rg1 = maybe_trade.get("franchise1_gave_up") or maybe_trade.get("franchise_gave_up")
                rg2 = maybe_trade.get("franchise2_gave_up") or maybe_trade.get("franchise2_gave_up_list")

        f1 = f1 or rf1
        f2 = f2 or rf2
        gave1 = gave1 if gave1 is not None else rg1
        gave2 = gave2 if gave2 is not None else rg2

    f1_txt = str(f1).strip() if ok(f1) else "?"
    f2_txt = str(f2).strip() if ok(f2) else "?"
    return f1_txt, f2_txt, _csv_ids(gave1), _csv_ids(gave2)


# ----------------------------
# Headline formatting
# ----------------------------

def format_headline(
    e: Dict[str, Any],
    player_resolver: Optional[PlayerResolver] = None,
    franchise_resolver: Optional[FranchiseResolver] = None,
) -> str:
    et = e.get("event_type")
    p = e.get("payload") or {}

    fid_raw = p.get("franchise_id", "?")
    fid = _fid(franchise_resolver, fid_raw)

    def resolve_players(ids: Any) -> List[str]:
        if player_resolver is None:
            return _csv_ids(ids)
        return player_resolver.many(ids)

    if et == "TRANSACTION_TRADE":
        f1, f2, gave1_ids, gave2_ids = _extract_trade_fields(p)
        f1_disp = _fid(franchise_resolver, f1)
        f2_disp = _fid(franchise_resolver, f2)

        left = ", ".join(resolve_players(gave1_ids)) if gave1_ids else "<?>"
        right = ", ".join(resolve_players(gave2_ids)) if gave2_ids else "<?>"
        return f"TRADE: {f1_disp} sent [{left}] to {f2_disp} for [{right}]"

    if et == "WAIVER_BID_AWARDED":
        bid_f = _as_float(p.get("bid_amount"), 0.0)
        add_ids = p.get("players_added_ids") or _csv_ids(p.get("player_id"))
        drop_ids = p.get("players_dropped_ids") or []

        add_txt = ", ".join(resolve_players(add_ids)) if add_ids else "<?>"
        drop_txt = ", ".join(resolve_players(drop_ids)) if drop_ids else "nobody"

        if drop_txt == "nobody":
            return f"WAIVER WIN: {fid} paid ${bid_f:.2f} for [{add_txt}]"
        return f"WAIVER WIN: {fid} paid ${bid_f:.2f} for [{add_txt}] (dropped [{drop_txt}])"

    if et == "TRANSACTION_WAIVER":
        add_ids = p.get("players_added_ids") or []
        drop_ids = p.get("players_dropped_ids") or []
        add_txt = ", ".join(resolve_players(add_ids)) if add_ids else "<?>"
        drop_txt = ", ".join(resolve_players(drop_ids)) if drop_ids else "<?>"
        return f"WAIVER MOVE: {fid} added [{add_txt}] (dropped [{drop_txt}])"

    if et == "TRANSACTION_FREE_AGENT":
        add_ids = p.get("players_added_ids") or []
        drop_ids = p.get("players_dropped_ids") or []
        add_txt = ", ".join(resolve_players(add_ids)) if add_ids else "<?>"
        drop_txt = ", ".join(resolve_players(drop_ids)) if drop_ids else "<?>"
        return f"FREE AGENT: {fid} added [{add_txt}] (dropped [{drop_txt}])"

    if et == "TRANSACTION_AUCTION_WON":
        return f"AUCTION WON: {fid}"

    return f"{et}: {fid}"


# ----------------------------
# Main
# ----------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Preview canonical events in a date range (recap candidate generator)."
    )
    ap.add_argument("--db", required=True, help="Path to SQLite DB (e.g. .local_squadvault.sqlite)")
    ap.add_argument("--league-id", required=True, help="League ID (e.g. 70985)")
    ap.add_argument("--season", type=int, required=True, help="Season year (e.g. 2024)")
    ap.add_argument("--start", required=True, help="Start occurred_at (ISO Z), e.g. 2024-09-01T00:00:00Z")
    ap.add_argument("--end", required=True, help="End occurred_at (ISO Z), e.g. 2024-09-08T23:59:59Z")
    ap.add_argument("--limit", type=int, default=5000, help="Max events to fetch (default 5000)")
    ap.add_argument("--max-notable", type=int, default=25, help="Max notable events to print (default 25)")

    ap.add_argument(
        "--allow-incomplete-canonical",
        action="store_true",
        help="Allow previewing a minimal, non-narrative summary even if canonicalization is incomplete (recap remains WITHHELD by default).",
    )

    ap.add_argument(
        "--debug-sample-event",
        action="store_true",
        help="Print the first canonical event dict (JSON) and exit (for schema mapping).",
    )



    ap.add_argument(
        "--debug-sample-type",
        type=str,
        default=None,
        help="Print the first canonical event matching EVENT_TYPE (JSON) and exit (for schema mapping).",
    )

    ap.add_argument(
        "--resolve-players",
        action="store_true",
        help="Resolve player IDs using player_directory.",
    )
    ap.add_argument(
        "--resolve-franchises",
        action="store_true",
        help="Resolve franchise IDs using franchise_directory.",
    )

    args = ap.parse_args()

    db_path = Path(args.db)
    store = SQLiteStore(db_path)

    events = store.fetch_events_in_range(
        league_id=args.league_id,
        season=args.season,
        occurred_at_min=args.start,
        occurred_at_max=args.end,
        limit=args.limit,
    )


    if getattr(args, "debug_sample_event", False):
        _print_header("DEBUG: sample canonical event")
        if events:
            import json
            print(json.dumps(events[0], indent=2, sort_keys=True))
        else:
            print("(No events in range.)")
        return 0
    if getattr(args, "debug_sample_type", None):
        _print_header(f"DEBUG: first canonical event of type {args.debug_sample_type}")
        match = None
        for _e in events:
            if (_e.get("event_type") or "") == args.debug_sample_type:
                match = _e
                break
        if match:
            import json
            print(json.dumps(match, indent=2, sort_keys=True))
        else:
            print("(No matching events in range.)")
        return 0


    # ----------------------------
    # Phase 2: Preflight gate (Do Not Generate / Minimal Preview override)
    # ----------------------------
    conn = sqlite3.connect(str(db_path))
    try:
        preflight = recap_preflight_verdict(
            conn=conn,
            league_id=args.league_id,
            season=args.season,
            start=args.start,
            end=args.end,
            canonical_events=events,
        )

        if preflight.verdict == PreflightVerdictType.DO_NOT_GENERATE:
            if (
                preflight.reason_code == DNGReason.DNG_DATA_GAP_DETECTED
                and getattr(args, "allow_incomplete_canonical", False)
            ):
                _print_header("MINIMAL MODE (CANONICAL GAP OVERRIDE) — Recap still WITHHELD")
                print(f"Status     : WITHHELD")
                print(f"Reason     : {preflight.reason_code.value if preflight.reason_code else None}")
                print(f"Evidence   : {preflight.evidence}")
                print()

                _print_header("Counts by event_type (canonical only)")
                counts = Counter([e.get("event_type") for e in events])
                for k in sorted(counts.keys()):
                    print(f"{k:<35} {counts[k]}")
                print()

                _print_header("Notable events (canonical only, capped)")
                cap_total = 15
                cap_per_type = 3

                priority = [
                    "TRANSACTION_TRADE",
                    "TRANSACTION_BBID_WAIVER",
                    "TRANSACTION_WAIVER",
                    "TRANSACTION_FREE_AGENT",
                    "WAIVER_BID_AWARDED",
                    "DRAFT_PICK",
                    "TRANSACTION_AUCTION_WON",
                    "TRANSACTION_LOCK_ALL_PLAYERS",
                    "TRANSACTION_AUTO_PROCESS_WAIVERS",
                ]

                by_type: dict[str, list[dict]] = {}
                for _e in events:
                    et = _e.get("event_type") or ""
                    by_type.setdefault(et, []).append(_e)

                

                omit_reasons = Counter()
                printed_by_type = Counter()
                seen_keys: set[str] = set()
                dedup_skipped = 0  # count of duplicate notable lines skipped (content-level)

                def _summarize_minimal(_e: dict) -> str | None:
                    event_type = _e.get("event_type") or ""
                    occurred_at = _e.get("occurred_at") or _e.get("occurred_at_utc") or ""
                    payload = _e.get("payload") or {}

                    if not event_type:
                        omit_reasons["missing_event_type"] += 1
                        return None
                    if not occurred_at:
                        omit_reasons["missing_occurred_at"] += 1
                        return None

                    mfl_type = payload.get("mfl_type")

                    # Trade (canonical payload currently stores the full MFL trade fields inside raw_mfl_json)
                    if event_type == "TRANSACTION_TRADE":
                        # Trades: canonical payload often stores detailed fields inside raw_mfl_json.
                        # We remain omission-first: if we cannot extract both franchises, omit (and record why).
                        f1 = payload.get("franchise") or payload.get("franchise_id")
                        f2 = payload.get("franchise2") or payload.get("franchise2_id")
                        g1 = payload.get("franchise1_gave_up")
                        g2 = payload.get("franchise2_gave_up")

                        raw = payload.get("raw_mfl_json")
                        rawj = _parse_raw_mfl_json(raw, omit_reasons)
                        if isinstance(rawj, dict):
                                f1 = f1 or rawj.get("franchise")
                                f2 = f2 or rawj.get("franchise2")
                                g1 = g1 or rawj.get("franchise1_gave_up")
                                g2 = g2 or rawj.get("franchise2_gave_up")
                                # If keys are absent, record it (still may succeed via fallback ids)
                                if ("franchise" not in rawj) or ("franchise2" not in rawj):
                                    omit_reasons["trade_raw_json_missing_keys"] += 1
                        else:
                            omit_reasons["trade_raw_json_missing"] += 1

                        if not f1 or not f2:
                            omit_reasons["trade_missing_franchises"] += 1
                            return None

                        g1s = (str(g1 or "")).strip().strip(",")
                        g2s = (str(g2 or "")).strip().strip(",")
                        extra = f" | mfl_type={mfl_type}" if mfl_type else ""
                        return f"- {occurred_at} | TRANSACTION_TRADE | {f1} gave [{g1s}] ⇄ {f2} gave [{g2s}]{extra}"

                    # Franchise/player identity (payload-first)
                    fid = (
                        payload.get("franchise_id")
                        or payload.get("franchise")
                        or _e.get("franchise_id")
                        or _e.get("fid")
                        or _e.get("franchise")
                    )
                    pid = (
                        payload.get("player_id")
                        or _e.get("player_id")
                        or _e.get("pid")
                    )

                    # System events can be shown without franchise/player
                    if event_type in ("TRANSACTION_LOCK_ALL_PLAYERS", "TRANSACTION_AUTO_PROCESS_WAIVERS"):
                        extra = f" | mfl_type={mfl_type}" if mfl_type else ""
                        return f"- {occurred_at} | {event_type}{extra}"

                    if not fid:
                        omit_reasons["missing_franchise_id"] += 1
                        return None

                    bid = payload.get("bid_amount")
                    parts = [f"- {occurred_at} | {event_type} | franchise={fid}"]
                    if pid is not None:
                        parts.append(f"player={pid}")
                    if mfl_type:
                        parts.append(f"mfl_type={mfl_type}")
                    if bid is not None:
                        parts.append(f"bid={bid}")

                    return " | ".join(parts)


                shown_total = 0
                for et in priority:
                    if shown_total >= cap_total:
                        break
                    per_type = 0
                    for _e in by_type.get(et, []):
                        if shown_total >= cap_total or per_type >= cap_per_type:
                            break
                        line = _summarize_minimal(_e)
                        if not line:
                            continue
                        # De-duplicate by rendered line content (handles distinct ids with identical content)
                        if line in seen_keys:
                            dedup_skipped += 1
                            continue
                        print(line)
                        seen_keys.add(line)
                        printed_by_type[et] += 1
                        shown_total += 1
                        per_type += 1

                # If we still have room, include a few events from remaining types (still capped per type).
                if shown_total < cap_total:
                    for et, lst in by_type.items():
                        if et in priority:
                            continue
                        if shown_total >= cap_total:
                            break
                        per_type = 0
                        for _e in lst:
                            if shown_total >= cap_total or per_type >= cap_per_type:
                                break
                        line = _summarize_minimal(_e)
                        if not line:
                            continue
                        # De-duplicate by rendered line content (handles distinct ids with identical content)
                        if line in seen_keys:
                            dedup_skipped += 1
                            continue
                        print(line)
                        seen_keys.add(line)
                        printed_by_type[et] += 1
                        shown_total += 1
                        per_type += 1

                shown = shown_total



                if shown == 0:
                    print("(No notable events met minimal identity requirements.)")

                print()
                _print_header("Minimal Mode diagnostics")
                print("Printed by type:")
                for _k in sorted(printed_by_type.keys()):
                    print(f"- {_k}: {printed_by_type[_k]}")
                print(f"De-dupe skipped: {dedup_skipped}")
                if omit_reasons:
                    print("Omitted (reason counts):")
                    for _k in sorted(omit_reasons.keys()):
                        print(f"- {_k}: {omit_reasons[_k]}")
                else:
                    print("Omitted (reason counts): (none)")

                print()
                print("Recap withheld: canonicalization incomplete; minimal summary shown for validation only.")
                return 0

            _print_header("Recap withheld (Do Not Generate)")
            print(f"Status     : WITHHELD")
            print(f"Reason     : {preflight.reason_code.value if preflight.reason_code else None}")
            print(f"Evidence   : {preflight.evidence}")
            return 0
    finally:
        conn.close()


    player_resolver: Optional[PlayerResolver] = None
    franchise_resolver: Optional[FranchiseResolver] = None

    if args.resolve_players:
        ids_needed = _collect_player_ids_from_events(events)
        player_resolver = PlayerResolver(db_path=db_path, league_id=args.league_id, season=args.season)
        player_resolver.load_for_ids(ids_needed)

    if args.resolve_franchises:
        fids_needed = _collect_franchise_ids_from_events(events)
        franchise_resolver = FranchiseResolver(db_path=db_path, league_id=args.league_id, season=args.season)
        franchise_resolver.load_for_ids(fids_needed)

    _print_header("Range Recap Preview (Canonical)")
    print(f"DB       : {db_path}")
    print(f"League   : {args.league_id}")
    print(f"Season   : {args.season}")
    print(f"Range    : {args.start}  →  {args.end}")
    print(f"Fetched  : {len(events)} events")

    if player_resolver is not None:
        print(f"Players  : player_directory | requested={player_resolver.requested} resolved={player_resolver.resolved}")

    if franchise_resolver is not None:
        print(
            f"Franchise: franchise_directory | requested={franchise_resolver.requested} resolved={franchise_resolver.resolved}"
        )

    counts = Counter(e.get("event_type") for e in events)
    _print_header("Counts by event_type")
    for etype, n in sorted(counts.items(), key=lambda x: (-x[1], x[0] or "")):
        print(f"{etype:35} {n}")

    trades_n = counts.get("TRANSACTION_TRADE", 0)
    waiver_wins_n = counts.get("WAIVER_BID_AWARDED", 0)
    fa_moves_n = counts.get("TRANSACTION_FREE_AGENT", 0)

    _print_header("Recap highlights (auto)")
    print(f"- Trades executed: {trades_n}")
    print(f"- Waiver bids awarded: {waiver_wins_n}")
    print(f"- Free agent moves: {fa_moves_n}")

    _print_header("Leaderboards (auto)")

    moves_by_team: Dict[str, int] = defaultdict(int)
    for e in events:
        p = e.get("payload") or {}
        fid = p.get("franchise_id")
        if fid:
            moves_by_team[str(fid)] += 1

    top_activity = sorted(moves_by_team.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    if top_activity:
        print("Most active franchises:")
        for fid_raw, n in top_activity:
            print(f"- {_fid(franchise_resolver, fid_raw)}: {n} moves")
    else:
        print("Most active franchises: (none)")

    print()

    faab_total_by_team: Dict[str, float] = defaultdict(float)
    biggest_bids: List[Tuple[float, str]] = []
    waiver_wins: List[Tuple[float, str, Dict[str, Any]]] = []

    for e in events:
        if e.get("event_type") != "WAIVER_BID_AWARDED":
            continue
        p = e.get("payload") or {}
        team = str(p.get("franchise_id", "?"))
        bid_f = _as_float(p.get("bid_amount"), 0.0)

        faab_total_by_team[team] += bid_f
        biggest_bids.append((bid_f, team))

        occurred_at = e.get("occurred_at") or ""
        waiver_wins.append((bid_f, occurred_at, e))

    top_faab_total = sorted(faab_total_by_team.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    if top_faab_total:
        print(f"Top FAAB spenders (total on waiver wins, budget ${FAAB_BUDGET:.2f}):")
        for fid_raw, total in top_faab_total:
            remaining = max(0.0, FAAB_BUDGET - total)
            print(f"- {_fid(franchise_resolver, fid_raw)}: spent ${total:.2f} (remaining ${remaining:.2f})")
    else:
        print("Top FAAB spenders (total on waiver wins): (none)")

    print()

    biggest_bids.sort(key=lambda t: (-t[0], t[1]))
    top_biggest = biggest_bids[:5]
    if top_biggest:
        print("Biggest single winning bids:")
        for bid, fid_raw in top_biggest:
            print(f"- {_fid(franchise_resolver, fid_raw)}: ${bid:.2f}")
    else:
        print("Biggest single winning bids: (none)")

    print()

    waiver_wins.sort(key=lambda t: (-t[0], t[1], _dedupe_key(t[2])))
    top_waiver_wins = waiver_wins[:5]
    if top_waiver_wins:
        print("Top waiver wins (by bid):")
        for bid_f, occurred_at, e in top_waiver_wins:
            p = e.get("payload") or {}
            fid_raw = p.get("franchise_id", "?")
            fid_disp = _fid(franchise_resolver, fid_raw)

            add_ids = p.get("players_added_ids") or _csv_ids(p.get("player_id"))
            drop_ids = p.get("players_dropped_ids") or []

            if player_resolver is None:
                add_disp = _csv_ids(add_ids)
                drop_disp = _csv_ids(drop_ids)
            else:
                add_disp = player_resolver.many(add_ids)
                drop_disp = player_resolver.many(drop_ids)

            add_txt = ", ".join(add_disp) if add_disp else "<?>"
            drop_txt = ", ".join(drop_disp) if drop_disp else "nobody"
            print(f"- {occurred_at} | {fid_disp} | ${bid_f:.2f} | +[{add_txt}] / -[{drop_txt}]")
    else:
        print("Top waiver wins (by bid): (none)")

    notable = _pick_notable(events, args.max_notable)
    _print_header(f"Notable events (first {len(notable)} shown)")
    for e in notable:
        occurred_at = e.get("occurred_at")
        ext = f'{e.get("external_source")}:{e.get("external_id")}'
        headline = format_headline(
            e,
            player_resolver=player_resolver,
            franchise_resolver=franchise_resolver,
        )
        print(f"- {occurred_at} | {headline} | {ext}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
