"""Matchup score string formatting — single source of truth.

Centralizes the rendering of canonical (winner_score, loser_score)
pairs into prose-safe strings. The historical hyphen-separated form
(e.g. "107.65-65.40") is ambiguous in the prompt: a model can read
the hyphen as a decimal separator and emit a rounded form
("108-65"), materially misrepresenting the margin.

The "to" format ("107.65 to 65.40") removes the hyphen-as-separator
hazard at the source. All matchup-score render sites in the
weekly-recap prompt path call this helper so the format change
propagates without drift.

Format selection rationale (per Step 1 diagnostic memo,
_observations/OBSERVATIONS_2026_05_03_SCORE_RENDERING_PRE_FIX_DIAGNOSTIC.md):
- Robust to _ascii_punct normalization — no characters in " to " are
  in the curly-apostrophe / en-dash / em-dash replacement set.
- Reads naturally in bullet form ("Winner beat Loser 107.65 to 65.40")
  and in narrative prose.
- Lower friction than en-dash with carve-out (which would expand the
  _ascii_punct surface) or "vs." (which reads awkwardly alongside
  "beat").

Governance:
- Derived-only render helper. No side effects, no I/O, no canonical
  fact creation.
- Consumed by deterministic_bullets_v1, season_context_v1, and
  narrative_angles_v1 in the weekly-recap prompt path.
- Out of scope: creative_layer_rivalry_v1 (separate module on a
  separate prompt lifecycle; tracked as a follow-up).
"""

from __future__ import annotations


def format_matchup_score_str(winner_score: float, loser_score: float) -> str:
    """Render a canonical (winner_score, loser_score) pair as prose-safe text.

    Returns a string of the form "{winner:.2f} to {loser:.2f}" — the
    unambiguous "to" format selected for the weekly-recap prompt path.

    Args:
        winner_score: Winning team score. May be int, float, or any
            numeric value coercible to float at the call site.
        loser_score: Losing team score. Same coercion rules.

    Returns:
        Two-decimal-place "to"-separated string, e.g. "107.65 to 65.40".

    Notes:
        - Always renders both sides at .2f precision regardless of
          whether the input is int or float. This matches the bullet
          and context-derivation conventions and keeps the helper's
          output deterministic.
        - The helper does NOT validate that winner_score >= loser_score.
          That is the caller's responsibility (the canonical event
          payload already encodes which side won). Tied matchups call
          with equal scores; the format is order-preserving.
        - Negative scores render as "-2.50 to 0.00". Acceptable in
          context ("X beat Y -2.50 to 0.00") though rare in practice.
    """
    return f"{winner_score:.2f} to {loser_score:.2f}"
