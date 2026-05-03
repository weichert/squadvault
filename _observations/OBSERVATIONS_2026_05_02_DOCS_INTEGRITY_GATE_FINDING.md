# OBSERVATIONS_2026_05_02 — docs-integrity gate finding (deferred)

**Predecessor:** `OBSERVATIONS_2026_05_02_H7_CAT_B_RESOLUTION.md` (today's H7 Cat B resolution); commit `1dbc24c` (today's H7 Cat B refactor).

**Stated purpose:** record a finding surfaced during the H7 Cat B refactor session: the docs-integrity gate (`scripts/check_docs_integrity_v1.py`) is failing in a shape that requires architectural-level resolution rather than a one-line index update. Defer the resolution to a separate session and document the finding while context is fresh.

This memo does not propose a fix. It records the finding, the three coherent interpretations of what's wrong, and why this session deferred. Future-Steve picking this up should read this memo, then read the cited commits, then form a position before touching the gate or the index.

## How the finding surfaced

The H7 Cat B refactor (commit `1dbc24c`) closed the memory_events allowlist gate failure. Running `prove_ci.sh` afterward returned `rc=1` from a different gate further down — the docs integrity gate at `scripts/check_docs_integrity_v1.py:137`:

```
==> Docs integrity gate (v1)
FAIL: CI guardrails index coverage gate failed:
- missing ref/link to invariant doc: docs/80_indices/ops/Docs_Integrity_Gate_Invariant_v1.0.md
- missing ref/link to proof runner: scripts/prove_docs_integrity_v1.sh
```

This is the gate behavior anticipated by today's resolution memo: with the memory_events gate green, errexit lets `prove_ci.sh` advance further, surfacing the next-failing gate. The new failure is unrelated to the H7 Cat B refactor.

## What the gate checks

`scripts/check_docs_integrity_v1.py:gate_ci_index_coverage()` reads one specific index file and performs literal substring matching for two strings:

```python
inv = "docs/80_indices/ops/Docs_Integrity_Gate_Invariant_v1.0.md"
runner = "scripts/prove_docs_integrity_v1.sh"
```

If either string is absent from the index file, the gate fails. The index file is hardcoded at the call site:

```python
ci_index = REPO_ROOT / "docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"
```

Both strings are absent from `CI_Guardrails_Index_v1.0.md` at HEAD. Both target files exist on disk:
- `docs/80_indices/ops/Docs_Integrity_Gate_Invariant_v1.0.md` — exists.
- `scripts/prove_docs_integrity_v1.sh` — exists.

So the failure is "the index doesn't reference these two existing artifacts," not "the index references missing artifacts."

## What `CI_Guardrails_Index_v1.0.md` actually contains

The index file is a single bounded block bracketed by HTML comment markers:

```
<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->
# CI Guardrails Ops Entrypoints

# - This section is enforced by scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh
# - Canonical Ops cluster order source: docs/80_indices/ops/CI_Guardrails_Ops_Cluster_Order_v1.tsv

- scripts/gate_ci_guardrails_ops_cluster_canonical_v1.sh — Ops guardrails cluster canonical gate (v1)
- scripts/gate_ci_guardrails_ops_entrypoint_exactness_v1.sh — Ops guardrails entrypoint block exactness gate (v1)
... [~40 more entries, all `scripts/gate_*.sh`] ...
- scripts/gate_worktree_cleanliness_v1.sh — Worktree cleanliness gate (v1)
<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->
```

Every entry in the block is a `scripts/gate_*.sh` script. The block's title and the enforcing-gate comment both assert its scope is "CI Guardrails Ops Entrypoints" — gate scripts specifically, not invariant docs or proof runners.

The gate at `check_docs_integrity_v1.py` is asking this index to also reference an invariant doc (`.md`) and a proof runner (`prove_*.sh`). Neither shape currently appears in the index. Adding them would either:

- Break the index's structural coherence (it becomes a mixed list of gates, invariants, and proof runners), or
- Require a new section in the index file (with new boundary markers and possibly a new enforcing gate) to accommodate the additional categories.

`prove_docs_integrity_v1.sh` does already appear in `CI_Proof_Surface_Registry_v1.0.md` (lines 11 and 63) and `Docs_Integrity_Gate_Invariant_v1.0.md` (line 80). The gate's check, narrowly, is "is this string present in `CI_Guardrails_Index_v1.0.md`" — but the string is plausibly present elsewhere in the documentation graph already.

## Three coherent interpretations

### Interpretation 1 — the index's scope should expand

Under this reading, `CI_Guardrails_Index_v1.0.md` should be the canonical reference list for **all** docs-integrity-relevant artifacts, not just gate scripts. The gate at `check_docs_integrity_v1.py` is correct as written; the fix is to add new entries (and likely a new section header) to the index, expanding its scope.

The objection: this conflicts with the index file's explicit `# CI Guardrails Ops Entrypoints` framing. The file's own comment asserts it is a single-purpose registry for gate scripts. Expanding its scope without updating the comment would create an internal contradiction; updating the comment is itself a structural change that wants design intent rather than a patch.

