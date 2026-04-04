"""Recap Verifier v1 — post-generation verification gate.

Contract:
- Deterministic: identical inputs produce identical verification results.
- Non-modifying: verifies only — never edits, rewrites, or filters.
- Reconstructable: drop and rebuild produces identical results.
- No inference: every check is a binary comparison against canonical data.

Verification Categories (V1):
1. SCORE — matchup scores mentioned in recap vs canonical WEEKLY_MATCHUP_RESULT
2. SUPERLATIVE — "season high", "all-time record" claims vs actual MAX/MIN
3. STREAK — "X-game streak", "snapped/extended" vs computed streaks

All three are HARD failure categories. A hard failure means the recap
contains a provably false factual claim.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from squadvault.core.storage.session import DatabaseSession

# ── Output dataclasses ───────────────────────────────────────────────


@dataclass(frozen=True)
class VerificationFailure:
    """A single verified-false claim in the recap text."""
    category: str     # "SCORE", "SUPERLATIVE", "STREAK"
    severity: str     # "HARD" (V1 only has HARD)
    claim: str        # the extracted claim from recap text
    evidence: str     # what canonical data actually shows


@dataclass(frozen=True)
class VerificationResult:
    """Full verification result for a recap draft."""
    passed: bool
    hard_failures: tuple[VerificationFailure, ...]
    soft_failures: tuple[VerificationFailure, ...]
    checks_run: int

    @property
    def hard_failure_count(self) -> int:
        return len(self.hard_failures)

    @property
    def soft_failure_count(self) -> int:
        return len(self.soft_failures)


# ── Data loading ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class _MatchupFact:
    """A canonical matchup result for verification."""
    week: int
    winner_id: str
    loser_id: str
    winner_score: float
    loser_score: float


def _load_season_matchups(
    db_path: str,
    league_id: str,
    season: int,
) -> list[_MatchupFact]:
    """Load all WEEKLY_MATCHUP_RESULT events for a season."""
    results: list[_MatchupFact] = []
    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT payload_json
               FROM v_canonical_best_events
               WHERE league_id = ? AND season = ?
                 AND event_type = 'WEEKLY_MATCHUP_RESULT'
               ORDER BY occurred_at ASC NULLS LAST""",
            (str(league_id), int(season)),
        ).fetchall()

    for row in rows:
        try:
            p = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        except (ValueError, TypeError):
            continue
        if not isinstance(p, dict):
            continue
        winner_id = p.get("winner_franchise_id") or p.get("winner_team_id")
        loser_id = p.get("loser_franchise_id") or p.get("loser_team_id")
        if not winner_id or not loser_id:
            continue
        try:
            results.append(_MatchupFact(
                week=int(p.get("week", 0)),
                winner_id=str(winner_id).strip(),
                loser_id=str(loser_id).strip(),
                winner_score=float(p["winner_score"]),
                loser_score=float(p["loser_score"]),
            ))
        except (ValueError, TypeError, KeyError):
            continue
    return results


def _load_all_matchups(
    db_path: str,
    league_id: str,
) -> list[_MatchupFact]:
    """Load ALL WEEKLY_MATCHUP_RESULT events across all seasons."""
    results: list[_MatchupFact] = []
    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT payload_json
               FROM v_canonical_best_events
               WHERE league_id = ?
                 AND event_type = 'WEEKLY_MATCHUP_RESULT'
               ORDER BY occurred_at ASC NULLS LAST""",
            (str(league_id),),
        ).fetchall()

    for row in rows:
        try:
            p = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        except (ValueError, TypeError):
            continue
        if not isinstance(p, dict):
            continue
        winner_id = p.get("winner_franchise_id") or p.get("winner_team_id")
        loser_id = p.get("loser_franchise_id") or p.get("loser_team_id")
        if not winner_id or not loser_id:
            continue
        try:
            results.append(_MatchupFact(
                week=int(p.get("week", 0)),
                winner_id=str(winner_id).strip(),
                loser_id=str(loser_id).strip(),
                winner_score=float(p["winner_score"]),
                loser_score=float(p["loser_score"]),
            ))
        except (ValueError, TypeError, KeyError):
            continue
    return results


def _load_franchise_names(
    db_path: str,
    league_id: str,
    season: int,
) -> dict[str, str]:
    """Load franchise_id -> name map for the season."""
    name_map: dict[str, str] = {}
    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT franchise_id, name
               FROM franchise_directory
               WHERE league_id = ? AND season = ?""",
            (str(league_id), int(season)),
        ).fetchall()
    for row in rows:
        if row[0] and row[1]:
            name_map[str(row[0]).strip()] = str(row[1]).strip()
    return name_map


def _load_player_season_high(
    db_path: str,
    league_id: str,
    season: int,
) -> float | None:
    """Return the highest individual player score of the season."""
    with DatabaseSession(db_path) as con:
        row = con.execute(
            """SELECT MAX(CAST(json_extract(payload_json, '$.score') AS REAL))
               FROM v_canonical_best_events
               WHERE league_id = ? AND season = ?
                 AND event_type = 'WEEKLY_PLAYER_SCORE'""",
            (str(league_id), int(season)),
        ).fetchone()
    if row and row[0] is not None:
        return float(row[0])
    return None


