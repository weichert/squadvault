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
4. SERIES — head-to-head series records vs computed H2H history
5. BANNED_PHRASE — cliché / speculation detection (SOFT)
6. PLAYER_SCORE — individual player scores vs canonical WEEKLY_PLAYER_SCORE
7. PLAYER_FRANCHISE — player-franchise attribution vs canonical roster
8. FAAB_CLAIM — FAAB dollar amounts vs canonical WAIVER_BID_AWARDED

Categories 1–4, 6–8 are HARD. Category 5 is SOFT. A hard failure means
the recap contains a provably false factual claim.
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
    category: str     # "SCORE", "SUPERLATIVE", "STREAK", etc.
    severity: str     # "HARD" or "SOFT"
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


def _load_franchise_owner_names(
    db_path: str,
    league_id: str,
    season: int,
) -> dict[str, str]:
    """Load franchise_id -> owner_name map for the season.

    Owner names power the "short-form-by-owner" alias pass in
    _build_reverse_name_map (e.g. recognizing "Michele" and "KP" as
    references to Italian Cavallini and Paradis' Playmakers when the
    model writes in league-insider voice). Returns only non-empty
    owner names; missing entries are silently omitted.
    """
    owner_map: dict[str, str] = {}
    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT franchise_id, owner_name
               FROM franchise_directory
               WHERE league_id = ? AND season = ?""",
            (str(league_id), int(season)),
        ).fetchall()
    for row in rows:
        if row[0] and row[1] and str(row[1]).strip():
            owner_map[str(row[0]).strip()] = str(row[1]).strip()
    return owner_map


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


def _build_reverse_name_map(
    name_map: dict[str, str],
    owner_map: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build name -> franchise_id reverse lookup.

    Adds both exact-case and lowercased entries for robustness.
    Normalizes apostrophes so curly quotes match straight quotes.

    Also adds short-form aliases to handle the ways the model refers to
    teams in league-insider prose:
      - Pass 2: first-word aliases from the franchise name (Eddie,
        Brandon, Ben, Miller, Paradis, etc.)
      - Pass 3: last-word aliases from the franchise name (Warmongers,
        Playmakers, Raiders, Cavallini — the distinctive noun the league
        commonly uses)
      - Pass 4: owner first-name aliases when owner_map is supplied
        (Michele, KP, Steve, Pat — owner names that never appear inside
        the franchise name itself)

    All alias passes require uniqueness and do not override existing
    entries. Substring hazards are handled by word-boundary regex
    matching at lookup time (_franchise_name_matches_in_context), not
    by length thresholds here.
    """
    reverse: dict[str, str] = {}

    # Pass 1: Full franchise names (exact case and lowercase)
    for fid, name in name_map.items():
        normalized = _normalize_apostrophes(name)
        reverse[normalized] = fid
        reverse[normalized.lower()] = fid

    # Pass 2: First-word aliases for short-form references.
    # Matches short-forms like "Eddie" (for "Eddie & the Cruisers") or
    # "Ben" (for "Ben's Gods"). Uniqueness across franchises is required
    # to avoid ambiguity. Substring hazards (e.g. "ben" inside "bench",
    # "brandon" inside "Brandon Aubrey") are handled by word-boundary
    # regex matching in _franchise_name_matches_in_context — not by a
    # length threshold here.
    _first_word_to_fids: dict[str, set[str]] = {}
    _stop_words = {"the", "and", "team", "club", "fantasy"}
    for fid, name in name_map.items():
        normalized = _normalize_apostrophes(name)
        words = re.findall(r"\w+", normalized)
        if not words:
            continue
        first_word = words[0].lower()
        if len(first_word) < 3:
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

    # Pass 3: Last-word aliases for short-form references.
    # Complements Pass 2 by picking up the common pattern where the model
    # uses the distinctive last token of a multi-word franchise name
    # ("Warmongers" for "Weichert's Warmongers", "Playmakers" for
    # "Paradis' Playmakers", "Raiders" for "Robb's Raiders"). 5-char
    # minimum keeps short generic nouns out; "draft" is stop-worded
    # because it collides with fantasy-draft language in prose.
    _last_word_to_fids: dict[str, set[str]] = {}
    _last_word_stop_words = _stop_words | {"draft", "league", "bowl"}
    for fid, name in name_map.items():
        normalized = _normalize_apostrophes(name)
        words = re.findall(r"\w+", normalized)
        if len(words) < 2:
            continue
        # Skip the trailing possessive 's' token if present
        last_word = words[-1].lower()
        if last_word == "s" and len(words) >= 2:
            last_word = words[-2].lower()
        if len(last_word) < 5:
            continue
        if last_word in _last_word_stop_words:
            continue
        _last_word_to_fids.setdefault(last_word, set()).add(fid)

    for alias, fids in _last_word_to_fids.items():
        if len(fids) != 1:
            continue
        fid = next(iter(fids))
        if alias not in reverse:
            reverse[alias] = fid

    # Pass 4: Owner first-name aliases (when owner_map supplied).
    # Picks up short-forms the model uses when writing in league-insider
    # voice ("Michele stayed perfect", "KP put up 169.60", "Steve squeaked
    # past Brandon") that don't appear anywhere in the franchise name
    # itself. 2-char minimum catches "KP" — safe because word boundaries
    # plus the capital-letter lookahead at match time prevent substring
    # and player-name hazards. Does not override existing aliases.
    if owner_map:
        _owner_word_to_fids: dict[str, set[str]] = {}
        for fid, owner in owner_map.items():
            if fid not in name_map:
                # Only alias owners for franchises we know by name
                continue
            normalized = _normalize_apostrophes(owner)
            words = re.findall(r"\w+", normalized)
            if not words:
                continue
            owner_first = words[0].lower()
            if len(owner_first) < 2:
                continue
            if owner_first in _stop_words:
                continue
            _owner_word_to_fids.setdefault(owner_first, set()).add(fid)

        for alias, fids in _owner_word_to_fids.items():
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

