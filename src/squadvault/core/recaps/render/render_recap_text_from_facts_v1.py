import json
from typing import Any, Dict, List, Optional


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


def render_recap_from_facts_v1(artifact: Dict[str, Any]) -> str:
    league_id = artifact.get("league_id")
    season = artifact.get("season")
    week_index = artifact.get("week_index")
    recap_version = artifact.get("recap_version")

    window = artifact.get("window", {}) or {}
    win_start = window.get("start")
    win_end = window.get("end")

    sel = artifact.get("selection", {}) or {}
    fingerprint = sel.get("fingerprint")

    facts = artifact.get("facts", []) or []

    lines: List[str] = []
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

        # Event type hints can appear in multiple places depending on extraction coverage.
        mfl_type = _get(f, "details", "mfl_type") or _get(f, "details", "payload", "mfl_type")
        payload_type = _get(f, "details", "payload", "mfl_type")
        raw_type = _get(f, "details", "raw_mfl", "type")

        norm = _get(f, "details", "normalized") or {}
        add_ids = _as_list(norm.get("add_player_ids"))
        drop_ids = _as_list(norm.get("drop_player_ids"))
        bid_amount = norm.get("bid_amount")

        # ----------------------------
        # BBID waiver + award formatting
        # ----------------------------
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

        # ----------------------------
        # Free agent formatting
        # ----------------------------
        # FREE_AGENT: render based on event_type alone.
        # This is deterministic (your system already classified the event_type).
        if et == "TRANSACTION_FREE_AGENT":
            # If we don't have normalized add/drop, still render safely.
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

        # ----------------------------
        # Trade formatting
        # ----------------------------
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


def render_recap_from_enriched_path_v1(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        artifact = json.load(f)
    return render_recap_from_facts_v1(artifact)
