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
    through_week: int | None = None,
) -> float | None:
    """Return the highest individual STARTER score of the season.

    Bench scores are excluded — the convention "highest individual score
    of the season" refers to scores from players who were actually in
    the starting lineup, not bench points that didn't count toward team
    totals.

    If through_week is provided, only considers scores from weeks
    <= through_week. This prevents future-data false positives when
    verifying an earlier week.
    """
    with DatabaseSession(db_path) as con:
        if through_week is not None:
            row = con.execute(
                """SELECT MAX(CAST(json_extract(payload_json, '$.score') AS REAL))
                   FROM v_canonical_best_events
                   WHERE league_id = ? AND season = ?
                     AND event_type = 'WEEKLY_PLAYER_SCORE'
                     AND CAST(json_extract(payload_json, '$.is_starter') AS INTEGER) = 1
                     AND CAST(json_extract(payload_json, '$.week') AS INTEGER) <= ?""",
                (str(league_id), int(season), int(through_week)),
            ).fetchone()
        else:
            row = con.execute(
                """SELECT MAX(CAST(json_extract(payload_json, '$.score') AS REAL))
                   FROM v_canonical_best_events
                   WHERE league_id = ? AND season = ?
                     AND event_type = 'WEEKLY_PLAYER_SCORE'
                     AND CAST(json_extract(payload_json, '$.is_starter') AS INTEGER) = 1""",
                (str(league_id), int(season)),
            ).fetchone()
    if row and row[0] is not None:
        return float(row[0])
    return None


