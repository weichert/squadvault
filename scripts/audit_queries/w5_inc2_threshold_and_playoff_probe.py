#!/usr/bin/env python3
"""W.5 increment 2 - threshold + playoff-derivability probe (D2 + D3).

Run against the LOCAL engine DB (the 17-season PFL Buddies data):

    ./scripts/py scripts/audit_queries/w5_inc2_threshold_and_playoff_probe.py --league-id 70985

D2 (The Executioner threshold): prints the all-time victory-margin distribution and,
for each candidate threshold, how many blowout wins exist and which franchise holds the
most (so the threshold is chosen knowing the frequency, not guessed).

D3 (The Unbroken Chain derivability): for each season, lists the franchises that appear
in CHAMPIONSHIP-WEEK matchups, and flags whether that set looks like a clean playoff
bracket (small subset) or the whole league (i.e. consolation games are mixed in and
"made the playoffs" is NOT exactly derivable -> defer per silence-over-speculation).

NOTE: schema-tolerant best effort. If table/column names differ in this DB, hand this
to a Claude Code session with the DB - it can adapt the two queries and run them.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter, defaultdict

DEFAULT_DB = ".local_squadvault.sqlite"
DEFAULT_LEAGUE = "70985"
CANDIDATE_THRESHOLDS = [30, 35, 40, 45, 50, 55, 60]


def champ_week(season: int) -> int:
    return 16 if season <= 2020 else 18


def load_matchups(conn, league_id):
    """Return list of dicts: season, week, winner_fid, loser_fid, w_score, l_score, is_tie."""
    rows = conn.execute(
        """
        SELECT ce.season, me.payload_json
        FROM canonical_events ce
        JOIN memory_events me ON me.id = ce.best_memory_event_id
        WHERE ce.league_id = ? AND ce.event_type = 'WEEKLY_MATCHUP_RESULT'
        """,
        (str(league_id),),
    ).fetchall()
    out = []
    for season, payload_json in rows:
        p = json.loads(payload_json)
        try:
            ws = float(p.get("winner_score") or 0)
            ls = float(p.get("loser_score") or 0)
        except (TypeError, ValueError):
            ws = ls = 0.0
        out.append({
            "season": int(season),
            "week": int(p.get("week") or 0),
            "winner_fid": str(p.get("winner_franchise_id") or ""),
            "loser_fid": str(p.get("loser_franchise_id") or ""),
            "w_score": ws, "l_score": ls,
            "is_tie": bool(p.get("is_tie", False)),
        })
    return out


def d2_threshold(matchups):
    print("\n=== D2: The Executioner - victory-margin distribution ===")
    margins = [round(m["w_score"] - m["l_score"], 2) for m in matchups if not m["is_tie"]]
    margins = [x for x in margins if x >= 0]
    if not margins:
        print("  (no non-tie matchups found - check schema)")
        return
    buckets = Counter()
    for x in margins:
        buckets[int(x // 10) * 10] += 1
    print(f"  total decided games: {len(margins)}  max margin: {max(margins):.2f}")
    for lo in sorted(buckets):
        print(f"   {lo:>3}-{lo+9:<3} pts: {buckets[lo]:>4}")
    print("\n  per candidate threshold (blowout = win by >= T):")
    for t in CANDIDATE_THRESHOLDS:
        per_fr = Counter(m["winner_fid"] for m in matchups
                         if not m["is_tie"] and (m["w_score"] - m["l_score"]) >= t)
        total = sum(per_fr.values())
        leader = per_fr.most_common(1)
        held = f"{leader[0][0]} ({leader[0][1]})" if leader else "-"
        print(f"   >= {t:>3}: {total:>4} blowouts across history | most-held: {held}")
    print("  -> pick T where the count feels rewarding-but-rare; holder shown per T.")


def d3_playoff(matchups):
    print("\n=== D3: The Unbroken Chain - playoff-appearance derivability ===")
    by_season = defaultdict(set)        # season -> franchises in championship-week matchups
    league_by_season = defaultdict(set)  # season -> all franchises seen that season
    for m in matchups:
        league_by_season[m["season"]].add(m["winner_fid"])
        league_by_season[m["season"]].add(m["loser_fid"])
        if m["week"] >= champ_week(m["season"]):
            by_season[m["season"]].add(m["winner_fid"])
            by_season[m["season"]].add(m["loser_fid"])
    print("  season | champ-week participants | league size | clean-bracket?")
    ambiguous = 0
    for season in sorted(league_by_season):
        cw = len(by_season.get(season, set()))
        ls = len(league_by_season[season])
        # heuristic: if ~all teams appear in champ-week games, consolation is mixed in -> ambiguous
        clean = "yes" if 0 < cw < ls else ("NO (all teams -> consolation mixed)" if cw >= ls else "none")
        if clean.startswith("NO"):
            ambiguous += 1
        print(f"   {season}  |  {cw:>3}  |  {ls:>3}  |  {clean}")
    print(f"\n  ambiguous seasons (playoff entrants NOT cleanly separable): {ambiguous}")
    print("  -> if >0, 'made the playoffs' is not exactly derivable from matchups alone;")
    print("     The Unbroken Chain DEFERS per silence-over-speculation, unless the")
    print("     championship_timeline bracket aggregation yields clean entrants per season.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--league-id", default=DEFAULT_LEAGUE)
    ap.add_argument("--db", default=DEFAULT_DB)
    args = ap.parse_args()
    conn = sqlite3.connect(args.db)
    matchups = load_matchups(conn, args.league_id)
    print(f"loaded {len(matchups)} WEEKLY_MATCHUP_RESULT rows for league {args.league_id}")
    d2_threshold(matchups)
    d3_playoff(matchups)
    conn.close()


if __name__ == "__main__":
    main()
