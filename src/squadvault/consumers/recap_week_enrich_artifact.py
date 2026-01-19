#!/usr/bin/env python3
"""
recap_week_enrich_artifact.py

Purpose:
- Compute deterministic "What happened (facts)" bullets for a given week (non-quiet only)
- Prepend them to the latest WEEKLY_RECAP artifact's rendered_text
- Write the updated rendered_text back to recap_artifacts

Flags:
- --remove-facts-block    : strip an existing facts block (if present) and write back
- --rewrite-facts-block   : remove existing facts block (if present) then regenerate + prepend fresh block
- --min-events-for-facts N: override quiet-week gating threshold (default: deterministic_bullets_v1.QUIET_WEEK_MIN_EVENTS)

Design constraints:
- Deterministic (ordering + content)
- No inference / no hallucination
- Only uses canonical selection + best_memory_event_id payload_json + directory tables
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple


# -------------------------
# Small utilities
# -------------------------

FACTS_HEADER = "What happened (facts)"
RECAP_HEADER_PREFIX = "SquadVault Weekly Recap"


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def _norm_id(raw: Any) -> str:
    s = "" if raw is None else str(raw).strip()
    if not s:
        return ""
    if s.isdigit():
        return s.lstrip("0") or "0"
    return s


def _safe_str(v: Any, default: str = "") -> str:
    if v is None:
        return default
    try:
        return str(v)
    except Exception:
        return default


def _has_column(cols: Sequence[str], name: str) -> bool:
    return name in set(cols)


def _ascii_punct(s: str) -> str:
    # Normalize curly apostrophe and common unicode dashes for stable exports/terminals.
    return s.replace("\u2019", "'").replace("\u2013", "-").replace("\u2014", "-")


def _facts_provenance_line(sel: Any) -> str:
    """
    Deterministic provenance line for the facts block.
    Uses only selection/window fields; no inference.
    """
    w = getattr(sel, "window", None)
    mode = getattr(w, "mode", None) if w is not None else None
    start = getattr(w, "window_start", None) if w is not None else None
    end = getattr(w, "window_end", None) if w is not None else None
    reason = getattr(w, "reason", None) if w is not None else None
    fp = getattr(sel, "fingerprint", None)

    parts = [
        f"mode={mode}",
        f"window={start}→{end}",
        f"fingerprint={fp}",
    ]
    if reason:
        parts.append(f"reason={reason}")
    return "(" + "Selection: " + " ".join(parts) + ")"


def _selection_allows_facts(sel: Any) -> bool:
    """
    Facts are only allowed when the selection window is a safe LOCK_TO_LOCK with non-empty bounds.
    This prevents writing facts under UNSAFE/degenerate windows.
    """
    w = getattr(sel, "window", None)
    mode = getattr(w, "mode", None) if w is not None else None
    start = getattr(w, "window_start", None) if w is not None else None
    end = getattr(w, "window_end", None) if w is not None else None
    return (mode == "LOCK_TO_LOCK") and bool(start) and bool(end)


# -------------------------
# Directory lookups (deterministic)
# -------------------------

class DirLookup:
    """
    Deterministic directory lookup for names.
    Tries exact id, then normalized (strip leading zeros).
    Caches results.
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

        out = _ascii_punct(name or key)  # stable fallback to id
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

        out = _ascii_punct(name or key)  # stable fallback to id
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
        v = row[0]
        return "" if v is None else str(v)


# -------------------------
# Canonical + memory fetch
# -------------------------

def _fetch_canonical_rows_by_ids(
    db_path: str,
    league_id: str,
    season: int,
    canonical_ids: List[str],
) -> List[Dict[str, Any]]:
    if not canonical_ids:
        return []

    CHUNK = 500
    out: List[Dict[str, Any]] = []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    for i in range(0, len(canonical_ids), CHUNK):
        chunk = canonical_ids[i : i + CHUNK]
        placeholders = ",".join(["?"] * len(chunk))
        cur.execute(
            f"""
            SELECT
              id AS canonical_id,
              occurred_at,
              event_type,
              best_memory_event_id
            FROM canonical_events
            WHERE league_id = ?
              AND season = ?
              AND id IN ({placeholders})
            """,
            [league_id, season, *chunk],
        )
        out.extend(_row_to_dict(r) for r in cur.fetchall())

    conn.close()
    return out


def _fetch_memory_payloads_by_ids(
    db_path: str,
    memory_event_ids: List[int],
) -> Dict[int, Dict[str, Any]]:
    if not memory_event_ids:
        return {}

    CHUNK = 500
    out: Dict[int, Dict[str, Any]] = {}
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    for i in range(0, len(memory_event_ids), CHUNK):
        chunk = memory_event_ids[i : i + CHUNK]
        placeholders = ",".join(["?"] * len(chunk))
        cur.execute(
            f"""
            SELECT id, payload_json
            FROM memory_events
            WHERE id IN ({placeholders})
            """,
            list(chunk),
        )
        for r in cur.fetchall():
            d = _row_to_dict(r)
            raw = d.get("payload_json") or ""
            payload: Dict[str, Any] = {}
            if isinstance(raw, str) and raw.strip():
                try:
                    val = json.loads(raw)
                    payload = val if isinstance(val, dict) else {}
                except Exception:
                    payload = {}
            out[int(d["id"])] = payload

    conn.close()
    return out