# ── V7: forward-lookback "superseding comparison" qualifier ─────────
# Captured prose (row 17, 2025 w10 a1):
#   "That's the highest individual score by any starter this season,
#    topping the previous mark of 46.75."
# The _PREVIOUS_QUALIFIER_PATTERN backward scan from "highest" misses
# because the disambiguating phrase ("topping the previous mark") sits
# AFTER the superlative trigger. Without a forward scan, the verifier
# extracts 103.10 (the losing team's game score in the prior sentence,
# nearest XX.XX to "highest") and flags a false SUPERLATIVE.
#
# Fix shape: symmetric forward-lookback, strictly additive. The helper
# only fires forward when backward returns False AND the forward window
# (bounded by the first sentence-terminal punctuation) contains a
# recognised "comparison-verb + qualifier" construction — e.g.
# "topping the previous", "breaking the old record of", "surpassing
# the previous mark", "eclipsing the prior mark", "beating the
# previous best". Conservative-guard discipline: a present forward
# qualifier can only CAUSE a skip, never flip a skip to a flag.
#
# Narrow scope: verb+qualifier, not bare "previous". The backward
# helper's bare "previous|prior" pattern is safe because the 40-char
# window tightly constrains what phrases can land there; a forward
# slice to end-of-sentence is wider and more forgiving, so the
# forward pattern requires explicit comparison-verb framing to avoid
# over-skipping prose like "...the season high; his previous game
# was only 80" where "previous" is narratively unrelated.
_SUPERSEDING_QUALIFIER_PATTERN = re.compile(
    r'\b(?:top(?:ping|ped|s)|'
    r'break(?:ing|s)?|broke|broken|'
    r'surpass(?:ing|es|ed)?|'
    r'eclips(?:ing|es|ed)?|'
    r'beat(?:ing|s|en)?|'
    r'exceed(?:ing|s|ed)?|'
    r'overtak(?:ing|es|en)|overtook)'
    r'\s+(?:the\s+)?(?:previous|prior|former|past|old)\b',
    re.IGNORECASE,
)
_SENTENCE_TERMINAL_PATTERN = re.compile(r'[.!?]')


def _has_previous_qualifier(
    text: str,
    pos: int,
    *,
    lookback: int = 40,
    match_end: int | None = None,
    forward_window: int = 120,
) -> bool:
    """Return True if a temporal qualifier precedes pos within lookback,
    OR (V7) a superseding-comparison construction follows the match in
    the same sentence.

    The forward scan begins at ``match_end`` when provided (cleaner
    semantics — skips the match body), otherwise at ``pos``. It is
    bounded by the first sentence-terminal punctuation in the forward
    window so qualifiers from unrelated adjacent sentences cannot leak
    in.
    """
    start = max(0, pos - lookback)
    if _PREVIOUS_QUALIFIER_PATTERN.search(text[start:pos]):
        return True
    forward_start = match_end if match_end is not None else pos
    forward_end = min(len(text), forward_start + forward_window)
    forward_slice = text[forward_start:forward_end]
    terminal = _SENTENCE_TERMINAL_PATTERN.search(forward_slice)
    if terminal is not None:
        forward_slice = forward_slice[: terminal.start()]
    return bool(_SUPERSEDING_QUALIFIER_PATTERN.search(forward_slice))


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
    """Extract the closest score (XX.XX) near a superlative keyword.

    V8 guard: skips scores that are part of a matchup-line format
    (A.AA-B.BB or B.BB-A.AA), where the dash connects two team scores.
    Source: OBSERVATIONS_2026_04_15 Finding 3, FP-SUPERLATIVE-MATCHUP-LINE.
    Prose "in their 137.50-103.10 win" → 103.10 is a team score, not a
    season-superlative claim.
    """
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

        # V8 matchup-line guard: skip scores connected by a dash to
        # another score (e.g. "137.50-103.10"). These are team scores
        # in a matchup line, not standalone player/season claims.
        in_matchup_line = False
        # Before: "137.50-[103.10]" — dash immediately preceding
        if m.start() > 0 and context[m.start() - 1] == "-":
            pre_start = max(0, m.start() - 8)
            pre = context[pre_start:m.start() - 1]
            if re.search(r"\d{2,3}\.\d{2}$", pre):
                in_matchup_line = True
        # After: "[103.10]-137.50" — dash immediately following
        if not in_matchup_line and m.end() < len(context) and context[m.end()] == "-":
            post = context[m.end() + 1:min(len(context), m.end() + 8)]
            if re.match(r"\d{2,3}\.\d{2}", post):
                in_matchup_line = True
        if in_matchup_line:
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
        # Fix V1/V7: "previous/prior season high of X" (backward) or
        # "highest ... topping the previous mark of X" (forward). Both
        # are pre-existing-record claims — skip, week-filtered
        # superlative data isn't available here.
        if _has_previous_qualifier(
            recap_text, match.start(), match_end=match.end(),
        ):
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
        # Fix V1/V7 (parity): backward "previous/prior season low of X"
        # or forward "lowest ... undercutting the previous mark of X"
        # — both pre-existing-record claims, skip.
        if _has_previous_qualifier(
            recap_text, match.start(), match_end=match.end(),
        ):
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

        # Fix V1/V7: "previous/prior all-time record of X" (backward)
        # or "all-time high ... breaking the previous record of X"
        # (forward) — pre-existing record claim, skip (same reasoning
        # as the season-high loop).
        if _has_previous_qualifier(
            recap_text, match.start(), match_end=match.end(),
        ):
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
# Cardinal counts 1-18 (practical ceiling for fantasy-football streak
# lengths — an 18-week regular season). Used by _POSSESSIVE_OBJECT_STREAK's
# optional count prefix to accept spelled-out counts ("four-game",
# "twelve-game") in addition to digits. All lowercase because captured
# prose (rows 9, 10, 24, 25, 35, 36, 40, 41, 42, 47, 53, 56, 105, 112,
# 113, 114 as of 2026-04-18) consistently lowercases these count words.
# If future captures show Title-case ("Four-game") or SHOUTCASE, extend
# here rather than adding re.IGNORECASE — the possessor group
# ([A-Z][\w&]*) has a case-sensitive leading-capital requirement that
# IGNORECASE would break (pronouns "his"/"their" would pass through).
_SPELLED_COUNTS_1_18 = (
    r'one|two|three|four|five|six|seven|eight|nine|ten|'
    r'eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen'
)

