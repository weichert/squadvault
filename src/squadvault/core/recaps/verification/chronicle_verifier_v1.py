"""Chronicle Verifier v1 -- post-generation verification gate for RIVALRY_CHRONICLE_V1.

Contract:
- Deterministic: identical inputs produce identical verification results.
- Non-modifying: verifies only; never edits, rewrites, or filters.
- No inference: every check is a binary comparison or structural assertion.

Verification Categories (V1):
1. STRUCTURE   (HARD) -- mandatory sections present and non-empty.
2. TRACE       (HARD) -- trace block contains required fields; fingerprint count
                          matches facts entry count.
3. SCORE_CLAIM (HARD) -- every score pattern in the narrative (## Chronicle)
                          appears verbatim in the ## Head-to-Head Results block.
4. RESTRAINT   (SOFT) -- narrative does not contain banned speculation phrases.

Human approval is the hard governance gate. This verifier is the automated
pre-approval quality check; it never substitutes for human review.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ── Output dataclasses ───────────────────────────────────────────────

@dataclass(frozen=True)
class ChronicleVerificationFailure:
    category: str   # "STRUCTURE", "TRACE", "SCORE_CLAIM", "RESTRAINT"
    severity: str   # "HARD" or "SOFT"
    claim: str      # the extracted claim or section name
    evidence: str   # what the check found


@dataclass(frozen=True)
class ChronicleVerificationResult:
    passed: bool
    hard_failures: tuple[ChronicleVerificationFailure, ...]
    soft_failures: tuple[ChronicleVerificationFailure, ...]
    checks_run: int

    @property
    def hard_failure_count(self) -> int:
        return len(self.hard_failures)

    @property
    def soft_failure_count(self) -> int:
        return len(self.soft_failures)


# ── Section parsing ──────────────────────────────────────────────────

_MANDATORY_SECTIONS = [
    "Head-to-Head Results",
    "Trace",
    "Disclosures",
]

_SCORE_PATTERN = re.compile(r"\b(\d{2,3}\.\d{2})-(\d{2,3}\.\d{2})\b")

_BANNED_PHRASES: tuple[str, ...] = (
    "trending",
    "momentum",
    "on a roll",
    "heating up",
    "cooling off",
    "predicted",
    "will win",
    "will lose",
    "guaranteed",
    "is destined",
    "could win",
    "might win",
    "should win",
    "better than ever",
    "worst ever",
    "all-time best",
    "all-time worst",
    "greatest rivalry",
    "dominant",
    "dominated",
)

_TRACE_REQUIRED_FIELDS = (
    "team_a_id",
    "team_b_id",
    "facts_block_hash",
)


def _extract_section(text: str, heading: str) -> str | None:
    """Extract content of a ## heading section. Returns None if absent."""
    pattern = re.compile(
        r"^## " + re.escape(heading) + r"\s*$",
        re.MULTILINE,
    )
    m = pattern.search(text)
    if not m:
        return None
    start = m.end()
    # Next ## heading or end of text
    next_h = re.search(r"^## ", text[start:], re.MULTILINE)
    end = start + next_h.start() if next_h else len(text)
    return text[start:end].strip()


def _count_hh_entries(hh_block: str) -> int:
    """Count matchup entries (lines starting with '- Season') in the H2H block."""
    return sum(1 for line in hh_block.splitlines() if line.strip().startswith("- Season"))


def _count_fingerprints(trace_block: str) -> int:
    """Count canonical_event_fingerprint lines in the trace block."""
    return sum(
        1 for line in trace_block.splitlines()
        if re.search(r"WEEKLY_MATCHUP_RESULT:", line)
    )


def _scores_in_text(text: str) -> set[str]:
    """Extract all 'NNN.NN-NNN.NN' score strings from text."""
    return {m.group(0) for m in _SCORE_PATTERN.finditer(text)}


# ── Check functions ──────────────────────────────────────────────────

def _check_structure(
    text: str,
) -> list[ChronicleVerificationFailure]:
    failures: list[ChronicleVerificationFailure] = []
    for section in _MANDATORY_SECTIONS:
        content = _extract_section(text, section)
        if content is None:
            failures.append(ChronicleVerificationFailure(
                category="STRUCTURE",
                severity="HARD",
                claim=f"## {section}",
                evidence="Section heading absent from rendered text.",
            ))
        elif not content.strip():
            failures.append(ChronicleVerificationFailure(
                category="STRUCTURE",
                severity="HARD",
                claim=f"## {section}",
                evidence="Section present but contains no content.",
            ))
    return failures


