#!/usr/bin/env python3
"""
Writing Room Intake v1.0 — CLI

Deterministic wrapper around build_selection_set_v1.
Intended for debugging, validation, and Sprint 1 verification.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from squadvault.recaps.writing_room.intake_v1 import (
    IntakeContextV1,
    build_selection_set_v1,
)


# ---------------------------------------------------------------------
# Minimal JSON adapter (Sprint 1 only)
# ---------------------------------------------------------------------

class JsonSignalAdapter:
    def __init__(self, path: Path):
        self.path = path

    def iter_signals(self, ctx):
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("signals JSON must be a list")
        return data


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Writing Room Intake v1.0")

    p.add_argument("--league-id", required=True)
    p.add_argument("--season", type=int, required=True)
    p.add_argument("--week-index", type=int, required=True)

    p.add_argument("--window-id", required=True)
    p.add_argument("--window-start", required=True)
    p.add_argument("--window-end", required=True)

    p.add_argument("--created-at-utc", required=True)

    p.add_argument("--signals-json", required=True,
                   help="Path to extracted signals JSON")

    p.add_argument("--out",
                   help="Write selection_set_v1.json to this path (default: stdout)")

    args = p.parse_args(argv)

    ctx = IntakeContextV1(
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
        window_id=args.window_id,
        window_start=args.window_start,
        window_end=args.window_end,
        created_at_utc=args.created_at_utc,
    )

    adapter = JsonSignalAdapter(Path(args.signals_json))
    signals = list(adapter.iter_signals(ctx))

    selection_set = build_selection_set_v1(
        ctx=ctx,
        signals=signals,
    )

    payload = selection_set.to_canonical_dict()

    if args.out:
        Path(args.out).write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )
    else:
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
