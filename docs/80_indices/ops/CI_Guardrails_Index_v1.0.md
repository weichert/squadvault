# SquadVault — CI Guardrails Index (v1.0)

This index enumerates **active, enforced CI guardrails** for the SquadVault ingest system.


<!-- SV_PATCH: nac fingerprint preflight doc (v1) -->
- **NAC fingerprint preflight normalization (Golden Path):** `scripts/prove_golden_path.sh` detects placeholder `Selection fingerprint: test-fingerprint` and normalizes it to a **64-lower-hex** fingerprint **in a temp copy used only for NAC validation (non-mutating)** before running the NAC harness (required by `Tests/_nac_check_assembly_plain_v1.py`). **Exports are ephemeral by default** (temp export root); set `SV_KEEP_EXPORTS=1` to persist exports under `artifacts/`.
<!-- /SV_PATCH: nac fingerprint preflight doc (v1) -->

## Operator Safety Note (Build Mode)

When running inspection commands from interactive shells (e.g. zsh), avoid leaking `set -u` into your session.
Use either a subshell:

- `( set -euo pipefail; <command> )`

or the canonical helper:

- `./scripts/strict_subshell_v1.sh '<command>'`


## Active Guardrails
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

- Guardrails listed here are **runtime-enforced**, not advisory.
- Any addition to this index must correspond to a concrete, testable enforcement mechanism.

- **ENV determinism envelope:**  
  → [ENV_Determinism_Invariant_v1.0.md](../../ops/invariants/ENV_Determinism_Invariant_v1.0.md)


## Ops Bundles

## Python Shim
- [CI Python Shim Compliance Gate (v1.0)](CI_Python_Shim_Compliance_Gate_v1.0.md)


- `scripts/ops_bundle_ci_docs_hardening_v1.sh` — CI + docs hardening sweep (idempotent; runs via `scripts/ops_orchestrate.sh`).

- `docs/80_indices/ops/Docs_Integrity_Gate_Invariant_v1.0.md`  <!-- ci_guardrails_index_add_docs_integrity_link_v1 -->

## Local-only helpers (not invoked by CI)

- `scripts/prove_local_clean_then_ci_v3.sh` — local-only helper: cleans *only* untracked scratch files named `scripts/_patch__*.py` and `scripts/patch__*.sh` (dry-run by default; requires `SV_LOCAL_CLEAN=1` to delete), then runs `bash scripts/prove_ci.sh`
- [CI Patcher/Wrapper Pairing Gate (v1.0)](CI_Patcher_Wrapper_Pairing_Gate_v1.0.md)
