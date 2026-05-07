#!/usr/bin/env python3
"""Player-streak verb inversion diagnostic harness.

Per
``_observations/session_brief_player_streak_verb_inversion_diagnostic.md``
and the §3.2 promotion criterion in
``_observations/OBSERVATIONS_2026_05_04_STREAK_VERB_PRE_COMPUTATION_SCOPE.md``.

Diagnostic-only. No production-path code, no DB writes, no model calls.
Output of this harness is cited in the matching observation memo.

For each (season, week) in the approved corpus:

1. Re-runs ``detect_player_narrative_angles_v1`` against the stored
   season/week context with production resolvers (cross-season name
   map, player name map, franchise tenure map) — same call shape used
   by the recap lifecycle and by ``verify_player_trend_detectors.py``.
2. Filters returned angles to PLAYER_HOT_STREAK (P1), PLAYER_COLD_STREAK
   (P2), and PLAYER_FRANCHISE_TENURE (P3).
3. Parses each canonical headline into structured fields (player,
   franchise, threshold, streak length) using emitter-specific
   regexes derived from the helper-bound canonical phrasings at
   ``player_narrative_angles_v1.py`` lines 752-755, 804-807, 1330-1333.
4. Classifies the corresponding claim in the recap's rendered_text
   into one of seven buckets:

   Integrity tier (HARD):
     - DIRECTION_INVERSION    — hot/cold direction flipped
     - FRANCHISE_MISMATCH     — claim attributed to wrong franchise
     - THRESHOLD_INVERSION    — scoring threshold differs from canonical
     - TENURE_NON_CONSECUTIVE — P3 only: "consecutive" qualifier dropped

   Editorial tier (SOFT):
     - DURATION_DRIFT         — "consecutive" → "across the last X" /
                                "in N of the last M"

   Other:
     - CORRECT                — prose matches canonical or paraphrases
                                without semantic loss
     - NO_CLAIM               — no player-streak claim for this tuple

Two-tier evidence gate per the brief's decision framework:
  - Any non-zero integrity-tier signal → GATE: PROMOTE
  - Editorial-tier only (DURATION_DRIFT > 0)  → GATE: ELECT
  - All zero                                   → GATE: CLOSE

Limitation acknowledged in v1: FRANCHISE_MISMATCH detection is
alias-naive. It flags only the obvious pattern — prose says
"for {alternate_franchise}" where the alternate is in the run's
canonical franchise set. Subtle alias-only mismatches (Option B
nickname overrides, owner-first-word resolution per migration 0010)
are known false negatives. The 18-row 2025 corpus is small enough
to spot-check by hand if FRANCHISE_MISMATCH returns zero hits.

Usage::

    scripts/py scripts/diagnose_player_streak_verb_inversions.py \\
        --db .local_squadvault.sqlite --league-id 70985 --season 2025

    # Single-week scope:
    scripts/py scripts/diagnose_player_streak_verb_inversions.py \\
        --season 2025 --week-index 11

    # Per-claim CSV for follow-up:
    scripts/py scripts/diagnose_player_streak_verb_inversions.py \\
        --season 2025 --write-csv /tmp/player_streak_diagnostic.csv
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from squadvault.core.recaps.context.league_history_v1 import (
    build_cross_season_name_resolver,
    compute_franchise_tenures,
)
from squadvault.core.recaps.context.player_narrative_angles_v1 import (
    detect_player_narrative_angles_v1,
)
from squadvault.core.resolvers import build_player_name_map
from squadvault.core.storage.session import DatabaseSession

# ───────────────────── Constants ─────────────────────

WINDOW_CHARS = 200  # ±chars around player-name occurrence in prose

CAT_DIRECTION_INVERSION = "DIRECTION_INVERSION"
CAT_FRANCHISE_MISMATCH = "FRANCHISE_MISMATCH"
CAT_THRESHOLD_INVERSION = "THRESHOLD_INVERSION"
CAT_TENURE_NON_CONSECUTIVE = "TENURE_NON_CONSECUTIVE"
CAT_DURATION_DRIFT = "DURATION_DRIFT"
CAT_CORRECT = "CORRECT"
CAT_NO_CLAIM = "NO_CLAIM"

INTEGRITY_TIER = frozenset({
    CAT_DIRECTION_INVERSION,
    CAT_FRANCHISE_MISMATCH,
    CAT_THRESHOLD_INVERSION,
    CAT_TENURE_NON_CONSECUTIVE,
})
EDITORIAL_TIER = frozenset({CAT_DURATION_DRIFT})

CATEGORY_DISPLAY_ORDER = [
    CAT_DIRECTION_INVERSION,
    CAT_FRANCHISE_MISMATCH,
    CAT_THRESHOLD_INVERSION,
    CAT_TENURE_NON_CONSECUTIVE,
    CAT_DURATION_DRIFT,
    CAT_CORRECT,
    CAT_NO_CLAIM,
]

# Headline parsers — extract structured fields from orchestrator output.
# These match the canonical helper-bound phrasings; if the emitter
# strings drift, these constants need updating in lockstep.

_P1_HEADLINE = re.compile(
    r"^(?P<player>.+?)\s+has\s+scored\s+(?P<threshold>\d+)\+\s+points\s+in\s+"
    r"(?P<n>\d+)\s+consecutive\s+weeks\s+for\s+(?P<franchise>.+)$"
)
_P2_HEADLINE = re.compile(
    r"^(?P<player>.+?)\s+has\s+scored\s+under\s+(?P<threshold>\d+)\s+points\s+in\s+"
    r"(?P<n>\d+)\s+straight\s+starts\s+for\s+(?P<franchise>.+)$"
)
_P3_HEADLINE = re.compile(
    r"^(?P<player>.+?)\s+has\s+been\s+on\s+(?P<franchise>.+)'s\s+roster\s+for\s+"
    r"(?P<n>\d+)\s+consecutive\s+seasons$"
)

# Duration-drift regex — common across all three emitters.
# Catches "in/across/over the last X" and "in N of the last M".
_DURATION_DRIFT_RE = re.compile(
    r"(?:in|across|over)\s+the\s+last\s+\d+|in\s+\d+\s+of\s+the\s+last\s+\d+",
    re.IGNORECASE,
)

# ───────────────────── Dataclasses ─────────────────────


@dataclass
class _ParsedHeadline:
    player: str
    franchise: str
    threshold: float | None
    streak_n: int


@dataclass
class _CanonicalClaim:
    season: int
    week: int
    emitter: str  # 'P1' | 'P2' | 'P3'
    category: str
    player: str
    franchise: str
    threshold: float | None
    streak_n: int
    canonical_headline: str


@dataclass
class _ClassifiedClaim:
    claim: _CanonicalClaim
    bucket: str
    evidence: str = ""
    prose_window: str = ""


# ───────────────────── Headline parsing ─────────────────────


def _emitter_for_category(category: str) -> str | None:
    return {
        "PLAYER_HOT_STREAK": "P1",
        "PLAYER_COLD_STREAK": "P2",
        "PLAYER_FRANCHISE_TENURE": "P3",
    }.get(category)


def _parse_headline(emitter: str, headline: str) -> _ParsedHeadline | None:
    """Parse a canonical orchestrator headline into structured fields."""
    if emitter == "P1":
        m = _P1_HEADLINE.match(headline)
        if not m:
            return None
        return _ParsedHeadline(
            player=m.group("player"),
            franchise=m.group("franchise"),
            threshold=float(m.group("threshold")),
            streak_n=int(m.group("n")),
        )
    if emitter == "P2":
        m = _P2_HEADLINE.match(headline)
        if not m:
            return None
        return _ParsedHeadline(
            player=m.group("player"),
            franchise=m.group("franchise"),
            threshold=float(m.group("threshold")),
            streak_n=int(m.group("n")),
        )
    if emitter == "P3":
        m = _P3_HEADLINE.match(headline)
        if not m:
            return None
        return _ParsedHeadline(
            player=m.group("player"),
            franchise=m.group("franchise"),
            threshold=None,
            streak_n=int(m.group("n")),
        )
    return None


# ───────────────────── Prose classification ─────────────────────


def _find_player_in_prose(player_full: str, prose: str) -> tuple[int, int] | None:
    """Locate player name in prose. Tries full name first, then last token."""
    if not player_full:
        return None
    m = re.search(rf"\b{re.escape(player_full)}\b", prose)
    if m:
        return (m.start(), m.end())
    parts = player_full.rsplit(" ", 1)
    if len(parts) == 2:
        last = parts[1]
        if len(last) >= 4:  # avoid "Jr" / "II" / "Sr"
            m = re.search(rf"\b{re.escape(last)}\b", prose)
            if m:
                return (m.start(), m.end())
    return None


def _window(prose: str, span: tuple[int, int], radius: int = WINDOW_CHARS) -> str:
    start = max(0, span[0] - radius)
    end = min(len(prose), span[1] + radius)
    return prose[start:end]


def _check_franchise_mismatch(
    claim: _CanonicalClaim,
    window: str,
    other_franchises: frozenset[str],
) -> _ClassifiedClaim | None:
    """Flag if prose attributes claim to an alternate canonical franchise.

    Conservative: only flags 'for {other}' attribution patterns where
    {other} is a different canonical franchise from this run. Alias-naive.
    """
    for other in other_franchises:
        if re.search(rf"\bfor\s+{re.escape(other)}\b", window, re.IGNORECASE):
            return _ClassifiedClaim(
                claim=claim,
                bucket=CAT_FRANCHISE_MISMATCH,
                evidence=(
                    f"Canonical franchise={claim.franchise!r}, prose attributes "
                    f"to {other!r} via 'for {other}'"
                ),
                prose_window=window,
            )
    return None


def _classify_p1(
    claim: _CanonicalClaim,
    prose: str,
    other_franchises: frozenset[str],
) -> _ClassifiedClaim:
    """Hot streak: '{player} has scored {th}+ points in {N} consecutive weeks for {fr}'."""
    span = _find_player_in_prose(claim.player, prose)
    if span is None:
        return _ClassifiedClaim(claim=claim, bucket=CAT_NO_CLAIM)
    window = _window(prose, span)
    threshold_int = int(claim.threshold) if claim.threshold is not None else 0

    mismatch = _check_franchise_mismatch(claim, window, other_franchises)
    if mismatch is not None:
        return mismatch

    # DIRECTION_INVERSION: hot streak's prose says "scored under/below N"
    if re.search(r"\bscored?\s+(?:under|below|less\s+than)\s+\d+", window, re.IGNORECASE):
        return _ClassifiedClaim(
            claim=claim,
            bucket=CAT_DIRECTION_INVERSION,
            evidence="Hot-streak prose contains 'scored under/below/less than N'",
            prose_window=window,
        )

    # THRESHOLD_INVERSION: prose has "{N}+" with N != canonical threshold
    for m in re.finditer(r"\bscored?\s+(\d+)\+", window, re.IGNORECASE):
        prose_thresh = int(m.group(1))
        if prose_thresh != threshold_int:
            return _ClassifiedClaim(
                claim=claim,
                bucket=CAT_THRESHOLD_INVERSION,
                evidence=f"Canonical {threshold_int}+, prose {prose_thresh}+",
                prose_window=window,
            )

    if _DURATION_DRIFT_RE.search(window):
        return _ClassifiedClaim(
            claim=claim,
            bucket=CAT_DURATION_DRIFT,
            evidence="Duration drift: 'consecutive' replaced with last-N construction",
            prose_window=window,
        )

    return _ClassifiedClaim(claim=claim, bucket=CAT_CORRECT, prose_window=window)


def _classify_p2(
    claim: _CanonicalClaim,
    prose: str,
    other_franchises: frozenset[str],
) -> _ClassifiedClaim:
    """Cold streak: '{player} has scored under {th} points in {N} straight starts for {fr}'."""
    span = _find_player_in_prose(claim.player, prose)
    if span is None:
        return _ClassifiedClaim(claim=claim, bucket=CAT_NO_CLAIM)
    window = _window(prose, span)
    threshold_int = int(claim.threshold) if claim.threshold is not None else 0

    mismatch = _check_franchise_mismatch(claim, window, other_franchises)
    if mismatch is not None:
        return mismatch

    # DIRECTION_INVERSION: cold streak's prose reframes as a hot streak
    if re.search(r"\bscored?\s+\d+\+\s+points", window, re.IGNORECASE):
        return _ClassifiedClaim(
            claim=claim,
            bucket=CAT_DIRECTION_INVERSION,
            evidence="Cold-streak prose contains 'scored N+ points' (drought reframed as hot streak)",
            prose_window=window,
        )
    if re.search(r"\bscored?\s+over\s+\d+\s+points", window, re.IGNORECASE):
        return _ClassifiedClaim(
            claim=claim,
            bucket=CAT_DIRECTION_INVERSION,
            evidence="Cold-streak prose contains 'scored over N points'",
            prose_window=window,
        )

    # THRESHOLD_INVERSION: "scored under M" with M != canonical
    for m in re.finditer(r"\bscored?\s+under\s+(\d+)", window, re.IGNORECASE):
        prose_thresh = int(m.group(1))
        if prose_thresh != threshold_int:
            return _ClassifiedClaim(
                claim=claim,
                bucket=CAT_THRESHOLD_INVERSION,
                evidence=f"Canonical under-{threshold_int}, prose under-{prose_thresh}",
                prose_window=window,
            )

    if _DURATION_DRIFT_RE.search(window):
        return _ClassifiedClaim(
            claim=claim,
            bucket=CAT_DURATION_DRIFT,
            evidence="Duration drift: 'straight starts' replaced with last-N construction",
            prose_window=window,
        )

    return _ClassifiedClaim(claim=claim, bucket=CAT_CORRECT, prose_window=window)


def _classify_p3(
    claim: _CanonicalClaim,
    prose: str,
    other_franchises: frozenset[str],
) -> _ClassifiedClaim:
    """Tenure: '{player} has been on {franchise}'s roster for {N} consecutive seasons'."""
    span = _find_player_in_prose(claim.player, prose)
    if span is None:
        return _ClassifiedClaim(claim=claim, bucket=CAT_NO_CLAIM)
    window = _window(prose, span)

    mismatch = _check_franchise_mismatch(claim, window, other_franchises)
    if mismatch is not None:
        return mismatch

    # Also check explicit "{other}'s roster" alternate-attribution pattern.
    for other in other_franchises:
        if re.search(rf"\b{re.escape(other)}\b's\s+roster\b", window, re.IGNORECASE):
            return _ClassifiedClaim(
                claim=claim,
                bucket=CAT_FRANCHISE_MISMATCH,
                evidence=(
                    f"Canonical franchise={claim.franchise!r}, prose says "
                    f"\"{other}'s roster\""
                ),
                prose_window=window,
            )

    # TENURE_NON_CONSECUTIVE: "for N seasons" without "consecutive" preceding.
    for m in re.finditer(r"\bfor\s+(\d+)\s+seasons?\b", window, re.IGNORECASE):
        preceding = window[max(0, m.start() - 30):m.start()]
        if not re.search(r"\bconsecutive\b", preceding, re.IGNORECASE):
            return _ClassifiedClaim(
                claim=claim,
                bucket=CAT_TENURE_NON_CONSECUTIVE,
                evidence=(
                    f"Tenure claim '{m.group(0)}' missing 'consecutive' qualifier"
                ),
                prose_window=window,
            )

    if _DURATION_DRIFT_RE.search(window):
        return _ClassifiedClaim(
            claim=claim,
            bucket=CAT_DURATION_DRIFT,
            evidence="Duration drift in tenure context",
            prose_window=window,
        )

    return _ClassifiedClaim(claim=claim, bucket=CAT_CORRECT, prose_window=window)


