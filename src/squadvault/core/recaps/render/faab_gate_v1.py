"""Deterministic post-generation FAAB gate (v1).

Enforces the canonical per-player FAAB allowlist on a generated narrative as a
deterministic final pass — a hard gate, not a prompt request. Motivated by the
residual-fabrication remediation (OBSERVATIONS_2026_06_09_RESIDUAL_REMEDIATION_
VERBATIM_RESULTS): FAAB fabrication is instruction-resistant (copy-only prompt
discipline did not move it; ~flat at 43% of samples). The proven lever is
enforcement, not instruction — so this module strips/blocks FAAB dollar figures
that are not on the canonical allowlist rather than asking the model to behave.

Relationship to the recap verifier (founder pick, defense-in-depth):
this is a STANDALONE backstop that runs ALONGSIDE verify_faab_claims, not a
replacement. It does NOT import the verifier and leaves the verifier's factual
contract frozen. It re-applies the same per-player allowlist contract (Category 8)
independently, so it also covers the narrative on paths where the verifier did
not gate it — notably the verifier-exception path, where an unverified draft is
otherwise kept. The detection contract is mirrored verbatim from Category 8 so
the two never disagree on what counts as an out-of-allowlist FAAB claim.

Behavior (founder pick, hybrid):
  - strip if clean: excise the sentence(s) carrying an out-of-allowlist FAAB
    figure when removal leaves substantive prose and no violation remains;
  - else block: when stripping would gut the narrative (the bad FAAB claim is
    effectively the whole story), signal the caller to fall back to facts-only.
Silence over speculation either way: no out-of-allowlist FAAB figure ships.

Layer law (mirrors presentation_lint_v1): this lives at the render layer and
creates, modifies, or reinterprets NO fact. The allowlist is canonical truth
loaded once by the caller (which has DB access) and supplied to a pure,
deterministic, DB-free core — keeping the gate testable without a database.
The facts block (deterministic, L2 byte-identity-protected) is never touched;
the gate operates only on the model-authored narrative.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from squadvault.core.storage.session import DatabaseSession

# ── Detection contract (mirrors recap_verifier_v1 Category 8 verbatim) ───
# Kept independent (no verifier import) but byte-for-byte aligned so the gate
# and the verifier never disagree about what is an out-of-allowlist FAAB claim.
_FAAB_DOLLAR_PATTERN = re.compile(r"\$(\d+(?:\.\d{1,2})?)")
_FAAB_KEYWORD_PATTERN = re.compile(
    r"\b(?:faab|waiver|pickup|pick-up|claim(?:ed)?|acquisition|investment|grabbed|snagged|spent|bid)s?\b",
    re.IGNORECASE,
)
_DRAFT_CONTEXT_PATTERN = re.compile(r"\bdraft\b", re.IGNORECASE)
_FAAB_KEYWORD_WINDOW = 30
_NAME_SEARCH_WINDOW = 100
_MIN_NAME_LEN = 5           # verifier skips names this short or shorter
_BID_TOLERANCE = 1.0        # rounding tolerance, matches the verifier

# Strip-vs-block threshold: stripping is "clean" only if at least this many
# non-whitespace characters of prose survive removal of the violating
# sentence(s). Below this the FAAB claim was effectively the whole narrative,
# so we block to facts-only rather than ship a gutted stub.
_MIN_SURVIVING_PROSE_CHARS = 40

# Sentence boundary for strip granularity (matches presentation_lint's splitter).
_SENTENCE_BOUNDARY = re.compile(r"[.!?]+(?:\s+|$)")


@dataclass(frozen=True)
class FaabAllowlist:
    """Canonical per-player FAAB allowlist for one (league, season).

    name_to_pid maps lowercased display-name variants to player_id for the
    FULL player universe (not just FAAB-acquired players) — phantom detection
    requires resolving a salient non-acquired star to find it has no bid.
    pid_to_amounts maps player_id to the canonical WAIVER_BID_AWARDED amounts.
    """

    name_to_pid: dict[str, str]
    pid_to_amounts: dict[str, tuple[float, ...]]


@dataclass(frozen=True)
class _Violation:
    dollar_start: int
    dollar_end: int
    claimed: float
    player_name: str
    kind: str            # "phantom" (no bid record) | "mispair" (wrong amount)


@dataclass(frozen=True)
class FaabGateOutcome:
    """Result of applying the gate to a narrative.

    action:
      - "clean"    — no out-of-allowlist FAAB figure; text unchanged.
      - "stripped" — violating sentence(s) excised; text is the survivor.
      - "blocked"  — stripping would gut the narrative; text is "" and the
                     caller must fall back to facts-only.
    """

    action: str
    text: str
    violations: tuple[str, ...]
    removed_sentences: tuple[str, ...]


# ── Canonical allowlist loader (the only DB-touching surface) ────────────


def load_faab_allowlist(
    db_path: str, league_id: str, season: int,
) -> FaabAllowlist:
    """Build the canonical FAAB allowlist for a (league, season).

    Mirrors the verifier's two private loaders (player_directory names and
    WAIVER_BID_AWARDED bids) with independent SQL so the gate stays standalone.
    """
    name_to_pid: dict[str, str] = {}
    pid_to_amounts: dict[str, list[float]] = {}

    with DatabaseSession(db_path) as con:
        name_rows = con.execute(
            """SELECT player_id, name FROM player_directory
               WHERE league_id = ? ORDER BY season DESC""",
            (str(league_id),),
        ).fetchall()
        bid_rows = con.execute(
            """SELECT payload_json
               FROM v_canonical_best_events
               WHERE league_id = ? AND season = ?
                 AND event_type = 'WAIVER_BID_AWARDED'
               ORDER BY occurred_at ASC NULLS LAST""",
            (str(league_id), int(season)),
        ).fetchall()

    # Display name -> player_id (first writer wins; ORDER BY season DESC keeps
    # the most recent name). Build the same "Last, First" -> "first last"
    # variant the verifier resolves against.
    for row in name_rows:
        pid = str(row[0]).strip()
        display = str(row[1]).strip() if row[1] else ""
        if not pid or not display:
            continue
        if ", " in display:
            last, first = display.split(", ", 1)
            key = f"{first} {last}".strip().lower()
        else:
            key = display.strip().lower()
        if key and key not in name_to_pid:
            name_to_pid[key] = pid

    # player_id -> canonical bid amounts (a player may have several).
    for row in bid_rows:
        try:
            p = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        except (ValueError, TypeError):
            continue
        if not isinstance(p, dict):
            continue
        pid = str(p.get("player_id", "")).strip()
        if not pid:
            added = p.get("players_added_ids")
            if isinstance(added, str) and added.strip():
                pid = added.split(",")[0].strip()
            elif isinstance(added, list) and added:
                pid = str(added[0]).strip()
        if not pid:
            continue
        try:
            amount = float(p.get("bid_amount", 0))
        except (ValueError, TypeError):
            continue
        if amount <= 0:
            continue
        pid_to_amounts.setdefault(pid, []).append(amount)

    return FaabAllowlist(
        name_to_pid=name_to_pid,
        pid_to_amounts={k: tuple(v) for k, v in pid_to_amounts.items()},
    )


# ── Pure detection + strip core (no DB, no clock, no network) ────────────


def _find_violations(text: str, allowlist: FaabAllowlist) -> list[_Violation]:
    """Return out-of-allowlist FAAB claims in text (verifier Category 8 logic)."""
    violations: list[_Violation] = []
    text_lower = text.lower()
    checked: set[tuple[str, float]] = set()

    for m in _FAAB_DOLLAR_PATTERN.finditer(text):
        try:
            claimed = float(m.group(1))
        except ValueError:
            continue

        kw_start = max(0, m.start() - _FAAB_KEYWORD_WINDOW)
        kw_end = min(len(text), m.end() + _FAAB_KEYWORD_WINDOW)
        kw_context = text[kw_start:kw_end]
        if not _FAAB_KEYWORD_PATTERN.search(kw_context):
            continue
        if _DRAFT_CONTEXT_PATTERN.search(kw_context):
            continue

        search_start = max(0, m.start() - _NAME_SEARCH_WINDOW)
        search_end = min(len(text_lower), m.end() + _NAME_SEARCH_WINDOW)
        search_context = text_lower[search_start:search_end]

        best_name: str | None = None
        best_dist = _NAME_SEARCH_WINDOW + 1
        for display_name in allowlist.name_to_pid:
            if len(display_name) <= _MIN_NAME_LEN:
                continue
            idx = search_context.find(display_name)
            if idx >= 0:
                dollar_offset = m.start() - search_start
                dist = abs(idx - dollar_offset)
                if dist < best_dist:
                    best_dist = dist
                    best_name = display_name
        if best_name is None:
            continue

        key = (best_name, claimed)
        if key in checked:
            continue
        checked.add(key)

        pid = allowlist.name_to_pid[best_name]
        canonical = allowlist.pid_to_amounts.get(pid, ())
        if not canonical:
            violations.append(_Violation(
                m.start(), m.end(), claimed, best_name.title(), "phantom",
            ))
        elif not any(abs(claimed - ca) <= _BID_TOLERANCE for ca in canonical):
            violations.append(_Violation(
                m.start(), m.end(), claimed, best_name.title(), "mispair",
            ))

    return violations


def _sentence_spans(text: str) -> list[tuple[int, int]]:
    """Segment text into (start, end) spans covering it whole, split on .!? runs."""
    spans: list[tuple[int, int]] = []
    start = 0
    for m in _SENTENCE_BOUNDARY.finditer(text):
        spans.append((start, m.end()))
        start = m.end()
    if start < len(text):
        spans.append((start, len(text)))
    return spans


def _normalize(text: str) -> str:
    """Collapse the whitespace seams left by removing a sentence."""
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r" *\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def apply_faab_gate(
    narrative_text: str, *, allowlist: FaabAllowlist,
) -> FaabGateOutcome:
    """Apply the FAAB gate to a model-authored narrative.

    Pure and deterministic given the allowlist. Strips the sentence(s) carrying
    an out-of-allowlist FAAB figure when substantive prose survives; otherwise
    blocks (action="blocked", text="") so the caller falls back to facts-only.
    """
    violations = _find_violations(narrative_text, allowlist)
    if not violations:
        return FaabGateOutcome("clean", narrative_text, (), ())

    descrs = tuple(
        f"${v.claimed:.0f} {v.kind} -> {v.player_name}" for v in violations
    )

    # Identify the sentence span carrying each violating dollar figure.
    spans = _sentence_spans(narrative_text)
    bad_span_idx: set[int] = set()
    for v in violations:
        for i, (s, e) in enumerate(spans):
            if s <= v.dollar_start < e:
                bad_span_idx.add(i)
                break

    removed = tuple(
        narrative_text[spans[i][0]:spans[i][1]].strip()
        for i in sorted(bad_span_idx)
    )
    survivor = _normalize(
        "".join(
            narrative_text[s:e]
            for i, (s, e) in enumerate(spans)
            if i not in bad_span_idx
        )
    )

    # Block unless the survivor is substantive AND fully clean (re-checking the
    # survivor guards against a figure the sentence segmentation failed to isolate).
    if (
        len(survivor) >= _MIN_SURVIVING_PROSE_CHARS
        and not _find_violations(survivor, allowlist)
    ):
        return FaabGateOutcome("stripped", survivor, descrs, removed)
    return FaabGateOutcome("blocked", "", descrs, removed)
