"""
Frozen baseline snapshot: STANDARD_SHOW_V1 InputNeed coverage (v1)

HARD RULES:
- Constant only (no dynamic computation)
- Tuple only
- No registry import
- No resolve_show_plan call
- No duplicates
"""

from __future__ import annotations

from pfl.enums import InputNeed

# Frozen contract surface: exact tuple snapshot (stable deterministic order).
STANDARD_SHOW_V1_INPUT_NEEDS_BASELINE: tuple[InputNeed, ...] = (InputNeed.SEASON_NARRATIVE_STATE, InputNeed.COACH_PROFILES)
