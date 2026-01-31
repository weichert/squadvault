# SquadVault — CI Guardrails Index (v1.0)

This index enumerates **active, enforced CI guardrails** for the SquadVault ingest system.

## Active Guardrails

### CI Cleanliness & Determinism Guardrail
- **Status:** ACTIVE (enforced)
- **Entrypoint:** `scripts/prove_ci.sh`
- **Invariant:** CI proofs must not modify the git working tree.
- **Details:**  
  → [CI_Cleanliness_Invariant_v1.0.md](./CI_Cleanliness_Invariant_v1.0.md)

## Notes

- Guardrails listed here are **runtime-enforced**, not advisory.
- Any addition to this index must correspond to a concrete, testable enforcement mechanism.