### Interpretation 2 — the gate is checking the wrong file

Under this reading, the docs-integrity gate's `ci_index` path is wrong. The two strings the gate looks for are a proof runner and an invariant doc — neither is a "CI Guardrails Ops Entrypoint." A different index already handles proof runners (`CI_Proof_Surface_Registry_v1.0.md`); a different artifact handles invariant docs (`Docs_Integrity_Gate_Invariant_v1.0.md` itself, which is *the* invariant doc). The fix is to either:

- Change the gate's `ci_index` path to a more appropriate target, or
- Have the gate check multiple indexes against multiple categories.

The objection: changing what an existing gate checks against is itself an architectural change. The original commit that added this gate (`a6657b1`, "Docs: add canonical docs integrity gate (v1)") presumably had intent about which index it was meant to enforce coverage on. Reading that commit before changing the gate is required.

### Interpretation 3 — the gate has a bug or stale assumption

Under this reading, `check_docs_integrity_v1.py` was written when `CI_Guardrails_Index_v1.0.md` had a wider scope, or against a planned-but-never-implemented expansion. The gate's logic became disconnected from the index's actual structure as the index evolved. The fix is to reconcile by reading the canonical history of both files and choosing whether to update the gate, the index, or both.

This interpretation is the most likely if the gate has been inert (rc=0 or unrun) until the H7 Cat B refactor closed the memory_events gate — at which point errexit advanced `prove_ci.sh` to the docs-integrity gate for the first time. If `check_docs_integrity_v1.py` has been silently failing for some time and only became visible today, the assumption-stale interpretation is consistent with that timeline.

## Why this session deferred

Four reasons:

1. **Architectural ambiguity, not a missing-line problem.** Each of the three interpretations above suggests a different change. Picking one without understanding the gate's design intent risks ratifying drift rather than resolving it. The same shape as the H7 Cat B issue resolved earlier today.

2. **Today's drift count is already high.** Six instances of stale-assertion drift have surfaced in today's sessions. Adding a hasty fix to a gate-vs-index mismatch without reading the gate's history is exactly the failure mode that count-of-six is the result of.

3. **The session's stated deliverable is complete.** The H7 Cat B refactor is committed and shipped (`1dbc24c`); the memory_events allowlist gate passes; the architectural transitional state from this morning's resolution memo is closed. The session succeeded on its own terms.

4. **Resolution wants a doc-read session.** The right shape is the same shape as today's H7 Cat B resolution session: read the gate's commit, read the index's commit, read related canonical artifacts, form a position, ship a resolution memo, then ship the fix in a follow-on session.

## What's next

A future session should:

1. Read commit `a6657b1` ("Docs: add canonical docs integrity gate (v1)") in full — the message body and the diff. Establishes original intent.
2. Read the most recent commits that touched `CI_Guardrails_Index_v1.0.md` and the `<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->` boundary markers. Establishes the index's evolution.
3. Read `CI_Proof_Surface_Registry_v1.0.md` and `Docs_Integrity_Gate_Invariant_v1.0.md` to understand how the proof-surface and invariant categories are currently organized elsewhere.
4. Form a position on which interpretation (1, 2, 3, or a fourth) is correct. Ship a resolution memo.
5. In a separate session, ship the fix.

That's at minimum two sessions. The first is the doc-read; the second is the code change. Today's H7 Cat B sequence (escalation → resolution → refactor) is the precedent shape.

## Cross-references

- Commit `a6657b1` ("Docs: add canonical docs integrity gate (v1)") — the gate's establishing commit.
- Commit `1dbc24c` ("ingest: remove diagnostic memory_events reads (H7 Cat B Position 2)") — today's H7 Cat B refactor, whose completion surfaced this finding.
- `scripts/check_docs_integrity_v1.py` — the gate's source.
- `docs/80_indices/ops/CI_Guardrails_Index_v1.0.md` — the index the gate checks.
- `docs/80_indices/ops/Docs_Integrity_Gate_Invariant_v1.0.md` — one of the two strings the gate looks for; itself an existing canonical artifact.
- `scripts/prove_docs_integrity_v1.sh` — the other string the gate looks for; itself an existing proof runner.
- `docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md` — already references the proof runner (lines 11 and 63), establishing that the proof runner has documentation in the system; the question is just whether `CI_Guardrails_Index_v1.0.md` is the right additional location.
- `_observations/OBSERVATIONS_2026_05_02_H7_CAT_B_RESOLUTION.md` — today's H7 Cat B resolution memo, whose investigation pattern this finding's future resolution should follow.

## Append-only

This memo records the finding. It does not edit any prior memo or artifact, including the gate, the index, or `prove_ci.sh`. The gate continues to fail at rc=1; the failure is now an explicitly-recorded transitional condition with a known-but-deferred resolution path, paralleling how today's H7 Cat B finding was held between escalation and resolution.
