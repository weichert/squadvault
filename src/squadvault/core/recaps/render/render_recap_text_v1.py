from __future__ import annotations

import json
from typing import Any, Dict


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def render_recap_text_v1(artifact: Dict[str, Any]) -> str:
    """
    Deterministic, non-hallucinated recap text.
    This does NOT infer details not present in the artifact.
    It summarizes counts + includes canonical_ids for traceability.
    """
    league_id = artifact.get("league_id")
    season = artifact.get("season")
    week_index = artifact.get("week_index")
    recap_version = artifact.get("recap_version")

    window = artifact.get("window", {}) or {}
    win_start = window.get("start")
    win_end = window.get("end")

    sel = artifact.get("selection", {}) or {}
    event_count = _safe_int(sel.get("event_count"), 0)
    counts_by_type = sel.get("counts_by_type", {}) or {}
    fingerprint = sel.get("fingerprint")
    canonical_ids = sel.get("canonical_ids", []) or []

    lines = []
    lines.append(f"SquadVault Weekly Recap — League {league_id} — Season {season} — Week {week_index} (v{recap_version})")
    lines.append("")
    lines.append(f"Window: {win_start} → {win_end}")
    lines.append(f"Selection fingerprint: {fingerprint}")
    lines.append("")
    lines.append(f"Events selected: {event_count}")

    if counts_by_type:
        lines.append("")
        lines.append("Breakdown:")
        for k in sorted(counts_by_type.keys()):
            lines.append(f"  - {k}: {counts_by_type[k]}")

    # Traceability / audit section (kept, but compact)
    lines.append("")
    lines.append("Trace (canonical_event ids):")
    # keep it readable; wrap-ish
    if canonical_ids:
        chunk = []
        for cid in canonical_ids:
            chunk.append(str(cid))
            if len(chunk) >= 25:
                lines.append("  " + ", ".join(chunk))
                chunk = []
        if chunk:
            lines.append("  " + ", ".join(chunk))
    else:
        lines.append("  (none)")

    lines.append("")
    lines.append("Note: This recap is summary-only and intentionally avoids fabricating details not present in event payloads.")
    return "\n".join(lines)


def render_recap_text_from_path_v1(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        artifact = json.load(f)
    return render_recap_text_v1(artifact)
