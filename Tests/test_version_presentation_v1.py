"""Tests for squadvault.core.versioning.version_presentation_navigation_v1.

Covers: schema validation, canonical constraints, supersession validation,
deterministic ordering, prev/next navigation, presentation index building.
"""
from __future__ import annotations

import pytest

from squadvault.core.versioning.version_presentation_navigation_v1 import (
    validate_version_metadata_schema,
    validate_version_set_schema,
    validate_canonical_constraints,
    validate_supersession_bidirectional,
    order_versions_deterministically,
    get_prev_next_version_ids,
    build_presentation_index_v1,
    PresentationIndexV1,
    _is_sha256ish,
)

FP = "a" * 64  # valid sha256-ish fingerprint


def _ver(version_id: str, version_number: int, **overrides) -> dict:
    """Build a valid version metadata dict."""
    base = {
        "artifact_id": "art_1",
        "version_id": version_id,
        "version_number": version_number,
        "created_at": "2024-10-01T00:00:00+00:00",
        "created_by": "system",
        "creation_reason": "initial",
        "approval_status": "draft",
        "is_canonical": False,
        "window_id": "W1",
        "fingerprint": FP,
    }
    base.update(overrides)
    return base


# ── _is_sha256ish ────────────────────────────────────────────────────

class TestIsSha256ish:
    def test_valid(self):
        assert _is_sha256ish("a" * 64) is True

    def test_too_short(self):
        assert _is_sha256ish("a" * 63) is False

    def test_too_long(self):
        assert _is_sha256ish("a" * 65) is False

    def test_non_hex(self):
        assert _is_sha256ish("g" * 64) is False

    def test_empty(self):
        assert _is_sha256ish("") is False


# ── validate_version_metadata_schema ─────────────────────────────────

class TestValidateMetadataSchema:
    def test_valid_record(self):
        assert validate_version_metadata_schema(_ver("v1", 1)) == []

    def test_missing_required(self):
        v = _ver("v1", 1)
        del v["artifact_id"]
        errs = validate_version_metadata_schema(v)
        assert any("artifact_id" in e for e in errs)

    def test_empty_artifact_id(self):
        errs = validate_version_metadata_schema(_ver("v1", 1, artifact_id="  "))
        assert any("non-empty" in e for e in errs)

    def test_negative_version_number(self):
        errs = validate_version_metadata_schema(_ver("v1", -1))
        assert any("version_number" in e for e in errs)

    def test_invalid_created_by(self):
        errs = validate_version_metadata_schema(_ver("v1", 1, created_by="robot"))
        assert any("created_by" in e for e in errs)

    def test_invalid_approval_status(self):
        errs = validate_version_metadata_schema(_ver("v1", 1, approval_status="maybe"))
        assert any("approval_status" in e for e in errs)

    def test_bad_fingerprint(self):
        errs = validate_version_metadata_schema(_ver("v1", 1, fingerprint="short"))
        assert any("fingerprint" in e or "sha256" in e for e in errs)

    def test_self_referencing_supersedes(self):
        errs = validate_version_metadata_schema(_ver("v1", 1, supersedes="v1"))
        assert any("self-reference" in e for e in errs)

    def test_not_a_dict(self):
        errs = validate_version_metadata_schema("not a dict")
        assert errs == ["version metadata must be a dict"]


# ── validate_version_set_schema ──────────────────────────────────────

class TestValidateSetSchema:
    def test_valid_set(self):
        assert validate_version_set_schema([_ver("v1", 1), _ver("v2", 2)]) == []

    def test_none_input(self):
        errs = validate_version_set_schema(None)
        assert any("must be provided" in e for e in errs)

    def test_errors_prefixed_with_index(self):
        bad = _ver("v1", 1)
        del bad["artifact_id"]
        errs = validate_version_set_schema([bad])
        assert any("versions[0]" in e for e in errs)


# ── validate_canonical_constraints ───────────────────────────────────

