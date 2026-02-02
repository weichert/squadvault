from __future__ import annotations
from typing import Optional
from squadvault.eal.consume_v1 import EALDirectivesV1

import json
from typing import Any, Dict

from squadvault.core.recaps.render.voice_variants_v1 import get_voice_spec


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def _apply_voice_framing_v1(*, voice_id: str, rendered_text: str) -> str:
    """
    Deterministic render-time framing only.
    Must not alter facts, counts, ids, fingerprint, or window.
    """
    spec = get_voice_spec(voice_id)

    if spec.voice_id == "neutral":
        return rendered_text

    if spec.voice_id == "playful":
        prefix = "Commissioner’s note: same facts, different flavor.\n\n"
        return prefix + rendered_text

    if spec.voice_id == "dry":
        prefix = "Commissioner’s note: minimal framing.\n\n"
        return prefix + rendered_text

    # Defensive (get_voice_spec already validates)
    return rendered_text


def render_recap_text_v1(artifact: Dict[str, Any], *, voice_id: str = "neutral") -> str:
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

    # If window is unsafe/nonstandard, surface it explicitly for operator trust.
    if window is not None:
        mode = getattr(window, "mode", None)
        reason = getattr(window, "reason", None)
        if mode and mode != "LOCK_TO_LOCK":
            if reason:
                lines.append(f"Window mode: {mode} ({reason})")
            else:
                lines.append(f"Window mode: {mode}")
            lines.append("")

    lines.append(f"Events selected: {event_count}")

    if counts_by_type:
        lines.append("")
        lines.append("Breakdown:")
        for k in sorted(counts_by_type.keys()):
            lines.append(f"  - {k}: {counts_by_type[k]}")

    # Traceability / audit section (kept, but compact)
    lines.append("")
    lines.append("Trace (selection ids):")
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

    text = "\n".join(lines)
    return _apply_voice_framing_v1(voice_id=voice_id, rendered_text=text)



def render_recap_text_from_path_v1(
    path: str,
    *,
    voice_id: str = "neutral",
    eal_directives: Optional[EALDirectivesV1] = None,
) -> str:
    _ = eal_directives  # EAL v1: accepted but not applied at render layer
    with open(path, "r", encoding="utf-8") as f:
        artifact = json.load(f)
    return render_recap_text_v1(artifact, voice_id=voice_id)

