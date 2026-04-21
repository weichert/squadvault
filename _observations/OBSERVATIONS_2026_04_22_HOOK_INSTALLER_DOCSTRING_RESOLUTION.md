# Hook installer docstring — Option A resolution (Finding 1 closed)

**Date:** 2026-04-22
**Session:** Hook installer question follow-up (single-commit session at
HEAD `19414c1`).
**Closes:** Finding 1 in
`_observations/OBSERVATIONS_2026_04_20_PRECOMMIT_GATE_PARITY_DEFERRED_FINDINGS.md`.
**Status:** FINAL

---

## Decision

**Option A — update the hook's docstring to reflect reality; do not
revive or formalize an installer script.**

The hook docstring had been referencing
`scripts/install_git_hooks_v1.sh`, which was moved to
`scripts/_archive/unreferenced/install_git_hooks_v1.sh` at some earlier
point. No replacement mechanism existed. Operators cloning the repo got
no hook by default and the only documentation pointed at an archived
path.

This commit:

1. Rewrites the `Notes:` block of `scripts/git-hooks/pre-commit_v1.sh`
   to describe the actual two-command manual install (`cp` + `chmod`).
   Escape-hatch documentation (`SV_SKIP_PRECOMMIT=1`) is left intact.
2. Adds a short **Developer Setup** section to `README.md` directly
   above **Status**, so new contributors see the install step without
   needing to open the hook file first.

No changes to hook logic. No new scripts. No Makefile changes. No CI
changes.

---

## Why Option A

Four options were on the table (see session brief):

- **A:** update docstring, add README pointer.
- **B:** add `make install-hooks` as the canonical install path.
- **C:** revive `scripts/_archive/unreferenced/install_git_hooks_v1.sh`
  from the archive.
- **D:** switch to `git config core.hooksPath scripts/git-hooks`.

Option A was chosen because:

1. **Proportionate to the problem.** The failure was documentation
   drift affecting new operators only. A docstring fix is the shape of
   the problem.
2. **Preserves optionality.** B, C, and D can still be chosen in a
   future session if the install mechanism needs to formalize. A does
   not foreclose them.
3. **Smallest reviewable diff.** One hook file edit, one README
   section, one memo.

Notes on the options not taken:

- **Option C is viable**, not dead. Inspection of the archived
  installer confirmed it still does what its docstring claims:
  idempotent install from `scripts/git-hooks/pre-commit_v1.sh` to
  `.git/hooks/pre-commit`, with timestamped backup on mismatch, and a
  no-op when source and destination are byte-identical. If a future
  session decides the manual install is too much friction, Option C's
  archaeology already looks clean. Not investigated in depth here —
  silence over speculation about whether the "unreferenced" archival
  was deliberate or accidental.
- **Option B** would have been the natural next-most-discoverable
  choice, but formalizing a Makefile target now ossifies a mechanism
  that may not be the right one long-term. Deferred.
- **Option D** would have broken the `_v1` filename versioning
  convention (git calls hooks by exact name, so `pre-commit_v1.sh`
  would need to become `pre-commit` or route through a wrapper).
  Deferred.

---

## Verification

Full pre-commit gate fired successfully after the docstring edit:

```
==> pre-commit: terminal banner paste gate
OK: no terminal banner pastes detected.
==> pre-commit: no-xtrace guardrail gate
OK: no active `set -x` in staged scripts.
==> pre-commit: repo-root allowlist gate
OK: repo root contains only allowlisted files.
OK: pre-commit checks passed.
```

Baselines at session exit (unchanged from entry at `19414c1`):

- Ruff (`ruff check src/`): All checks passed!
- Mypy (`mypy src/squadvault/core/`): Success: no issues found in 58
  source files
- Pytest: 1811 passed, 3 skipped

No src/ changes in this session; baseline equivalence is expected.

---

## What this session does not do

- Does not adopt the `pre-commit` framework or any third-party tooling.
- Does not change what the hook does (the three-gate chain is
  unchanged).
- Does not touch other hook types.
- Does not fix Finding 2 from the deferred-findings memo
  (`gate_ci_guardrails_ops_entrypoints_section_v2.sh` pre-existing
  failure). Still flagged, still out of scope.

---

## Carry-forward

None specific to this thread. The install mechanism is now truthfully
documented. If future friction argues for formalization, a new session
brief picks Option B, C, or D. The archived installer at
`scripts/_archive/unreferenced/install_git_hooks_v1.sh` remains in
place and is not referenced by anything.
