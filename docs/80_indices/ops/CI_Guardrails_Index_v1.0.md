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
- [Active Guardrails](#active-guardrails)
- [Proof Surface](#proof-surface)
- [Notes](#notes)
- [Ops Bundles](#ops-bundles)
- [Guardrails Development](#guardrails-development)
- [CWD Independence](#cwd-independence)
- [Local-only helpers (not invoked by CI)](#local-only-helpers-not-invoked-by-ci)
- [Local Workstation Hygiene](#local-workstation-hygiene)

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
