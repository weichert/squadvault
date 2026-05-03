# OBSERVATIONS_2026_05_02 — pfl.registry resolution: Position C selected (retire the orphaned gate)

**Predecessor:** `_observations/OBSERVATIONS_2026_05_02_PFL_REGISTRY_MODULE_MISSING.md` (f40a459) — the finding memo this resolution closes.

**Stated purpose:** select Position C (retire the orphaned gate `scripts/gate_standard_show_input_need_coverage_v1.sh` along with its `prove_ci.sh` invocation and registry entries) as the architecturally correct resolution to the `pfl.registry` ModuleNotFoundError. Reject Positions A and B with explicit reasoning. Frame the follow-on refactor session.

This memo resolves the question. It does not execute the retirement. `prove_ci.sh` continues to fail at rc=1 with `ModuleNotFoundError: No module named 'pfl.registry'` until a separate session ships the file move plus the `prove_ci.sh` and registry edits.

This is the **fifth instance** of `2dfb96e`-residue dormancy resolved in two weeks. The pattern recognition is now well-established and the precedent is extensive.

## The actual call chain

Reading the gate's source (`scripts/gate_standard_show_input_need_coverage_v1.sh`) end-to-end establishes that the gate is structurally identical to the rivalry-chronicle wrapper we retired earlier today: a thin shell wrapper around a Python heredoc whose only logic depends entirely on a deleted module.

The gate's full content (36 lines):

- Lines 1-3: bash scaffolding (shebang, errexit, repo-root resolution)
- Line 5: `PYTHONPATH="$repo_root/src" python - <<'PY'` — heredoc redirect
- Lines 6-35: Python heredoc with four `from pfl.*` imports plus logic that uses them
- Line 36: `PY` heredoc terminator

The four imports:

```python
from pfl.registry import STANDARD_SHOW_V1, CANONICAL_SEGMENT_REGISTRY_V1
from pfl.planning import resolve_show_plan
from pfl.coverage import resolve_input_need_coverage
from pfl.coverage_baseline_v1 import STANDARD_SHOW_V1_INPUT_NEEDS_BASELINE as expected
```

Every import targets a submodule under the `pfl.*` namespace. Every line of logic in the heredoc references one of those imports. There is no shell-level work that survives the imports failing. The entire gate is dead the moment `pfl/` was deleted.

## Canonical archaeology

The gate's git history is single-commit, and the broader `pfl` module's history tells the architectural story.

**`dab9252`** — "PFL Phase 6: enforce STANDARD_SHOW_V1 InputNeed coverage baseline (v1)". The gate's only commit. Added in the same multi-phase build that produced the `pfl` module.

**The PFL broadcast/show-planning module was built across six phases:**

```
3217e98 PFL Phase 1+: deterministic broadcast models + commissioner settings
bfd3c16 PFL Phase 2: deterministic broadcast schema primitives (v1)
3a34a9e PFL: enums.py newline at EOF
46e1e0f PFL Phase 3: segment registry + tests (v1)
2d0fc11 PFL Phase 4: deterministic show plan resolver (v1)
a182065 PFL Phase 5: deterministic InputNeed coverage resolution (v1)
dab9252 PFL Phase 6: enforce STANDARD_SHOW_V1 InputNeed coverage baseline (v1)
```

Substantial work — six commits across the phases, building a complete `pfl.*` namespace: `pfl.registry`, `pfl.planning`, `pfl.coverage`, `pfl.coverage_baseline_v1`, `pfl.enums`, plus the Phase 6 enforcement gate.

**`2dfb96e`** — "engineering excellence: 512 tests, 100% docs, schema aligned". The same 1,427-file sweep cleanup that retired four other gates throughout today's investigation chain. **Deleted the entire `pfl/` module.**

The Phase 6 gate `gate_standard_show_input_need_coverage_v1.sh` survived the sweep — it's a `scripts/` file, not a `src/pfl/` file — but its imports now point to nothing. The pattern is identical to the rivalry-chronicle wrapper retirement we shipped earlier this evening.

A note about which "PFL" this is: the project's name is "PFL Buddies" (the fantasy football league this codebase serves), but the deleted `pfl.*` module appears to have been a separate broadcast/show-planning concept — possibly intended for some out-of-scope feature, possibly relating to the Constitution's "Broadcast" mention. Whatever its product purpose, the module was deliberately removed in `2dfb96e`'s engineering-excellence sweep, alongside the other 1,426 files in that commit.

