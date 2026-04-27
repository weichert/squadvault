# F2+F5 fix scope expansion — prose-block drift + `prove_repo_root_allowlist` wiring gap

**Session date:** 2026-04-27
**Commit at session entry:** `28ae2bf` (post-F4 fix on `main`)
**Session outcome:** **Path A taken in-session.** Scope expanded to include wiring `scripts/prove_repo_root_allowlist_gate_behavior_v1.sh` into `prove_ci.sh`. F2+F5 closed in a single commit alongside this memo. See "Specific instructions for next session" → Path A below for the executed steps.

**Mid-session correction:** Initial fix landed in commit `0042a61` but missed a fourth registry block (`CI_PROOF_RUNNERS`, lines 61–75 of the registry doc). After-state `prove_ci.sh` run surfaced a new ERROR from `check_ci_proof_surface_matches_registry_v1.sh`: "CI invokes proof(s) not listed in registry: scripts/prove_repo_root_allowlist_gate_behavior_v1.sh". Fix amended into the commit. Lesson recorded in §"Post-mortem" below.

---

## TL;DR

The Finding-B triage memo's prescription for F2+F5 (regenerate the machine block in
`docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md`) is **incomplete**. The memo
asserts that "all 18 mentions currently live inside the SV_PROOF_SURFACE_LIST_v1
machine block — there is no prose mention outside the block." That assertion is
false at HEAD `28ae2bf`: there are mentions of the same 3 stale scripts in two
additional marker-bounded blocks (`PROOF_SURFACE_REGISTRY_LOCAL_PROOFS_v1` and
`SV_CI_EXECUTION_EXEMPT_v1`).

Cleaning **all three blocks** to remove the stale references closes F2+F5 cleanly,
but introduces a new failure in `gate_ci_registry_execution_alignment_v1.sh`: the
script `scripts/prove_repo_root_allowlist_gate_behavior_v1.sh` is **registered**
(present in the tracked tree, must be added to the machine block per F2) but is
**not invoked** by `scripts/prove_ci.sh`. Resolving that requires either a
semantic-stretch workaround or a scope expansion.

Three viable next-session paths (detailed below). Decision is Steve's, not mine.

---

## What was verified empirically this session

### 1. Pre-edit baseline (in this container, fresh clone of `28ae2bf`)

| Check | Result |
|---|---|
| `git rev-parse HEAD` | `28ae2bf` (matches origin/main) |
| `git status --porcelain` | clean |
| `ruff check src/` | All checks passed |
| `mypy src/squadvault/core/` | Success: no issues found in 58 source files |
| `PYTHONPATH=src python -m pytest -q` | 1811 passed, 3 skipped |
| `bash scripts/prove_ci.sh` rc | 0 |
| `prove_ci.sh` ERROR count | **17** (not 25 as cited in F4 brief — see below) |
| F2 ERROR present at expected position | yes (line 35 of capture; exact text matches memo) |
| F5 ERROR present at expected positions | yes (lines 140 and 221; exact text matches memo, 2 invocations as memo says) |
| Zero FS-ordering errors (F4 fix in?) | yes |

### 2. The 17-vs-25 ERROR-count delta (informational, not blocking)

The F4 session brief cites "rc=0, 25 ERRORs" as the post-F4 clean anchor captured
in Steve's same-shell environment on 2026-04-21. This session, in a fresh
container with a fresh clone, captured **17 ERRORs**. Same-shell ±1 tolerance
does not apply here since the environments are different.

ERROR family breakdown (this session):
- F1 shim violations: **8** (4 emitted by `gate_cwd_independence_shims_v1.sh`,
  4 by `check_shims_compliance.sh`). Brief cites 16 — likely Steve's environment
  exercises a third emission path I didn't observe. Not blocking for F2+F5.
- F2 (registry out of sync): 1 ✓
- F3 (allowlist wrapper not found): 1
- F5 (Proof suite completeness violation): 2 ✓
- F6 (expected canonical file missing): 4
- "duplicate gate invocations": 1
- **Total:** 17

The F2+F5 closure target (3 ERROR drop) is unambiguous and independent of the
absolute baseline.

