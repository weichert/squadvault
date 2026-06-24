#!/usr/bin/env python3
"""gen_supabase_rebuild.py (v2) -- emit the PFL Buddies real-data seed.

Reads two JSON inputs produced by the engine-reading generators:
  --records       franchise_records_*.json   (gen_franchise_records.py)
  --season-names  season_names_*.json         (gen_season_names.py --emit-json)

Emits ONE idempotent SQL transaction (FK-safe DELETE then INSERT) that:
  1. clears trophy_room_entries, franchise_season_records, franchise_season_names,
     and franchises for league canonical_id 70985,
  2. inserts the 10 real franchises (current display names; charter per policy),
  3. inserts CHAMPIONSHIP trophies with ERA-CORRECT titles -- the team name as it
     existed in the title season (e.g. 2016 reads "SS Express", not the current
     "Brandon Knows Ball"),
  4. inserts the 160 franchise_season_records (full 2010-2025 history),
  5. inserts the 160 franchise_season_names (season-scoped team names).

Every franchise reference resolves by (league canonical_id, canonical_franchise_id);
no UUIDs are hardcoded. Wrapped in BEGIN/COMMIT and re-runnable. This is the
canonical REAL seed of record -- intended for production; it carries NO demo
guard (unlike seed/001). Output goes to supabase/seed/003_pfl_buddies_real.sql.

PREREQUISITE: migrations 008 (franchise_season_records) AND 009
(franchise_season_names) must be applied first.

Pure stdlib; does not import the engine. Read-only on the JSON inputs.

USAGE:
  python3 ~/sv-apply/gen_supabase_rebuild.py \
      --records ~/sv-apply/franchise_records_70985.json \
      --season-names ~/sv-apply/season_names_70985.json \
      --out ~/sv-apply/003_pfl_buddies_real.sql
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from typing import Any

# Current display names (the franchise's present banner / hero name). These are
# correct for the franchises.owner_display_name column. ERA-correct names for
# trophies and the names table come from the --season-names JSON, NOT from here.
ROSTER = {
    "0001": "Stu's Crew",
    "0002": "Paradis' Playmakers",
    "0003": "Purple Haze",
    "0004": "Eddie & the Cruisers",
    "0005": "Weichert's Warmongers",
    "0006": "Miller's Genuine Draft",
    "0007": "Robb's Raiders",
    "0008": "Ben's Gods",
    "0009": "Italian Cavallini",
    "0010": "Brandon Knows Ball",
}

# Charter membership is a HUMAN fact, not derivable from franchise-slot data.
# Slot 0010 turned over within the data era (SS Express -> Neal's -> Baber's ->
# Jack of All Trades -> Brandon Knows Ball), so its current occupant is not a
# charter member. All other slots held continuously.
NON_CHARTER = {"0010"}


def q(s: str) -> str:
    """SQL single-quoted literal with quote-doubling."""
    return "'" + s.replace("'", "''") + "'"


def emit_backfill(rows: list[dict[str, Any]], league: str) -> str:
    """W.5 Inc 2 Wave 2 - a TARGETED UPDATE backfill of the two new columns
    (points_against, blowout_wins_60), NOT a destructive rebuild. Touches only those
    columns on existing rows, matched by (league, canonical_franchise_id, season).
    Paste-safe for the Supabase SQL editor: no semicolons inside comments."""
    out: list[str] = []
    w = out.append
    w("-- W.5 Inc 2 Wave 2 backfill - points_against (regular season) + blowout_wins_60 (all games).")
    w("-- TARGETED UPDATE, not a rebuild: only the two new columns on existing rows are written.")
    w("-- Prerequisite: migration 027 added the columns. Generated - do not hand-edit.")
    w("BEGIN;")
    w("UPDATE franchise_season_records AS fsr")
    w("SET points_against = v.pa, blowout_wins_60 = v.bw")
    w("FROM (VALUES")
    vals = []
    for r in sorted(rows, key=lambda d: (d["franchise_id"], int(d["season"]))):
        vals.append(
            f"  ({q(r['franchise_id'])}, {int(r['season'])}, "
            f"{float(r['points_against'])}, {int(r['blowout_wins_60'])})"
        )
    w(",\n".join(vals))
    w(") AS v(fid, season, pa, bw)")
    w(f"JOIN leagues l ON l.canonical_id = {q(league)}")
    w("JOIN franchises f ON f.league_id = l.id AND f.canonical_franchise_id = v.fid")
    w("WHERE fsr.league_id = l.id AND fsr.franchise_id = f.id AND fsr.season = v.season;")
    w("COMMIT;")
    w("")
    return "\n".join(out)


def emit_correction(rows: list[dict[str, Any]], league: str) -> str:
    """Championship Week 17 correction - a TARGETED, idempotent, FK-SAFE UPDATE of the five
    mutable franchise_season_records columns (wins, losses, points_for, points_against,
    blowout_wins_60) for the 2021+ rows, matched by (league, canonical_franchise_id, season).

    NOT a re-seed (Hard Rule 1): no DELETE/INSERT, so franchise UUIDs and every FK from
    season_award_winners / trophy custody are preserved. 2010-2020 rows are NOT touched (their
    championship is wk16, unaffected). Idempotent: re-running sets the same known values. The
    2021+ wk18 championship phantom is collapsed at the canonical layer (engine R1), so the
    regular-season stats here no longer include the title game; this re-points the published
    franchise_season_records to that corrected truth."""
    out: list[str] = []
    w = out.append
    w("-- supabase/migrations/029_franchise_season_records_champ_week_correction.sql")
    w("-- Championship Week 17 correction (engine ad37ec9). This league's 2021+ championship is")
    w("-- wk17 - the bracket ends 10->8->4->2 at wk17. The wk18 phantom is collapsed at the")
    w("-- canonical layer, so regular-season wins/losses/points + points_against no longer count")
    w("-- the title game. TARGETED idempotent FK-SAFE UPDATE of the five mutable columns for the")
    w("-- 2021+ rows - NOT a re-seed (preserves every franchise UUID and FK, per Hard Rule 1).")
    w("-- 2010-2020 untouched.")
    w("-- Generated by scripts/gen_supabase_rebuild.py --correction - do not hand-edit. Paste-safe.")
    w("BEGIN;")
    w("UPDATE franchise_season_records AS fsr")
    w("SET wins = v.wins, losses = v.losses, points_for = v.pf, "
      "points_against = v.pa, blowout_wins_60 = v.bw")
    w("FROM (VALUES")
    vals = []
    for r in sorted((x for x in rows if int(x["season"]) >= 2021),
                    key=lambda d: (d["franchise_id"], int(d["season"]))):
        vals.append(
            f"  ({q(r['franchise_id'])}, {int(r['season'])}, {int(r['wins'])}, "
            f"{int(r['losses'])}, {float(r['points_for'])}, {float(r['points_against'])}, "
            f"{int(r['blowout_wins_60'])})"
        )
    w(",\n".join(vals))
    w(") AS v(fid, season, wins, losses, pf, pa, bw)")
    w(f"JOIN leagues l ON l.canonical_id = {q(league)}")
    w("JOIN franchises f ON f.league_id = l.id AND f.canonical_franchise_id = v.fid")
    w("WHERE fsr.league_id = l.id AND fsr.franchise_id = f.id AND fsr.season = v.season;")
    w("COMMIT;")
    w("")
    return "\n".join(out)


def emit_wl_correction(rows: list[dict[str, Any]], league: str) -> str:
    """Migration 030 - the W-L + points_for regular-season correction across ALL 16 seasons.

    The championship final was leaking into the two finalists' W-L and points_for every season
    (champion +1 win, runner-up +1 loss, both PF inflated by the final's score) - only
    points_against had excluded it. This re-points wins/losses/points_for to REGULAR-SEASON
    (exclude the final), consistent with points_against and the recap verifier. SUPERSEDES the
    W-L portion of migration 029 for 2021+ and adds the 2010-2020 finalists 029 never touched.

    Updates wins/losses/points_for ONLY (ties, points_against, blowout_wins_60 are already
    correct on prod and untouched). TARGETED, idempotent, FK-SAFE UPDATE - NOT a re-seed
    (preserves every franchise UUID and FK). Emits all rows; non-finalists are idempotent
    no-ops, the 32 finalist rows are corrected."""
    out: list[str] = []
    w = out.append
    w("-- supabase/migrations/030_franchise_season_records_wl_regseason_correction.sql")
    w("-- W-L + points_for regular-season correction (engine gen_franchise_records fix). The")
    w("-- championship final was leaking into the two finalists' W-L + points_for every season")
    w("-- (champion +1 win, runner-up +1 loss, both PF inflated) - only points_against excluded it.")
    w("-- Re-points wins/losses/points_for to regular-season (exclude the final) for ALL 16 seasons,")
    w("-- consistent with points_against and the verifier. SUPERSEDES migration 029's W-L portion")
    w("-- for 2021+ and adds the 2010-2020 finalists. Updates wins/losses/points_for only (ties,")
    w("-- points_against, blowout_wins_60 unchanged). TARGETED idempotent FK-SAFE UPDATE - NOT a")
    w("-- re-seed. Generated by scripts/gen_supabase_rebuild.py --wl-correction - do not hand-edit.")
    w("-- Paste-safe.")
    w("BEGIN;")
    w("UPDATE franchise_season_records AS fsr")
    w("SET wins = v.wins, losses = v.losses, points_for = v.pf")
    w("FROM (VALUES")
    vals = []
    for r in sorted(rows, key=lambda d: (d["franchise_id"], int(d["season"]))):
        vals.append(
            f"  ({q(r['franchise_id'])}, {int(r['season'])}, {int(r['wins'])}, "
            f"{int(r['losses'])}, {float(r['points_for'])})"
        )
    w(",\n".join(vals))
    w(") AS v(fid, season, wins, losses, pf)")
    w(f"JOIN leagues l ON l.canonical_id = {q(league)}")
    w("JOIN franchises f ON f.league_id = l.id AND f.canonical_franchise_id = v.fid")
    w("WHERE fsr.league_id = l.id AND fsr.franchise_id = f.id AND fsr.season = v.season;")
    w("COMMIT;")
    w("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Emit PFL real-data seed (era-correct).")
    ap.add_argument("--records", required=True, help="franchise_records_*.json")
    ap.add_argument("--season-names", help="season_names_*.json (rebuild only)")
    ap.add_argument("--out", required=True, help="output .sql path")
    ap.add_argument("--league", default="70985", help="league canonical_id")
    ap.add_argument("--backfill", action="store_true",
                    help="emit a TARGETED UPDATE backfill of points_against + blowout_wins_60 "
                         "(W.5 Inc 2 Wave 2), instead of the full rebuild")
    ap.add_argument("--correction", action="store_true",
                    help="emit the championship-week (wk17) TARGETED UPDATE correction of the five "
                         "mutable franchise_season_records columns for 2021+ rows (NOT a re-seed)")
    ap.add_argument("--wl-correction", action="store_true",
                    help="emit migration 030: the W-L + points_for regular-season correction "
                         "(wins/losses/points_for) across ALL 16 seasons (NOT a re-seed)")
    args = ap.parse_args(argv)

    with open(args.records) as f:
        rows: list[dict[str, Any]] = json.load(f)

    if args.wl_correction:
        sql = emit_wl_correction(rows, args.league)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(sql)
        print(f"Wrote W-L correction {args.out}: {len(rows)} rows all seasons "
              "(wins/losses/points_for targeted UPDATE).")
        return 0

    if args.correction:
        sql = emit_correction(rows, args.league)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(sql)
        n_corr = sum(1 for r in rows if int(r["season"]) >= 2021)
        print(f"Wrote correction {args.out}: {n_corr} 2021+ rows (5-column targeted UPDATE).")
        return 0

    if args.backfill:
        sql = emit_backfill(rows, args.league)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(sql)
        print(f"Wrote backfill {args.out}: {len(rows)} rows "
              "(points_against + blowout_wins_60, targeted UPDATE).")
        return 0

    if not args.season_names:
        raise SystemExit("--season-names is required for the full rebuild (omit only with --backfill)")
    with open(args.season_names) as f:
        name_rows: list[dict[str, Any]] = json.load(f)

    # Era-correct name map: (fid, season) -> team_name.
    era_name: dict[tuple[str, int], str] = {
        (str(n["franchise_id"]), int(n["season"])): str(n["team_name"])
        for n in name_rows
    }

    fids = sorted({r["franchise_id"] for r in rows})
    unknown = [f for f in fids if f not in ROSTER]
    if unknown:
        raise SystemExit(f"records contain fids not in verified roster: {unknown}")

    seasons_by_fid: dict[str, list[int]] = defaultdict(list)
    for r in rows:
        seasons_by_fid[r["franchise_id"]].append(int(r["season"]))

    champions = sorted(
        (int(r["season"]), r["franchise_id"])
        for r in rows
        if r["result"] == "CHAMPION"
    )

    # Every champion must have an era name; fail loud rather than fall back to
    # the current name (which would silently reintroduce the misattribution).
    missing = [(s, f) for s, f in champions if (f, s) not in era_name]
    if missing:
        raise SystemExit(f"champions missing era names: {missing}")

    name_rows_sorted = sorted(
        name_rows, key=lambda n: (str(n["franchise_id"]), int(n["season"]))
    )

    lid = f"(SELECT id FROM leagues WHERE canonical_id = {q(args.league)})"
    out: list[str] = []
    w = out.append

    w("-- supabase/seed/003_pfl_buddies_real.sql")
    w("-- PFL Buddies real-data seed (era-correct). Generated; do not hand-edit.")
    w(f"-- league {args.league}: {len(fids)} franchises, {len(champions)} champions, "
      f"{len(rows)} season records, {len(name_rows)} season names.")
    n_charter = sum(1 for f in fids if f not in NON_CHARTER)
    w(f"-- charter members: {n_charter} (non-charter: {sorted(NON_CHARTER)}).")
    w("-- Prerequisite: migrations 008 and 009 applied first.")
    w("-- Real data, production-intended: NO demo guard (cf. seed/001).")
    w("BEGIN;")
    w("")
    w("-- 1. Clear any existing dataset for this league (FK-safe order).")
    w(f"DELETE FROM trophy_room_entries WHERE league_id = {lid};")
    w(f"DELETE FROM franchise_season_records WHERE league_id = {lid};")
    w(f"DELETE FROM franchise_season_names WHERE league_id = {lid};")
    w(f"DELETE FROM franchises WHERE league_id = {lid};")
    w("")
    w("-- 2. Real franchises (current display names; canonical_franchise_id 0001..0010).")
    w("INSERT INTO franchises")
    w("  (league_id, canonical_franchise_id, owner_display_name, charter_member, seasons_active)")
    w("SELECT l.id, v.fid, v.name, v.charter, v.seasons::integer[]")
    w("FROM (VALUES")
    fr_vals = []
    for fid in fids:
        sea = sorted(set(seasons_by_fid[fid]))
        arr = "'{" + ",".join(str(s) for s in sea) + "}'"
        charter = "false" if fid in NON_CHARTER else "true"
        fr_vals.append(f"  ({q(fid)}, {q(ROSTER[fid])}, {charter}, {arr})")
    w(",\n".join(fr_vals))
    w(") AS v(fid, name, charter, seasons)")
    w(f"JOIN leagues l ON l.canonical_id = {q(args.league)};")
    w("")
    w("-- 3. Championship trophies, ERA-CORRECT titles (name as of the title season).")
    w("INSERT INTO trophy_room_entries")
    w("  (league_id, entry_type, season, franchise_id, title, provenance)")
    w("SELECT l.id, 'CHAMPIONSHIP', v.season, f.id, v.title, 'CANONICAL'")
    w("FROM (VALUES")
    tr_vals = []
    for season, fid in champions:
        ename = era_name[(fid, season)]
        title = f"{ename} - {season} PFL Buddies Champion"
        tr_vals.append(f"  ({season}, {q(fid)}, {q(title)})")
    w(",\n".join(tr_vals))
    w(") AS v(season, fid, title)")
    w(f"JOIN leagues l ON l.canonical_id = {q(args.league)}")
    w("JOIN franchises f ON f.league_id = l.id AND f.canonical_franchise_id = v.fid;")
    w("")
    w("-- 4. Per-franchise per-season records (full 2010-2025 history).")
    w("INSERT INTO franchise_season_records")
    w("  (league_id, franchise_id, season, wins, losses, ties, points_for,")
    w("   points_against, blowout_wins_60, result, provenance)")
    w("SELECT l.id, f.id, v.season, v.wins, v.losses, v.ties, v.pf,")
    w("       v.pa, v.bw, v.result, 'engine:matchup-derived'")
    w("FROM (VALUES")
    rec_vals = []
    for r in sorted(rows, key=lambda d: (d["franchise_id"], int(d["season"]))):
        rec_vals.append(
            f"  ({q(r['franchise_id'])}, {int(r['season'])}, {int(r['wins'])}, "
            f"{int(r['losses'])}, {int(r['ties'])}, {float(r['points_for'])}, "
            f"{float(r.get('points_against', 0.0))}, {int(r.get('blowout_wins_60', 0))}, "
            f"{q(r['result'])})"
        )
    w(",\n".join(rec_vals))
    w(") AS v(fid, season, wins, losses, ties, pf, pa, bw, result)")
    w(f"JOIN leagues l ON l.canonical_id = {q(args.league)}")
    w("JOIN franchises f ON f.league_id = l.id AND f.canonical_franchise_id = v.fid;")
    w("")
    w("-- 5. Season-scoped team names (era-correct attribution source).")
    w("INSERT INTO franchise_season_names")
    w("  (league_id, canonical_franchise_id, season, team_name)")
    w("SELECT l.id, v.cfid, v.season, v.team_name")
    w("FROM (VALUES")
    nm_vals = []
    for n in name_rows_sorted:
        nm_vals.append(
            f"  ({q(str(n['franchise_id']))}, {int(n['season'])}, "
            f"{q(str(n['team_name']))})"
        )
    w(",\n".join(nm_vals))
    w(") AS v(cfid, season, team_name)")
    w(f"JOIN leagues l ON l.canonical_id = {q(args.league)};")
    w("")
    w("COMMIT;")
    w("")

    sql = "\n".join(out)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(sql)
    print(f"Wrote {args.out}: {len(fids)} franchises ({n_charter} charter), "
          f"{len(champions)} champions (era-correct titles), "
          f"{len(rows)} records, {len(name_rows)} names.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