# -------------------------
# Artifact read/update
# -------------------------

def _recap_artifacts_columns(conn: sqlite3.Connection) -> List[str]:
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(recap_artifacts);")
    rows = cur.fetchall()
    return [r[1] for r in rows]  # (cid, name, type, notnull, dflt_value, pk)


def _fetch_latest_weekly_recap_artifact_row(
    conn: sqlite3.Connection,
    league_id: str,
    season: int,
    week_index: int,
) -> Optional[Dict[str, Any]]:
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
    return None if row is None else _row_to_dict(row)


def _update_rendered_text(
    conn: sqlite3.Connection,
    cols: Sequence[str],
    *,
    league_id: str,
    season: int,
    week_index: int,
    version: int,
    new_rendered_text: str,
) -> None:
    if not _has_column(cols, "rendered_text"):
        raise RuntimeError("recap_artifacts table has no 'rendered_text' column; cannot update.")

    cur = conn.cursor()
    cur.execute(
        """
        UPDATE recap_artifacts
        SET rendered_text = ?
        WHERE league_id = ?
          AND season = ?
          AND week_index = ?
          AND artifact_type = 'WEEKLY_RECAP'
          AND version = ?
        """,
        (new_rendered_text, league_id, season, week_index, version),
    )
    conn.commit()


# -------------------------
# Deterministic facts block
# -------------------------

def build_deterministic_facts_block_v1(
    *,
    db_path: str,
    league_id: str,
    season: int,
    canonical_ids: List[str],
    sel: Any,
    min_events_for_facts: Optional[int] = None,
) -> str:
    """
    Deterministic 'What happened (facts)' block.
    Uses deterministic bullets module, fed by canonical rows + memory payloads + directory lookups.

    Gating:
    - Facts are only emitted for safe LOCK_TO_LOCK windows (sel.window)
    - By default uses deterministic_bullets_v1.QUIET_WEEK_MIN_EVENTS
    - If min_events_for_facts is provided, overrides the threshold deterministically.
    """
    from squadvault.recaps.deterministic_bullets_v1 import (
        CanonicalEventRow,
        QUIET_WEEK_MIN_EVENTS,
        render_deterministic_bullets_v1,
    )

    # Hard safety gate: never write facts under UNSAFE/nonstandard windows.
    if not _selection_allows_facts(sel):
        return ""

    threshold = QUIET_WEEK_MIN_EVENTS if min_events_for_facts is None else int(min_events_for_facts)
    if len(canonical_ids) < threshold:
        return ""

    # If canonical_ids are string keys (current system), use deterministic parsing fallback.
    # If they are numeric IDs (legacy), you can keep the DB lookup path.
    facts_bullets = _facts_from_canonical_id_strings(canonical_ids)

    # Fallback path: emit deterministic bullets derived solely from canonical_id strings.
    # No payload lookups, no inference.
    if facts_bullets:
        facts_bullets = [_ascii_punct(b) for b in facts_bullets]
        prov = _facts_provenance_line(sel)
        lines: List[str] = [FACTS_HEADER, prov]
        lines.extend([f"- {b}" for b in facts_bullets])
        return "\n".join(lines) + "\n\n"

    # If fallback produced nothing, return empty (silence over noise).
    return ""


def _facts_from_canonical_id_strings(canonical_ids: list[str]) -> list[str]:
    """
    Deterministic fallback: derive minimal facts bullets from canonical_id strings.

    No inference. No names. No fabricated context.
    Only parse what is embedded in the canonical_id itself.
    """
    bullets: list[str] = []

    for cid in canonical_ids:
        # Format is "EVENT_TYPE:..." — keep it robust
        parts = cid.split(":")
        if not parts:
            continue

        event_type = parts[0]

        if event_type == "WAIVER_BID_AWARDED":
            # Example seen: WAIVER_BID_AWARDED:70985:2023:2023-09-21T01:00:00Z:0003:13168:20.0
            # We'll pull the last two fields as (player_id, bid) if present.
            if len(parts) >= 2:
                player_id = parts[-2] if len(parts) >= 2 else "UNKNOWN"
                bid = parts[-1] if len(parts) >= 1 else "UNKNOWN"
                bullets.append(f"Waiver awarded: player {player_id} for {bid}.")

        elif event_type == "TRANSACTION_FREE_AGENT":
            # Example seen: ...:ADD:16150:DROP:13139 (but sometimes missing)
            add_id = None
            drop_id = None
            for i, p in enumerate(parts):
                if p == "ADD" and i + 1 < len(parts) and parts[i + 1]:
                    add_id = parts[i + 1]
                if p == "DROP" and i + 1 < len(parts) and parts[i + 1]:
                    drop_id = parts[i + 1]
            if add_id or drop_id:
                if add_id and drop_id:
                    bullets.append(f"Free agent move: added {add_id}, dropped {drop_id}.")
                elif add_id:
                    bullets.append(f"Free agent move: added {add_id}.")
                else:
                    bullets.append(f"Free agent move: dropped {drop_id}.")

        elif event_type == "TRANSACTION_TRADE":
            # Example seen: TRANSACTION_TRADE:70985:2023:MEMORY_EVENT_ID:1078
            mid = None
            for i, p in enumerate(parts):
                if p == "MEMORY_EVENT_ID" and i + 1 < len(parts):
                    mid = parts[i + 1]
                    break
            if mid:
                bullets.append(f"Trade completed (memory_event_id {mid}).")
            else:
                bullets.append("Trade completed.")

        # Otherwise: intentionally silent for all other TRANSACTION_* noise.

    return bullets