def _classify(
    claim: _CanonicalClaim,
    prose: str,
    other_franchises: frozenset[str],
) -> _ClassifiedClaim:
    if claim.emitter == "P1":
        return _classify_p1(claim, prose, other_franchises)
    if claim.emitter == "P2":
        return _classify_p2(claim, prose, other_franchises)
    if claim.emitter == "P3":
        return _classify_p3(claim, prose, other_franchises)
    return _ClassifiedClaim(claim=claim, bucket=CAT_NO_CLAIM, evidence="unknown emitter")


# ───────────────────── Corpus loading ─────────────────────


def _load_approved_corpus(
    db_path: str,
    league_id: str,
    season: int,
    week_filter: int | None,
) -> list[tuple[int, str]]:
    """Return list of (week_index, rendered_text) for approved recaps."""
    out: list[tuple[int, str]] = []
    sql = """
        SELECT week_index, rendered_text
          FROM recap_artifacts
         WHERE state = 'APPROVED'
           AND season = ?
           AND league_id = ?
           AND rendered_text IS NOT NULL
         ORDER BY week_index
    """
    with DatabaseSession(db_path) as con:
        for row in con.execute(sql, (season, league_id)):
            week, prose = int(row[0]), str(row[1])
            if week_filter is not None and week != week_filter:
                continue
            out.append((week, prose))
    return out


