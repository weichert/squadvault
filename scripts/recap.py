#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys

from squadvault.recaps.weekly_recap_lifecycle import (
    approve_latest_weekly_recap,
    generate_weekly_recap_draft,
)


def sh(cmd: list[str]) -> int:
    print(f"\n$ {' '.join(cmd)}")
    return subprocess.call(cmd)


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
    print(json.dumps(res.__dict__, indent=2, sort_keys=True))
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    # We intentionally do NOT provide an Option-A bypass here.
    # Approval requires a DRAFT to exist in the lifecycle.
    if args.require_draft:
        # lifecycle will fail anyway; keep message consistent
        pass

    res = approve_latest_weekly_recap(
        db_path=args.db,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
        approved_by=args.approved_by,
    )
    print(json.dumps(res.__dict__, indent=2, sort_keys=True))
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
    sp.add_argument("--require-draft", action="store_true")
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

    return p


def main() -> int:
    p = build_parser()
    args = p.parse_args()
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())
