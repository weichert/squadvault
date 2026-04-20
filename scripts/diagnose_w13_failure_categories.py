#!/usr/bin/env python3
"""Dump prompt_audit.verification_result_json for a given
(league, season, week_index), showing every failure record
(category, severity, claim, evidence) in structured form.

Why this script exists
----------------------
My first W13 diagnostic (diagnose_series_pattern_trigger.py) ran
_SERIES_RECORD_PATTERN against narrative_draft and found zero matches
across all five prompt_audit rows. Since SERIES failures can only be
emitted by verify_series_records, and that function only runs when the
pattern matches, the W13 FAILED rows must have failed from a different
category. This script shows which one(s) by reading the canonical
failure store: verification_result_json.

For any failure whose `claim` contains a W-L-shaped substring (e.g.
"8-5", "10-4-1"), the script also finds every occurrence of that
substring in narrative_draft and shows a ±150-char prose window. That
gives us the same "where does the offending text actually live" view
the first diagnostic was trying to produce, but anchored to the actual
failure claim rather than a regex we assumed was firing.

Read-only: no DB writes, no model calls. Output: /tmp/.

Usage:
    set -a; source .env.local; set +a
    scripts/py scripts/diagnose_w13_failure_categories.py \\
        --db .local_squadvault.sqlite --league-id 70985 \\
        --season 2025 --week-index 13
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from squadvault.core.storage.session import DatabaseSession

_WL_IN_CLAIM = re.compile(r'\b\d{1,2}-\d{1,2}(?:-\d{1,2})?\b')


def _format_repr(s: str, maxlen: int = 1200) -> str:
    r = repr(s)
    if len(r) > maxlen:
        r = r[:maxlen] + "…"
    return r


def _find_all(hay: str, needle: str) -> list[int]:
    if not needle:
        return []
    out: list[int] = []
    i = 0
    while True:
        j = hay.find(needle, i)
        if j < 0:
            break
        out.append(j)
        i = j + len(needle)
    return out


def _window(text: str, offset: int, length: int, n: int = 150) -> str:
    s = max(0, offset - n)
    e = min(len(text), offset + length + n)
    return text[s:e]


def _dump_failure(out, idx: int, f: dict, draft: str) -> None:
    cat = f.get("category", "?")
    sev = f.get("severity", "?")
    claim = str(f.get("claim", ""))
    evidence = str(f.get("evidence", ""))

    out.write(f"\n  --- failure #{idx} ---\n")
    out.write(f"  category:   {cat}\n")
    out.write(f"  severity:   {sev}\n")
    out.write(f"  claim:      {_format_repr(claim, maxlen=400)}\n")
    out.write(f"  evidence:   {_format_repr(evidence, maxlen=600)}\n")

    # W-L occurrences referenced in the claim, mapped back into draft prose
    wls = sorted(set(_WL_IN_CLAIM.findall(claim)))
    if not wls:
        return
    out.write(f"  W-L tokens in claim: {wls}\n")
    for wl in wls:
        offsets = _find_all(draft, wl)
        if not offsets:
            out.write(f"    '{wl}': not found in narrative_draft\n")
            continue
        for k, off in enumerate(offsets, start=1):
            win = _window(draft, off, len(wl), n=150)
            out.write(
                f"    '{wl}' occurrence #{k} at draft offset {off}:\n"
                f"      {_format_repr(win, maxlen=500)}\n"
            )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week-index", type=int, required=True)
    ap.add_argument(
        "--out",
        default=None,
        help="Output path (default: /tmp/failure_categories_<league>_<season>_w<week>.txt)",
    )
    args = ap.parse_args()

    default_out = (
        f"/tmp/failure_categories_"
        f"{args.league_id}_{args.season}_w{args.week_index}.txt"
    )
    out_path = Path(args.out or default_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as out, \
            DatabaseSession(args.db) as con:
        out.write("Verification failure categories diagnosis\n")
        out.write(f"  db:          {args.db}\n")
        out.write(f"  league_id:   {args.league_id}\n")
        out.write(f"  season:      {args.season}\n")
        out.write(f"  week_index:  {args.week_index}\n")
        out.write("\n")

        rows = con.execute(
            "SELECT id, attempt, verification_passed, "
            "       verification_result_json, narrative_draft "
            "FROM prompt_audit "
            "WHERE league_id = ? AND season = ? AND week_index = ? "
            "ORDER BY id",
            (str(args.league_id), args.season, args.week_index),
        ).fetchall()

        if not rows:
            out.write("\n[no prompt_audit rows for this (league,season,week)]\n")
            print(f"Wrote {out_path}")
            return 0

        # Row summary up top for quick scanning
        out.write(f"Found {len(rows)} prompt_audit row(s).\n\n")
        out.write(
            f"  {'id':>5}  {'attempt':>7}  {'status':>7}  "
            f"{'hard':>4}  {'soft':>4}  {'checks':>6}  categories\n"
        )

        parsed_rows = []
        for pid, attempt, passed, vr_json, draft in rows:
            draft = draft or ""
            try:
                vr = json.loads(vr_json or "{}")
            except json.JSONDecodeError:
                vr = {}
            hard = vr.get("hard_failures") or []
            soft = vr.get("soft_failures") or []
            categories = sorted({f.get("category", "?")
                                 for f in list(hard) + list(soft)})
            parsed_rows.append((pid, attempt, passed, vr, hard, soft, draft))
            status = "PASSED" if passed else "FAILED"
            checks = vr.get("checks_run")
            out.write(
                f"  {pid:>5}  {attempt:>7}  {status:>7}  "
                f"{len(hard):>4}  {len(soft):>4}  "
                f"{str(checks):>6}  {','.join(categories) or '(none)'}\n"
            )

        # Per-row detail
        for pid, attempt, passed, vr, hard, soft, draft in parsed_rows:
            status = "PASSED" if passed else "FAILED"
            out.write(f"\n{'=' * 78}\n")
            out.write(f"=== prompt_audit id={pid}  attempt={attempt}  {status}\n")
            out.write(f"=== hard_failures={len(hard)}  soft_failures={len(soft)}  "
                      f"checks_run={vr.get('checks_run')}\n")
            out.write(f"=== narrative_draft length: {len(draft)} chars\n")
            out.write(f"{'=' * 78}\n")

            all_failures = list(hard) + list(soft)
            if not all_failures:
                out.write("\n  (no failure records)\n")
                continue

            for i, f in enumerate(all_failures, start=1):
                _dump_failure(out, i, f, draft)

    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
