# OBSERVATIONS_2026_05_02 — gate_contract_linkage resolution: Position C selected (retire the orphaned wrapper)

**Predecessor:** `_observations/OBSERVATIONS_2026_05_02_GATE_CONTRACT_LINKAGE_MISSING.md` (d9c93e6) — the finding memo this resolution closes.

**Stated purpose:** select Position C (retire the orphaned wrapper `gate_rivalry_chronicle_contract_linkage_v1.sh` along with its `prove_ci.sh` invocation and registry entries) as the architecturally correct resolution to the gate_contract_linkage_v1.sh missing failure. Reject Positions A and B with explicit reasoning. Frame the follow-on refactor session.

This memo resolves the question. It does not execute the retirement. `prove_ci.sh` continues to fail at rc=127 until a separate session ships the file move plus the `prove_ci.sh` and registry edits.

The doc-read this session also surfaced that the original finding memo's three interpretations were reasoning about an incomplete picture: the missing gate is invoked transitively (through a wrapper), not directly by `prove_ci.sh`. This memo's interpretations are recast against the actual call chain.

## The actual call chain

`prove_ci.sh` does not directly reference `gate_contract_linkage_v1.sh`. The chain is:

1. `prove_ci.sh:236` invokes `bash scripts/gate_rivalry_chronicle_contract_linkage_v1.sh` (this file exists).
2. `gate_rivalry_chronicle_contract_linkage_v1.sh:10` invokes `bash scripts/gate_contract_linkage_v1.sh` (this file is missing — the rc=127).

The intermediate file is a **10-line compatibility wrapper.** Its entire substantive content:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Compatibility wrapper: RC contract linkage gate -> general contract linkage gate (v1)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