def _already_has_facts_block(existing_text: str) -> bool:
    prefix = "\n".join(existing_text.splitlines()[:60])
    return FACTS_HEADER in prefix


def _strip_facts_block(existing_text: str) -> str:
    """
    If a facts block exists at/near the top, remove it deterministically by cutting
    from the recap header onward (robust even if bullets contain blank lines).
    """
    if not existing_text:
        return existing_text
    idx = existing_text.find(RECAP_HEADER_PREFIX)
    if idx == -1:
        return existing_text
    return existing_text[idx:]


def _prepend_block(existing: str, block: str, *, force: bool) -> str:
    if not block.strip():
        return existing
    if not existing:
        return block
    if not force and _already_has_facts_block(existing):
        return existing
    return block + existing


# -------------------------
# Main
# -------------------------

def main() -> int:
    p = argparse.ArgumentParser(description="Enrich a weekly recap artifact by adding deterministic facts bullets.")
    p.add_argument("--db", required=True)
    p.add_argument("--league-id", required=True)
    p.add_argument("--season", type=int, required=True)
    p.add_argument("--week-index", type=int, required=True)

    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute and print the would-be rendered_text, but do not write to the DB.",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Prepend facts even if a facts block appears to already exist.",
    )
    p.add_argument(
        "--remove-facts-block",
        action="store_true",
        help="Remove the facts block if present (no regeneration).",
    )
    p.add_argument(
        "--rewrite-facts-block",
        action="store_true",
        help="Remove the facts block if present, then regenerate and prepend a fresh one.",
    )
    p.add_argument(
        "--min-events-for-facts",
        type=int,
        default=None,
        help="Override quiet-week gating. Require at least N canonical events to emit a facts block.",
    )

    args = p.parse_args()

    if args.remove_facts_block and args.rewrite_facts_block:
        raise SystemExit("Choose only one: --remove-facts-block OR --rewrite-facts-block")

    from squadvault.recaps.select_weekly_recap_events_v1 import select_weekly_recap_events_v1

    conn = sqlite3.connect(args.db)
    cols = _recap_artifacts_columns(conn)

    art = _fetch_latest_weekly_recap_artifact_row(
        conn,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
    )
    if art is None:
        conn.close()
        raise SystemExit("No WEEKLY_RECAP artifact found for this week (recap_artifacts latest is missing).")

    version = int(art.get("version"))
    existing_text = art.get("rendered_text") or ""

    # Mode: remove only
    if args.remove_facts_block:
        updated = _strip_facts_block(existing_text)

        if args.dry_run:
            print(updated)
            conn.close()
            return 0

        _update_rendered_text(
            conn,
            cols,
            league_id=args.league_id,
            season=args.season,
            week_index=args.week_index,
            version=version,
            new_rendered_text=updated,
        )
        conn.close()
        print(
            f"recap_week_enrich_artifact: OK (removed facts block) "
            f"(league={args.league_id} season={args.season} week={args.week_index} version={version})",
            file=sys.stderr,
        )
        return 0

    # For rewrite or default prepend: we need selection + a fresh facts block.
    sel = select_weekly_recap_events_v1(
        db_path=args.db,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
    )
    canonical_ids = list(sel.canonical_ids or [])

    facts_block = build_deterministic_facts_block_v1(
        db_path=args.db,
        league_id=args.league_id,
        season=args.season,
        canonical_ids=canonical_ids,
        sel=sel,
        min_events_for_facts=args.min_events_for_facts,
    )

    if args.rewrite_facts_block:
        base = _strip_facts_block(existing_text)
        updated = _prepend_block(base, facts_block, force=True)
    else:
        updated = _prepend_block(existing_text, facts_block, force=args.force)

    if args.dry_run:
        print(updated)
        conn.close()
        return 0

    _update_rendered_text(
        conn,
        cols,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
        version=version,
        new_rendered_text=updated,
    )
    conn.close()

    action = "rewrote facts block" if args.rewrite_facts_block else "enriched"
    print(
        f"recap_week_enrich_artifact: OK ({action}) "
        f"(league={args.league_id} season={args.season} week={args.week_index} version={version})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