def _check_trace(
    text: str,
    hh_block: str | None,
) -> list[ChronicleVerificationFailure]:
    failures: list[ChronicleVerificationFailure] = []
    trace_block = _extract_section(text, "Trace")
    if trace_block is None:
        # Already caught by STRUCTURE check; skip double-reporting.
        return failures

    # Required fields present
    for field in _TRACE_REQUIRED_FIELDS:
        if f"{field}:" not in trace_block:
            failures.append(ChronicleVerificationFailure(
                category="TRACE",
                severity="HARD",
                claim=f"trace field: {field}",
                evidence="Required trace field absent from ## Trace section.",
            ))

    # Fingerprint count matches H2H entry count
    if hh_block is not None:
        hh_count = _count_hh_entries(hh_block)
        fp_count = _count_fingerprints(trace_block)
        if hh_count != fp_count:
            failures.append(ChronicleVerificationFailure(
                category="TRACE",
                severity="HARD",
                claim=f"fingerprint count: {fp_count} vs H2H entries: {hh_count}",
                evidence=(
                    f"## Trace has {fp_count} canonical_event_fingerprint(s) but "
                    f"## Head-to-Head Results has {hh_count} matchup entries. "
                    f"Counts must match."
                ),
            ))

    return failures


def _check_score_claims(
    hh_block: str | None,
    narrative_block: str | None,
) -> list[ChronicleVerificationFailure]:
    """Every score in the narrative must appear verbatim in the H2H facts block."""
    if narrative_block is None or not narrative_block.strip():
        return []  # No narrative; nothing to check.
    if hh_block is None:
        return []  # H2H absent; caught by STRUCTURE check.

    narrative_scores = _scores_in_text(narrative_block)
    if not narrative_scores:
        return []

    hh_scores = _scores_in_text(hh_block)

    failures: list[ChronicleVerificationFailure] = []
    for score in sorted(narrative_scores):
        if score not in hh_scores:
            failures.append(ChronicleVerificationFailure(
                category="SCORE_CLAIM",
                severity="HARD",
                claim=f"score in narrative: {score}",
                evidence=(
                    f"Score '{score}' appears in ## Chronicle narrative but is not "
                    f"present in ## Head-to-Head Results. "
                    f"Scores in H2H block: {sorted(hh_scores) or '(none)'}."
                ),
            ))
    return failures


def _check_restraint(
    narrative_block: str | None,
) -> list[ChronicleVerificationFailure]:
    """Narrative must not contain banned speculation or trend-claim phrases."""
    if narrative_block is None or not narrative_block.strip():
        return []

    lower = narrative_block.lower()
    failures: list[ChronicleVerificationFailure] = []
    for phrase in _BANNED_PHRASES:
        if phrase in lower:
            # Find the surrounding context (up to 80 chars)
            idx = lower.index(phrase)
            ctx_start = max(0, idx - 30)
            ctx_end = min(len(lower), idx + len(phrase) + 30)
            context = narrative_block[ctx_start:ctx_end].replace("\n", " ").strip()
            failures.append(ChronicleVerificationFailure(
                category="RESTRAINT",
                severity="SOFT",
                claim=f"banned phrase: '{phrase}'",
                evidence=f"Found in narrative: '...{context}...'",
            ))
    return failures


# ── Public API ───────────────────────────────────────────────────────

def verify_chronicle_v1(rendered_text: str) -> ChronicleVerificationResult:
    """Verify a RIVALRY_CHRONICLE_V1 rendered_text.

    Returns a ChronicleVerificationResult. Does not modify the input.
    Deterministic: identical inputs produce identical results.

    Args:
        rendered_text: The full rendered text of a RIVALRY_CHRONICLE_V1 artifact.

    Returns:
        ChronicleVerificationResult with hard_failures and soft_failures.
        passed=True iff hard_failure_count == 0.
    """
    hard: list[ChronicleVerificationFailure] = []
    soft: list[ChronicleVerificationFailure] = []
    checks_run = 0

    # STRUCTURE
    hard.extend(_check_structure(rendered_text))
    checks_run += len(_MANDATORY_SECTIONS)

    hh_block = _extract_section(rendered_text, "Head-to-Head Results")
    narrative_block = _extract_section(rendered_text, "Chronicle")

    # TRACE
    trace_failures = _check_trace(rendered_text, hh_block)
    hard.extend(trace_failures)
    checks_run += len(_TRACE_REQUIRED_FIELDS) + 1  # fields + count check

    # SCORE_CLAIM
    score_failures = _check_score_claims(hh_block, narrative_block)
    hard.extend(score_failures)
    checks_run += 1

    # RESTRAINT
    restraint_failures = _check_restraint(narrative_block)
    soft.extend(restraint_failures)
    checks_run += len(_BANNED_PHRASES)

    return ChronicleVerificationResult(
        passed=len(hard) == 0,
        hard_failures=tuple(hard),
        soft_failures=tuple(soft),
        checks_run=checks_run,
    )