def _build_canonical_for_week(
    db_path: str,
    league_id: str,
    season: int,
    week: int,
    name_map: dict[str, str],
    player_name_map: dict[str, str],
    tenure_map: dict[str, int] | None,
) -> list[_CanonicalClaim]:
    """Run the orchestrator at (season, week) and return P1/P2/P3 claims."""
    pname = lambda pid: player_name_map.get(pid, pid)  # noqa: E731
    fname = lambda fid: name_map.get(fid, fid)  # noqa: E731

    angles = detect_player_narrative_angles_v1(
        db_path=db_path,
        league_id=league_id,
        season=season,
        week=week,
        tenure_map=tenure_map,
        pname=pname,
        fname=fname,
    )

    claims: list[_CanonicalClaim] = []
    for a in angles:
        emitter = _emitter_for_category(a.category)
        if emitter is None:
            continue
        parsed = _parse_headline(emitter, a.headline)
        if parsed is None:
            print(
                f"  ⚠ Could not parse {emitter} headline at season={season} "
                f"week={week}: {a.headline!r}",
                file=sys.stderr,
            )
            continue
        claims.append(_CanonicalClaim(
            season=season,
            week=week,
            emitter=emitter,
            category=a.category,
            player=parsed.player,
            franchise=parsed.franchise,
            threshold=parsed.threshold,
            streak_n=parsed.streak_n,
            canonical_headline=a.headline,
        ))
    return claims


