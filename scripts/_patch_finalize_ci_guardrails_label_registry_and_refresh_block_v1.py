#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY = REPO_ROOT / "docs" / "80_indices" / "ops" / "CI_Guardrail_Entrypoint_Labels_v1.tsv"
DOC = REPO_ROOT / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"
RENDERER = REPO_ROOT / "scripts" / "_render_ci_guardrails_ops_entrypoints_block_v1.py"

BLOCK_BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
BLOCK_END = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

CANONICAL_ROWS = [
    "scripts/gate_allowlist_patchers_must_insert_sorted_v1.sh\tAllowlist patchers must insert sorted blocks (v1)",
    "scripts/gate_ci_guardrails_ops_entrypoint_exactness_v1.sh\tOps guardrails entrypoint block exactness gate (v1)",
    "scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh\tOps guardrails entrypoint parity gate (v1)",
    "scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh\tCI Guardrails ops entrypoints section + TOC (v2)",
    "scripts/gate_ci_milestones_latest_block_v1.sh\tEnforce CI_MILESTONES.md has exactly one bounded ## Latest block (v1)",
    "scripts/gate_ci_proof_runners_block_sorted_v1.sh\tCI proof runners block sorted gate (v1)",
    "scripts/gate_ci_proof_surface_registry_exactness_v1.sh\tCI proof surface registry exactness gate (v1)",
    "scripts/gate_ci_proof_surface_registry_index_discoverability_v1.sh\tCI proof surface registry discoverability in Ops index (v1)",
    "scripts/gate_ci_prove_ci_relative_script_invocations_v1.sh\tprove_ci relative script invocations gate (v1)",
    "scripts/gate_ci_registry_execution_alignment_v1.sh\tCI registry execution alignment gate (v1)",
    "scripts/gate_ci_runtime_envelope_v1.sh\tCI runtime envelope gate (v1)",
    "scripts/gate_contract_surface_manifest_hash_v1.sh\tContract surface manifest hash gate (v1)",
    "scripts/gate_contracts_index_discoverability_v1.sh\tContracts index discoverability gate (v1)",
    "scripts/gate_creative_surface_fingerprint_canonical_v1.sh\tCreative surface fingerprint canonical gate (v1)",
    "scripts/gate_creative_surface_fingerprint_v1.sh\tCreative surface fingerprint gate (v1)",
    "scripts/gate_creative_surface_registry_discoverability_v1.sh\tCreative surface registry discoverability gate (v1)",
    "scripts/gate_creative_surface_registry_parity_v1.sh\tCreative surface registry parity gate (v1)",
    "scripts/gate_creative_surface_registry_usage_v1.sh\tCreative surface registry usage gate (v1)",
    "scripts/gate_cwd_independence_shims_v1.sh\tCWD independence shims gate (v1)",
    "scripts/gate_docs_integrity_v2.sh\tDocs integrity gate (v2)",
    "scripts/gate_docs_mutation_guardrail_v2.sh\tDocs mutation guardrail gate (v2)",
    "scripts/gate_enforce_test_db_routing_v1.sh\tEnforce canonical test DB routing (v1)",
    "scripts/gate_meta_surface_parity_v1.sh\tMeta surface parity gate (v1)",
    "scripts/gate_no_bare_chevron_markers_v1.sh\tNo bare chevron markers in scripts gate (v1)",
    "scripts/gate_no_double_scripts_prefix_v2.sh\tNo double scripts prefix gate (v2)",
    "scripts/gate_no_mapfile_readarray_in_scripts_v1.sh\tNo mapfile/readarray in scripts gate (v1)",
    "scripts/gate_no_network_in_ci_proofs_v1.sh\tNo network/package-manager actions in CI proofs (v1)",
    "scripts/gate_no_obsolete_allowlist_rewrite_artifacts_v1.sh\tNo obsolete allowlist rewrite artifacts gate (v1)",
    "scripts/gate_no_terminal_banner_paste_v1.sh\tNo terminal banner paste gate (v1)",
    "scripts/gate_no_test_dir_case_drift_v1.sh\tNo test dir case drift gate (v1)",
    "scripts/gate_no_untracked_patch_artifacts_v1.sh\tNo untracked patch artifacts gate (v1)",
    "scripts/gate_no_xtrace_v1.sh\tNo forbidden set -x in prove/gate scripts (v1)",
    "scripts/gate_ops_indices_no_autofill_placeholders_v1.sh\tOps indices no autofill placeholders gate (v1)",
    "scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh\tPatch wrapper idempotence allowlist gate (v1)",
    "scripts/gate_proof_suite_completeness_v1.sh\tProof suite completeness gate (v1)",
    "scripts/gate_proof_surface_registry_excludes_gates_v1.sh\tProof surface registry excludes gates gate (v1)",
    "scripts/gate_prove_ci_structure_canonical_v1.sh\tprove_ci structure canonical gate (v1)",
    "scripts/gate_prove_ci_references_existing_scripts_v1.sh\tprove_ci references existing scripts gate (v1)",
    "scripts/gate_pytest_targets_are_tracked_v1.sh\tPytest targets are tracked gate (v1)",
    "scripts/gate_pytest_tracked_tests_only_v1.sh\tPytest tracked tests only gate (v1)",
    "scripts/gate_repo_clean_after_proofs_v1.sh\tRepo clean after proofs gate (v1)",
    "scripts/gate_rivalry_chronicle_contract_linkage_v1.sh\tRivalry Chronicle contract linkage gate (v1)",
    "scripts/gate_standard_show_input_need_coverage_v1.sh\tStandard show input need coverage gate (v1)",
    "scripts/gate_worktree_cleanliness_v1.sh\tWorktree cleanliness gate (v1)",
]

