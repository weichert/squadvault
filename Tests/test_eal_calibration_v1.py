"""Tests for squadvault.core.eal.eal_calibration_v1

Covers: schema validation, default calibration, effective selection,
restraint directive derivation, fingerprint determinism, build_restraint_directive_v1.
"""
from __future__ import annotations

import pytest

from squadvault.core.eal.eal_calibration_v1 import (
    DEFAULT_CALIBRATION_VALUES,
    RestraintDirective,
    _is_nonempty_str,
    _is_semver_like,
    _parse_iso8601_utc,
    build_restraint_directive_v1,
    compute_directive_fingerprint,
    default_system_calibration_record,
    derive_restraint_directive,
    select_effective_calibration,
    validate_calibration_schema,
)


def _valid_cal(**overrides):
    base = {
        "calibration_id": "cal_1",
        "scope": "system",
        "min_signal_count_for_confidence": 3,
        "max_ambiguity_tolerance": 0.25,
        "max_grouping_density": 0.5,
        "version": "1.0.0",
        "approved_by": "founder",
        "approved_at": "2024-10-01T00:00:00+00:00",
    }
    base.update(overrides)
    return base


# ── Helpers ──────────────────────────────────────────────────────────

class TestHelpers:
    def test_is_nonempty_str(self):
        assert _is_nonempty_str("hello")
        assert not _is_nonempty_str("")
        assert not _is_nonempty_str("   ")
        assert not _is_nonempty_str(None)
        assert not _is_nonempty_str(42)

    def test_is_semver_like(self):
        assert _is_semver_like("1.0.0")
        assert _is_semver_like("10.20.30")
        assert not _is_semver_like("1.0")
        assert not _is_semver_like("abc")
        assert not _is_semver_like(None)

    def test_parse_iso8601_utc_valid(self):
        dt = _parse_iso8601_utc("2024-10-01T00:00:00+00:00")
        assert dt is not None
        assert dt.year == 2024

    def test_parse_iso8601_utc_z_suffix(self):
        dt = _parse_iso8601_utc("2024-10-01T00:00:00Z")
        assert dt is not None

    def test_parse_iso8601_utc_non_utc_rejected(self):
        assert _parse_iso8601_utc("2024-10-01T00:00:00+05:00") is None

    def test_parse_iso8601_utc_naive_rejected(self):
        assert _parse_iso8601_utc("2024-10-01T00:00:00") is None

    def test_parse_iso8601_utc_empty(self):
        assert _parse_iso8601_utc("") is None
        assert _parse_iso8601_utc(None) is None


# ── Schema validation ────────────────────────────────────────────────

class TestValidateSchema:
    def test_valid_record_no_errors(self):
        assert validate_calibration_schema(_valid_cal()) == []

    def test_missing_required_field(self):
        cal = _valid_cal()
        del cal["calibration_id"]
        errs = validate_calibration_schema(cal)
        assert any("calibration_id" in e for e in errs)

    def test_unexpected_field(self):
        cal = _valid_cal(extra_field="oops")
        errs = validate_calibration_schema(cal)
        assert any("unexpected" in e for e in errs)

    def test_invalid_scope(self):
        errs = validate_calibration_schema(_valid_cal(scope="global"))
        assert any("scope" in e for e in errs)

    def test_group_scope_requires_scope_id(self):
        errs = validate_calibration_schema(_valid_cal(scope="group"))
        assert any("scope_id" in e for e in errs)

    def test_group_scope_with_scope_id_valid(self):
        cal = _valid_cal(scope="group", scope_id="league_1")
        assert validate_calibration_schema(cal) == []

    def test_min_signal_count_must_be_positive_int(self):
        errs = validate_calibration_schema(_valid_cal(min_signal_count_for_confidence=0))
        assert any("min_signal_count" in e for e in errs)

    def test_ambiguity_out_of_range(self):
        errs = validate_calibration_schema(_valid_cal(max_ambiguity_tolerance=1.5))
        assert any("out of range" in e for e in errs)

    def test_bad_version(self):
        errs = validate_calibration_schema(_valid_cal(version="v1"))
        assert any("semver" in e for e in errs)

    def test_bad_approved_at(self):
        errs = validate_calibration_schema(_valid_cal(approved_at="not-a-date"))
        assert any("ISO-8601" in e for e in errs)


# ── Default calibration ─────────────────────────────────────────────

class TestDefaultCalibration:
    def test_default_is_valid(self):
        cal = default_system_calibration_record()
        # scope_id=None is optional, remove if present to avoid "unexpected" error
        assert validate_calibration_schema(cal) == []

    def test_default_has_system_scope(self):
        assert default_system_calibration_record()["scope"] == "system"


# ── select_effective_calibration ─────────────────────────────────────

