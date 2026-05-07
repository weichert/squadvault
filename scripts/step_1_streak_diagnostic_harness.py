#!/usr/bin/env python3
"""Streak verb diagnostic harness — Step 3.2 of the four-step playbook.

Adapts the score-thread `step_1_score_diagnostic_harness.py` pattern
(which lived in /tmp during the score thread and is reconstructed
here) to streak categories per
`_observations/OBSERVATIONS_2026_05_04_STREAK_VERB_PRE_COMPUTATION_SCOPE.md`
§8.

For each prompt_audit row in scope, the harness:

1. Parses the rendered NARRATIVE ANGLES block for STREAK lines.
2. For each STREAK line, identifies the canonical phrasing
   (T1/T2/T3/T4 status, T5/T6 outcome detail, T8/T9/T10 record).
3. Classifies the corresponding claim in the model's narrative_draft:

   * VERBATIM   — the canonical headline appears as a substring of
     the prose. (Outcome details T5/T6 are checked separately;
     verbatim on either headline or outcome counts as VERBATIM for
     that claim.)
   * PARAPHRASE — the franchise is named in the prose, the streak
     fact is plausibly preserved, but the canonical phrasing is not
     verbatim. (Pluralization corrections like "have" → "has"
     count as PARAPHRASE — they are legitimate language fixes.)
   * INVERTED   — the franchise is named in the prose AND a streak
     claim of the opposite direction or wrong verb appears in a
     200-character window around the franchise mention. This is the
     load-bearing failure category for the streak thread.
   * OMITTED    — the franchise is not named in the prose at all.
     Silence is preferred over fabrication, so OMITTED is reported
     as a coverage measurement, not a failure.

The harness is helper-bound: canonical phrases come from
`streak_strings_v1.format_streak_*`, never hand-written. Per the V8
follow-up lesson, hand-written format expectations leak silent
regressions.

§10 Q1 extension (added by the post-review brief):
Per-(row, franchise) fabrication-shape classification across five
buckets (RECORD_APPROACH, STATUS_CLAIM_EVICTED, STATUS_CLAIM_OMITTED,
STATUS_CLAIM_NOT_EVICTED, MISS) in addition to the per-claim VERBATIM/
PARAPHRASE/INVERTED/OMITTED classifier. The fabrication-shape
classifier requires per-row counterfactual angle reconstruction
(re-running _detect_streaks against derived canonical context) because
prompt_audit.angles_summary_json strips franchise_ids and headline
fields per prompt_audit_v1.py:174.

Usage:

    scripts/py scripts/step_1_streak_diagnostic_harness.py \\
        --db .local_squadvault.sqlite \\
        --league-id 70985 \\
        --scope last10-approved

    scripts/py scripts/step_1_streak_diagnostic_harness.py \\
        --db .local_squadvault.sqlite \\
        --league-id 70985 \\
        --scope week --season 2024 --week-index 13

    scripts/py scripts/step_1_streak_diagnostic_harness.py \\
        --db .local_squadvault.sqlite \\
        --league-id 70985 \\
        --scope week --season 2025 --week-index 13 --show-snippets

Outputs:

* Per-row table (prompt_audit.id, season, week, attempt, claim
  template, canonical phrase, classification, [optional] prose
  snippet around the relevant franchise name).
* Aggregate counts by classification, total claims, total rows.
* §10 Q1 fabrication-shape bucket aggregate.
* If `--show-snippets`: a short prose snippet for each non-VERBATIM
  classification, to support manual classification audit.

Exit code is always 0 — this is observational, not a gate.
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Add src/ to path so the helper module resolves when the harness is
# invoked from the repo root.
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

from squadvault.core.recaps.context.league_history_v1 import (  # noqa: E402
    derive_league_history_v1,
)
from squadvault.core.recaps.context.narrative_angles_v1 import (  # noqa: E402
    _detect_streak_records,
    _detect_streaks,
)
from squadvault.core.recaps.context.season_context_v1 import (  # noqa: E402
    derive_season_context_v1,
)
from squadvault.core.recaps.render.streak_strings_v1 import (  # noqa: E402
    format_streak_marker,
    format_streak_outcome,
    format_streak_phrase,
    format_streak_record,
    format_streak_status,
)

# Reference the helpers so static analyzers don't drop the imports.
# Each is wired into the harness's classifier (canonical-phrase
# generation) or kept available for future-iteration extensions
# (e.g. per-template verbatim windows).
_HELPERS = (
    format_streak_marker,
    format_streak_outcome,
    format_streak_phrase,
    format_streak_record,
    format_streak_status,
)
# §10 Q1 reserves these for use after Step 1 (helper extension); at
# 0a-time they are imported-but-unused above the predicate definition.
_DETECTORS = (
    _detect_streak_records,
    _detect_streaks,
)


# ── Data classes ────────────────────────────────────────────────────


@dataclass(frozen=True)
class StreakClaim:
    """A streak claim emitted into the angles block, derived for classification."""

    franchise_name: str
    template_id: str          # T1, T2, T3, T4, T8, T9, T10
    direction: str            # "win" or "loss"
    canonical_headline: str   # what the helper emits, verbatim
    canonical_outcome: str    # T5/T6 clause if present in the angle line, else ""


@dataclass(frozen=True)
class PromptAuditRow:
    id: int
    league_id: str
    season: int
    week_index: int
    attempt: int
    captured_at: str
    narrative_angles_text: str
    narrative_draft: str
    verification_passed: int


@dataclass(frozen=True)
class Classification:
    row_id: int
    season: int
    week_index: int
    attempt: int
    claim: StreakClaim
    category: str             # VERBATIM | PARAPHRASE | INVERTED | OMITTED
    snippet: str              # short prose excerpt around franchise mention


@dataclass(frozen=True)
class FabricationShape:
    """Fabrication-shape classification for one (row, franchise) pair.

    Per §10 Q1 paired-thread brief. A single prompt_audit row can yield
    multiple FabricationShape entries (one per franchise in the row's
    standings); aggregate counts represent franchise-instances, not
    rows.
    """

    row_id: int
    season: int
    week_index: int
    attempt: int
    franchise_id: str
    franchise_name: str
    bucket: str               # RECORD_APPROACH | STATUS_CLAIM_EVICTED |
                              # STATUS_CLAIM_OMITTED | STATUS_CLAIM_NOT_EVICTED |
                              # MISS
    evidence: str             # short prose snippet or per-bucket diagnostic


# ── Angle-block parsing ─────────────────────────────────────────────


# Match the rendered angle line shape, optionally:
#   "  [HEADLINE] [RE: Wolves] Wolves on 5-game win streak — Record: 7-1. Beat Bears this week — streak continues."
_LINE_PREFIX_RE = re.compile(
    r"^\s*\[(?:HEADLINE|NOTABLE|MINOR)\]"          # strength label
    r"(?:\s*\[RE:[^\]]*\])?"                        # optional attribution tag
    r"\s*(?P<body>.*)$"                             # body
)

# Streak templates. Each tuple: (compiled regex, template_id, direction).
# Patterns match the HEADLINE part only (post-detail-split).
_STREAK_TEMPLATES = [
    # T1: long-form winning  — "Wolves on 5-game win streak"
    (re.compile(r"^(?P<name>.+?) on (?P<n>\d+)-game win streak$"), "T1", "win"),
    # T3: long-form losing   — "Wolves on 5-game losing streak"
    (re.compile(r"^(?P<name>.+?) on (?P<n>\d+)-game losing streak$"), "T3", "loss"),
    # T2: short-form winning — "Wolves has won 3 straight"
    (re.compile(r"^(?P<name>.+?) has won 3 straight$"), "T2", "win"),
    # T4: short-form losing  — "Wolves has lost 3 straight"
    (re.compile(r"^(?P<name>.+?) has lost 3 straight$"), "T4", "loss"),
    # T8: tied/broke winning record
    (re.compile(r"^(?P<name>.+?) tied/broke the league win streak record \(\d+ games\)$"), "T8", "win"),
    # T9: 1 win from record
    (re.compile(r"^(?P<name>.+?) is 1 win from the league win streak record \(\d+\)$"), "T9", "win"),
    # T10: tied/broke losing record
    (re.compile(r"^(?P<name>.+?) tied/broke the league loss streak record \(\d+ games\)$"), "T10", "loss"),
]


def parse_streak_claims(angles_text: str) -> list[StreakClaim]:
    """Extract STREAK claims from rendered narrative_angles_text."""
    claims: list[StreakClaim] = []
    for raw_line in angles_text.split("\n"):
        m = _LINE_PREFIX_RE.match(raw_line)
        if not m:
            continue
        body = m.group("body")
        # Split headline from outcome detail at the em-dash separator.
        # Format: "<headline> — <detail>" where detail is "Record: <rec>." or
        # "<outcome clause>". We want the headline component for template match,
        # and any "Beat/Lost to/etc." outcome clause for the canonical_outcome.
        if " — " in body:
            headline, _sep, detail = body.partition(" — ")
        else:
            headline, detail = body, ""
        for pattern, template_id, direction in _STREAK_TEMPLATES:
            tm = pattern.match(headline.strip())
            if not tm:
                continue
            # canonical_outcome: the T5/T6 clause if it appears anywhere in
            # the rendered detail. Detected by presence of "Beat", "Lost to",
            # "snapped" (rare, post-snap form), or "streak continues".
            outcome = ""
            if detail and (
                "Beat " in detail
                or "Lost to " in detail
                or "snapped" in detail
                or "streak continues" in detail
            ):
                # Strip "Record: X-Y." prefix and trailing period if present.
                # The outcome clause is the substring after "Record: <rec>."
                # marker; we keep the verb-bearing minimum span.
                rec_marker = re.search(r"Record:\s*\d+-\d+\.\s*", detail)
                outcome = detail[rec_marker.end():] if rec_marker else detail
                outcome = outcome.strip().rstrip(".").strip()
            claims.append(StreakClaim(
                franchise_name=tm.group("name"),
                template_id=template_id,
                direction=direction,
                canonical_headline=headline.strip(),
                canonical_outcome=outcome,
            ))
            break
    return claims


# ── Inversion detection ─────────────────────────────────────────────


# Inversion phrases for each direction. These are the verb-bearing
# forms the model uses when it commits the streak-direction error.
# "snapped" is direction-AGNOSTIC for active streak claims: for either
# a win-direction or loss-direction CONTINUING streak, "snapped" implies
# the streak ended, which contradicts the active-streak angle.
_WIN_INVERSION_RE = re.compile(
    r"\b(losing streak|loss streak|snapped|on a (\d+)-game (?:loss|losing)|"
    r"lost (?:\d+|three) (?:in a row|straight|consecutive))\b",
    re.IGNORECASE,
)
_LOSS_INVERSION_RE = re.compile(
    r"\b(win streak|winning streak|snapped|on a (\d+)-game win|"
    r"won (?:\d+|three) (?:in a row|straight|consecutive))\b",
    re.IGNORECASE,
)


def _is_inversion_attached_to_alias(
    prose: str, aliases: list[str], inversion_re: re.Pattern[str]
) -> bool:
    """Return True if any inversion-phrase match in prose has an alias
    of the franchise close before it (within 30 chars, with optional
    possessive 's).

    This rejects cross-team false positives where the inversion phrase
    appears in the prose window around the franchise's mention but is
    grammatically attached to a DIFFERENT team.

    Examples:
      - 'Brandon, who remains winless at 0-13'        → no inversion attached
      - 'KP extended his win streak ... over Brandon' → 'win streak' attached to KP, NOT Brandon
      - 'Brandon\\'s win streak'                       → 'win streak' attached to Brandon
      - 'Brandon won 5 in a row'                       → 'won 5 in a row' attached to Brandon
    """
    for match in inversion_re.finditer(prose):
        m_start = match.start()
        # Search backward up to 30 chars for any alias (or its possessive form)
        # ending close before the inversion phrase.
        lookback_start = max(0, m_start - 60)
        lookback = prose[lookback_start:m_start]
        for alias in aliases:
            if not alias:
                continue
            # Possessive variant: "alias's " or "alias' " (common with names ending in s).
            for variant in (alias + "'s ", alias + "' ", alias + " "):
                pos = lookback.rfind(variant)
                if pos < 0:
                    continue
                gap = len(lookback) - (pos + len(variant))
                if gap <= 30:
                    return True
    return False


def _is_record_approach_attached_to_alias(
    prose: str, aliases: list[str], record_re: re.Pattern[str]
) -> tuple[bool, str]:
    """Return (True, snippet) if any record-approach phrase has an
    alias of the franchise within ~200 chars before it; else (False, '').

    Mirrors the look-backward-from-regex pattern of
    _is_inversion_attached_to_alias but with a wider lookback window
    (200 chars vs. 30) because record-approach prose typically follows
    the franchise mention by more characters than the verb-bearing
    inversion phrases — the model writes "Brandon's streak to 11
    straight defeats, matching the league's all-time record" with
    intermediate clauses.

    The earlier earliest-alias-window approach
    (_extract_window(prose, found_alias, before=120, after=200))
    misses W11 id=140-shape rows: BKB is mentioned at the start of a
    long franchise paragraph and the matching-record phrase appears
    267 chars later, outside the +200 window. Look-backward from the
    regex match to ANY alias-variant mention catches the closer
    later possessive ("Brandon's" at gap=31 chars) and attributes
    correctly.

    The returned snippet is 100 chars before + 200 chars after the
    regex match, suitable for memo specimen citation.
    """
    for match in record_re.finditer(prose):
        m_start = match.start()
        lookback_start = max(0, m_start - 200)
        lookback = prose[lookback_start:m_start]
        for alias in aliases:
            if not alias:
                continue
            for variant in (alias + "'s ", alias + "' ", alias + " ", alias + ","):
                pos = lookback.rfind(variant)
                if pos < 0:
                    continue
                # Found alias-variant before the regex match — attribute.
                snippet_start = max(0, m_start - 100)
                snippet_end = min(len(prose), match.end() + 100)
                return (True, prose[snippet_start:snippet_end].strip()[:240])
    return (False, "")


def _extract_window(prose: str, name: str, before: int = 100, after: int = 200) -> str:
    """Return prose centered on the first occurrence of `name`, or ''.

    Used for snippet output during PARAPHRASE/INVERTED reporting; not
    for inversion detection (that uses _is_inversion_attached_to_alias).
    """
    idx = prose.find(name)
    if idx < 0:
        return ""
    start = max(0, idx - before)
    end = min(len(prose), idx + len(name) + after)
    return prose[start:end]


def _find_any_alias(prose: str, aliases: list[str]) -> tuple[int, str]:
    """Return (index, alias) for the earliest alias match in prose, or (-1, '').

    Aliases are tried in order. The list should be ordered most-specific
    first (full name before owner-first-word) so we don't match a
    short alias inside a longer one when the longer one would have
    been more informative for windowing.
    """
    earliest = -1
    found = ""
    for alias in aliases:
        if not alias:
            continue
        idx = prose.find(alias)
        if idx >= 0 and (earliest < 0 or idx < earliest):
            earliest = idx
            found = alias
    return (earliest, found)


def _build_aliases_for_franchise(
    full_name: str, nickname: str | None, owner_name: str | None
) -> list[str]:
    """Build the alias set the model is likely to use for a franchise.

    Mirrors the resolver passes 4a (curated nickname) and 4b (owner
    first-word) used by _build_reverse_name_map. The returned list is
    ordered most-specific first; the matching code uses earliest-hit.
    """
    aliases: list[str] = []
    if full_name:
        aliases.append(full_name)
    # Curated nickname (pass 4a): e.g. "Brandon Knows Ball" -> "BKB" or
    # whatever commissioner seeded.
    if nickname and nickname.strip():
        aliases.append(nickname.strip())
    # Owner first-word (pass 4b): e.g. owner "Brandon Smith" -> "Brandon".
    if owner_name and owner_name.strip():
        first_word = owner_name.strip().split()[0]
        if first_word and first_word not in aliases:
            aliases.append(first_word)
    # Franchise-name first-word: e.g. "Miller's Genuine Draft" -> "Miller's".
    # This catches the natural-prose shortening the model often picks
    # when the full team name is long and obviously possessive.
    if full_name:
        first_word = full_name.split()[0]
        if first_word and first_word not in aliases:
            aliases.append(first_word)
    return aliases


def classify(claim: StreakClaim, prose: str, aliases: list[str]) -> tuple[str, str]:
    """Classify a single claim against the model's prose.

    aliases: list of names the model might use for this franchise,
    most-specific first. Built by _build_aliases_for_franchise and
    used for OMITTED detection and inversion-window placement.

    Returns (category, snippet). Snippet is empty for VERBATIM/OMITTED;
    for PARAPHRASE/INVERTED it's the 100-before-200-after window
    around the earliest alias mention.
    """
    # VERBATIM: canonical headline as substring of prose.
    if claim.canonical_headline in prose:
        return ("VERBATIM", "")
    # VERBATIM via outcome clause (T1-T4 with appended T5/T6 detail).
    # If the headline isn't verbatim but the outcome clause is, count
    # this as VERBATIM for the streak claim — the model has carried
    # the verb-bearing minimum span. Memo §4 designates these as the
    # "verbatim-required" windows.
    if claim.canonical_outcome and claim.canonical_outcome in prose:
        return ("VERBATIM", "")

    # OMITTED: no alias for this franchise appears in prose.
    idx, matched_alias = _find_any_alias(prose, aliases)
    if idx < 0:
        return ("OMITTED", "")

    # Franchise mentioned (via some alias), headline not verbatim.
    # Test for inversion: only flag INVERTED if an inversion phrase
    # is grammatically attached to one of the franchise's aliases
    # (within 30 chars after, possibly possessive). This rejects
    # cross-team false positives where another team's opposite-
    # direction streak appears in the windowed prose.
    snippet = _extract_window(prose, matched_alias)
    if claim.direction == "win":
        if _is_inversion_attached_to_alias(prose, aliases, _WIN_INVERSION_RE):
            return ("INVERTED", snippet)
    elif claim.direction == "loss":
        if _is_inversion_attached_to_alias(prose, aliases, _LOSS_INVERSION_RE):
            return ("INVERTED", snippet)

    # Mentioned, neither verbatim nor inverted → PARAPHRASE.
    return ("PARAPHRASE", snippet)


# ── §10 Q1 fabrication-shape classifier ─────────────────────────────


_T9_LOSS_RECORD_APPROACH = re.compile(
    # Verb phrase + optional "the" + optional 0..3 modifier words + "record".
    # The original brief regex used (?:league|all-time)? which permits ONE
    # adjective; specimens like "the league's all-time record" and
    # "the all-time league record" need TWO. The {0,3} window covers the
    # observed phrasings without unbounded false-positive risk; the
    # alternation '|longest...streak' carries the second canonical shape.
    r"(?:closing in on|short of|shy of|matching|matches)\s+"
    r"(?:the\s+)?(?:[a-zA-Z'\-]+\s+){0,3}record"
    r"|longest\s+(?:active\s+)?(?:losing|loss)\s+streak",
    re.IGNORECASE,
)

_T3_STATUS_CLAIM = re.compile(
    r"\b(?:on|riding)\s+(?:a|an)?\s*(?P<count>\d+)[- ](?:game\s+)?"
    r"(?:losing|loss|win|winning)\s+streak",
    re.IGNORECASE,
)

_T9_LOSS_IN_ANGLES_RE = re.compile(
    r"is\s+1\s+loss\s+from\s+the\s+league\s+loss\s+streak\s+record",
    re.IGNORECASE,
)



def classify_fabrication_shape(
    row: PromptAuditRow,
    standings: list[Any],
    longest_loss_record: int | None,
    is_multi_season: bool,
    fid_to_name: dict[str, str],
    aliases_by_name: dict[str, list[str]],
) -> list[FabricationShape]:
    """Classify per-(row, franchise) fabrication shape per §10 Q1 thread.

    Buckets:
    * RECORD_APPROACH         — T9-LOSS-shaped fabrication (Bug 2): the
                                losing-streak record-approach prose
                                pattern fires AND no T9-LOSS angle is
                                present in the rendered angles block
                                AND the post-fix detector gate would
                                fire (streak <= -3 AND abs(streak) ==
                                record - 1) AND the prose match falls
                                in a window mentioning this franchise.
    * STATUS_CLAIM_EVICTED    — Bug 1 fabrication shape: |streak| >= 5
                                (the strength=3 long-form gate at
                                narrative_angles_v1.py:185, :203) AND
                                the canonical T1/T3 angle is absent
                                from the rendered angles block AND the
                                prose contains a status claim attributed
                                to this franchise AND the count in the
                                prose disagrees with abs(streak) from
                                STANDINGS.
    * STATUS_CLAIM_OMITTED    — Bug 1 silent-omission shape: |streak|
                                >= 5 AND the canonical angle is absent
                                from the rendered angles block AND the
                                franchise IS named in prose AND no
                                T3-shape status claim is attributed to
                                that franchise. This is the §6
                                silence-fallback's observable signature
                                (model talks about the franchise in
                                some other context but skips the
                                canonical streak status claim).
    * STATUS_CLAIM_NOT_EVICTED — Distribution-context bucket: prose
                                matches the status-claim pattern in a
                                window mentioning this franchise AND
                                the canonical T1/T3 angle is present in
                                the rendered angles block. Not a Bug 1
                                signal.
    * MISS                    — None of the above applies. (Includes
                                the brief's "paraphrase, fine" case
                                where the angle is absent but the
                                count agrees.)

    The strength=3 / |streak| >= 5 gate reads the brief's "strength-3
    T3 STREAK angle" criterion as referring to the strength assignment
    actually produced by _detect_streaks at the long-form gate; the
    brief's |streak| >= 4 wording is a drafting carryover from the
    long-form streak threshold and does not co-occur with strength=3
    in the production code.
    """
    out: list[FabricationShape] = []
    angles_text = row.narrative_angles_text or ""
    prose = row.narrative_draft or ""

    # Parse which canonical streak phrasings reached the angles block,
    # keyed by franchise name (the same key _detect_streaks emits via
    # fname()).
    angle_claims_by_name: dict[str, set[str]] = {}
    for c in parse_streak_claims(angles_text):
        angle_claims_by_name.setdefault(c.franchise_name, set()).add(
            c.template_id
        )

    has_t9_loss_in_text = (
        _T9_LOSS_IN_ANGLES_RE.search(angles_text) is not None
    )

    for rec in standings:
        fid = rec.franchise_id
        streak = rec.current_streak
        name = fid_to_name.get(fid, fid)
        aliases = aliases_by_name.get(name, [name])

        bucket: str | None = None
        evidence = ""

        # RECORD_APPROACH (Bug 2). Multi-season guard mirrors
        # _detect_streak_records:551–556. Attribution uses look-backward
        # from regex match (mirrors _is_inversion_attached_to_alias);
        # the earlier earliest-alias-window approach missed W11 id=140-
        # shape rows where the franchise is named at the start of a
        # long paragraph and the record-approach phrase appears past
        # the +200-char window.
        # Post-§10 Q1 closure: the predicate _would_t9_loss_fire
        # has been retired in favor of routing through the helper.
        # Helper returns non-None for both T9-LOSS and T10 on the
        # loss side; the abs(streak) < record check filters to
        # T9-LOSS specifically (RECORD_APPROACH bucket scope).
        helper_t9_loss_result = (
            format_streak_record(name, streak, longest_loss_record, "")
            if longest_loss_record is not None
            else None
        )
        helper_would_t9_loss_fire = (
            helper_t9_loss_result is not None
            and longest_loss_record is not None
            and abs(streak) < longest_loss_record
        )
        if (
            is_multi_season
            and longest_loss_record is not None
            and helper_would_t9_loss_fire
            and not has_t9_loss_in_text
        ):
            matched, snippet = _is_record_approach_attached_to_alias(
                prose, aliases, _T9_LOSS_RECORD_APPROACH
            )
            if matched:
                bucket = "RECORD_APPROACH"
                evidence = snippet

        # STATUS_CLAIM family — only when |streak| >= 5 (the strength=3
        # gate in _detect_streaks at narrative_angles_v1.py:185, :203).
        if bucket is None and abs(streak) >= 5:
            template_ids = angle_claims_by_name.get(name, set())
            angle_present = bool(template_ids & {"T1", "T3"})
            _, found_alias = _find_any_alias(prose, aliases)
            window = (
                _extract_window(prose, found_alias, before=120, after=200)
                if found_alias
                else ""
            )
            status_match = (
                _T3_STATUS_CLAIM.search(window) if window else None
            )

            if status_match and angle_present:
                bucket = "STATUS_CLAIM_NOT_EVICTED"
                evidence = window.strip()[:200]
            elif status_match and not angle_present:
                # Compare prose count against canonical |streak|.
                try:
                    prose_count = int(status_match.group("count"))
                except (TypeError, ValueError):
                    prose_count = -1
                if prose_count != abs(streak):
                    bucket = "STATUS_CLAIM_EVICTED"
                    evidence = (
                        f"prose_count={prose_count} canonical={abs(streak)} "
                        f"window={window.strip()[:160]}"
                    )
                # If counts agree but angle is absent, falls through to
                # MISS — the brief's "paraphrase, fine" case.
            elif found_alias and not status_match and not angle_present:
                # Bug 1 silent-omission shape: franchise IS mentioned in
                # prose but no T3-shape status claim is attributed AND the
                # canonical T1/T3 angle is absent from the angles block.
                # This is the §6 silence-fallback's observable signature
                # — model talks about the franchise (e.g., in a non-status
                # context like a record-approach claim or a matchup recap)
                # but skips the canonical streak status claim. The
                # earlier draft of this gate required `not found_alias`
                # (interpretation: franchise NOT named at all), which
                # would have miscounted W11 id=140-shape rows as MISS;
                # corrected here to require franchise IS named.
                bucket = "STATUS_CLAIM_OMITTED"
                evidence = (
                    f"|streak|={abs(streak)} mentioned but no canonical claim"
                )

        if bucket is None:
            bucket = "MISS"

        out.append(FabricationShape(
            row_id=row.id,
            season=row.season,
            week_index=row.week_index,
            attempt=row.attempt,
            franchise_id=fid,
            franchise_name=name,
            bucket=bucket,
            evidence=evidence,
        ))

    return out


# ── DB access ───────────────────────────────────────────────────────


_SCHEMA_PROBE_SQL = """
SELECT pa.id, pa.league_id, pa.season, pa.week_index, pa.attempt,
       pa.captured_at, pa.narrative_angles_text, pa.narrative_draft,
       pa.verification_passed
  FROM prompt_audit pa
"""


def fetch_rows_last10_approved(conn: sqlite3.Connection, league_id: str) -> list[PromptAuditRow]:
    """Last 10 (season, week_index) pairs that have at least one APPROVED
    artifact, returning the most-recent prompt_audit row per pair.

    The previous version filtered prompt_audit by captured_at <=
    recap_artifacts.created_at, but that produced 0 results — the
    temporal relationship between prompt_audit captures and recap
    artifact creation isn't reliably "audit before artifact" across
    all approved weeks (some approvals predate audit data, others
    post-date the artifact's original creation due to regen-on-
    approval flows). Simpler and more robust: approved-week filter,
    then take the latest pa row for that week.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT season, week_index, MAX(created_at) AS latest_created
          FROM recap_artifacts
         WHERE league_id = ?
           AND state = 'APPROVED'
         GROUP BY season, week_index
         ORDER BY latest_created DESC
         LIMIT 10
        """,
        (league_id,),
    )
    pairs = cur.fetchall()
    rows: list[PromptAuditRow] = []
    for season, week_index, _ in pairs:
        cur.execute(
            _SCHEMA_PROBE_SQL
            + " WHERE pa.league_id = ? AND pa.season = ? AND pa.week_index = ? "
              "ORDER BY pa.id DESC LIMIT 1",
            (league_id, season, week_index),
        )
        r = cur.fetchone()
        if r is not None:
            rows.append(PromptAuditRow(*r))
    return rows


def fetch_rows_week(
    conn: sqlite3.Connection, league_id: str, season: int, week_index: int
) -> list[PromptAuditRow]:
    """All prompt_audit rows for a single (league, season, week)."""
    cur = conn.cursor()
    cur.execute(
        _SCHEMA_PROBE_SQL
        + " WHERE pa.league_id = ? AND pa.season = ? AND pa.week_index = ? "
          "ORDER BY pa.id ASC",
        (league_id, season, week_index),
    )
    return [PromptAuditRow(*r) for r in cur.fetchall()]


def load_franchise_aliases(
    conn: sqlite3.Connection, league_id: str, season: int
) -> dict[str, list[str]]:
    """Build {full_name -> aliases[]} map for the given (league, season).

    The angles block keys streak claims by franchise *name* (the
    output of fname() during angle detection), so the harness keys
    aliases by the same name string. Mirrors _build_reverse_name_map
    pass 4a (curated nickname) and pass 4b (owner first-word).
    """
    cur = conn.cursor()
    # franchise_directory (per-season) gives full name + owner_name per franchise_id.
    cur.execute(
        """
        SELECT franchise_id, name, owner_name
          FROM franchise_directory
         WHERE league_id = ? AND season = ?
        """,
        (league_id, season),
    )
    directory = {fid: (name, owner) for fid, name, owner in cur.fetchall()}

    # franchise_nicknames (cross-season) gives commissioner-curated alias.
    cur.execute(
        """
        SELECT franchise_id, nickname
          FROM franchise_nicknames
         WHERE league_id = ?
        """,
        (league_id,),
    )
    nicknames = {fid: nick for fid, nick in cur.fetchall()}

    aliases_by_name: dict[str, list[str]] = {}
    for fid, (name, owner) in directory.items():
        if not name:
            continue
        aliases = _build_aliases_for_franchise(
            full_name=name,
            nickname=nicknames.get(fid),
            owner_name=owner,
        )
        aliases_by_name[name] = aliases
    return aliases_by_name


def load_franchise_id_to_name(
    conn: sqlite3.Connection, league_id: str, season: int
) -> dict[str, str]:
    """Build {franchise_id -> name} map for the given (league, season).

    Used by classify_fabrication_shape to resolve standings.franchise_id
    back to the name string that load_franchise_aliases keys by.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT franchise_id, name
          FROM franchise_directory
         WHERE league_id = ? AND season = ?
        """,
        (league_id, season),
    )
    return {fid: name for fid, name in cur.fetchall() if name}


# ── Output ──────────────────────────────────────────────────────────


def print_per_row(classifications: list[Classification], show_snippets: bool) -> None:
    print(
        "id\tseason\tweek\tattempt\ttemplate\tdirection\tcategory\tcanonical_headline"
    )
    for c in classifications:
        print(
            f"{c.row_id}\t{c.season}\t{c.week_index}\t{c.attempt}\t"
            f"{c.claim.template_id}\t{c.claim.direction}\t{c.category}\t"
            f"{c.claim.canonical_headline}"
        )
        if show_snippets and c.category in ("PARAPHRASE", "INVERTED") and c.snippet:
            snippet = c.snippet.replace("\n", " \u23CE ")
            print(f"    snippet: ...{snippet}...")


def print_aggregate(classifications: list[Classification]) -> None:
    cats = Counter(c.category for c in classifications)
    total = len(classifications)
    print()
    print("=== AGGREGATE ===")
    print(f"Total claims: {total}")
    if total == 0:
        print("(no STREAK claims detected — empty scope or angle parsing miss)")
        return
    for cat in ("VERBATIM", "PARAPHRASE", "INVERTED", "OMITTED"):
        count = cats.get(cat, 0)
        pct = (100.0 * count / total) if total else 0.0
        print(f"  {cat:11s}: {count:4d}  ({pct:5.1f}%)")
    # Per-template breakdown
    print()
    print("=== PER-TEMPLATE ===")
    by_template: dict[str, Counter] = {}
    for c in classifications:
        by_template.setdefault(c.claim.template_id, Counter())[c.category] += 1
    for template_id in sorted(by_template):
        tcounter = by_template[template_id]
        ttotal = sum(tcounter.values())
        line_parts = [f"{template_id} (n={ttotal})"]
        for cat in ("VERBATIM", "PARAPHRASE", "INVERTED", "OMITTED"):
            count = tcounter.get(cat, 0)
            line_parts.append(f"{cat[0]}={count}")
        print("  " + "  ".join(line_parts))


def print_fabrication_aggregate(shapes: list[FabricationShape]) -> None:
    """Aggregate counts across §10 Q1 fabrication-shape buckets."""
    counts = Counter(s.bucket for s in shapes)
    print()
    print("=== FABRICATION SHAPE BUCKETS (§10 Q1) ===")
    for bucket in (
        "RECORD_APPROACH",
        "STATUS_CLAIM_EVICTED",
        "STATUS_CLAIM_OMITTED",
        "STATUS_CLAIM_NOT_EVICTED",
        "MISS",
    ):
        print(f"  {bucket:26s}: {counts.get(bucket, 0):4d}")
    non_miss = sum(c for b, c in counts.items() if b != "MISS")
    print(f"  Total non-MISS entries: {non_miss}")
    print(f"  Total franchise-instances: {len(shapes)}")


# ── CLI ─────────────────────────────────────────────────────────────



# -- §10 Q1 Bug 1 specimen #2 hunt --------------------------------
#
# Cross-season scan for T9-LOSS-eligible (week, franchise) candidates
# from a franchise other than Brandon Knows Ball (fid=0010), whose
# specimen #1 is recorded in
# _observations/OBSERVATIONS_2026_05_06_T9_LOSS_POST_FIX_REVERIFY.md.
#
# Per the post-fix memo's diversity-trigger criterion, Bug 1
# (HEADLINE budget eviction) needs >=2 distinct franchises across
# >=2 distinct weeks of T9-LOSS angles generated-but-evicted before
# promotion to actionable thread. Specimen #1 is single-franchise
# (Brandon W11-W18 2025); specimen #2 must be cross-franchise.
#
# This scan walks every (season, week) tuple from
# WEEKLY_MATCHUP_RESULT events for the league, derives the
# canonical SeasonContextV1 and LeagueHistoryContextV1 (with
# temporal scoping per LEAGUE_HISTORY discipline), invokes
# _detect_streak_records, and reports any T9-LOSS angle whose
# franchise_id != "0010".
#
# Diagnostic-only. No production-path changes. No prompt_audit
# inspection -- this scans canonical data only and reports
# detector-eligibility, not generated-but-evicted (the eviction
# half is not measurable from canonical data alone since the recap
# lifecycle's budget filter operates on rendered output).
# Detector-eligibility is necessary for eviction; if zero
# detector-eligible non-Brandon specimens exist, eviction is
# trivially zero, and the diversity trigger cannot be satisfied
# by any prior season.

_BRANDON_FID = "0010"
_T9_LOSS_HEADLINE_RE = re.compile(
    r"is 1 loss from the league loss streak record",
    re.IGNORECASE,
)


def _enumerate_season_weeks(
    db_path: str, league_id: str
) -> list[tuple[int, int]]:
    """Return sorted (season, max_week) tuples for every season with
    WEEKLY_MATCHUP_RESULT events.
    """
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT
              season,
              MAX(CAST(json_extract(payload_json, '$.week') AS INTEGER)) AS max_week
            FROM v_canonical_best_events
            WHERE league_id = ?
              AND event_type = 'WEEKLY_MATCHUP_RESULT'
            GROUP BY season
            ORDER BY season
            """,
            (league_id,),
        ).fetchall()
    finally:
        conn.close()
    return [(int(s), int(w)) for s, w in rows if s is not None and w]