def parse_row(row: str) -> tuple[str, str]:
    if "\t" not in row:
        raise RuntimeError(f"invalid registry row: {row}")
    rel_path, label = row.split("\t", 1)
    rel_path = rel_path.strip()
    label = label.strip()
    if not rel_path or not label:
        raise RuntimeError(f"invalid registry row: {row}")
    return rel_path, label

def load_existing_registry() -> dict[str, str]:
    if not REGISTRY.is_file():
        raise RuntimeError(f"missing registry: {REGISTRY}")
    mapping: dict[str, str] = {}
    for raw in REGISTRY.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        rel_path, label = parse_row(raw)
        if rel_path in mapping and mapping[rel_path] != label:
            raise RuntimeError(f"conflicting registry row for {rel_path}")
        mapping[rel_path] = label
    return mapping

def render_block() -> str:
    try:
        return subprocess.check_output(
            [sys.executable, str(RENDERER)],
            text=True,
            encoding="utf-8",
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "renderer invocation failed:\n"
            f"{exc.output}"
        ) from exc

def replace_bounded_block(doc_text: str, new_block: str) -> str:
    pattern = re.compile(
        re.escape(BLOCK_BEGIN) + r".*?" + re.escape(BLOCK_END),
        re.DOTALL,
    )
    match = pattern.search(doc_text)
    if not match:
        raise RuntimeError("bounded CI guardrails block not found in docs index")
    return doc_text[:match.start()] + new_block.rstrip("\n") + "\n" + doc_text[match.end():]

def main() -> int:
    existing = load_existing_registry()
    for row in CANONICAL_ROWS:
        rel_path, label = parse_row(row)
        if rel_path in existing and existing[rel_path] != label:
            raise RuntimeError(
                f"registry row mismatch for {rel_path}: "
                f"have {existing[rel_path]!r}, want {label!r}"
            )
        existing[rel_path] = label

    new_registry_text = "\n".join(
        f"{rel_path}\t{existing[rel_path]}" for rel_path in sorted(existing)
    ) + "\n"
    old_registry_text = REGISTRY.read_text(encoding="utf-8")
    if old_registry_text != new_registry_text:
        REGISTRY.write_text(new_registry_text, encoding="utf-8")

    new_block = render_block()
    old_doc_text = DOC.read_text(encoding="utf-8")
    new_doc_text = replace_bounded_block(old_doc_text, new_block)
    if old_doc_text != new_doc_text:
        DOC.write_text(new_doc_text, encoding="utf-8")

    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
