# Observations - Unit E1.2: Pre-commit gate hardening (add ruff)

**Date:** 2026-06-09
**Implementation commit:** `87c400f`
**HEAD at authoring:** `87c400f` (docs commit follows)
**Source brief:** `_observations/session_brief_e1_2_precommit_gate_hardening.md`
**Discharges:** Roadmap section 7.3 standing item; Document of Record v2.1 Unit E1.2.

---

## What shipped

- `scripts/gate_ruff_lint_v1.sh` - runs `ruff check src/squadvault/` (CI-identical),
  repo-root anchored, bash3-safe, no xtrace.
- Wired into BOTH `scripts/git-hooks/pre-commit_v1.sh` (gate 5) AND `scripts/prove_ci.sh`.
- `Tests/test_ruff_lint_gate_v1.py` - asserts the gate exists, is executable, runs the
  CI-identical command, and is wired into the hook and prove_ci.
- Registry parity threaded (see finding below).

## Decision

D-A adjudicated by founder: **ruff yes, pytest no.** Full suite is ~99s and prove_ci
owns it; ruff's absence is the gap that let R1 land. No pytest subset at commit time.

## Finding: registration is the hard part, exactly as the F2/F5 lesson warned

Adding the gate to the hook is trivial. Making it *registered* is not - the guardrail
surface is a tightly-coupled registry enforced by ~15 parity gates. A new pre-commit gate
must be invoked in `prove_ci.sh` (the registry-completeness gate requires every
`CI_Guardrail_Entrypoint_Labels_v1.tsv` row to be executed by prove_ci), which then
cascades through:
- `CI_Guardrail_Entrypoint_Labels_v1.tsv` - label source-of-truth (add sorted row).
- `CI_Guardrails_Index_v1.0.md` - the rendered entrypoints block (regenerate via
  `scripts/_render_ci_guardrails_ops_entrypoints_block_v1.py`, do not hand-edit).
- `CI_Guardrails_Surface_Fingerprint_v1.txt` - the `surface_freeze` gate pins a sha256
  over prove_ci + Labels TSV + Index; a legitimate surface change requires an explicit
  fingerprint bump (regenerated via `gen_ci_guardrails_surface_fingerprint_v1.py`).
- `README.md` Developer Setup - **was already stale** ("three gates"; reality was four).
  Corrected to five and all gates enumerated. This is a live instance of the exact
  enumeration-drift F2/F5 documents.

Method used (per brief): make the change, run the fast guardrail gates directly, resolve
every ERROR. Only `surface_freeze` failed on first pass (expected - the deliberate
freeze); bumping the fingerprint cleared it. All guardrail gates green before commit.

## Verification

- Planted an F401 in `src/squadvault/utils/time.py`; the installed pre-commit hook
  BLOCKED (exit 1) at the ruff gate. Removed it; hook PASSED. Planted error reverted,
  never committed (acceptance criterion 1, both directions).
- ruff zero; mypy 158 clean; targeted gate tests green; all `gate_ci_guardrails_*`
  parity gates pass. prove_ci run on the clean tree (3.11 interpreter).
- The implementation commit `87c400f` itself passed all five pre-commit gates,
  including the new ruff gate - the gate is live and self-consistent.

## Carried forward

The Document of Record v2.1 is not in the repo, which is why the E1.x cluster could not
be retrieved from Claude Code while scoping E1.2 (founder supplied the entry). Candidate
to fold into E1.3's doc sweep so the retrieval gap does not recur. NOT actioned here.