## What the prior finding memo got right and wrong

The earlier finding memo (`f40a459`) named three coherent interpretations of the failure: PYTHONPATH/install issue (1), dormant import never implemented (2), sweep-cleanup orphan analogous to `2dfb96e` (3).

The interpretation cluster recasts after the doc-read:

**Interpretation 1 (PYTHONPATH issue)** — rejected. The gate sets `PYTHONPATH="$repo_root/src"` explicitly before invoking Python. If `pfl/` existed at `src/pfl/`, the import would work. The issue is not configuration; it's missing source.

**Interpretation 2 (dormant import never implemented)** — rejected. The git history shows `pfl.*` was implemented across six phase commits before being deleted. This is not a "planned but never built" case; it is a "built and then deliberately swept" case.

**Interpretation 3 (sweep-cleanup orphan)** — confirmed. `2dfb96e` deleted `pfl/`; the Phase 6 gate at `scripts/gate_standard_show_input_need_coverage_v1.sh` survived the sweep but its imports broke. Identical pattern to the gate_contract_linkage retirement we shipped earlier this session at commit `4ceb28b`.

## Position C selected

Position C: retire `scripts/gate_standard_show_input_need_coverage_v1.sh` and the cluster of references that point at it.

The reasoning chain:

1. The gate's existence is structurally tied to the `pfl` module's existence. Without `pfl.*`, the gate's Python heredoc cannot run; with the heredoc broken, the gate has no architectural purpose.
2. The gate has no shell-level logic to preserve. Its entire substantive content is the Python heredoc which depends entirely on the deleted module.
3. `2dfb96e`'s sweep cleanup was deliberate; restoring the `pfl` module to feed the gate would undo that cleanup without a justifying invariant. The sweep removed 1,427 files in a coordinated engineering-excellence pass — selectively unwinding one slice of it without architectural rationale would be ad-hoc.
4. **Five-instance precedent.** This is the fifth `2dfb96e`-residue retirement. The 2026-04-22 (Finding 2), 2026-04-27 (F3 + F6 + C/E/F triple), and earlier-tonight (gate_contract_linkage) retirements all closed structurally-identical orphan gates. The pattern is well-rehearsed.
5. Retirement closes the rc=1 by removing the dormant call chain entirely. No new gate logic needed. No restoration of swept-cleanup content needed.

## Why Position A was rejected

Restoring `pfl/` from history would undo `2dfb96e`'s deliberate sweep cleanup. The sweep removed 1,427 files in a single commit titled "engineering excellence: 512 tests, 100% docs, schema aligned" — a self-evidently deliberate consolidation. Restoring one module from that sweep without architectural context for what made it different from the other content would be ad-hoc unwinding driven by a downstream call site.

If a future session decides the PFL broadcast/show-planning capability is valuable and should be reconstituted, that would be a *new feature design exercise* — start from product intent, decide whether the capability fits the post-MVP roadmap, design from scratch. Not a restoration of a deleted module to satisfy a dormant gate.

## Why Position B was rejected

The gate's heredoc has no fall-back logic — every line of Python depends on the deleted imports. There is no shell-level work to preserve. Rewriting the gate to do something different would mean *implementing a new gate inside what used to be a wrapper file* — that's a new feature, not a fix.

A Position B alternative interpretation might be: rewrite the gate to enforce a different invariant that doesn't depend on `pfl`. That's out of scope for this session and would require a separate design exercise to identify what invariant is worth enforcing.

## Surgical edit scope (for the follow-on session)

Five coordinated edits, parallel to today's earlier gate_contract_linkage retirement (`4ceb28b`) but slightly simpler — no marker block in `prove_ci.sh` to remove:

1. **Move the gate to archived state.** `git mv scripts/gate_standard_show_input_need_coverage_v1.sh scripts/_archive/unreferenced/gate_standard_show_input_need_coverage_v1.sh`. Preserves blame.

2. **Remove the invocation from `prove_ci.sh`.** Single line at line 236: `bash scripts/gate_standard_show_input_need_coverage_v1.sh`. No surrounding SV_GATE markers (verified via grep).

3. **Remove the corresponding registry entries.**
   - `docs/80_indices/ops/CI_Guardrails_Index_v1.0.md` line 52: remove the entry.
   - `docs/80_indices/ops/CI_Guardrail_Entrypoint_Labels_v1.tsv` line 32: remove the matching TSV row.
   - `docs/80_indices/ops/CI_Guardrails_Surface_Fingerprint_v1.txt`: regenerate via `scripts/gen_ci_guardrails_surface_fingerprint_v1.py`.

