import json
import sqlite3
from typing import Any, Dict, List, Optional, Tuple


QUIET_WEEK_MIN_EVENTS = 3
MAX_BULLETS = 20


def _get(d: Dict[str, Any], *keys: str) -> Optional[Any]:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def _as_list(v: Any) -> List[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x) for x in v if x is not None]
    return [str(v)]


def _fmt_ids(ids: List[str]) -> str:
    if not ids:
        return "(none)"
    return ", ".join(ids)


def _safe_str(v: Any, default: str = "?") -> str:
    if v is None:
        return default
    try:
        return str(v)
    except Exception:
        return default


def _norm_id(raw: Any) -> str:
    s = "" if raw is None else str(raw).strip()
    if not s:
        return ""
    if s.isdigit():
        return s.lstrip("0") or "0"
    return s


class _DirLookup:
    """
    Deterministic directory lookup for names.

    - franchise_directory(league_id, season, franchise_id, name, ...)
    - player_directory(league_id, season, player_id, name, ...)
    """

    def __init__(self, db_path: str, league_id: str, season: int):
        self.db_path = db_path
        self.league_id = league_id
        self.season = season
        self._fr_cache: Dict[str, str] = {}
        self._pl_cache: Dict[str, str] = {}

    def franchise(self, fid_raw: Any) -> str:
        key = "" if fid_raw is None else str(fid_raw).strip()
        if not key:
            return "Unknown team"
        if key in self._fr_cache:
            return self._fr_cache[key]

        name = self._query_one(
            "SELECT name FROM franchise_directory WHERE league_id=? AND season=? AND franchise_id=? LIMIT 1",
            (self.league_id, self.season, key),
        )
        if not name:
            alt = _norm_id(key)
            if alt and alt != key:
                name = self._query_one(
                    "SELECT name FROM franchise_directory WHERE league_id=? AND season=? AND franchise_id=? LIMIT 1",
                    (self.league_id, self.season, alt),
                )

        out = name or key
        self._fr_cache[key] = out
        return out

    def player(self, pid_raw: Any) -> str:
        key = "" if pid_raw is None else str(pid_raw).strip()
        if not key:
            return "Unknown player"
        if key in self._pl_cache:
            return self._pl_cache[key]

        name = self._query_one(
            "SELECT name FROM player_directory WHERE league_id=? AND season=? AND player_id=? LIMIT 1",
            (self.league_id, self.season, key),
        )
        if not name:
            alt = _norm_id(key)
            if alt and alt != key:
                name = self._query_one(
                    "SELECT name FROM player_directory WHERE league_id=? AND season=? AND player_id=? LIMIT 1",
                    (self.league_id, self.season, alt),
                )

        out = name or key
        self._pl_cache[key] = out
        return out

    def _query_one(self, sql: str, params: Tuple[Any, ...]) -> str:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql, params)
        row = cur.fetchone()
        conn.close()
        if row is None:
            return ""
        # first column
        v = row[0]
        return "" if v is None else str(v)


