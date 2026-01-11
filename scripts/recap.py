#!/usr/bin/env python3
import os
import sys

# --- bootstrap PYTHONPATH so `squadvault` is importable when run as a script ---
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_PATH = os.path.join(REPO_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)
# ------------------------------------------------------------------------------

import argparse
import dataclasses
import json
import sqlite3
import subprocess
from typing import Any, Optional

from squadvault.recaps.weekly_recap_lifecycle import (
    approve_latest_weekly_recap,
    generate_weekly_recap_draft,
)

ARTIFACT_TYPE_WEEKLY_RECAP = "WEEKLY_RECAP"


def sh(cmd: list[str]) -> int:
    print(f"\n$ {' '.join(cmd)}")
    return subprocess.call(cmd)


def _jsonable(obj: Any) -> Any:
    """
    Convert common Python objects (including dataclasses) into JSON-serializable structures.
    Falls back to stringification for unknown objects.
    """
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (list, tuple)):
        return [_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if dataclasses.is_dataclass(obj):
        return _jsonable(dataclasses.asdict(obj))
    if hasattr(obj, "__dict__"):
        return _jsonable(obj.__dict__)
    return str(obj)


def _print_json(obj: Any) -> None:
    print(json.dumps(_jsonable(obj), indent=2, sort_keys=True))


def _latest_weekly_recap_artifact_state(
    db_path: str, league_id: str, season: int, week_index: int
) -> Optional[str]:
    """
    Returns the state of the latest WEEKLY_RECAP artifact for the given (league_id, season, week_index),
    or None if none exists.
    """
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT state
            FROM recap_artifacts
            WHERE league_id = ?
              AND season = ?
              AND week_index = ?
              AND artifact_type = ?
            ORDER BY version DESC
            LIMIT 1
            """,
            (league_id, season, week_index, ARTIFACT_TYPE_WEEKLY_RECAP),
        )
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()

def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cur.fetchall()}  # row[1] = column name


def _fetch_week_status(db_path: str, league_id: str, season: int, week_index: int) -> dict[str, Any]:
    """
    Returns a compact status payload:
    - recap_runs: state/reason/updated_at (only fields that exist)
    - latest_artifact: best-effort fields (only columns that exist)
    - approved_artifact: best-effort fields (only columns that exist)
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()

        # --- recap_runs (schema-resilient) ---
        runs_cols = _table_columns(conn, "recap_runs")
        runs_select = [c for c in ["state", "reason", "updated_at"] if c in runs_cols]
        recap_run = None
        if runs_select:
            cur.execute(
                f"""
                SELECT {", ".join(runs_select)}
                FROM recap_runs
                WHERE league_id = ?
                  AND season = ?
                  AND week_index = ?
                LIMIT 1
                """,
                (league_id, season, week_index),
            )
            row = cur.fetchone()
            recap_run = dict(row) if row else None

        # --- recap_artifacts (schema-resilient) ---
        art_cols = _table_columns(conn, "recap_artifacts")

        base_where = """
            league_id = ?
            AND season = ?
            AND week_index = ?
            AND artifact_type = ?
        """

        # Only include columns that exist in *your* DB.
        preferred_artifact_fields = [
            "version",
            "state",
            "supersedes_version",
            "created_by",
            "created_at",
            "approved_by",
            "approved_at",
            "selection_fingerprint",
            "window_start",
            "window_end",
            "withheld_reason",
        ]

        art_select = [c for c in preferred_artifact_fields if c in art_cols]

        def fetch_one_artifact(extra_and: str = "", params_extra: tuple[Any, ...] = ()) -> Optional[dict[str, Any]]:
            if not art_select:
                return None
            sql = f"""
                SELECT {", ".join(art_select)}
                FROM recap_artifacts
                WHERE {base_where}
                {extra_and}
                ORDER BY version DESC
                LIMIT 1
            """
            cur.execute(
                sql,
                (league_id, season, week_index, ARTIFACT_TYPE_WEEKLY_RECAP, *params_extra),
            )
            r = cur.fetchone()
            return dict(r) if r else None

        latest_artifact = fetch_one_artifact()
        approved_artifact = fetch_one_artifact("AND state = 'APPROVED'")

        return {
            "week": {"league_id": league_id, "season": season, "week_index": week_index},
            "recap_run": recap_run,
            "latest_artifact": latest_artifact,
            "approved_artifact": approved_artifact,
        }
    finally:
        conn.close()

# --- ADD this new command implementation somewhere near cmd_status (after _fetch_week_status is fine) ---

def _list_week_indexes(db_path: str, league_id: str, season: int) -> list[int]:
    """
    Returns all week_index values that appear in either recap_runs or recap_artifacts
    for the given league/season, sorted ascending.
    """
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT week_index FROM (
              SELECT DISTINCT week_index
              FROM recap_runs
              WHERE league_id = ? AND season = ?
              UNION
              SELECT DISTINCT week_index
              FROM recap_artifacts
              WHERE league_id = ? AND season = ? AND artifact_type = ?
            )
            ORDER BY week_index ASC
            """,
            (league_id, season, league_id, season, ARTIFACT_TYPE_WEEKLY_RECAP),
        )
        return [int(r[0]) for r in cur.fetchall()]
    finally:
        conn.close()


def _short_fp(fp: Optional[str]) -> str:
    if not fp:
        return ""
    return fp[:10]

def cmd_list_weeks(args: argparse.Namespace) -> int:
    weeks = _list_week_indexes(args.db, args.league_id, args.season)

    # Optional bounds
    if args.start_week is not None:
        weeks = [w for w in weeks if w >= args.start_week]
    if args.end_week is not None:
        weeks = [w for w in weeks if w <= args.end_week]

    rows: list[dict[str, Any]] = []
    for w in weeks:
        payload = _fetch_week_status(
            db_path=args.db,
            league_id=args.league_id,
            season=args.season,
            week_index=w,
        )

        rr = payload.get("recap_run") or {}
        la = payload.get("latest_artifact") or {}
        aa = payload.get("approved_artifact") or {}

        rows.append(
            {
                "week_index": w,
                "run_state": rr.get("state"),
                "run_updated_at": rr.get("updated_at"),
                "latest_version": la.get("version"),
                "latest_state": la.get("state"),
                "approved_version": aa.get("version"),
                "approved_state": aa.get("state"),
                "fingerprint": la.get("selection_fingerprint"),
                "window_start": la.get("window_start"),
                "window_end": la.get("window_end"),
                "withheld_reason": la.get("withheld_reason"),
            }
        )

    # --- NEW: problems shortcut ---
    # Definition:
    # - latest artifact state is DRAFT or WITHHELD
    # - OR recap_runs missing or not APPROVED
    if getattr(args, "problems", False):
        def is_problem(r: dict[str, Any]) -> bool:
            run_state = (r.get("run_state") or "").upper()
            latest_state = (r.get("latest_state") or "").upper()
            if latest_state in {"DRAFT", "WITHHELD"}:
                return True
            if run_state != "APPROVED":
                return True
            return False

        rows = [r for r in rows if is_problem(r)]

    # --- filtering ---
    def _norm_states(vals: list[str]) -> set[str]:
        out: set[str] = set()
        for v in vals:
            if not v:
                continue
            # allow comma-separated
            for part in v.split(","):
                part = part.strip()
                if part:
                    out.add(part.upper())
        return out

    only_states = _norm_states(args.only or [])
    scope = (args.scope or "any").lower()

    if only_states:
        def matches(r: dict[str, Any]) -> bool:
            run_state = (r.get("run_state") or "").upper()
            latest_state = (r.get("latest_state") or "").upper()
            approved_state = (r.get("approved_state") or "").upper()
            has_approved = r.get("approved_version") is not None

            if scope == "run":
                return run_state in only_states

            if scope == "latest":
                return latest_state in only_states

            if scope == "approved":
                # Treat presence of an approved artifact as APPROVED
                # (and also accept approved_state if your table stores it).
                return ("APPROVED" in only_states) and (has_approved or approved_state == "APPROVED")

            # scope == "any" (default): match if any dimension matches.
            if run_state in only_states:
                return True
            if latest_state in only_states:
                return True
            if approved_state in only_states:
                return True
            if ("APPROVED" in only_states) and has_approved:
                return True
            return False

        rows = [r for r in rows if matches(r)]

    # --- output ---
    if args.format == "json":
        _print_json(
            {
                "league_id": args.league_id,
                "season": args.season,
                "filter": {
                    "only": sorted(list(only_states)) if only_states else [],
                    "scope": scope,
                    "problems": bool(getattr(args, "problems", False)),
                },
                "weeks": rows,
            }
        )
        return 0

    # text/table output (human)
    def s(v: Any) -> str:
        return "" if v is None else str(v)

    headers = [
        ("Wk", 3),
        ("Run", 10),
        ("Latest", 14),
        ("Approved", 14),
        ("FP", 12),
        ("Window", 33),
        ("Withheld", 20),
    ]

    def fmt_cell(val: str, width: int) -> str:
        val = val or ""
        return (val[: width - 1] + "…") if len(val) > width else val.ljust(width)

    line = "  ".join(fmt_cell(h, w) for h, w in headers)
    print(line)
    print("-" * len(line))

    for r in rows:
        wk = s(r["week_index"])
        run = s(r["run_state"])

        latest = ""
        if r["latest_version"] is not None or r["latest_state"] is not None:
            latest = f"v{r['latest_version']} {s(r['latest_state'])}".strip()

        approved = ""
        if r["approved_version"] is not None:
            approved = f"v{r['approved_version']} APPROVED"

        fp = _short_fp(r.get("fingerprint"))

        window = ""
        if r.get("window_start") or r.get("window_end"):
            window = f"{s(r.get('window_start'))} → {s(r.get('window_end'))}"

        withheld = s(r.get("withheld_reason"))

        row_cells = [
            fmt_cell(wk, headers[0][1]),
            fmt_cell(run, headers[1][1]),
            fmt_cell(latest, headers[2][1]),
            fmt_cell(approved, headers[3][1]),
            fmt_cell(fp, headers[4][1]),
            fmt_cell(window, headers[5][1]),
            fmt_cell(withheld, headers[6][1]),
        ]
        print("  ".join(row_cells))

    return 0

def cmd_status(args: argparse.Namespace) -> int:
    payload = _fetch_week_status(
        db_path=args.db,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
    )

    # optional terse format for humans; default JSON for scripts
    if args.format == "json":
        _print_json(payload)
        return 0

    # text format
    wk = payload["week"]
    rr = payload["recap_run"]
    la = payload["latest_artifact"]
    aa = payload["approved_artifact"]

    print(f"Week: league_id={wk['league_id']} season={wk['season']} week_index={wk['week_index']}")
    print()

    if rr is None:
        print("recap_runs: (none)")
    else:
        reason = rr.get("reason") or ""
        print(f"recap_runs: state={rr.get('state')} updated_at={rr.get('updated_at')} reason={reason}")

    def fmt_art(a: Optional[dict[str, Any]]) -> str:
        if not a:
            return "(none)"
        parts = [
            f"v{a.get('version')}",
            f"state={a.get('state')}",
        ]
        if a.get("supersedes_version") is not None:
            parts.append(f"supersedes=v{a.get('supersedes_version')}")
        if a.get("selection_fingerprint"):
            parts.append(f"fingerprint={a.get('selection_fingerprint')}")
        if a.get("window_start") or a.get("window_end"):
            parts.append(f"window={a.get('window_start')} → {a.get('window_end')}")
        if a.get("approved_by") or a.get("approved_at"):
            parts.append(f"approved_by={a.get('approved_by')} approved_at={a.get('approved_at')}")
        if a.get("created_by") or a.get("created_at"):
            parts.append(f"created_by={a.get('created_by')} created_at={a.get('created_at')}")
        if a.get("withheld_reason"):
            parts.append(f"withheld_reason={a.get('withheld_reason')}")
        return " | ".join(parts)

    print(f"latest_artifact:   {fmt_art(la)}")
    print(f"approved_artifact: {fmt_art(aa)}")
    return 0


def cmd_render_week(args: argparse.Namespace) -> int:
    cmd = [
        sys.executable,
        "-u",
        "src/squadvault/consumers/recap_week_render.py",
        "--db",
        args.db,
        "--league-id",
        args.league_id,
        "--season",
        str(args.season),
        "--week-index",
        str(args.week_index),
    ]
    if args.suppress_render_warning:
        cmd.append("--suppress-render-warning")
    return sh(cmd)


def cmd_regen(args: argparse.Namespace) -> int:
    res = generate_weekly_recap_draft(
        db_path=args.db,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
        reason=args.reason,
        created_by=args.created_by,
        force=args.force,
    )
    _print_json(res)
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    # We intentionally do NOT provide an Option-A bypass here.
    # Approval requires a DRAFT to exist in the lifecycle.
    if args.require_draft:
        state = _latest_weekly_recap_artifact_state(
            db_path=args.db,
            league_id=args.league_id,
            season=args.season,
            week_index=args.week_index,
        )
        if state is None:
            print(
                "ERROR: --require-draft set, but no WEEKLY_RECAP artifact exists for this week.",
                file=sys.stderr,
            )
            return 2
        if state != "DRAFT":
            print(
                f"ERROR: --require-draft set, but latest WEEKLY_RECAP artifact is state='{state}', not 'DRAFT'.",
                file=sys.stderr,
            )
            return 2

    res = approve_latest_weekly_recap(
        db_path=args.db,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
        approved_by=args.approved_by,
    )
    _print_json(res)
    return 0


def cmd_fetch_approved(args: argparse.Namespace) -> int:
    cmd = [
        sys.executable,
        "-u",
        "scripts/recap_week_fetch_approved.py",
        "--db",
        args.db,
        "--league-id",
        args.league_id,
        "--season",
        str(args.season),
        "--week-index",
        str(args.week_index),
    ]
    return sh(cmd)


def cmd_golden_path(args: argparse.Namespace) -> int:
    cmd = [
        sys.executable,
        "-u",
        "scripts/golden_path_recap_lifecycle.py",
        "--db",
        args.db,
        "--league-id",
        args.league_id,
        "--season",
        str(args.season),
        "--week-index",
        str(args.week_index),
        "--approved-by",
        args.approved_by,
    ]
    if args.legacy_force:
        cmd.append("--legacy-force")
    if args.no_force_fallback:
        cmd.append("--no-force-fallback")
    return sh(cmd)


def cmd_check(args: argparse.Namespace) -> int:
    cmd = [
        "bash",
        "scripts/check_golden_path_recap.sh",
        args.db,
        args.league_id,
        str(args.season),
        str(args.week_index),
        args.approved_by,
    ]
    return sh(cmd)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="recap", description="SquadVault recap operator CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    # Shared args helper
    def add_common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--db", required=True)
        sp.add_argument("--league-id", dest="league_id", required=True)
        sp.add_argument("--season", type=int, required=True)
        sp.add_argument("--week-index", dest="week_index", type=int, required=True)

    sp = sub.add_parser("status", help="Show recap_runs + artifact status for a given week")
    add_common(sp)
    sp.add_argument("--format", choices=["json", "text"], default="json")
    sp.set_defaults(fn=cmd_status)

    sp = sub.add_parser("render-week", help="Render weekly recap (selection + render output)")
    add_common(sp)
    sp.add_argument("--suppress-render-warning", action="store_true")
    sp.set_defaults(fn=cmd_render_week)

    sp = sub.add_parser("regen", help="Regenerate weekly recap artifact draft via lifecycle")
    add_common(sp)
    sp.add_argument("--reason", required=True)
    sp.add_argument("--created-by", dest="created_by", default="system")
    sp.add_argument("--force", action="store_true")
    sp.set_defaults(fn=cmd_regen)

    sp = sub.add_parser("approve", help="Approve latest weekly recap draft via lifecycle")
    add_common(sp)
    sp.add_argument("--approved-by", dest="approved_by", required=True)
    sp.add_argument(
        "--require-draft",
        action="store_true",
        help="Fail fast unless the latest WEEKLY_RECAP artifact is in DRAFT state.",
    )
    sp.set_defaults(fn=cmd_approve)

    sp = sub.add_parser("fetch-approved", help="Fetch approved weekly recap (current approved artifact)")
    add_common(sp)
    sp.set_defaults(fn=cmd_fetch_approved)

    sp = sub.add_parser("golden-path", help="Run golden path harness (render -> regen -> maybe approve)")
    add_common(sp)
    sp.add_argument("--approved-by", dest="approved_by", required=True)
    sp.add_argument("--legacy-force", action="store_true")
    sp.add_argument("--no-force-fallback", action="store_true")
    sp.set_defaults(fn=cmd_golden_path)

    sp = sub.add_parser("check", help="Run non-destructive golden path + invariant checks")
    add_common(sp)
    sp.add_argument("--approved-by", dest="approved_by", default="steve")
    sp.set_defaults(fn=cmd_check)

    sp = sub.add_parser("list-weeks", help="List all weeks and their recap/artifact status for a season")
    sp.add_argument("--db", required=True)
    sp.add_argument("--league-id", dest="league_id", required=True)
    sp.add_argument("--season", type=int, required=True)
    sp.add_argument("--format", choices=["json", "text"], default="text")
    sp.add_argument("--start-week", dest="start_week", type=int, default=None, help="Optional lower bound week_index")
    sp.add_argument("--end-week", dest="end_week", type=int, default=None, help="Optional upper bound week_index")

    sp.add_argument(
    "--only",
    action="append",
    default=[],
    help="Filter to weeks matching state(s). Repeatable or comma-separated (e.g. --only APPROVED or --only DRAFT,WITHHELD).",
    )
    sp.add_argument(
        "--scope",
        choices=["any", "run", "latest", "approved"],
        default="any",
        help="Where to apply --only: any (default), run (recap_runs.state), latest (latest artifact state), approved (has approved artifact).",
    )

    sp.set_defaults(fn=cmd_list_weeks)

    sp.add_argument(
    "--problems",
    action="store_true",
    help="Shortcut for surfacing problematic weeks (WITHHELD/DRAFT latest, or recap_run not APPROVED).",
    )

    return p

def main() -> int:
    p = build_parser()
    args = p.parse_args()
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())