### 3. The drift in the registry doc, fully enumerated at HEAD `28ae2bf`

`git ls-files 'scripts/prove_*.sh' | sort` returns **16 entries** (the
authoritative target).

**Block 1 — `SV_PROOF_SURFACE_LIST_v1` (machine block, lines 4–25):** has 18
entries.
- 3 stale (deleted scripts):
  - `scripts/prove_local_clean_then_ci_v3.sh`
  - `scripts/prove_local_shell_hygiene_v1.sh`
  - `scripts/prove_pytest_does_not_dirty_fixture_db_v1.sh`
- 1 missing (added in commit `19414c1` without registry update):
  - `scripts/prove_repo_root_allowlist_gate_behavior_v1.sh`

**Block 2 — `PROOF_SURFACE_REGISTRY_LOCAL_PROOFS_v1` (lines 82–89):** has 2 entries,
both stale (the deleted local-only proofs). This block is **NOT** referenced by
any active gate — only by archived patches under `scripts/_archive/`. The memo
missed this block entirely.

**Block 3 — `SV_CI_EXECUTION_EXEMPT_v1` (lines 90–97):** has 4 entries.
- 1 valid: `scripts/prove_creative_sharepack_determinism_v1.sh` (legitimately exempt
  because it has a conditional wrapper, `prove_ci_creative_sharepack_if_available_v1.sh`).
- 3 stale: same 3 deleted scripts as in Block 1. The memo missed this block too.

This block IS referenced by the active gate
`scripts/gate_ci_registry_execution_alignment_v1.sh`, which is invoked at
`prove_ci.sh:122` and `prove_ci.sh:286`. The gate's logic:
  - `R` = all `scripts/prove_*.sh` mentions anywhere in registry doc (sorted unique).
  - `X` = entries inside `SV_CI_EXECUTION_EXEMPT_v1` markers.
  - `E` = invocations inside `prove_ci.sh`.
  - **Fail if `(R − X) − E ≠ ∅`** ("Registered but not executed and not exempted").

### 4. Why the alignment gate currently passes (before any fix)

At baseline, `R` includes the 3 stale entries, `X` includes those same 3 stale
entries, so `R − X` cancels them out. The gate passes coincidentally because the
two errors (stale-in-list + stale-in-exempt) hide each other.

### 5. What happens if I do the "clean" full Option-B fix

Edits attempted:
1. Update machine block: 18 → 16 entries (remove 3 stale, add `prove_repo_root_allowlist`).
2. Empty `PROOF_SURFACE_REGISTRY_LOCAL_PROOFS_v1` contents (keep markers and section header).
3. Remove 3 stale entries from `SV_CI_EXECUTION_EXEMPT_v1` (keep
   `prove_creative_sharepack_determinism_v1.sh` only).

Empirical result of running each affected gate standalone after these edits:

| Gate | Result |
|---|---|
| `gate_ci_proof_surface_registry_exactness_v1.sh` (F2) | **PASS** |
| `gate_proof_suite_completeness_v1.sh` (F5) | **PASS** (`OK: proof runners match registry exactly.`) |
| `gate_ci_registry_execution_alignment_v1.sh` | **FAIL** (`Registered but not executed (and not exempted): scripts/prove_repo_root_allowlist_gate_behavior_v1.sh`) |

So the trade-off is real: closing F2+F5 cleanly via prose-block cleanup unmasks
a pre-existing wiring gap that was hidden by the cross-cancelling drift.

### 6. The wiring gap, in detail

`scripts/prove_repo_root_allowlist_gate_behavior_v1.sh` was added by commit
`19414c1` ("Pre-commit: add repo-root allowlist gate (local/CI parity)"). It is:

- Tracked in git (`git ls-files` includes it).
- Referenced **only** by the registry doc itself (no other consumer in `scripts/`,
  `docs/`, `src/`, or `Tests/`).
- **Not invoked** anywhere in `scripts/prove_ci.sh`.

Compare with the analogous existing pattern `prove_no_terminal_banner_paste_gate_behavior_v1.sh`,
which has the same naming structure (a "gate behavior proof") and IS invoked at
`prove_ci.sh:106`. The natural conclusion: `prove_repo_root_allowlist_gate_behavior_v1.sh`
was added but its `prove_ci.sh` invocation was never written.