class TestCanonicalConstraints:
    def test_single_canonical_approved(self):
        v = _ver("v1", 1, is_canonical=True, approval_status="approved")
        assert validate_canonical_constraints([v]) == []

    def test_multiple_canonical(self):
        v1 = _ver("v1", 1, is_canonical=True, approval_status="approved")
        v2 = _ver("v2", 2, is_canonical=True, approval_status="approved")
        errs = validate_canonical_constraints([v1, v2])
        assert any("ambiguous" in e for e in errs)

    def test_canonical_must_be_approved(self):
        v = _ver("v1", 1, is_canonical=True, approval_status="draft")
        errs = validate_canonical_constraints([v])
        assert any("approved" in e.lower() or "draft" in e.lower() for e in errs)

    def test_canonical_must_not_be_superseded(self):
        v = _ver("v1", 1, is_canonical=True, approval_status="approved", superseded_by="v2")
        errs = validate_canonical_constraints([v])
        assert any("superseded" in e for e in errs)

    def test_no_canonical_is_fine(self):
        v = _ver("v1", 1, is_canonical=False)
        assert validate_canonical_constraints([v]) == []


# ── validate_supersession_bidirectional ──────────────────────────────

class TestSupersessionBidirectional:
    def test_valid_chain(self):
        v1 = _ver("v1", 1, superseded_by="v2")
        v2 = _ver("v2", 2, supersedes="v1")
        assert validate_supersession_bidirectional([v1, v2]) == []

    def test_broken_forward(self):
        v1 = _ver("v1", 1, superseded_by="v2")
        v2 = _ver("v2", 2)  # missing supersedes
        errs = validate_supersession_bidirectional([v1, v2])
        assert any("mismatch" in e for e in errs)

    def test_missing_target(self):
        v1 = _ver("v1", 1, supersedes="v_nonexistent")
        errs = validate_supersession_bidirectional([v1])
        assert any("missing" in e for e in errs)


# ── order_versions_deterministically ─────────────────────────────────

class TestOrderVersions:
    def test_orders_by_version_number(self):
        v1 = _ver("v1", 1)
        v2 = _ver("v2", 2)
        v3 = _ver("v3", 3)
        result = order_versions_deterministically([v3, v1, v2])
        assert [v["version_id"] for v in result] == ["v1", "v2", "v3"]

    def test_same_version_number_orders_by_created_at(self):
        v1 = _ver("v_early", 1, created_at="2024-01-01T00:00:00+00:00")
        v2 = _ver("v_late", 1, created_at="2024-06-01T00:00:00+00:00")
        result = order_versions_deterministically([v2, v1])
        assert result[0]["version_id"] == "v_early"

    def test_empty_list(self):
        assert order_versions_deterministically([]) == []


# ── get_prev_next_version_ids ────────────────────────────────────────

class TestPrevNextVersionIds:
    def test_middle(self):
        versions = [_ver("v1", 1), _ver("v2", 2), _ver("v3", 3)]
        prev_id, next_id = get_prev_next_version_ids(versions, "v2")
        assert prev_id == "v1"
        assert next_id == "v3"

    def test_first(self):
        versions = [_ver("v1", 1), _ver("v2", 2)]
        prev_id, next_id = get_prev_next_version_ids(versions, "v1")
        assert prev_id is None
        assert next_id == "v2"

    def test_last(self):
        versions = [_ver("v1", 1), _ver("v2", 2)]
        prev_id, next_id = get_prev_next_version_ids(versions, "v2")
        assert prev_id == "v1"
        assert next_id is None

    def test_not_found(self):
        versions = [_ver("v1", 1)]
        prev_id, next_id = get_prev_next_version_ids(versions, "v_missing")
        assert prev_id is None
        assert next_id is None

    def test_empty_input(self):
        assert get_prev_next_version_ids([], "v1") == (None, None)

    def test_none_input(self):
        assert get_prev_next_version_ids([], None) == (None, None)


# ── build_presentation_index_v1 ─────────────────────────────────────

class TestBuildPresentationIndex:
    def test_basic_index(self):
        v1 = _ver("v1", 1, approval_status="approved", is_canonical=True)
        v2 = _ver("v2", 2, approval_status="draft")
        idx = build_presentation_index_v1([v1, v2])
        assert isinstance(idx, PresentationIndexV1)
        assert len(idx.versions) == 2

    def test_empty_versions(self):
        idx = build_presentation_index_v1([])
        assert len(idx.versions) == 0
