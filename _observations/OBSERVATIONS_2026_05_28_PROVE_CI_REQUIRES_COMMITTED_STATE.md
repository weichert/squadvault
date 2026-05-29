# OBSERVATIONS — prove_ci Requires Committed State (2026-05-28)

**Surfaced by:** Milestone 4 session — bad paste-block ordering placed `./scripts/prove_ci.sh` before `git commit`. The proof's terminal-banner-paste-gate behavior check failed with `ERROR: proof requires clean repo (working tree + index)` and listed the staged-but-uncommitted new file.
**Engine HEAD at observation:** `cc8a993` (post-pattern-fix carry-overs).
**Disposition:** Pattern reference. Captures a sequencing rule that previously lived only in shell behavior and one error message. No code change.
**Append-only:** This memo records the pattern. It does not edit any prior memo, gate, or proof.

---

## The rule

`./scripts/prove_ci.sh` requires a clean repo — both the working tree AND the index. It cannot run against staged-but-uncommitted state. Therefore the canonical workflow for adding new code is:

```
1. (apply changes to working tree)
2. (run cheap local checks: parse, ruff, mypy, pytest baseline)
3. git add
4. git commit          <- pre-commit hooks fire here (banner, xtrace, repo-root, docs Map)
5. ./scripts/prove_ci.sh   <- runs against committed state
6. git push
```

Steps 4 and 5 are non-negotiable in this order. Step 5 cannot occur with a dirty index.

## Why prove_ci is strict

The `prove_no_terminal_banner_paste_gate_behavior_v1.sh` proof tests that the banner-paste gate works correctly by **mutating the working tree** (staging a synthetic file with a known banner-paste pattern, asserting the gate catches it, then reverting). This proof can only run against a clean state because it needs an unambiguous baseline to mutate and revert. A dirty index would make the revert ambiguous.

Other proofs in `prove_ci.sh` (creative determinism, rivalry chronicle end-to-end, golden path) have similar mutation-and-revert patterns. The end-of-run gate `Enforce repo clean after proofs (v1)` confirms the proofs left the repo as they found it. None of this can work if the index is dirty going in.

## Why pre-commit hooks are NOT a substitute

The pre-commit hooks (`banner paste gate`, `no-xtrace guardrail`, `repo-root allowlist`, `docs Map registration`) run automatically at `git commit` and gate that single transition. They are cheap (sub-second) and run on every commit.

`prove_ci.sh` is the post-commit verification: ~8 minutes, runs the full proof suite including unit tests, EAL tests, golden-path proof mode, rivalry chronicle end-to-end, creative sharepack determinism, and the meta-gates. It is the merge-blocker.

Pre-commit hooks and prove_ci are complementary, not redundant. Pre-commit catches a small set of fast-failable conditions at the moment of commit. prove_ci catches the broad set of structural and behavioral invariants after the commit has landed.

## Recovery if prove_ci fails post-commit

```
git reset --soft HEAD~1
```

This unwinds the commit while keeping the changes staged. Investigate the proof failure, fix, recommit, re-run prove_ci. Non-destructive; the working tree is preserved.

This pattern is the reason the canonical workflow puts prove_ci AFTER commit: a prove_ci failure is recoverable cheaply, whereas a prove_ci-before-commit attempt fails on a constraint the proof can't itself articulate clearly (it just says "proof requires clean repo," which is technically accurate but doesn't suggest the right fix to a reader who hasn't internalized this rule).

## Related rules already on the books

- "Lint+test gates and `git commit`/`git push` MUST be in separate paste turns; never chained with `&&`." Reason: zsh `INTERACTIVE_COMMENTS` and chat-paste hazards interact poorly with multi-step terminal flows.
- "Pre-commit hooks cover banner/xtrace/repo-root only, NOT ruff or pytest." Reason: pre-commit must stay fast; broader checks live in prove_ci or in dev-loop tooling.

This memo adds: **prove_ci requires committed state.** That belongs alongside the two above as a fundamental sequencing constraint, not a session-specific lesson.

## Provenance

The bad ordering was given in an assistant paste sequence during M4 (May 28, 2026). The proof flagged it correctly. The session adjusted by reordering: commit first, prove_ci second. Carry-over #5 from the M4 closing summary lists this as a pattern memo to capture so the lesson is durable.

The M4 final commits landed cleanly at `a5f79f9`, `3a7eeab`, `cc8a993` after the reordering. This memo accompanies them.
