#!/usr/bin/env python3
"""Dump the exact prompt payload that the creative layer would receive.

Usage:
    ./scripts/py scripts/dump_prompt.py \
        --db .local_squadvault.sqlite \
        --league-id 70985 --season 2025 --week 1

    # Write to file instead of stdout:
    ./scripts/py scripts/dump_prompt.py \
        --db .local_squadvault.sqlite \
        --league-id 70985 --season 2025 --week 1 \
        --output prompt_week1.txt

Reconstructs the complete system prompt and user prompt by running the
same derivation pipeline as generate_weekly_recap_draft, but stops before
the API call. Use this to diagnose *why* the model fabricates — inspect
what it actually sees.
"""
from __future__ import annotations

import argparse
import json

from squadvault.ai.creative_layer_v1 import (
    _EAL_TEMPERATURE,
    _MODEL,
    _TEMPERATURE,
    _build_system_prompt,
    _build_user_prompt,
)
from squadvault.core.eal.editorial_attunement_v1 import (
    EALMeta,
    evaluate_editorial_attunement_v1,
)
from squadvault.core.recaps.recap_runs import get_recap_run_state
from squadvault.core.recaps.render.deterministic_bullets_v1 import (
    render_deterministic_bullets_v1,
)
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
            last_regular_week = last_reg_row[0] if last_reg_row else None
            if last_regular_week and week_index > last_regular_week:
                is_playoff = True
        except Exception:
            pass

    meta = EALMeta(
        has_selection_set=True,
        has_window=True,
        included_count=included_count,
        excluded_count=None,
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
    ap = argparse.ArgumentParser(description="Dump creative layer prompt payload.")
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--output", default=None,
                    help="Write to file instead of stdout")
    args = ap.parse_args()

    # Verify recap_runs data exists
    state = get_recap_run_state(args.db, args.league_id, args.season, args.week)
    if state is None:
        print(f"ERROR: No recap_runs data for league={args.league_id} "
              f"season={args.season} week={args.week}")
        return 1

    # EAL
    eal_directive = _compute_eal(args.db, args.league_id, args.season, args.week)
    temperature = _EAL_TEMPERATURE.get(eal_directive, _TEMPERATURE)

    # Window
    _, window_start, window_end = _get_recap_run_trace(
        args.db, args.league_id, args.season, args.week,
    )

    # Context
    ctx = _derive_prompt_context(
        db_path=args.db, league_id=args.league_id, season=args.season,
        week_index=args.week, window_end=window_end,
    )

    # Facts bullets
    bullets = _load_creative_bullets(
        args.db, args.league_id, args.season, args.week,
    )

    # Build prompts
    system_prompt = _build_system_prompt(ctx.tone_preset, voice_profile=ctx.voice_profile)
    user_prompt = _build_user_prompt(
        facts_bullets=bullets,
        eal_directive=eal_directive,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week,
        season_context=ctx.season_context_text,
        league_history=ctx.league_history_text,
        narrative_angles=ctx.narrative_angles_text,
        writer_room_context=ctx.writer_room_text,
        player_highlights=ctx.player_highlights_text,
        tone_preset=ctx.tone_preset,
        seasons_count=ctx.seasons_count,
        verification_feedback="",
    )

    # Stats
    sys_tokens_approx = len(system_prompt.split())
    user_tokens_approx = len(user_prompt.split())
    angle_lines = [
        ln for ln in ctx.narrative_angles_text.strip().splitlines()
        if ln.strip().startswith("[")
    ]
    rivalry_angles = [ln for ln in angle_lines if "RIVALRY" in ln.upper()]

    # Format output
    sep = "=" * 72
    output_parts = [
        f"{sep}",
        f"PROMPT DUMP: league={args.league_id} season={args.season} week={args.week}",
        f"{sep}",
        "",
        f"EAL directive  : {eal_directive}",
        f"Temperature    : {temperature}",
        f"Model          : {_MODEL}",
        f"Window         : {window_start} → {window_end}",
        f"Facts bullets   : {len(bullets)}",
        f"Angle lines    : {len(angle_lines)}",
        f"Rivalry angles : {len(rivalry_angles)}",
        f"Approx tokens  : system ~{sys_tokens_approx} words, user ~{user_tokens_approx} words",
        "",
        f"{sep}",
        "SYSTEM PROMPT",
        f"{sep}",
        "",
        system_prompt,
        "",
        f"{sep}",
        "USER PROMPT",
        f"{sep}",
        "",
        user_prompt,
        "",
        f"{sep}",
        "NARRATIVE ANGLES (extracted)",
        f"{sep}",
        "",
    ]

    if angle_lines:
        for ln in angle_lines:
            output_parts.append(f"  {ln.strip()}")
    else:
        output_parts.append("  (none)")

    output_parts.append("")

    if rivalry_angles:
        output_parts.append(f"{sep}")
        output_parts.append("RIVALRY ANGLES (focus)")
        output_parts.append(f"{sep}")
        output_parts.append("")
        for ln in rivalry_angles:
            output_parts.append(f"  {ln.strip()}")
        output_parts.append("")

    full_output = "\n".join(output_parts)

    if args.output:
        with open(args.output, "w") as f:
            f.write(full_output)
        print(f"Written to {args.output} ({len(full_output):,} chars)")
    else:
        print(full_output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
