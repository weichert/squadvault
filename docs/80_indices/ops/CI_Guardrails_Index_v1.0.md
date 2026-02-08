# SquadVault — CI Guardrails Index (v1.0)

This index enumerates **active, enforced CI guardrails** for the SquadVault ingest system.

## How to Read This Index

- **Active Guardrails** are enforced by CI and will fail builds if violated.
- Sections explicitly labeled **local-only** document helpers or hygiene practices that are *not* invoked by CI.
- If a guardrail appears here, it must correspond to a concrete enforcement mechanism.

## Operator Safety Note (Build Mode)
When running inspection commands from interactive shells (e.g. zsh), avoid leaking `set -u` into your session.
Use either a subshell:

- `( set -euo pipefail; <command> )`

or the canonical helper:

- `./scripts/strict_subshell_v1.sh '<command>'`

## Contents
- [Operator Safety Note (Build Mode)](#operator-safety-note-build-mode)
<!-- SV_BEGIN: ops_entrypoints_toc (v1) -->
- [Ops Entrypoints (Canonical)](#ops-entrypoints-canonical)
<!-- SV_END: ops_entrypoints_toc (v1) -->

- [Active Guardrails](#active-guardrails)
- [Proof Surface](#proof-surface)
- [Notes](#notes)
- [Ops Bundles](#ops-bundles)
- [Guardrails Development](#guardrails-development)
- [CWD Independence](#cwd-independence)
- [Local-only helpers (not invoked by CI)](#local-only-helpers-not-invoked-by-ci)
- [Local Workstation Hygiene](#local-workstation-hygiene)

<!-- SV_BEGIN: ops_entrypoints_hub (v1) -->
## Ops Entrypoints (Canonical)

If you are unsure where to start, use this section.

- [Ops Entrypoints Hub (v1.0)](Ops_Entrypoints_Hub_v1.0.md)
- [Canonical Indices Map (v1.0)](Canonical_Indices_Map_v1.0.md)
- [Process Discipline Index (v1.0)](Process_Discipline_Index_v1.0.md)
- [Recovery Workflows Index (v1.0)](Recovery_Workflows_Index_v1.0.md)
- [Ops Rules — One Page (v1.0)](Ops_Rules_One_Page_v1.0.md)
- [New Contributor Orientation (10 min) (v1.0)](New_Contributor_Orientation_10min_v1.0.md)
<!-- SV_END: ops_entrypoints_hub (v1) -->

## Active Guardrails
<!-- SV_PATCH: nac fingerprint preflight doc (v1) -->
- **NAC fingerprint preflight normalization (Golden Path):** `scripts/prove_golden_path.sh` detects placeholder `Selection fingerprint: test-fingerprint` and normalizes it to a **64-lower-hex** fingerprint **in a temp copy used only for NAC validation (non-mutating)** before running the NAC harness (required by `Tests/_nac_check_assembly_plain_v1.py`). **Exports are ephemeral by default** (temp export root); set `SV_KEEP_EXPORTS=1` to persist exports under `artifacts/`.
<!-- /SV_PATCH: nac fingerprint preflight doc (v1) -->

### Docs Integrity Guardrail
- **Status:** ACTIVE (enforced)
- **Entrypoint:** `scripts/prove_ci.sh`
- **Enforcement:** `scripts/prove_docs_integrity_v1.sh`
- **Invariant:** Enforces structural governance invariants for canonical docs; fail-closed.
- **Details:**  
  → [Docs_Integrity_Gate_Invariant_v1.0.md](./Docs_Integrity_Gate_Invariant_v1.0.md)

### CI Cleanliness & Determinism Guardrail
- **Status:** ACTIVE (enforced)
- **Entrypoint:** `scripts/prove_ci.sh`
- **Invariant:** CI proofs must not modify the git working tree.
- **Details:**  
  → [CI_Cleanliness_Invariant_v1.0.md](./CI_Cleanliness_Invariant_v1.0.md)

### Filesystem Ordering Determinism Guardrail
<!-- SV_PATCH: filesystem ordering gate ignores pyc/__pycache__ (v1) -->
### Filesystem Ordering Determinism — Bytecode Exclusion
The filesystem ordering determinism gate intentionally ignores:

- `__pycache__/` directories
- `*.pyc` Python bytecode files

Rationale:
- bytecode is **not** a source-of-truth input
- local `py_compile` runs can embed incidental string fragments
- scanning bytecode creates **false positives** unrelated to real ordering bugs

This exclusion is **narrow**, **portable (BSD/GNU compatible)**, and does **not** weaken
ordering guarantees for tracked source files.
<!-- /SV_PATCH: filesystem ordering gate ignores pyc/__pycache__ (v1) -->

- **Status:** ACTIVE (enforced)
- **Entrypoint:** `scripts/prove_ci.sh`
- **Enforcement:** `scripts/check_filesystem_ordering_determinism.sh`
- **Invariant:** CI must reject nondeterministic filesystem ordering dependencies.
- **Details:**  
  → [Filesystem_Ordering_Determinism_Invariant_v1.0.md](../../ops/invariants/Filesystem_Ordering_Determinism_Invariant_v1.0.md)

### Time & Timestamp Determinism Guardrail
- **Status:** ACTIVE (enforced)
- **Entrypoint:** `scripts/prove_ci.sh`
- **Enforcement:** `scripts/check_time_timestamp_determinism.sh`
- **Invariant:** CI must reject unsafe wall-clock time usage and implicit local-time conversions unless explicitly allowlisted.
- **Notes:** `SV_TIME_OK` is the inline escape hatch for deliberate exceptions.

## Proof Surface

- `scripts/prove_idempotence_allowlist_noop_in_idempotence_mode_v1.sh` — Allowlisted patch wrappers are no-op under `SV_IDEMPOTENCE_MODE=1`.
- **CI Proof Surface Registry (v1.0)**  
  Canonical, frozen list of all proof runners invoked by CI.  
  → docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md

## Notes
- Unless explicitly marked as **local-only**, guardrails listed in **Active Guardrails** are **runtime-enforced**, not advisory.
- Any addition to this index must correspond to a concrete, testable enforcement mechanism.

- **ENV determinism envelope:**  
  → [ENV_Determinism_Invariant_v1.0.md](../../ops/invariants/ENV_Determinism_Invariant_v1.0.md)

## Ops Bundles

## Python Shim
- [CI Python Shim Compliance Gate (v1.0)](CI_Python_Shim_Compliance_Gate_v1.0.md)

- `scripts/ops_bundle_ci_docs_hardening_v1.sh` — CI + docs hardening sweep (idempotent; runs via `scripts/ops_orchestrate.sh`).

- `docs/80_indices/ops/Docs_Integrity_Gate_Invariant_v1.0.md`  <!-- ci_guardrails_index_add_docs_integrity_link_v1 -->

## Guardrails Development
- [CI Guardrails Extension Playbook (v1.0)](CI_Guardrails_Extension_Playbook_v1.0.md)

## CWD Independence
- [CI CWD Independence Gate (Shims) (v1.0)](CI_CWD_Independence_Shims_Gate_v1.0.md)

## Local-only helpers (not invoked by CI)
_CI never invokes anything in this section._

- `scripts/prove_local_shell_hygiene_v1.sh` — local-only helper: validates bash nounset startup/teardown safety (SV_NOUNSET_GUARDS_V1)

- `scripts/prove_local_clean_then_ci_v3.sh` — local-only helper: cleans *only* untracked scratch files named `scripts/_patch__*.py` and `scripts/patch__*.sh` (dry-run by default; requires `SV_LOCAL_CLEAN=1` to delete), then runs `bash scripts/prove_ci.sh`
- [CI Patcher/Wrapper Pairing Gate (v1.0)](CI_Patcher_Wrapper_Pairing_Gate_v1.0.md)

## Local Workstation Hygiene
- [Local Bash Nounset Guards (v1.0)](Local_Bash_Nounset_Guards_v1.0.md)

<!-- PATCHER_WRAPPER_LINKS_v1_BEGIN -->
## Related Process Docs

- **Canonical Patcher / Wrapper Pattern (v1.0):** `docs/process/Canonical_Patcher_Wrapper_Pattern_v1.0.md`  
  Required for operational, CI, and documentation mutations. Prefer the reference implementation:
  `scripts/_patch_example_noop_v1.py` + `scripts/patch_example_noop_v1.sh`.

<!-- PATCHER_WRAPPER_LINKS_v1_END -->


- [Process Discipline Index (v1.0)](Process_Discipline_Index_v1.0.md)

- [Recovery Workflows Index (v1.0)](Recovery_Workflows_Index_v1.0.md)

- [Canonical Indices Map (v1.0)](Canonical_Indices_Map_v1.0.md)


<!-- SV_DOCS_MUTATION_DISCOVERABILITY: rules_of_engagement (v1) -->
- docs/process/rules_of_engagement.md — Docs + CI Mutation Policy (Enforced)

<!-- SV_DOCS_MUTATION_GUARDRAIL_GATE: v2 (v1) -->
- scripts/gate_docs_mutation_guardrail_v2.sh — Docs Mutation Guardrail Gate (canonical)
<!-- SV_CI_PROOF_SURFACE_REGISTRY: v1 -->
- scripts/check_ci_proof_surface_matches_registry_v1.sh — CI Proof Surface Registry Gate (canonical)
<!-- SV_CI_REGISTRY_EXECUTION_ALIGNMENT: v1 -->
- scripts/gate_ci_registry_execution_alignment_v1.sh — CI Registry → Execution Alignment Gate (v1)

<!-- SV_TERMINAL_BANNER_GATE_ENTRY_v1_BEGIN -->
## Terminal Banner Paste Gate (canonical)

- **Gate:** `scripts/gate_no_terminal_banner_paste_v1.sh`
- **Purpose:** Prevent pasted terminal/session banners (e.g., “Last login:”, zsh default shell banner) from entering tracked scripts/docs.
- **Escape hatch (emergency only):** `SV_ALLOW_TERMINAL_BANNER_PASTE=1`
  - Behavior: prints a clear `WARN`, skips enforcement, exits `0`.
  - Use: only to unblock urgent work; remove banner paste and re-run CI before merging.
- **Scan scope (fast + deterministic):** restricted to likely text files under `scripts/`:
  - `scripts/**/*.sh`
  - `scripts/**/*.py`
  - `scripts/**/*.md`
  - `scripts/**/*.txt`
- **Pattern discipline:** banner patterns are **anchored to start-of-line** (`^`) intentionally to avoid “self-matches”
  inside patchers/docs/gates (the gate should detect **pasted output**, not pattern literals embedded in source).

### Standard: text pathspecs for scan-based gates
When a gate scans `scripts/`, prefer a **pathspec allowlist** using git’s glob-magic pathspecs (avoid scanning unexpected types):

- `:(glob)scripts/**/*.sh`
- `:(glob)scripts/**/*.py`
- `:(glob)scripts/**/*.md`
- `:(glob)scripts/**/*.txt`

### Standard: “latest wrapper” convention
For a given patch family, treat the **highest version wrapper** as the canonical entrypoint:

- Example: `scripts/patch_*_v4.sh` supersedes `*_v3.sh`, etc.
- Older versions remain for auditability and historical provenance.
- scripts/prove_no_terminal_banner_paste_gate_behavior_v1.sh — Proof: terminal banner paste gate behavior (v1)

<!-- SV_TERMINAL_BANNER_GATE_ENTRY_v1_END -->

<!-- PROOF_SUITE_COMPLETENESS_GATE_v1_BEGIN -->
### Proof suite completeness gate (v1)

**Invariant (fail-closed):** every `scripts/prove_*.sh` proof runner **must** be referenced in the canonical Proof Surface Registry, and the registry list must match the filesystem list **exactly**.

- Gate: `scripts/gate_proof_suite_completeness_v1.sh`
- Wired by: `scripts/prove_ci.sh` (inserted under `SV_ANCHOR: docs_gates (v1)`)
- Registry: `docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md`
- Purpose: prevents proof coverage drift (new/removed proof runner scripts that CI would otherwise miss)

<!-- PROOF_SUITE_COMPLETENESS_GATE_v1_END -->

<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->
## CI guardrails entrypoints (bounded)

# NOTE:
# - This section is enforced by scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh
- scripts/gate_ops_indices_no_autofill_placeholders_v1.sh — Enforce Ops indices contain no autofill placeholders (v1)
# - Only list gate/check entrypoints you intend to be validated as discoverable.
# - Format: `- scripts/<path> — description`

- scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh — Ops index ↔ prove_ci gate execution parity (v1)
- scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh — Enforce bounded Ops guardrails entrypoints section + TOC completeness (v2)
- scripts/gate_ci_proof_surface_registry_index_discoverability_v1.sh — Prove Ops index contains proof-surface registry discoverability marker + bullet (v1)
- scripts/gate_ci_registry_execution_alignment_v1.sh — Enforce CI proof registry ↔ prove_ci execution alignment (v1)
- scripts/gate_docs_integrity_v2.sh — Docs integrity gate: enforce canonical docs invariants (v2)
- scripts/gate_docs_mutation_guardrail_v2.sh — Guardrail: proofs must not mutate docs unexpectedly (v2)
- scripts/gate_enforce_test_db_routing_v1.sh — Enforce CI uses temp working DB copy (fixture immutable) (v1)
- scripts/gate_no_bare_chevron_markers_v1.sh — Disallow bare '==>' marker lines in scripts/*.sh (v1)
- scripts/gate_no_double_scripts_prefix_v2.sh — Disallow 'scripts/scripts/' path invocations (v2)
- scripts/gate_no_terminal_banner_paste_v1.sh — Detect pasted terminal banner content in scripts/ (v1)
- scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh — Enforce patch-wrapper allowlist is canonical + safe (v1)
- scripts/gate_proof_suite_completeness_v1.sh — Enforce proof runners match registry exactly (v1)
<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->
