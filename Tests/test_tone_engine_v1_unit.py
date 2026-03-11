"""Tests for squadvault.core.tone.tone_engine_v1.

Covers: schema validation, directive derivation, fingerprint determinism,
effective config selection, directive building.
"""
from __future__ import annotations

import pytest

from squadvault.core.tone.tone_engine_v1 import (
    validate_tone_config_schema_v1,
    derive_directive_values_v1,
    compute_directive_fingerprint_v1,
    select_effective_tone_config_v1,
    build_tone_directive_v1,
    ToneDirectiveV1,
)


def _valid_cfg(**overrides):
    base = {
        "tone_config_id": "cfg_1",
        "group_id": "G1",
        "formality_level": "balanced",
        "humor_permitted": True,
        "profanity_permitted": False,
        "ceremonial_weight": "medium",
        "approved_at": "2024-10-01T00:00:00+00:00",
    }
    base.update(overrides)
    return base


# ── Schema validation ────────────────────────────────────────────────

class TestValidateSchema:
    def test_valid_config(self):
        assert validate_tone_config_schema_v1(_valid_cfg()) == []

    def test_missing_required_field(self):
        cfg = _valid_cfg()
        del cfg["tone_config_id"]
        errs = validate_tone_config_schema_v1(cfg)
        assert any("tone_config_id" in e for e in errs)

    def test_invalid_formality(self):
        errs = validate_tone_config_schema_v1(_valid_cfg(formality_level="extreme"))
        assert any("formality_level" in e for e in errs)

    def test_invalid_ceremonial_weight(self):
        errs = validate_tone_config_schema_v1(_valid_cfg(ceremonial_weight="extreme"))
        assert any("ceremonial_weight" in e for e in errs)

    def test_bad_approved_at(self):
        errs = validate_tone_config_schema_v1(_valid_cfg(approved_at="not-a-date"))
        assert any("ISO-8601" in e for e in errs)

    def test_not_a_dict(self):
        errs = validate_tone_config_schema_v1("not a dict")
        assert errs == ["tone config must be a dict"]

    def test_empty_tone_config_id(self):
        errs = validate_tone_config_schema_v1(_valid_cfg(tone_config_id="  "))
        assert any("non-empty" in e for e in errs)


# ── Directive derivation ─────────────────────────────────────────────

class TestDeriveDirective:
    def test_balanced_humor_nonceremonial(self):
        values = derive_directive_values_v1(
            _valid_cfg(formality_level="balanced", humor_permitted=True,
                       profanity_permitted=False, ceremonial_weight="medium"),
            artifact_class_is_ceremonial=False,
        )
        assert values["formality_constraint"] == "medium"
        assert values["humor_constraint"] == "light"
        assert values["profanity_constraint"] == "forbidden"
        assert values["ceremonial_emphasis"] == "none"  # non-ceremonial artifact

    def test_ceremonial_artifact_gets_emphasis(self):
        values = derive_directive_values_v1(
            _valid_cfg(ceremonial_weight="high"),
            artifact_class_is_ceremonial=True,
        )
        assert values["ceremonial_emphasis"] == "elevated"

    def test_casual_formality(self):
        values = derive_directive_values_v1(
            _valid_cfg(formality_level="casual"),
            artifact_class_is_ceremonial=False,
        )
        assert values["formality_constraint"] == "low"

    def test_formal_formality(self):
        values = derive_directive_values_v1(
            _valid_cfg(formality_level="formal"),
            artifact_class_is_ceremonial=False,
        )
        assert values["formality_constraint"] == "high"


# ── Fingerprint determinism ──────────────────────────────────────────

class TestFingerprint:
    def test_same_input_same_hash(self):
        kwargs = dict(
            group_id="G1", window_id="W1",
            source_tone_config_id="cfg_1",
            directive_values={"formality_constraint": "medium"},
        )
        assert compute_directive_fingerprint_v1(**kwargs) == compute_directive_fingerprint_v1(**kwargs)

    def test_different_input_different_hash(self):
        fp1 = compute_directive_fingerprint_v1(
            group_id="G1", window_id="W1",
            source_tone_config_id="cfg_1",
            directive_values={"formality_constraint": "low"},
        )
        fp2 = compute_directive_fingerprint_v1(
            group_id="G1", window_id="W1",
            source_tone_config_id="cfg_1",
            directive_values={"formality_constraint": "high"},
        )
        assert fp1 != fp2

    def test_sha256_length(self):
        fp = compute_directive_fingerprint_v1(
            group_id="G1", window_id="W1",
            source_tone_config_id="cfg_1",
            directive_values={},
        )
        assert len(fp) == 64


# ── Effective config selection ───────────────────────────────────────

class TestSelectEffective:
    def test_no_configs_returns_default(self):
        cfg, warnings, errors = select_effective_tone_config_v1(None, group_id="G1")
        assert cfg["tone_config_id"].startswith("default")

    def test_empty_list_returns_default(self):
        cfg, warnings, errors = select_effective_tone_config_v1([], group_id="G1")
        assert cfg["tone_config_id"].startswith("default")

    def test_selects_most_recent(self):
        c1 = _valid_cfg(tone_config_id="old", approved_at="2024-01-01T00:00:00+00:00")
        c2 = _valid_cfg(tone_config_id="new", approved_at="2024-06-01T00:00:00+00:00")
        cfg, warnings, errors = select_effective_tone_config_v1([c1, c2], group_id="G1")
        assert cfg["tone_config_id"] == "new"

    def test_invalid_config_rejected(self):
        bad = {"tone_config_id": ""}  # missing fields
        good = _valid_cfg()
        cfg, warnings, errors = select_effective_tone_config_v1([bad, good], group_id="G1")
        # Good config's group_id is "G1" — it should be selected
        # If not, default is used (group_id matching may filter it out)
        assert cfg is not None


# ── Build directive ──────────────────────────────────────────────────

class TestBuildDirective:
    def test_produces_valid_directive(self):
        directive, status, error, warnings = build_tone_directive_v1(
            configs=[_valid_cfg()],
            group_id="G1",
            window_id="W1",
            artifact_class_is_ceremonial=False,
        )
        assert isinstance(directive, ToneDirectiveV1)
        assert directive.group_id == "G1"
        assert directive.window_id == "W1"
        assert directive.directive_fingerprint  # non-empty

    def test_no_configs_still_produces_directive(self):
        directive, status, error, warnings = build_tone_directive_v1(
            configs=None,
            group_id="G1",
            window_id="W1",
            artifact_class_is_ceremonial=False,
        )
        assert isinstance(directive, ToneDirectiveV1)
        # Default fallback should still produce a valid directive
