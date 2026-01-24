#!/usr/bin/env python3
import os
import sys
from pathlib import Path

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
from collections import Counter
from typing import Any, Optional

from squadvault.recaps.weekly_recap_lifecycle import (
    approve_latest_weekly_recap,
    generate_weekly_recap_draft,
)

# NEW: approved export CLI wrapper
from squadvault.consumers.recap_export_approved import main as export_approved_main

# NEW: Writing Room SelectionSet v1 consumer wrapper
from squadvault.consumers.recap_writing_room_select_v1 import main as writing_room_select_main


ARTIFACT_TYPE_WEEKLY_RECAP = "WEEKLY_RECAP"


def sh(cmd: list[str]) -> int:
    print(f"\n$ {' '.join(cmd)}")
    env = os.environ.copy()
    env["PYTHONPATH"] = SRC_PATH + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return subprocess.call(cmd, env=env)


def run_script(script_path: str, argv: list[str]) -> int:
    cmd = [sys.executable, "-u", script_path] + argv
    return sh(cmd)


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


def cmd_export_assemblies(args: argparse.Namespace) -> int:
    """
    Phase 2.3: export deterministic narrative assemblies (PLAIN_V1 + SHAREPACK_V1)
    from APPROVED weekly recap artifacts only. Export-only; no canonical writes.
    """
    cmd = [
        sys.executable,
        "-u",
        "src/squadvault/consumers/recap_export_narrative_assemblies_approved.py",
        "--db", args.db,
        "--league-id", args.league_id,
        "--season", str(args.season),
        "--week-index", str(args.week_index),
        "--export-dir", args.export_dir,
    ]

    env = dict(**os.environ)
    env["PYTHONPATH"] = "src" + (":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")

    proc = subprocess.run(cmd, env=env)
    return int(proc.returncode)


def cmd_review_week(args: argparse.Namespace) -> int:
    return run_script(
        "src/squadvault/consumers/editorial_review_week.py",
        [
            "--db", args.db,
            "--league-id", args.league_id,
            "--season", str(args.season),
            "--week-index", str(args.week_index),
            "--actor", args.actor,
            "--base-dir", args.base_dir,
        ],
    )


def cmd_editorial_log(args: argparse.Namespace) -> int:
    return run_script(
        "src/squadvault/consumers/editorial_log_week.py",
        [
            "--db", args.db,
            "--league-id", args.league_id,
            "--season", str(args.season),
            "--week-index", str(args.week_index),
            "--limit", str(args.limit),
        ],
    )


def cmd_list_weeks(args: argparse.Namespace) -> int:
    weeks = _list_week_indexes(args.db, args.league_id, args.season)

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
        if not rows:
            print("(no problems)")
            return 0

    def _norm_states(vals: list[str]) -> set[str]:
        out: set[str] = set()
        for v in vals:
            if not v:
                continue
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
                return ("APPROVED" in only_states) and (has_approved or approved_state == "APPROVED")

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

    if args.format == "json":
        _print_json(payload)
        return 0

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


def _maybe_build_writing_room_selection_set_v1(args: argparse.Namespace) -> None:
    """Optional deterministic side-artifact: Writing Room SelectionSetV1.

    Non-invasive: produces selection_set_v1.json but does NOT alter recap render/selection yet.
    """
    if not getattr(args, "enable_writing_room", False):
        return

    created_at = getattr(args, "created_at_utc", None) or getattr(args, "writing_room_created_at_utc", None)
    if not created_at:
        print("--enable-writing-room requires --created-at-utc (or --writing-room-created-at-utc)", file=sys.stderr)
        raise SystemExit(2)

    out_path = getattr(args, "writing_room_out", None)
    if not out_path:
        out_path = (
            f"artifacts/writing_room/{args.league_id}/{args.season}/"
            f"week_{int(args.week_index):02d}/selection_set_v1.json"
        )

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    argv = [
        "--db", args.db,
        "--league-id", str(args.league_id),
        "--season", str(args.season),
        "--week-index", str(args.week_index),
        "--created-at-utc", created_at,
        "--signals-source", "db",
        "--out", out_path,
    ]

    rc = int(writing_room_select_main(argv))
    if rc != 0:
        raise SystemExit(rc)


