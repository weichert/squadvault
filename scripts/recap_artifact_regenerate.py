#!/usr/bin/env python3

import argparse
import json
import os
import sys
from dataclasses import asdict

from squadvault.recaps.weekly_recap_lifecycle import generate_weekly_recap_draft


def main() -> int:
    p = argparse.ArgumentParser(description="Regenerate weekly recap artifact draft (canonical lifecycle).")
    p.add_argument("--db", required=True)
    p.add_argument("--league-id", required=True)
    p.add_argument("--season", type=int, required=True)
    p.add_argument("--week-index", type=int, required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--created-by", default="system")
    p.add_argument("--force", action="store_true")
    args = p.parse_args()

    # ── Finding 8: fail loudly on missing API key ────────────────────
    # Regen is a human-initiated action where the expectation is a
    # model-generated narrative. Silent fallback to facts-only output
    # produces a quality regression that is hard to detect in the JSON
    # output (verification_attempts=1, verification_result=null looks
    # like any other failure). Fail early with a clear message.
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
    # The prompt_audit sidecar captures what the model received and
    # produced — essential diagnostic data. Regen without audit means
    # "diagnostic that produces no diagnostic record." Force it on so
    # .env.local sourcing is not a prerequisite for useful regen output.
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

    # asdict() recurses into nested dataclasses (e.g. res.verification_result,
    # which is a frozen VerificationResult containing tuples of
    # VerificationFailure). res.__dict__ does not, so json.dumps crashes when
    # verification_result is non-None. Frozen dataclasses are supported.
    d = asdict(res)

    # Finding 9 (b): surface in the JSON that audit was forced on,
    # so the operator can confirm diagnostic data was captured.
    d["audit_forced"] = True

    print(json.dumps(d, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