bash scripts/gate_contract_linkage_v1.sh
```

The wrapper does nothing except delegate to the general gate. With the general gate gone, the wrapper has no remaining purpose.

## Canonical archaeology

The lifecycle is unambiguous from the commit history.

**`a77140c`** — added `gate_rivalry_chronicle_contract_linkage_v1.sh` originally as the rivalry-chronicle linkage gate.

**`5862a08`** — "CI: general contract linkage gate (v1) + RC wrapper delegation". This single commit:
- Created `gate_contract_linkage_v1.sh` as a new general-purpose contract linkage gate.
- Rewrote `gate_rivalry_chronicle_contract_linkage_v1.sh` as a thin wrapper that delegates to the new general gate.

So the wrapper's existence is structurally tied to the general gate. The intent at the time was: rivalry-chronicle linkage enforcement is a special case of general contract linkage enforcement; the rivalry-chronicle gate becomes a wrapper for backward compatibility while the general gate handles the actual checks.

**Several maintenance commits followed** (`3949c06`, `4b4a870`, `d9628c8`, `3139aa2`) — each touching the general gate, none touching the wrapper. The wrapper had nothing to maintain because it had no logic.

**`2dfb96e`** — "engineering excellence: 512 tests, 100% docs, schema aligned". A 1,427-file sweep cleanup. **Deleted `gate_contract_linkage_v1.sh`.** Did not delete the wrapper. Did not remove the wrapper's invocation from `prove_ci.sh`.

The result: the wrapper became orphaned. It points at a file that no longer exists. `prove_ci.sh` invokes the wrapper, which invokes the missing file, which produces rc=127 ("command not found").

**`9404659`** — a prior session author drafted a hygiene bundle to address this exact situation. The 2026-04-27 retirement memos reference `9404659` as "unpushed; resolves when that bundle lands." It never landed. It exists in no branch this repo has access to. Whatever work was in `9404659` is functionally lost.

## What the prior finding memo got right and got wrong

The earlier finding memo (`d9c93e6`) named three coherent interpretations of the failure: gate archived but invocation remained (1), gate planned but never implemented (2), gate moved or renamed (3). The memo correctly identified the most likely interpretation as (1) by analogy to the 2026-04-27 retirement precedent.

What the memo did not have: the call chain. The memo's framing assumed `prove_ci.sh` directly invokes `gate_contract_linkage_v1.sh`. This session's `grep` revealed the missing gate is invoked *transitively* via the rivalry-chronicle wrapper. That changes the resolution from "remove the invocation from `prove_ci.sh`" (the memo's implied fix) to "retire the wrapper, which removes the invocation from `prove_ci.sh` as a side-effect."

The interpretation cluster recasts:

**Interpretation A** — restore `gate_contract_linkage_v1.sh` from history (so the wrapper has its delegation target back). Rejected: would undo `2dfb96e`'s deliberate sweep cleanup, and there's no evidence anywhere that the gate's removal in `2dfb96e` was a mistake. The 1,427-file sweep was deliberate engineering-excellence work; restoring one file from it without also restoring everything else of similar shape would be selective unwinding without a justifying invariant.

**Interpretation B** — rewrite the wrapper so it doesn't delegate (i.e., implement the contract-linkage check inside the wrapper itself). Rejected: the wrapper has zero substantive logic. There's nothing to rewrite. Rewriting would mean *implementing a new gate inside what used to be a wrapper file* — that's a new feature, not a fix, and it's out of scope for the dormancy resolution this session is handling.

**Interpretation C** — retire the wrapper. The wrapper is orphaned residue from `2dfb96e`'s incomplete sweep. The 2026-04-27 retirement precedent (Findings C, E, F) addressed three structurally-identical orphaned shell gates; this is a fourth instance of the same pattern.

## Position C selected

Position C: retire `gate_rivalry_chronicle_contract_linkage_v1.sh` and the cluster of references that point at it.

The reasoning chain in canonical-document order:

1. The wrapper's existence is structurally tied (per `5862a08`'s commit subject) to the general gate's existence. Without the general gate, the wrapper has no architectural purpose.
2. The wrapper has no substantive logic to preserve. Its entire content is the delegation call to the now-deleted file.
3. `2dfb96e`'s sweep cleanup was deliberate; restoring the general gate to feed the wrapper would undo that cleanup without a justifying invariant.
4. The 2026-04-27 retirement precedent retired three shell gates wholesale for the same root cause (orphaned by Phase 7.8 / `2dfb96e` sweep). The retirement was commissioner-authorized at the time. Same precedent applies here.
5. Retirement closes the rc=127 by removing the dormant call chain entirely. No new gate logic needed. No restoration of swept-cleanup content needed.

## Why Position A was rejected

Restoring `gate_contract_linkage_v1.sh` from history would undo `2dfb96e`'s deliberate sweep cleanup. The sweep removed 1,427 files in a single commit titled "engineering excellence: 512 tests, 100% docs, schema aligned" — a self-evidently deliberate consolidation. Restoring one file from that sweep without architectural context for what made it different from the other 1,426 would be ad-hoc unwinding driven by a downstream call site rather than by re-evaluation of the cleanup decision.

If a future session decides the contract-linkage enforcement was valuable and should be reconstituted, that would be a *new feature* with a written architectural justification, not a restoration of a deleted file to satisfy a dormant wrapper.

## Why Position B was rejected

The wrapper file has no substantive logic — it's a 10-line shell script of which 9 lines are scaffolding (shebang, `set -euo pipefail`, repo-root resolution, `cd`) and the 10th line is the delegation call. There is no enforcement logic to "rewrite into the wrapper."

A Position B alternative interpretation might be: implement actual rivalry-chronicle contract linkage enforcement inside what used to be the wrapper. That's a new feature, not a dormancy resolution, and it's out of scope. If reconstituted contract-linkage enforcement is wanted, that would be its own design exercise — start from the contract card and the architectural model, not from filling in an empty wrapper.

## Surgical edit scope (for the follow-on session)

Three coordinated edits, parallel to the 2026-04-27 retirement of three shell gates:

1. **Move the wrapper to archived state.** `git mv scripts/gate_rivalry_chronicle_contract_linkage_v1.sh scripts/_archive/unreferenced/gate_rivalry_chronicle_contract_linkage_v1.sh`. Preserves blame.

2. **Remove the invocation from `prove_ci.sh`.** Line 236 (`bash scripts/gate_rivalry_chronicle_contract_linkage_v1.sh`) plus the `SV_GATE: rivalry_chronicle_contract_linkage (v1) begin/end` markers (around line 320, per earlier grep evidence).

3. **Remove the corresponding registry entries.**
   - `docs/80_indices/ops/CI_Guardrails_Index_v1.0.md`: remove the entry for `gate_rivalry_chronicle_contract_linkage_v1.sh`.
   - `docs/80_indices/ops/CI_Guardrail_Entrypoint_Labels_v1.tsv`: remove the matching TSV row.
   - `docs/80_indices/ops/CI_Guardrails_Surface_Fingerprint_v1.txt`: regenerate. The surface-freeze gate computes the fingerprint from the canonical surface (prove_ci gate-cluster region + Labels TSV + Index entry block); removing entries materially changes the fingerprint and regeneration is a required parity step.

The 2026-04-27 retirement memo (`OBSERVATIONS_2026_04_27_FINDINGS_C_E_RETIREMENT.md`) provides the exact shape of these edits, including the fingerprint regeneration step.

After the surgical edit, `prove_ci.sh` should advance past the now-removed invocation cleanly. Whether it returns rc=0 overall depends on whether further-downstream gates have additional dormancy residue this session did not surface.

## Side-finding worth recording for separate sessions

**Side-finding D — rivalry-chronicle contract has no meaningful automated enforcement.**

`Rivalry_Chronicle_v1_Contract_Card.md` exists as a canonical artifact in the project. With the wrapper retired, no automated gate enforces its contract linkage. Realistically, no gate has been *meaningfully* enforcing it since `2dfb96e` — the wrapper has been calling a deleted file ever since, producing the rc=127 we've been chasing rather than any actual enforcement. So this side-finding is not introducing a regression; it's recording that the absence of enforcement was already true and is now made structurally explicit by the retirement.

A future session might want to reconstitute meaningful rivalry-chronicle contract linkage enforcement. That would be a new design — start from the contract card, identify the invariants worth checking, write a real gate that performs real checks. Not a restoration of the dormant wrapper.

## Pattern note — `2dfb96e`-residue dormancy

This is the fourth instance of `2dfb96e`-related dormancy resolved in the past two weeks:

1. F3 cluster — retired 2026-04-27.
2. F6 — retired 2026-04-27 (separate from C/E/F).
3. C/E/F — three gates retired 2026-04-27 (Findings C, E, F).
4. **(This memo)** — Position C selected for `gate_rivalry_chronicle_contract_linkage_v1.sh`.

The pattern: `2dfb96e` was a 1,427-file sweep that did not fully follow through with all `prove_ci.sh` invocations and registry references. Each surfacing instance is one more missed cleanup. There is no reason to assume this is the last instance. The next time `prove_ci.sh` advances further than it has before — for example, after this resolution's follow-on refactor ships — additional `2dfb96e`-residue dormancy may surface. Future-Steve picking up the next prove_ci.sh failure should test the hypothesis "is this `2dfb96e`-residue dormancy?" early in the investigation. The pattern recognition is now well-rehearsed.

## What this memo does not do

- **Does not execute the retirement.** Per session discipline established in today's H7 Cat B and docs-integrity sequences, one topic per session. This session resolves the architectural question; the next session executes the surgical retirement.
- **Does not propose reconstituting rivalry-chronicle contract linkage enforcement.** The dormant wrapper was not enforcing anything meaningful; retiring it does not weaken any actual enforcement. Reconstituting real enforcement is a separate design exercise.
- **Does not restore `9404659`.** The hygiene bundle is functionally lost; this resolution achieves the same operational outcome by retiring rather than fixing. Future-Steve does not need to find or recreate `9404659`.

## Cross-references

- `_observations/OBSERVATIONS_2026_05_02_GATE_CONTRACT_LINKAGE_MISSING.md` (d9c93e6) — the finding memo this resolution closes.
- `_observations/OBSERVATIONS_2026_04_27_FINDINGS_C_E_RETIREMENT.md` — three shell gates retired for the same root cause; direct precedent for the surgical edit shape.
- `_observations/OBSERVATIONS_2026_04_22_FINDING2_OPS_ENTRYPOINTS_GATE_RETIRED.md` — first retirement of `2dfb96e` / Phase 7.8 dormancy residue; established the archaeology pattern.
- `_observations/OBSERVATIONS_2026_05_02_DOCS_INTEGRITY_GATE_RESOLUTION.md` (b3885d0) — today's earlier resolution for a structurally similar dormancy. This memo follows the same shape.
- Commit `5862a08` — added the general gate and rewrote the rivalry-chronicle gate as a delegation wrapper.
- Commit `2dfb96e` — the 1,427-file sweep that deleted the general gate without removing the wrapper or its invocation.
- `Rivalry_Chronicle_v1_Contract_Card.md` — the canonical artifact whose contract linkage was nominally being enforced; side-finding D records the absence of meaningful enforcement as a separate concern.

## Append-only

This memo records the resolution. It does not edit any prior memo or artifact. `prove_ci.sh` continues at rc=127; the failure is now an explicitly-recorded transitional condition with a known and well-precedented resolution path, awaiting execution in a follow-on session.