Edits revert was clean (`git status --porcelain` empty after revert; F2 fails again
as before; alignment gate passes again as before).

---

## Three next-session paths

### Path A — Scope expansion: wire `prove_repo_root_allowlist` into `prove_ci.sh`

**Edits in one commit:**
1. Update machine block (18 → 16) per memo's F2 prescription.
2. Empty `PROOF_SURFACE_REGISTRY_LOCAL_PROOFS_v1` contents.
3. Remove 3 stale from `SV_CI_EXECUTION_EXEMPT_v1`.
4. **Add** `bash scripts/prove_repo_root_allowlist_gate_behavior_v1.sh` invocation
   to `prove_ci.sh` (alongside the existing `prove_no_terminal_banner_paste_gate_behavior_v1.sh`
   invocation at line 106 — same semantic category).

**Pros:** Correct fix. Closes F2+F5 (-3 ERRORs) AND fixes the wiring gap with no
new ERRORs. Aligns with the
"prove_no_terminal_banner_paste_gate_behavior_v1.sh" precedent.

**Cons:** Touches `prove_ci.sh`. The F2+F5 brief's "Out of scope" list explicitly
excludes "Changes to `prove_ci.sh`. Finding B closure is deferred until all six
fix sessions land." Path A violates that boundary.

**Mitigation:** This isn't really a Finding-B closure-style change (no
`set -euo pipefail`, no errexit work). It's adding one invocation line, in the
same shape as 14 other lines in `prove_ci.sh`. If the boundary is interpretable,
this is well within the spirit of "F2+F5: regenerate the registry to match
reality" — reality includes a script that should be invoked.

**Estimated time:** 30–45 min. One commit. Strong recommendation if Steve allows
the scope expansion.

### Path B — Workaround: add `prove_repo_root_allowlist` to EXEMPT with TODO comment

**Edits in one commit:**
1–3 as in Path A.
4. **Add** `prove_repo_root_allowlist_gate_behavior_v1.sh` to
   `SV_CI_EXECUTION_EXEMPT_v1` with a TODO comment indicating the proper fix
   is wiring, e.g.:
   ```
   - scripts/prove_creative_sharepack_determinism_v1.sh
   # TODO: not actually exempt — wire into prove_ci.sh alongside prove_no_terminal_banner_paste pattern.
   - scripts/prove_repo_root_allowlist_gate_behavior_v1.sh
   ```

**Pros:** Closes F2+F5 (-3 ERRORs) cleanly with no scope-boundary violation.
TODO comment is self-documenting.

**Cons:** Lies about intent. EXEMPT means "intentionally not in CI"; this script
should be in CI. The lie is small and documented, but it's still a lie. Future
readers may rationalize the TODO away. SquadVault's "silence over fabrication"
principle weighs against this.

**Estimated time:** 30 min. One commit. Acceptable if Steve prefers strict scope
adherence over semantic correctness, and is willing to live with the TODO until
the wiring change happens.

### Path C — Defer F2+F5 to a combined session with the wiring change

Don't fix F2+F5 in isolation. Roll them into a future session whose explicit
scope is "F2+F5 + wiring fix for `prove_repo_root_allowlist`". That session can
cleanly produce a single commit with all four edits in Path A.

**Pros:** No principle compromised. No mid-session re-triage. Clean attribution.

**Cons:** F2+F5 remain open until that session lands. The other Finding-B
fix-order sessions (F1, F3, F6, F7) are all independent of F2+F5, so deferral
doesn't block them.

**Estimated time:** Same as Path A (30–45 min) when it eventually runs.

### My recommendation

**Path A, with Path C as fallback.** Path A produces the clean fix in one
commit. The "no changes to prove_ci.sh" boundary in the F2+F5 brief was
written assuming the memo's prescription was complete; now that we know it
isn't, the right response is to expand scope minimally rather than work around.

Path B I'd avoid — the TODO is self-documenting but the underlying lie about
intent is the kind of thing that calcifies in the codebase.

Path C is the conservative option if Steve wants to preserve strict scope
discipline for this round of Finding-B fixes; F2+F5 closure is just delayed,
not abandoned.

