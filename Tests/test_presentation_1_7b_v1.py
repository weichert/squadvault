"""Unit 1.7b presentation implementation — the 26 frozen Gate-2 obligations.

Spec: docs/Narrative_Presentation_Spec_v1_0.md. Structure module + spec-4.1 renderer + gap-fixed
lint. Byte-identity is SCOPED (Gate 1 Q1): facts block + approved content verbatim; the chrome
(masthead, no setext underline) conforms to spec - that change IS R5. Fixtures are 2 real approved
artifacts (2024 wk1 early, 2025 wk10 recent) + 1 real unparseable (2024 wk17); the full 34-artifact
sweep is the Step-3 read-only proof in the memo, not a prod-touching test.
"""
from __future__ import annotations

from pathlib import Path

from squadvault.core.exports.season_html_export_v1 import extract_shareable_parts
from squadvault.core.recaps.render.artifact_structure_v1 import (
    ArtifactStructure,
    Masthead,
    UnparseableArtifact,
    parse_artifact,
)
from squadvault.core.recaps.render.plain_text_recap_v1 import (
    render_masthead_line_v1,
    render_structure_plain_text,
)
from squadvault.core.recaps.render.presentation_lint_v1 import (
    lint_presentation,
    render_transactions_block_v1,
)

FIX = Path(__file__).parent / "fixtures" / "recap_1_7b"
ART_2024_WK1 = (FIX / "artifact_2024_wk1.txt").read_text(encoding="utf-8")
ART_2025_WK10 = (FIX / "artifact_2025_wk10.txt").read_text(encoding="utf-8")
ART_UNPARSEABLE = (FIX / "artifact_unparseable_2024_wk17.txt").read_text(encoding="utf-8")


def _struct(lede="First para one. Sentence two.", bullets=("Alpha beat Bravo 100.0-90.0.",),
            title=None, matchups=(), season=2024, week=1):
    return ArtifactStructure(
        masthead=Masthead("PFL Buddies", season, week), title=title, narrative_lede=lede,
        matchups=list(matchups), transactions=None, standings_note=None,
        facts_block=render_transactions_block_v1(list(bullets), bullet_prefix="- "),
    )


# ── A. spec section 6 prohibitions (P1-P8 + P8b) ─────────────────────
def test_p1_no_add_over_empty_sections():
    out = render_structure_plain_text(_struct())
    for header in ("Transactions:", "Standings:", "none", "Matchups:"):
        assert header not in out  # no headers/placeholders over empty (dormant) sections

def test_p2_no_remove_or_truncate():
    s = _struct(lede="Verbatim lede body. Second sentence here.")
    out = render_structure_plain_text(s)
    assert s.narrative_lede in out and s.facts_block in out  # complete + verbatim

def test_p3_no_reorder_facts_last():
    s = _struct(lede="LEDE_MARKER body one. Sentence two.")
    out = render_structure_plain_text(s)
    assert out.startswith("PFL BUDDIES")                        # masthead first
    assert out.index("LEDE_MARKER") < out.index(s.facts_block)  # lede before facts
    assert out.rstrip().endswith(s.facts_block)                 # facts block is LAST

def test_p4_no_rephrase_or_normalize():
    weird = "Odd   spacing and MiXeD case, kept.  Second one!"
    out = render_structure_plain_text(_struct(lede=weird))
    assert weird in out  # byte-exact; no whitespace/case/punct normalization

def test_p5_no_re_derive_pure_no_db():
    s = _struct()
    assert render_structure_plain_text(s) == render_structure_plain_text(s)  # deterministic
    # parse_artifact takes rendered_text + metadata only - no DB handle in the call:
    r = parse_artifact(ART_2024_WK1, league_name="PFL Buddies", season=2024, week_index=1)
    assert isinstance(r, ArtifactStructure)

def test_p6_facts_block_byte_identity():
    s = _struct()
    assert s.facts_block in render_structure_plain_text(s)

def test_p7_no_channel_markup_and_no_setext():
    out = render_structure_plain_text(parse_artifact(ART_2024_WK1, league_name="PFL Buddies", season=2024, week_index=1))
    assert "**" not in out and "`" not in out
    assert not any(ln.strip() and set(ln.strip()) == {"="} for ln in out.splitlines())  # no "====="

def test_p8_malformed_surfaced_not_repaired():
    r = parse_artifact(ART_UNPARSEABLE, league_name="PFL Buddies", season=2024, week_index=17)
    assert isinstance(r, UnparseableArtifact)

def test_p8b_surfacing_is_human_readable():
    r = parse_artifact(ART_UNPARSEABLE, league_name="PFL Buddies", season=2024, week_index=17)
    assert isinstance(r, UnparseableArtifact)
    assert isinstance(r.reason, str) and len(r.reason) > 10 and "Traceback" not in r.reason


# ── B. lint L1-L5 firing + non-firing ────────────────────────────────
def _clean(struct):  # a spec-conformant clean form for linting
    return render_structure_plain_text(struct)

def test_l1_masthead_firing_and_non_firing():
    good = _clean(_struct(season=2025, week=7))
    ok = lint_presentation(good, season=2025, week_index=7, channel="plain_text")
    assert next(f for f in ok.findings if f.rule == "L1").ok
    bad = good.replace("PFL BUDDIES — WEEK 7 — 2025", "Weekly Recap 7")
    flg = lint_presentation(bad, season=2025, week_index=7, channel="plain_text")
    assert not next(f for f in flg.findings if f.rule == "L1").ok