def _render_deterministic_bullets_from_facts_v1(
    *,
    db_path: str,
    league_id: str,
    season: int,
    facts: List[Dict[str, Any]],
) -> str:
    """
    Deterministic 'headline bullets' derived from already-enriched facts.

    Rules:
    - only for non-quiet weeks (>= QUIET_WEEK_MIN_EVENTS facts)
    - deterministic ordering
    - no inference; only uses existing normalized ids + directory lookups
    """
    if len(facts) < QUIET_WEEK_MIN_EVENTS:
        return ""

    lookup = _DirLookup(db_path=db_path, league_id=league_id, season=season)

    # Stable ordering: occurred_at, event_type, canonical_id
    def _k(f: Dict[str, Any]) -> Tuple[str, str, str]:
        return (
            _safe_str(f.get("occurred_at"), "UNKNOWN_TIME"),
            _safe_str(f.get("event_type"), "UNKNOWN"),
            _safe_str(f.get("canonical_id"), "0"),
        )

    ordered = sorted(facts, key=_k)

    bullets: List[str] = []
    for f in ordered[:MAX_BULLETS]:
        et = _safe_str(f.get("event_type"), "UNKNOWN")
        norm = _get(f, "details", "normalized") or {}
        franchise_id = (
            _get(f, "details", "franchise_id")
            or _get(f, "details", "payload", "franchise_id")
            or norm.get("franchise_id")
        )

        team_name = lookup.franchise(franchise_id)

        # Prefer normalized ids (deterministic) for add/drop
        add_ids = _as_list(norm.get("add_player_ids"))
        drop_ids = _as_list(norm.get("drop_player_ids"))

        # Free agent
        if et == "TRANSACTION_FREE_AGENT":
            added = lookup.player(add_ids[0]) if add_ids else "Unknown player"
            bullets.append(f"{team_name} added {added} (free agent).")
            continue

        # Waiver award (win)
        if et == "WAIVER_BID_AWARDED":
            won = lookup.player(add_ids[0]) if add_ids else "Unknown player"
            bid_amount = norm.get("bid_amount")
            bid_txt = f" for ${bid_amount}" if bid_amount is not None else ""
            bullets.append(f"{team_name} won {won}{bid_txt} on waivers.")
            continue

        # BBID waiver claim (placed)
        if et == "TRANSACTION_BBID_WAIVER":
            target = lookup.player(add_ids[0]) if add_ids else "Unknown player"
            bid_amount = norm.get("bid_amount")
            bid_txt = f" (${bid_amount})" if bid_amount is not None else ""
            bullets.append(f"{team_name} placed a blind-bid claim for {target}{bid_txt}.")
            continue

        # Trade (basic, no inference)
        if et == "TRANSACTION_TRADE":
            f1 = norm.get("franchise1_id") or franchise_id
            f2 = norm.get("franchise2_id")
            t1 = lookup.franchise(f1)
            t2 = lookup.franchise(f2) if f2 else "Unknown team"

            f1_gave = _as_list(norm.get("franchise1_gave_up_player_ids"))
            f2_gave = _as_list(norm.get("franchise2_gave_up_player_ids"))

            # Keep it simple/deterministic: first player each side if available
            p1 = lookup.player(f1_gave[0]) if f1_gave else "players"
            p2 = lookup.player(f2_gave[0]) if f2_gave else "players"
            bullets.append(f"Trade: {t1} ↔ {t2} ({p1} / {p2}).")
            continue

        # Default: do not invent
        # Skip unknowns rather than clutter the headline bullets
        continue

    if not bullets:
        return ""

    return "What happened (facts)\n" + "\n".join(f"- {b}" for b in bullets) + "\n\n"