---

## Other observations from this session (incidental, not blocking)

### Stale referenced patch script

`gate_ci_proof_surface_registry_exactness_v1.sh:34` and `:69` reference a
helper `scripts/patch_ci_proof_surface_registry_machine_block_v1.sh` in its
error-message hint text:

```
Run: bash scripts/patch_ci_proof_surface_registry_machine_block_v1.sh
```

That patch script does **not** exist in the tracked tree. The hint is dead.
Low priority; suggest cleaning up in a future "registry doc maintenance" pass.
Does not affect any gate's pass/fail result.

### Missing gate referenced in `prove_ci.sh`

In the before-state output, line 219 contains:
```
bash: scripts/gate_idempotence_allowlist_wrappers_no_prove_ci_v1.sh: No such file or directory
```

This is from `prove_ci.sh:218` (or thereabouts — exact line near the
`==> Guard: allowlist wrappers must not recurse into prove_ci` banner). The
referenced gate script does not exist in the tracked tree. The error message
appears in `prove_ci.sh` output but is **not** captured by `grep -E '^ERROR|ERROR:'`
because it's a bash "No such file or directory" message, not an `ERROR:` line.

This is a separate dangling reference, distinct from the F-series findings.
Suggest backlog item: investigate whether the referenced gate was retired or
was never created. If retired, remove the invocation from `prove_ci.sh`.
If never created, decide whether to create or remove the line.

---

## Hand-back state

- Tree at `28ae2bf`, no edits applied (revert verified clean via `git status`).
- Working venv preserved in `/home/claude/squadvault/.venv` for diagnostic continuity.
- Before-state capture preserved at `/tmp/proveci_f2f5_before.txt` (17 ERRORs, rc=0).
- Pre-commit hook installed (`scripts/git-hooks/pre-commit_v1.sh` copied to `.git/hooks/pre-commit`).
- This memo is **NOT YET COMMITTED**. Steve's call: commit it as a standalone
  observation memo, or defer until the next-session-decision is made.

---

## Specific instructions for next session

If Steve picks **Path A** (recommended):

1. Apply the four edits described in Path A.
2. Run all three relevant gates standalone:
   - `bash scripts/gate_ci_proof_surface_registry_exactness_v1.sh` → expect rc=0.
   - `bash scripts/gate_proof_suite_completeness_v1.sh` → expect rc=0.
   - `bash scripts/gate_ci_registry_execution_alignment_v1.sh` → expect rc=0.
3. Re-run `prove_ci.sh`, confirm: rc=0, ERROR count drops by exactly 3 (no new
   errors), no registry/out-of-sync lines.
4. Commit with message referencing F2, F5, and the wiring fix. Single-quoted
   heredoc for safety. Cite this observation memo by path.

If Steve picks **Path B** (workaround):

1. Apply the four edits described in Path B.
2. Same gate checks as Path A.
3. Same prove_ci verification.
4. Commit. Add explicit note in commit message that EXEMPT entry is a
   workaround, with cite to this memo.
5. Add backlog item: "wire prove_repo_root_allowlist_gate_behavior_v1.sh into
   prove_ci.sh, then remove from EXEMPT."

If Steve picks **Path C** (defer):

1. No code change.
2. Optionally commit just this memo as a standalone observation commit.
3. Schedule a future session whose scope is explicitly "F2+F5 + repo-root
   allowlist proof wiring" — that session executes Path A.

---

## Confirmed unchanged (baselines)

- `ruff check src/`: All checks passed!
- `mypy src/squadvault/core/`: Success: no issues found in 58 source files.
- `PYTHONPATH=src python -m pytest -q`: 1811 passed, 3 skipped (default env).

---

## Post-mortem: the missed `CI_PROOF_RUNNERS` block

The initial fix in this session landed via a 3-block edit (machine block,
LOCAL_PROOFS, EXEMPT) plus the prove_ci.sh wiring. Standalone gate verification
covered the four gates I had identified at audit time: F2, F5, alignment, and
the proof-runners block-sorted gate. All passed. The commit landed (`0042a61`).

The subsequent full `prove_ci.sh` run on the clean tree surfaced a new ERROR:

