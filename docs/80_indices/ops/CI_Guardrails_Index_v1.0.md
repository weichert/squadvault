# SquadVault — CI Guardrails Index (v1.0)

This index enumerates **active, enforced CI guardrails** for the SquadVault ingest system.

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

- `scripts/ops_bundle_ci_docs_hardening_v1.sh` — CI + docs hardening sweep (idempotent; runs via `scripts/ops_orchestrate.sh`).

- `docs/80_indices/ops/Docs_Integrity_Gate_Invariant_v1.0.md`  <!-- ci_guardrails_index_add_docs_integrity_link_v1 -->