def _load_alltime_player_high(
    db_path: str,
    league_id: str,
) -> float | None:
    """Return the highest individual player score across all seasons."""
    with DatabaseSession(db_path) as con:
        row = con.execute(
            """SELECT MAX(CAST(json_extract(payload_json, '$.score') AS REAL))
               FROM v_canonical_best_events
               WHERE league_id = ?
                 AND event_type = 'WEEKLY_PLAYER_SCORE'""",
            (str(league_id),),
        ).fetchone()
    if row and row[0] is not None:
        return float(row[0])
    return None


# ── Extraction helpers ───────────────────────────────────────────────


def _extract_shareable_recap(full_text: str) -> str:
    """Extract the narrative prose between SHAREABLE RECAP delimiters.

    If delimiters are absent, returns the full text (the verifier should
    still work on raw recap text for testing).
    """
    start_marker = "--- SHAREABLE RECAP ---"
    end_marker = "--- END SHAREABLE RECAP ---"
    start = full_text.find(start_marker)
    end = full_text.find(end_marker)
    if start >= 0 and end > start:
        return full_text[start + len(start_marker):end].strip()
    return full_text.strip()


def _normalize_apostrophes(text: str) -> str:
    """Normalize curly/smart apostrophes to straight ASCII apostrophes.

    MFL franchise names may use U+2019 (RIGHT SINGLE QUOTATION MARK)
    while LLM-generated recap text uses U+0027 (APOSTROPHE).
    """
    return text.replace("\u2018", "'").replace("\u2019", "'")


def _build_reverse_name_map(name_map: dict[str, str]) -> dict[str, str]:
    """Build name -> franchise_id reverse lookup.

    Adds both exact-case and lowercased entries for robustness.
    Normalizes apostrophes so curly quotes match straight quotes.
    """
    reverse: dict[str, str] = {}
    for fid, name in name_map.items():
        normalized = _normalize_apostrophes(name)
        reverse[normalized] = fid
        reverse[normalized.lower()] = fid
    return reverse


# ── Category 1: Score Verification ───────────────────────────────────

# Pattern: a fantasy score like "120.50" or "95.30" (2-3 digits, dot, 2 digits)
_SCORE_PATTERN = re.compile(r'\b(\d{2,3}\.\d{2})\b')


def _find_nearby_franchise(
    text: str,
    score_pos: int,
    reverse_name_map: dict[str, str],
    *,
    window: int = 150,
) -> str | None:
    """Find the franchise name most likely associated with a score mention.

    In recap prose, the dominant pattern is "Team scored X" — the team name
    precedes the score. This function prefers franchise names that appear
    BEFORE the score position. If no preceding name is found, it falls back
    to names after the score.

    Returns the franchise_id if found, None otherwise.
    """
    # Search the text before the score first (stronger association)
    before_start = max(0, score_pos - window)
    before_context = _normalize_apostrophes(text[before_start:score_pos]).lower()

    best_match: str | None = None
    best_dist: int = window + 1

    # Pass 1: look for franchise names BEFORE the score (preferred)
    for name, fid in reverse_name_map.items():
        if not name.islower():
            continue
        idx = before_context.rfind(name)  # rightmost = closest to score
        if idx >= 0:
            dist = len(before_context) - idx - len(name)
            if dist < best_dist:
                best_dist = dist
                best_match = fid

    if best_match is not None:
        return best_match

    # Pass 2: look for franchise names AFTER the score (fallback)
    after_end = min(len(text), score_pos + window)
    after_context = _normalize_apostrophes(text[score_pos:after_end]).lower()

    for name, fid in reverse_name_map.items():
        if not name.islower():
            continue
        idx = after_context.find(name)
        if idx >= 0 and idx < best_dist:
            best_dist = idx
            best_match = fid

    return best_match


def _resolve_display_name(
    franchise_id: str,
    reverse_name_map: dict[str, str],
) -> str:
    """Resolve franchise_id back to display name (exact-case entry)."""
    for name, fid in reverse_name_map.items():
        if fid == franchise_id and not name.islower():
            return name
    return franchise_id