def _load_alltime_player_high(
    db_path: str,
    league_id: str,
) -> float | None:
    """Return the highest individual STARTER score across all seasons."""
    with DatabaseSession(db_path) as con:
        row = con.execute(
            """SELECT MAX(CAST(json_extract(payload_json, '$.score') AS REAL))
               FROM v_canonical_best_events
               WHERE league_id = ?
                 AND event_type = 'WEEKLY_PLAYER_SCORE'
                 AND CAST(json_extract(payload_json, '$.is_starter') AS INTEGER) = 1""",
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

    Also adds first-word aliases (5+ chars, unique across all franchises)
    to handle short-form references in recap prose. The model often writes
    "Eddie snapped his streak" or "Brandon bounced back" rather than the
    full franchise name. Without aliases, _find_nearby_franchise falls
    back to AFTER-the-position matching and may attribute claims to the
    wrong team.
    """
    reverse: dict[str, str] = {}

    # Pass 1: Full franchise names (exact case and lowercase)
    for fid, name in name_map.items():
        normalized = _normalize_apostrophes(name)
        reverse[normalized] = fid
        reverse[normalized.lower()] = fid

    # Pass 2: First-word aliases for short-form references.
    # Only add if 5+ chars (avoids substring matches like "ben" in "bench")
    # and unique across franchises (avoids ambiguity).
    _first_word_to_fids: dict[str, set[str]] = {}
    _stop_words = {"the", "and", "team", "club", "fantasy"}
    for fid, name in name_map.items():
        normalized = _normalize_apostrophes(name)
        words = re.findall(r"\w+", normalized)
        if not words:
            continue
        first_word = words[0].lower()
        if len(first_word) < 5:
            continue
        if first_word in _stop_words:
            continue
        _first_word_to_fids.setdefault(first_word, set()).add(fid)

    for alias, fids in _first_word_to_fids.items():
        if len(fids) != 1:
            continue
        fid = next(iter(fids))
        if alias not in reverse:
            reverse[alias] = fid

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

    # Also extract integer score positions (e.g., "115" in "115-107.50").
    # Models sometimes write team scores as integers when the canonical
    # score happens to be a whole number. These don't get verified
    # individually but they help complete pair detection.
    _INT_SCORE_PATTERN = re.compile(r'(?<![\d.])(\d{2,3})(?![\d.])')
    int_score_positions: list[tuple[int, float]] = []
    for match in _INT_SCORE_PATTERN.finditer(recap_text):
        try:
            val = float(match.group(1))
        except ValueError:
            continue
        if 40.0 <= val <= 250.0:
            int_score_positions.append((match.start(), val))

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

    # Pass 1b: Integer-decimal pair detection (e.g., "115-107.50").
    # Mark a decimal score as pair-verified if a nearby integer score
    # matches the other half of a canonical matchup pair.
    for i, (pos_dec, val_dec) in enumerate(score_positions):
        if i in pair_verified:
            continue
        for pos_int, val_int in int_score_positions:
            if abs(pos_int - pos_dec) > _PAIR_WINDOW:
                continue
            for w_score, l_score in week_matchup_pairs:
                if ((abs(val_dec - w_score) <= 0.01 and abs(val_int - l_score) <= 0.5) or
                        (abs(val_dec - l_score) <= 0.01 and abs(val_int - w_score) <= 0.5)):
                    pair_verified.add(i)
                    break

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

        # Check whether the attributed franchise name actually appears
        # BEFORE the score (in which case the attribution is strong) or
        # only AFTER (in which case _find_nearby_franchise fell back and
        # the attribution is weak — the score may belong to a team named
        # with an alias that isn't in the canonical name map).
        _before_start = max(0, pos - 150)
        _before_text_norm = _normalize_apostrophes(
            recap_text[_before_start:pos]
        ).lower()
        _attributed_name_lc = None
        for _n, _f in reverse_name_map.items():
            if _f == franchise_id and _n.islower():
                _attributed_name_lc = _n
                break
        _attribution_is_before = (
            _attributed_name_lc is not None
            and _attributed_name_lc in _before_text_norm
        )

        # Weak attribution + score is a valid canonical score for the week:
        # the model likely wrote "[alias] beat [attributed] <score>" where
        # [alias] isn't in the name map (e.g. "The Playmakers" vs
        # "Paradis' Playmakers"). Skip the flag — we cannot reliably
        # determine the scorer.
        if not _attribution_is_before:
            continue

        # Strong attribution (name appears before the score) but the score
        # is wrong. Before flagging, still check if a DIFFERENT franchise
        # preceding in the same sentence owns this score — handles
        # "KP demolished Purple Haze 198.80" where Purple Haze is nearer
        # but KP owns the score.
        _sentence_start = max(0, pos - 80)
        _sentence_raw = recap_text[_sentence_start:pos]
        for _sep in (".", "\n"):
            _sep_idx = _sentence_raw.rfind(_sep)
            if _sep_idx >= 0:
                _sentence_raw = _sentence_raw[_sep_idx + 1:]
        _sentence_text = _normalize_apostrophes(_sentence_raw).lower()
        _any_preceding_match = False
        for _fname_lc, _fid in reverse_name_map.items():
            if not _fname_lc.islower():
                continue
            if _fid == franchise_id:
                continue
            if _fname_lc not in _sentence_text:
                continue
            _cs = canonical_scores.get(_fid)
            if _cs is not None and abs(mentioned_score - _cs) <= 0.01:
                _any_preceding_match = True
                break
        if _any_preceding_match:
            continue  # Score matches a franchise that precedes it in same sentence

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

# Temporal-displacement qualifiers. When one of these appears in the
# ~40 chars preceding a "season high" / "all-time record" keyword, the
# model's claim is about a pre-existing record (e.g. "breaks the
# previous season high of 48.10" — the 48.10 is the *old* high being
# broken, not the current season max). This verifier does not have
# week-filtered superlative data, so it cannot evaluate such claims;
# silence over speculation.
_PREVIOUS_QUALIFIER_PATTERN = re.compile(
    r'\b(?:previous|prior|former|past)\b', re.IGNORECASE,
)


def _has_previous_qualifier(
    text: str, pos: int, *, lookback: int = 40,
) -> bool:
    """Return True if a temporal qualifier precedes pos within lookback."""
    start = max(0, pos - lookback)
    return bool(_PREVIOUS_QUALIFIER_PATTERN.search(text[start:pos]))


# After "all-time record" / "all-time high", a following integer count
# (e.g. "of 15" meaning "15 games") is a non-scoring claim. Scoring
# values in this league always use XX.XX format, so an integer in this
# position indicates the claim refers to a count, not a score.
_INTEGER_OBJECT_PATTERN = re.compile(r'\s*of\s+\d+\b(?!\s*\.\s*\d)')


# ── V4: ordinal-qualifier guard for SUPERLATIVE ─────────────────────
# An ordinal prefix immediately before "highest"/"lowest" negates the
# superlative. "His second-lowest output of the season" is a claim
# about Brandon's #2-worst score, not the season minimum. The
# _SEASON_{HIGH,LOW}_PATTERN matches anchor at "highest"/"lowest" and
# do not consume the preceding "second-"/"third-"/"Nth-". Without a
# guard, the pattern fires and _extract_nearby_score pulls an unrelated
# score from the surrounding context.
#
# Shape mirrors V1: skip when an ordinal qualifier appears immediately
# before the match, joined by hyphen or space. Personal-scoped
# "Nth-lowest" data is not available here, so silence over speculation.
_ORDINAL_QUALIFIER_PATTERN = re.compile(
    r'\b(?:second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|'
    r'\d+(?:st|nd|rd|th))[- ]+$',
    re.IGNORECASE,
)


def _has_ordinal_qualifier(
    text: str, pos: int, *, lookback: int = 15,
) -> bool:
    """Return True if an ordinal prefix ('second-', 'third-', 'Nth-')
    immediately precedes pos within lookback chars."""
    start = max(0, pos - lookback)
    return bool(_ORDINAL_QUALIFIER_PATTERN.search(text[start:pos]))


# ── V5: possessive / personal-scope guard for SUPERLATIVE ───────────
# A possessive pronoun ("his", "her", "their", "its") or a personal-
# scope marker ("in N tries", "in N attempts", "in N games") scopes
# the superlative to a person/team, not the league. Example prose:
#   "Brandon's 116.75 — easily his highest output in nine tries this
#   season."
# The superlative is Brandon's personal best, not a league record; the
# verifier compares against the league-wide max and misattributes.
# Per-franchise/per-player historical bests are not available to this
# verifier, so skip the check — silence over speculation.
_POSSESSIVE_PRONOUN_PATTERN = re.compile(
    r'\b(?:his|her|their|its)\b', re.IGNORECASE,
)
_PERSONAL_SCOPE_PATTERN = re.compile(
    r'\bin\s+\w+\s+(?:tries|attempts|games|outings|starts|appearances)\b',
    re.IGNORECASE,
)


def _has_possessive_scope(
    text: str, match_start: int, match_end: int, *, lookback: int = 30,
) -> bool:
    """Return True if the superlative at [match_start:match_end] is
    scoped to an individual/team via a preceding possessive pronoun or
    a personal-scope marker within the match span."""
    start = max(0, match_start - lookback)
    if _POSSESSIVE_PRONOUN_PATTERN.search(text[start:match_start]):
        return True
    # Personal-scope marker may be consumed by the match itself, e.g.
    # "highest output in nine tries this season" — _SEASON_HIGH_PATTERN's
    # [^.]{0,40} filler captures "output in nine tries".
    if _PERSONAL_SCOPE_PATTERN.search(text[match_start:match_end]):
        return True
    return False


# ── V6: frequency-marker guard for SUPERLATIVE (all-time loop) ──────
# "Nth time in league history" is an event-frequency construction, not
# a scoring record. Example prose:
#   "marking just the 323rd time in league history a starter has been
#   completely shut out. Pat stayed perfect with a 125.30-111.95 win"
# _ALLTIME_PATTERN fires on "league history" and
# _extract_nearby_score picks up the team score 125.30 from an
# unrelated adjacent clause. The existing series/rivalry and
# auction/investment guards don't cover occurrence-count framing.
#
# Covered constructions: "Nth time", "only/first/last/sole/lone time",
# "few times", "handful of times". Bare frequency adjectives like
# "rare" are intentionally excluded — they co-occur with legitimate
# scoring claims ("a rare feat in league history" describing the
# 192.15 score) and would over-skip.
_FREQUENCY_MARKER_PATTERN = re.compile(
    r'\b(?:\d+(?:st|nd|rd|th)\s+time|'
    r'(?:only|first|last|second|third|fourth|fifth|sole|lone)\s+time|'
    r'few\s+times|handful\s+of\s+times)\b',
    re.IGNORECASE,
)


def _has_frequency_marker(
    text: str, pos: int, *, lookback: int = 40,
) -> bool:
    """Return True if a frequency-count marker ('Nth time', 'only
    time', 'first time', 'few times') precedes pos within lookback."""
    start = max(0, pos - lookback)
    return bool(_FREQUENCY_MARKER_PATTERN.search(text[start:pos]))


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
        # Fix V1: "previous/prior season high of X" is a claim about the
        # pre-existing record, not the current max. Skip — week-filtered
        # superlative data isn't available here, so we can't evaluate it.
        if _has_previous_qualifier(recap_text, match.start()):
            continue

        # Fix V4: ordinal-qualifier prefix ("second-highest", "3rd-highest")
        # negates the superlative. The pattern anchors at "highest" and
        # does not consume the preceding ordinal, so a bare match here
        # would compare an unrelated nearby score against the league max.
        if _has_ordinal_qualifier(recap_text, match.start()):
            continue

        # Fix V5: possessive pronoun or personal-scope marker scopes the
        # superlative to an individual/team, not the league. We lack
        # per-franchise/per-player history data, so skip.
        if _has_possessive_scope(recap_text, match.start(), match.end()):
            continue

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
        # Fix V1 (parity with season-high loop): "previous/prior season
        # low of X" is a pre-existing record claim — week-filtered data
        # isn't available, skip.
        if _has_previous_qualifier(recap_text, match.start()):
            continue

        # Fix V4: "his second-lowest output of the season" — the ordinal
        # prefix negates the superlative. The pattern anchors at
        # "lowest" and does not consume "second-". Without this guard,
        # _extract_nearby_score pulls an unrelated score and flags.
        if _has_ordinal_qualifier(recap_text, match.start()):
            continue

        # Fix V5 (parity with season-high loop): possessive-scoped lows
        # are personal, not league-wide. Skip.
        if _has_possessive_scope(recap_text, match.start(), match.end()):
            continue

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
        # Bug fix 1: "all-time" in series context (e.g. "all-time series
        # dominance to 21-7") is about H2H scope, not a scoring record.
        _at_start = max(0, match.start() - 10)
        _at_end = min(len(recap_text), match.end() + 40)
        _at_context = recap_text[_at_start:_at_end].lower()
        if re.search(
            r'all[- ]?time\s+(?:series|meetings?|edge|dominance|lead|head|h2h|rivalry)',
            _at_context,
        ):
            continue

        # Bug fix 2: "in league history" / "all-time bargains" referring
        # to AUCTION INVESTMENT context, not scoring records.  Examples:
        #   "the most productive auction pick in league history"
        #   "one of the league's all-time bargains at 1,088 points per dollar"
        #   "auction investment in league history"
        # The surrounding sentence will mention auction/investment/pick
        # /dollar/draft. Check a wider window.
        _auction_start = max(0, match.start() - 80)
        _auction_end = min(len(recap_text), match.end() + 80)
        _auction_context = recap_text[_auction_start:_auction_end].lower()
        if re.search(
            r'(?:auction|investment|points\s+per\s+dollar|bargain|'
            r'draft\s+pick|\$\d+\s+(?:spent|investment|pickup|pick)|'
            r'most\s+productive\s+(?:auction|draft))',
            _auction_context,
        ):
            continue

        # Fix V1: "previous/prior all-time record of X" is a pre-existing
        # record claim — skip, same reasoning as the season-high loop.
        if _has_previous_qualifier(recap_text, match.start()):
            continue

        # Fix V2: "all-time record of <integer>" is a count claim (games,
        # occurrences), not a scoring record. Scoring numbers in this
        # league always use XX.XX format. Example: "the streak marches
        # toward the all-time record of 15" — 15 is games, not a score.
        if _INTEGER_OBJECT_PATTERN.match(recap_text, match.end()):
            continue

        # Fix V6: "Nth time in league history" / "only time in league
        # history" is an event-frequency construction, not a scoring
        # record. Example: "marking just the 323rd time in league
        # history a starter has been completely shut out. Pat stayed
        # perfect with a 125.30-111.95 win" — 125.30 is an unrelated
        # adjacent score. Skip the check.
        if _has_frequency_marker(recap_text, match.start()):
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

# Possessive-object construction: "<Franchise>'s [N-game]? losing streak".
# When the streak owner is explicitly named as the possessor of the streak
# in the snap clause (e.g. "snapped Brandon's 11-game losing streak"), the
# owner is unambiguous — no attribution heuristic needed. The capture group
# yields the possessor name, which is looked up directly against
# reverse_name_map. Case-sensitive leading capital requirement filters out
# pronoun possessors ("his", "their", "the") that shouldn't be treated as
# franchise references. See OBSERVATIONS_2026_04_14 backlog B.
_POSSESSIVE_OBJECT_STREAK = re.compile(
    r'\b([A-Z][\w&]*(?:\s+[A-Z&][\w&]*)*)'
    r'(?:\'s|\u2019s)\s+'
    r'(?:\d{1,2}[-\s]game\s+)?'
    r'losing\s+streak',
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

        # Skip historical references — "11-game win streak ended last
        # season", "previous season", "from 2022", etc. The model is
        # citing a past streak, not making a current-season claim.
        _hist_start = max(0, match.start() - 80)
        _hist_end = min(len(recap_text), match.end() + 80)
        _hist_context = recap_text[_hist_start:_hist_end].lower()
        if re.search(
            r'(?:last\s+season|previous\s+season|prior\s+season|'
            r'last\s+year|prior\s+year|ended\s+(?:last|in\s+\d{4})|'
            r'from\s+\d{4}|in\s+\d{4}|back\s+in\s+\d{4}|'
            r'his\s+career|career[- ](?:high|long|best))',
            _hist_context,
        ):
            continue

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

        # Skip historical references same as explicit count check
        _hist_start = max(0, match.start() - 80)
        _hist_end = min(len(recap_text), match.end() + 80)
        _hist_context = recap_text[_hist_start:_hist_end].lower()
        if re.search(
            r'(?:last\s+season|previous\s+season|prior\s+season|'
            r'last\s+year|prior\s+year|ended\s+(?:last|in\s+\d{4})|'
            r'from\s+\d{4}|in\s+\d{4}|back\s+in\s+\d{4})',
            _hist_context,
        ):
            continue

        # Possessive-object attribution: if the match span contains
        # "<Franchise>'s [N-game]? losing streak", the streak owner is
        # explicitly named in the prose — use that directly rather than
        # falling through to the proximity heuristic, which can misattribute
        # when the snap-verb subject has a short first name not in the
        # alias map (e.g. "Ben snapped Brandon's losing streak" — pass 1
        # of _find_nearby_franchise finds no "ben" alias, pass 2 picks up
        # "brandon" inside the snap clause, and the failure cites Brandon
        # as the snap-claim subject rather than the streak owner). See
        # OBSERVATIONS_2026_04_14 backlog B, row 20 (2025 w11 attempt 1).
        _match_text = recap_text[match.start():match.end()]
        _possessive = _POSSESSIVE_OBJECT_STREAK.search(_match_text)
        if _possessive:
            _possessor_key = (
                _normalize_apostrophes(_possessive.group(1)).lower().strip()
            )
            _possessor_fid = reverse_name_map.get(_possessor_key)
            if _possessor_fid is None:
                # Unmappable possessor (short first name, franchise not
                # registered, or off-league reference). Silence over
                # misattribution: do NOT fall through to the heuristic.
                continue
            _pre_streak = pre_week_streaks.get(_possessor_fid, 0)
            _current_streak = actual_streaks.get(_possessor_fid, 0)
            _fname = _resolve_display_name(_possessor_fid, reverse_name_map)
            if _pre_streak >= 0:
                failures.append(VerificationFailure(
                    category="STREAK",
                    severity="HARD",
                    claim=f"{_fname}'s losing streak was snapped",
                    evidence=(
                        f"{_fname} had no losing streak entering Week "
                        f"{week} (pre-week streak: {_pre_streak})."
                    ),
                ))
            elif _current_streak < 0:
                failures.append(VerificationFailure(
                    category="STREAK",
                    severity="HARD",
                    claim=f"{_fname}'s losing streak was snapped",
                    evidence=(
                        f"{_fname} lost in Week {week} — losing streak "
                        f"extended to {abs(_current_streak)}, not snapped."
                    ),
                ))
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

    # Pre-compute all H2H records: (frozenset({fid_a, fid_b})) -> (a_wins, b_wins, fid_a)
    h2h_records: dict[frozenset[str], tuple[int, int, str, str]] = {}
    for m in all_matchups:
        pair_key = frozenset({m.winner_id, m.loser_id})
        if pair_key not in h2h_records:
            h2h_records[pair_key] = (0, 0, m.winner_id, m.loser_id)
        w, ls, fa, fb = h2h_records[pair_key]
        if m.winner_id == fa:
            h2h_records[pair_key] = (w + 1, ls, fa, fb)
        else:
            h2h_records[pair_key] = (w, ls + 1, fa, fb)

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

        # Tenure-scoped records ("4-0 under current ownership") are a
        # subset of all-time meetings — skip verification when tenure
        # context is present.
        _sr_start = max(0, match.start() - 30)
        _sr_end = min(len(recap_text), match.end() + 80)
        _sr_context = recap_text[_sr_start:_sr_end].lower()
        if re.search(
            r'(?:under\s+current\s+ownership|current\s+owner|tenure)',
            _sr_context,
        ):
            continue

        # Find all franchises that appear in a wider window around the
        # record. The series record could belong to any pair of
        # franchises mentioned in the surrounding paragraph — not just
        # the two closest.
        _ctx_start = max(0, match.start() - 300)
        _ctx_end = min(len(recap_text), match.end() + 100)
        _context = _normalize_apostrophes(recap_text[_ctx_start:_ctx_end]).lower()

        nearby_fids: set[str] = set()
        for name, fid in reverse_name_map.items():
            if not name.islower():
                continue
            if name in _context:
                nearby_fids.add(fid)

        if len(nearby_fids) < 2:
            continue

        # Check if the claimed record matches ANY pair of nearby franchises
        matched = False
        for fid_a in nearby_fids:
            for fid_b in nearby_fids:
                if fid_a >= fid_b:
                    continue
                pair_key = frozenset({fid_a, fid_b})
                if pair_key not in h2h_records:
                    continue
                a_wins, b_wins, _fa, _fb = h2h_records[pair_key]
                if (
                    (claimed_w == a_wins and claimed_l == b_wins)
                    or (claimed_w == b_wins and claimed_l == a_wins)
                ):
                    matched = True
                    break
            if matched:
                break

        if matched:
            continue

        # No nearby pair has this exact record. Find the closest pair to
        # report in the failure message.
        fid_a, fid_b = _find_two_franchises(
            recap_text, match.start(), reverse_name_map,
        )
        if fid_a is None or fid_b is None:
            continue
        pair_key = frozenset({fid_a, fid_b})
        if pair_key not in h2h_records:
            continue
        a_wins, b_wins, fa, fb = h2h_records[pair_key]
        total = a_wins + b_wins
        if total == 0:
            continue

        fname_a = _resolve_display_name(fa, reverse_name_map)
        fname_b = _resolve_display_name(fb, reverse_name_map)
        actual_str = f"{a_wins}-{b_wins}"
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


# ── Category 6: Player Score Verification ────────────────────────────

# Player score pattern: 1-2 digit scores with 2 decimal places
_PLAYER_SCORE_PATTERN = re.compile(r'(\d{1,2}\.\d{2})')


def _load_week_player_scores(
    db_path: str, league_id: str, season: int, week: int,
) -> dict[str, float]:
    """Load player_id -> score for all players in a given week."""
    scores: dict[str, float] = {}
    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT json_extract(payload_json, '$.player_id'),
                      CAST(json_extract(payload_json, '$.score') AS REAL)
               FROM v_canonical_best_events
               WHERE league_id = ? AND season = ?
                 AND event_type = 'WEEKLY_PLAYER_SCORE'
                 AND CAST(json_extract(payload_json, '$.week') AS INTEGER) = ?""",
            (str(league_id), int(season), int(week)),
        ).fetchall()
    for row in rows:
        if row[0] and row[1] is not None:
            scores[str(row[0])] = float(row[1])
    return scores


def _load_player_all_season_scores(
    db_path: str, league_id: str, season: int, through_week: int,
) -> dict[str, set[float]]:
    """Load player_id -> set of all scores in season through given week.

    Used to validate callbacks: if the model writes "Goff's 47.30" in
    week 7 referencing his week 2 score, the verifier should not flag it.
    """
    scores: dict[str, set[float]] = {}
    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT json_extract(payload_json, '$.player_id'),
                      CAST(json_extract(payload_json, '$.score') AS REAL)
               FROM v_canonical_best_events
               WHERE league_id = ? AND season = ?
                 AND event_type = 'WEEKLY_PLAYER_SCORE'
                 AND CAST(json_extract(payload_json, '$.week') AS INTEGER) <= ?""",
            (str(league_id), int(season), int(through_week)),
        ).fetchall()
    for row in rows:
        if row[0] and row[1] is not None:
            pid = str(row[0])
            scores.setdefault(pid, set()).add(round(float(row[1]), 2))
    return scores


def _build_player_display_to_score(
    player_scores: dict[str, float],
    player_name_map: dict[str, str],
) -> dict[str, float]:
    """Build 'first last' (lowered) -> score lookup.

    Converts 'Last, First' from name map to 'first last' for matching
    against recap prose where the model writes 'Josh Allen' not 'Allen, Josh'.
    """
    lookup: dict[str, float] = {}
    for pid, score in player_scores.items():
        display = player_name_map.get(pid)
        if not display:
            continue
        # Convert "Last, First" -> "first last"
        if ", " in display:
            parts = display.split(", ", 1)
            first_last = f"{parts[1]} {parts[0]}".strip().lower()
            # Also store "last" alone for single-name matches
            lookup[first_last] = score
            # Handle suffixes: "Penix Jr., Michael" -> "michael penix jr."
            # Already handled by the split above
        else:
            lookup[display.strip().lower()] = score
    return lookup


def _load_player_name_map_for_verify(
    db_path: str, league_id: str,
) -> dict[str, str]:
    """Load player_id -> display name map for verification."""
    name_map: dict[str, str] = {}
    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT player_id, name FROM player_directory
               WHERE league_id = ? ORDER BY season DESC""",
            (str(league_id),),
        ).fetchall()
    for row in rows:
        pid = str(row[0]).strip()
        name = str(row[1]).strip() if row[1] else ""
        if pid and name and pid not in name_map:
            name_map[pid] = name
    return name_map


def verify_player_scores(
    recap_text: str,
    *,
    db_path: str,
    league_id: str,
    season: int,
    week: int,
) -> list[VerificationFailure]:
    """Verify player scores attributed in recap text against canonical data.

    Searches for player names (from the player directory) in the recap,
    finds TIGHTLY attributed scores (within 25 chars, no sentence break,
    no 'by' separator), and checks them against the actual
    WEEKLY_PLAYER_SCORE for that player in that week.
    """
    failures: list[VerificationFailure] = []

    player_scores = _load_week_player_scores(db_path, league_id, season, week)
    if not player_scores:
        return []

    player_name_map = _load_player_name_map_for_verify(db_path, league_id)
    display_to_score = _build_player_display_to_score(player_scores, player_name_map)

    if not display_to_score:
        return []

    # Build display_name -> player_id map for callback verification
    display_to_pid: dict[str, str] = {}
    for pid, display in player_name_map.items():
        if not display:
            continue
        if ", " in display:
            parts = display.split(", ", 1)
            first_last = f"{parts[1]} {parts[0]}".strip().lower()
            if first_last not in display_to_pid:
                display_to_pid[first_last] = pid
        else:
            key = display.strip().lower()
            if key not in display_to_pid:
                display_to_pid[key] = pid

    # Load all-season scores per player (for callback verification —
    # the model can legitimately reference a player's prior-week score
    # like "Goff's 47.30 from Week 2").
    all_season_scores = _load_player_all_season_scores(
        db_path, league_id, season, through_week=week,
    )

    # Collect matchup scores and margins to exclude from player verification.
    # A number like "40.85" near a player name might be the matchup margin,
    # not a claim that the player scored 40.85. Exclude all matchup-level
    # numbers from player score flagging to eliminate this class of false
    # positive.
    matchup_numbers: set[float] = set()
    try:
        week_matchups_list = _load_season_matchups(db_path, league_id, season)
        for m in week_matchups_list:
            if m.week != week:
                continue
            matchup_numbers.add(round(m.winner_score, 2))
            matchup_numbers.add(round(m.loser_score, 2))
            matchup_numbers.add(round(abs(m.winner_score - m.loser_score), 2))
    except Exception:
        pass

    text_lower = recap_text.lower()

    # For each known player name found in the recap, check nearby scores
    checked: set[tuple[str, float]] = set()  # avoid duplicate checks

    for display_name, actual_score in display_to_score.items():
        # Skip very short names (5 chars or less) to avoid false matches
        if len(display_name) <= 5:
            continue

        idx = text_lower.find(display_name)
        while idx >= 0:
            # Look for scores within 25 chars after the name (tight window).
            # Models attribute player scores with patterns like "'s 24.50",
            # "had 24.50", "scored 24.50", "posted 24.50" — all <20 chars.
            name_end = idx + len(display_name)
            window_start = name_end
            window_end = min(len(recap_text), name_end + 25)
            window = recap_text[window_start:window_end]

            for m in _PLAYER_SCORE_PATTERN.finditer(window):
                try:
                    claimed_score = float(m.group(1))
                except ValueError:
                    continue

                # Detect a leading minus sign immediately before the matched
                # number. The regex captures only digits.dot.digits but
                # negative scores ("-0.30" for defensive penalties) appear
                # in actual prose. Without this check, the verifier extracts
                # "0.30" and flags it as not matching canonical "-0.30".
                score_abs_pos = window_start + m.start()
                if score_abs_pos > 0 and recap_text[score_abs_pos - 1] == "-":
                    # Make sure this is a unary minus, not a hyphen between
                    # words/scores. Look at the char before the minus.
                    if score_abs_pos < 2 or recap_text[score_abs_pos - 2] in (
                        " ", "(", "\n", "\t",
                    ):
                        claimed_score = -claimed_score

                # Guard: skip if a sentence break or clause-break separator
                # appears between the name and the score. These indicate
                # the score is about something else (matchup margin,
                # team total, bench total, etc.), not the player.
                # " but " catches the pattern "got 20.30 from X but left
                # 53.90 on the bench" where 53.90 is a bench total.
                between = window[:m.start()]
                if (
                    "." in between
                    or " by " in between
                    or "\n" in between
                    or " but " in between
                ):
                    continue

                # Guard: skip scores that match matchup numbers (team
                # totals or margins). The model isn't claiming the player
                # scored that — it's just proximity.
                if round(claimed_score, 2) in matchup_numbers:
                    continue

                # Skip if we already checked this name+score pair
                check_key = (display_name, claimed_score)
                if check_key in checked:
                    continue
                checked.add(check_key)

                # Skip scores that look like dollar amounts (preceded by $)
                if score_abs_pos > 0 and recap_text[score_abs_pos - 1] == "$":
                    continue

                # Check if the claimed score matches the actual score
                if abs(claimed_score - actual_score) > 0.01:
                    # Doesn't match this week's score. Check if it matches
                    # any other player's score this week (proximity false
                    # positive from adjacent player mentions) OR any of
                    # this player's prior-week scores in the season
                    # (legitimate callback like "Goff's 47.30 from Week 2").
                    valid_scores = set(
                        round(s, 2) for s in player_scores.values()
                    )
                    if round(claimed_score, 2) in valid_scores:
                        continue

                    # Callback check: does this player have this score
                    # in any prior week of the current season?
                    pid = display_to_pid.get(display_name)
                    if pid and pid in all_season_scores:
                        if round(claimed_score, 2) in all_season_scores[pid]:
                            continue  # legitimate callback

                    orig_display = display_name.title()
                    failures.append(VerificationFailure(
                        category="PLAYER_SCORE",
                        severity="HARD",
                        claim=(
                            f"Player score {claimed_score:.2f} "
                            f"attributed to {orig_display}"
                        ),
                        evidence=(
                            f"No player scored {claimed_score:.2f} in "
                            f"Week {week}. {orig_display}'s actual "
                            f"score: {actual_score:.2f}."
                        ),
                    ))

            # Find next occurrence of this name
            idx = text_lower.find(display_name, idx + 1)

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
        season_player_high = _load_player_season_high(
            db_path, league_id, season, through_week=week,
        )

    # Filter season_matchups to only weeks <= current week. Using future
    # weeks to invalidate a "season high" claim is a false positive —
    # the model only knows about weeks that have happened.
    season_matchups_through_week = [
        m for m in season_matchups if m.week <= week
    ]

    all_failures.extend(verify_superlatives(
        narrative, season_matchups_through_week, all_matchups, season,
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

    # Category 6: Player score verification (HARD)
    checks_run += 1
    all_failures.extend(verify_player_scores(
        narrative,
        db_path=db_path,
        league_id=league_id,
        season=season,
        week=week,
    ))

    hard = tuple(f for f in all_failures if f.severity == "HARD")
    soft = tuple(f for f in all_failures if f.severity == "SOFT")

    return VerificationResult(
        passed=len(hard) == 0,
        hard_failures=hard,
        soft_failures=soft,
        checks_run=checks_run,
    )
