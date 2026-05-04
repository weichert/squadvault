"""Streak phrase string formatting — single source of truth.

Centralizes the rendering of streak claims (W-L sequence) into prose
strings used by the weekly-recap prompt path. Today, ~10 distinct
streak claim categories are emitted as ad-hoc f-strings across four
modules; the model paraphrases the verb at the boundary
("won 3 in a row" of a losing streak, "snapped" of an extended
streak), inverting direction or substituting the wrong verb. This
helper consolidates the canonical phrasings so:

1. Every consumer renders identical prose for identical inputs.
2. The downstream prompt instruction (Step 3.2) and verifier
   (Step 3.3) read the same canonical strings through this module
   — never by hand-writing the format.

Format selection rationale (per the Step 3 audit memo,
_observations/OBSERVATIONS_2026_05_04_STREAK_VERB_PRE_COMPUTATION_SCOPE.md
§4 taxonomy and §5 API):

- Status forms (T1-T4): "{name} on {N}-game win streak" /
  "{name} on {N}-game losing streak" for |streak| >= 4;
  "{name} has won 3 straight" / "{name} has lost 3 straight"
  for |streak| == 3. Threshold parity with _detect_streaks
  (narrative_angles_v1.py:172/180/188/196).
- Outcome forms (T5/T6): explicit verb-bearing clauses appended to
  the record string. The em-dash separator is preserved verbatim
  from the existing _outcome_detail body — the angle path does not
  apply _ascii_punct, so the em-dash reaches the prompt unchanged.
- Record forms (T8/T9/T10): tied/broke headlines plus an
  approach-to-record headline on the winning side only. Asymmetric
  by design (no "1 loss from record" form on the losing side); see
  memo §10 Q1.
- Marker form (T7): compact "W{N}" / "L{N}" / "-" used in the
  standings rows of the season-context prompt block.

Governance:

- Derived-only render helper. No side effects, no I/O, no canonical
  fact creation.
- Consumed by season_context_v1, narrative_angles_v1, and
  franchise_deep_angles_v1 in the weekly-recap prompt path.
- Out of scope:
    * league_history_v1 T11/T12 (longest-streak renderer lines):
      no natural helper analog — these are presentational forms
      that don't share a sub-phrase with the angle layer.
    * creative_layer_rivalry_v1 and chronicle/ modules: separate
      prompt lifecycles; tracked as follow-ups if the diagnostic
      surfaces drift there.
    * player streak emitters (PLAYER_HOT_STREAK / PLAYER_COLD_STREAK
      / detect_player_franchise_tenure in player_narrative_angles_v1):
      separate four-step thread per memo §3.2 if post-3.3
      measurement shows player-streak verb inversions.

Anti-fragility property:

If any template in this module changes (e.g. shorter verb-form for
mobile rendering), Step 3.1 consumers and Step 3.3 verifier checks
both pick up the change without edits to either consumer file. The
V8 follow-up lesson (OBSERVATIONS_2026_05_03_V8_REGRESSION_COVERAGE_GAP)
applies: instrumentation tracks its own data-layer contracts.
"""

from __future__ import annotations


def format_streak_phrase(streak: int) -> str | None:
    """Canonical noun phrase. Covers the sub-span shared by T1, T3, and D49.

    Args:
        streak: Signed streak length. Positive = wins, negative = losses,
            zero or |streak| == 1 = no canonical phrase.

    Returns:
        ``"{N}-game win streak"`` for ``streak >= 2``,
        ``"{N}-game losing streak"`` for ``streak <= -2``,
        ``None`` for ``streak in {-1, 0, 1}``.

    Notes:
        - The grammatical floor is 2 ("a 2-game win streak" reads
          naturally; "a 1-game win streak" doesn't). Consumer-side
          gating typically requires |streak| >= 4 (T1/T3, D49); the
          helper extends down to 2 to keep the noun-phrase contract
          generic. None of the in-scope §3.1 consumers calls this
          helper at |streak| in {2, 3} today.
        - The phrasing is "losing streak" (not "loss streak"), which
          is asymmetric with the marker form L{N} but consistent
          with the canonical English idiom and with the existing
          _detect_streaks output.
    """
    if streak >= 2:
        return f"{streak}-game win streak"
    if streak <= -2:
        return f"{abs(streak)}-game losing streak"
    return None


def format_streak_status(franchise_name: str, streak: int) -> str | None:
    """Canonical STREAK angle headline. Covers T1, T2, T3, T4.

    Args:
        franchise_name: Resolved franchise display name.
        streak: Signed streak length.

    Returns:
        Full headline string for ``|streak| >= 3``:

        * ``streak >= 4``  → ``"{name} on {N}-game win streak"`` (T1)
        * ``streak == 3``  → ``"{name} has won 3 straight"`` (T2)
        * ``streak <= -4`` → ``"{name} on {N}-game losing streak"`` (T3)
        * ``streak == -3`` → ``"{name} has lost 3 straight"`` (T4)

        ``None`` for ``|streak| < 3`` (no canonical headline).

    Notes:
        - Threshold parity with ``_detect_streaks``
          (narrative_angles_v1.py:172/180/188/196).
        - Long-form composes from ``format_streak_phrase`` so any
          future change to the "{N}-game ... streak" sub-phrase
          propagates to T1/T3 without a separate edit here.
    """
    if abs(streak) >= 4:
        phrase = format_streak_phrase(streak)
        # Non-None guaranteed: format_streak_phrase returns str for |streak| >= 2,
        # and we just gated on |streak| >= 4. Assert keeps mypy honest.
        assert phrase is not None
        return f"{franchise_name} on {phrase}"
    if streak == 3:
        return f"{franchise_name} has won 3 straight"
    if streak == -3:
        return f"{franchise_name} has lost 3 straight"
    return None


