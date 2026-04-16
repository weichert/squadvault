"""Regenerate a weekly recap draft artifact."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict

from squadvault.recaps.weekly_recap_lifecycle import generate_weekly_recap_draft


def main() -> int:
    """CLI entrypoint: regenerate a recap draft artifact."""
    p = argparse.ArgumentParser(
        description="Regenerate weekly recap artifact draft (canonical lifecycle)."
    )
    p.add_argument("--db", required=True)
    p.add_argument("--league-id", required=True)
    p.add_argument("--season", type=int, required=True)
    p.add_argument("--week-index", type=int, required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--created-by", default="system")
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    # ── Finding 8: fail loudly on missing API key ────────────────────
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print(
            "ERROR: ANTHROPIC_API_KEY not set.\n"
            "Regen requires an API key to produce model-generated narratives.\n"
            "Without it, the lifecycle silently falls back to facts-only output.\n"
            "\n"
            "Propagate with:  set -a; source .env.local; set +a",
            file=sys.stderr,
        )
        return 1

    # ── Finding 9: make audit unconditional during regen ─────────────
    os.environ["SQUADVAULT_PROMPT_AUDIT"] = "1"

    res = generate_weekly_recap_draft(
        db_path=args.db,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
        reason=args.reason,
        force=args.force,
        created_by=args.created_by,
    )

    d = asdict(res)
    d["audit_forced"] = True
    print(json.dumps(d, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
