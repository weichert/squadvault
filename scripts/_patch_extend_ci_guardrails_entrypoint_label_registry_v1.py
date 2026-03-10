#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY = REPO_ROOT / "docs" / "80_indices" / "ops" / "CI_Guardrail_Entrypoint_Labels_v1.tsv"

REQUIRED_ROWS = [
    "scripts/gate_ci_proof_runners_block_sorted_v1.sh\tCI proof runners block sorted gate (v1)",
    "scripts/gate_ci_prove_ci_relative_script_invocations_v1.sh\tprove_ci relative script invocations gate (v1)",
    "scripts/gate_ci_runtime_envelope_v1.sh\tCI runtime envelope gate (v1)",
    "scripts/gate_contract_surface_manifest_hash_v1.sh\tContract surface manifest hash gate (v1)",
    "scripts/gate_contracts_index_discoverability_v1.sh\tContracts index discoverability gate (v1)",
    "scripts/gate_creative_surface_fingerprint_v1.sh\tCreative surface fingerprint gate (v1)",
    "scripts/gate_creative_surface_registry_discoverability_v1.sh\tCreative surface registry discoverability gate (v1)",
    "scripts/gate_meta_surface_parity_v1.sh\tMeta surface parity gate (v1)",
    "scripts/gate_no_mapfile_readarray_in_scripts_v1.sh\tNo mapfile/readarray in scripts gate (v1)",
    "scripts/gate_no_test_dir_case_drift_v1.sh\tNo test dir case drift gate (v1)",
    "scripts/gate_no_untracked_patch_artifacts_v1.sh\tNo untracked patch artifacts gate (v1)",
    "scripts/gate_proof_surface_registry_excludes_gates_v1.sh\tProof surface registry excludes gates gate (v1)",
    "scripts/gate_pytest_tracked_tests_only_v1.sh\tPytest tracked tests only gate (v1)",
    "scripts/gate_repo_clean_after_proofs_v1.sh\tRepo clean after proofs gate (v1)",
    "scripts/gate_rivalry_chronicle_contract_linkage_v1.sh\tRivalry Chronicle contract linkage gate (v1)",
    "scripts/gate_standard_show_input_need_coverage_v1.sh\tStandard show input need coverage gate (v1)",
]

def parse_row(row: str) -> tuple[str, str]:
    if "\t" not in row:
        raise RuntimeError(f"invalid required row: {row}")
    rel_path, label = row.split("\t", 1)
    rel_path = rel_path.strip()
    label = label.strip()
    if not rel_path or not label:
        raise RuntimeError(f"invalid required row: {row}")
    return rel_path, label

def main() -> int:
    if not REGISTRY.is_file():
        raise RuntimeError(f"missing registry: {REGISTRY}")

    existing_lines = REGISTRY.read_text(encoding="utf-8").splitlines()
    kept_lines: list[str] = []
    existing_map: dict[str, str] = {}

    for raw in existing_lines:
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        if line.lstrip().startswith("#"):
            kept_lines.append(line)
            continue
        rel_path, label = parse_row(line)
        if rel_path in existing_map and existing_map[rel_path] != label:
            raise RuntimeError(f"conflicting existing registry row for {rel_path}")
        existing_map[rel_path] = label

    changed = False
    for row in REQUIRED_ROWS:
        rel_path, label = parse_row(row)
        if rel_path in existing_map:
            if existing_map[rel_path] != label:
                raise RuntimeError(
                    f"registry row mismatch for {rel_path}: "
                    f"have {existing_map[rel_path]!r}, want {label!r}"
                )
            continue
        existing_map[rel_path] = label
        changed = True

    ordered_rows = [f"{rel_path}\t{existing_map[rel_path]}" for rel_path in sorted(existing_map)]
    new_text = "\n".join(ordered_rows) + "\n"
    old_text = REGISTRY.read_text(encoding="utf-8")
    if old_text != new_text:
        REGISTRY.write_text(new_text, encoding="utf-8")

    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
