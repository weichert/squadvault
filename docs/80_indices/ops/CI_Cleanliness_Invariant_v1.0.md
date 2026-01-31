# SquadVault — CI Cleanliness & Determinism Guardrail (v1.0)

Status: ACTIVE (enforced)

## Invariant

When running the authoritative CI proof entrypoint:

- **Entrypoint:** `scripts/prove_ci.sh`
- The git working tree **must remain clean** throughout the run.
- If the run begins dirty: **fail early**.
- If the run dirties the repo (tracked or untracked): **fail loudly** with an actionable diff summary.
- No silent cleanup of repo state. No masking.

## Rationale

Even with fixture immutability enforced, allowing proofs to dirty the working tree can:

- mask nondeterminism
- hide bugs that only appear from a clean checkout
- undermine auditability and operator trust

This guardrail prioritizes detect + fail over convenience.

## Enforcement

- Pre-check: `scripts/check_repo_cleanliness_ci.sh --phase before`
- Post-check (EXIT): `scripts/check_repo_cleanliness_ci.sh --phase after`

Any porcelain output is a hard failure.

## Recovery (operator choice)

- Inspect: `git status`
- Discard tracked changes: `git restore --staged --worktree -- .`
- Remove untracked (destructive): `git clean -fd`