_POSSESSIVE_OBJECT_STREAK = re.compile(
    r'\b([A-Z][\w&]*(?:\s+[A-Z&][\w&]*)*)'
    r'(?:\'s|\u2019s)\s+'
    r'(?:(?:\d{1,2}|' + _SPELLED_COUNTS_1_18 + r')[-\s]game\s+)?'
    r'losing\s+streak',
)

# Idiomatic-target possessor in a snap clause. Matches a proper-noun
# possessor ("Brandon's", "Purple Haze's") — case-sensitive leading
# capital excludes pronoun possessors ("his", "their", "the"). Used
# only by _has_idiomatic_snap_possessor to decide whether a
# soft-trailing snap span ("snapped Brandon's perfect losing
# season…") is an idiomatic rhetorical target rather than a literal
# streak claim. See OBSERVATIONS_2026_04_15 D12 finding + backlog.
_PROPER_NOUN_POSSESSOR_IN_SNAP = re.compile(
    r'\b[A-Z][\w&]*(?:\s+[A-Z&][\w&]*)*(?:\'s|\u2019s)\b'
)


def _has_idiomatic_snap_possessor(match_text: str) -> bool:
    """True when a snap clause targets an idiomatic possessor, not a literal streak.

    The _SNAP_PATTERN can fire via a SOFT trailing keyword
    (losing / winning / straight / consecutive) when the actual
    streak-like noun in the clause is rhetorical — e.g. "Brandon's
    perfect losing **season**" (id=54) or "Purple Haze's modest
    **momentum**" (id=25) or "Brandon's losing **slide**" / "winning
    **run**". In those cases the span ends BEFORE the literal "streak"
    noun (either because no "streak" follows, or because the greedy
    80-char window cannot stretch far enough).

    Without this guard, _POSSESSIVE_OBJECT_STREAK fails on the span
    (no literal "streak" noun), and _find_nearby_franchise pass-2
    picks up the possessor after the snap verb, emitting a
    wrong-subject STREAK failure against prose that never claimed
    a literal streak was snapped.

    Return contract:
        True  → caller should `continue` (silence over speculation)
        False → fall through to the existing resolvers
                (_POSSESSIVE_OBJECT_STREAK, then proximity heuristic),
                which correctly handle literal-streak claims

    Literal claims — spans ending in "streak" or "skid" — always
    return False here; _POSSESSIVE_OBJECT_STREAK and the proximity
    heuristic remain authoritative for those. Pronoun-possessive
    idiomatic cases (e.g. "snapped their winning run") also return
    False because _PROPER_NOUN_POSSESSOR_IN_SNAP requires a
    case-sensitive leading capital; those fall through unchanged.
    """
    low = match_text.lower()
    if low.endswith("streak") or low.endswith("skid"):
        return False  # literal → existing resolvers handle
    return bool(_PROPER_NOUN_POSSESSOR_IN_SNAP.search(match_text))


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

        _match_text = recap_text[match.start():match.end()]

        # Idiomatic-target guard: if the snap clause fired via a SOFT
        # trailing keyword (losing/winning/straight/consecutive) and
        # targets a rhetorical possessor ("Brandon's perfect losing
        # season", "Purple Haze's modest momentum", "winning run",
        # "losing slide"), silence the check. The literal-streak
        # resolvers below stay authoritative for spans ending in
        # "streak" or "skid". See OBSERVATIONS_2026_04_15 D12.
        if _has_idiomatic_snap_possessor(_match_text):
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
# Lookbehind (?<![\d-]) prevents matching:
#   - tail of a larger number ("8-9" inside "18-9")
#   - embedded W-L inside a 3-part W-L-T triple ("12-1" inside "16-12-1")
# The second case (S1) is real: greedy [^.]{0,40} before the number
# backtracks to 11 chars ("lead to 16-") where "12-1" becomes a valid
# W-L match with tie group unfilled, misreading 16-12-1 as 12-1. The
# hyphen-rejection anchor forces the match to start at a non-hyphen
# position, where greedy backtracking correctly captures the full
# 16-12-1 triple via the optional tie group.
#
# Source: prompt_audit row 3 (2025 w2 a1) — "extending their series
# lead to 16-12-1 across 29 all-time meetings".
_SERIES_RECORD_PATTERN = re.compile(
    r'(?:'
    r'(?:leads?|trails?|series|rivalry|all[- ]?time|meetings?|record)\s[^.]{0,40}'
    r'(?<![\d-])(\d{1,2})-(\d{1,2})(?:-(\d{1,2}))?'
    r'|'
    r'(?<![\d-])(\d{1,2})-(\d{1,2})(?:-(\d{1,2}))?\s[^.]{0,40}'
    r'(?:series|rivalry|all[- ]?time|meetings?|record|lead)'
    r')',
    re.IGNORECASE,
)

