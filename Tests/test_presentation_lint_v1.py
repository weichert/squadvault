"""Tests for the E1.5b narrative presentation lint (closes R5 gate half).

Covers the pure lint (L1-L5 per Narrative Presentation Spec v1.0), the shared
transactions-block formatter, and the clean plain_text assembler. No DB needed —
the L2 canonical reference is passed directly.
"""
from __future__ import annotations

from squadvault.core.recaps.render.plain_text_recap_v1 import render_plain_text_recap_v1
from squadvault.core.recaps.render.presentation_lint_v1 import (
    Severity,
    extract_facts_block,
    lint_presentation,
    render_transactions_block_v1,
    strip_frontmatter,
)

SEASON, WEEK = 2025, 7
_BULLETS = ["Stu's Crew added Miller, Kendre (RB, NOS) (free agent).",
            "Purple Haze won Reichard, Will (PK, MIN) for $1 on waivers."]


def _clean_recap(bullets: list[str] | None = None, narrative: str | None = None) -> str:
    narrative = narrative or (
        "The Playmakers put up 192.15 to demolish Steve. It was the week's most "
        "lopsided result.\n\nMiller extended his streak to five. He sits atop the "
        "standings now."
    )
    return render_plain_text_recap_v1(
        narrative=narrative,
        bullets=_BULLETS if bullets is None else bullets,
        season=SEASON,
        week_index=WEEK,
    )


def _canonical(bullets: list[str] | None = None) -> str:
    return render_transactions_block_v1(_BULLETS if bullets is None else bullets)


class TestCleanArtifact:
    def test_clean_passes_all_rules(self) -> None:
        rep = lint_presentation(
            _clean_recap(), season=SEASON, week_index=WEEK,
            channel="plain_text", canonical_facts_block=_canonical(),
        )
        assert not rep.hard_failed
        assert rep.soft_flags == []
        assert {f.rule for f in rep.findings} == {"L1", "L2", "L3", "L4", "L5"}


class TestL2HardRule:
    def test_tampered_facts_block_hard_fails(self) -> None:
        clean = _clean_recap()
        tampered = clean.replace("for $1 on waivers", "for $999 on waivers")
        rep = lint_presentation(
            tampered, season=SEASON, week_index=WEEK,
            channel="plain_text", canonical_facts_block=_canonical(),
        )
        assert rep.hard_failed
        l2 = next(f for f in rep.findings if f.rule == "L2")
        assert l2.severity is Severity.HARD and not l2.ok

    def test_missing_canonical_reference_does_not_block(self) -> None:
        rep = lint_presentation(
            _clean_recap(), season=SEASON, week_index=WEEK, canonical_facts_block=None,
        )
        assert not rep.hard_failed
        assert next(f for f in rep.findings if f.rule == "L2").ok

    def test_deleted_facts_block_hard_fails(self) -> None:
        # Quiet-week artifact (no S5) but canonical has transactions → modification.
        rep = lint_presentation(
            _clean_recap(bullets=[]), season=SEASON, week_index=WEEK,
            channel="plain_text", canonical_facts_block=_canonical(),
        )
        assert rep.hard_failed


class TestSoftRules:
    def test_missing_title_flags_l1_soft_only(self) -> None:
        body = _clean_recap().split("\n", 2)[2]  # drop S1 title + underline
        rep = lint_presentation(
            body, season=SEASON, week_index=WEEK,
            channel="plain_text", canonical_facts_block=_canonical(),
        )
        assert not rep.hard_failed
        assert "L1" in {f.rule for f in rep.soft_flags}

    def test_markdown_in_plain_text_flags_l4(self) -> None:
        rep = lint_presentation(
            _clean_recap(narrative="The **Playmakers** put up 192.15. They won big."),
            season=SEASON, week_index=WEEK,
            channel="plain_text", canonical_facts_block=_canonical(),
        )
        assert "L4" in {f.rule for f in rep.soft_flags}
        assert not rep.hard_failed

    def test_web_prose_channel_skips_markup_rule(self) -> None:
        rep = lint_presentation(
            _clean_recap(narrative="The **Playmakers** won. It was lopsided."),
            season=SEASON, week_index=WEEK,
            channel="web_prose", canonical_facts_block=_canonical(),
        )
        assert next(f for f in rep.findings if f.rule == "L4").ok

    def test_short_paragraph_flags_l3(self) -> None:
        rep = lint_presentation(
            _clean_recap(narrative="One sentence only."),
            season=SEASON, week_index=WEEK,
            channel="plain_text", canonical_facts_block=_canonical(),
        )
        assert "L3" in {f.rule for f in rep.soft_flags}
        assert not rep.hard_failed


class TestFormatters:
    def test_transactions_block_clean_vs_internal_prefix(self) -> None:
        clean = render_transactions_block_v1(_BULLETS)
        internal = render_transactions_block_v1(_BULLETS, bullet_prefix="  - ")
        assert clean.splitlines()[1].startswith("- ")
        assert internal.splitlines()[1].startswith("  - ")
        assert clean.splitlines()[0] == "What happened this week:"

    def test_plain_text_assembler_structure(self) -> None:
        out = _clean_recap()
        lines = out.splitlines()
        assert lines[0] == f"PFL Buddies — Season {SEASON}, Week {WEEK}"
        assert set(lines[1]) == {"="}                       # setext underline
        assert "---" in lines                               # S4 separator
        assert "What happened this week:" in lines          # S5 header

    def test_quiet_week_omits_separator_and_facts(self) -> None:
        out = render_plain_text_recap_v1(
            narrative="Quiet week. Nothing moved.", bullets=[],
            season=SEASON, week_index=WEEK,
        )
        assert "What happened this week:" not in out
        assert "---" not in out

    def test_extract_and_strip_helpers(self) -> None:
        doc = "---\nkey: val\n---\n\nBody line\n\nWhat happened this week:\n- a\n- b\n"
        body = strip_frontmatter(doc)
        assert body.startswith("Body line")
        block = extract_facts_block(body)
        assert block == "What happened this week:\n- a\n- b"
