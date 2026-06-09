# SESSION BRIEF - Unit E1.2: Pre-commit gate hardening (add ruff)

**Authored against engine HEAD `c082d0d`** (verify per charter section 3 before proceeding).
**Tool/model:** Claude Code / Opus 4.8 (EXECUTE unit; acceptance criteria below are binary).
**Source:** Document of Record v2.1, Unit E1.2 (= Completion Plan v1.0 Unit 1.2;
discharges Roadmap section 7.3 standing item).

## Decision (pre-adjudicated - do not re-litigate)

- **D-A adjudicated: ruff YES, pytest NO.** Add ruff to the pre-commit gate chain.
  Do NOT add a pytest smoke subset. Rationale: full suite is ~99s and prove_ci owns it;
  ruff's absence at commit time is what caused R1. Founder pick recorded 2026-06-09.

## Verified premises (checked at authoring; re-verify per section 3)

1. **E1.1 has landed** - `bf0833e` (ruff errors cleared) + ruff pinned in requirements.
   `ruff check src/squadvault/` returns zero at `c082d0d`. THEREFORE adding ruff to
   pre-commit will NOT retroactively block commits. No sequencing blocker; E1.2 runs standalone.
2. ruff is NOT currently in `scripts/git-hooks/pre-commit_v1.sh` (CI-only at `.github/workflows/ci.yml:52`).
3. Installed `.git/hooks/pre-commit` is in sync with the tracked hook at authoring.
4. Standing hazard: run prove_ci under a Python 3.11+ `python3` (default `/usr/local/bin/python3`
   is 3.10.4; see STATE.md). CI uses 3.12.

## Scope of work

**Primary edit - add the ruff gate:**
- Create `scripts/gate_ruff_lint_v1.sh` following the existing gate conventions
  (repo-root anchored; no xtrace; bash3-safe; `set -euo pipefail`; header comment block
  matching siblings like `gate_repo_root_allowlist_v1.sh`). Body runs the CI-identical
  command: `ruff check src/squadvault/`.
- Wire it into `scripts/git-hooks/pre-commit_v1.sh` as a new gate step (separate
  `echo ==> ...` + `bash scripts/gate_ruff_lint_v1.sh`), before the final
  "OK: pre-commit checks passed" line. Keep it ordered with the other gates.
- Reinstall the hook locally so it actually runs: `cp scripts/git-hooks/pre-commit_v1.sh
  .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit` (installed hook is untracked;
  this is a local action, not a commit artifact).

**Registry enumeration - the F2/F5 lesson (enumerate ALL marker-bounded blocks):**
Adding a gate that updates only the obvious file is the F2/F5 failure mode (precedent:
`OBSERVATIONS_2026_04_27_F2_F5_*`, where a fix missed the `CI_PROOF_RUNNERS` block and a
later `prove_ci` surfaced the gap). Update EVERY enumeration of the gate/guardrail set,
not just the hook. Known surfaces to check and update as applicable:
- `README.md` Developer Setup (line ~157) - **ALREADY STALE**: says "three gates",
  reality is four (banner, xtrace, allowlist, docs-Map). Correct it to enumerate ALL
  current gates INCLUDING the new ruff gate (will be five).
- `docs/80_indices/ops/CI_Guardrails_Index_v1.0.md`
- `docs/80_indices/ops/CI_Guardrail_Entrypoint_Labels_v1.tsv`
- `docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md`
- The parity gates that ENFORCE these (`gate_ci_guardrails_*`, `gate_ci_proof_surface_*`,
  `gate_ci_registry_execution_alignment_v1.sh`, `check_ci_proof_surface_matches_registry_v1.sh`)
  will FAIL prove_ci if any block is missed. **Method:** make the change, run prove_ci,
  and resolve every registry ERROR it surfaces - exactly the F2/F5 amend pattern.
  Determine whether a pre-commit-only gate belongs in the CI-guardrail registries (they
  may be scoped to prove_ci/CI entrypoints); let the parity gates adjudicate.
- Optional but recommended (mirrors precedent `Tests/test_docs_map_registration_gate_v1.py`):
  add a test asserting the ruff gate script exists, is executable, and is wired into the
  tracked pre-commit hook.

## Acceptance criteria (binary)

1. A deliberately-introduced lint error in a `src/squadvault/` file is BLOCKED at commit
   time (the commit fails via the new gate); removing the error allows the commit.
   Demonstrate both directions; do NOT leave the planted error committed.
2. The ruff gate is registered: wired into `scripts/git-hooks/pre-commit_v1.sh`; README
   gate enumeration corrected to list all gates including ruff; every CI-guardrail/registry
   parity gate passes (no registry ERROR under prove_ci).
3. `ruff check src/squadvault/` returns zero (unchanged from E1.1).
4. Tests/ruff/mypy green; prove_ci clean on a clean tree (under a 3.11+ interpreter).
5. STATE.md updated in the same commit series (E1.2 discharged with hash; Roadmap section
   7.3 standing item noted closed). Observation memo filed in `_observations/`.

## Gates (charter section 1)

ruff / mypy / pytest before each commit; gates and commits as SEPARATE steps (never `&&`);
prove_ci on the clean tree after the final commit (3.11+ interpreter); then stop for
founder review before push.

## OUT OF SCOPE (no drive-by work; charter amendment required to expand)

- pytest in pre-commit (D-A: NO).
- UP042 / StrEnum migration (parked open item - leave the ignore in place).
- Any change to the CI workflow ruff step (`.github/workflows/ci.yml`).
- Tests/ ruff scope (the gate matches CI: `src/squadvault/` only).
- Filing the Document of Record into the repo - founder's call; candidate to fold into
  E1.3's doc sweep so the unit-definition retrieval gap (hit while scoping E1.2) does not
  recur. NOTE as a known dependency; do NOT action here.

## Sequencing

E1.1 landed (`bf0833e`); no blocker. Single session, one topic per commit.
