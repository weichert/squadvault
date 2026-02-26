## Canonical Proof Surface List (Machine-Managed)
This block is updated by `scripts/patch_ci_proof_surface_registry_machine_block_v1.sh`.
Do not edit manually.
<!-- SV_PROOF_SURFACE_LIST_v1_BEGIN -->

- scripts/prove_ci.sh
- scripts/prove_ci_creative_sharepack_if_available_v1.sh
- scripts/prove_contract_surface_autosync_noop_v1.sh
- scripts/prove_contract_surface_completeness_v1.sh
- scripts/prove_creative_determinism_v1.sh
- scripts/prove_creative_sharepack_determinism_v1.sh
- scripts/prove_docs_integrity_v1.sh
- scripts/prove_eal_calibration_type_a_v1.sh
- scripts/prove_golden_path.sh
- scripts/prove_idempotence_allowlist_noop_in_idempotence_mode_v1.sh
- scripts/prove_local_clean_then_ci_v3.sh
- scripts/prove_local_shell_hygiene_v1.sh
- scripts/prove_no_terminal_banner_paste_gate_behavior_v1.sh
- scripts/prove_pytest_does_not_dirty_fixture_db_v1.sh
- scripts/prove_rivalry_chronicle_end_to_end_v1.sh
- scripts/prove_signal_scout_tier1_type_a_v1.sh
- scripts/prove_tone_engine_type_a_v1.sh
- scripts/prove_version_presentation_navigation_type_a_v1.sh

<!-- SV_PROOF_SURFACE_LIST_v1_END -->
[SV_CANONICAL_HEADER_V1]
Contract Name: CI Proof Surface Registry
Version: v1.0
Status: CANONICAL — FROZEN

Defers To:
  - SquadVault — Canonical Operating Constitution (Tier 0)
  - SquadVault — Ops Shim & CWD Independence Contract (Ops)
  - SquadVault Development Playbook (MVP)

Default: Any behavior not explicitly permitted by this registry is forbidden.

—

# SquadVault — CI Proof Surface Registry (v1.0)


<!-- SV_PATCH: nac fingerprint preflight doc (v1) -->
- **NAC fingerprint preflight normalization (Golden Path):** `scripts/prove_golden_path.sh` detects placeholder `Selection fingerprint: test-fingerprint` and normalizes it to a **64-lower-hex** fingerprint **in a temp copy used only for NAC validation (non-mutating)** before running the NAC harness (required by `Tests/_nac_check_assembly_plain_v1.py`). **Exports are ephemeral by default** (temp export root); set `SV_KEEP_EXPORTS=1` to persist exports under `artifacts/`.
<!-- /SV_PATCH: nac fingerprint preflight doc (v1) -->

## FROZEN DECLARATION (ENFORCED)

This registry defines the **complete, authoritative CI proof surface**.

**FROZEN:** CI may run only the proofs listed here. Any drift (addition/removal/rename) must:
1) update this registry via versioned patcher + wrapper, and
2) pass the enforcement gate.

This registry is intentionally boring and auditable.

## CI Entrypoint (GitHub Actions invokes this)

- scripts/prove_ci.sh — Single blessed CI entrypoint; runs gates + invokes all proof runners below.

## Proof Runners (invoked by scripts/prove_ci.sh)

<!-- CI_PROOF_RUNNERS_BEGIN -->
- scripts/prove_contract_surface_autosync_noop_v1.sh — Proof: contract surface autosync no-op on canonical repo (v1)
- scripts/prove_contract_surface_completeness_v1.sh — Proof: contract surface completeness gate (v1)
- scripts/prove_creative_determinism_v1.sh — Prove: creative determinism drift guard (v1)
- scripts/prove_ci_creative_sharepack_if_available_v1.sh — Proof runner (CI): creative sharepack determinism if inputs present (v1)
- scripts/prove_docs_integrity_v1.sh — Proves canonical docs structural governance invariants (fail-closed).
- scripts/prove_eal_calibration_type_a_v1.sh — Proves EAL calibration Type A invariants end-to-end.
- scripts/prove_golden_path.sh — Proves canonical operator golden path via shims and gates (exports ephemeral by default; set `SV_KEEP_EXPORTS=1` to persist; NAC normalization is non-mutating).
- scripts/prove_idempotence_allowlist_noop_in_idempotence_mode_v1.sh — Proof: allowlisted patch wrappers are no-op under `SV_IDEMPOTENCE_MODE=1`.
- scripts/prove_no_terminal_banner_paste_gate_behavior_v1.sh — Proof: terminal banner paste gate behavior (v1)
- scripts/prove_rivalry_chronicle_end_to_end_v1.sh — Proves Rivalry Chronicle generate → approve → export flow.
- scripts/prove_signal_scout_tier1_type_a_v1.sh — Proves Signal Scout Tier-1 Type A derivation + determinism.
- scripts/prove_tone_engine_type_a_v1.sh — Proves Tone Engine Type A contract/invariants.
- scripts/prove_version_presentation_navigation_type_a_v1.sh — Proves version presentation + navigation invariants.
<!-- CI_PROOF_RUNNERS_END -->

## Notes

- **No globbing. No discovery. No heuristics.**
- The enforcement gate compares this registry against **exact proof invocations in `scripts/prove_ci.sh`**.

<!-- PROOF_SURFACE_REGISTRY_LOCAL_PROOFS_v1_BEGIN -->

### Local hygiene proofs (registered)

- `scripts/prove_local_clean_then_ci_v3.sh`
- `scripts/prove_local_shell_hygiene_v1.sh`

<!-- PROOF_SURFACE_REGISTRY_LOCAL_PROOFS_v1_END -->
<!-- SV_CI_EXECUTION_EXEMPT_v1_BEGIN -->

- scripts/prove_creative_sharepack_determinism_v1.sh
scripts/prove_local_clean_then_ci_v3.sh # local-only: developer workflow proof (not executed in CI)
scripts/prove_local_shell_hygiene_v1.sh # local-only: interactive shell hygiene proof (not executed in CI)
scripts/prove_pytest_does_not_dirty_fixture_db_v1.sh

<!-- SV_CI_EXECUTION_EXEMPT_v1_END -->

<!-- SV_RULE_GATE_VS_PROOF_BOUNDARY_v1_BEGIN -->
## Gate vs Proof Boundary (Canonical)

**Rule:** CI **gates** (`scripts/gate_*.sh`) are **not proofs** and must **never** appear in this registry.

- This file lists **proof surfaces** only (typically `scripts/prove_*.sh`).
- Enforcement scripts belong in the **Ops Guardrails Index** instead.

This boundary is CI-enforced by: **gate_proof_surface_registry_excludes_gates_v1**.
<!-- SV_RULE_GATE_VS_PROOF_BOUNDARY_v1_END -->

## Contract Surface Proofs

<!-- SV_CONTRACT_SURFACE_PROOFS_v1_BEGIN -->
- scripts/prove_contract_surface_autosync_noop_v1.sh — Proof: Contract surface autosync is a no-op on canonical repo (v1)
<!-- SV_CONTRACT_SURFACE_PROOFS_v1_END -->

<!-- SV_CI_PROOF_CREATIVE_SHAREPACK_IF_AVAILABLE_v1_BEGIN -->
- scripts/prove_ci_creative_sharepack_if_available_v1.sh — Proof runner (CI): creative sharepack determinism if inputs present (v1)
<!-- SV_CI_PROOF_CREATIVE_SHAREPACK_IF_AVAILABLE_v1_END -->