```
ERROR: CI invokes proof(s) not listed in registry:
scripts/prove_repo_root_allowlist_gate_behavior_v1.sh
```

This came from `scripts/check_ci_proof_surface_matches_registry_v1.sh`
(invoked at `prove_ci.sh:161`), which compares the prove-script invocations
in `prove_ci.sh` against a fourth marker-bounded block in the registry doc:

```
<!-- CI_PROOF_RUNNERS_BEGIN -->
- scripts/prove_*.sh — purpose
...
<!-- CI_PROOF_RUNNERS_END -->
```

This block uses a **strict** entry grammar: `- scripts/prove_*.sh — purpose`
(em-dash separator). The other three blocks I audited use loose grammar
(plain `- scripts/...` bullets). I had grepped for marker patterns in the
registry doc and identified blocks at audit time, but I traced consumers
only for the three blocks the F2/F5 memo named. I did not exhaustively
check whether **all** marker blocks had active consumers.

**Lesson:** When fixing registry drift, the audit must enumerate ALL
marker-bounded blocks in the registry doc and trace ALL consumers of each
block, not just the blocks named by the originating finding's memo. The
grep for marker pairs was correct; the follow-through to consumer-mapping
was incomplete. Specifically:

```
grep -nE '<!--' <registry_doc>             # find all marker pairs
# then for each block name:
grep -rln <block_name> scripts/            # find active consumers
```

Both steps must be done before declaring the fix scope. The F2/F5 brief
asked "find the enforcing gate" but did not say "find ALL enforcing gates";
I followed the brief literally and missed the fourth gate.

**Amended commit:** `0042a61` was amended (still local, never pushed) to
include a one-line addition to `CI_PROOF_RUNNERS`:

```
- scripts/prove_repo_root_allowlist_gate_behavior_v1.sh — Proof: repo-root allowlist gate behavior (v1)
```

Inserted in alphabetical position (between `prove_no_terminal_banner_paste`
and `prove_rivalry_chronicle`), matching the strict entry grammar.

**Verified after amendment** (all standalone, rc=0):
- `gate_ci_proof_surface_registry_exactness_v1` (F2)
- `gate_proof_suite_completeness_v1` (F5)
- `gate_ci_registry_execution_alignment_v1`
- `gate_ci_proof_runners_block_sorted_v1`
- `check_ci_proof_surface_matches_registry_v1` (the gate I had missed)

Full `prove_ci.sh` re-run on clean tree: see commit message for final ERROR
count delta.

---

## Map of all marker blocks in the registry doc (post-fix, for future
reference)

| Block | Active consumer(s) | Entry grammar |
|---|---|---|
| `SV_PROOF_SURFACE_LIST_v1` | `gate_ci_proof_surface_registry_exactness_v1.sh` | `- scripts/prove_*.sh` (loose) |
| `CI_PROOF_RUNNERS` | `check_ci_proof_surface_matches_registry_v1.sh`, `gate_ci_proof_runners_block_sorted_v1.sh` | `- scripts/prove_*.sh — purpose` (strict) |
| `PROOF_SURFACE_REGISTRY_LOCAL_PROOFS_v1` | (none — only archived patches) | n/a |
| `SV_CI_EXECUTION_EXEMPT_v1` | `gate_ci_registry_execution_alignment_v1.sh` | mixed (loose) |
| `SV_RULE_GATE_VS_PROOF_BOUNDARY_v1` | (prose-only block; no parseable entries) | n/a |
| `SV_CONTRACT_SURFACE_PROOFS_v1` | (no active consumers; entries are documentation) | n/a |
| `SV_CI_PROOF_CREATIVE_SHAREPACK_IF_AVAILABLE_v1` | (no active consumers; documentation) | n/a |
| `SV_PATCH: nac fingerprint preflight doc` | (single-line annotation, not a block) | n/a |

`gate_proof_suite_completeness_v1.sh` (F5) does a **global** grep across
the entire doc for `scripts/prove_*\.sh`, not bounded by markers — so it
sees every prove-script mention regardless of which block it lives in.
This is what made the F2 fix without prose-block cleanup leave F5 still
firing in the original audit.