def verify_scores(
    recap_text: str,
    week_matchups: list[_MatchupFact],
    week: int,
    reverse_name_map: dict[str, str],
) -> list[VerificationFailure]:
    """Verify matchup scores mentioned in the recap against canonical data.

    Uses a two-pass strategy:
    1. Find score PAIRS that match canonical matchups (both winner and loser
       scores appear near each other). These are correctly stated matchups.
    2. Check remaining solo scores attributed to a specific franchise.

    This avoids false positives from "X beat Y 123.20-86.35" patterns where
    proximity-based franchise matching picks the wrong team.
    """
    failures: list[VerificationFailure] = []

    # Build matchup score pairs for this week
    week_matchup_pairs: list[tuple[float, float]] = []
    canonical_scores: dict[str, float] = {}
    all_week_scores: set[float] = set()
    for m in week_matchups:
        if m.week != week:
            continue
        week_matchup_pairs.append((m.winner_score, m.loser_score))
        canonical_scores[m.winner_id] = m.winner_score
        canonical_scores[m.loser_id] = m.loser_score
        all_week_scores.add(m.winner_score)
        all_week_scores.add(m.loser_score)

    if not canonical_scores:
        return []

    # Extract all score positions in the text
    score_positions: list[tuple[int, float]] = []
    for match in _SCORE_PATTERN.finditer(recap_text):
        try:
            val = float(match.group(1))
        except ValueError:
            continue
        if 40.0 <= val <= 250.0:
            score_positions.append((match.start(), val))

    # Pass 1: Find score pairs that match canonical matchups.
    # Two scores within 80 chars of each other that match a matchup pair
    # are a correctly stated matchup — mark both positions as pair-verified.
    # 80 chars handles patterns like "Team A fell to Team B Name 179.55-103.55"
    # where franchise names add 20-40 chars between the two scores.
    _PAIR_WINDOW = 80
    pair_verified: set[int] = set()
    for i, (pos_a, val_a) in enumerate(score_positions):
        for j, (pos_b, val_b) in enumerate(score_positions):
            if i >= j:
                continue
            if abs(pos_b - pos_a) > _PAIR_WINDOW:
                continue
            # Check if these two scores match any matchup pair (either order)
            for w_score, l_score in week_matchup_pairs:
                if ((abs(val_a - w_score) <= 0.01 and abs(val_b - l_score) <= 0.01) or
                        (abs(val_a - l_score) <= 0.01 and abs(val_b - w_score) <= 0.01)):
                    pair_verified.add(i)
                    pair_verified.add(j)

    # Pass 2: Check solo scores (not part of a verified pair)
    for i, (pos, mentioned_score) in enumerate(score_positions):
        if i in pair_verified:
            continue

        if mentioned_score not in all_week_scores:
            # Score not in any matchup — likely player/FAAB. Skip.
            continue

        franchise_id = _find_nearby_franchise(
            recap_text, pos, reverse_name_map,
        )

        if franchise_id is None:
            continue

        if franchise_id not in canonical_scores:
            continue

        canonical = canonical_scores[franchise_id]
        if abs(mentioned_score - canonical) <= 0.01:
            continue  # correct

        fname = _resolve_display_name(franchise_id, reverse_name_map)

        failures.append(VerificationFailure(
            category="SCORE",
            severity="HARD",
            claim=f"{fname} scored {mentioned_score:.2f}",
            evidence=(
                f"Canonical score for {fname} in Week {week}: "
                f"{canonical:.2f}, not {mentioned_score:.2f}."
            ),
        ))

    return failures


# ── Category 2: Superlative Verification ─────────────────────────────

_SEASON_HIGH_PATTERN = re.compile(
    r'(?:season[- ]?high|highest[^.]{0,40}(?:this season|of the season|season))',
    re.IGNORECASE,
)
_ALLTIME_PATTERN = re.compile(
    r'(?:all[- ]?time(?:\s+(?:high|record|best|mark))?|'
    r'league\s+(?:history|record)|'
    r'(?:highest|most|best|record)[^.]{0,40}(?:all[- ]?time|league\s+history|'
    r'(?:across|in|over)\s+\d+\s+seasons?))',
    re.IGNORECASE,
)
_SEASON_LOW_PATTERN = re.compile(
    r'(?:season[- ]?low|lowest[^.]{0,40}(?:this season|of the season|season))',
    re.IGNORECASE,
)


def _extract_nearby_score(text: str, match_pos: int, *, window: int = 100) -> float | None:
    """Extract the closest score (XX.XX) near a superlative keyword."""
    start = max(0, match_pos - window)
    end = min(len(text), match_pos + window)
    context = text[start:end]
    best: float | None = None
    best_dist = window + 1
    for m in _SCORE_PATTERN.finditer(context):
        try:
            val = float(m.group(1))
        except ValueError:
            continue
        keyword_offset = match_pos - start
        dist = abs(m.start() - keyword_offset)
        if dist < best_dist:
            best_dist = dist
            best = val
    return best