# ───────────────────── Two-tier evidence gate ─────────────────────


def _apply_gate(buckets: dict[str, int]) -> str:
    integrity = sum(buckets.get(c, 0) for c in INTEGRITY_TIER)
    editorial = sum(buckets.get(c, 0) for c in EDITORIAL_TIER)
    if integrity > 0:
        return "PROMOTE"
    if editorial > 0:
        return "ELECT"
    return "CLOSE"


# ───────────────────── Output ─────────────────────


def _print_per_emitter_table(emitter: str, classified: list[_ClassifiedClaim]) -> None:
    print(f"\n  {emitter} — {len(classified)} canonical claim(s):")
    if not classified:
        print("    (no canonical claims fired across the corpus)")
        return
    counts = {cat: sum(1 for c in classified if c.bucket == cat)
              for cat in CATEGORY_DISPLAY_ORDER}
    for cat in CATEGORY_DISPLAY_ORDER:
        n = counts.get(cat, 0)
        marker = ""
        if n > 0 and cat in INTEGRITY_TIER:
            marker = "  ⚠ INTEGRITY"
        elif n > 0 and cat in EDITORIAL_TIER:
            marker = "  ⚠ EDITORIAL"
        print(f"    {cat:<28} {n:>4}{marker}")


def _print_specimens(
    classified: list[_ClassifiedClaim],
    bucket: str,
    label: str,
) -> None:
    specimens = [c for c in classified if c.bucket == bucket]
    if not specimens:
        return
    print(f"\n  {label}:")
    for c in specimens:
        print(
            f"    season={c.claim.season} week={c.claim.week} "
            f"emitter={c.claim.emitter} player={c.claim.player!r} "
            f"franchise={c.claim.franchise!r}"
        )
        print(f"      canonical: {c.claim.canonical_headline!r}")
        print(f"      evidence:  {c.evidence}")
        if c.prose_window:
            window_excerpt = c.prose_window.replace("\n", " ")
            if len(window_excerpt) > 240:
                window_excerpt = window_excerpt[:240] + "…"
            print(f"      window:    {window_excerpt!r}")