# S4 idiom set — season-record transitions and state locatives.
# Used inside verify_series_records as an additional skip signal when the
# match text has no narrow H2H marker and the pre-context ends with an
# unambiguous single-franchise season-record attribution like "moved to"
# or "sits at". Anchored with `$` so the idiom must land flush against
# the W-L digits. Narrow verb set — only verbs that plausibly take a
# single-franchise subject and transition/describe its season W-L.
#
# Source: prompt_audit row 17 (2025 w10 a1) — "KP's team moved to 8-2
# and maintains the league's best record" and "Michele's Italian
# Cavallini dropped to 5-5 after leaving 59.20 bench points". Neither
# has a determiner (S2's shape), neither carries an H2H marker (S2's
# h2h-marker shape). Both are unambiguous season-record attributions
# that misattributed to an H2H pair.
_SEASON_RECORD_IDIOM_PATTERN = re.compile(
    r'\b(?:moved|dropped|fell|improved|climbed|rose|advanced)\s+to\s+$'
    r'|\b(?:sits|stands)\s+at\s+$'
    r'|\bnow\s+at\s+$',
    re.IGNORECASE,
)

# S2 h2h-marker set — unambiguous head-to-head keywords. Promoted from
# the inline regex previously built inside verify_series_records so the
# same marker definition can be reused by _should_skip_series_match
# (which is called from both verify_series_records and
# _extract_series_claims). Note: "record" is deliberately excluded —
# it's ambiguous between season and H2H framings, which is why the
# skip guards below exist.
_S2_H2H_MARKER = re.compile(
    r'\b(?:series|rivalry|meetings?|all[- ]?time|lead|head[- ]?to[- ]?head)\b',
    re.IGNORECASE,
)

# S2 post-context H2H markers — "vs X" / "against X" / "all-time" in
# the 40-char post-window indicates a legitimate H2H claim that should
# override a single-team skip signal in pre-context.
_S2_POST_H2H_CONTEXT = re.compile(
    r'\b(?:vs\.?|versus|against|head[- ]?to[- ]?head|all[- ]?time)\b',
    re.IGNORECASE,
)

# S2 determiner — single-team possessive or article preceding a W-L,
# indicating single-franchise season-record framing ("a 7-3 record",
# "his 8-2 mark"). Promoted from inline regex.
_S2_DETERMINER = re.compile(
    r'\b(?:a|an|his|her|their)\s+$',
    re.IGNORECASE,
)

# S5 (Phase 10, W13 observation): parenthesized W-L token inside the
# match text is a standings-list signal. Real series-record prose
# never parenthesizes the record — "Team (W-L)" is only used for
# standings listings. Unambiguous enough to skip even when an h2h
# marker like "lead" appears inside the match, because the greedy
# _SERIES_RECORD_PATTERN backbone can pull "holds a commanding lead
# at 11-2, while Miller (9-4), Steve (8-5)" into one match despite
# the surface "lead" keyword being standings-framed, not H2H-framed.
#
# Source: 2025 W13 approved recap — "KP holds a commanding lead at
# 11-2, while Miller (9-4), Steve (8-5), and Pat (8-5) battle for
# the remaining spots." match.group(0) captured three W-L tokens
# including one inside `(9-4)` parens.
#
# Only the opening paren and W-L are required; the closing paren may
# lie outside match.group(0) depending on where _SERIES_RECORD_PATTERN's
# 40-char gap terminates.
_S5_PAREN_WL = re.compile(r'\(\s*\d{1,2}-\d{1,2}(?:-\d{1,2})?')

# S6 (Phase 10, W10 observation): possessive proper-noun pre-context
# indicating single-team season record. Structurally equivalent to the
# S2 determiner set (which covers pronouns and articles) but for
# possessive-'s forms — "Pat's 8-2 record", "Miller's 7-3 record",
# "KP's 11-2 lead". The 's can be straight (U+0027) or curly (U+2019).
#
# Source: 2025 W10 approved recap — "Pat's 8-2 record took its first
# hit in two weeks". The 8-2 is Pat's season W-L, not a series record
# between any franchise pair. Under pre-S6 logic the match fell
# through to H2H comparison, was misattributed to (Purple Haze,
# Stu's Crew), and flagged against that pair's 9-12 all-time record.
_S6_POSSESSIVE = re.compile(r"\b\w{2,}['\u2019]s\s+$", re.IGNORECASE)


