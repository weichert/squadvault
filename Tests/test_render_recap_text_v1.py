"""Tests for render_recap_text_v1 and voice_variants_v1.

Covers: render_recap_text_v1 output structure, voice framing,
_safe_int, get_voice_spec, format_variant_block, render_from_path.
"""
from __future__ import annotations

import json

import pytest

from squadvault.core.recaps.render.render_recap_text_v1 import (
    _safe_int,
    render_recap_text_from_path_v1,
    render_recap_text_v1,
)
from squadvault.core.recaps.render.voice_variants_v1 import (
    VOICE_IDS,
    VoiceSpec,
    format_variant_block,
    get_voice_spec,
)


def _artifact(**overrides):
    base = {
        "league_id": "L1",
        "season": 2024,
        "week_index": 5,
        "recap_version": 1,
        "window": {"start": "2024-10-01", "end": "2024-10-08"},
        "selection": {
            "event_count": 3,
            "counts_by_type": {"MATCHUP_RESULT": 2, "TRADE": 1},
            "fingerprint": "abc123",
            "canonical_ids": [10, 11, 12],
        },
    }
    base.update(overrides)
    return base


# ── _safe_int ────────────────────────────────────────────────────────

class TestSafeInt:
    def test_normal_int(self):
        assert _safe_int(42) == 42

    def test_string_int(self):
        assert _safe_int("7") == 7

    def test_none_uses_default(self):
        assert _safe_int(None, 99) == 99

    def test_garbage_uses_default(self):
        assert _safe_int("xyz", 5) == 5

    def test_default_is_zero(self):
        assert _safe_int(None) == 0


# ── voice_variants_v1 ───────────────────────────────────────────────

class TestVoiceSpec:
    def test_all_voice_ids_valid(self):
        for vid in VOICE_IDS:
            spec = get_voice_spec(vid)
            assert isinstance(spec, VoiceSpec)
            assert spec.voice_id == vid

    def test_unknown_voice_raises(self):
        with pytest.raises(ValueError, match="Unknown voice_id"):
            get_voice_spec("aggressive")

    def test_none_raises(self):
        with pytest.raises(ValueError):
            get_voice_spec(None)

    def test_case_insensitive(self):
        spec = get_voice_spec("NEUTRAL")
        assert spec.voice_id == "neutral"


class TestFormatVariantBlock:
    def test_contains_header_and_body(self):
        result = format_variant_block(voice_id="playful", body="Hello world")
        assert "NON-CANONICAL VARIANT" in result
        assert "PLAYFUL" in result
        assert "Hello world" in result

    def test_body_stripped(self):
        result = format_variant_block(voice_id="dry", body="  text  \n\n")
        assert result.endswith("text\n")


# ── render_recap_text_v1 ─────────────────────────────────────────────

class TestRenderRecapText:
    def test_header_line(self):
        text = render_recap_text_v1(_artifact())
        assert "League L1" in text
        assert "Season 2024" in text
        assert "Week 5" in text
        assert "(v1)" in text

    def test_window_line(self):
        text = render_recap_text_v1(_artifact())
        assert "2024-10-01" in text
        assert "2024-10-08" in text

    def test_fingerprint_line(self):
        text = render_recap_text_v1(_artifact())
        assert "abc123" in text

    def test_event_count_line(self):
        text = render_recap_text_v1(_artifact())
        assert "Events selected: 3" in text

    def test_breakdown_sorted(self):
        text = render_recap_text_v1(_artifact())
        lines = text.split("\n")
        breakdown_lines = [l for l in lines if l.strip().startswith("- ")]
        # MATCHUP_RESULT and TRADE, alphabetically
        assert "MATCHUP_RESULT" in breakdown_lines[0]
        assert "TRADE" in breakdown_lines[1]

    def test_trace_ids_present(self):
        text = render_recap_text_v1(_artifact())
        assert "10, 11, 12" in text

    def test_no_canonical_ids_shows_none(self):
        art = _artifact()
        art["selection"]["canonical_ids"] = []
        text = render_recap_text_v1(art)
        assert "(none)" in text

    def test_note_present(self):
        text = render_recap_text_v1(_artifact())
        assert "intentionally avoids fabricating" in text

    def test_missing_selection(self):
        art = _artifact(selection=None)
        text = render_recap_text_v1(art)
        assert "Events selected: 0" in text

    def test_missing_window(self):
        art = _artifact(window=None)
        text = render_recap_text_v1(art)
        assert "None" in text  # Window: None → None


# ── Voice framing ────────────────────────────────────────────────────

class TestVoiceFraming:
    def test_neutral_no_prefix(self):
        text = render_recap_text_v1(_artifact(), voice_id="neutral")
        assert not text.startswith("Commissioner's note")

    def test_playful_has_prefix(self):
        text = render_recap_text_v1(_artifact(), voice_id="playful")
        assert "Commissioner" in text.split("\n")[0]
        assert "same facts" in text.split("\n")[0]

    def test_dry_has_prefix(self):
        text = render_recap_text_v1(_artifact(), voice_id="dry")
        assert "Commissioner" in text.split("\n")[0]
        assert "minimal framing" in text.split("\n")[0]


# ── Trace ID chunking (>25 IDs) ─────────────────────────────────────

class TestTraceChunking:
    def test_ids_chunked_at_25(self):
        art = _artifact()
        art["selection"]["canonical_ids"] = list(range(1, 60))
        text = render_recap_text_v1(art)
        lines = text.split("\n")
        # Find the "Trace" header and count indented lines after it
        trace_idx = next(i for i, l in enumerate(lines) if "Trace (selection ids)" in l)
        trace_lines = []
        for l in lines[trace_idx + 1:]:
            if l.startswith("  ") and any(c.isdigit() for c in l) and "- " not in l:
                trace_lines.append(l)
            elif l.strip() == "":
                continue
            else:
                break
        # 59 ids / 25 per chunk = 3 lines (25, 25, 9)
        assert len(trace_lines) == 3


# ── render_recap_text_from_path_v1 ───────────────────────────────────

class TestRenderFromPath:
    def test_reads_file_and_renders(self, tmp_path):
        art = _artifact()
        path = str(tmp_path / "artifact.json")
        with open(path, "w") as f:
            json.dump(art, f)
        text = render_recap_text_from_path_v1(path)
        assert "League L1" in text
        assert "Week 5" in text
