"""Canonicalization engine: deduplicate memory events into canonical events."""

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv(".env")

import hashlib
import json
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from squadvault.core.storage.session import DatabaseSession

DEFAULT_DB_PATH = Path(os.environ.get("SQUADVAULT_DB", ".local_squadvault.sqlite"))  # type: ignore[name-defined]


@dataclass(frozen=True)
class MemoryEventRow:
    id: int
    league_id: str
    season: int
    event_type: str
    occurred_at: str | None
    ingested_at: str
    payload_json: str


def now_iso_z() -> str:
    """Return current UTC time as ISO-8601 Z-suffix string."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_json_loads(s: str) -> dict[str, Any]:
    """Parse JSON string, returning empty dict on failure."""
    try:
        obj = json.loads(s)
        return obj if isinstance(obj, dict) else {"_non_object_payload": obj}
    except (ValueError, TypeError):
        return {"_payload_parse_error": True, "_raw": s}


def norm(v: Any) -> str:
    """Normalize a string for comparison: lowercase, strip whitespace."""
    if v is None:
        return ""
    return str(v).strip()


def sha1_text(s: str) -> str:
    """Compute SHA-1 hex digest of a text string."""
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def raw_mfl_obj(payload: dict[str, Any]) -> dict[str, Any]:
    """
    raw_mfl_json might be:
      - a dict
      - a JSON string (e.g. '{"type":"BBID_WAIVER", ...}')
      - missing / malformed
    Return a dict if possible, else {}.
    """
    raw = payload.get("raw_mfl_json")

    if isinstance(raw, dict):
        return raw

    if isinstance(raw, str):
        s = raw.strip()
        if s.startswith("{") and s.endswith("}"):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, dict):
                    return parsed
            except (ValueError, TypeError):
                return {}

    return {}


def _as_list_str(v: Any) -> list[str]:
    """
    Accepts:
      - list -> list[str]
      - comma-separated string -> list[str]
      - otherwise -> []
    """
    if v is None:
        return []
    if isinstance(v, list):
        out: list[str] = []
        for item in v:
            s = norm(item)
            if s:
                out.append(s)
        return out
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return []
        # allow json-like list strings to still degrade safely
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return _as_list_str(parsed)
            except (ValueError, TypeError):
                pass
        parts = [p.strip() for p in s.split(",")]
        return [p for p in parts if p]
    return []


def _stable_ids_key(ids: list[str]) -> str:
    """
    Stable string for fingerprinting: sorted unique ids joined by ','.
    """
    if not ids:
        return ""
    uniq = sorted(set([norm(x) for x in ids if norm(x)]))
    return ",".join(uniq)


def _parse_free_agent_add_drop_from_raw(payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    """
    Try to parse add/drop player ids from raw MFL transaction field.

    Observed FREE_AGENT pattern:
      "<add_ids>|<drop_ids>"
      e.g. "16207,|14108,"

    Returns (added_ids, dropped_ids), possibly empty lists.
    """
    raw = raw_mfl_obj(payload)
    txn_field = raw.get("transaction") if isinstance(raw, dict) else None
    if not isinstance(txn_field, str) or not txn_field:
        return ([], [])

    parts = txn_field.split("|")
    while len(parts) < 2:
        parts.append("")

    add_part = parts[0]
    drop_part = parts[1] if len(parts) >= 2 else ""

    def split_ids(s: str) -> list[str]:
        """Split a comma-separated ID string into a list of stripped strings."""
        items = [x.strip() for x in s.split(",")]
        return [x for x in items if x]

    return (split_ids(add_part), split_ids(drop_part))


def action_fingerprint(row: MemoryEventRow, payload: dict[str, Any]) -> str:
    """
    Deterministic canonical action key.

    - WAIVER_BID_AWARDED: dedupe + skip stub rows
    - TRANSACTION_FREE_AGENT: dedupe by occurred_at+franchise+add/drop (parsed or raw)
    - Other types: safe default 1:1 by memory_event_id (incremental rollout)
    """
    et = row.event_type
    occurred_at = norm(row.occurred_at)

    # -------------------------
    # WAIVER_BID_AWARDED
    # -------------------------
    if et == "WAIVER_BID_AWARDED":
        franchise_id = norm(payload.get("franchise_id"))
        player_id = norm(payload.get("player_id"))
        bid_amount = norm(payload.get("bid_amount"))
        added = norm(payload.get("players_added_ids"))

        # Detect and drop stub "award" rows that are actually BBID_WAIVER transaction records.
        # These have no award-level fields, but raw_mfl_json.type == "BBID_WAIVER".
        raw_obj = raw_mfl_obj(payload)
        raw_type = norm(raw_obj.get("type"))

        if (not player_id) and (not bid_amount) and (not added) and (raw_type == "BBID_WAIVER"):
            return ""  # empty fingerprint => skip canonicalization for this row

        if player_id:
            return f"{et}:{row.league_id}:{row.season}:{occurred_at}:{franchise_id}:{player_id}:{bid_amount}"

        if added:
            return f"{et}:{row.league_id}:{row.season}:{occurred_at}:{franchise_id}:ADDED:{added}:{bid_amount}"

        # Last resort: stable hash of raw MFL json
        raw_str = ""
        raw = payload.get("raw_mfl_json")
        if isinstance(raw, str):
            raw_str = raw
        elif isinstance(raw, dict):
            raw_str = json.dumps(raw, sort_keys=True, separators=(",", ":"))
        else:
            raw_str = norm(raw)

        if raw_str:
            return f"{et}:{row.league_id}:{row.season}:{occurred_at}:{franchise_id}:RAW:{sha1_text(raw_str)}"

        return f"{et}:{row.league_id}:{row.season}:{occurred_at}:{franchise_id}:PAYLOAD:{sha1_text(row.payload_json)}"

    # -------------------------
    # TRANSACTION_FREE_AGENT
    # -------------------------
    if et == "TRANSACTION_FREE_AGENT":
        franchise_id = norm(payload.get("franchise_id"))

        # Prefer structured add/drop if present
        added_ids = _as_list_str(payload.get("players_added_ids"))
        dropped_ids = _as_list_str(payload.get("players_dropped_ids"))

        # If missing, try to parse from raw_mfl_json.transaction
        if not added_ids and not dropped_ids:
            ra, rd = _parse_free_agent_add_drop_from_raw(payload)
            if ra or rd:
                added_ids = ra
                dropped_ids = rd

        added_key = _stable_ids_key(added_ids)
        dropped_key = _stable_ids_key(dropped_ids)

        # If we have add/drop, this is the best fingerprint
        if added_key or dropped_key:
            return (
                f"{et}:{row.league_id}:{row.season}:{occurred_at}:"
                f"{franchise_id}:ADD:{added_key}:DROP:{dropped_key}"
            )

        # Fallback: player_id + bid (still better than memory_event_id)
        player_id = norm(payload.get("player_id"))
        bid_amount = norm(payload.get("bid_amount"))
        if player_id:
            return f"{et}:{row.league_id}:{row.season}:{occurred_at}:{franchise_id}:PLAYER:{player_id}:BID:{bid_amount}"

        # Last resort: hash raw MFL json (stable)
        raw_str = ""
        raw = payload.get("raw_mfl_json")
        if isinstance(raw, str):
            raw_str = raw
        elif isinstance(raw, dict):
            raw_str = json.dumps(raw, sort_keys=True, separators=(",", ":"))
        else:
            raw_str = norm(raw)

        if raw_str:
            return f"{et}:{row.league_id}:{row.season}:{occurred_at}:{franchise_id}:RAW:{sha1_text(raw_str)}"

        # Absolute last resort
        return f"{et}:{row.league_id}:{row.season}:{occurred_at}:{franchise_id}:PAYLOAD:{sha1_text(row.payload_json)}"

    # -------------------------
    # WEEKLY_MATCHUP_RESULT
    # -------------------------
    if et == "WEEKLY_MATCHUP_RESULT":
        week = norm(payload.get("week"))
        # Use sorted franchise IDs for stable fingerprint regardless of winner/loser ordering
        winner_id = norm(payload.get("winner_franchise_id"))
        loser_id = norm(payload.get("loser_franchise_id"))
        sorted_ids = sorted([winner_id, loser_id])
        return f"{et}:{row.league_id}:{row.season}:W{week}:{sorted_ids[0]}:{sorted_ids[1]}"

    # -------------------------
    # WEEKLY_PLAYER_SCORE
    # -------------------------
    if et == "WEEKLY_PLAYER_SCORE":
        week = norm(payload.get("week"))
        franchise_id = norm(payload.get("franchise_id"))
        player_id = norm(payload.get("player_id"))
        return f"{et}:{row.league_id}:{row.season}:W{week}:{franchise_id}:{player_id}"

    # -------------------------
    # Default safe rollout
    # -------------------------
    return f"{et}:{row.league_id}:{row.season}:MEMORY_EVENT_ID:{row.id}"


def score_event(payload: dict[str, Any], memory_event_id: int) -> int:
    """
    Deterministic "best event" scoring. Higher is better.
    """
    score = 0

    # Hard-penalize stub waiver-award rows (no meaningful fields)
    if (
        not norm(payload.get("player_id"))
        and not norm(payload.get("players_added_ids"))
        and not norm(payload.get("bid_amount"))
    ):
        score -= 1000
        return score

    # Prefer identity fields
    if norm(payload.get("player_id")):
        score += 50
    if norm(payload.get("bid_amount")):
        score += 20

    # Prefer structured add/drop info when available
    if norm(payload.get("players_added_ids")):
        score += 15
    if norm(payload.get("players_dropped_ids")):
        score += 10

    # Prefer more complete raw json (works for dict or string)
    raw = payload.get("raw_mfl_json")
    raw_str = ""
    if isinstance(raw, str):
        raw_str = raw
    elif isinstance(raw, dict):
        raw_str = json.dumps(raw, sort_keys=True, separators=(",", ":"))
    if raw_str:
        score += min(len(raw_str) // 200, 25)  # cap influence

    # Stable tie-breaker: later id wins slightly
    score += (memory_event_id % 10)

    return score


# ---------------------------------------------------------------------------
# CANONICALIZATION SEMANTIC RULE R1 - Championship-week phantom collapse
#
# Adjudicated + ratified 2026-06-23
# (_observations/OBSERVATIONS_2026_06_23_CHAMPIONSHIP_WEEK17_CANONICALIZATION_ADJUDICATION).
#
# For the 2021+ expansion era this league's championship is week 17 (the playoff bracket
# contracts 10 -> 8 -> 4 -> 2 and ENDS at wk17). MFL ALSO reports the decided final again at
# week 18 - a byte-identical trailing/padding copy, not a distinct game. The structural
# `action_fingerprint` dedup does NOT catch it (the fingerprint includes W{week}, so W17 and
# W18 differ), so this is a separate SEMANTIC rule:
#
#   A 2021+ WEEKLY_MATCHUP_RESULT at week 18 whose (sorted franchises, winner_score,
#   loser_score, is_tie) equals a week-17 matchup is a phantom. Its matchup row AND the
#   week-18 WEEKLY_PLAYER_SCORE rows for those two franchises are SUPPRESSED from
#   canonical_events (the derived projection consumers read via v_canonical_best_events).
#
# Invariants (binding, per the adjudication):
#   - Append-only preserved: memory_events keeps BOTH rows unchanged; only the derived
#     canonical projection dedups. Nothing is deleted from the ledger.
#   - Byte-identical only / conservative: keyed on matchup identity at the GAME level. A
#     week-18 matchup with any differing score is NOT a phantom and is kept (the
#     "report league happenings after our championship" case is never dropped).
#   - Deterministic / reconstructable: a pure function of the season's rows; re-canonicalizing
#     the same ledger yields identical canonical output.
#   - 2010-2020 never fires (championship at wk16; no trailing wk18).
# ---------------------------------------------------------------------------
_PHANTOM_ERA_START = 2021


def _matchup_identity(payload: dict[str, Any]) -> tuple[tuple[str, str], str, str, str]:
    """Game-level identity for phantom detection: sorted franchises + scores + tie flag."""
    w = norm(payload.get("winner_franchise_id"))
    lo = norm(payload.get("loser_franchise_id"))
    pair = tuple(sorted((w, lo)))
    return (pair, norm(payload.get("winner_score")), norm(payload.get("loser_score")), norm(payload.get("is_tie")))  # type: ignore[return-value]


def _phantom_memory_event_ids(event_rows: list[MemoryEventRow]) -> set[int]:
    """Memory-event ids of the 2021+ week-18 championship phantom (see R1 above).

    Per season (>= 2021): a week-18 matchup identical to a week-17 matchup is a phantom; its
    matchup row and the week-18 player rows for those two franchises are returned for skipping.
    """
    phantom: set[int] = set()
    by_season: dict[int, list[MemoryEventRow]] = defaultdict(list)
    for r in event_rows:
        by_season[r.season].append(r)

    for season, srows in by_season.items():
        if season < _PHANTOM_ERA_START:
            continue
        wk17_matchups: set[tuple[tuple[str, str], str, str, str]] = set()
        for r in srows:
            if r.event_type == "WEEKLY_MATCHUP_RESULT":
                p = safe_json_loads(r.payload_json)
                if norm(p.get("week")) == "17":
                    wk17_matchups.add(_matchup_identity(p))
        phantom_franchises: set[str] = set()
        for r in srows:
            if r.event_type == "WEEKLY_MATCHUP_RESULT":
                p = safe_json_loads(r.payload_json)
                if norm(p.get("week")) == "18" and _matchup_identity(p) in wk17_matchups:
                    phantom.add(r.id)
                    phantom_franchises.add(norm(p.get("winner_franchise_id")))
                    phantom_franchises.add(norm(p.get("loser_franchise_id")))
        if phantom_franchises:
            for r in srows:
                if r.event_type == "WEEKLY_PLAYER_SCORE":
                    p = safe_json_loads(r.payload_json)
                    if norm(p.get("week")) == "18" and norm(p.get("franchise_id")) in phantom_franchises:
                        phantom.add(r.id)
    return phantom


def canonicalize(league_id: str, season: int, db_path: str | Path | None = None) -> None:
    """
    Canonicalize memory_events into canonical_events for a (league_id, season) scope.

    IMPORTANT:
    - Uses the provided db_path when given.
    - Falls back to env SQUADVAULT_DB, then .local_squadvault.sqlite.
    """
    resolved_db = Path(db_path) if db_path is not None else DEFAULT_DB_PATH

    if not resolved_db.exists():
        raise FileNotFoundError(f"SQLite DB not found at {resolved_db.resolve()}")

    with DatabaseSession(str(resolved_db)) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")

        # ---------------------------------------------------------------------
        # MVP INVARIANT:
        # canonical_events represents CURRENT truth for (league_id, season).
        # It is rebuilt deterministically each run. No accumulated versions.
        # ---------------------------------------------------------------------
        conn.execute("BEGIN;")

        # Delete memberships first (safe even without cascading FKs)
        conn.execute(
            """
            DELETE FROM canonical_membership
            WHERE canonical_event_id IN (
              SELECT id
              FROM canonical_events
              WHERE league_id = ? AND season = ?
            )
            """,
            (league_id, season),
        )

        # Delete canonical rows for this scope
        conn.execute(
            """
            DELETE FROM canonical_events
            WHERE league_id = ? AND season = ?
            """,
            (league_id, season),
        )
        conn.execute("COMMIT;")

        # Now rebuild (single transaction for determinism and speed)
        conn.execute("BEGIN;")

        rows = conn.execute(
            """
            SELECT id, league_id, season, event_type, occurred_at, ingested_at, payload_json
            FROM memory_events
            WHERE league_id = ? AND season = ?
            ORDER BY id
            """,
            (league_id, season),
        ).fetchall()

        event_rows = [
            MemoryEventRow(
                id=int(id_),
                league_id=str(lg),
                season=int(yr),
                event_type=str(et),
                occurred_at=occ,
                ingested_at=str(ing),
                payload_json=str(payload_json),
            )
            for (id_, lg, yr, et, occ, ing, payload_json) in rows
        ]

        # R1: suppress the 2021+ week-18 championship phantom from the canonical projection
        # (ledger untouched; byte-identical-only; deterministic). See the rule doc above.
        phantom_ids = _phantom_memory_event_ids(event_rows)

        processed = 0
        created = 0
        updated_best = 0
        skipped_empty_fingerprint = 0
        skipped_phantom = 0

        for row in event_rows:
            if row.id in phantom_ids:
                skipped_phantom += 1
                continue

            payload = safe_json_loads(row.payload_json)
            fp = action_fingerprint(row, payload)

            # Skip events we intentionally do not canonicalize (e.g., stub waiver "awards")
            if not fp:
                skipped_empty_fingerprint += 1
                continue

            sc = score_event(payload, row.id)

            existing = conn.execute(
                """
                SELECT id, best_memory_event_id, best_score
                FROM canonical_events
                WHERE league_id=? AND season=? AND event_type=? AND action_fingerprint=?
                """,
                (row.league_id, row.season, row.event_type, fp),
            ).fetchone()

            if existing is None:
                cur = conn.execute(
                    """
                    INSERT INTO canonical_events (
                      league_id, season, event_type, action_fingerprint,
                      best_memory_event_id, best_score,
                      selection_version, updated_at,
                      occurred_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
                    """,
                    (
                        row.league_id,
                        row.season,
                        row.event_type,
                        fp,
                        row.id,
                        sc,
                        now_iso_z(),
                        row.occurred_at,
                    ),
                )
                canonical_id = int(cur.lastrowid or 0)
                created += 1
            else:
                canonical_id, best_id, best_score = existing
                canonical_id = int(canonical_id)
                best_id = int(best_id)
                best_score = int(best_score)

                better = (sc > best_score) or (sc == best_score and row.id > best_id)
                if better:
                    conn.execute(
                        """
                        UPDATE canonical_events
                        SET best_memory_event_id=?,
                            best_score=?,
                            selection_version=1,
                            updated_at=?
                        WHERE id=?
                        """,
                        (row.id, sc, now_iso_z(), canonical_id),
                    )
                    updated_best += 1

            # Always set occurred_at (and keep deterministic metadata fresh)
            conn.execute(
                """
                UPDATE canonical_events
                SET best_memory_event_id=?,
                    best_score=?,
                    selection_version=1,
                    updated_at=?,
                    occurred_at=?
                WHERE id=?
                """,
                (row.id, sc, now_iso_z(), row.occurred_at, canonical_id),
            )

            processed += 1

        conn.execute("COMMIT;")

        print("canonicalize_done")
        print("league_id =", league_id, "season =", season)
        print("db_path =", str(resolved_db))
        print("memory_events_processed =", processed)
        print("skipped_empty_fingerprint =", skipped_empty_fingerprint)
        print("skipped_phantom =", skipped_phantom)
        print("canonical_events_created =", created)
        print("canonical_best_updated =", updated_best)

        totals = conn.execute(
            """
            SELECT event_type, COUNT(*) AS n
            FROM canonical_events
            WHERE league_id=? AND season=?
            GROUP BY event_type
            ORDER BY n DESC
            """,
            (league_id, season),
        ).fetchall()
        print("canonical_by_type =", {et: int(n) for (et, n) in totals})


if __name__ == "__main__":
    import argparse
    import os
    p = argparse.ArgumentParser(description="Canonicalize memory events into canonical events")
    p.add_argument("--db", default=os.environ.get("SQUADVAULT_DB", ".local_squadvault.sqlite"))
    p.add_argument("--league-id", default=os.environ.get("MFL_LEAGUE_ID", "").strip())
    p.add_argument("--season", type=int, default=int(os.environ.get("SQUADVAULT_YEAR", "2024")))
    args = p.parse_args()

    if not args.league_id:
        raise RuntimeError("MFL_LEAGUE_ID env var required (or pass --league-id)")

    canonicalize(league_id=args.league_id, season=args.season, db_path=args.db)