def verify_superlatives(
    recap_text: str,
    season_matchups: list[_MatchupFact],
    all_matchups: list[_MatchupFact] | None,
    season: int,
    season_player_high: float | None,
    alltime_player_high: float | None,
) -> list[VerificationFailure]:
    """Verify superlative claims (season high/low, all-time records)."""
    failures: list[VerificationFailure] = []

    # Compute actual season highs/lows from matchup scores
    season_scores = [
        score for m in season_matchups
        for score in (m.winner_score, m.loser_score)
    ]
    actual_season_high_team = max(season_scores) if season_scores else None
    actual_season_low_team = min(season_scores) if season_scores else None

    alltime_scores = (
        [score for m in all_matchups for score in (m.winner_score, m.loser_score)]
        if all_matchups else []
    )
    actual_alltime_high_team = max(alltime_scores) if alltime_scores else None

    # Check "season high" claims
    for match in _SEASON_HIGH_PATTERN.finditer(recap_text):
        claimed_score = _extract_nearby_score(recap_text, match.start())
        if claimed_score is None:
            continue

        # Can't verify without canonical data — silence over false positive
        if actual_season_high_team is None and season_player_high is None:
            continue

        is_valid_team = (
            actual_season_high_team is not None
            and abs(claimed_score - actual_season_high_team) <= 0.01
        )
        is_valid_player = (
            season_player_high is not None
            and abs(claimed_score - season_player_high) <= 0.01
        )

        if not is_valid_team and not is_valid_player:
            evidence_parts: list[str] = []
            if actual_season_high_team is not None:
                evidence_parts.append(
                    f"actual season-high team score: {actual_season_high_team:.2f}"
                )
            if season_player_high is not None:
                evidence_parts.append(
                    f"actual season-high player score: {season_player_high:.2f}"
                )
            failures.append(VerificationFailure(
                category="SUPERLATIVE",
                severity="HARD",
                claim=f"Season high of {claimed_score:.2f}",
                evidence=(
                    f"Claimed {claimed_score:.2f} as season high, but "
                    + "; ".join(evidence_parts) + "."
                ),
            ))

    # Check "season low" claims
    for match in _SEASON_LOW_PATTERN.finditer(recap_text):
        claimed_score = _extract_nearby_score(recap_text, match.start())
        if claimed_score is None:
            continue

        if actual_season_low_team is not None and abs(claimed_score - actual_season_low_team) > 0.01:
            failures.append(VerificationFailure(
                category="SUPERLATIVE",
                severity="HARD",
                claim=f"Season low of {claimed_score:.2f}",
                evidence=(
                    f"Claimed {claimed_score:.2f} as season low, but "
                    f"actual season-low team score: {actual_season_low_team:.2f}."
                ),
            ))

    # Check "all-time" / "league history" / "across N seasons" claims
    for match in _ALLTIME_PATTERN.finditer(recap_text):
        # Bug fix: "all-time" in series context (e.g. "all-time series
        # dominance to 21-7") is about H2H scope, not a scoring record.
        # Check the surrounding text for series-context words and skip.
        _at_start = max(0, match.start() - 10)
        _at_end = min(len(recap_text), match.end() + 40)
        _at_context = recap_text[_at_start:_at_end].lower()
        if re.search(
            r'all[- ]?time\s+(?:series|meetings?|edge|dominance|lead|head|h2h|rivalry)',
            _at_context,
        ):
            continue

        claimed_score = _extract_nearby_score(recap_text, match.start())
        if claimed_score is None:
            continue

        # Can't verify without canonical data
        if actual_alltime_high_team is None and alltime_player_high is None:
            continue

        is_valid_team = (
            actual_alltime_high_team is not None
            and abs(claimed_score - actual_alltime_high_team) <= 0.01
        )
        is_valid_player = (
            alltime_player_high is not None
            and abs(claimed_score - alltime_player_high) <= 0.01
        )

        if not is_valid_team and not is_valid_player:
            evidence_parts = []
            if actual_alltime_high_team is not None:
                evidence_parts.append(
                    f"actual all-time high team score: {actual_alltime_high_team:.2f}"
                )
            if alltime_player_high is not None:
                evidence_parts.append(
                    f"actual all-time high player score: {alltime_player_high:.2f}"
                )
            failures.append(VerificationFailure(
                category="SUPERLATIVE",
                severity="HARD",
                claim=f"All-time/league-history claim of {claimed_score:.2f}",
                evidence=(
                    f"Claimed {claimed_score:.2f} as all-time record, but "
                    + "; ".join(evidence_parts) + "."
                ),
            ))

    return failures


# ── Category 3: Streak Verification ──────────────────────────────────

_STREAK_PATTERN = re.compile(
    r'(?:'
    r'(\d+)[- ]?game\s+(?:win(?:ning)?|losing|los[st])\s*(?:streak|skid)|'
    r'(?:won|lost|losing)\s+(\d+)\s+(?:straight|consecutive|in a row)'
    r')',
    re.IGNORECASE,
)

_SNAP_PATTERN = re.compile(
    r'\b(snapped?|broke|ended|broken)\b[^.]{0,80}'
    r'(?:streak|skid|losing|winning|straight|consecutive)',
    re.IGNORECASE,
)


def _compute_streaks(
    matchups: list[_MatchupFact],
    through_week: int,
) -> dict[str, int]:
    """Compute current streak for each franchise through a given week.

    Returns dict of franchise_id -> streak count.
    Positive = consecutive wins, negative = consecutive losses.
    """
    franchise_results: dict[str, list[tuple[int, bool]]] = {}
    for m in matchups:
        if m.week > through_week:
            continue
        if m.winner_id not in franchise_results:
            franchise_results[m.winner_id] = []
        franchise_results[m.winner_id].append((m.week, True))

        if m.loser_id not in franchise_results:
            franchise_results[m.loser_id] = []
        franchise_results[m.loser_id].append((m.week, False))

    streaks: dict[str, int] = {}
    for fid, results in franchise_results.items():
        results.sort(key=lambda x: x[0])
        if not results:
            streaks[fid] = 0
            continue
        last_was_win = results[-1][1]
        count = 0
        for _, won in reversed(results):
            if won == last_was_win:
                count += 1
            else:
                break
        streaks[fid] = count if last_was_win else -count
    return streaks


