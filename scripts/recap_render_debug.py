#!/usr/bin/env python3

import argparse
import json
import sqlite3
import sys
from typing import Any, Dict, List, Optional, Tuple


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}

def _extract_artifact_window_from_rendered_text(rendered_text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Best-effort: parse the first 'Window: <start> → <end>' line from rendered_text.
    Returns (start, end) or (None, None) if not found.
    """
    if not rendered_text:
        return (None, None)

    for line in rendered_text.splitlines()[:80]:
        line = line.strip()
        if line.startswith("Window: "):
            rest = line[len("Window: ") :].strip()
            if "→" in rest:
                left, right = rest.split("→", 1)
                return (left.strip() or None, right.strip() or None)
            if "->" in rest:
                left, right = rest.split("->", 1)
                return (left.strip() or None, right.strip() or None)
    return (None, None)

def _fetch_latest_weekly_recap_artifact(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT *
        FROM recap_artifacts
        WHERE league_id = ?
          AND season = ?
          AND week_index = ?
          AND artifact_type = 'WEEKLY_RECAP'
        ORDER BY version DESC
        LIMIT 1
        """,
        (league_id, season, week_index),
    )
    row = cur.fetchone()
    conn.close()
    return None if row is None else _row_to_dict(row)


def _fetch_weekly_recap_artifact_by_version(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
    version: int,
) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT *
        FROM recap_artifacts
        WHERE league_id = ?
          AND season = ?
          AND week_index = ?
          AND artifact_type = 'WEEKLY_RECAP'
          AND version = ?
        LIMIT 1
        """,
        (league_id, season, week_index, version),
    )
    row = cur.fetchone()
    conn.close()
    return None if row is None else _row_to_dict(row)


def _fetch_approved_weekly_recap_artifact(
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT *
        FROM recap_artifacts
        WHERE league_id = ?
          AND season = ?
          AND week_index = ?
          AND artifact_type = 'WEEKLY_RECAP'
          AND state = 'APPROVED'
        ORDER BY version DESC
        LIMIT 1
        """,
        (league_id, season, week_index),
    )
    row = cur.fetchone()
    conn.close()
    return None if row is None else _row_to_dict(row)


# -------------------------
# Deterministic facts prepend (debug)
# -------------------------

class CanonicalEventRow:
    def __init__(self, canonical_id: str, occurred_at: str, event_type: str, payload: Dict[str, Any]):
        self.canonical_id = canonical_id
        self.occurred_at = occurred_at
        self.event_type = event_type
        self.payload = payload