def test_l2_facts_byte_identity_firing_and_non_firing():
    s = _struct()
    clean = _clean(s)
    ok = lint_presentation(clean, season=2024, week_index=1, channel="plain_text",
                           canonical_facts_block=s.facts_block)
    assert next(f for f in ok.findings if f.rule == "L2").ok and not ok.hard_failed
    bad = lint_presentation(clean, season=2024, week_index=1, channel="plain_text",
                            canonical_facts_block=s.facts_block + "\n- injected fabricated fact.")
    assert bad.hard_failed  # HARD

def test_l3_paragraph_bounds_firing_and_non_firing():
    ok = lint_presentation(_clean(_struct(lede="One sentence. Two sentence.")),
                           season=2024, week_index=1, channel="plain_text")
    assert next(f for f in ok.findings if f.rule == "L3").ok
    runon = " ".join(f"S{i} is a sentence." for i in range(9))  # 9 sentences > 7
    flg = lint_presentation(_clean(_struct(lede=runon)), season=2024, week_index=1, channel="plain_text")
    assert not next(f for f in flg.findings if f.rule == "L3").ok

def test_l4_markup_firing_on_setext_R5_guard_and_non_firing():
    # R5 REGRESSION GUARD: the legacy setext "=====" underline (W7 v27 markdown-in-group-text)
    # MUST fire L4 so it can never silently return to the distributed form.
    legacy = "PFL Buddies — Season 2024, Week 1\n=================================\n\nBody one. Two."
    flg = lint_presentation(legacy, season=2024, week_index=1, channel="plain_text")
    assert not next(f for f in flg.findings if f.rule == "L4").ok
    clean = _clean(_struct())
    ok = lint_presentation(clean, season=2024, week_index=1, channel="plain_text")
    assert next(f for f in ok.findings if f.rule == "L4").ok

def test_l5_structure_order_firing_and_non_firing():
    s = _struct()
    clean = _clean(s)
    ok = lint_presentation(clean, season=2024, week_index=1, channel="plain_text")
    assert next(f for f in ok.findings if f.rule == "L5").ok
    trailing = clean + "\nStray content after the facts block."
    flg = lint_presentation(trailing, season=2024, week_index=1, channel="plain_text")
    assert not next(f for f in flg.findings if f.rule == "L5").ok


# ── C. masthead-from-metadata locked (M1-M2) ─────────────────────────
def test_m1_masthead_exact_form():
    assert render_masthead_line_v1(Masthead("PFL Buddies", 2024, 1)) == "PFL BUDDIES — WEEK 1 — 2024"

def test_m2_masthead_pure_function_of_metadata():
    a = render_masthead_line_v1(Masthead("PFL Buddies", 2024, 1))
    b = render_masthead_line_v1(Masthead("PFL Buddies", 2024, 2))
    assert a != b and "WEEK 2" in b  # changes with metadata, no prose/DB


# ── D. scoped regeneration guard on 2 real fixtures ──────────────────
def _assert_scoped_regen(art_text, season, week):
    s = parse_artifact(art_text, league_name="PFL Buddies", season=season, week_index=week)
    assert isinstance(s, ArtifactStructure)
    narr, bullets = extract_shareable_parts(art_text)
    assert s.narrative_lede == narr and s.narrative_lede in art_text          # lede byte-identical
    assert s.facts_block == render_transactions_block_v1(bullets, bullet_prefix="- ")  # facts byte-identical
    out = render_structure_plain_text(s)
    assert s.narrative_lede in out and s.facts_block in out                    # survive rendering
    # chrome diff is EXPECTED: new masthead present, legacy "=====" underline absent
    assert f"PFL BUDDIES — WEEK {week} — {season}" in out
    assert not any(ln.strip() and set(ln.strip()) == {"="} for ln in out.splitlines())

def test_d1_regen_2024_wk1():
    _assert_scoped_regen(ART_2024_WK1, 2024, 1)

def test_d1_regen_2025_wk10():
    _assert_scoped_regen(ART_2025_WK10, 2025, 10)


# ── E. the 6 unparseable exclusions (surfaced-not-repaired) ──────────
def test_e1_unparseable_surfaced_with_reason():
    r = parse_artifact(ART_UNPARSEABLE, league_name="PFL Buddies", season=2024, week_index=17)
    assert isinstance(r, UnparseableArtifact) and "SHAREABLE" in r.reason

def test_e2_no_synthetic_content_for_unparseable():
    r = parse_artifact(ART_UNPARSEABLE, league_name="PFL Buddies", season=2024, week_index=17)
    assert isinstance(r, UnparseableArtifact)
    assert not hasattr(r, "narrative_lede") and not hasattr(r, "facts_block")  # nothing fabricated


# ── F. provenance-marker survival (post-A8) ──────────────────────────
def test_f1_attested_provenance_survives_rendering():
    marked = "Weichert won Lamar Jackson for $1 [ATTESTED: MANUAL:KP-AUCTION-2019]."
    s = _struct(bullets=(marked,))
    out = render_structure_plain_text(s)
    assert marked in out and "MANUAL:KP-AUCTION-2019" in out  # byte-identical provenance survives