def verify_streaks(
    recap_text: str,
    season_matchups: list[_MatchupFact],
    week: int,
    reverse_name_map: dict[str, str],
) -> list[VerificationFailure]:
    """Verify streak claims in the recap against computed streaks."""
    failures: list[VerificationFailure] = []

    actual_streaks = _compute_streaks(season_matchups, through_week=week)
    pre_week_streaks = _compute_streaks(season_matchups, through_week=week - 1)

    # Check explicit streak count claims
    for match in _STREAK_PATTERN.finditer(recap_text):
        claimed_count_str = match.group(1) or match.group(2)
        if not claimed_count_str:
            continue
        claimed_count = int(claimed_count_str)

        context = match.group(0).lower()
        is_losing = any(w in context for w in ("losing", "lost", "loss", "skid"))

        franchise_id = _find_nearby_franchise(
            recap_text, match.start(), reverse_name_map, window=150,
        )
        if franchise_id is None:
            continue

        actual = actual_streaks.get(franchise_id, 0)
        pre_actual = pre_week_streaks.get(franchise_id, 0)
        fname = _resolve_display_name(franchise_id, reverse_name_map)

        if is_losing:
            actual_count = abs(actual) if actual < 0 else 0
            pre_count = abs(pre_actual) if pre_actual < 0 else 0
            if claimed_count != actual_count and claimed_count != pre_count:
                failures.append(VerificationFailure(
                    category="STREAK",
                    severity="HARD",
                    claim=f"{fname} has/had a {claimed_count}-game losing streak",
                    evidence=(
                        f"Actual losing streak for {fname}: "
                        f"{actual_count} (current), {pre_count} (pre-week). "
                        f"Claimed: {claimed_count}."
                    ),
                ))
        else:
            actual_count = actual if actual > 0 else 0
            pre_count = pre_actual if pre_actual > 0 else 0
            if claimed_count != actual_count and claimed_count != pre_count:
                failures.append(VerificationFailure(
                    category="STREAK",
                    severity="HARD",
                    claim=f"{fname} has/had a {claimed_count}-game win streak",
                    evidence=(
                        f"Actual win streak for {fname}: "
                        f"{actual_count} (current), {pre_count} (pre-week). "
                        f"Claimed: {claimed_count}."
                    ),
                ))

    # Check "snapped" logic for losing streaks
    for match in _SNAP_PATTERN.finditer(recap_text):
        snap_context = match.group(0).lower()
        is_losing_snap = any(w in snap_context for w in ("losing", "lost", "skid"))
        if not is_losing_snap:
            continue

        franchise_id = _find_nearby_franchise(
            recap_text, match.start(), reverse_name_map, window=150,
        )
        if franchise_id is None:
            continue

        pre_streak = pre_week_streaks.get(franchise_id, 0)
        current_streak = actual_streaks.get(franchise_id, 0)
        fname = _resolve_display_name(franchise_id, reverse_name_map)

        if pre_streak >= 0:
            failures.append(VerificationFailure(
                category="STREAK",
                severity="HARD",
                claim=f"{fname} snapped a losing streak",
                evidence=(
                    f"{fname} had no losing streak entering Week {week} "
                    f"(pre-week streak: {pre_streak})."
                ),
            ))
        elif current_streak < 0:
            failures.append(VerificationFailure(
                category="STREAK",
                severity="HARD",
                claim=f"{fname} snapped a losing streak",
                evidence=(
                    f"{fname} lost in Week {week} — streak extended to "
                    f"{abs(current_streak)}, not snapped."
                ),
            ))

    return failures


# ── Category 4: Series Record Verification ───────────────────────────

# Pattern: "X-Y" (W-L record) near series/rivalry keywords
# (?<!\d) prevents matching the tail of a larger number (e.g. "8-9" from "18-9")
_SERIES_RECORD_PATTERN = re.compile(
    r'(?:'
    r'(?:leads?|trails?|series|rivalry|all[- ]?time|meetings?|record)\s[^.]{0,40}'
    r'(?<!\d)(\d{1,2})-(\d{1,2})(?:-(\d{1,2}))?'
    r'|'
    r'(?<!\d)(\d{1,2})-(\d{1,2})(?:-(\d{1,2}))?\s[^.]{0,40}'
    r'(?:series|rivalry|all[- ]?time|meetings?|record|lead)'
    r')',
    re.IGNORECASE,
)


def _find_two_franchises(
    text: str,
    match_pos: int,
    reverse_name_map: dict[str, str],
    *,
    window: int = 200,
) -> tuple[str | None, str | None]:
    """Find two franchise names near a series record claim.

    Returns (franchise_a_id, franchise_b_id) or (None, None) if fewer
    than two franchises are found in the window.
    """
    start = max(0, match_pos - window)
    end = min(len(text), match_pos + window)
    context = _normalize_apostrophes(text[start:end]).lower()

    found: list[tuple[int, str]] = []  # (position, franchise_id)
    seen_ids: set[str] = set()

    for name, fid in reverse_name_map.items():
        if not name.islower():
            continue
        if fid in seen_ids:
            continue
        idx = context.find(name)
        if idx >= 0:
            found.append((idx, fid))
            seen_ids.add(fid)

    if len(found) < 2:
        return (None, None)

    # Return the two closest to the match position
    found.sort(key=lambda x: abs(x[0] - (match_pos - start)))
    return (found[0][1], found[1][1])