class TestSelectEffective:
    def test_no_candidates_returns_default(self):
        cal, warnings = select_effective_calibration([], scope="system", scope_id=None)
        assert cal["calibration_id"] == "default_system_calibration_v1"
        assert any("no valid" in w for w in warnings)

    def test_selects_most_recent(self):
        c1 = _valid_cal(calibration_id="old", approved_at="2024-01-01T00:00:00Z")
        c2 = _valid_cal(calibration_id="new", approved_at="2024-06-01T00:00:00Z")
        cal, _ = select_effective_calibration([c1, c2], scope="system", scope_id=None)
        assert cal["calibration_id"] == "new"

    def test_warns_on_conflict(self):
        c1 = _valid_cal(calibration_id="a", approved_at="2024-01-01T00:00:00Z")
        c2 = _valid_cal(calibration_id="b", approved_at="2024-06-01T00:00:00Z")
        _, warnings = select_effective_calibration([c1, c2], scope="system", scope_id=None)
        assert any("conflicting" in w for w in warnings)

    def test_invalid_scope_returns_default(self):
        cal, warnings = select_effective_calibration([], scope="bad", scope_id=None)
        assert cal["calibration_id"] == "default_system_calibration_v1"

    def test_group_scope_filters_by_scope_id(self):
        c1 = _valid_cal(calibration_id="g1", scope="group", scope_id="league_A",
                        approved_at="2024-06-01T00:00:00Z")
        c2 = _valid_cal(calibration_id="g2", scope="group", scope_id="league_B",
                        approved_at="2024-06-01T00:00:00Z")
        cal, _ = select_effective_calibration([c1, c2], scope="group", scope_id="league_A")
        assert cal["calibration_id"] == "g1"


# ── derive_restraint_directive ───────────────────────────────────────

class TestDeriveRestraint:
    def _cal(self):
        return _valid_cal()

    def test_all_within_thresholds_returns_high_restraint(self):
        rd = derive_restraint_directive(
            window_id="w1", signal_count=5, ambiguity=0.1,
            grouping_density=0.2, calibration=self._cal(),
        )
        assert rd == RestraintDirective.high_restraint

    def test_missing_window_id_prefers_silence(self):
        rd = derive_restraint_directive(
            window_id="", signal_count=5, ambiguity=0.1,
            grouping_density=0.2, calibration=self._cal(),
        )
        assert rd == RestraintDirective.prefer_silence

    def test_low_signal_count_prefers_silence(self):
        rd = derive_restraint_directive(
            window_id="w1", signal_count=1, ambiguity=0.1,
            grouping_density=0.2, calibration=self._cal(),
        )
        assert rd == RestraintDirective.prefer_silence

    def test_high_ambiguity_prefers_silence(self):
        rd = derive_restraint_directive(
            window_id="w1", signal_count=5, ambiguity=0.9,
            grouping_density=0.2, calibration=self._cal(),
        )
        assert rd == RestraintDirective.prefer_silence

    def test_high_grouping_density_prefers_silence(self):
        rd = derive_restraint_directive(
            window_id="w1", signal_count=5, ambiguity=0.1,
            grouping_density=0.9, calibration=self._cal(),
        )
        assert rd == RestraintDirective.prefer_silence

    def test_none_calibration_prefers_silence(self):
        rd = derive_restraint_directive(
            window_id="w1", signal_count=5, ambiguity=0.1,
            grouping_density=0.2, calibration=None,
        )
        assert rd == RestraintDirective.prefer_silence

    def test_none_signal_count_prefers_silence(self):
        rd = derive_restraint_directive(
            window_id="w1", signal_count=None, ambiguity=0.1,
            grouping_density=0.2, calibration=self._cal(),
        )
        assert rd == RestraintDirective.prefer_silence


# ── Fingerprint determinism ──────────────────────────────────────────

class TestFingerprint:
    def test_same_input_same_fingerprint(self):
        kwargs = dict(
            window_id="w1", source_calibration_id="cal_1",
            restraint_directive="high_restraint",
            inputs={"signal_count": 5, "ambiguity": 0.1},
        )
        assert compute_directive_fingerprint(**kwargs) == compute_directive_fingerprint(**kwargs)

    def test_different_input_different_fingerprint(self):
        base = dict(
            window_id="w1", source_calibration_id="cal_1",
            restraint_directive="high_restraint",
            inputs={"signal_count": 5},
        )
        fp1 = compute_directive_fingerprint(**base)
        base["inputs"]["signal_count"] = 10
        fp2 = compute_directive_fingerprint(**base)
        assert fp1 != fp2


# ── build_restraint_directive_v1 ─────────────────────────────────────

class TestBuildDirective:
    def test_produces_valid_record(self):
        result = build_restraint_directive_v1(
            window_id="w1", signal_count=5, ambiguity=0.1,
            grouping_density=0.2, calibration=_valid_cal(),
            generated_at="2024-10-01T00:00:00Z",
        )
        assert result.restraint_directive == "high_restraint"
        assert result.window_id == "w1"
        assert result.directive_fingerprint  # non-empty
        assert result.source_calibration_id == "cal_1"

    def test_missing_calibration_still_produces_record(self):
        result = build_restraint_directive_v1(
            window_id="w1", signal_count=5, ambiguity=0.1,
            grouping_density=0.2, calibration=None,
            generated_at="2024-10-01T00:00:00Z",
        )
        assert result.restraint_directive == "prefer_silence"
        assert result.source_calibration_id == "default_system_calibration_v1"