def _build_fname_resolver(
    db_path: str, league_id: str, season: int
):
    """Resolve franchise_id -> display name for a given season."""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT franchise_id, name
              FROM franchise_directory
             WHERE league_id = ? AND season = ?
            """,
            (league_id, season),
        ).fetchall()
    finally:
        conn.close()
    name_map = {fid: name for fid, name in rows}

    def fname(fid: str) -> str:
        return name_map.get(fid, fid)

    return fname


def _scan_t9_loss_cross_season(db_path: str, league_id: str) -> int:
    """Specimen #2 hunt. Returns 0 on success regardless of hit count
    (the hit count is the diagnostic output, not a pass/fail signal).
    """
    print("=" * 78)
    print("  SECTION 10 Q1 BUG 1 SPECIMEN #2 HUNT -- CROSS-SEASON T9-LOSS SCAN")
    print(f"  league_id={league_id}  excluded_fid={_BRANDON_FID} (Brandon Knows Ball)")
    print("=" * 78)

    season_weeks = _enumerate_season_weeks(db_path, league_id)
    if not season_weeks:
        print("\n  No WEEKLY_MATCHUP_RESULT data found for league.")
        return 0

    print(f"\n  Seasons in scope: {len(season_weeks)} ({season_weeks[0][0]}..{season_weeks[-1][0]})")
    total_weeks = sum(mw for _, mw in season_weeks)
    print(f"  (season, week) tuples to scan: {total_weeks}")

    specimens = []
    brandon_hits = []
    weeks_scanned = 0
    weeks_with_history = 0

    for season, max_week in season_weeks:
        fname = _build_fname_resolver(db_path, league_id, season)
        for week in range(1, max_week + 1):
            weeks_scanned += 1
            try:
                sctx = derive_season_context_v1(
                    db_path=db_path,
                    league_id=league_id,
                    season=season,
                    week_index=week,
                )
                hctx = derive_league_history_v1(
                    db_path=db_path,
                    league_id=league_id,
                    as_of_season=season,
                    as_of_week=week,
                )
            except Exception as exc:
                print(f"  WARN context derivation failed for season={season} week={week}: {exc}")
                continue

            if hctx is None or not hctx.is_multi_season:
                continue
            weeks_with_history += 1

            angles = _detect_streak_records(sctx, hctx, fname=fname)
            for a in angles:
                if not _T9_LOSS_HEADLINE_RE.search(a.headline):
                    continue
                if not a.franchise_ids:
                    continue
                fid = a.franchise_ids[0]
                if fid == _BRANDON_FID:
                    brandon_hits.append((season, week))
                    continue
                streak = next(
                    (r.current_streak for r in sctx.standings if r.franchise_id == fid),
                    0,
                )
                record_length = (
                    hctx.longest_loss_streak.length
                    if hctx.longest_loss_streak is not None else 0
                )
                specimens.append((
                    season, week, fid, a.headline,
                    int(streak), int(record_length),
                ))

    print(f"\n  Weeks scanned:                   {weeks_scanned}")
    print(f"  Weeks with multi-season history: {weeks_with_history}")
    print(f"  Brandon T9-LOSS hits (excluded): {len(brandon_hits)}")
    print(f"  Non-Brandon T9-LOSS specimens:   {len(specimens)}")

    if specimens:
        print("\n  -- NON-BRANDON SPECIMENS --")
        for season, week, fid, headline, streak, record_length in specimens:
            print(f"\n  season={season} week={week} fid={fid} streak={streak} record_length={record_length}")
            print(f"    headline: {headline!r}")
        print("\n  *** DIVERSITY TRIGGER SATISFIED -- Bug 1 promotes to actionable thread.")
    else:
        print(f"\n  No non-Brandon T9-LOSS specimens across {weeks_scanned} (season, week) tuples.")
        print("  Diversity trigger NOT satisfied; Bug 1 stays at single-specimen status.")

    if brandon_hits:
        hits_str = ", ".join(f"{s}W{w}" for s, w in brandon_hits)
        print(f"\n  Brandon hit weeks (excluded; for completeness): {hits_str}")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Step 3.2 streak verb diagnostic harness."
    )
    parser.add_argument("--db", required=True, help="Path to .sqlite database.")
    parser.add_argument("--league-id", required=True, help="League ID, e.g. 70985.")
    parser.add_argument(
        "--scope",
        required=True,
        choices=("last10-approved", "week", "hunt-t9-loss-cross-season"),
        help="Scope selector.",
    )
    parser.add_argument("--season", type=int, default=None, help="Required for --scope week.")
    parser.add_argument("--week-index", type=int, default=None, help="Required for --scope week.")
    parser.add_argument(
        "--show-snippets",
        action="store_true",
        help="Print prose snippets for non-VERBATIM classifications.",
    )
    args = parser.parse_args(argv)

    if args.scope == "week" and (args.season is None or args.week_index is None):
        parser.error("--scope week requires --season and --week-index.")

    if args.scope == "hunt-t9-loss-cross-season":
        return _scan_t9_loss_cross_season(args.db, args.league_id)

    conn = sqlite3.connect(args.db)
    conn.row_factory = None
    try:
        if args.scope == "last10-approved":
            rows = fetch_rows_last10_approved(conn, args.league_id)
        else:
            rows = fetch_rows_week(conn, args.league_id, args.season, args.week_index)

        # Pre-load alias maps and fid→name maps per season encountered
        # in the row set. Both are used by the §10 Q1 fabrication-shape
        # classifier; aliases_by_season is also used by the per-claim
        # classifier (existing behavior).
        seasons_seen = {row.season for row in rows}
        aliases_by_season: dict[int, dict[str, list[str]]] = {}
        fid_to_name_by_season: dict[int, dict[str, str]] = {}
        for season in seasons_seen:
            aliases_by_season[season] = load_franchise_aliases(
                conn, args.league_id, season
            )
            fid_to_name_by_season[season] = load_franchise_id_to_name(
                conn, args.league_id, season
            )
    finally:
        conn.close()

    classifications: list[Classification] = []
    fabrications: list[FabricationShape] = []
    # Cache derived contexts per (season, week_index) to amortize cost
    # across rows in the same week (e.g. multiple attempt rows at the
    # same prompt-audit week get one context derivation).
    context_cache: dict[tuple[int, int], tuple[Any, Any]] = {}

    for row in rows:
        season_aliases = aliases_by_season.get(row.season, {})
        season_fid_to_name = fid_to_name_by_season.get(row.season, {})

        # Existing per-claim classification (T1/T2/T3/T4/T8/T9-WIN/T10).
        for claim in parse_streak_claims(row.narrative_angles_text):
            aliases = season_aliases.get(
                claim.franchise_name, [claim.franchise_name]
            )
            category, snippet = classify(claim, row.narrative_draft, aliases)
            classifications.append(Classification(
                row_id=row.id,
                season=row.season,
                week_index=row.week_index,
                attempt=row.attempt,
                claim=claim,
                category=category,
                snippet=snippet,
            ))

        # §10 Q1 fabrication-shape classification (per row, per franchise).
        # Counterfactual angle reconstruction requires canonical context;
        # the cache amortizes the derive cost across rows in the same week.
        key = (row.season, row.week_index)
        if key not in context_cache:
            sctx = derive_season_context_v1(
                db_path=args.db,
                league_id=args.league_id,
                season=row.season,
                week_index=row.week_index,
            )
            hctx = derive_league_history_v1(
                db_path=args.db,
                league_id=args.league_id,
                as_of_season=row.season,
                as_of_week=row.week_index,
            )
            context_cache[key] = (sctx, hctx)
        sctx, hctx = context_cache[key]

        longest_loss_record = (
            hctx.longest_loss_streak.length
            if hctx is not None and hctx.longest_loss_streak is not None
            else None
        )
        is_multi_season = bool(hctx is not None and hctx.is_multi_season)

        fabrications.extend(classify_fabrication_shape(
            row=row,
            standings=sctx.standings,
            longest_loss_record=longest_loss_record,
            is_multi_season=is_multi_season,
            fid_to_name=season_fid_to_name,
            aliases_by_name=season_aliases,
        ))

    print_per_row(classifications, show_snippets=args.show_snippets)
    print_aggregate(classifications)
    print_fabrication_aggregate(fabrications)
    return 0


if __name__ == "__main__":
    sys.exit(main())
