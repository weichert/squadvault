#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class SelectionMeta:
    league_id: str
    season: int
    week_index: int
    window_start: str
    window_end: str


FACTS_HEADER = "What happened (facts)"

TEAM_WON_RE = re.compile(r"^- (.+?) won .+ on waivers\.\s*$")
TEAM_ADDED_RE = re.compile(r"^- (.+?) added .+\(free agent\)\.\s*$")


def load_selection_meta(p: Path) -> SelectionMeta:
    obj = json.loads(p.read_text(encoding="utf-8"))
    return SelectionMeta(
        league_id=str(obj["league_id"]),
        season=int(obj["season"]),
        week_index=int(obj["week_index"]),
        window_start=str(obj["window_start"]),
        window_end=str(obj["window_end"]),
    )


def extract_facts_block(recap_md_path: Path) -> List[str]:
    lines = recap_md_path.read_text(encoding="utf-8").splitlines()
    try:
        i = next(idx for idx, line in enumerate(lines) if line.strip() == FACTS_HEADER)
    except StopIteration:
        raise SystemExit(f"ERROR: Missing '{FACTS_HEADER}' in {recap_md_path}")

    bullets: List[str] = []
    for line in lines[i + 1 :]:
        if line.strip() == "":
            break
        if not line.startswith("- "):
            raise SystemExit(f"ERROR: Non-bullet line inside facts block: {line!r}")
        bullets.append(line)

    if not bullets:
        raise SystemExit(f"ERROR: Facts block exists but is empty in {recap_md_path}")

    return bullets


def classify_and_count(bullets: List[str]):
    waivers: List[str] = []
    fas: List[str] = []
    team_counts = Counter()
    team_waiver_counts = Counter()

    for b in bullets:
        m1 = TEAM_WON_RE.match(b)
        m2 = TEAM_ADDED_RE.match(b)
        if m1:
            team = m1.group(1)
            waivers.append(b)
            team_counts[team] += 1
            team_waiver_counts[team] += 1
        elif m2:
            team = m2.group(1)
            fas.append(b)
            team_counts[team] += 1
        else:
            # Unknown bullet format: allowed but not classifiable.
            pass

    return waivers, fas, team_counts, team_waiver_counts


def one_sentence_summary(week_index: int, has_waivers: bool, has_fas: bool) -> str:
    if has_waivers and has_fas:
        return (
            f"Week {week_index} was an active waiver week, with multiple rosters reshaped through claims "
            f"and a steady stream of free-agent adds."
        )
    if has_waivers:
        return f"Week {week_index} was driven by waiver claims, with several teams making targeted moves."
    if has_fas:
        return f"Week {week_index} leaned on free-agent adds, with incremental roster changes across the league."
    return f"Week {week_index} was quiet on the transaction wire."


def turning_points(team_counts: Counter, has_waivers: bool, has_fas: bool) -> List[str]:
    beats: List[str] = []

    if team_counts:
        top_team, top_n = team_counts.most_common(1)[0]
        if top_n >= 3:
            beats.append(f"- **{top_team}** was the most active roster, accounting for {top_n} moves this week.")

        # up to 2 additional multi-move teams
        for team, n in team_counts.most_common():
            if team == top_team:
                continue
            if n >= 2:
                beats.append(f"- **{team}** made multiple moves, adding {n} new pieces.")
            if len(beats) >= 3:
                break

    if has_waivers and has_fas:
        beats.append("- Several teams supplemented waiver activity with late-week free-agent adds.")

    return beats[:4]


def notable_moves(waivers: List[str], fas: List[str], team_waiver_counts: Counter) -> List[str]:
    out: List[str] = []

    if waivers:
        out.append("**Waivers**")
        out.append(f"- {len(waivers)} successful waiver claims were awarded across the league.")
        if team_waiver_counts:
            top_team, top_n = team_waiver_counts.most_common(1)[0]
            if top_n >= 2:
                out.append(f"- {top_team} accounted for {top_n} of them, the highest total this week.")
        out.append("")

    if fas:
        out.append("**Free agents**")
        teams = sorted({TEAM_ADDED_RE.match(b).group(1) for b in fas if TEAM_ADDED_RE.match(b)})
        out.append(f"- {len(fas)} free-agent additions were made by {len(teams)} teams.")
        return out

    if out and out[-1] == "":
        out.pop()

    return out


def build_sharepack(meta: SelectionMeta, facts_bullets: List[str]) -> str:
    waivers, fas, team_counts, team_waiver_counts = classify_and_count(facts_bullets)

    summary = one_sentence_summary(meta.week_index, bool(waivers), bool(fas))
    beats = turning_points(team_counts, bool(waivers), bool(fas))
    notable = notable_moves(waivers, fas, team_waiver_counts)

    lines: List[str] = []
    lines.append("## Writing Room Sharepack v1")
    lines.append(f"**League {meta.league_id} · Season {meta.season} · Week {meta.week_index}**")
    lines.append(f"**Window:** {meta.window_start} → {meta.window_end}")
    lines.append("")
    lines.append("### One-sentence week summary")
    lines.append(summary)
    lines.append("")
    lines.append("### What happened (facts)")
    lines.extend(facts_bullets)
    lines.append("")
    lines.append("### The week’s turning points")
    if beats:
        lines.extend(beats)
    else:
        lines.append("- This week’s activity was straightforward and required no additional framing.")
    lines.append("")
    if notable:
        lines.append("### Notable moves")
        lines.extend(notable)
        lines.append("")
    lines.append("### Trust & boundaries")
    lines.append("Generated solely from the week’s approved selection set. No projections, inferred intent, or external data.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build Writing Room Sharepack v1 from selection_set_v1.json + recap.md facts block."
    )
    ap.add_argument("--selection-set", required=True, help="Path to selection_set_v1.json")
    ap.add_argument("--recap-md", required=True, help="Path to recap.md (must contain 'What happened (facts)' block)")
    ap.add_argument("--out", required=True, help="Output path for sharepack markdown (e.g., sharepack_v1.md)")
    args = ap.parse_args()

    selection_path = Path(args.selection_set)
    recap_md_path = Path(args.recap_md)
    out_path = Path(args.out)

    meta = load_selection_meta(selection_path)
    facts = extract_facts_block(recap_md_path)
    sharepack = build_sharepack(meta, facts)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(sharepack, encoding="utf-8")
    print(f"OK: wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
