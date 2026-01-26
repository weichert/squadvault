#!/usr/bin/env python3
from __future__ import annotations

def _persist_rivalry_draft_v1(
    *,
    db_path: str,
    league_id: int,
    season: int,
    week_index: int,
    selection_fingerprint: str,
    window_start: str | None,
    window_end: str | None,
    rendered_text: str,
    created_by: str,
) -> dict:
    """
    Persist a DRAFT recap_artifacts row for RIVALRY_CHRONICLE_V1.

    Notes:
    - This is intentionally local to the consumer (no core engine modifications).
    - Version increments monotonically per (league_id, season, week_index, artifact_type).
    """
    import sqlite3

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        row = con.execute(
            """
            SELECT COALESCE(MAX(version), 0) AS mx
            FROM recap_artifacts
            WHERE league_id=? AND season=? AND week_index=? AND artifact_type=?
            """,
            (str(league_id), int(season), int(week_index), "RIVALRY_CHRONICLE_V1"),
        ).fetchone()
        next_v = int(row["mx"] or 0) + 1

        con.execute(
            """
            INSERT INTO recap_artifacts (
              league_id, season, week_index, artifact_type,
              version, state,
              selection_fingerprint, window_start, window_end,
              rendered_text, created_by
            )
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                str(league_id),
                int(season),
                int(week_index),
                "RIVALRY_CHRONICLE_V1",
                int(next_v),
                "DRAFT",
                str(selection_fingerprint),
                (str(window_start) if window_start else None),
                (str(window_end) if window_end else None),
                str(rendered_text),
                str(created_by),
            ),
        )
        con.commit()

        return {
            "league_id": int(league_id),
            "season": int(season),
            "week_index": int(week_index),
            "artifact_type": "RIVALRY_CHRONICLE_V1",
            "version": int(next_v),
            "state": "DRAFT",
            "selection_fingerprint": str(selection_fingerprint),
        }
    finally:
        con.close()


import argparse
import hashlib
import json
import sqlite3
import sys
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from squadvault.core.recaps.selection.weekly_windows_v1 import window_for_week_index

from squadvault.core.recaps.recap_artifacts import create_recap_artifact_draft_idempotent, ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1


def _sv_call_with_signature_filter(fn, **kwargs):
    """
    Call fn(**kwargs) but only pass parameters that exist in fn's signature.

    This avoids hard-coding store function arg names while keeping behavior deterministic.
    """
    import inspect
    sig = inspect.signature(fn)
    accepted = set(sig.parameters.keys())
    filtered = {k: v for k, v in kwargs.items() if k in accepted}
    return fn(**filtered)


MATCHUP_EVENT_TYPES = ("MATCHUP_RESULT", "WEEKLY_MATCHUP_RESULT")


@dataclass(frozen=True)
class RivalryChronicleRequest:
    db: str
    league_id: int
    season: int
    team_a_id: int
    team_b_id: int
    start_week: int
    end_week: int
    requested_at_utc: Optional[str] = None
    out: Optional[str] = None


def _db_connect(db_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    return con


def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _canon_json(obj: Any) -> str:
    # Deterministic serialization (stable fingerprint input)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _walk_values(x: Any) -> List[Any]:
    out: List[Any] = []
    if isinstance(x, dict):
        for k in sorted(x.keys(), key=lambda z: str(z)):
            out.extend(_walk_values(x[k]))
    elif isinstance(x, list):
        for it in x:
            out.extend(_walk_values(it))
    else:
        out.append(x)
    return out


def _payload_mentions_team(payload: Dict[str, Any], team_id: int) -> bool:
    # Strict equality match against either int or str occurrences, recursively.
    tid_int = int(team_id)
    tid_str = str(team_id)
    for v in _walk_values(payload):
        try:
            if isinstance(v, bool):
                continue
            if isinstance(v, int) and int(v) == tid_int:
                return True
            if isinstance(v, str) and v.strip() == tid_str:
                return True
        except Exception:
            continue
    return False



def _detect_canonical_events_payload_col(con: sqlite3.Connection) -> Optional[str]:
    """
    Autodetect the JSON payload column name for canonical_events.

    We do NOT assume schema; we detect deterministically via PRAGMA.
    Preference order is stable.
    """
    cols = [str(r["name"]) for r in con.execute("PRAGMA table_info(canonical_events)").fetchall()]
    # stable preference order
    for cand in ("payload_json", "payload", "action_payload_json", "payload_blob", "payload_text"):
        if cand in cols:
            return cand
    return None


# cached per-process (deterministic)
_CANON_PAYLOAD_COL: Optional[str] = None


def _payload_col(con: sqlite3.Connection) -> Optional[str]:
    global _CANON_PAYLOAD_COL
    if _CANON_PAYLOAD_COL is None:
        _CANON_PAYLOAD_COL = _detect_canonical_events_payload_col(con)
    return _CANON_PAYLOAD_COL

def _fetch_matchup_events_for_window(
    con: sqlite3.Connection,
    league_id: int,
    season: int,
    window_start: str,
    window_end: str,
) -> List[Tuple[int, str, str, Dict[str, Any]]]:
    # Returns: (canonical_event_id, event_type, occurred_at, payload_dict)

    # Robust schema autodetect: probe candidate payload columns by attempting a SELECT.
    # This avoids assuming canonical_events column names (payload_json vs payload, etc.).
    candidates = ("payload_json", "payload", "action_payload_json", "payload_text", "payload_blob")
    chosen: Optional[str] = None
    for cand in candidates:
        try:
            con.execute(f"SELECT {cand} FROM canonical_events LIMIT 1")
            chosen = cand
            break
        except sqlite3.OperationalError:
            continue

    payload_select = f"{chosen} AS payload_any" if chosen else "NULL AS payload_any"

    rows = con.execute(
        f"""
        SELECT id, event_type, occurred_at, {payload_select}
        FROM canonical_events
        WHERE league_id=? AND season=?
          AND occurred_at IS NOT NULL
          AND occurred_at >= ? AND occurred_at < ?
          AND event_type IN ({",".join(["?"] * len(MATCHUP_EVENT_TYPES))})
        ORDER BY occurred_at ASC, event_type ASC, id ASC
        """,
        (str(league_id), int(season), str(window_start), str(window_end), *MATCHUP_EVENT_TYPES),
    ).fetchall()

    out: List[Tuple[int, str, str, Dict[str, Any]]] = []
    for r in rows:
        cid = int(r["id"])
        et = str(r["event_type"] or "")
        oa = str(r["occurred_at"] or "")
        raw = r["payload_any"]
        if raw is None:
            payload = {}
        else:
            raw_s = str(raw)
            try:
                payload = json.loads(raw_s) if raw_s else {}
                if not isinstance(payload, dict):
                    payload = {}
            except Exception:
                payload = {}
        out.append((cid, et, oa, payload))
    return out


def _extract_optional_scores(payload: Dict[str, Any], team_a_id: int, team_b_id: int) -> Dict[str, Any]:
    # Only include fields if they already exist in canonical payload.
    # We do not infer which side is home/away; we only surface obvious keys.
    out: Dict[str, Any] = {}

    # Common patterns (best-effort, deterministic, optional)
    for k in ("winner_team_id", "winner_franchise_id", "winner_id"):
        if k in payload and payload[k] is not None:
            out["winner_team_id"] = str(payload[k])
            break

    # Try common score key names; include as strings to preserve exact canonical representation.
    for a_key, b_key in (
        ("team_a_score", "team_b_score"),
        ("a_score", "b_score"),
        ("score_a", "score_b"),
        ("home_score", "away_score"),
        ("team1_score", "team2_score"),
    ):
        if a_key in payload and b_key in payload:
            out["team_a_score"] = str(payload[a_key])
            out["team_b_score"] = str(payload[b_key])
            break

    # If canonical payload includes explicit team ids, surface them (optional)
    for k in ("team_a_id", "teamA_id", "franchise_a_id", "team1_id"):
        if k in payload and payload[k] is not None:
            out["team_a_id_raw"] = str(payload[k])
            break
    for k in ("team_b_id", "teamB_id", "franchise_b_id", "team2_id"):
        if k in payload and payload[k] is not None:
            out["team_b_id_raw"] = str(payload[k])
            break

    return out


def build_facts_only_payload(req: RivalryChronicleRequest) -> Dict[str, Any]:
    facts: List[Dict[str, Any]] = []
    covered_weeks: List[int] = []
    withheld_weeks: List[Dict[str, Any]] = []

    con = _db_connect(req.db)
    try:
        for week_index in range(int(req.start_week), int(req.end_week) + 1):
            w = window_for_week_index(
                db_path=req.db,
                league_id=str(req.league_id),
                season=int(req.season),
                week_index=int(week_index),
            )

            if str(w.mode) == "UNSAFE":
                withheld_weeks.append(
                    {
                        "week_index": int(week_index),
                        "reason": str(w.reason or "UNSAFE"),
                    }
                )
                continue

            covered_weeks.append(int(week_index))

            ws = str(w.window_start or "")
            we = str(w.window_end or "")
            if not ws or not we:
                # Should not happen in non-UNSAFE modes, but stay silent and deterministic.
                withheld_weeks.append(
                    {
                        "week_index": int(week_index),
                        "reason": "WINDOW_UNSAFE_TO_COMPUTE",
                    }
                )
                continue

            events = _fetch_matchup_events_for_window(
                con,
                league_id=req.league_id,
                season=req.season,
                window_start=ws,
                window_end=we,
            )

            for canonical_event_id, event_type, occurred_at, payload in events:
                if not _payload_mentions_team(payload, req.team_a_id):
                    continue
                if not _payload_mentions_team(payload, req.team_b_id):
                    continue

                row: Dict[str, Any] = {
                    "week_index": int(week_index),
                    "canonical_event_id": int(canonical_event_id),
                    "event_type": str(event_type),
                    "occurred_at": str(occurred_at),
                }

                # Optional fields only if present in canonical payload (no inference)
                row.update(_extract_optional_scores(payload, req.team_a_id, req.team_b_id))

                facts.append(row)

    finally:
        con.close()

    # Deterministic ordering (belt-and-suspenders)
    facts.sort(key=lambda r: (int(r.get("week_index", 0)), int(r.get("canonical_event_id", 0))))

    facts_fingerprint = _sha256_hex(_canon_json(facts))

    payload: Dict[str, Any] = {
        "version": "v1.0",
        "league_id": int(req.league_id),
        "season": int(req.season),
        "team_a_id": int(req.team_a_id),
        "team_b_id": int(req.team_b_id),
        "start_week_index": int(req.start_week),
        "end_week_index": int(req.end_week),
        "covered_weeks": covered_weeks,
        "withheld_weeks": withheld_weeks,
        "facts": facts,
        "facts_fingerprint": facts_fingerprint,
    }

    # Metadata-only (allowed)
    if req.requested_at_utc:
        payload["requested_at_utc"] = str(req.requested_at_utc)

    # Narrative intentionally omitted in Lock B.

    return payload


def _parse_args(argv: List[str]) -> RivalryChronicleRequest:
    ap = argparse.ArgumentParser(description="Generate Rivalry Chronicle v1 (facts-only; Lock B)")
    ap.add_argument("--db", required=True, help="Path to SQLite db")
    ap.add_argument("--league-id", type=int, required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--team-a-id", type=int, required=True)
    ap.add_argument("--team-b-id", type=int, required=True)
    ap.add_argument("--start-week", type=int, required=True)
    ap.add_argument("--end-week", type=int, required=True)
    ap.add_argument("--requested-at-utc", default=None, help="Optional: metadata only (ISO-8601 UTC)")
    ap.add_argument("--out", default=None, help="Optional: write payload JSON to this path")
    args = ap.parse_args(argv)

    return RivalryChronicleRequest(
        db=str(args.db),
        league_id=int(args.league_id),
        season=int(args.season),
        team_a_id=int(args.team_a_id),
        team_b_id=int(args.team_b_id),
        start_week=int(args.start_week),
        end_week=int(args.end_week),
        requested_at_utc=str(args.requested_at_utc) if args.requested_at_utc else None,
        out=str(args.out) if args.out else None,
    )


def main(argv: List[str] | None = None) -> int:
    req = _parse_args(list(argv or []))
    payload = build_facts_only_payload(req)

    # LOCK_C_PERSIST_DRAFT: Persist Rivalry Chronicle draft via existing recap_artifacts semantics.
    # Deterministic compatibility choice: store under week_index = start_week_index.
    selection_fingerprint = str(payload.get("facts_fingerprint") or "")

    # Stable JSON serialization (no whitespace drift)
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))

    # NOTE: window_start/window_end are range-spanning; leave None (silence) unless the store requires otherwise.
    window_start = None
    window_end = None

    con = sqlite3.connect(str(req.db))
    con.row_factory = sqlite3.Row
    try:
        created = _sv_call_with_signature_filter(
            create_recap_artifact_draft_idempotent,
                        db_path=str(req.db),
            rendered_text="",
con=con,
            league_id=int(req.league_id),
            season=int(req.season),
            week_index=int(req.start_week),
            artifact_type=ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
            selection_fingerprint=selection_fingerprint,
            window_start=window_start,
            window_end=window_end,
            artifact_json=payload_json,
            payload_json=payload_json,
            data_json=payload_json,
            created_at_utc=req.requested_at_utc,
            created_by="operator",
            actor="operator",
        )
        # SV_DEBUG: show whether draft was newly created vs idempotent hit
        if isinstance(created, tuple) and len(created) == 2:
            draft_version, created_new = created
        else:
            draft_version, created_new = created, None
    finally:
        con.close()

    # Best-effort operator feedback (do not depend on return shape)
    if isinstance(created, dict):
        v = created.get("version")
    else:
        v = getattr(created, "version", None)
    if v is not None:
        print(f"rivalry_chronicle_v1: Lock C OK (draft persisted) v{v}")
    else:
        print("rivalry_chronicle_v1: Lock C OK (draft persisted)")


    out_json = json.dumps(payload, sort_keys=True, indent=2)

    if req.out:
        from pathlib import Path
        p = Path(req.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(out_json + "\n", encoding="utf-8")
        print(f"rivalry_chronicle_v1: Lock B OK (facts-only) -> {p}")
    else:
        print(out_json)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
