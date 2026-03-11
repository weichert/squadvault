"""Governance gate: validate contract alignment and architectural invariants.

Ensures the implementation matches what the governance documents promise.
These tests enforce structural truths from the Canonical Operating Constitution,
Core Engine Spec, and Contract Cards.
"""
from __future__ import annotations

import ast
import glob
import os
import sqlite3
import tempfile

import pytest


SRC = os.path.join(os.path.dirname(__file__), "..", "src")
FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures")
SCHEMA_PATH = os.path.join(SRC, "squadvault", "core", "storage", "schema.sql")


# ── Contract-specified components exist ──────────────────────────────

class TestComponentPresence:
    """Every component specified by contract cards must have an implementation file."""

    # Map: component name → expected file path relative to src/squadvault/
    REQUIRED_COMPONENTS = {
        # Core Engine
        "MemoryEvent storage": "core/storage/sqlite_store.py",
        "Canonical events": "core/canonicalize/run_canonicalize.py",
        "Recap artifacts lifecycle": "core/recaps/recap_artifacts.py",
        "Recap runs tracking": "core/recaps/recap_runs.py",
        "Tone Engine": "core/tone/tone_engine_v1.py",
        "EAL calibration": "core/eal/eal_calibration_v1.py",
        "DatabaseSession": "core/storage/session.py",
        "Schema migrations": "core/storage/migrate.py",
        # Narrative Assembly Pipeline
        "Deterministic bullets": "core/recaps/render/deterministic_bullets_v1.py",
        "Facts block assembly": "core/recaps/render/render_deterministic_facts_block_v1.py",
        "Recap text rendering": "core/recaps/render/render_recap_text_v1.py",
        "Voice variants": "core/recaps/render/voice_variants_v1.py",
        # Writing Room
        "Writing Room Intake": "recaps/writing_room/intake_v1.py",
        "Selection Set Schema": "recaps/writing_room/selection_set_schema_v1.py",
        "Signal adapter": "recaps/writing_room/signal_adapter_v1.py",
        "Window resolver": "recaps/writing_room/window_resolver_v1.py",
        # Weekly Recap Lifecycle
        "Weekly recap lifecycle": "recaps/weekly_recap_lifecycle.py",
        "Preflight gate": "recaps/preflight.py",
        "DNG reasons": "recaps/dng_reasons.py",
        # Rivalry Chronicle
        "Rivalry chronicle generation": "chronicle/generate_rivalry_chronicle_v1.py",
        "Rivalry chronicle persistence": "chronicle/persist_rivalry_chronicle_v1.py",
        "Rivalry chronicle input contract": "chronicle/input_contract_v1.py",
        # Error hierarchy
        "Error hierarchy": "errors.py",
    }

    def test_all_contract_components_exist(self):
        """Every contract-specified component must have an implementation file."""
        missing = []
        for name, rel_path in self.REQUIRED_COMPONENTS.items():
            full_path = os.path.join(SRC, "squadvault", rel_path)
            if not os.path.exists(full_path):
                missing.append(f"{name} → {rel_path}")
        assert missing == [], (
            f"Contract-specified components missing:\n" +
            "\n".join(f"  {m}" for m in missing)
        )


# ── Constitution invariants ──────────────────────────────────────────

class TestConstitutionInvariants:
    """Invariants from the Canonical Operating Constitution."""

    def test_memory_events_is_append_only(self):
        """Constitution: Memory is append-only. No DELETE or UPDATE on memory_events."""
        violations = []
        for f in glob.glob(os.path.join(SRC, "squadvault", "**", "*.py"), recursive=True):
            if "__pycache__" in f:
                continue
            with open(f) as fh:
                for i, line in enumerate(fh, 1):
                    upper = line.upper().strip()
                    # Skip comments
                    if upper.startswith("#"):
                        continue
                    if ("DELETE FROM MEMORY_EVENTS" in upper or
                        "UPDATE MEMORY_EVENTS" in upper):
                        violations.append(f"{f}:{i}")
        assert violations == [], (
            f"Constitution violation: memory_events must be append-only.\n"
            f"Found DELETE/UPDATE:\n" + "\n".join(f"  {v}" for v in violations)
        )

    def test_no_autonomous_publish(self):
        """Constitution: Human approval gates all publication. No auto-publish."""
        # Check that recap_artifacts state machine requires explicit approval
        from squadvault.core.recaps.recap_artifacts import _ALLOWED_TRANSITIONS
        # DRAFT -> APPROVED must exist (requires human action)
        assert ("DRAFT", "APPROVED") in _ALLOWED_TRANSITIONS
        # There must not be a direct path from any state to PUBLISHED
        for old, new in _ALLOWED_TRANSITIONS:
            assert new != "PUBLISHED", "PUBLISHED state would violate human-in-the-loop"

    def test_schema_has_append_only_memory(self):
        """Schema must define memory_events as the core append-only table."""
        schema = open(SCHEMA_PATH).read()
        assert "CREATE TABLE IF NOT EXISTS memory_events" in schema


# ── Artifact state machine ───────────────────────────────────────────

class TestArtifactStateMachine:
    """Validate artifact lifecycle state machine matches governance."""

    def test_valid_transitions_only(self):
        """Only DRAFT→APPROVED, DRAFT→WITHHELD, APPROVED→SUPERSEDED are allowed."""
        from squadvault.core.recaps.recap_artifacts import _ALLOWED_TRANSITIONS
        expected = {
            ("DRAFT", "APPROVED"),
            ("DRAFT", "WITHHELD"),
            ("APPROVED", "SUPERSEDED"),
        }
        assert _ALLOWED_TRANSITIONS == expected

    def test_approved_requires_approved_by(self):
        """approve_recap_artifact must require approved_by parameter."""
        import inspect
        from squadvault.core.recaps.recap_artifacts import approve_recap_artifact
        sig = inspect.signature(approve_recap_artifact)
        assert "approved_by" in sig.parameters


