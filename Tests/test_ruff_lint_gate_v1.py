"""Gate test: the ruff lint gate exists and is wired into the pre-commit hook.

Unit E1.2 (pre-commit gate hardening). ruff's absence from pre-commit is what
let R1's 10 lint errors reach HEAD before CI caught them. These tests are the
static proof that the gate exists, is executable, and runs at commit time.

Mirrors the precedent in Tests/test_docs_map_registration_gate_v1.py.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GATE_SCRIPT = REPO_ROOT / "scripts" / "gate_ruff_lint_v1.sh"
PRE_COMMIT_TRACKED = REPO_ROOT / "scripts" / "git-hooks" / "pre-commit_v1.sh"
PROVE_CI = REPO_ROOT / "scripts" / "prove_ci.sh"


class TestRuffGatePresence:
    """The ruff gate must exist, be executable, and be wired into both surfaces."""

    def test_gate_script_exists(self) -> None:
        assert GATE_SCRIPT.exists(), (
            f"Ruff lint gate missing: {GATE_SCRIPT}. Per Unit E1.2 the pre-commit "
            "chain must run ruff at commit time."
        )

    def test_gate_script_is_executable(self) -> None:
        assert GATE_SCRIPT.stat().st_mode & 0o111, (
            f"Gate script not executable: {GATE_SCRIPT}. Run: chmod +x {GATE_SCRIPT}"
        )

    def test_gate_runs_ci_identical_command(self) -> None:
        """The gate must check the same surface CI lints (src/squadvault/)."""
        text = GATE_SCRIPT.read_text(encoding="utf-8")
        assert "ruff check src/squadvault/" in text, (
            "Ruff gate must run 'ruff check src/squadvault/' to match the CI Lint step."
        )

    def test_gate_wired_into_pre_commit_hook(self) -> None:
        assert PRE_COMMIT_TRACKED.exists(), f"Tracked pre-commit hook missing: {PRE_COMMIT_TRACKED}"
        hook_text = PRE_COMMIT_TRACKED.read_text(encoding="utf-8")
        assert "gate_ruff_lint_v1.sh" in hook_text, (
            "gate_ruff_lint_v1.sh is not wired into the tracked pre-commit hook at "
            "scripts/git-hooks/pre-commit_v1.sh. Add the gate call before the final "
            "'OK: pre-commit checks passed' line, and re-run the install step."
        )

    def test_gate_wired_into_prove_ci(self) -> None:
        """Registry parity (CI_Guardrail_Entrypoint_Labels) requires prove_ci to run it."""
        assert "gate_ruff_lint_v1.sh" in PROVE_CI.read_text(encoding="utf-8"), (
            "gate_ruff_lint_v1.sh must be invoked in prove_ci.sh so the guardrail "
            "registry (CI_Guardrail_Entrypoint_Labels_v1.tsv) stays in parity."
        )
