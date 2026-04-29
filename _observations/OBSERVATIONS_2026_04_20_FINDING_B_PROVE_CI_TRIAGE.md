# Finding B — Triage of pre-existing failures in `prove_ci.sh` output

**Session date:** 2026-04-20
**HEAD:** `b84297e` (CI Guardrails: retire gate_ci_guardrails_ops_entrypoints_section_v2)
**Posture:** Diagnostic-only classification (Option A per session brief). No changes to `scripts/prove_ci.sh`, no gate fixes, no errexit introduced.

---

## Summary

`scripts/prove_ci.sh` does not use `set -e`, `set -u`, or `set -o pipefail`. Its final exit code is the return code of its last command (`bash scripts/gate_worktree_cleanliness_v1.sh end "${SV_WORKTREE_SNAP0}"` at line 356). All preceding failures are absorbed at the script level and invisible to CI, which only sees the final rc.

Baseline capture on a clean worktree at `b84297e`:

```
bash scripts/prove_ci.sh > /tmp/proveci_finding_b.txt 2>&1 ; echo "rc=$?"
# rc=0
# 521 lines of output
# 29 ERROR: signals in that output
```

The 29 ERROR instances collapse to **7 distinct findings**. Bucket distribution:

| Bucket               | Count | Findings      |
|----------------------|-------|---------------|
| Real issue           | 4     | F1, F2, F5, F7|
| Gate bug             | 3     | F3, F4, F6    |
| Environment-dependent| 0     | —             |
| Load-bearing         | 0     | —             |

**F2 and F5 share a single fix target** (the registry doc): they detect the same drift from different angles, so six sessions close all seven findings.

### The load-bearing commit

Five of the seven findings (F2, F3, F5, F6, F7) trace to a single commit:

```
2dfb96e  2026-03-11  engineering excellence: 512 tests, 100% docs, schema aligned
```

That commit deleted 15 files referenced by downstream gates, allowlists, and docs, but did not sweep:
- `scripts/gate_no_obsolete_allowlist_rewrite_artifacts_v1.sh` (the `allow_exact` array) → F6
- `scripts/patch_idempotence_allowlist_v1.txt` (the allowlist contents) → F3
- `docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md` (the machine block) → F2, F5
- `docs/contracts/rivalry_chronicle_contract_output_v1.md` (the Enforced By section) → F7

All five failures have been silent-red in `prove_ci.sh` output for **224 commits / 40 days** (from 2026-03-11 to 2026-04-20). This is the strongest empirical case for Finding B mattering — one cleanup commit left five governance artifacts unsynchronized for over a month with no gate-surface feedback.

F1 (shim violations in `process_full_season.sh`) and F4 (filesystem-ordering filter misses `_archive/`) are independent of 2dfb96e.

---

## Finding F1 — Shim violations in `scripts/process_full_season.sh`

**Originating check:** `scripts/check_shims_compliance.sh` (and indirectly `scripts/gate_cwd_independence_shims_v1.sh`, which invokes the same logic)
**Captured at:** lines 6–9, 122–125, 394–397, 507–510 of `/tmp/proveci_finding_b.txt` (4 clusters × 4 call sites = 16 error instances from one underlying defect; the shim check runs multiple times through different gate/proof paths)
**Exact error text (one representative):**
```
ERROR: shim violation (PYTHONPATH=src python): /Users/steve/projects/squadvault-ingest-fresh/scripts/process_full_season.sh:17:PYTHONPATH=src python3 << PYEOF
```

**Classification:** REAL ISSUE.

**Root cause:** `scripts/process_full_season.sh` invokes Python inline with `PYTHONPATH=src python3` at four call sites (lines 17, 51, 78, 102) instead of using the canonical `./scripts/py` shim. The shim contract (`Ops_Shim_And_Cwd_Independence_Contract`) requires all scripted Python entry points to route through the shim to get CWD-independence and deterministic tool selection. The script has three heredocs (`<< PYEOF`, `<< 'PYEOF'`, `<< 'PYEOF'`) and one `-c "..."` inline invocation that need conversion.

**Scope estimate:** ~60–90 minutes (single session). Heredocs → either pull the embedded Python into standalone `.py` files under `scripts/_helpers/` or convert to `./scripts/py -c "$(cat <<'PYEOF' ... PYEOF)"` form. The `-c "..."` at line 78 converts trivially.

