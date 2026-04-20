#!/usr/bin/env python3
"""Diagnose _SERIES_RECORD_PATTERN triggers for a given (league, season,
week) in prompt_audit, and evaluate candidate skip guards against each
match.

Purpose
-------
Before designing an S5 standings-list guard for verify_series_records,
we need hard evidence of what _SERIES_RECORD_PATTERN is actually
matching in the failing W13 prompt_audit rows. The existing diagnostic
(diagnose_purple_haze_series.py) shows ±220-char prose windows around
a target W-L string; it does NOT itself run the regex. This script
closes that gap.

For each prompt_audit row for the target (league, season, week), this
script runs _SERIES_RECORD_PATTERN.finditer against narrative_draft
and reports, per match:

  - branch  — FORWARD (keyword ... W-L) or BACKWARD (W-L ... keyword)
  - the exact matched text (match.group(0))
  - which keyword(s) appear inside the match
  - 40-char pre-window and 40-char post-window (what the verifier's
    S2/S4 skip guards evaluate)
  - 200-char pre-/post-context for human reading
  - existing-guard decisions: S2 h2h-marker, determiner, idiom,
    post-window h2h-context
  - whether the CANDIDATE S5 "standings-list" guard from the briefing
    would fire (does not modify the verifier; evaluation only)

Output: /tmp/series_pattern_trigger_<league>_<season>_w<week>.txt
Read-only: no DB writes, no model calls, no verifier modification.

Usage
-----
    set -a; source .env.local; set +a
    scripts/py scripts/diagnose_series_pattern_trigger.py \\
        --db .local_squadvault.sqlite --league-id 70985 \\
        --season 2025 --week-index 13
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from squadvault.core.recaps.verification.recap_verifier_v1 import (
    _SEASON_RECORD_IDIOM_PATTERN,
    _SERIES_RECORD_PATTERN,
)
from squadvault.core.storage.session import DatabaseSession

# --- Candidate S5 guard (EVALUATION ONLY — not yet part of the verifier) ---
#
# TWO variants are evaluated, because where the list-connector signal
# lands depends on pattern greed:
#
# (A) S5-as-drafted (briefing): post-40 window contains "and/,/vs <W-L>".
#     Assumption: the connector-and-second-W-L sits AFTER the match.
#
# (B) S5-in-match: match.group(0) itself contains two W-L records
#     separated by a connector. This catches the case where the
#     backward-greedy _SERIES_RECORD_PATTERN has already consumed the
#     "and <W-L>" span on its way to a keyword further right. A
#     legitimate series-record match always contains exactly ONE W-L;
#     a standings list contains two or more. That distinction is
#     independent of whether h2h-marker language happens to appear in
#     the match, which makes (B) robust to prose like "8-5 and 9-4 in
#     the season series" where "series" is a false h2h-marker signal.
_S5_STANDINGS_LIST_CANDIDATE = re.compile(
    r'\s+(?:and|vs\.?|versus|,)\s+\d{1,2}-\d{1,2}(?:-\d{1,2})?\b',
    re.IGNORECASE,
)
_S5_IN_MATCH_MULTI_WL = re.compile(
    r'\d{1,2}-\d{1,2}(?:-\d{1,2})?\s+(?:and|vs\.?|versus|,)\s+\d{1,2}-\d{1,2}',
    re.IGNORECASE,
)

# Mirrors of the verifier's S2/S4 guard regexes, extracted here so the
# diagnostic can report each guard's decision WITHOUT calling into
# verify_series_records (which bundles them with the franchise-lookup
# and attribution logic).
_S2_H2H_MARKER = re.compile(
    r'\b(?:series|rivalry|meetings?|all[- ]?time|lead|head[- ]?to[- ]?head)\b',
    re.IGNORECASE,
)
_S2_POST_H2H_CONTEXT = re.compile(
    r'\b(?:vs\.?|versus|against|head[- ]?to[- ]?head|all[- ]?time)\b',
    re.IGNORECASE,
)
_S2_DETERMINER = re.compile(
    r'\b(?:a|an|his|her|their)\s+$',
    re.IGNORECASE,
)

# Keyword union across both branches of _SERIES_RECORD_PATTERN. "leads?"
# covers both "lead" and "leads"; the superset is: leads|trails|series
# |rivalry|all-time|meetings|record.
_ANY_SERIES_KEYWORD = re.compile(
    r'(?:leads?|trails?|series|rivalry|all[- ]?time|meetings?|record)',
    re.IGNORECASE,
)


def _which_branch(match: re.Match) -> str:
    if match.group(1) is not None:
        return "FORWARD (keyword ... W-L)"
    return "BACKWARD (W-L ... keyword)"


def _extract_wl(match: re.Match) -> str:
    if match.group(1) is not None:
        w, losses, ties = match.group(1), match.group(2), match.group(3)
    else:
        w, losses, ties = match.group(4), match.group(5), match.group(6)
    return f"{w}-{losses}" + (f"-{ties}" if ties else "")


def _window(text: str, start: int, end: int, n: int) -> tuple[str, str]:
    pre = text[max(0, start - n):start]
    post = text[end:min(len(text), end + n)]
    return pre, post


def _format_repr(s: str, maxlen: int = 500) -> str:
    """Single-line repr, capped; useful so multi-paragraph prose doesn't
    blow up the output."""
    r = repr(s)
    if len(r) > maxlen:
        r = r[:maxlen] + "…"
    return r


def _dump_match(out, match: re.Match, draft: str, idx: int) -> None:
    matched = match.group(0)
    wl = _extract_wl(match)
    branch = _which_branch(match)
    pre40, post40 = _window(draft, match.start(), match.end(), 40)
    pre200, post200 = _window(draft, match.start(), match.end(), 200)

    has_h2h_marker = bool(_S2_H2H_MARKER.search(matched))
    has_det = bool(_S2_DETERMINER.search(pre40))
    has_idiom = bool(_SEASON_RECORD_IDIOM_PATTERN.search(pre40))
    has_post_h2h = bool(_S2_POST_H2H_CONTEXT.search(post40))

    existing_s2_s4_skip = (
        (not has_h2h_marker)
        and (has_det or has_idiom)
        and (not has_post_h2h)
    )
    # Variant A: briefing-drafted (post-40 adjacency). Gated on
    # "not has_h2h_marker" per the briefing.
    s5a_post_list = bool(_S5_STANDINGS_LIST_CANDIDATE.search(post40))
    s5a_skip = (not has_h2h_marker) and s5a_post_list
    # Variant B: in-match multi-WL. NOT gated on has_h2h_marker,
    # because the backward-greedy pattern often pulls "series" into
    # the match text for lists that aren't actually H2H records.
    s5b_in_match_multi_wl = bool(_S5_IN_MATCH_MULTI_WL.search(matched))
    s5b_skip = s5b_in_match_multi_wl

    in_match_keywords = sorted({k.lower() for k in _ANY_SERIES_KEYWORD.findall(matched)})

    out.write(f"\n  --- match #{idx} at offset {match.start()}..{match.end()} ---\n")
    out.write(f"  branch:          {branch}\n")
    out.write(f"  W-L claimed:     {wl}\n")
    out.write(f"  match.group(0):  {_format_repr(matched)}\n")
    out.write(f"  keyword(s) in match: {in_match_keywords or '(none found — unexpected)'}\n")
    out.write(f"  pre 40 chars:    {_format_repr(pre40)}\n")
    out.write(f"  post 40 chars:   {_format_repr(post40)}\n")
    out.write(f"  pre 200 chars:   {_format_repr(pre200, maxlen=900)}\n")
    out.write(f"  post 200 chars:  {_format_repr(post200, maxlen=900)}\n")
    out.write("  --- guard decisions ---\n")
    out.write(f"  has_h2h_marker   (in match):  {has_h2h_marker}\n")
    out.write(f"  has_determiner   (pre40):     {has_det}\n")
    out.write(f"  has_season_idiom (pre40):     {has_idiom}\n")
    out.write(f"  has_h2h_context  (post40):    {has_post_h2h}\n")
    out.write(f"  existing S2/S4 would skip:    {existing_s2_s4_skip}\n")
    out.write(f"  S5-A (briefing: post-40 adj): post_hit={s5a_post_list}  "
              f"skip={s5a_skip}\n")
    out.write(f"  S5-B (in-match multi-WL):     match_hit={s5b_in_match_multi_wl}  "
              f"skip={s5b_skip}\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week-index", type=int, required=True)
    ap.add_argument(
        "--out",
        default=None,
        help="Output path (default: /tmp/series_pattern_trigger_<league>_<season>_w<week>.txt)",
    )
    args = ap.parse_args()

    default_out = (
        f"/tmp/series_pattern_trigger_"
        f"{args.league_id}_{args.season}_w{args.week_index}.txt"
    )
    out_path = Path(args.out or default_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as out, \
            DatabaseSession(args.db) as con:
        out.write("_SERIES_RECORD_PATTERN trigger diagnosis\n")
        out.write(f"  db:          {args.db}\n")
        out.write(f"  league_id:   {args.league_id}\n")
        out.write(f"  season:      {args.season}\n")
        out.write(f"  week_index:  {args.week_index}\n")
        out.write("\n")
        out.write(
            "Per-row dump of every _SERIES_RECORD_PATTERN match in\n"
            "narrative_draft, with guard-decision breakdown. The\n"
            "candidate S5 guard at the bottom of each match block is\n"
            "EVALUATION ONLY — this script does not modify the verifier.\n"
        )

        rows = con.execute(
            "SELECT id, attempt, verification_passed, narrative_draft "
            "FROM prompt_audit "
            "WHERE league_id = ? AND season = ? AND week_index = ? "
            "ORDER BY id",
            (str(args.league_id), args.season, args.week_index),
        ).fetchall()

        if not rows:
            out.write(
                f"\n[no prompt_audit rows for league={args.league_id} "
                f"season={args.season} week={args.week_index}]\n"
            )
            print(f"Wrote {out_path}")
            return 0

        out.write(f"\nFound {len(rows)} prompt_audit row(s).\n")

        # Summary matrix at top for quick scanning
        out.write("\nRow summary:\n")
        out.write(f"  {'id':>5}  {'attempt':>7}  {'status':>7}  "
                  f"{'matches':>7}  draft_len\n")
        summaries = []
        for row in rows:
            pid, attempt, passed, draft = row
            draft = draft or ""
            matches = list(_SERIES_RECORD_PATTERN.finditer(draft))
            status = "PASSED" if passed else "FAILED"
            summaries.append((pid, attempt, status, len(matches), len(draft), draft))
            out.write(f"  {pid:>5}  {attempt:>7}  {status:>7}  "
                      f"{len(matches):>7}  {len(draft)}\n")

        # Per-row detail
        for pid, attempt, status, n_matches, draft_len, draft in summaries:
            out.write(f"\n{'=' * 78}\n")
            out.write(f"=== prompt_audit id={pid}  attempt={attempt}  {status}\n")
            out.write(f"=== narrative_draft length: {draft_len} chars, "
                      f"{n_matches} pattern match(es)\n")
            out.write(f"{'=' * 78}\n")

            if n_matches == 0:
                out.write("\n  (no _SERIES_RECORD_PATTERN matches in this draft)\n")
                continue

            for i, m in enumerate(
                _SERIES_RECORD_PATTERN.finditer(draft), start=1
            ):
                _dump_match(out, m, draft, i)

        # Aggregate decision summary — useful for confirming that the
        # candidate S5 guard would correctly skip every FAILED row's
        # triggering match and would NOT falsely skip any match in a
        # PASSED row (the latter is the false-negative risk).
        out.write(f"\n{'=' * 78}\n")
        out.write("=== Aggregate decision summary — S5 variant comparison\n")
        out.write(f"{'=' * 78}\n")
        out.write(
            "\nPer row: match count, existing-guard skips, and each S5\n"
            "variant's skip count. The RIGHT fix is the variant that:\n"
            "  - skips every match in every FAILED row that existing\n"
            "    guards miss (catches the false positives), AND\n"
            "  - does NOT skip any match in any PASSED row\n"
            "    (does not introduce false negatives).\n"
            "\n"
            "Column legend:\n"
            "  existing: matches the current S2/S4 guards would skip\n"
            "  S5-A:     skips under the briefing's drafted post-40 guard\n"
            "  S5-B:     skips under the in-match multi-WL guard\n"
        )
        out.write(
            f"\n  {'id':>5}  {'attempt':>7}  {'status':>7}  "
            f"{'matches':>7}  {'existing':>8}  {'S5-A':>5}  {'S5-B':>5}\n"
        )
        for pid, attempt, status, n_matches, _draft_len, draft in summaries:
            existing_skip_count = 0
            s5a_skip_count = 0
            s5b_skip_count = 0
            for m in _SERIES_RECORD_PATTERN.finditer(draft):
                matched = m.group(0)
                pre40, post40 = _window(draft, m.start(), m.end(), 40)
                has_h2h = bool(_S2_H2H_MARKER.search(matched))
                has_det = bool(_S2_DETERMINER.search(pre40))
                has_idiom = bool(_SEASON_RECORD_IDIOM_PATTERN.search(pre40))
                has_post_h2h = bool(_S2_POST_H2H_CONTEXT.search(post40))
                if (not has_h2h) and (has_det or has_idiom) and (not has_post_h2h):
                    existing_skip_count += 1
                if (not has_h2h) and bool(_S5_STANDINGS_LIST_CANDIDATE.search(post40)):
                    s5a_skip_count += 1
                if bool(_S5_IN_MATCH_MULTI_WL.search(matched)):
                    s5b_skip_count += 1
            out.write(
                f"  {pid:>5}  {attempt:>7}  {status:>7}  "
                f"{n_matches:>7}  {existing_skip_count:>8}  "
                f"{s5a_skip_count:>5}  {s5b_skip_count:>5}\n"
            )

    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