# ── Preflight gate exists and blocks fabrication ─────────────────────

class TestPreflightGovernance:
    """The preflight gate must block generation when data is missing."""

    def test_empty_events_blocks_generation(self):
        """Preflight must return DO_NOT_GENERATE when canonical events are empty."""
        from squadvault.recaps.preflight import (
            PreflightVerdictType,
            recap_preflight_verdict,
        )
        v = recap_preflight_verdict(
            league_id="L1", season=2024, week=1, canonical_events=[],
        )
        assert v.verdict == PreflightVerdictType.DO_NOT_GENERATE


# ── EAL restraint defaults ──────────────────────────────────────────

class TestEALGovernance:
    """EAL must default to restraint, not engagement."""

    def test_missing_inputs_default_to_silence(self):
        """EAL must prefer silence when inputs are missing."""
        from squadvault.core.eal.eal_calibration_v1 import (
            RestraintDirective,
            derive_restraint_directive,
        )
        result = derive_restraint_directive(
            window_id="w1",
            signal_count=None,
            ambiguity=None,
            grouping_density=None,
            calibration=None,
        )
        assert result == RestraintDirective.prefer_silence

    def test_all_inputs_present_still_restrained(self):
        """Even with full inputs, EAL defaults to high_restraint (not neutral)."""
        from squadvault.core.eal.eal_calibration_v1 import (
            RestraintDirective,
            default_system_calibration_record,
            derive_restraint_directive,
        )
        cal = default_system_calibration_record()
        result = derive_restraint_directive(
            window_id="w1",
            signal_count=10,
            ambiguity=0.1,
            grouping_density=0.1,
            calibration=cal,
        )
        assert result == RestraintDirective.high_restraint


# ── Platform guardrails in code ──────────────────────────────────────

class TestPlatformGuardrails:
    """What SquadVault Is Not — enforced structurally."""

    def test_no_prediction_or_ranking_modules(self):
        """No files named 'predict', 'rank', 'optimize', or 'score' in core/."""
        forbidden_patterns = ["predict", "ranking", "optimize", "scoring"]
        violations = []
        for f in glob.glob(os.path.join(SRC, "squadvault", "core", "**", "*.py"), recursive=True):
            basename = os.path.basename(f).lower()
            for pattern in forbidden_patterns:
                if pattern in basename:
                    violations.append(f)
        assert violations == [], (
            f"Platform guardrail violation: found prediction/ranking/optimization files:\n" +
            "\n".join(f"  {v}" for v in violations)
        )

    def test_no_engagement_tracking_in_core(self):
        """Core must not contain engagement, analytics, or notification modules."""
        forbidden = ["engagement", "analytics", "notification", "dashboard"]
        violations = []
        for f in glob.glob(os.path.join(SRC, "squadvault", "core", "**", "*.py"), recursive=True):
            basename = os.path.basename(f).lower()
            for pattern in forbidden:
                if pattern in basename:
                    violations.append(f)
        assert violations == [], (
            f"Platform guardrail violation:\n" +
            "\n".join(f"  {v}" for v in violations)
        )


# ── Error hierarchy exists and is used ───────────────────────────────

class TestErrorHierarchy:
    """SquadVaultError hierarchy must exist and be importable."""

    def test_error_classes_importable(self):
        """All error classes from errors.py must be importable."""
        from squadvault.errors import (
            SquadVaultError,
            RecapNotFoundError,
            RecapStateError,
            RecapDataError,
            ChronicleError,
            ConfigError,
            SchemaError,
        )
        assert issubclass(RecapNotFoundError, SquadVaultError)
        assert issubclass(RecapStateError, SquadVaultError)
        assert issubclass(RecapDataError, SquadVaultError)
        assert issubclass(ChronicleError, SquadVaultError)
        assert issubclass(ConfigError, SquadVaultError)
        assert issubclass(SchemaError, SquadVaultError)

    def test_lifecycle_uses_proper_errors(self):
        """weekly_recap_lifecycle must not use SystemExit in business logic."""
        filepath = os.path.join(SRC, "squadvault", "recaps", "weekly_recap_lifecycle.py")
        with open(filepath) as f:
            for i, line in enumerate(f, 1):
                if "raise SystemExit" in line:
                    pytest.fail(
                        f"weekly_recap_lifecycle.py:{i} still uses SystemExit. "
                        f"Use SquadVaultError subclasses instead."
                    )

    def test_no_systemexit_in_business_logic(self):
        """No non-main function should raise SystemExit — use SquadVaultError subclasses."""
        import ast

        issues = []
        for f in glob.glob(os.path.join(SRC, "squadvault", "**", "*.py"), recursive=True):
            if "__pycache__" in f:
                continue
            with open(f) as fh:
                try:
                    tree = ast.parse(fh.read())
                except SyntaxError:
                    continue
            short = f.replace(SRC + "/squadvault/", "")
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name in ("main",):
                        continue
                    for child in ast.walk(node):
                        if isinstance(child, ast.Raise) and child.exc:
                            if isinstance(child.exc, ast.Call):
                                func = child.exc.func
                                if isinstance(func, ast.Name) and func.id == "SystemExit":
                                    issues.append(f"{short}: {node.name}() line {child.lineno}")
        assert issues == [], (
            f"SystemExit in business logic (use SquadVaultError subclasses):\n" +
            "\n".join(f"  {i}" for i in issues)
        )
