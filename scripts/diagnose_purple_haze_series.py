#!/usr/bin/env python3
"""Diagnose Purple Haze SERIES failures in 2025 W4 / W10 / W13.

Pulls in one pass:
  - The narrative_angles_text the model received (lines relevant to the
    Purple Haze pair + any [NO H2H DATA] markers + the full RIVALRY
    block for cross-attribution checking).
  - The ±220-char prose window around the target W-L ("9-12" / "8-2" /
    "8-5") in narrative_draft.
  - Whether the prose contains "under current ownership" / "current
    ownership" anywhere near the claim (drives the verifier tenure-skip
    decision).
  - Live all-time and tenure-scoped H2H computation for each pair, plus
    which rivalry tier (if any) the detector would emit right now.
  - Purple Haze's 2025 season W-L through W13 (to confirm or rule out
    the subcase where the model conflated season record with series).

Usage:
    set -a; source .env.local; set +a
    scripts/py scripts/diagnose_purple_haze_series.py \\
        --db .local_squadvault.sqlite --league-id 70985

Output: /tmp/purple_haze_series_diagnosis.txt
Read-only: no DB writes, no model calls.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from squadvault.core.recaps.context.league_history_v1 import (
    compute_franchise_tenures,
    compute_head_to_head,
    load_all_matchups,
)
from squadvault.core.storage.session import DatabaseSession

# Each target describes what we expect to see in the model's prose and
# which pair the verifier flagged.  The "kind" column is just a label
# so the output clearly distinguishes the W4 correct case from the two
# failure cases.
TARGETS = {
    4:  {"target": "9-12", "opponents": ("Purple Haze", "Stu's Crew"),
         "kind": "CORRECT (W4 — matches all-time)"},
    10: {"target": "8-2",  "opponents": ("Purple Haze", "Stu's Crew"),
         "kind": "FAILURE (W10 — verifier flagged)"},
    13: {"target": "8-5",  "opponents": ("Purple Haze", "Miller's Genuine Draft"),
         "kind": "FAILURE (W13 — verifier flagged)"},
}


def _norm_apos(s: str) -> str:
    """Normalize curly apostrophes to straight — franchise names may have either."""
    return s.replace("\u2019", "'").replace("\u2018", "'") if s else s


def _resolve_franchise_id(con, league_id: str, season: int, name_hint: str) -> str | None:
    """Find franchise_id by best-effort name match in the given season."""
    rows = con.execute(
        "SELECT franchise_id, name FROM franchise_directory "
        "WHERE league_id = ? AND season = ? AND name IS NOT NULL",
        (league_id, season),
    ).fetchall()
    needle = _norm_apos(name_hint).lower()
    # Exact match first
    for fid, name in rows:
        if _norm_apos(name or "").strip().lower() == needle:
            return str(fid)
    # Substring fallback (first word or distinctive token)
    for fid, name in rows:
        if needle in _norm_apos(name or "").strip().lower():
            return str(fid)
    # Looser: match on first word
    first = needle.split()[0] if needle else ""
    if first:
        for fid, name in rows:
            if first in _norm_apos(name or "").strip().lower():
                return str(fid)
    return None


def _slice_around(text: str, target: str, radius: int = 220) -> list[tuple[int, str]]:
    """Return ALL ±radius windows around target (not just the first).

    Returns list of (char_offset, window_text). Empty if target absent.
    """
    if not text:
        return []
    windows: list[tuple[int, str]] = []
    start_search = 0
    while True:
        idx = text.find(target, start_search)
        if idx < 0:
            break
        start = max(0, idx - radius)
        end = min(len(text), idx + len(target) + radius)
        windows.append((idx, text[start:end]))
        start_search = idx + len(target)
    return windows


def _qualifier_near(prose_window: str) -> str:
    """Classify whether a scope qualifier appears in a prose window.

    Mirrors the verifier's tenure-skip patterns plus a few obvious
    paraphrases the model might use (these are NOT currently in the
    verifier — they're diagnostic hints).
    """
    low = prose_window.lower()
    hits = []
    if "under current ownership" in low:
        hits.append("under current ownership")
    if "current ownership" in low and "under current ownership" not in low:
        hits.append("current ownership (unprefixed)")
    if "current owner" in low:
        hits.append("current owner")
    if "tenure" in low:
        hits.append("tenure")
    if "since" in low and ("took over" in low or "joined" in low):
        hits.append("since <owner> took over / joined (paraphrase)")
    if "all-time" in low or "all time" in low:
        hits.append("all-time (explicit all-time claim — NO skip)")
    return ", ".join(hits) if hits else "(none — verifier would NOT skip)"


def _dump_prompt_audit_for_week(con, out, league_id: str, season: int,
                                  week_index: int, target: dict) -> None:
    out.write(f"\n{'='*78}\n")
    out.write(f"=== W{week_index} — {target['kind']}\n")
    out.write(f"=== Target record in prose: \"{target['target']}\"\n")
    out.write(f"=== Opponents: {' vs '.join(target['opponents'])}\n")
    out.write(f"{'='*78}\n")

    rows = con.execute(
        "SELECT id, attempt, verification_passed, "
        "       narrative_angles_text, narrative_draft "
        "FROM prompt_audit "
        "WHERE league_id = ? AND season = ? AND week_index = ? "
        "ORDER BY id",
        (league_id, season, week_index),
    ).fetchall()

    if not rows:
        out.write(
            f"\n[no prompt_audit rows for W{week_index}]\n"
            f"The approved artifact was generated before prompt_audit was\n"
            f"capturing. To get evidence, regen this week:\n\n"
            f"  scripts/py scripts/recap_artifact_regenerate.py \\\n"
            f"    --db .local_squadvault.sqlite --league-id {league_id} \\\n"
            f"    --season {season} --week-index {week_index} \\\n"
            f"    --reason 'diag purple haze series' --force\n"
        )
        return

    out.write(f"\nFound {len(rows)} prompt_audit row(s).\n")

    for row in rows:
        pid, attempt, passed, angles_text, draft_text = row
        angles_text = angles_text or ""
        draft_text = draft_text or ""

        out.write(f"\n--- prompt_audit id={pid} attempt={attempt} passed={passed} ---\n")

        # All RIVALRY lines that fired — check for cross-attribution noise
        rivalry_lines = [ln.rstrip() for ln in angles_text.splitlines()
                         if "Long series" in ln or "leads the series" in ln
                         or "Even rivalry" in ln or "Upset:" in ln]
        out.write("\nAll RIVALRY angle lines emitted this week:\n")
        if rivalry_lines:
            for ln in rivalry_lines:
                out.write(f"  {ln}\n")
        else:
            out.write("  [no RIVALRY angles fired this week]\n")

        # Angle lines mentioning either target franchise
        needles_norm = tuple(_norm_apos(n).lower() for n in target["opponents"])
        pair_angle_lines = []
        for ln in angles_text.splitlines():
            ln_low = _norm_apos(ln).lower()
            if any(n in ln_low for n in needles_norm):
                pair_angle_lines.append(ln.rstrip())

        out.write(f"\nAngle lines mentioning {target['opponents']}:\n")
        if pair_angle_lines:
            for ln in pair_angle_lines:
                out.write(f"  {ln}\n")
        else:
            out.write("  [none — no angle mentions either franchise]\n")

        # [NO H2H DATA] lines
        no_h2h_lines = [ln.rstrip() for ln in angles_text.splitlines()
                        if "[NO H2H DATA]" in ln]
        relevant_no_h2h = []
        for ln in no_h2h_lines:
            ln_low = _norm_apos(ln).lower()
            if any(n in ln_low for n in needles_norm):
                relevant_no_h2h.append(ln)
        out.write("\n[NO H2H DATA] markers for this pair:\n")
        if relevant_no_h2h:
            for ln in relevant_no_h2h:
                out.write(f"  {ln}\n")
        else:
            out.write("  [none — either an angle fired OR the pair had no week matchup]\n")
        if no_h2h_lines and not relevant_no_h2h:
            out.write(f"  (other [NO H2H DATA] lines exist for other pairs: "
                      f"{len(no_h2h_lines)} total)\n")

        # Prose windows around the target record
        windows = _slice_around(draft_text, target["target"])
        out.write(f"\nProse windows around \"{target['target']}\" in narrative_draft:\n")
        if not windows:
            out.write(f"  [\"{target['target']}\" not found in narrative_draft]\n")
            out.write("  (It may be in rendered_text but not the narrative_draft — "
                      "check recap_artifacts.)\n")
        else:
            for i, (offset, window) in enumerate(windows):
                qualifier = _qualifier_near(window)
                out.write(f"\n  -- occurrence #{i+1} at offset {offset} --\n")
                out.write(f"  scope qualifier near this claim: {qualifier}\n")
                out.write(f"  --BEGIN WINDOW--\n{window}\n  --END WINDOW--\n")

        # Any global uses of scope language in this draft (helps spot
        # cases where the model uses qualifiers in some places but not
        # the flagged one)
        global_qualifier_count = sum(
            draft_text.lower().count(k)
            for k in ("under current ownership", "current ownership",
                      "current owner", "since took over", "took over")
        )
        out.write(f"\nGlobal count of scope-qualifier phrases in this draft: "
                  f"{global_qualifier_count}\n")


def _dump_live_h2h(out, all_matchups, tenure_map, pair_names, fid_a, fid_b) -> None:
    """Compute all-time and tenure-scoped H2H; show which rivalry tier it hits."""
    out.write(f"\n--- Live H2H: {pair_names[0]} vs {pair_names[1]} ---\n")
    if not (fid_a and fid_b):
        out.write(f"  [could not resolve franchise_ids: {fid_a}, {fid_b}]\n")
        return

    pair = [m for m in all_matchups if {m.winner_id, m.loser_id} == {fid_a, fid_b}]
    h2h_all = compute_head_to_head(pair, fid_a, fid_b)
    total_all = h2h_all.a_wins + h2h_all.b_wins + h2h_all.ties

    t_a = tenure_map.get(fid_a)
    t_b = tenure_map.get(fid_b)

    out.write(f"  {pair_names[0]} fid={fid_a}, tenure start={t_a}\n")
    out.write(f"  {pair_names[1]} fid={fid_b}, tenure start={t_b}\n")
    out.write(f"  All-time: {pair_names[0]} {h2h_all.a_wins}-{h2h_all.b_wins}"
              f"{'-' + str(h2h_all.ties) if h2h_all.ties else ''} {pair_names[1]} "
              f"({total_all} meetings)\n")

    if not (t_a and t_b):
        out.write("  [tenure missing for one or both — tenure filter would NOT apply]\n")
        return

    newer_start = max(t_a, t_b)
    earliest_league = min((m.season for m in all_matchups), default=newer_start)
    out.write(f"  newer_start = max({t_a}, {t_b}) = {newer_start}\n")
    out.write(f"  earliest season in league data: {earliest_league}\n")

    if newer_start <= earliest_league:
        out.write("  tenure filter does NOT apply (newer_start <= earliest) — "
                  "angle would use all-time record\n")
        h2h = h2h_all
        tenure_label = "all-time"
    else:
        tenure_pair = [m for m in pair if m.season >= newer_start]
        h2h = compute_head_to_head(tenure_pair, fid_a, fid_b)
        tenure_total = h2h.a_wins + h2h.b_wins + h2h.ties
        out.write(f"  Under current ownership (>= {newer_start}): "
                  f"{pair_names[0]} {h2h.a_wins}-{h2h.b_wins}"
                  f"{'-' + str(h2h.ties) if h2h.ties else ''} {pair_names[1]} "
                  f"({tenure_total} meetings)\n")
        tenure_label = "under current ownership"

    # Tier the detector would emit for the chosen record
    total = h2h.a_wins + h2h.b_wins + h2h.ties
    def _pct(n, d): return (n / d) if d else 0.0
    out.write(f"\n  Detector tier check (using {tenure_label} record):\n")
    if total >= 3 and _pct(h2h.a_wins, total) >= 0.70 and h2h.a_wins >= 3:
        out.write(f"    -> DOMINANCE fires: \"{pair_names[0]} leads the series "
                  f"{h2h.a_wins}-{h2h.b_wins} ({tenure_label})\"\n")
    elif total >= 3 and _pct(h2h.b_wins, total) >= 0.70 and h2h.b_wins >= 3:
        out.write(f"    -> UPSET DOMINANCE possible if winner_id == {pair_names[0]}: "
                  f"record would show {h2h.b_wins}-{h2h.a_wins}\n")
    elif total >= 5 and abs(h2h.a_wins - h2h.b_wins) <= 1:
        out.write(f"    -> EVEN RIVALRY fires: \"({h2h.a_wins}-{h2h.b_wins}, "
                  f"{tenure_label})\"\n")
    elif total >= 15:
        out.write(f"    -> LONG SERIES fires: \"({h2h.a_wins}-{h2h.b_wins}, "
                  f"{total} meetings {tenure_label})\"\n")
    else:
        out.write(f"    -> NO ANGLE (below all thresholds: "
                  f"total={total}, a_wins={h2h.a_wins}, b_wins={h2h.b_wins}). "
                  f"[NO H2H DATA] marker would emit.\n")


def _dump_purple_haze_season_record(con, out, league_id: str, season: int,
                                      through_week: int, ph_fid: str | None) -> None:
    out.write(f"\n{'='*78}\n")
    out.write(f"=== Purple Haze 2025 season W-L through W{through_week} "
              f"(subcase 2a check)\n")
    out.write(f"{'='*78}\n")
    if not ph_fid:
        out.write("  [franchise_id unresolved — cannot compute]\n")
        return

    try:
        rows = con.execute(
            "SELECT "
            "  CAST(json_extract(payload_json, '$.week') AS INTEGER) AS wk, "
            "  json_extract(payload_json, '$.winner_franchise_id') AS winner, "
            "  json_extract(payload_json, '$.loser_franchise_id') AS loser "
            "FROM v_canonical_best_events "
            "WHERE league_id = ? AND season = ? AND event_type = 'WEEKLY_MATCHUP_RESULT'",
            (league_id, season),
        ).fetchall()
    except Exception as e:
        out.write(f"  [query failed: {e}]\n")
        return

    wins = losses = 0
    for wk, winner, loser in rows:
        if wk is None or wk > through_week:
            continue
        w, l = str(winner or ""), str(loser or "")
        if w == ph_fid:
            wins += 1
        elif l == ph_fid:
            losses += 1
    out.write(f"\n  Purple Haze through W{through_week}: {wins}-{losses}\n")
    if (wins, losses) == (8, 5):
        out.write("  *** MATCHES MODEL'S CLAIMED \"8-5\" — subcase 2a "
                  "(season-vs-series conflation) is LIVE ***\n")
    elif (wins, losses) == (8, 2):
        out.write("  *** season record would match W10's claimed \"8-2\" "
                  "through W10 — check separately ***\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--league-id", required=True)
    parser.add_argument("--season", type=int, default=2025)
    parser.add_argument("--out", default="/tmp/purple_haze_series_diagnosis.txt")
    args = parser.parse_args()

    db_path = args.db
    league_id = str(args.league_id)
    season = int(args.season)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as out, \
            DatabaseSession(db_path) as con:

        out.write("Purple Haze SERIES diagnosis\n")
        out.write(f"  db: {db_path}\n")
        out.write(f"  league_id: {league_id}\n")
        out.write(f"  season: {season}\n")

        # Resolve franchises
        fid_ph = _resolve_franchise_id(con, league_id, season, "Purple Haze")
        fid_sc = (_resolve_franchise_id(con, league_id, season, "Stu's Crew")
                  or _resolve_franchise_id(con, league_id, season, "Stu"))
        fid_mgd = (_resolve_franchise_id(con, league_id, season, "Miller's Genuine Draft")
                   or _resolve_franchise_id(con, league_id, season, "Miller"))

        out.write(f"\nFranchise resolution (by {season} directory name):\n")
        out.write(f"  Purple Haze:               {fid_ph}\n")
        out.write(f"  Stu's Crew:                {fid_sc}\n")
        out.write(f"  Miller's Genuine Draft:    {fid_mgd}\n")

        # Tenures
        try:
            tenure_map = compute_franchise_tenures(db_path, league_id)
        except Exception as e:
            out.write(f"\n[compute_franchise_tenures failed: {e}]\n")
            tenure_map = {}

        out.write("\nTenure map (first season under current name) for targets:\n")
        for fid, label in [(fid_ph, "Purple Haze"),
                            (fid_sc, "Stu's Crew"),
                            (fid_mgd, "Miller's Genuine Draft")]:
            if fid:
                out.write(f"  {label:28s} fid={fid}  since={tenure_map.get(fid)}\n")

        # Full tenure map (abbreviated) for context
        if tenure_map:
            out.write("\nAll franchise tenures (sorted newest first):\n")
            for fid, start in sorted(tenure_map.items(), key=lambda kv: -kv[1]):
                out.write(f"  fid={fid}  since={start}\n")

        # Subcase 2a check: Purple Haze season record through W13
        _dump_purple_haze_season_record(con, out, league_id, season, 13, fid_ph)

        # Load all matchups once for live H2H computation
        try:
            all_matchups = load_all_matchups(db_path, league_id)
            out.write(f"\nLoaded {len(all_matchups)} historical matchups for live H2H checks.\n")
        except Exception as e:
            out.write(f"\n[load_all_matchups failed: {e}]\n")
            all_matchups = []

        # Per-week dumps + live H2H for each pair
        for week, target in TARGETS.items():
            _dump_prompt_audit_for_week(con, out, league_id, season, week, target)

            # Pick the right pair of franchise_ids for this week's target
            if "Stu" in target["opponents"][1]:
                _dump_live_h2h(out, all_matchups, tenure_map,
                               target["opponents"], fid_ph, fid_sc)
            elif "Miller" in target["opponents"][1]:
                _dump_live_h2h(out, all_matchups, tenure_map,
                               target["opponents"], fid_ph, fid_mgd)

        out.write(f"\n{'='*78}\n")
        out.write("=== Interpretation guide\n")
        out.write(f"{'='*78}\n")
        out.write(
            "\n"
            "For each failure week, the hypothesis tree is:\n"
            "\n"
            "A) An angle fired WITH a tenure-scoped record matching the claim.\n"
            "   - The angle line under 'All RIVALRY angle lines' shows the pair\n"
            "     with record == target, labeled '(under current ownership)'.\n"
            "   - Live H2H shows the detector tier still fires with the same\n"
            "     tenure-scoped record.\n"
            "   - The prose window 'scope qualifier near this claim' is\n"
            "     '(none — verifier would NOT skip)'.\n"
            "   => STRIPPED-QUALIFIER fabrication. Fix: make scope load-bearing\n"
            "      in the angle headline + expand verifier tenure-skip patterns.\n"
            "\n"
            "B) No angle fired for the pair AND [NO H2H DATA] is present.\n"
            "   - The prose window still contains the claim.\n"
            "   - Either the season record matches (subcase 2a — season-vs-series\n"
            "     conflation) or the number is a cold fabrication (2b).\n"
            "   => Different failure mode. Fix: prompt-layer clarifier on\n"
            "      [NO H2H DATA] + possibly tighten verifier S2 guard to catch\n"
            "      season-record shapes that use 'series' wording.\n"
            "\n"
            "C) An angle fired with a DIFFERENT record than the claim.\n"
            "   => Pure fabrication / number replacement. Fix: unclear until\n"
            "      examined; the angle presence should make this rare.\n"
        )

    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