The 2026-04-27 retirement memo and today's gate_contract_linkage retirement both ship with this exact edit shape; the apply script pattern from `4ceb28b` can be adapted with anchor pattern updates.

After the surgical retirement, `prove_ci.sh`'s invocation of the broken gate is gone. Whether `prove_ci.sh` returns rc=0 overall depends on whether further-downstream gates have additional dormancy residue.

## Side-finding worth recording for separate sessions

**Side-finding E — the PFL broadcast/show-planning module's product question is open.**

`Rivalry_Chronicle_v1_Contract_Card.md` exists as a canonical artifact and was retiring one form of contract enforcement when we landed `4ceb28b`. The PFL broadcast/show-planning module is a different shape: it was a multi-phase implementation that got swept entirely. Whether the broadcast/show-planning capability is something the post-MVP product roadmap wants is a question that lives somewhere between this resolution and Phase B/C of the Operational Plan.

This memo does not reopen that question. The retirement here closes a code-level dormancy. Reconstituting (or formally rejecting) the broadcast capability is a future product-direction decision, not part of the dormancy cleanup.

## Pattern note — `2dfb96e`-residue dormancy, fifth instance

This is the fifth instance of `2dfb96e`-residue dormancy resolved in two weeks:

1. **F3 cluster** — retired 2026-04-27.
2. **F6** — retired 2026-04-27.
3. **C/E/F triple** (3 gates) — retired 2026-04-27.
4. **gate_rivalry_chronicle_contract_linkage** — retired earlier today (`4ceb28b`).
5. **(This memo)** — Position C selected for `gate_standard_show_input_need_coverage_v1.sh`.

The pattern remains: `2dfb96e` was a 1,427-file sweep that did not follow through with all `prove_ci.sh` invocations and registry references. After this resolution's follow-on retirement ships, additional `2dfb96e`-residue dormancy may surface as `prove_ci.sh` advances further.

The investigation pattern at this point is fully reproducible: re-grounding step 1, doc-read for archaeology (what was the deleted target's history?), confirm the surviving caller has no preserveable logic, ship the retirement using the precedent-based six-edit pattern. Future-Steve picking up the next `prove_ci.sh` failure should test the "is this `2dfb96e`-residue dormancy?" hypothesis early in the investigation.

## What this memo does not do

- **Does not execute the retirement.** Per session discipline established across today's earlier sequences, one topic per session. This session resolves the architectural question; the next session executes the surgical retirement.
- **Does not propose reconstituting the PFL broadcast/show-planning capability.** That is a product-direction question separate from the dormancy cleanup.
- **Does not restore `pfl/` from history.** The module's deletion was deliberate; this resolution achieves the operational outcome by retiring the orphaned gate rather than restoring its dependency.

## Cross-references

- `_observations/OBSERVATIONS_2026_05_02_PFL_REGISTRY_MODULE_MISSING.md` (f40a459) — the finding memo this resolution closes.
- `_observations/OBSERVATIONS_2026_05_02_GATE_CONTRACT_LINKAGE_RESOLUTION.md` (328d9ac) — today's earlier resolution for a structurally identical dormancy. This memo follows the same shape.
- `_observations/OBSERVATIONS_2026_04_27_FINDINGS_C_E_RETIREMENT.md` — three shell gates retired for the same `2dfb96e` root cause; precedent for the surgical edit shape.
- `_observations/OBSERVATIONS_2026_04_22_FINDING2_OPS_ENTRYPOINTS_GATE_RETIRED.md` — first retirement of `2dfb96e` / Phase 7.8 dormancy residue.
- Commit `dab9252` — added the gate as Phase 6 enforcement.
- Commits `3217e98`, `bfd3c16`, `46e1e0f`, `2d0fc11`, `a182065` — the Phase 1-5 builds of the `pfl` module that supported the gate.
- Commit `2dfb96e` — the 1,427-file sweep that deleted the `pfl/` module without removing the gate or its registry entries.
- Commit `4ceb28b` (today) — gate_contract_linkage retirement; direct precedent for this resolution's surgical edit pattern.

## Append-only

This memo records the resolution. It does not edit any prior memo or artifact. `prove_ci.sh` continues at rc=1; the failure is now an explicitly-recorded transitional condition with a known and well-precedented resolution path, awaiting execution in a follow-on session.
