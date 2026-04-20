#!/usr/bin/env python3
"""Diagnose _SERIES_RECORD_PATTERN triggers against APPROVED recaps in
recap_artifacts (the store verify_season.py reads), for a given
(league, season) across a list of week_indexes.

Why this script exists
----------------------
verify_season.py pulled live SERIES failures at W10 and W13. My prior
diagnostic (diagnose_series_pattern_trigger.py) searched prompt_audit.
narrative_draft and found zero pattern matches — but the verifier in
verify_season.py reads recap_artifacts.rendered_text, not prompt_audit.
Two different text stores. This script closes that gap by running the
pattern against the same text the verifier sees on approved recaps.

For each target week's approved recap, this script:
  - Pulls rendered_text from recap_artifacts where state='APPROVED'
  - Runs _extract_shareable_recap exactly as verify_recap_v1 does
  - Runs _SERIES_RECORD_PATTERN.finditer on the shareable text
  - Per match: reports branch, matched text, 40-char pre/post windows,
    200-char pre/post context, existing S2/S4 guard decisions, and
    evaluates two candidate S5 skip guards (briefing post-40 adjacency
    vs in-match multi-WL)

Read-only: no DB writes, no model calls, no verifier modification.
Output: /tmp/.

Usage:
    set -a; source .env.local; set +a
    scripts/py scripts/diagnose_approved_recap_series_trigger.py \\
        --db .local_squadvault.sqlite --league-id 70985 \\
        --season 2025 --weeks 4 10 13
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from squadvault.core.recaps.verification.recap_verifier_v1 import (
    _SEASON_RECORD_IDIOM_PATTERN,
    _SERIES_RECORD_PATTERN,
    _extract_shareable_recap,
)
from squadvault.core.storage.session import DatabaseSession

# Mirrors of the candidate and existing-guard regexes from the first
# trigger diagnostic. Kept identical so output is directly comparable.
_S5_POST_ADJ = re.compile(
    r'\s+(?:and|vs\.?|versus|,)\s+\d{1,2}-\d{1,2}(?:-\d{1,2})?\b',
    re.IGNORECASE,
)
_S5_IN_MATCH_MULTI_WL = re.compile(
    r'\d{1,2}-\d{1,2}(?:-\d{1,2})?\s+(?:and|vs\.?|versus|,)\s+\d{1,2}-\d{1,2}',
    re.IGNORECASE,
)
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
    r = repr(s)
    if len(r) > maxlen:
        r = r[:maxlen] + "…"
    return r


def _dump_match(out, match: re.Match, text: str, idx: int) -> None:
    matched = match.group(0)
    wl = _extract_wl(match)
    branch = _which_branch(match)
    pre40, post40 = _window(text, match.start(), match.end(), 40)
    pre200, post200 = _window(text, match.start(), match.end(), 200)

    has_h2h_marker = bool(_S2_H2H_MARKER.search(matched))
    has_det = bool(_S2_DETERMINER.search(pre40))
    has_idiom = bool(_SEASON_RECORD_IDIOM_PATTERN.search(pre40))
    has_post_h2h = bool(_S2_POST_H2H_CONTEXT.search(post40))

    existing_s2_s4_skip = (
        (not has_h2h_marker)
        and (has_det or has_idiom)
        and (not has_post_h2h)
    )
    s5a_post_list = bool(_S5_POST_ADJ.search(post40))
    s5a_skip = (not has_h2h_marker) and s5a_post_list
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
    out.write(f"  S5-A (briefing: post-40 adj): post_hit={s5a_post_list}  skip={s5a_skip}\n")
    out.write(f"  S5-B (in-match multi-WL):     match_hit={s5b_in_match_multi_wl}  skip={s5b_skip}\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument(
        "--weeks",
        type=int,
        nargs="+",
        required=True,
        help="One or more week_index values to inspect (e.g. --weeks 10 13)",
    )
    ap.add_argument(
        "--out",
        default=None,
        help=("Output path (default: "
              "/tmp/approved_series_trigger_<league>_<season>.txt)"),
    )
    args = ap.parse_args()

    default_out = (
        f"/tmp/approved_series_trigger_"
        f"{args.league_id}_{args.season}.txt"
    )
    out_path = Path(args.out or default_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as out, \
            DatabaseSession(args.db) as con:
        out.write("_SERIES_RECORD_PATTERN trigger diagnosis (approved recaps)\n")
        out.write(f"  db:        {args.db}\n")
        out.write(f"  league_id: {args.league_id}\n")
        out.write(f"  season:    {args.season}\n")
        out.write(f"  weeks:     {args.weeks}\n")
        out.write("\n")

        placeholders = ",".join("?" * len(args.weeks))
        rows = con.execute(
            f"SELECT week_index, rendered_text "
            f"FROM recap_artifacts "
            f"WHERE league_id = ? AND season = ? "
            f"  AND artifact_type = 'WEEKLY_RECAP' "
            f"  AND state = 'APPROVED' "
            f"  AND week_index IN ({placeholders}) "
            f"ORDER BY week_index ASC",
            (str(args.league_id), args.season, *args.weeks),
        ).fetchall()

        if not rows:
            out.write(
                "\n[no APPROVED recaps found in recap_artifacts for the "
                "requested weeks]\n"
            )
            print(f"Wrote {out_path}")
            return 0

        out.write(f"Found {len(rows)} approved recap(s).\n\n")

        # Summary row
        out.write(
            f"  {'week':>4}  {'rendered':>8}  {'shareable':>9}  "
            f"{'matches':>7}\n"
        )
        summaries = []
        for week_index, rendered_text in rows:
            rendered_text = rendered_text or ""
            shareable = _extract_shareable_recap(rendered_text)
            matches = list(_SERIES_RECORD_PATTERN.finditer(shareable))
            summaries.append((int(week_index), rendered_text, shareable, matches))
            out.write(
                f"  {week_index:>4}  {len(rendered_text):>8}  "
                f"{len(shareable):>9}  {len(matches):>7}\n"
            )

        # Per-week detail
        for week_index, rendered_text, shareable, matches in summaries:
            out.write(f"\n{'=' * 78}\n")
            out.write(f"=== Week {week_index}  approved recap\n")
            out.write(f"=== rendered_text: {len(rendered_text)} chars  |  "
                      f"shareable: {len(shareable)} chars\n")
            out.write(f"=== _SERIES_RECORD_PATTERN matches on shareable: {len(matches)}\n")
            out.write(f"{'=' * 78}\n")

            if not matches:
                # If the shareable has no pattern match, show where the
                # literal claim W-L might live in the text anyway. This
                # helps diagnose cases where the failure comes from
                # something other than the current pattern shape.
                out.write(
                    "\n  (no _SERIES_RECORD_PATTERN matches in shareable text — "
                    "the verifier's SERIES check would skip this week entirely)\n"
                )
                continue

            for i, m in enumerate(matches, start=1):
                _dump_match(out, m, shareable, i)

        # Aggregate decision summary
        out.write(f"\n{'=' * 78}\n")
        out.write("=== Aggregate decision summary — S5 variant comparison\n")
        out.write(f"{'=' * 78}\n")
        out.write(
            f"\n  {'week':>4}  {'matches':>7}  {'existing':>8}  "
            f"{'S5-A':>5}  {'S5-B':>5}\n"
        )
        for week_index, _rendered, shareable, matches in summaries:
            existing_skip = 0
            s5a_skip = 0
            s5b_skip = 0
            for m in _SERIES_RECORD_PATTERN.finditer(shareable):
                matched = m.group(0)
                pre40, post40 = _window(shareable, m.start(), m.end(), 40)
                has_h2h = bool(_S2_H2H_MARKER.search(matched))
                has_det = bool(_S2_DETERMINER.search(pre40))
                has_idiom = bool(_SEASON_RECORD_IDIOM_PATTERN.search(pre40))
                has_post_h2h = bool(_S2_POST_H2H_CONTEXT.search(post40))
                if (not has_h2h) and (has_det or has_idiom) and (not has_post_h2h):
                    existing_skip += 1
                if (not has_h2h) and bool(_S5_POST_ADJ.search(post40)):
                    s5a_skip += 1
                if bool(_S5_IN_MATCH_MULTI_WL.search(matched)):
                    s5b_skip += 1
            out.write(
                f"  {week_index:>4}  {len(matches):>7}  {existing_skip:>8}  "
                f"{s5a_skip:>5}  {s5b_skip:>5}\n"
            )

    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
