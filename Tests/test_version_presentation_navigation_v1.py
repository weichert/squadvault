import unittest
import importlib.util
import sys
from pathlib import Path


def _load_module_by_path():
    """
    Workaround: macOS+iCloud importlib loader can time out on get_data for src modules.
    Load the module by explicit file path to keep Type A semantics testable.

    Important: register in sys.modules before exec_module so dataclasses works.
    """
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "src" / "squadvault" / "core" / "versioning" / "version_presentation_navigation_v1.py"
    module_name = "sv_version_presentation_navigation_v1"

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not create module spec for: {module_path}")

    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod  # required for dataclasses / annotations resolution
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


m = _load_module_by_path()

PresentationStatus = m.PresentationStatus
build_presentation_index_v1 = m.build_presentation_index_v1
get_prev_next_version_ids = m.get_prev_next_version_ids
order_versions_deterministically = m.order_versions_deterministically
validate_canonical_constraints = m.validate_canonical_constraints
validate_supersession_bidirectional = m.validate_supersession_bidirectional
validate_version_metadata_schema = m.validate_version_metadata_schema


def _v(
    *,
    artifact_id="a1",
    version_id="v-0001",
    version_number=1,
    created_at="2026-01-01T00:00:00+00:00",
    created_by="system",
    creation_reason="initial",
    approval_status="approved",
    is_canonical=False,
    supersedes=None,
    superseded_by=None,
    window_id="w1",
    fingerprint="0" * 64,
):
    return {
        "artifact_id": artifact_id,
        "version_id": version_id,
        "version_number": version_number,
        "created_at": created_at,
        "created_by": created_by,
        "creation_reason": creation_reason,
        "approval_status": approval_status,
        "is_canonical": is_canonical,
        "supersedes": supersedes,
        "superseded_by": superseded_by,
        "window_id": window_id,
        "fingerprint": fingerprint,
    }


class TestVersionPresentationNavigationV1(unittest.TestCase):
    def test_schema_ok(self):
        self.assertEqual(validate_version_metadata_schema(_v()), [])

    def test_schema_missing_required(self):
        bad = _v()
        del bad["created_at"]
        errs = validate_version_metadata_schema(bad)
        self.assertTrue(any("missing required field: created_at" in e for e in errs))

    def test_schema_invalid_enums(self):
        bad = _v(created_by="robot")
        errs = validate_version_metadata_schema(bad)
        self.assertTrue(any("created_by invalid" in e for e in errs))

    def test_schema_created_at_must_be_utc(self):
        bad = _v(created_at="2026-01-01T00:00:00")
        errs = validate_version_metadata_schema(bad)
        self.assertTrue(any("created_at must be ISO-8601 UTC" in e for e in errs))

    def test_canonical_constraints_at_most_one(self):
        v1 = _v(version_id="v1", version_number=1, is_canonical=True, approval_status="approved")
        v2 = _v(version_id="v2", version_number=2, is_canonical=True, approval_status="approved")
        errs = validate_canonical_constraints([v1, v2])
        self.assertTrue(any("ambiguous canonical" in e for e in errs))

    def test_canonical_must_be_approved(self):
        v1 = _v(version_id="v1", is_canonical=True, approval_status="withheld")
        errs = validate_canonical_constraints([v1])
        self.assertTrue(any("canonical version must be approval_status=approved" in e for e in errs))

    def test_draft_or_withheld_never_canonical(self):
        v1 = _v(version_id="v1", is_canonical=True, approval_status="draft")
        errs = validate_canonical_constraints([v1])
        self.assertTrue(any("draft/withheld versions may never be canonical" in e for e in errs))

    def test_supersession_bidirectional_ok(self):
        v1 = _v(version_id="v1", version_number=1, superseded_by="v2")
        v2 = _v(version_id="v2", version_number=2, is_canonical=True, supersedes="v1")
        errs = validate_supersession_bidirectional([v1, v2])
        self.assertEqual(errs, [])

    def test_supersession_bidirectional_mismatch(self):
        v1 = _v(version_id="v1", version_number=1, superseded_by="v2")
        v2 = _v(version_id="v2", version_number=2, supersedes="vX")
        errs = validate_supersession_bidirectional([v1, v2])
        self.assertTrue(len(errs) > 0)

    def test_ordering_primary_version_number(self):
        a = _v(version_id="v1", version_number=2, created_at="2026-01-02T00:00:00+00:00")
        b = _v(version_id="v2", version_number=1, created_at="2026-01-03T00:00:00+00:00")
        ordered = order_versions_deterministically([a, b])
        self.assertEqual([v["version_id"] for v in ordered], ["v2", "v1"])

    def test_navigation_lossless_prev_next(self):
        v1 = _v(version_id="v1", version_number=1)
        v2 = _v(version_id="v2", version_number=2)
        v3 = _v(version_id="v3", version_number=3)
        ordered = order_versions_deterministically([v2, v3, v1])
        self.assertEqual(get_prev_next_version_ids(ordered, "v2"), ("v1", "v3"))
        self.assertEqual(get_prev_next_version_ids(ordered, "v1"), (None, "v2"))
        self.assertEqual(get_prev_next_version_ids(ordered, "v3"), ("v2", None))

    def test_builder_missing_metadata_blocks_with_error(self):
        v1 = _v()
        del v1["fingerprint"]
        idx = build_presentation_index_v1([v1])
        self.assertEqual(idx.status, PresentationStatus.error)
        self.assertIsNotNone(idx.error)

    def test_builder_ambiguous_canonical_defaults_withheld(self):
        v1 = _v(version_id="v1", is_canonical=True, approval_status="approved", version_number=1)
        v2 = _v(version_id="v2", is_canonical=True, approval_status="approved", version_number=2)
        idx = build_presentation_index_v1([v1, v2])
        self.assertEqual(idx.status, PresentationStatus.withheld)
        self.assertIsNone(idx.canonical_version_id)

    def test_builder_ok_sets_canonical_version_id(self):
        v1 = _v(version_id="v1", is_canonical=False, approval_status="approved", version_number=1)
        v2 = _v(version_id="v2", is_canonical=True, approval_status="approved", version_number=2, supersedes="v1")
        v1 = dict(v1)
        v1["superseded_by"] = "v2"
        idx = build_presentation_index_v1([v2, v1])
        self.assertEqual(idx.status, PresentationStatus.ok)
        self.assertEqual(idx.canonical_version_id, "v2")


if __name__ == "__main__":
    unittest.main()
