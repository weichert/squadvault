import unittest
import importlib.util
import sys
from pathlib import Path
import hashlib
import json


def _load_module_by_path():
    """
    Workaround: macOS+iCloud importlib loader can time out on get_data for src modules.
    Load the module by explicit file path to keep Type A semantics testable.

    Important: register in sys.modules before exec_module so dataclasses works.
    """
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "src" / "squadvault" / "core" / "tone" / "tone_engine_v1.py"
    module_name = "sv_tone_engine_v1"

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not create module spec for: {module_path}")

    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


m = _load_module_by_path()


def _cfg(
    *,
    tone_config_id="tc1",
    group_id="g1",
    formality_level="balanced",
    humor_permitted=False,
    profanity_permitted=False,
    ceremonial_weight="low",
    approved_at="2026-01-01T00:00:00+00:00",
    supersedes=None,
):
    d = {
        "tone_config_id": tone_config_id,
        "group_id": group_id,
        "formality_level": formality_level,
        "humor_permitted": humor_permitted,
        "profanity_permitted": profanity_permitted,
        "ceremonial_weight": ceremonial_weight,
        "approved_at": approved_at,
        "supersedes": supersedes,
    }
    if supersedes is None:
        d.pop("supersedes")
    return d


class TestToneEngineV1_TypeA(unittest.TestCase):
    def test_default_neutral_used_when_missing(self):
        d, status, err, warnings = m.build_tone_directive_v1(
            group_id="g1",
            window_id="w1",
            configs=None,
            artifact_class_is_ceremonial=False,
        )
        self.assertEqual(status, m.ToneDirectiveStatus.ok)
        self.assertIsNone(err)
        self.assertEqual(d.source_tone_config_id, "default-neutral")
        self.assertEqual(d.formality_constraint, "medium")
        self.assertEqual(d.humor_constraint, "none")
        self.assertEqual(d.profanity_constraint, "forbidden")
        self.assertEqual(d.ceremonial_emphasis, "none")

    def test_schema_rejects_invalid_enum(self):
        bad = _cfg(formality_level="weird")
        errs = m.validate_tone_config_schema_v1(bad)
        self.assertTrue(any("formality_level invalid" in e for e in errs))

    def test_schema_approved_at_must_be_tz_aware(self):
        bad = _cfg(approved_at="2026-01-01T00:00:00")
        errs = m.validate_tone_config_schema_v1(bad)
        self.assertTrue(any("approved_at must be ISO-8601 UTC" in e for e in errs))

    def test_ceremonial_gating_non_ceremonial_forces_none(self):
        cfg = _cfg(ceremonial_weight="high")
        dv = m.derive_directive_values_v1(cfg, artifact_class_is_ceremonial=False)
        self.assertEqual(dv["ceremonial_emphasis"], "none")

    def test_ceremonial_mapping_high(self):
        cfg = _cfg(ceremonial_weight="high")
        dv = m.derive_directive_values_v1(cfg, artifact_class_is_ceremonial=True)
        self.assertEqual(dv["ceremonial_emphasis"], "elevated")

    def test_conflict_selection_most_recent_warns(self):
        c1 = _cfg(tone_config_id="tc1", approved_at="2026-01-01T00:00:00+00:00")
        c2 = _cfg(tone_config_id="tc2", approved_at="2026-01-02T00:00:00+00:00")
        cfg, errs, warnings = m.select_effective_tone_config_v1([c1, c2], group_id="g1")
        self.assertEqual(errs, [])
        self.assertTrue(any("conflicting active configurations" in w for w in warnings))
        self.assertEqual(cfg["tone_config_id"], "tc2")

    def test_fingerprint_matches_canonical_formula(self):
        cfg = _cfg(tone_config_id="tcX", group_id="g1", formality_level="formal", humor_permitted=True, profanity_permitted=False, ceremonial_weight="low")
        dv = m.derive_directive_values_v1(cfg, artifact_class_is_ceremonial=True)
        fp = m.compute_directive_fingerprint_v1(
            group_id="g1",
            window_id="w9",
            source_tone_config_id="tcX",
            directive_values=dv,
        )

        payload = "g1|w9|tcX|" + json.dumps(dv, sort_keys=True, separators=(",", ":"))
        expected = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        self.assertEqual(fp, expected)

    def test_build_is_deterministic(self):
        cfg = _cfg(tone_config_id="tc1", approved_at="2026-01-01T00:00:00+00:00")
        d1, s1, e1, w1 = m.build_tone_directive_v1(group_id="g1", window_id="w1", configs=[cfg], artifact_class_is_ceremonial=True)
        d2, s2, e2, w2 = m.build_tone_directive_v1(group_id="g1", window_id="w1", configs=[cfg], artifact_class_is_ceremonial=True)
        self.assertEqual(s1, m.ToneDirectiveStatus.ok)
        self.assertEqual(s2, m.ToneDirectiveStatus.ok)
        self.assertIsNone(e1)
        self.assertIsNone(e2)
        self.assertEqual(d1, d2)
        self.assertEqual(w1, w2)


if __name__ == "__main__":
    unittest.main()