def cmd_render_week(args: argparse.Namespace) -> int:
    _maybe_build_writing_room_selection_set_v1(args)
    cmd = [
        sys.executable,
        "-u",
        "src/squadvault/consumers/recap_week_render.py",
        "--db", args.db,
        "--league-id", args.league_id,
        "--season", str(args.season),
        "--week-index", str(args.week_index),
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


def cmd_withhold(args: argparse.Namespace) -> int:
    cmd = [
        sys.executable,
        "-u",
        "src/squadvault/consumers/recap_artifact_withhold.py",
        "--db", args.db,
        "--league-id", args.league_id,
        "--season", str(args.season),
        "--week-index", str(args.week_index),
        "--version", str(args.version),
        "--reason", args.reason,
    ]
    return sh(cmd)


def cmd_fetch_approved(args: argparse.Namespace) -> int:
    cmd = [
        sys.executable,
        "-u",
        "scripts/recap_week_fetch_approved.py",
        "--db", args.db,
        "--league-id", args.league_id,
        "--season", str(args.season),
        "--week-index", str(args.week_index),
    ]
    return sh(cmd)


def cmd_export_approved(args: argparse.Namespace) -> int:
    argv = [
        "--db", args.db,
        "--league-id", str(args.league_id),
        "--season", str(args.season),
        "--week-index", str(args.week_index),
    ]

    if args.out_dir:
        argv += ["--out-dir", args.out_dir]
    if args.out_root:
        argv += ["--out-root", args.out_root]
    if args.version is not None:
        argv += ["--version", str(args.version)]
    if args.non_deterministic:
        argv += ["--non-deterministic"]

    return export_approved_main(argv)


def cmd_golden_path(args: argparse.Namespace) -> int:
    _maybe_build_writing_room_selection_set_v1(args)
    cmd = [
        sys.executable,
        "-u",
        "scripts/golden_path_recap_lifecycle.py",
        "--db", args.db,
        "--league-id", args.league_id,
        "--season", str(args.season),
        "--week-index", str(args.week_index),
        "--approved-by", args.approved_by,
    ]
    if args.legacy_force:
        cmd.append("--legacy-force")
    if args.no_force_fallback:
        cmd.append("--no-force-fallback")
    return sh(cmd)


def cmd_check(args: argparse.Namespace) -> int:
    _maybe_build_writing_room_selection_set_v1(args)
    cmd = [
        "bash",
        "scripts/check_golden_path_recap.sh",
        "--db", args.db,
        "--league-id", str(args.league_id),
        "--season", str(args.season),
        "--start-week", str(args.week_index),
        "--end-week", str(args.week_index),
    ]
    return sh(cmd)


def cmd_writing_room_review(args: argparse.Namespace) -> int:
    """
    Human-auditable review of Writing Room SelectionSetV1 JSON.

    File-only MVP:
      ./scripts/recap.sh writing-room-review --selection-set <path> [--show-included] [--show-excluded]
    """
    p = Path(args.selection_set)
    if not p.exists():
        print(f"ERROR: selection set not found: {p}", file=sys.stderr)
        return 2

    data = json.loads(p.read_text(encoding="utf-8"))

    withheld = bool(data.get("withheld", False))
    withheld_reason = data.get("withheld_reason")
    included = data.get("included_signal_ids", []) or []
    excluded = data.get("excluded", []) or []

    reasons = [e.get("reason_code", "UNKNOWN") for e in excluded]
    c = Counter(reasons)

    print("Writing Room SelectionSetV1 Review")
    print(f"file: {p}")
    print(f"withheld: {withheld}")
    if withheld:
        print(f"withheld_reason: {withheld_reason}")
    print(f"included: {len(included)}")
    print(f"excluded: {len(excluded)}")

    if excluded:
        print("\nexcluded_by_reason:")
        for k in sorted(c.keys()):
            print(f"  - {k}: {c[k]}")

    if args.show_included:
        print("\nINCLUDED signal_ids:")
        for sid in included:
            print(f"  - {sid}")

    if args.show_excluded:
        print("\nEXCLUDED signals:")
        for e in excluded:
            sid = e.get("signal_id")
            rc = e.get("reason_code")
            details = e.get("details") or []
            if details:
                d_str = ", ".join([f"{d.get('k')}={d.get('v')}" for d in details])
                print(f"  - {sid}  [{rc}]  ({d_str})")
            else:
                print(f"  - {sid}  [{rc}]")

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="recap", description="SquadVault recap operator CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--db", required=True)
        sp.add_argument("--league-id", dest="league_id", required=True)
        sp.add_argument("--season", type=int, required=True)
        sp.add_argument("--week-index", dest="week_index", type=int, required=True)

    # status
    sp = sub.add_parser("status", help="Show recap_runs + artifact status for a given week")
    add_common(sp)
    sp.add_argument("--format", choices=["json", "text"], default="json")
    sp.set_defaults(fn=cmd_status)

    # render-week
    sp = sub.add_parser("render-week", help="Render weekly recap (selection + render output)")
    add_common(sp)
    sp.add_argument("--suppress-render-warning", action="store_true")
    sp.add_argument(
        "--enable-writing-room",
        action="store_true",
        help="Also generate Writing Room SelectionSetV1 as a deterministic side-artifact (does not affect recap yet).",
    )
    sp.add_argument(
        "--writing-room-out",
        default=None,
        help="Optional override output path for selection_set_v1.json (deterministic default under artifacts/writing_room/...).",
    )
    # FIX: accept --created-at-utc on render-week (your earlier error)
    sp.add_argument(
        "--created-at-utc",
        dest="created_at_utc",
        default=None,
        help="When --enable-writing-room: ISO-8601 UTC timestamp for Writing Room artifact metadata.",
    )
    sp.add_argument(
        "--writing-room-created-at-utc",
        default=None,
        help="Alias/fallback timestamp for Writing Room. Prefer --created-at-utc.",
    )
    sp.set_defaults(fn=cmd_render_week)

    # regen
    sp = sub.add_parser("regen", help="Regenerate weekly recap artifact draft via lifecycle")
    add_common(sp)
    sp.add_argument("--reason", required=True)
    sp.add_argument("--created-by", dest="created_by", default="system")
    sp.add_argument("--force", action="store_true")
    sp.set_defaults(fn=cmd_regen)

    # approve
    sp = sub.add_parser("approve", help="Approve latest weekly recap draft via lifecycle")
    add_common(sp)
    sp.add_argument("--approved-by", dest="approved_by", required=True)
    sp.add_argument(
        "--require-draft",
        action="store_true",
        help="Fail fast unless the latest WEEKLY_RECAP artifact is in DRAFT state.",
    )
    sp.set_defaults(fn=cmd_approve)

    # export-assemblies
    sp = sub.add_parser(
        "export-assemblies",
        help="Export Phase 2.3 narrative assemblies from APPROVED weekly recap artifact",
    )
    sp.add_argument("--db", required=True)
    sp.add_argument("--league-id", required=True)
    sp.add_argument("--season", type=int, required=True)
    sp.add_argument("--week-index", type=int, required=True)
    sp.add_argument("--export-dir", default="artifacts", help="Export root (default: artifacts)")
    sp.set_defaults(fn=cmd_export_assemblies)

    # withhold
    sp = sub.add_parser("withhold", help="Withhold a specific weekly recap artifact version (ops-safe)")
    add_common(sp)
    sp.add_argument("--version", type=int, required=True)
    sp.add_argument("--reason", required=True)
    sp.set_defaults(fn=cmd_withhold)

    # fetch-approved
    sp = sub.add_parser("fetch-approved", help="Fetch approved weekly recap (current approved artifact)")
    add_common(sp)
    sp.set_defaults(fn=cmd_fetch_approved)

    # review-week
    sp = sub.add_parser("review-week", help="Commissioner editorial review loop for a weekly recap")
    sp.add_argument("--db", required=True)
    sp.add_argument("--league-id", required=True)
    sp.add_argument("--season", type=int, required=True)
    sp.add_argument("--week-index", type=int, required=True)
    sp.add_argument("--actor", required=True)
    sp.add_argument("--base-dir", default="artifacts")
    sp.set_defaults(fn=cmd_review_week)

    # editorial-log
    sp = sub.add_parser("editorial-log", help="Show editorial history for a week")
    sp.add_argument("--db", required=True)
    sp.add_argument("--league-id", required=True)
    sp.add_argument("--season", type=int, required=True)
    sp.add_argument("--week-index", type=int, required=True)
    sp.add_argument("--limit", type=int, default=200)
    sp.set_defaults(fn=cmd_editorial_log)

    # export-approved
    sp = sub.add_parser(
        "export-approved",
        help="Export latest APPROVED weekly recap artifact to a portable bundle.",
    )
    add_common(sp)
    sp.add_argument("--out-dir", help="Exact directory to write export bundle into.")
    sp.add_argument("--out-root", help="Root directory under which canonical export path will be created.")
    sp.add_argument("--version", type=int, default=None)
    sp.add_argument(
        "--non-deterministic",
        dest="non_deterministic",
        action="store_true",
        help="Include volatile metadata like exported_at (default is deterministic).",
    )
    sp.set_defaults(fn=cmd_export_approved)

    # golden-path
    sp = sub.add_parser("golden-path", help="Run golden path harness (render -> regen -> maybe approve)")
    add_common(sp)
    sp.add_argument("--approved-by", dest="approved_by", required=True)
    sp.add_argument("--legacy-force", action="store_true")
    sp.add_argument("--no-force-fallback", action="store_true")

    sp.add_argument(
        "--enable-writing-room",
        action="store_true",
        help="Also generate Writing Room SelectionSetV1 as a deterministic side-artifact (does not affect recap yet).",
    )
    sp.add_argument(
        "--writing-room-out",
        default=None,
        help="Optional override output path for selection_set_v1.json (deterministic default under artifacts/writing_room/...).",
    )
    sp.add_argument(
        "--created-at-utc",
        dest="created_at_utc",
        default=None,
        help="When --enable-writing-room: ISO-8601 UTC timestamp for Writing Room artifact metadata.",
    )
    sp.add_argument(
        "--writing-room-created-at-utc",
        dest="writing_room_created_at_utc",
        default=None,
        help="Alias for --created-at-utc (Writing Room only).",
    )
    sp.set_defaults(fn=cmd_golden_path)

    # check
    sp = sub.add_parser("check", help="Run non-destructive golden path + invariant checks")
    add_common(sp)
    sp.add_argument("--approved-by", dest="approved_by", default="steve")

    sp.add_argument(
        "--enable-writing-room",
        action="store_true",
        help="Also build Writing Room SelectionSetV1 side-artifact (deterministic, non-invasive).",
    )
    sp.add_argument(
        "--created-at-utc",
        dest="created_at_utc",
        default=None,
        help="When --enable-writing-room: ISO-8601 UTC timestamp for Writing Room artifact metadata.",
    )
    sp.add_argument(
        "--writing-room-created-at-utc",
        dest="writing_room_created_at_utc",
        default=None,
        help="Alias for --created-at-utc (Writing Room only).",
    )
    sp.add_argument(
        "--writing-room-out",
        dest="writing_room_out",
        default=None,
        help="Optional output path for selection_set_v1.json (Writing Room).",
    )
    sp.set_defaults(fn=cmd_check)

    # list-weeks
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
    sp.add_argument(
        "--problems",
        action="store_true",
        help="Shortcut for surfacing problematic weeks (WITHHELD/DRAFT latest, or recap_run not APPROVED).",
    )
    sp.set_defaults(fn=cmd_list_weeks)

    # NEW: writing-room-review (so your attempted command works)
    sp = sub.add_parser("writing-room-review", help="Review a Writing Room SelectionSetV1 JSON")
    sp.add_argument("--selection-set", dest="selection_set", required=True, help="Path to selection_set_v1.json")
    sp.add_argument("--show-included", action="store_true", help="Print included signal_ids")
    sp.add_argument("--show-excluded", action="store_true", help="Print excluded signals w/ reason/details")
    sp.set_defaults(fn=cmd_writing_room_review)

    return p


def main() -> int:
    p = build_parser()
    args = p.parse_args()
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())
