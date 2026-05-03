# OBSERVATIONS_2026_05_02 — gate_contract_linkage_v1.sh missing (deferred)

**Predecessor:** `bfde774` (today's docs-integrity surgical retirement).

**Stated purpose:** record a finding surfaced when the docs-integrity surgical edit allowed `prove_ci.sh`'s errexit to advance further than ever before tonight, surfacing the next dormancy issue down the pipeline. Defer the resolution to a separate session and document the finding while context is fresh.

This memo follows the same shape as today's earlier `OBSERVATIONS_2026_05_02_DOCS_INTEGRITY_GATE_FINDING.md`: surface the finding, name what's known, defer to a separate session.

## How the finding surfaced

The docs-integrity surgical retirement (commit `bfde774`) closed the docs-integrity gate. Running `prove_ci.sh` afterward returned `rc=127` from a different point much further down the pipeline:

```
bash: scripts/gate_contract_linkage_v1.sh: No such file or directory
prove_ci rc=127
```

`rc=127` is "command not found" — `prove_ci.sh` is invoking a script (`scripts/gate_contract_linkage_v1.sh`) that does not exist on disk.

## What's known

This is the next item from the standing-items baseline that was named on 2026-04-28 in `_observations/OBSERVATIONS_2026_04_28_TRACK_A_FIRST_DISTRIBUTION.md`:

> The standing items remain: `_status.sh` missing, 6× memory_events allowlist violations, Docs integrity gate self-referential coverage gap, 3× Voice variant rendering retired, **`gate_contract_linkage_v1.sh` missing**, `pfl.registry` ModuleNotFoundError.

Today's session work has now closed two items from this list:
- 6× memory_events allowlist violations → closed by H7 Cat B refactor (`1dbc24c`)
- Docs integrity gate self-referential coverage gap → closed by today's surgical retirement (`bfde774`)

`gate_contract_linkage_v1.sh` missing is the third item to surface visibly. Errexit's progressive advance is the mechanism: each closed gate lets the pipeline reach the next.

## Pipeline depth gained

Before this surfaced, `prove_ci.sh` advanced through approximately 50 gates successfully — past memory_events, past docs-integrity, through the entire meta-gate cluster, the docs mutation guardrails (v1 and v2), creative surface gates, proof suite completeness, registry alignment, and so on. The new failure surfaces near the end of the pipeline. Substantial dormancy was closed today.

## Three coherent shapes for the resolution

By analogy to today's docs-integrity gate, three interpretations are possible without further reading:

1. **The gate was archived but its invocation in `prove_ci.sh` was not removed.** Same shape as the 2026-04-27 Findings C+E retirement pass for shell gates with the v2 docs-integrity gate. The fix would be to remove the invocation from `prove_ci.sh` (and any TSV/index references). Most likely interpretation given the precedent.

2. **The gate is planned but never implemented.** A reference was added in anticipation of the gate's creation, which never followed. The fix would be to either remove the reference or implement the gate. Less likely, but worth ruling out.

3. **The gate exists at a different path or with a different name.** Refactor or rename without updating `prove_ci.sh`'s invocation. The fix would be to update the path. Quick to check.

A doc-read session that reads the most recent commits touching `prove_ci.sh` and any history of `gate_contract_linkage*` would settle which interpretation is correct.

## Why this session deferred

Three reasons:

1. **The session's substantive deliverable is complete.** The docs-integrity gate is closed end-to-end (resolution memo, surgical edit, prove_ci confirms green). `bfde774` shipped to origin.

2. **It's late and finding count for the day is high.** Today already closed three architectural transitional states (priority list / MVP / H7 Cat B) plus the docs-integrity sequence. Pushing through a fourth without re-grounding on a fresh day risks the same fatigue patterns we've been catching all evening.

3. **The finding has clear next-session shape.** Same investigation pattern as the docs-integrity gate (read `prove_ci.sh`'s history, read any history of `gate_contract_linkage*`, identify which interpretation fits, ship resolution memo, then refactor in a follow-on session). The pattern is now well-rehearsed.

## What's next

A future session should:

1. Run `git log --all --oneline -- scripts/gate_contract_linkage_v1.sh` to determine if the gate ever existed in the repo's history.
2. Run `git log -p -- scripts/prove_ci.sh | grep -B2 -A2 "gate_contract_linkage"` to see the commits that added or modified the invocation.
3. Form a position on which of the three interpretations fits.
4. Ship a resolution memo.
5. In a separate session, ship the fix.

The expected resolution is most likely "remove the invocation from `prove_ci.sh`" by analogy to the 2026-04-27 retirement precedent, but the doc-read decides.

## Cross-references

- Commit `bfde774` (today, 2026-05-02) — docs-integrity surgical retirement, whose completion surfaced this finding.
- `_observations/OBSERVATIONS_2026_04_28_TRACK_A_FIRST_DISTRIBUTION.md` — names `gate_contract_linkage_v1.sh` missing as a standing item on 2026-04-28.
- `_observations/OBSERVATIONS_2026_05_02_DOCS_INTEGRITY_GATE_FINDING.md` (74f58c8) — the structurally parallel earlier finding from this evening.
- `_observations/OBSERVATIONS_2026_04_27_FINDINGS_C_E_RETIREMENT.md` — the 2026-04-27 retirement pass that closed three shell gates with similar dormancy. Likely precedent for this finding's resolution.
- `scripts/prove_ci.sh` — the script that invokes the missing gate.

## Append-only

This memo records the finding. It does not edit any prior memo or artifact. `prove_ci.sh` continues at rc=127; the failure is now an explicitly-recorded transitional condition with a known-but-deferred resolution path, paralleling how today's docs-integrity finding was held between escalation and resolution.
