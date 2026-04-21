# Pre-commit gate local/CI parity — deferred drift findings

**Date:** 2026-04-20
**Session:** Pre-commit gate local/CI parity fix (adds
`gate_repo_root_allowlist_v1.sh` to the pre-commit chain).
**Commit-of-record:** this session's single commit.

This memo captures two drift findings surfaced during the session that
are **out of scope for this session's fix pass** but were clear enough
to note for future sessions.

---

## Finding 1: Hook installer has been archived, hook docstring still references it

The tracked pre-commit hook at `scripts/git-hooks/pre-commit_v1.sh` has a
docstring that says:

> This file is repo-tracked. It is installed into `.git/hooks/pre-commit`
> by `scripts/install_git_hooks_v1.sh` (installer is idempotent).

But that installer no longer lives at `scripts/install_git_hooks_v1.sh`.
It's been moved to `scripts/_archive/unreferenced/install_git_hooks_v1.sh`.

No replacement mechanism exists in `Makefile` (no `hook`/`install` targets).
The session brief for this session assumed the installer was still in
place — it explicitly referenced running it in Step 5.

**Session-scope mitigation:** for this commit, the operator installed
the updated hook manually via `cp scripts/git-hooks/pre-commit_v1.sh
.git/hooks/pre-commit && chmod +x .git/hooks/pre-commit`. This is a
one-off, not a pattern.

**What's deferred:** the question of how the installation mechanism
should work — revive the archived installer, create a Makefile target,
update the hook docstring to reflect reality, or something else. All
legitimate options; none addressed here. The hook's docstring currently
lies about its own installation mechanism, which is a small but real
form of documentation drift.

**Why out of scope:** the brief explicitly said "do NOT reopen broader
design questions beyond the minimum needed here." The installer was
deliberately archived as "unreferenced" — there's presumably a reason
(could be deliberate deprecation, could be accidental), and guessing
without context would violate silence-over-speculation. Warrants its
own briefed session.

---

## Finding 2: `gate_ci_guardrails_ops_entrypoints_section_v2.sh` fails at pristine HEAD `10e12a8`

When sweeping CI-guardrail gates to validate this session's changes,
`gate_ci_guardrails_ops_entrypoints_section_v2.sh` fails. **It also
fails at pristine HEAD `10e12a8`** — verified via a clean worktree
checkout. It's not caused by this session's changes.

**Failure detail:** the gate looks for a bounded block in
`docs/80_indices/ops/CI_Guardrails_Index_v1.0.md` delimited by:

```
<!-- SV_BEGIN: ops_entrypoints_toc (v1) -->
<!-- SV_END: ops_entrypoints_toc (v1) -->
```

The index file does not contain these markers. The gate errors with
`ERROR: missing bounded section`.

**Observed behavior at pristine HEAD:**
- `gate_ci_guardrails_surface_freeze_v1.sh` → rc=0 (passes)
- `gate_ci_guardrails_ops_entrypoints_section_v2.sh` → rc=1 (fails)
- All other `gate_ci_guardrails_*` → rc=0

This is not a silent drift — the gate's failure is loud and deterministic.
Either:
(a) The gate is expected to fail locally and is enabled only in CI
    against a different file layout (unlikely but possible).
(b) The bounded-markers were removed from the index at some point
    without retiring or updating the gate.
(c) The gate was added without ever being satisfied at repo HEAD.

**Why out of scope:** not caused by this session, and diagnosing
properly requires `git log --follow` archaeology across the index file
and the gate script, which is its own session. Flagging only.

**Not-a-blocker:** this session's work adds to the registry and
fingerprint, which are enforced by `registry_completeness`,
`registry_authority`, and `surface_freeze` — all of which pass. The
`entrypoints_section_v2` gate is orthogonal and was failing before.

---

## Items not carried forward

- This session's changes proved `gate_repo_root_allowlist_v1.sh` works
  end-to-end (both positive and negative cases exercised manually
  during development, plus the prove script once the commit is staged).
- Baselines at the session-exit commit are: ruff clean, mypy clean,
  pytest 1811 passed / 3 skipped. (One more env-gated skip vs. the
  brief's expected 1812/2 at `8082040`, introduced by two unrelated
  Phase 10 conformance commits that landed between brief-writing and
  session-start; total test count unchanged.)