def render_recap_from_facts_v1(artifact: Dict[str, Any], *, db_path: Optional[str] = None) -> str:
    league_id = artifact.get("league_id")
    season = artifact.get("season")
    week_index = artifact.get("week_index")
    recap_version = artifact.get("recap_version")

    window = artifact.get("window", {}) or {}
    win_start = window.get("start")
    win_end = window.get("end")

    mode = _get(artifact, "window", "mode")
    reason = _get(artifact, "window", "reason")
    if mode and mode != "LOCK_TO_LOCK":
        if reason:
            lines.append(f"Window mode: {mode} ({reason})")
        else:
            lines.append(f"Window mode: {mode}")

    sel = artifact.get("selection", {}) or {}
    fingerprint = sel.get("fingerprint")

    facts = artifact.get("facts", []) or []

    lines: List[str] = []

    # NEW: deterministic headline bullets (requires db_path)
    if db_path and league_id is not None and season is not None:
        try:
            bullet_block = _render_deterministic_bullets_from_facts_v1(
                db_path=db_path,
                league_id=str(league_id),
                season=int(season),
                facts=facts,
            )
            if bullet_block:
                lines.append(bullet_block.rstrip("\n"))
                lines.append("")
        except Exception:
            # Debug/audit renderer should never die due to bullet enrichment
            pass

    lines.append(
        f"SquadVault Weekly Recap — League {league_id} — Season {season} — Week {week_index} (v{recap_version})"
    )
    lines.append("")
    lines.append(f"Window: {win_start} → {win_end}")
    lines.append(f"Selection fingerprint: {fingerprint}")
    lines.append("")
    lines.append(f"Facts: {len(facts)}")
    lines.append("")

    for f in facts:
        et = f.get("event_type")
        cid = f.get("canonical_id")
        occurred_at = _safe_str(f.get("occurred_at"), default="UNKNOWN_TIME")

        franchise_id = (
            _get(f, "details", "franchise_id")
            or _get(f, "details", "payload", "franchise_id")
            or "UNKNOWN_TEAM"
        )

        mfl_type = _get(f, "details", "mfl_type") or _get(f, "details", "payload", "mfl_type")
        payload_type = _get(f, "details", "payload", "mfl_type")
        raw_type = _get(f, "details", "raw_mfl", "type")

        norm = _get(f, "details", "normalized") or {}
        add_ids = _as_list(norm.get("add_player_ids"))
        drop_ids = _as_list(norm.get("drop_player_ids"))
        bid_amount = norm.get("bid_amount")

        is_bbid = (mfl_type == "BBID_WAIVER") or (payload_type == "BBID_WAIVER") or (raw_type == "BBID_WAIVER")
        if is_bbid and et in ("TRANSACTION_BBID_WAIVER", "WAIVER_BID_AWARDED"):
            if bid_amount is not None:
                lines.append(
                    f"[{occurred_at}] {et} (team {franchise_id}) "
                    f"bid {bid_amount} add [{_fmt_ids(add_ids)}] drop [{_fmt_ids(drop_ids)}] "
                    f"(canonical {cid})"
                )
            else:
                lines.append(
                    f"[{occurred_at}] {et} (team {franchise_id}) "
                    f"add [{_fmt_ids(add_ids)}] drop [{_fmt_ids(drop_ids)}] "
                    f"(canonical {cid})"
                )
            continue

        if et == "TRANSACTION_FREE_AGENT":
            if add_ids or drop_ids:
                lines.append(
                    f"[{occurred_at}] FREE_AGENT (team {franchise_id}) "
                    f"add [{_fmt_ids(add_ids)}] drop [{_fmt_ids(drop_ids)}] "
                    f"(canonical {cid})"
                )
            else:
                lines.append(
                    f"[{occurred_at}] FREE_AGENT (team {franchise_id}) "
                    f"add [(unknown)] drop [(unknown)] "
                    f"(canonical {cid})"
                )
            continue

        is_trade = (mfl_type == "TRADE") or (payload_type == "TRADE") or (raw_type == "TRADE")
        if is_trade and et == "TRANSACTION_TRADE":
            f1 = norm.get("franchise1_id") or franchise_id
            f2 = norm.get("franchise2_id") or "UNKNOWN_TEAM"

            f1_gave = _as_list(norm.get("franchise1_gave_up_player_ids"))
            f2_gave = _as_list(norm.get("franchise2_gave_up_player_ids"))

            lines.append(
                f"[{occurred_at}] TRADE {f1} ↔ {f2} | "
                f"{f1} gave [{_fmt_ids(f1_gave)}] ; "
                f"{f2} gave [{_fmt_ids(f2_gave)}] "
                f"(canonical {cid})"
            )
            continue

        lines.append(f"[{occurred_at}] {_safe_str(et)} (canonical {cid}) — unrendered")

    lines.append("")
    lines.append("Note: ID-based output only. No inference or hallucination.")
    return "\n".join(lines)


def render_recap_from_enriched_path_v1(path: str, *, db_path: Optional[str] = None) -> str:
    with open(path, "r", encoding="utf-8") as f:
        artifact = json.load(f)
    return render_recap_from_facts_v1(artifact, db_path=db_path)