def format_streak_outcome(
    franchise_name: str,
    record_str: str,
    won_this_week: bool,
    opponent_name: str,
) -> str:
    """Canonical outcome detail clause. Covers T5, T6.

    Args:
        franchise_name: Resolved franchise display name. Accepted for
            API symmetry with the other helpers; not used in the
            current template body. Retained so a future template
            revision (e.g. "{name} beat {opp}...") can drop in
            without changing call-site signatures.
        record_str: Pre-formatted record string, e.g. ``"7-3"``.
        won_this_week: ``True`` if the franchise won the week's
            matchup (T5 continuation), ``False`` if it lost (T6
            extension).
        opponent_name: Resolved opponent display name.

    Returns:
        T5 (won): ``"Record: {rec}. Beat {opp} this week — streak continues."``
        T6 (lost): ``"Record: {rec}. Lost to {opp} this week — streak extended, not snapped."``

    Notes:
        - Em-dash (U+2014) is preserved verbatim. The narrative-angles
          render path does not apply ``_ascii_punct``, so the em-dash
          reaches the prompt unchanged. If a future refactor adds
          ``_ascii_punct`` to this path, the em-dash will normalize
          to a hyphen — ``test_streak_strings_v1`` documents this
          interaction.
        - SNAP cases (won-from-losing, lost-from-winning) are NOT
          covered. Those angles do not fire today; coverage gap
          surfaced as memo §10 Q2 and out of scope for Step 3.1.
    """
    # franchise_name reserved for future template revisions; see docstring.
    del franchise_name
    if won_this_week:
        return f"Record: {record_str}. Beat {opponent_name} this week — streak continues."
    return f"Record: {record_str}. Lost to {opponent_name} this week — streak extended, not snapped."


def format_streak_record(
    franchise_name: str,
    streak: int,
    record_length: int,
    record_holder_name: str,
) -> tuple[str, str] | None:
    """Canonical (headline, detail) for league-record streak claims. Covers T8, T9, T10.

    Args:
        franchise_name: Resolved franchise display name (current streak holder).
        streak: Signed streak length for the franchise.
        record_length: League-record streak length (always positive,
            from ``StreakRecord.length``).
        record_holder_name: Resolved name of the franchise that holds
            the existing league record.

    Returns:
        ``(headline, detail)`` tuple for an applicable record claim:

        * ``streak >= record_length``      → T8 tied/broke (winning)
        * ``streak == record_length - 1``  → T9 one-from-record (winning); detail is ``""``
        * ``abs(streak) >= record_length`` → T10 tied/broke (losing)

        ``None`` when no record claim applies (including the
        deliberately absent T9-loss form — see Notes).

    Notes:
        - Branch order matches ``_detect_streak_records``
          (narrative_angles_v1.py:552-580).
        - Asymmetry by design: there is no "{name} is 1 loss from
          the league loss streak record" form. The existing detector
          does not emit it; the helper preserves that behavior.
          Coverage gap surfaced as memo §10 Q1 and out of scope for
          Step 3.1.
        - T9 returns an empty detail string, matching the existing
          detector (narrative_angles_v1.py:566). The empty string is
          a deliberate convention — ``NarrativeAngle.detail`` is
          required, and "" signals that no supporting context is
          available for the approach-to-record case.
    """
    # Winning side: T8 (tied/broke) or T9 (one win from record).
    if streak >= 3:
        if streak >= record_length:
            headline = f"{franchise_name} tied/broke the league win streak record ({streak} games)"
            detail = f"Previous record: {record_length} by {record_holder_name}."
            return (headline, detail)
        if streak == record_length - 1:
            headline = f"{franchise_name} is 1 win from the league win streak record ({record_length})"
            return (headline, "")

    # Losing side: T10 (tied/broke) only — no T9-loss form (memo §10 Q1).
    if streak <= -3:
        if abs(streak) >= record_length:
            headline = (
                f"{franchise_name} tied/broke the league loss streak record "
                f"({abs(streak)} games)"
            )
            detail = f"Previous record: {record_length} by {record_holder_name}."
            return (headline, detail)

    return None


def format_streak_marker(streak: int) -> str:
    """Compact standings-row streak marker. Covers T7.

    Args:
        streak: Signed streak length.

    Returns:
        ``"W{N}"`` for ``streak > 0``,
        ``"L{N}"`` for ``streak < 0``,
        ``"-"`` for ``streak == 0``.

    Notes:
        - Direct lift of the existing ``_streak_str`` nested helper
          (season_context_v1.py:616-622). Behavior preserved
          byte-for-byte.
        - Helper-hosted but NOT verifier-required-verbatim — this is
          a structured cell in the standings table, not a prose
          claim. Step 3.3's STREAK_VERBATIM check ignores it.
    """
    if streak > 0:
        return f"W{streak}"
    if streak < 0:
        return f"L{abs(streak)}"
    return "-"