def verify_series_records(
    recap_text: str,
    all_matchups: list[_MatchupFact],
    reverse_name_map: dict[str, str],
) -> list[VerificationFailure]:
    """Verify head-to-head series record claims against canonical matchups."""
    failures: list[VerificationFailure] = []

    if not all_matchups:
        return []

    for match in _SERIES_RECORD_PATTERN.finditer(recap_text):
        # Extract the W-L(-T) record — groups depend on which branch matched
        if match.group(1) is not None:
            w_str, l_str, t_str = match.group(1), match.group(2), match.group(3)
        else:
            w_str, l_str, t_str = match.group(4), match.group(5), match.group(6)

        try:
            claimed_w = int(w_str)
            claimed_l = int(l_str)
            claimed_t = int(t_str) if t_str else 0
        except (ValueError, TypeError):
            continue

        # Find the two franchises this record is about
        fid_a, fid_b = _find_two_franchises(
            recap_text, match.start(), reverse_name_map,
        )
        if fid_a is None or fid_b is None:
            continue

        # Compute actual H2H from canonical matchups
        actual_a_wins = 0
        actual_b_wins = 0
        actual_ties = 0
        for m in all_matchups:
            pair = {m.winner_id, m.loser_id}
            if pair != {fid_a, fid_b}:
                continue
            if m.winner_id == fid_a:
                actual_a_wins += 1
            elif m.winner_id == fid_b:
                actual_b_wins += 1
            # Ties would need an is_tie field — not in _MatchupFact currently

        total = actual_a_wins + actual_b_wins + actual_ties
        if total == 0:
            continue

        # Check if claimed record matches actual (in either direction)
        matches_ab = (
            claimed_w == actual_a_wins
            and claimed_l == actual_b_wins
            and claimed_t == actual_ties
        )
        matches_ba = (
            claimed_w == actual_b_wins
            and claimed_l == actual_a_wins
            and claimed_t == actual_ties
        )

        if not matches_ab and not matches_ba:
            # Bug fix: tenure-scoped records ("4-0 under current ownership")
            # are a subset of all-time meetings. The verifier only has the
            # all-time H2H, so it would reject a correct tenure-scoped claim.
            # Skip verification when tenure context is present — silence over
            # false positive.
            _sr_start = max(0, match.start() - 30)
            _sr_end = min(len(recap_text), match.end() + 80)
            _sr_context = recap_text[_sr_start:_sr_end].lower()
            if re.search(
                r'(?:under\s+current\s+ownership|current\s+owner|tenure)',
                _sr_context,
            ):
                continue

            fname_a = _resolve_display_name(fid_a, reverse_name_map)
            fname_b = _resolve_display_name(fid_b, reverse_name_map)
            actual_str = f"{actual_a_wins}-{actual_b_wins}"
            if actual_ties:
                actual_str += f"-{actual_ties}"
            claimed_str = f"{claimed_w}-{claimed_l}"
            if claimed_t:
                claimed_str += f"-{claimed_t}"
            failures.append(VerificationFailure(
                category="SERIES",
                severity="HARD",
                claim=f"Series record {claimed_str} ({fname_a} vs {fname_b})",
                evidence=(
                    f"Actual H2H record: {fname_a} {actual_str} {fname_b} "
                    f"({total} meetings)."
                ),
            ))

    return failures


# ── Category 5: Banned Phrase Detection ──────────────────────────────

# Exact phrases from the creative layer kill list — these should never
# appear in a recap. Case-insensitive matching.
_BANNED_PHRASES: tuple[str, ...] = (
    "the kind of chaos that makes fantasy football",
    "delivered a statement",
    "set a tone",
    "the irony here is painful",
    "peaked at exactly the right moment",
    "nightmare season continued",
    "self-sabotage",
    "stings when you lose by",
)

# Speculation patterns — the model attributing emotions or intent to
# franchise owners despite explicit hard rules against it.
_SPECULATION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r'\bkicking\s+(himself|herself|themselves)\b', re.IGNORECASE),
    re.compile(r'\bthat\s+stings\b', re.IGNORECASE),
    re.compile(r'\blooking\s+desperate\b', re.IGNORECASE),
    re.compile(r'\bprobably\s+regret', re.IGNORECASE),
    re.compile(r'\bhas\s+to\s+be\s+frustrating\b', re.IGNORECASE),
    re.compile(r'\bhad\s+to\s+(?:sting|hurt)\b', re.IGNORECASE),
)


def verify_banned_phrases(
    recap_text: str,
) -> list[VerificationFailure]:
    """Detect banned phrases and speculation patterns.

    These are SOFT failures — flagged for human review but do not
    auto-reject the draft. They indicate the model is ignoring
    explicit hard rules in the system prompt.
    """
    failures: list[VerificationFailure] = []
    text_lower = recap_text.lower()

    for phrase in _BANNED_PHRASES:
        if phrase.lower() in text_lower:
            failures.append(VerificationFailure(
                category="BANNED_PHRASE",
                severity="SOFT",
                claim=f"Contains banned phrase: \"{phrase}\"",
                evidence="This phrase is on the creative layer kill list.",
            ))

    for pattern in _SPECULATION_PATTERNS:
        match = pattern.search(recap_text)
        if match:
            failures.append(VerificationFailure(
                category="SPECULATION",
                severity="SOFT",
                claim=f"Speculation detected: \"{match.group(0)}\"",
                evidence=(
                    "The system prompt prohibits attributing emotions "
                    "or intent to franchise owners."
                ),
            ))

    return failures