def _write_csv(path: Path, classified: list[_ClassifiedClaim]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "season", "week", "emitter", "category", "player", "franchise",
            "threshold", "streak_n", "bucket", "canonical_headline",
            "evidence", "prose_window",
        ])
        for c in classified:
            w.writerow([
                c.claim.season, c.claim.week, c.claim.emitter, c.claim.category,
                c.claim.player, c.claim.franchise,
                c.claim.threshold if c.claim.threshold is not None else "",
                c.claim.streak_n, c.bucket, c.claim.canonical_headline,
                c.evidence, c.prose_window,
            ])


# ───────────────────── Main ─────────────────────


def _run_diagnostic(
    db_path: str,
    league_id: str,
    season: int,
    week_filter: int | None,
) -> tuple[list[_ClassifiedClaim], dict[str, int]]:
    name_map = build_cross_season_name_resolver(db_path, league_id)
    player_name_map = build_player_name_map(db_path, league_id)
    try:
        tenure_map: dict[str, int] | None = compute_franchise_tenures(db_path, league_id)
    except Exception as exc:  # noqa: BLE001
        print(f"  (tenure_map unavailable: {exc})", file=sys.stderr)
        tenure_map = None

    corpus = _load_approved_corpus(db_path, league_id, season, week_filter)
    print(f"\n  Approved {season} corpus rows in scope: {len(corpus)}")
    if not corpus:
        return [], {}

    # Pass 1: collect canonical claims per week.
    claims_by_week: dict[int, list[_CanonicalClaim]] = {}
    for week, _prose in corpus:
        claims_by_week[week] = _build_canonical_for_week(
            db_path, league_id, season, week,
            name_map, player_name_map, tenure_map,
        )

    # Aggregate canonical-franchise alias set for the run.
    all_canonical_franchises = frozenset(
        c.franchise
        for week_claims in claims_by_week.values()
        for c in week_claims
    )

    # Pass 2: classify each claim against its corresponding week's prose.
    prose_by_week = dict(corpus)
    all_classified: list[_ClassifiedClaim] = []
    for week, week_claims in claims_by_week.items():
        prose = prose_by_week[week]
        for claim in week_claims:
            other_franchises = frozenset(
                f for f in all_canonical_franchises if f != claim.franchise
            )
            all_classified.append(_classify(claim, prose, other_franchises))

    buckets: dict[str, int] = {}
    for c in all_classified:
        buckets[c.bucket] = buckets.get(c.bucket, 0) + 1
    return all_classified, buckets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Diagnostic-only harness for player-streak verb inversions. "
            "Per the §3.2 promotion criterion in the streak-verb scope memo."
        ),
    )
    parser.add_argument("--db", default=".local_squadvault.sqlite",
                        help="Path to .sqlite database.")
    parser.add_argument("--league-id", default="70985",
                        help="League ID (default: 70985 PFL Buddies).")
    parser.add_argument("--season", type=int, default=2025,
                        help="Season to scan (default: 2025).")
    parser.add_argument("--week-index", type=int, default=None,
                        help="Optional single-week filter; default scans all approved weeks.")
    parser.add_argument("--write-csv", type=str, default=None,
                        help="Optional path; writes per-claim detail to CSV.")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress per-emitter tables and specimens; print summary + gate only.")
    args = parser.parse_args(argv)

    if not os.path.exists(args.db):
        print(f"ERROR: DB not found at {args.db}", file=sys.stderr)
        return 1

    print("=" * 78)
    print("  PLAYER-STREAK VERB INVERSION DIAGNOSTIC")
    print(
        f"  league={args.league_id}  season={args.season}  "
        f"week={args.week_index if args.week_index is not None else 'ALL'}"
    )
    print("=" * 78)

    classified, buckets = _run_diagnostic(
        args.db, args.league_id, args.season, args.week_index,
    )

    if not classified:
        print("\n  No canonical player-streak claims fired in scope.")
        print("\n  GATE: CLOSE (no evidence in current corpus)")
        return 0

    by_emitter: dict[str, list[_ClassifiedClaim]] = {"P1": [], "P2": [], "P3": []}
    for c in classified:
        by_emitter[c.claim.emitter].append(c)

    if not args.quiet:
        for emitter in ("P1", "P2", "P3"):
            _print_per_emitter_table(emitter, by_emitter[emitter])

        for cat, label in [
            (CAT_DIRECTION_INVERSION, "DIRECTION_INVERSION specimens (integrity)"),
            (CAT_FRANCHISE_MISMATCH, "FRANCHISE_MISMATCH specimens (integrity)"),
            (CAT_THRESHOLD_INVERSION, "THRESHOLD_INVERSION specimens (integrity)"),
            (CAT_TENURE_NON_CONSECUTIVE, "TENURE_NON_CONSECUTIVE specimens (integrity)"),
            (CAT_DURATION_DRIFT, "DURATION_DRIFT specimens (editorial)"),
        ]:
            _print_specimens(classified, cat, label)

    print("\n" + "─" * 78)
    print(f"  Total canonical claims: {len(classified)}")
    print("  Bucket distribution:")
    for cat in CATEGORY_DISPLAY_ORDER:
        print(f"    {cat:<28} {buckets.get(cat, 0):>4}")

    gate = _apply_gate(buckets)
    print()
    if gate == "PROMOTE":
        print("  GATE: PROMOTE (integrity-tier specimens present)")
        print("  Decision: thread promotes to four-step playbook follow-on.")
    elif gate == "ELECT":
        print("  GATE: ELECT (editorial-tier specimens only)")
        print("  Decision: defer absent egregious distortion; record sentinel.")
    else:
        print("  GATE: CLOSE (no integrity- or editorial-tier specimens)")
        print("  Decision: close standing-backlog item with conditional reopening.")

    if args.write_csv:
        out = Path(args.write_csv)
        _write_csv(out, classified)
        print(f"\n  Per-claim CSV written: {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