def _should_skip_series_match(
    match: re.Match,
    recap_text: str,
) -> bool:
    """Decide whether a _SERIES_RECORD_PATTERN match should be skipped
    (not verified as a head-to-head series-record claim).

    Centralizes the S2/S4/S5/S6 skip heuristics so the same decision
    is applied by both verify_series_records (per-week Category 4) and
    _extract_series_claims (feeds verify_cross_week_consistency). These
    two call sites must agree — a match verify_series_records skips
    should not be extracted as a cross-week claim either.

    Skip signals (evaluated in order, any one of which skips):

      S5 (standings-list): match.group(0) contains a parenthesized W-L
        token (`(W-L`). Unconditional — "Team (W-L)" prose is only used
        in standings listings, never in a real series-record claim.

      S2 / S4 / S6 (single-team season-record attribution): match text
        lacks a narrow H2H marker (series/rivalry/meetings/all-time/
        lead/head-to-head) AND pre-context (40-char window) ends with
        one of
          - single-team determiner a/an/his/her/their [S2]
          - season-record idiom "moved to "/"sits at "/"now at "/... [S4]
          - possessive proper-noun form "X's "/"X\u2019s " [S6]
        AND post-context (40-char window) lacks an overriding H2H
        marker (vs/versus/against/head-to-head/all-time).
    """
    matched = match.group(0)

    # S5: parenthesized W-L in match text — unambiguous standings-list
    # signal, applies even when h2h markers like "lead" appear in the
    # match (standings "lead" is framed differently than series "lead").
    if _S5_PAREN_WL.search(matched):
        return True

    # S2 / S4 / S6: single-team season-record attribution
    has_h2h_marker = bool(_S2_H2H_MARKER.search(matched))
    if has_h2h_marker:
        return False

    pre_start = max(0, match.start() - 40)
    pre40 = recap_text[pre_start:match.start()].lower()
    post_end = min(len(recap_text), match.end() + 40)
    post40 = recap_text[match.end():post_end].lower()

    has_det = bool(_S2_DETERMINER.search(pre40))
    has_idiom = bool(_SEASON_RECORD_IDIOM_PATTERN.search(pre40))
    has_poss = bool(_S6_POSSESSIVE.search(pre40))
    has_post_h2h = bool(_S2_POST_H2H_CONTEXT.search(post40))

    return (has_det or has_idiom or has_poss) and (not has_post_h2h)


