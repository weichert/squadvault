"""
Consumer: Writing Room Selection Set (v1)

Purpose:
- Load Tier 1 signals (dict signals from JSON file or extracted from canonical_events)
- Run Writing Room intake_v1 deterministic gates
- Emit SelectionSetV1 artifact JSON

This is Build Phase / T6 scaffolding:
- We intentionally do NOT invent a signal schema.
- Input supports:
- --signals-source=json with --signals-json (list of dict signals)
- --signals-source=db (extract from canonical_events for resolved window)
- Later tasks may replace the db extractor with the real Tier 1 signal feed (keeping the SignalAdapter boundary).

Window inputs:
- If --window-id/--window-start/--window-end are omitted, the consumer auto-resolves the weekly window using existing weekly window logic.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, List

from squadvault.recaps.writing_room.artifact_io_v1 import write_selection_set_v1
from squadvault.recaps.writing_room.identity_recipes_v1 import (
    compute_sha256_hex_from_payload_v1,
    selection_fingerprint_payload_v1,
    selection_set_id_payload_v1,
)
from squadvault.recaps.writing_room.intake_v1 import IntakeContextV1, build_selection_set_v1
from squadvault.recaps.writing_room.signal_adapter_v1 import DictSignalAdapter


def _read_dict_signals(path: str) -> List[dict]:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit(f"signals JSON must be a list of dicts: got {type(data)}")
    out: List[dict] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise SystemExit(f"signals[{i}] must be dict: got {type(item)}")
        out.append(item)
    return out


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="(reserved) sqlite path; not used yet")
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week-index", type=int, required=True)
    ap.add_argument("--window-id", required=False)
    ap.add_argument("--window-start", required=False, help="ISO-8601 UTC")
    ap.add_argument("--window-end", required=False, help="ISO-8601 UTC")
    ap.add_argument("--created-at-utc", required=True, help="ISO-8601 UTC")
    ap.add_argument("--signals-source", choices=["json","db"], default="json")
    ap.add_argument("--signals-json", required=False, help="when --signals-source=json: list of dict signals")
    ap.add_argument("--out", required=True, help="output selection_set_v1.json path")

    args = ap.parse_args(argv)

    adapter = DictSignalAdapter()


    # Resolve window inputs
    if args.window_start and args.window_end and args.window_id:
        window_id = args.window_id
        window_start = args.window_start
        window_end = args.window_end
    else:
        from squadvault.recaps.writing_room.window_resolver_v1 import resolve_weekly_window_v1
        w = resolve_weekly_window_v1(
            db_path=args.db,
            league_id=args.league_id,
            season=args.season,
            week_index=args.week_index,
        )
        window_id = w.window_id
        window_start = w.window_start
        window_end = w.window_end

    ctx = IntakeContextV1(
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
        window_id=window_id,
        window_start=window_start,
        window_end=window_end,
    )

    # Load signals (must happen AFTER window resolution for db mode)
    if args.signals_source == "json":
        if not args.signals_json:
            raise SystemExit("--signals-json is required when --signals-source=json")
        signals = _read_dict_signals(args.signals_json)
    else:
        from squadvault.recaps.writing_room.signal_extractors_v1 import CanonicalEventsSignalExtractorV1
        ex = CanonicalEventsSignalExtractorV1()
        signals = ex.extract_signals(
            db_path=args.db,
            league_id=args.league_id,
            season=args.season,
            window_start=window_start,
            window_end=window_end,
        )


    # ID (opt-in payload recipe)
    id_payload = selection_set_id_payload_v1(
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
        window_id=window_id,
    )
    selection_set_id = compute_sha256_hex_from_payload_v1(id_payload)

    # Run intake
    ss = build_selection_set_v1(
        signals,
        adapter=adapter,
        ctx=ctx,
        selection_set_id=selection_set_id,
        created_at_utc=args.created_at_utc,
        selection_fingerprint="__pending__",  # replaced below
    )

    # Fingerprint (opt-in payload recipe) — based on outputs
    # Keep it minimal: included + excluded signal ids only.
    excluded_ids = [e.signal_id for e in ss.excluded]
    fp_payload = selection_fingerprint_payload_v1(
        included_signal_ids=ss.included_signal_ids,
        excluded_signal_ids=excluded_ids,
    )
    fp = compute_sha256_hex_from_payload_v1(fp_payload)

    # Rebuild with fingerprint (SelectionSetV1 is frozen)
    ss2 = type(ss)(
        selection_set_id=ss.selection_set_id,
        version=ss.version,
        league_id=ss.league_id,
        season=ss.season,
        week_index=ss.week_index,
        window_id=ss.window_id,
        window_start=ss.window_start,
        window_end=ss.window_end,
        selection_fingerprint=fp,
        created_at_utc=ss.created_at_utc,
        included_signal_ids=ss.included_signal_ids,
        excluded=ss.excluded,
        groupings=ss.groupings,
        notes=ss.notes,
        withheld=ss.withheld,
        withheld_reason=ss.withheld_reason,
    )

    out_path = write_selection_set_v1(args.out, ss2)

    d = ss2.to_canonical_dict()
    print("writing_room_select_v1: OK")
    print(f"  out: {out_path}")
    print(f"  included: {len(d['included_signal_ids'])}")
    print(f"  excluded: {len(d['excluded'])}")
    if d.get("withheld"):
        print(f"  withheld_reason: {d.get('withheld_reason')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