# ── Category 6: Cross-Week Consistency (batch only) ──────────────────

@dataclass(frozen=True)
class _StreakClaim:
    """An extracted streak claim from a specific week's recap."""
    week: int
    franchise_id: str
    franchise_name: str
    is_losing: bool
    count: int


@dataclass(frozen=True)
class _SeriesClaim:
    """An extracted series record claim from a specific week's recap."""
    week: int
    fid_a: str
    fid_b: str
    name_a: str
    name_b: str
    wins: int
    losses: int


def _extract_streak_claims(
    narrative: str,
    week: int,
    reverse_name_map: dict[str, str],
) -> list[_StreakClaim]:
    """Extract streak count claims from a single week's recap."""
    claims: list[_StreakClaim] = []
    for match in _STREAK_PATTERN.finditer(narrative):
        count_str = match.group(1) or match.group(2)
        if not count_str:
            continue
        count = int(count_str)
        context = match.group(0).lower()
        is_losing = any(w in context for w in ("losing", "lost", "loss", "skid"))

        fid = _find_nearby_franchise(
            narrative, match.start(), reverse_name_map, window=150,
        )
        if fid is None:
            continue
        fname = _resolve_display_name(fid, reverse_name_map)
        claims.append(_StreakClaim(
            week=week, franchise_id=fid, franchise_name=fname,
            is_losing=is_losing, count=count,
        ))
    return claims


def _extract_series_claims(
    narrative: str,
    week: int,
    reverse_name_map: dict[str, str],
) -> list[_SeriesClaim]:
    """Extract series record claims from a single week's recap."""
    claims: list[_SeriesClaim] = []
    for match in _SERIES_RECORD_PATTERN.finditer(narrative):
        if match.group(1) is not None:
            w_str, l_str = match.group(1), match.group(2)
        else:
            w_str, l_str = match.group(4), match.group(5)
        try:
            wins, losses = int(w_str), int(l_str)
        except (ValueError, TypeError):
            continue

        fid_a, fid_b = _find_two_franchises(
            narrative, match.start(), reverse_name_map,
        )
        if fid_a is None or fid_b is None:
            continue

        # Normalize pair order for consistent comparison
        if fid_a > fid_b:
            fid_a, fid_b = fid_b, fid_a
            wins, losses = losses, wins

        name_a = _resolve_display_name(fid_a, reverse_name_map)
        name_b = _resolve_display_name(fid_b, reverse_name_map)
        claims.append(_SeriesClaim(
            week=week, fid_a=fid_a, fid_b=fid_b,
            name_a=name_a, name_b=name_b,
            wins=wins, losses=losses,
        ))
    return claims


