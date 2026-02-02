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

## FROZEN DECLARATION (ENFORCED)

This registry defines the **complete, authoritative CI proof surface**.

**FROZEN:** CI may run only the proofs listed here. Any drift (addition/removal/rename) must:
1) update this registry via versioned patcher + wrapper, and
2) pass the enforcement gate.

This registry is intentionally boring and auditable.

## CI Entrypoint (GitHub Actions invokes this)

- scripts/prove_ci.sh — Single blessed CI entrypoint; runs gates + invokes all proof runners below.

## Proof Runners (invoked by scripts/prove_ci.sh)

- scripts/prove_eal_calibration_type_a_v1.sh — Proves EAL calibration Type A invariants end-to-end.
- scripts/prove_golden_path.sh — Proves canonical operator golden path via shims and gates.
- scripts/prove_rivalry_chronicle_end_to_end_v1.sh — Proves Rivalry Chronicle generate → approve → export flow.
- scripts/prove_signal_scout_tier1_type_a_v1.sh — Proves Signal Scout Tier-1 Type A derivation + determinism.
- scripts/prove_tone_engine_type_a_v1.sh — Proves Tone Engine Type A contract/invariants.
- scripts/prove_version_presentation_navigation_type_a_v1.sh — Proves version presentation + navigation invariants.

## Notes

- **No globbing. No discovery. No heuristics.**
- The enforcement gate compares this registry against **exact proof invocations in `scripts/prove_ci.sh`**.