**Cross-references:** Independent of 2dfb96e. Only touches `scripts/process_full_season.sh`.

---

## Finding F2 — `CI_Proof_Surface_Registry` machine block out of sync

**Originating gate:** `scripts/gate_ci_proof_surface_registry_exactness_v1.sh`
**Captured at:** line 35 of `/tmp/proveci_finding_b.txt`
**Exact error text:**
```
ERROR: CI_Proof_Surface_Registry is out of sync with tracked prove scripts.
```

**Classification:** REAL ISSUE.

**Root cause:** The registry doc `docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md` maintains a machine-readable block (`<!-- SV_PROOF_SURFACE_LIST_v1_BEGIN -->` … `_END -->`) that must exactly match the tracked set `git ls-files 'scripts/prove_*.sh'`. Current state at HEAD:

- Registry has 18 entries; tracked set has 16.
- **3 stale entries** in registry (files deleted by 2dfb96e, registry never updated):
  - `scripts/prove_local_clean_then_ci_v3.sh`
  - `scripts/prove_local_shell_hygiene_v1.sh`
  - `scripts/prove_pytest_does_not_dirty_fixture_db_v1.sh`
- **1 missing entry** in registry (file added by commit `19414c1 "Pre-commit: add repo-root allowlist gate (local/CI parity)"` without registry update):
  - `scripts/prove_repo_root_allowlist_gate_behavior_v1.sh`

**Scope estimate:** ~30 minutes. Single-commit fix: regenerate the machine block from `git ls-files 'scripts/prove_*.sh' | sort` with `- ` bullet prefix, replace between the two markers.

**Cross-references:** F5 detects the same drift from a different angle (greps all prove mentions anywhere in the doc; happens to catch only the machine block since no prose mentions exist outside it). Fixing F2 closes F5.

---

## Finding F3 — `patch_idempotence_allowlist_v1.txt` references 7 non-existent wrappers

**Originating proof:** `scripts/prove_idempotence_allowlist_noop_in_idempotence_mode_v1.sh`
**Captured at:** line 81 of `/tmp/proveci_finding_b.txt`
**Exact error text:**
```
ERROR: allowlist wrapper not found: scripts/patch_fix_ci_registry_execution_alignment_fail_v1.sh
```

**Classification:** GATE BUG (Finding-2-style pattern — proof checks something that was deliberately removed).

**Root cause:** The allowlist file `scripts/patch_idempotence_allowlist_v1.txt` lists 7 wrapper scripts that the proof iterates, invokes, and checks for mutation-free behavior under `SV_IDEMPOTENCE_MODE=1`. All 7 wrappers were present at `2dfb96e^` and absent at `2dfb96e`; the allowlist file was not updated. The proof uses `exit 2` on the first missing wrapper (`scripts/prove_idempotence_allowlist_noop_in_idempotence_mode_v1.sh:53`), which is why only 1 error appears for 7 missing files.

The 7 wrappers:
- `scripts/patch_fix_ci_registry_execution_alignment_fail_v1.sh` (first hit)
- `scripts/patch_gate_ci_registry_execution_alignment_exclude_prove_ci_v1.sh`
- `scripts/patch_gate_ci_registry_execution_alignment_v1.sh`
- `scripts/patch_index_ci_proof_surface_registry_discoverability_v3.sh`
- `scripts/patch_index_ci_registry_execution_alignment_discoverability_v1.sh`
- `scripts/patch_registry_add_ci_execution_exempt_locals_v1.sh`
- `scripts/patch_wire_ci_milestone_latest_into_append_wrapper_v1.sh`