def verify_cross_week_consistency(
    week_narratives: list[tuple[int, str]],
    reverse_name_map: dict[str, str],
) -> list[VerificationFailure]:
    """Check for contradictory facts across weeks in a season.

    This is a batch-only check — it requires all weeks' narratives.
    It catches cases like "15-game streak" in week 10 and "14 is the
    longest" in week 14.

    Checks:
    1. Streak claims: a franchise's claimed streak count for the same
       streak type should not decrease between weeks without a reset.
    2. Series records: an H2H record between the same two franchises
       should change by at most 1 game per week.
    """
    failures: list[VerificationFailure] = []

    # ── Streak consistency ──
    # Group streak claims by (franchise_id, is_losing)
    streak_claims: dict[tuple[str, bool], list[_StreakClaim]] = {}
    for week_idx, narrative in week_narratives:
        for claim in _extract_streak_claims(narrative, week_idx, reverse_name_map):
            key = (claim.franchise_id, claim.is_losing)
            streak_claims.setdefault(key, []).append(claim)

    for (fid, is_losing), claims in streak_claims.items():
        if len(claims) < 2:
            continue
        claims_sorted = sorted(claims, key=lambda c: c.week)
        for i in range(len(claims_sorted) - 1):
            prev = claims_sorted[i]
            curr = claims_sorted[i + 1]
            streak_type = "losing" if is_losing else "winning"
            # A streak count claimed in a later week should be >= the earlier
            # claim (it can only grow or reset). If it decreased, either the
            # earlier or later claim is wrong.
            # Allow resets (curr.count < prev.count is OK if the streak broke
            # and restarted). But flag if both are large — suggests the same
            # ongoing streak is being miscounted.
            if (curr.count < prev.count
                    and prev.count >= 3
                    and curr.count >= 3
                    and curr.week - prev.week <= 3):
                failures.append(VerificationFailure(
                    category="CONSISTENCY",
                    severity="HARD",
                    claim=(
                        f"{prev.franchise_name}: {streak_type} streak "
                        f"claimed as {prev.count} in Week {prev.week} "
                        f"but {curr.count} in Week {curr.week}"
                    ),
                    evidence=(
                        f"A {streak_type} streak cannot decrease from "
                        f"{prev.count} to {curr.count} over "
                        f"{curr.week - prev.week} week(s) without a reset."
                    ),
                ))

    # ── Series record consistency ──
    # Group series claims by normalized franchise pair
    series_claims: dict[tuple[str, str], list[_SeriesClaim]] = {}
    for week_idx, narrative in week_narratives:
        for sc in _extract_series_claims(narrative, week_idx, reverse_name_map):
            skey = (sc.fid_a, sc.fid_b)
            series_claims.setdefault(skey, []).append(sc)

    for (_sa, _sb), s_claims in series_claims.items():
        if len(s_claims) < 2:
            continue
        s_sorted = sorted(s_claims, key=lambda c: c.week)
        for i in range(len(s_sorted) - 1):
            s_prev = s_sorted[i]
            s_curr = s_sorted[i + 1]
            prev_total = s_prev.wins + s_prev.losses
            curr_total = s_curr.wins + s_curr.losses
            weeks_between = s_curr.week - s_prev.week
            # Between two weeks, teams can play at most once per week.
            # So the total meetings can increase by at most weeks_between.
            max_change = weeks_between
            if curr_total - prev_total > max_change:
                failures.append(VerificationFailure(
                    category="CONSISTENCY",
                    severity="HARD",
                    claim=(
                        f"{s_prev.name_a} vs {s_prev.name_b}: series record "
                        f"changed from {s_prev.wins}-{s_prev.losses} (Week {s_prev.week}) "
                        f"to {s_curr.wins}-{s_curr.losses} (Week {s_curr.week})"
                    ),
                    evidence=(
                        f"Total meetings jumped from {prev_total} to {curr_total} "
                        f"over {weeks_between} week(s) — impossible increase."
                    ),
                ))
            # Also check if wins or losses decreased (impossible)
            if s_curr.wins < s_prev.wins or s_curr.losses < s_prev.losses:
                failures.append(VerificationFailure(
                    category="CONSISTENCY",
                    severity="HARD",
                    claim=(
                        f"{s_prev.name_a} vs {s_prev.name_b}: series record "
                        f"changed from {s_prev.wins}-{s_prev.losses} (Week {s_prev.week}) "
                        f"to {s_curr.wins}-{s_curr.losses} (Week {s_curr.week})"
                    ),
                    evidence=(
                        "Wins or losses cannot decrease between weeks."
                    ),
                ))

    return failures


# ── Orchestrator ─────────────────────────────────────────────────────


def verify_recap_v1(
    recap_text: str,
    *,
    db_path: str,
    league_id: str,
    season: int,
    week: int,
) -> VerificationResult:
    """Run all V1 verification checks on a recap draft.

    This is the canonical entry point for the verification gate.
    Returns a VerificationResult indicating pass/fail with details.
    """
    narrative = _extract_shareable_recap(recap_text)
    if not narrative:
        return VerificationResult(
            passed=True,
            hard_failures=(),
            soft_failures=(),
            checks_run=0,
        )

    season_matchups = _load_season_matchups(db_path, league_id, season)
    name_map = _load_franchise_names(db_path, league_id, season)
    reverse_name_map = _build_reverse_name_map(name_map)

    all_failures: list[VerificationFailure] = []
    checks_run = 0

    # Category 1: Score verification
    checks_run += 1
    all_failures.extend(verify_scores(
        narrative, season_matchups, week, reverse_name_map,
    ))

    # Category 2: Superlative verification
    checks_run += 1
    all_matchups: list[_MatchupFact] | None = None
    alltime_player_high: float | None = None
    if _ALLTIME_PATTERN.search(narrative):
        all_matchups = _load_all_matchups(db_path, league_id)
        alltime_player_high = _load_alltime_player_high(db_path, league_id)

    season_player_high: float | None = None
    if _SEASON_HIGH_PATTERN.search(narrative):
        season_player_high = _load_player_season_high(db_path, league_id, season)

    all_failures.extend(verify_superlatives(
        narrative, season_matchups, all_matchups, season,
        season_player_high, alltime_player_high,
    ))

    # Category 3: Streak verification
    checks_run += 1
    all_failures.extend(verify_streaks(
        narrative, season_matchups, week, reverse_name_map,
    ))

    # Category 4: Series record verification
    checks_run += 1
    if _SERIES_RECORD_PATTERN.search(narrative):
        if all_matchups is None:
            all_matchups = _load_all_matchups(db_path, league_id)
        all_failures.extend(verify_series_records(
            narrative, all_matchups or [], reverse_name_map,
        ))

    # Category 5: Banned phrase / speculation detection (SOFT)
    checks_run += 1
    all_failures.extend(verify_banned_phrases(narrative))

    hard = tuple(f for f in all_failures if f.severity == "HARD")
    soft = tuple(f for f in all_failures if f.severity == "SOFT")

    return VerificationResult(
        passed=len(hard) == 0,
        hard_failures=hard,
        soft_failures=soft,
        checks_run=checks_run,
    )
