"""Narrative presentation lint (v1) — standalone deterministic structural lint.

Implements Narrative Presentation Spec v1.0 (docs/Narrative_Presentation_Spec_v1_0.md),
Units E1.5b (gate half of finding R5) + 1.7b (reconciled to the spec masthead; R5 closed).

Layer law (spec section 1): presentation lives at the derived/render layer only.
This module creates, modifies, or reinterprets NO fact. It reads recap artifact
text and reports structural findings. It is STANDALONE (D-F): the recap verifier's
factual contract is untouched and this module does not import it.

Severity model (spec section 4): SOFT rules flag for the Office review checklist
and never block. Exactly one HARD rule — L2 facts-block byte-identity — whose
failure blocks pre-approval.

Pure: no DB I/O, no network, no clock. The L2 canonical reference is supplied by
the caller (which has DB access), keeping this module deterministic and testable.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

FACTS_HEADER = "What happened this week:"

def render_transactions_block_v1(
    bullets: list[str], *, bullet_prefix: str = "- "
) -> str:
    """Render the S5 transactions block from deterministic bullet payloads.

    Returns the block from the header line through the final bullet (no leading or
    trailing newline). Single formatter for both forms:
      - clean distributed form (spec S5): bullet_prefix='- ' (default).
      - internal lifecycle rendered_text: bullet_prefix='  - '.
    Used to build the clean artifact (publication path) and the L2 byte reference,
    so artifact and reference are byte-identical by construction for a given form.
    """
    lines = [FACTS_HEADER]
    lines.extend(f"{bullet_prefix}{b}" for b in bullets)
    return "\n".join(lines)


class Severity(str, Enum):
    SOFT = "SOFT"
    HARD = "HARD"


@dataclass(frozen=True)
class Finding:
    rule: str          # "L1".."L5"
    severity: Severity
    ok: bool           # True = rule satisfied; False = flagged
    message: str


@dataclass(frozen=True)
class PresentationLintReport:
    findings: list[Finding] = field(default_factory=list)

    @property
    def hard_failed(self) -> bool:
        """True iff any HARD rule is flagged. The only blocking condition."""
        return any(f.severity is Severity.HARD and not f.ok for f in self.findings)

    @property
    def soft_flags(self) -> list[Finding]:
        return [f for f in self.findings if f.severity is Severity.SOFT and not f.ok]


@dataclass(frozen=True)
class _Body:
    """Artifact body below the YAML frontmatter, segmented per spec section 2."""

    text: str
    prose_lines: list[str]      # S1-S3 region lines (before the S4 separator)
    facts_block: str | None     # S5 span: FACTS_HEADER through final "- " bullet, or None


def strip_frontmatter(artifact_text: str) -> str:
    """Return the artifact body below a leading YAML frontmatter block.

    Frontmatter is a leading '---' line through the next '---' line (lifecycle-
    owned; out of presentation scope per spec section 2). If absent, the text is
    returned unchanged.
    """
    lines = artifact_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return artifact_text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[i + 1:]).lstrip("\n")
    return artifact_text  # unterminated frontmatter → treat whole text as body


def extract_facts_block(body_text: str) -> str | None:
    """Extract the S5 transactions span: FACTS_HEADER through the final '- ' bullet.

    Returns None if the header is absent (quiet-week omission is permitted, spec
    section 5). Leading whitespace on bullet lines is preserved verbatim — byte
    identity (L2) compares exactly what is present.
    """
    lines = body_text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if ln.strip() == FACTS_HEADER:
            start = i
            break
    if start is None:
        return None
    # Last line that is a bullet ("- " after optional leading spaces).
    end = start
    for i in range(start + 1, len(lines)):
        if lines[i].lstrip().startswith("- "):
            end = i
    return "\n".join(lines[start:end + 1])


def _segment(artifact_text: str) -> _Body:
    body = strip_frontmatter(artifact_text)
    facts = extract_facts_block(body)
    if facts is not None:
        prose_region = body.split(FACTS_HEADER, 1)[0]
    else:
        prose_region = body
    # Drop the S4 separator ("---") and blank lines from the prose region tail.
    prose_lines = [ln for ln in prose_region.splitlines()]
    return _Body(text=body, prose_lines=prose_lines, facts_block=facts)


def _title_pattern(season: int, week_index: int) -> re.Pattern[str]:
    # Spec section 3 masthead: "PFL BUDDIES — WEEK {week} — {season}" (all caps, em-dash
    # separators). Accept em dash or the ascii "--" fallback. (Unit 1.7b replaced the pre-R5
    # "PFL Buddies — Season N, Week W" title with its setext "=" underline.)
    dash = r"(?:—|--)"
    return re.compile(
        rf"^PFL BUDDIES {dash} WEEK {week_index} {dash} {season}\s*$"
    )


def _paragraphs(prose_lines: list[str]) -> list[str]:
    """Group consecutive non-blank prose lines into paragraphs, excluding the
    setext underline (a run of '=') and the S4 separator ('---')."""
    paras: list[str] = []
    cur: list[str] = []
    for ln in prose_lines:
        s = ln.strip()
        is_underline = bool(s) and set(s) <= {"="}
        is_separator = bool(s) and set(s) <= {"-"} and len(s) >= 3
        if not s or is_underline or is_separator:
            if cur:
                paras.append(" ".join(cur).strip())
                cur = []
            continue
        cur.append(s)
    if cur:
        paras.append(" ".join(cur).strip())
    # First paragraph is the title line; presentation paragraphs are the rest.
    return paras[1:] if paras else paras


_SENTENCE_END = re.compile(r"[.!?]+(?:\s|$)")
_MARKUP_PATTERNS = (
    ("#", re.compile(r"(?m)^\s*#")),
    ("**", re.compile(r"\*\*")),
    ("__", re.compile(r"__")),
    ("`", re.compile(r"`")),
    ("[](url)", re.compile(r"\[[^\]]+\]\([^)]+\)")),
    # R5 REGRESSION GUARD (Unit 1.7b): the setext "=" underline (markdown H1) is the W7 v27
    # "markdown chrome in the group text" defect that started this whole arc. This pattern
    # exists so that class of artifact can never silently return to the distributed form.
    ("===== (setext underline)", re.compile(r"(?m)^[ \t]*={3,}[ \t]*$")),
)


def _count_sentences(paragraph: str) -> int:
    return len([m for m in _SENTENCE_END.findall(paragraph)]) or (1 if paragraph else 0)


def lint_presentation(
    artifact_text: str,
    *,
    season: int,
    week_index: int,
    channel: str = "plain_text",
    canonical_facts_block: str | None = None,
) -> PresentationLintReport:
    """Lint a recap artifact against the presentation spec.

    canonical_facts_block: the lifecycle-emitted transactions block for this
    artifact version (byte reference for L2). When None, L2 reports "not
    evaluated" (ok=True) rather than failing — absence of a reference is not a
    facts-block modification.
    """
    body = _segment(artifact_text)
    findings: list[Finding] = []

    # L1 SOFT — title present.
    first_nonempty = next((ln for ln in body.prose_lines if ln.strip()), "")
    l1_ok = bool(_title_pattern(season, week_index).match(first_nonempty.strip()))
    findings.append(Finding(
        "L1", Severity.SOFT, l1_ok,
        "Masthead present" if l1_ok
        else f"Masthead line does not match 'PFL BUDDIES — WEEK {week_index} — {season}'",
    ))

    # L2 HARD — facts block byte-identity against the canonical reference.
    if canonical_facts_block is None:
        findings.append(Finding(
            "L2", Severity.HARD, True,
            "Facts block byte-identity not evaluated (no canonical reference supplied)",
        ))
    else:
        l2_ok = body.facts_block is not None and body.facts_block == canonical_facts_block
        findings.append(Finding(
            "L2", Severity.HARD, l2_ok,
            "Facts block byte-identical to lifecycle emission" if l2_ok
            else "Facts block differs from the lifecycle-emitted transactions block "
                 "(facts must be byte-identical; this is the one hard condition)",
        ))

    # L3 SOFT — paragraph bounds (2-7 sentences per S2/S3 paragraph).
    paras = _paragraphs(body.prose_lines)
    bad = [i + 1 for i, p in enumerate(paras) if not (2 <= _count_sentences(p) <= 7)]
    findings.append(Finding(
        "L3", Severity.SOFT, not bad,
        "Paragraph bounds (2-7 sentences) ok" if not bad
        else f"Paragraph(s) {bad} outside 2-7 sentences",
    ))

    # L4 SOFT — channel markup hygiene (plain_text only).
    if channel == "plain_text":
        prose = "\n".join(body.prose_lines)
        hits = [label for label, pat in _MARKUP_PATTERNS if pat.search(prose)]
        findings.append(Finding(
            "L4", Severity.SOFT, not hits,
            "No disallowed markup for plain_text" if not hits
            else f"Disallowed plain_text markup present: {', '.join(hits)}",
        ))
    else:
        findings.append(Finding(
            "L4", Severity.SOFT, True,
            f"Markup hygiene not applicable to channel '{channel}'",
        ))

    # L5 SOFT — structure order: facts block, when present, follows all prose;
    # nothing after the final bullet.
    l5_ok = True
    msg = "Structure order ok"
    if body.facts_block is not None:
        idx = body.text.find(FACTS_HEADER)
        tail = body.text[idx + len(body.facts_block):] if idx >= 0 else ""
        # Everything after the facts block must be whitespace only.
        after_block = body.text[idx:].split(body.facts_block, 1)
        trailing = after_block[1] if len(after_block) > 1 else tail
        if trailing.strip():
            l5_ok = False
            msg = "Content follows the final transactions bullet"
    findings.append(Finding("L5", Severity.SOFT, l5_ok, msg))

    return PresentationLintReport(findings=findings)