def _fetch_canonical_events_by_ids(
    db_path: str, league_id: str, season: int, canonical_ids: List[int]
) -> List[Dict[str, Any]]:
    if not canonical_ids:
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    placeholders = ",".join(["?"] * len(canonical_ids))
    cur.execute(
        f"""
        SELECT id, league_id, season, event_type, occurred_at, best_memory_event_id
        FROM canonical_events
        WHERE league_id = ?
          AND season = ?
          AND id IN ({placeholders})
        ORDER BY occurred_at, event_type, id
        """,
        (league_id, season, *canonical_ids),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def _fetch_memory_payloads_by_ids(db_path: str, mem_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    if not mem_ids:
        return {}
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    placeholders = ",".join(["?"] * len(mem_ids))
    cur.execute(
        f"""
        SELECT id, payload_json
        FROM memory_events
        WHERE id IN ({placeholders})
        """,
        tuple(mem_ids),
    )
    out: Dict[int, Dict[str, Any]] = {}
    for r in cur.fetchall():
        mid = int(r["id"])
        try:
            out[mid] = json.loads(r["payload_json"])
        except Exception:
            out[mid] = {}
    conn.close()
    return out


def _prepend_deterministic_facts_block(
    *,
    db_path: str,
    league_id: str,
    season: int,
    week_index: int,
) -> str:
    """
    Debug-only: recompute selection and render deterministic bullets.
    This does NOT mutate the DB; it just prints a facts block + newline.
    """
    from squadvault.core.recaps.selection.weekly_selection_v1 import select_weekly_recap_events_v1
    from squadvault.recaps.deterministic_bullets_v1 import render_deterministic_bullets_v1

    sel = select_weekly_recap_events_v1(
        db_path=db_path,
        league_id=str(league_id),
        season=int(season),
        week_index=int(week_index),
    )
    canonical_ids = [int(x) for x in (sel.canonical_ids or [])]
    if not canonical_ids:
        return ""

    canon_rows = _fetch_canonical_events_by_ids(db_path, str(league_id), int(season), canonical_ids)
    mem_ids = sorted({int(r["best_memory_event_id"]) for r in canon_rows if r.get("best_memory_event_id") is not None})
    mem_payload_by_id = _fetch_memory_payloads_by_ids(db_path, mem_ids)

    rows: List[CanonicalEventRow] = []
    for r in canon_rows:
        mid = r.get("best_memory_event_id")
        payload = mem_payload_by_id.get(int(mid), {}) if mid is not None else {}
        rows.append(
            CanonicalEventRow(
                canonical_id=str(r["id"]),
                occurred_at=r.get("occurred_at") or "",
                event_type=r["event_type"],
                payload=payload,
            )
        )

    # ---- render bullets (debug: resolvers may be absent; deterministic_bullets handles gracefully) ----
    bullets = render_deterministic_bullets_v1(
        rows,
        team_resolver=None,
        player_resolver=None,
    )

    if not bullets:
        return ""

    return "What happened (facts)\n" + "\n".join(f"- {b}" for b in bullets) + "\n\n"


def _print_live_window_to_stderr(db_path: str, league_id: str, season: int, week_index: int) -> None:
    """
    Debug: show what the current window_for_week_index computes *today*.
    Useful when stored artifacts have a window baked in that may differ from live logic.
    """
    from squadvault.core.recaps.selection.weekly_windows_v1 import window_for_week_index

    w = window_for_week_index(
        db_path=db_path,
        league_id=str(league_id),
        season=int(season),
        week_index=int(week_index),
    )
    # Use getattr for forwards-compat if fields evolve.
    print(
        "LIVE WINDOW: "
        f"mode={getattr(w, 'mode', None)} "
        f"week_index={getattr(w, 'week_index', None)} "
        f"window_start={getattr(w, 'window_start', None)} "
        f"window_end={getattr(w, 'window_end', None)} "
        f"start_lock={getattr(w, 'start_lock', None)} "
        f"next_lock={getattr(w, 'next_lock', None)} "
        f"reason={getattr(w, 'reason', None)}",
        file=sys.stderr,
    )


def _print_rendered_text_or_die(artifact: Dict[str, Any]) -> None:
    rendered = artifact.get("rendered_text")
    if not rendered:
        raise SystemExit("Artifact missing rendered_text; cannot render.")
    print(rendered)


def main() -> None:
    p = argparse.ArgumentParser(description="Render (view) a weekly recap artifact (debug helper)")
    p.add_argument("--db", required=True)
    p.add_argument("--league-id", required=True)
    p.add_argument("--season", type=int, required=True)
    p.add_argument("--week-index", type=int, required=True)

    p.add_argument(
        "--approved-only",
        action="store_true",
        help="Render ONLY an APPROVED recap artifact; error if none exists.",
    )
    p.add_argument(
        "--version",
        type=int,
        default=None,
        help="Render a specific recap artifact version (overrides latest).",
    )
    p.add_argument(
        "--suppress-render-warning",
        action="store_true",
        help="Suppress warning when rendering latest artifact without approval gate (internal use only).",
    )

    # Debug add-ons
    p.add_argument(
        "--prepend-deterministic-facts",
        action="store_true",
        help="Debug: recompute selection and prepend deterministic facts bullets to stdout.",
    )
    p.add_argument(
        "--show-live-window",
        action="store_true",
        help="Debug: print current live window_for_week_index() to stderr.",
    )

    args = p.parse_args()

    # Priority order:
    # 1) explicit version
    # 2) approved-only
    # 3) latest (any state)

    artifact: Optional[Dict[str, Any]] = None

    if args.version is not None:
        artifact = _fetch_weekly_recap_artifact_by_version(
            db_path=args.db,
            league_id=args.league_id,
            season=args.season,
            week_index=args.week_index,
            version=args.version,
        )
        if artifact is None:
            raise SystemExit(f"No WEEKLY_RECAP artifact found for version={args.version}.")
    elif args.approved_only:
        artifact = _fetch_approved_weekly_recap_artifact(
            db_path=args.db,
            league_id=args.league_id,
            season=args.season,
            week_index=args.week_index,
        )
        if artifact is None:
            raise SystemExit(
                "No APPROVED WEEKLY_RECAP artifact found for this week. "
                "Refusing to render drafts/ready artifacts."
            )
    else:
        artifact = _fetch_latest_weekly_recap_artifact(
            db_path=args.db,
            league_id=args.league_id,
            season=args.season,
            week_index=args.week_index,
        )
        if artifact is None:
            raise SystemExit("No WEEKLY_RECAP artifacts found for this week.")
        if not args.suppress_render_warning:
            print(
                "WARNING: rendering latest artifact without approval gate. "
                "Use --approved-only for any UI/export path.",
                file=sys.stderr,
            )

    if artifact is None:
        raise SystemExit("Unexpected: no artifact selected to render.")

    if args.show_live_window:
        _print_live_window_to_stderr(args.db, args.league_id, args.season, args.week_index)

        art_text = artifact.get("rendered_text") or ""
        a_start, a_end = _extract_artifact_window_from_rendered_text(art_text)
        print(
            f"ARTIFACT WINDOW: start={a_start} end={a_end}",
            file=sys.stderr,
        )

    if args.prepend_deterministic_facts:
        facts = _prepend_deterministic_facts_block(
            db_path=args.db,
            league_id=args.league_id,
            season=args.season,
            week_index=args.week_index,
        )
        if facts:
            print(facts, end="")

    _print_rendered_text_or_die(artifact)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