**Scope estimate:** ~30 minutes. Fix options in order of preference:
1. **Empty the allowlist** (keep header comments). The proof becomes trivially-passing-vacuous when no wrappers are listed, which is the correct current state — no wrappers currently need idempotence allowlisting.
2. **Retire the proof entirely.** If vacuous-pass is not philosophically acceptable, retire `prove_idempotence_allowlist_noop_in_idempotence_mode_v1.sh` plus its registry entry (F2's list) and its invocation at `prove_ci.sh:127`.

Recommend option 1 — preserves the enforcement surface for any future wrapper that does need allowlisting.

**Cross-references:** Shares 2dfb96e root cause with F2, F5, F6, F7. Independent fix target.

---

## Finding F4 — Filesystem-ordering gate false-positives on `scripts/_archive/`

**Originating check:** `scripts/check_filesystem_ordering_determinism.sh`
**Captured at:** lines 91, 94, 97, 105 of `/tmp/proveci_finding_b.txt`
**Exact error text (four distinct errors, one per pattern family):**
```
ERROR: Filesystem ordering nondeterminism risk: shell: 'find ... | grep -Ev (/__pycache__/|\.pyc$) | while read' (traversal order)
ERROR: Filesystem ordering nondeterminism risk: python: os.listdir() used (must sort)
ERROR: Filesystem ordering nondeterminism risk: python: glob.glob() used (must sort)
ERROR: Filesystem ordering nondeterminism risk: python: Path.glob()/rglob() used without sorted(...)
```

**Classification:** GATE BUG (overly narrow exclusion filter).

**Root cause:** `check_filesystem_ordering_determinism.sh:34-39` defines:

```bash
filter_exclusions() {
  grep -v -E '^scripts/_graveyard/' | \
  grep -v -E 'scripts/(patch_|_patch_|_diag_).*' | \
  grep -v -E 'scripts/check_filesystem_ordering_determinism\.sh' | \
  grep -v "SV_ALLOW_UNSORTED_FS_ORDER"
}
```

The second filter matches `scripts/patch_*`, `scripts/_patch_*`, `scripts/_diag_*` only when the pattern immediately follows `scripts/`. The flagged paths are all under `scripts/_archive/patches/_patch_*` — the regex does not match because `_archive/patches/` intervenes. All 21 flagged hits across 9 files are under `scripts/_archive/patches/`; none are in the active script surface.

This is an evolutionary gap: the filter was written when `scripts/_graveyard/` was the canonical retirement location (hence the explicit first line). `scripts/_archive/` was introduced later as a distinct directory (8 commits touching it vs 15 for `_graveyard`) and never added to the exclusion list. A historical artifact `scripts/_graveyard/patch_fs_ordering_gate_exclude_graveyard_v1.sh` (itself in `_graveyard`) confirms someone previously added the graveyard exclusion when the same gap surfaced for that directory.

**Scope estimate:** ~30 minutes. One-line fix — add a `grep -v -E '^scripts/_archive/'` line to `filter_exclusions`, or broaden the existing second filter. Bonus optional: audit whether other directories (e.g., `scripts/_retired/`) need the same treatment.

**Cross-references:** Independent of 2dfb96e. Only touches `scripts/check_filesystem_ordering_determinism.sh`.

---

## Finding F5 — "Proof suite completeness violation" (redundant with F2)

**Originating gate:** `scripts/gate_proof_suite_completeness_v1.sh`
**Captured at:** lines 164 and 245 of `/tmp/proveci_finding_b.txt` (the gate is invoked twice in `prove_ci.sh`)
**Exact error text:**
```
ERROR: Proof suite completeness violation.
```

**Classification:** REAL ISSUE (same root cause as F2; redundant check).

**Root cause:** F5's gate greps the entire registry doc (`docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md`) for `scripts/prove_*.sh` mentions and compares to `git ls-files`. Verified that all 18 mentions currently live inside the SV_PROOF_SURFACE_LIST_v1 machine block — there is no prose mention outside the block — so F5 detects precisely the same drift F2 detects. When F2 is fixed (machine block regenerated from `git ls-files`), F5 passes automatically.

F5 and F2 are not semantically identical (F5 would catch a drift between the machine block and any prose mention; F2 would not), but at this point in the repo's history the two gates are checking the same content.

**Scope estimate:** Zero incremental work beyond F2. Fixing F2 closes F5 in the same commit.

**Cross-references:** F2 (same fix).

---

## Finding F6 — `gate_no_obsolete_allowlist_rewrite_artifacts_v1` expects deleted canonical files

**Originating gate:** `scripts/gate_no_obsolete_allowlist_rewrite_artifacts_v1.sh`
**Captured at:** lines 230–233 of `/tmp/proveci_finding_b.txt`
**Exact error text (four instances, one per canonical file):**
```
ERROR: expected canonical file missing: scripts/_patch_rewrite_allowlist_patchers_insert_sorted_no_eof_v2.py
ERROR: expected canonical file missing: scripts/patch_rewrite_allowlist_patchers_insert_sorted_no_eof_v2.sh
ERROR: expected canonical file missing: scripts/_patch_cleanup_allowlist_rewrite_recovery_artifacts_v1.py
ERROR: expected canonical file missing: scripts/patch_cleanup_allowlist_rewrite_recovery_artifacts_v1.sh
```

**Classification:** GATE BUG (Finding-2-style pattern — gate checks artifacts deliberately removed).

**Root cause:** The gate was created by commit `7f07191 "CI: gate obsolete allowlist rewrite recovery artifacts (v1)"` on 2026-02-08. Its logic has two checks:

1. A `deny_globs` array (patterns the gate forbids from ever returning). This half of the gate currently passes — no forbidden artifacts are present.
2. An `allow_exact` array of 4 canonical recovery-tooling files that MUST exist (defense-in-depth — the recovery tooling was meant to always be available). All 4 files were present at `2dfb96e^` and absent at `2dfb96e`.

The `allow_exact` half has failed since 2026-03-11 (2dfb96e). Duration of silent-red: **224 commits / 40 days** at time of this memo.

The 4 files appear to have been intentionally retired in 2dfb96e (commit subject: "engineering excellence: 512 tests, 100% docs, schema aligned") as part of a cleanup of one-time recovery tooling. The gate was written assuming they would remain permanent.

**Scope estimate:** ~45 minutes. Fix options:

1. **Empty the `allow_exact` array.** Keep the `deny_globs` half (which still serves a purpose — prevents regression of obsolete artifacts). The gate reduces to its deny-only role.
2. **Retire the gate entirely.** If the deny_globs half is also no longer needed (i.e., those specific obsolete patterns are extinct and not coming back), retire per the Finding-2 pattern established at `b84297e`: remove gate file, remove its invocation from `prove_ci.sh` (line 227), update CI proof-surface accounting if applicable.

Recommend option 1 unless there is evidence the deny patterns are stale.

**Cross-references:** Shares 2dfb96e root cause with F2, F3, F5, F7.

---

## Finding F7 — Contract doc references deleted enforcement gate

**Originating gate:** `scripts/gate_contract_surface_completeness_v1.sh:201`
**Captured at:** line 516 of `/tmp/proveci_finding_b.txt`
**Exact error text:**
```
ERROR: Enforced By script does not exist: doc=docs/contracts/rivalry_chronicle_contract_output_v1.md entry=scripts/gate_rivalry_chronicle_output_contract_v1.sh
```

**Classification:** REAL ISSUE (stale doc cross-reference).

**Root cause:** The contract doc `docs/contracts/rivalry_chronicle_contract_output_v1.md` lists two Enforced By scripts (lines 3–5):

```markdown
## Enforced By
- scripts/gate_rivalry_chronicle_output_contract_v1.sh      # <- MISSING (deleted in 2dfb96e)
- scripts/prove_rivalry_chronicle_end_to_end_v1.sh           # <- EXISTS
```

The first was present at `2dfb96e^` and absent at `2dfb96e`. The contract doc was not updated. The prove script still enforces end-to-end behavior, so partial contract enforcement remains in place; only the output-contract-specific gate is missing.

Check confirmed this is the only contract doc with a dangling Enforced By reference at HEAD (iterated over `docs/contracts/*.md`).

**Scope estimate:** ~20 minutes. Fix options:

1. **Remove the dangling line** from the contract doc (keep only the existing prove script). If the gate was deliberately retired because the prove script's end-to-end check is sufficient, this is correct.
2. **Re-create the gate.** If the output contract was meant to have a narrow gate distinct from the end-to-end proof (contract vs execution concerns), re-author the gate. Requires intent research — read the 2dfb96e delete diff, confirm whether the gate's role was intentionally absorbed into the prove script or just dropped.

Recommend option 1 on the balance of evidence (2dfb96e's "engineering excellence" framing suggests deliberate simplification), but flag option 2 as possible if Steve's intent at delete-time was different.

**Cross-references:** Shares 2dfb96e root cause with F2, F3, F5, F6.

---

## Proposed remediation sequence

Each finding is one commit, one session. Ordering principle: fix the gate bugs first so subsequent passes of `prove_ci.sh` don't carry noise signal into real-issue work.

**Phase 1 — Gate bugs (unblock the output surface):**

1. **F4** — `check_filesystem_ordering_determinism.sh` filter: add `scripts/_archive/` exclusion. One-line edit. ~30 min.
2. **F6** — `gate_no_obsolete_allowlist_rewrite_artifacts_v1.sh` `allow_exact`: empty or retire (prefer empty). ~45 min.
3. **F3** — `patch_idempotence_allowlist_v1.txt`: empty list contents. ~30 min.

**Phase 2 — Real issues (maintenance catch-up):**

4. **F2 + F5 (single commit)** — `CI_Proof_Surface_Registry_v1.0.md` machine block: regenerate from `git ls-files 'scripts/prove_*.sh' | sort`. ~30 min.
5. **F7** — `rivalry_chronicle_contract_output_v1.md` Enforced By: remove dangling line (pending intent confirmation). ~20 min.
6. **F1** — `scripts/process_full_season.sh`: convert four inline `PYTHONPATH=src python3` call sites to `./scripts/py`. ~90 min.

**Phase 3 — Finding B mechanism closure:**

7. After all six findings are fixed, `prove_ci.sh` should run with zero silent-red. At that point, a Finding B closure session adds `set -euo pipefail` to `scripts/prove_ci.sh`, confirms `rc=0` on clean worktree, and retires Finding B.

Total estimated work across all seven sessions: ~4.5 hours across ~7 commits.

---

## Mechanism path forward

The brief's Option B (adding errexit now with `|| true` on each pre-existing failure) is **not recommended** given this triage:

- Seven `|| true` markers for 7 findings that each have clean one-file fixes would be over-scaffolded. Adding them all now and removing them one by one as each gets fixed requires a cleanup gate that enforces "no `|| true` in `prove_ci.sh` except on cleanup commands."
- The alternative — fix in sequence, then add errexit once all gates are green — is equivalent in total work and avoids the tactical-scaffolding overhead.

**Recommended closure sequence for Finding B:** fix F1–F7 as independent sessions (Phase 1 and 2 above), then close Finding B mechanism (Phase 3). Phase 3 is near-zero-risk at that point — `prove_ci.sh` already runs green under a clean tree; errexit just makes a future new regression visible in CI.

No `|| true` should ever appear in `prove_ci.sh` except on the two existing cleanup `rm -f` lines (28 and 59).

---

## Out of scope for this session

- No changes to `scripts/prove_ci.sh`.
- No gate, script, or doc fixes for F1–F7.
- No changes to `.github/workflows/*`.
- No changes to `src/`, `Tests/`, or the Creative Layer.
- No retirement, rewrite, or relocation of any gate.

## What this memo does not claim

- **No retroactive inference about 2dfb96e's intent.** The commit message reads "engineering excellence: 512 tests, 100% docs, schema aligned" — that is consistent with a deliberate cleanup, but this memo does not assert the cleanup was wrong or right. It asserts only that the downstream gates, allowlists, and docs that referenced the removed files were not updated to reflect the removal, and that the resulting silent-red surface is Finding B's symptom.
- **No claim that all fixes should preserve current behavior.** F3 and F6 in particular may be candidates for full retirement (option 2 in their respective sections) rather than emptying (option 1). Intent-research is per-finding follow-up, not a triage decision.
- **No claim the 29-error count is exhaustive of `prove_ci.sh` pathology.** This memo reflects what fired on one clean-worktree run at `b84297e`. Environment-dependent failures, race-conditioned failures, and failures conditional on proof-specific state (e.g., if a fixture DB row were missing) could surface additional findings.

---

## References

- Baseline capture: `/tmp/proveci_finding_b.txt` (local, not committed)
- Session brief: `session_brief_finding_b_prove_ci_errexit_triage.md` (2026-04-22)
- Finding 2 retire precedent: `_observations/OBSERVATIONS_2026_04_22_FINDING2_OPS_ENTRYPOINTS_GATE_RETIRED.md`
- Commit `2dfb96e` (2026-03-11): load-bearing root for F2, F3, F5, F6, F7
- Commit `19414c1` ("Pre-commit: add repo-root allowlist gate (local/CI parity)"): contributing root for F2 (unregistered prove script)
- Commit `7f07191` (2026-02-08): introduced the F6 gate

---

## Gates passed for this session

- Ruff clean in `src/` — unchanged (no `src/` changes).
- Mypy clean on `src/squadvault/core/` — unchanged.
- Pytest: 1812 passed, 2 skipped — unchanged.
- Pre-commit hook matches canonical `scripts/git-hooks/pre-commit_v1.sh`.
- Memo exists under `_observations/` per repo-root allowlist rule; this commit adds exactly one file under that directory.

---

## Addendum log

*Append-only closure timeline. The triage above captured the
F-series in its initial state; this log records each finding's
resolution as it shipped, plus the four new findings (B/C/D/E)
spawned during F-series closure work, plus the final mechanism
closure (H1+H4) that converted strict-mode-on from a planned future
state into the active state on `prove_ci.sh`.*

### F1 — process_full_season.sh shim violations — CLOSED

**Commit `bcac553`** ("scripts: replace inline `PYTHONPATH=src
python3` with `scripts/py` shim in `process_full_season.sh` (F1)").
Replaced 4 inline `PYTHONPATH=src python3` invocations with
`./scripts/py` calls, restoring CWD-independence per the canonical
shim convention.

### F2 + F5 — Registry machine block / proof suite completeness — CLOSED

**Commit `a56c147`** ("CI: close F2+F5 — regenerate registry, wire
`prove_repo_root_allowlist` (Path A)"). Path A from the original
triage: registered the proof script and regenerated the
`CI_Proof_Surface_Registry` machine block. F2 and F5 closed
together because F5 was a redundant downstream symptom of F2.

### F3 — patch_idempotence_allowlist + autosync residue — CLOSED

**Commit `e358886`** ("CI: retire dormant idempotence-allowlist
cluster + autosync residue (F3 + autosync)"). Retirement (option 2
from the original triage), not emptying. The 7 referenced wrapper
scripts were genuinely dead code; the gate that referenced them was
also dead. Retired together.

### F4 — Filesystem-ordering gate false-positives on `_archive/` — CLOSED

**Commit `28ae2bf`** ("CI: fix filesystem-ordering gate — exclude
`scripts/_archive/` (F4)"). Excluded the archive directory from the
ordering scan, the simplest fix that preserved the gate's intent
for active scripts.

### F6 — `gate_no_obsolete_allowlist_rewrite_artifacts_v1` — CLOSED

**Commit `c98bda6`** ("CI: retire dormant
`gate_no_obsolete_allowlist_rewrite_artifacts_v1` (F6)"). Retired
the dormant gate. Closure observation memo:
`OBSERVATIONS_2026_04_27_F6_RETIREMENT.md`.

### F7 — Contract doc dangling Enforced By line — CLOSED

**Commit `6ceb550`** ("docs: remove dangling Enforced By line in
rivalry chronicle contract (F7)"). Single-line documentation fix.

### Finding B (new) — `gate_prove_ci_structure_canonical_v1` dormant checks — CLOSED

Spawned during F-series closure work. Discovered that a separate
gate carried dormant checks for retired scripts. **Commit
`cfaee3b`** ("CI: strip dormant checks from
`gate_prove_ci_structure_canonical_v1` (Finding B)"). Closure memo:
`OBSERVATIONS_2026_04_27_FINDING_B_CLOSURE.md`. The closure memo
asserted: "Finding B mechanism closure (`set -euo pipefail`
addition to `prove_ci.sh`) is now safe to land — there is no
pre-existing silent-rc=1 gate for it to expose."

That assessment was incomplete (see H1+H4 below).

### Finding C — Phase 7.8 prose-deletion residue (1/3) — CLOSED

**Commit `c90b4e4`** ("CI: retire Phase 7.8 prose-deletion residue
(Findings C + E + F)"). Bundled with E and F because all three were
residue from the same Phase 7.8 prose-deletion work that left
multiple downstream references stale. Closure memo:
`OBSERVATIONS_2026_04_27_FINDINGS_C_E_RETIREMENT.md`.

### Finding D — LC_ALL portability across 9 parity gates — CLOSED

**Commit `70e4003`** ("CI: add LC_ALL=C envelope to 9 parity gates
(Finding D)"). Added the deterministic-locale envelope to nine
parity-comparison gates that were susceptible to environment-
dependent sort/collation order. Closure memo:
`OBSERVATIONS_2026_04_27_FINDING_D_LC_ALL_PORTABILITY.md`.

### Finding E — Phase 7.8 prose-deletion residue (2/3) — CLOSED

Bundled with C in commit `c90b4e4`. Closure memo:
`OBSERVATIONS_2026_04_27_FINDINGS_C_E_RETIREMENT.md`.

### Finding F (named at retirement) — Phase 7.8 prose-deletion residue (3/3) — CLOSED

Bundled with C and E in commit `c90b4e4`.

### H1 + H4 — Strict mode on `prove_ci.sh` + dangling _status.sh source — CLOSED

**Commit `bfee780`** ("prove_ci: strict execution + retire dangling
`_status.sh` source (H1+H4)"). Bundled because H1's strict-mode
addition surfaced H4 as a silent-rc=1 latent failure on its first
attempted solo apply — exactly the failure mode H1 was designed to
expose. The CWD-independence gate had been silently red since
2026-03-11 (commit `2dfb96e`), masked by errexit-off behavior. H4
removed the dangling `source` line in `scripts/recap`; H1 added
`set -euo pipefail` after the deterministic envelope. Closure
memo: `OBSERVATIONS_2026_04_29_H1_H4_SHIPPED_AND_MEMORY_EVENTS_EXPOSED.md`.

H1 also surfaced a *third* latent failure (memory_events allowlist
gate) that was carried as a standing item but not recognized as
H1-coupled at the time of the closure memo. Tracked as H7 on
`PRIORITY_LIST_2026_04_28.md`.

### F-series workstream summary

The F-series began on 2026-04-20 with the triage that produced this
memo. Every sub-finding (F1–F7) and every spawned finding (B/C/D/E)
is now closed. The mechanism that the F-series was protecting —
`set -euo pipefail` on `prove_ci.sh` — is now active on
`origin/main`.

| Finding | Closed at | Closure memo |
|---|---|---|
| F1 | `bcac553` | (in commit message) |
| F2 + F5 | `a56c147` | `OBSERVATIONS_2026_04_27_F2_F5_PROSE_DRIFT_AND_REPO_ROOT_PROOF_GAP.md` |
| F3 | `e358886` | `OBSERVATIONS_2026_04_27_F3_RETIREMENT_AND_AUTOSYNC_RESIDUE.md` |
| F4 | `28ae2bf` | (in commit message) |
| F6 | `c98bda6` | `OBSERVATIONS_2026_04_27_F6_RETIREMENT.md` |
| F7 | `6ceb550` | (in commit message) |
| Finding B | `cfaee3b` | `OBSERVATIONS_2026_04_27_FINDING_B_CLOSURE.md` |
| Finding C | `c90b4e4` | `OBSERVATIONS_2026_04_27_FINDINGS_C_E_RETIREMENT.md` |
| Finding D | `70e4003` | `OBSERVATIONS_2026_04_27_FINDING_D_LC_ALL_PORTABILITY.md` |
| Finding E | `c90b4e4` | `OBSERVATIONS_2026_04_27_FINDINGS_C_E_RETIREMENT.md` |
| Finding F | `c90b4e4` | (bundled with C+E) |
| H1 + H4 | `bfee780` | `OBSERVATIONS_2026_04_29_H1_H4_SHIPPED_AND_MEMORY_EVENTS_EXPOSED.md` |

Total: 12 findings closed across 9 commits over 9 days
(2026-04-20 → 2026-04-29). Workstream is closed.

### Lesson — closure verification methodology

The Finding B closure memo at commit `cfaee3b` used "ERROR-prefixed
line count" as its verification signal for "no remaining silent-rc=1
gates." That signal was incomplete: two gates were silently failing
with output formats the regex did not match.

- The CWD-independence gate failed with `bash: source: No such file
  or directory` (no `ERROR:` prefix; surfaced by H1+H4).
- The memory_events gate failed with `❌ Downstream reads from
  memory_events are not allowed (outside allowlist)` (no `ERROR:`
  prefix; surfaced by H1+H4 → H7).

The honest assessment of "truly clean" required errexit itself.
Verification under errexit-off is fundamentally limited because
the script can return rc=0 even when individual gates have failed.

For future workstreams of this shape: when a gate's output format
is being relied upon for closure verification, enumerate every
possible failure-output format the gate can emit (`exit 1` with no
output, `exit 1` with `❌`, `exit 1` with bash error from a missing
sourced file, etc.) and ensure the verification regex covers all
of them. Or, more simply, run the script under errexit and treat
rc != 0 as the canonical signal.
