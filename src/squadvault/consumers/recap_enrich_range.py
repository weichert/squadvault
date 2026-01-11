#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from typing import Optional


def _run(cmd: list[str]) -> int:
    p = subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stderr)
    return int(p.returncode)


def main() -> int:
    ap = argparse.ArgumentParser(description="Bulk enrich weekly recap artifacts across a range of weeks.")
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--start-week", type=int, required=True)
    ap.add_argument("--end-week", type=int, required=True)

    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--remove-facts-block", action="store_true")
    ap.add_argument("--rewrite-facts-block", action="store_true")

    args = ap.parse_args()

    if args.remove_facts_block and args.rewrite_facts_block:
        raise SystemExit("Choose only one: --remove-facts-block OR --rewrite-facts-block")

    base = [
        sys.executable,
        "src/squadvault/consumers/recap_week_enrich_artifact.py",
        "--db",
        args.db,
        "--league-id",
        args.league_id,
        "--season",
        str(args.season),
    ]

    failures = 0
    for wk in range(args.start_week, args.end_week + 1):
        cmd = base + ["--week-index", str(wk)]

        if args.dry_run:
            cmd.append("--dry-run")
        if args.force:
            cmd.append("--force")
        if args.remove_facts_block:
            cmd.append("--remove-facts-block")
        if args.rewrite_facts_block:
            cmd.append("--rewrite-facts-block")

        print(f"=== WEEK {wk} ===", file=sys.stderr)
        rc = _run(cmd)
        if rc != 0:
            failures += 1
            print(f"❌ WEEK {wk} FAILED (rc={rc})", file=sys.stderr)

    if failures:
        print(f"Done: {failures} week(s) failed.", file=sys.stderr)
        return 2

    print("Done: all weeks OK.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
