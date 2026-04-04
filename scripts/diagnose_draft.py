#!/usr/bin/env python3
"""Generate a single draft and show the full output with verification.

Usage:
    source .env.local
    ./scripts/py scripts/diagnose_draft.py \
        --db .local_squadvault.sqlite \
        --league-id 70985 --season 2025 --week 1

Shows the exact narrative text the model produces alongside what the
verifier catches. Use this to understand HOW the model fabricates —
not just that it did.
"""
from __future__ import annotations

import argparse
import json

from squadvault.ai.creative_layer_v1 import draft_narrative_v1
from squadvault.core.eal.editorial_attunement_v1 import (
    EALMeta,
    evaluate_editorial_attunement_v1,
)
from squadvault.core.recaps.recap_runs import get_recap_run_state
from squadvault.core.recaps.render.deterministic_bullets_v1 import (
    render_deterministic_bullets_v1,
)
from squadvault.core.recaps.verification.recap_verifier_v1 import verify_recap_v1
from squadvault.core.resolvers import FranchiseResolver, PlayerResolver
from squadvault.core.storage.session import DatabaseSession
from squadvault.recaps.weekly_recap_lifecycle import (
    _collect_ids_from_payloads,
    _derive_prompt_context,
    _get_recap_run_trace,
    _load_canonical_event_rows,
)


def _compute_eal(db_path: str, league_id: str, season: int,
                 week_index: int) -> str:
    """Reproduce the lifecycle's EAL evaluation."""
    included_count = None
    is_playoff = False
    with DatabaseSession(db_path) as con:
        row = con.execute(
            "SELECT canonical_ids_json FROM recap_runs"
            " WHERE league_id=? AND season=? AND week_index=?",
            (league_id, season, week_index),
        ).fetchone()
        if row and row[0]:
            try:
                ids = json.loads(row[0])
                if isinstance(ids, list):
                    included_count = len(ids)
            except (ValueError, TypeError):
                pass
        try:
            last_reg_row = con.execute(
                "SELECT MAX(week) FROM ("
                "  SELECT CAST(json_extract(payload_json, '$.week') AS INTEGER) as week,"
                "         COUNT(*) as cnt"
                "  FROM v_canonical_best_events"
                "  WHERE league_id=? AND season=? AND event_type='WEEKLY_MATCHUP_RESULT'"
                "  GROUP BY json_extract(payload_json, '$.week')"
                "  HAVING cnt = ("
                "    SELECT MAX(cnt2) FROM ("
                "      SELECT COUNT(*) as cnt2 FROM v_canonical_best_events"
                "      WHERE league_id=? AND season=? AND event_type='WEEKLY_MATCHUP_RESULT'"
                "      GROUP BY json_extract(payload_json, '$.week')"
                "    )"
                "  )"
                ")",
                (league_id, season, league_id, season),
            ).fetchone()
            if last_reg_row and last_reg_row[0] and week_index > last_reg_row[0]:
                is_playoff = True
        except Exception:
            pass
    meta = EALMeta(
        has_selection_set=True, has_window=True,
        included_count=included_count, excluded_count=None,
        is_playoff=is_playoff,
    )
    return evaluate_editorial_attunement_v1(meta)


def _load_creative_bullets(db_path: str, league_id: str, season: int,
                           week_index: int) -> list[str]:
    """Reproduce the lifecycle's creative bullet rendering."""
    with DatabaseSession(db_path) as con:
        row = con.execute(
            "SELECT canonical_ids_json FROM recap_runs"
            " WHERE league_id=? AND season=? AND week_index=?",
            (league_id, season, week_index),
        ).fetchone()
        if not row or not row[0]:
            return []
        try:
            ids = json.loads(row[0])
            if not isinstance(ids, list) or not ids:
                return []
        except (ValueError, TypeError):
            return []
    events = _load_canonical_event_rows(db_path, ids)
    if not events:
        return []
    pids, fids = _collect_ids_from_payloads(events)
    pres = PlayerResolver(db_path, league_id, season)
    fres = FranchiseResolver(db_path, league_id, season)
    if pids:
        pres.load_for_ids(pids)
    if fids:
        fres.load_for_ids(fids)
    return render_deterministic_bullets_v1(
        events, team_resolver=fres.one, player_resolver=pres.one,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Diagnose a single draft.")
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--attempts", type=int, default=1,
                    help="Number of independent drafts to generate")
    ap.add_argument("--output", default=None)
    args = ap.parse_args()

    state = get_recap_run_state(args.db, args.league_id, args.season, args.week)
    if state is None:
        print(f"ERROR: No recap_runs data for week {args.week}")
        return 1

    eal = _compute_eal(args.db, args.league_id, args.season, args.week)
    _, _, window_end = _get_recap_run_trace(
        args.db, args.league_id, args.season, args.week,
    )
    ctx = _derive_prompt_context(
        db_path=args.db, league_id=args.league_id, season=args.season,
        week_index=args.week, window_end=window_end,
    )
    bullets = _load_creative_bullets(
        args.db, args.league_id, args.season, args.week,
    )

    sep = "=" * 72
    parts: list[str] = []

    for attempt in range(1, args.attempts + 1):
        parts.append(f"{sep}")
        parts.append(f"ATTEMPT {attempt}/{args.attempts}")
        parts.append(f"{sep}")
        parts.append("")

        draft = draft_narrative_v1(
            facts_bullets=bullets,
            eal_directive=eal,
            league_id=args.league_id,
            season=args.season,
            week_index=args.week,
            season_context=ctx.season_context_text,
            league_history=ctx.league_history_text,
            narrative_angles=ctx.narrative_angles_text,
            writer_room_context=ctx.writer_room_text,
            player_highlights=ctx.player_highlights_text,
            tone_preset=ctx.tone_preset,
            voice_profile=ctx.voice_profile,
            seasons_count=ctx.seasons_count,
            verification_feedback="",
        )

        if not draft:
            parts.append("(no draft produced — API key missing or EAL silence)")
            parts.append("")
            continue

        parts.append("DRAFT TEXT:")
        parts.append("-" * 40)
        parts.append(draft)
        parts.append("-" * 40)
        parts.append("")

        # Build the rendered_text the same way the lifecycle does
        rendered_for_verify = (
            "placeholder\n\n--- SHAREABLE RECAP ---\n"
            + draft
            + "\n--- END SHAREABLE RECAP ---\n"
        )

        try:
            result = verify_recap_v1(
                rendered_for_verify,
                db_path=args.db,
                league_id=args.league_id,
                season=args.season,
                week=args.week,
            )
        except Exception as e:
            parts.append(f"VERIFICATION ERROR: {e}")
            parts.append("")
            continue

        if result.passed:
            soft_count = len(result.soft_failures)
            parts.append(
                f"VERIFICATION: PASSED ({result.checks_run} checks, "
                f"{soft_count} soft warnings)"
            )
            for sf in result.soft_failures:
                parts.append(f"  [SOFT] {sf.category}: {sf.claim}")
        else:
            parts.append(
                f"VERIFICATION: FAILED ({result.hard_failure_count} hard, "
                f"{len(result.soft_failures)} soft)"
            )
            for hf in result.hard_failures:
                parts.append(f"  [HARD] {hf.category}: {hf.claim}")
                parts.append(f"         Evidence: {hf.evidence}")
                parts.append("")

        parts.append("")

    output = "\n".join(parts)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Written to {args.output}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