def _franchise_name_matches_in_context(
    name: str, context: str,
) -> int:
    """Return earliest match position of franchise `name` in `context`,
    or -1 if no proper match is found.

    `name` is a lowercase key from `reverse_name_map`. `context` should
    have apostrophes normalized but case preserved (the single-word
    lookahead inspects capital letters directly).

    Matching rules:
      - Multi-word names (contain a space): word-boundary match via \\b.
        The interior whitespace already constrains the match to proper
        franchise-name alignment; no further filtering needed.
      - Single-word names (no spaces, i.e. short-form first-word aliases
        like "brandon", "paradis", "miller"): word-boundary match PLUS
        a negative lookahead rejecting whitespace + capital letter. A
        capitalized word immediately after a franchise short-form is
        almost always a player surname ("Brandon Aubrey" the kicker,
        not the franchise Brandon Knows Ball), and allowing such matches
        causes franchise misattribution.

    Source: prompt_audit row 3 (2025 w2 a1) — the bare-substring match
    for short-form alias "brandon" was hitting inside "Brandon Aubrey",
    adding Brandon Knows Ball to the verify_series_records nearby_fids
    set. The series-record claim 16-12-1 was then compared against the
    (wrong) Ben's Gods vs Brandon Knows Ball pair, firing a false H2H
    flag. The real H2H (Paradis' Playmakers vs Ben's Gods) sat outside
    the 300-char context window; with the short-form hazard removed,
    nearby_fids drops below two and the check correctly skips in
    silence rather than misattributing.
    """
    escaped = re.escape(name)
    if " " in name:
        pattern = re.compile(r'\b' + escaped + r'\b', re.IGNORECASE)
    else:
        # (?-i:[A-Z]) resets case-insensitivity inside the lookahead —
        # under IGNORECASE alone, [A-Z] would also match lowercase and
        # the lookahead would reject every word boundary followed by
        # any letter, not just capital-letter-starting tokens.
        pattern = re.compile(
            r'\b' + escaped + r'\b(?!\s+(?-i:[A-Z]))',
            re.IGNORECASE,
        )
    m = pattern.search(context)
    return m.start() if m else -1


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
    # Case preserved for the single-word-alias capital-letter lookahead
    # in _franchise_name_matches_in_context.
    context = _normalize_apostrophes(text[start:end])

    found: list[tuple[int, str]] = []  # (position, franchise_id)
    seen_ids: set[str] = set()

    for name, fid in reverse_name_map.items():
        if not name.islower():
            continue
        if fid in seen_ids:
            continue
        idx = _franchise_name_matches_in_context(name, context)
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

        # S2/S4/S5/S6 skip decision: delegated to _should_skip_series_match
        # so both this call site and _extract_series_claims (cross-week
        # consistency) apply identical heuristics. The helper's docstring
        # documents the individual skip signals.
        if _should_skip_series_match(match, recap_text):
            continue

        # Find all franchises that appear in a wider window around the
        # record. The series record could belong to any pair of
        # franchises mentioned in the surrounding paragraph — not just
        # the two closest. Case preserved so the single-word-alias
        # lookahead in _franchise_name_matches_in_context can inspect
        # capital letters directly.
        _ctx_start = max(0, match.start() - 300)
        _ctx_end = min(len(recap_text), match.end() + 100)
        _context = _normalize_apostrophes(recap_text[_ctx_start:_ctx_end])

        nearby_fids: set[str] = set()
        for name, fid in reverse_name_map.items():
            if not name.islower():
                continue
            if _franchise_name_matches_in_context(name, _context) >= 0:
                nearby_fids.add(fid)

        if len(nearby_fids) < 2:
            continue

        # Check if the claimed record matches ANY pair of nearby franchises
        matched = False
        for candidate_a in nearby_fids:
            for candidate_b in nearby_fids:
                if candidate_a >= candidate_b:
                    continue
                pair_key = frozenset({candidate_a, candidate_b})
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
        # Apply the same skip heuristics the per-week SERIES check
        # uses — otherwise verify_cross_week_consistency can flag
        # "inconsistencies" built from matches that would never have
        # been verified per-week (e.g., "Pat's 8-2 record" [S6] or
        # a parenthesized standings list [S5]).
        if _should_skip_series_match(match, narrative):
            continue
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
    for player_id, display in player_name_map.items():
        if not display:
            continue
        if ", " in display:
            parts = display.split(", ", 1)
            first_last = f"{parts[1]} {parts[0]}".strip().lower()
            if first_last not in display_to_pid:
                display_to_pid[first_last] = player_id
        else:
            key = display.strip().lower()
            if key not in display_to_pid:
                display_to_pid[key] = player_id

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
        for matchup in week_matchups_list:
            if matchup.week != week:
                continue
            matchup_numbers.add(round(matchup.winner_score, 2))
            matchup_numbers.add(round(matchup.loser_score, 2))
            matchup_numbers.add(round(abs(matchup.winner_score - matchup.loser_score), 2))
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

                score_abs_pos = window_start + m.start()

                # P1 guard (digit-boundary): the _PLAYER_SCORE_PATTERN has
                # no left boundary, so prose like "119.10-89.00" yields a
                # spurious "19.10" match at offset 1 inside "119.10". A
                # digit immediately before the match means we are inside
                # a larger decimal number — skip rather than flag.
                #
                # Source: prompt_audit rows 40/41 (2024 w10) — "119.10-
                # 89.00 win over Brandon" with a Ja'Marr Chase mention in
                # range was flagging "19.10" against Chase.
                if score_abs_pos > 0 and recap_text[score_abs_pos - 1].isdigit():
                    continue

                # Detect a leading minus sign immediately before the matched
                # number. The regex captures only digits.dot.digits but
                # negative scores ("-0.30" for defensive penalties) appear
                # in actual prose. Without this check, the verifier extracts
                # "0.30" and flags it as not matching canonical "-0.30".
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

                # P2 guard (bench-aggregate): the stable signature of a
                # bench-total clause is the trailing "points on the bench"
                # construction. The existing " but " guard catches only
                # one separator shape; captured prose uses " and ", ", "
                # (after "leaving"), and a fresh "Miller left" sentence
                # clause — all of which slip past the between-check. Peek
                # forward from the matched score for the bench construction
                # and skip if present.
                #
                # Source: prompt_audit rows 47 (2024 w14, "Aaron Rodgers
                # and 47.60 points on the bench"), 9 (2025 w5, "51.50
                # points on the bench with Stefon Diggs…"), 15 (2025 w9,
                # "left 52.60 points on the bench, including…").
                post_start = window_start + m.end()
                post_end = min(len(recap_text), post_start + 30)
                _post = recap_text[post_start:post_end].lower()
                if re.match(
                    r'\s*points?\s+(?:on|sitting\s+on|left\s+on)\s+'
                    r'(?:the\s+|his\s+|her\s+)?bench',
                    _post,
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


# ── Category 7: Player-Franchise Attribution ────────────────────────


def _load_week_player_franchise(
    db_path: str, league_id: str, season: int, week: int,
) -> dict[str, str]:
    """Load player_id -> franchise_id for all players in a given week."""
    mapping: dict[str, str] = {}
    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT json_extract(payload_json, '$.player_id'),
                      json_extract(payload_json, '$.franchise_id')
               FROM v_canonical_best_events
               WHERE league_id = ? AND season = ?
                 AND event_type = 'WEEKLY_PLAYER_SCORE'
                 AND CAST(json_extract(payload_json, '$.week') AS INTEGER) = ?""",
            (str(league_id), int(season), int(week)),
        ).fetchall()
    for row in rows:
        if row[0] and row[1]:
            mapping[str(row[0]).strip()] = str(row[1]).strip()
    return mapping


def _find_nearby_franchise_ids(
    text: str,
    position: int,
    reverse_name_map: dict[str, str],
    *,
    window: int = 200,
) -> set[str]:
    """Find all franchise_ids mentioned near a text position.

    Scans *window* chars before and after *position* for franchise names
    present in the reverse_name_map. Returns the set of franchise_ids
    found. An empty set means no franchise context could be determined
    (the caller should treat this as "no opinion", not "wrong franchise").

    Uses _franchise_name_matches_in_context for robust matching: word
    boundaries prevent substring hazards (e.g. "ben" inside "bench" or
    "brandon" inside "Brandon Aubrey") and a capital-letter lookahead
    prevents single-word aliases from matching inside player names.
    Case is preserved in the scanned context so the lookahead works.
    """
    start = max(0, position - window)
    end = min(len(text), position + window)
    # Case preserved — _franchise_name_matches_in_context inspects
    # capital letters directly for the single-word-alias lookahead.
    context = _normalize_apostrophes(text[start:end])

    found: set[str] = set()
    for name, fid in reverse_name_map.items():
        if not name.islower():
            continue
        if _franchise_name_matches_in_context(name, context) >= 0:
            found.add(fid)
    return found


def verify_player_franchise(
    recap_text: str,
    *,
    db_path: str,
    league_id: str,
    season: int,
    week: int,
    reverse_name_map: dict[str, str],
) -> list[VerificationFailure]:
    """Verify that players with attributed scores belong to a franchise
    in the surrounding text context.

    Catches cross-franchise misattribution: a real player with a real
    score placed in a paragraph about a matchup they were not involved
    in. This is the gap identified in OBSERVATIONS_2026_04_15 Finding 4
    (Watson 22.90 attributed to Paradis' Playmakers, actually on Steve's
    Warmongers).

    Gate: a player name must have a tightly attributed score (XX.XX
    within 25 chars, same window as PLAYER_SCORE) to trigger the
    franchise check. This limits the check to performance claims and
    avoids false positives from casual player mentions in cross-matchup
    comparisons.

    When the player's actual franchise_id is NOT among the franchise
    names found within 200 chars of the player mention, the check fires
    as HARD. When no franchise names are found nearby, the check is
    silent (no opinion is safer than a false positive).
    """
    failures: list[VerificationFailure] = []

    player_franchise = _load_week_player_franchise(
        db_path, league_id, season, week,
    )
    if not player_franchise:
        return []

    player_name_map = _load_player_name_map_for_verify(db_path, league_id)

    # Build display_name -> (player_id, franchise_id)
    display_to_info: dict[str, tuple[str, str]] = {}
    for pid, display in player_name_map.items():
        fid = player_franchise.get(pid)
        if not display or not fid:
            continue
        if ", " in display:
            parts = display.split(", ", 1)
            first_last = f"{parts[1]} {parts[0]}".strip().lower()
            if first_last not in display_to_info:
                display_to_info[first_last] = (pid, fid)
        else:
            key = display.strip().lower()
            if key not in display_to_info:
                display_to_info[key] = (pid, fid)

    text_lower = recap_text.lower()
    checked: set[str] = set()  # one flag per player display name

    for display_name, (pid, actual_fid) in display_to_info.items():
        if len(display_name) <= 5:
            continue
        if display_name in checked:
            continue

        idx = text_lower.find(display_name)
        while idx >= 0:
            name_end = idx + len(display_name)

            # Require a tightly attributed score (same 25-char window
            # and guards as PLAYER_SCORE).
            score_window_end = min(len(recap_text), name_end + 25)
            score_window = recap_text[name_end:score_window_end]

            has_attributed_score = False
            for m in _PLAYER_SCORE_PATTERN.finditer(score_window):
                score_abs_pos = name_end + m.start()
                # P1 digit-boundary guard
                if score_abs_pos > 0 and recap_text[score_abs_pos - 1].isdigit():
                    continue
                # Clause-break / separator guards
                between = score_window[:m.start()]
                if (
                    "." in between
                    or " by " in between
                    or "\n" in between
                    or " but " in between
                ):
                    continue
                # Dollar sign guard
                if score_abs_pos > 0 and recap_text[score_abs_pos - 1] == "$":
                    continue
                has_attributed_score = True
                break

            if has_attributed_score:
                nearby_fids = _find_nearby_franchise_ids(
                    recap_text, idx, reverse_name_map,
                )

                if nearby_fids and actual_fid not in nearby_fids:
                    actual_fname = _resolve_display_name(
                        actual_fid, reverse_name_map,
                    )
                    nearby_fnames = sorted(
                        _resolve_display_name(fid, reverse_name_map)
                        for fid in nearby_fids
                    )
                    failures.append(VerificationFailure(
                        category="PLAYER_FRANCHISE",
                        severity="HARD",
                        claim=(
                            f"{display_name.title()} mentioned in "
                            f"context of "
                            f"{', '.join(nearby_fnames)}"
                        ),
                        evidence=(
                            f"{display_name.title()} was on "
                            f"{actual_fname} in Week {week}, not "
                            f"{' or '.join(nearby_fnames)}."
                        ),
                    ))
                    checked.add(display_name)
                    break  # one flag per player is sufficient

                # Correctly attributed — mark checked to avoid
                # flagging a later occurrence in a different paragraph
                # where context might be ambiguous.
                checked.add(display_name)
                break

            idx = text_lower.find(display_name, idx + 1)

    return failures


# ── Category 8: FAAB Transaction Verification ───────────────────────

# Dollar amount pattern: $20, $20.00, $15.50
_FAAB_DOLLAR_PATTERN = re.compile(r"\$(\d+(?:\.\d{1,2})?)")

# Keywords that identify a dollar amount as a FAAB claim (not an
# auction draft amount or budget reference). Must appear within
# _FAAB_KEYWORD_WINDOW chars of the dollar sign.
_FAAB_KEYWORD_PATTERN = re.compile(
    r"\b(?:faab|waiver|pickup|pick-up|claim(?:ed)?|acquisition)\b",
    re.IGNORECASE,
)
_FAAB_KEYWORD_WINDOW = 30


def _load_faab_bids(
    db_path: str, league_id: str, season: int,
) -> dict[str, list[float]]:
    """Load player_id -> list of FAAB bid amounts for the season.

    Returns all canonical WAIVER_BID_AWARDED events. A player may
    have multiple bids (dropped and re-added).
    """
    bids: dict[str, list[float]] = {}
    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT payload_json
               FROM v_canonical_best_events
               WHERE league_id = ? AND season = ?
                 AND event_type = 'WAIVER_BID_AWARDED'
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

        player_id = str(p.get("player_id", "")).strip()
        if not player_id:
            added = p.get("players_added_ids")
            if isinstance(added, str) and added.strip():
                player_id = added.split(",")[0].strip()
            elif isinstance(added, list) and added:
                player_id = str(added[0]).strip()
        if not player_id:
            continue

        try:
            amount = float(p.get("bid_amount", 0))
        except (ValueError, TypeError):
            continue
        if amount <= 0:
            continue

        bids.setdefault(player_id, []).append(amount)

    return bids


def verify_faab_claims(
    recap_text: str,
    *,
    db_path: str,
    league_id: str,
    season: int,
) -> list[VerificationFailure]:
    """Verify FAAB dollar amounts attributed to players in recap text.

    Catches fabricated FAAB amounts: the model writes "$45 FAAB pickup"
    when the canonical bid was $20. Source: OBSERVATIONS_2026_04_15
    Finding 6 — FAAB dollar amounts were not verified by any existing
    check category.

    Gate: a dollar amount must appear within _FAAB_KEYWORD_WINDOW chars
    of a FAAB-related keyword (faab, waiver, pickup, claim, acquisition)
    to be treated as a FAAB claim. This avoids false positives from
    auction draft amounts or budget references.

    Matching tolerance: ±1.0 to handle rounding (model writes "$20"
    for a canonical $20.45 bid).
    """
    failures: list[VerificationFailure] = []

    faab_bids = _load_faab_bids(db_path, league_id, season)
    if not faab_bids:
        return []

    player_name_map = _load_player_name_map_for_verify(db_path, league_id)

    # Build display_name -> player_id
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

    text_lower = recap_text.lower()
    checked: set[tuple[str, float]] = set()  # (display_name, claimed)

    for dollar_match in _FAAB_DOLLAR_PATTERN.finditer(recap_text):
        try:
            claimed = float(dollar_match.group(1))
        except ValueError:
            continue

        # Gate: FAAB keyword must appear near the dollar amount
        kw_start = max(0, dollar_match.start() - _FAAB_KEYWORD_WINDOW)
        kw_end = min(len(recap_text), dollar_match.end() + _FAAB_KEYWORD_WINDOW)
        kw_context = recap_text[kw_start:kw_end]
        if not _FAAB_KEYWORD_PATTERN.search(kw_context):
            continue

        # Find nearest player name within 100 chars
        search_start = max(0, dollar_match.start() - 100)
        search_end = min(len(text_lower), dollar_match.end() + 100)
        search_context = text_lower[search_start:search_end]

        best_name: str | None = None
        best_dist = 101
        for display_name, pid in display_to_pid.items():
            if len(display_name) <= 5:
                continue
            if pid not in faab_bids:
                continue
            idx = search_context.find(display_name)
            if idx >= 0:
                # Distance from player name to dollar sign
                dollar_offset = dollar_match.start() - search_start
                dist = abs(idx - dollar_offset)
                if dist < best_dist:
                    best_dist = dist
                    best_name = display_name

        if best_name is None:
            continue

        check_key = (best_name, claimed)
        if check_key in checked:
            continue
        checked.add(check_key)

        pid = display_to_pid[best_name]
        canonical_amounts = faab_bids.get(pid, [])

        # Match within ±1.0 to handle model rounding ($20 vs $20.45)
        if not any(abs(claimed - ca) <= 1.0 for ca in canonical_amounts):
            canonical_str = ", ".join(f"${a:.2f}" for a in canonical_amounts)
            failures.append(VerificationFailure(
                category="FAAB_CLAIM",
                severity="HARD",
                claim=(
                    f"${claimed:.0f} FAAB attributed to "
                    f"{best_name.title()}"
                ),
                evidence=(
                    f"Canonical FAAB bids for {best_name.title()}: "
                    f"{canonical_str if canonical_str else 'none found'}."
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
    owner_map = _load_franchise_owner_names(db_path, league_id, season)
    reverse_name_map = _build_reverse_name_map(name_map, owner_map)

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

    # Category 7: Player-franchise attribution (HARD)
    checks_run += 1
    all_failures.extend(verify_player_franchise(
        narrative,
        db_path=db_path,
        league_id=league_id,
        season=season,
        week=week,
        reverse_name_map=reverse_name_map,
    ))

    # Category 8: FAAB transaction verification (HARD)
    checks_run += 1
    all_failures.extend(verify_faab_claims(
        narrative,
        db_path=db_path,
        league_id=league_id,
        season=season,
    ))

    hard = tuple(f for f in all_failures if f.severity == "HARD")
    soft = tuple(f for f in all_failures if f.severity == "SOFT")

    return VerificationResult(
        passed=len(hard) == 0,
        hard_failures=hard,
        soft_failures=soft,
        checks_run=checks_run,
    )
