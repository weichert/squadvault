#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("obs_log_path")
    p.add_argument("league_id")
    p.add_argument("season")
    p.add_argument("week_index")
    p.add_argument("--did", required=True, help="What the system did (short)")
    p.add_argument("--felt", required=True, help="How it felt (short)")
    p.add_argument("--wanted", required=True, help="What you wanted to change (but didn’t)")
    p.add_argument("--comment", default="", help="Optional extra comment (kept separate)")
    args = p.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = Path(args.obs_log_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    entry = [
        f"## {ts} — League {args.league_id} — Season {args.season} — Week {args.week_index}",
        f"- **What the system did:** {args.did}",
        f"- **How it felt:** {args.felt}",
        f"- **What I wanted to change (but didn’t):** {args.wanted}",
    ]
    if args.comment.strip():
        entry.append(f"- **Comment:** {args.comment.strip()}")

    out.write_text((out.read_text() if out.exists() else "") + "\n".join(entry) + "\n\n", encoding="utf-8")
    print(f"path1_note: OK ({out})")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
