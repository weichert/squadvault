"""Gate test: new top-level docs/ files must be accompanied by a Map touch.

Enforces Reset Memo v1.0 section 6.3: a binding document is not binding until
registered in the Documentation Map. The gate script
`scripts/gate_docs_map_registration_v1.sh` catches this at commit time;
these tests verify the static invariants the gate is designed to protect.

Two classes of invariant are tested:

1. Gate script exists and is wired into the pre-commit hook -- structural
   proof that the gate will actually run.
2. Current top-level docs/ files are all Map-adjacent (Map versions or patch
   addenda) or are legacy files pre-dating the gate -- filesystem proof that
   no unregistered binding document has already slipped in.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
GATE_SCRIPT = REPO_ROOT / "scripts" / "gate_docs_map_registration_v1.sh"
PRE_COMMIT_TRACKED = REPO_ROOT / "scripts" / "git-hooks" / "pre-commit_v1.sh"

# Top-level docs/ files that pre-date the gate (registered or grandfathered).
# Any file added to docs/ top-level AFTER the gate ships must be accompanied
# by a Map modification in the same commit; those files then join this set on
# the next sweep of this allowlist.
_GRANDFATHERED_TOP_LEVEL_DOCS = {
    # Map versions
    "SquadVault_Documentation_Map_v1.5.docx",
    "SquadVault_Documentation_Map_v1_6.md",
    "SquadVault_Documentation_Map_v1_7.md",
    # Patch addenda
    "map_patch_2026_05_14_template_registration.md",
    "map_patch_2026_05_16_f1_sat_provisional.md",
    "map_patch_2026_06_09_state_ledger.md",
    "map_patch_2026_06_09_document_of_record.md",
    "map_patch_2026_06_10_w6_consent_governance.md",
    "map_patch_2026_06_22_w5_trophy_taxonomy.md",
    "map_patch_2026_07_04_narrative_presentation_spec.md",
    "map_patch_2026_07_05_completion_plan_v1_4.md",
    # Binding docs registered via the patch addenda above
    "SquadVault_W6_Consent_Governance_Memo_v1_2.md",
    "SquadVault_W5_Trophy_Taxonomy_DJ_Input_v1_2_2026_06_21.md",
    "Narrative_Presentation_Spec_v1_0.md",
    "SquadVault_Completion_Plan_v1_4_2026_07_05.md",
    # Operational read-model (Charter v1.0 section 4; registered via the patch above)
    "STATE.md",
    # Product plan of record (Charter-named; registered via the patch above) - E1.3
    "SquadVault_Product_Document_of_Record_v2_1.md",
    # Legacy binding addendum (pre-dates gate; registered in Map v1.6+)
    "SquadVault_IRP_Playbook_Authority_Clarification_Addendum.docx",
}


def _top_level_docs_files() -> set[str]:
    """All tracked files directly in docs/ (not in subdirectories)."""
    if not DOCS_DIR.exists():
        return set()
    return {
        p.name
        for p in DOCS_DIR.iterdir()
        if p.is_file() and p.suffix in {".md", ".docx", ".pdf"}
    }


class TestGateScriptPresence:
    """The gate script must exist and be wired into the pre-commit hook."""

    def test_gate_script_exists(self) -> None:
        """scripts/gate_docs_map_registration_v1.sh must exist."""
        assert GATE_SCRIPT.exists(), (
            f"Gate script missing: {GATE_SCRIPT}. "
            "Per Reset Memo v1.0 section 6.3, the docs/ Map registration gate "
            "must be implemented."
        )

    def test_gate_script_is_executable(self) -> None:
        """Gate script must be executable."""
        assert GATE_SCRIPT.stat().st_mode & 0o111, (
            f"Gate script not executable: {GATE_SCRIPT}. "
            "Run: chmod +x scripts/gate_docs_map_registration_v1.sh"
        )

    def test_gate_wired_into_pre_commit_hook(self) -> None:
        """The tracked pre-commit hook must invoke the gate script."""
        assert PRE_COMMIT_TRACKED.exists(), (
            f"Tracked pre-commit hook missing: {PRE_COMMIT_TRACKED}"
        )
        hook_text = PRE_COMMIT_TRACKED.read_text(encoding="utf-8")
        assert "gate_docs_map_registration_v1.sh" in hook_text, (
            "gate_docs_map_registration_v1.sh is not wired into the tracked "
            "pre-commit hook at scripts/git-hooks/pre-commit_v1.sh. "
            "Add the gate call before the final 'OK: pre-commit checks passed' line."
        )


class TestTopLevelDocsAllowlist:
    """All top-level docs/ files must be in the grandfathered set.

    Any file added to docs/ top-level after the gate ships must appear here,
    confirming it was accompanied by a Map modification at the time of addition.
    If a new file appears in docs/ but not in this allowlist, it means either:
      (a) the gate was bypassed (SV_SKIP_PRECOMMIT=1), or
      (b) the allowlist was not updated after a legitimate addition.
    Either case is a finding; this test surfaces it.
    """

    def test_no_unregistered_top_level_docs_files(self) -> None:
        """Every top-level docs/ file must be in the allowlist."""
        actual = _top_level_docs_files()
        unexpected = sorted(actual - _GRANDFATHERED_TOP_LEVEL_DOCS)
        assert not unexpected, (
            f"Unexpected top-level docs/ file(s) not in the gate allowlist:\n"
            + "\n".join(f"  {f}" for f in unexpected)
            + "\n\nIf this file was added legitimately (accompanied by a Map "
            "modification in the same commit), add it to "
            "_GRANDFATHERED_TOP_LEVEL_DOCS in this test file.\n"
            "If it was added without a Map modification, that is a "
            "Reset Memo v1.0 section 6.3 violation."
        )

    def test_grandfathered_files_still_exist(self) -> None:
        """Files in the grandfathered set should still exist (catches renames/removals)."""
        actual = _top_level_docs_files()
        persistent = {
            "SquadVault_Documentation_Map_v1_7.md",
            "map_patch_2026_05_14_template_registration.md",
            "map_patch_2026_05_16_f1_sat_provisional.md",
        }
        missing = sorted(persistent - actual)
        assert not missing, (
            f"Expected top-level docs/ file(s) no longer present: {missing}. "
            "If a Map version was superseded by a new version, update "
            "_GRANDFATHERED_TOP_LEVEL_DOCS and the persistent set in this test."
        )
