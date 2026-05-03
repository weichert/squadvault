# OBSERVATIONS_2026_05_02 — pfl.registry ModuleNotFoundError (deferred)

**Predecessor:** `4ceb28b` (today's gate_contract_linkage retirement).

**Stated purpose:** record a finding surfaced when the gate_contract_linkage retirement (commit `4ceb28b`) closed the missing-gate failure, allowing `prove_ci.sh`'s errexit to advance further than ever before today, surfacing the next dormancy issue down the pipeline. Defer the resolution to a separate session and document the finding while context is fresh.

This memo follows the same shape as today's prior finding memos (`74f58c8` for docs-integrity, `d9c93e6` for gate_contract_linkage): surface the finding, name what's known, defer to a separate session.

## How the finding surfaced

The gate_contract_linkage retirement (commit `4ceb28b`) closed the missing-gate `rc=127` failure. Running `prove_ci.sh` afterward returned `rc=1` from a different point much further down the pipeline:

```
Traceback (most recent call last):
  File "<stdin>", line 3, in <module>
ModuleNotFoundError: No module named 'pfl.registry'
prove_ci rc=1
```

`rc=1` from a Python `ModuleNotFoundError`, not the bash `command not found` patterns we've been clearing. The traceback's `File "<stdin>", line 3` indicates the Python is being executed from stdin — i.e., a heredoc piped into a Python interpreter from inside `prove_ci.sh` (or a script `prove_ci.sh` invokes).

## What's known

This is the next item from the standing-items baseline that was named on 2026-04-28 in `_observations/OBSERVATIONS_2026_04_28_TRACK_A_FIRST_DISTRIBUTION.md`:

> The standing items remain: `_status.sh` missing, 6× memory_events allowlist violations, Docs integrity gate self-referential coverage gap, 3× Voice variant rendering retired, `gate_contract_linkage_v1.sh` missing, **`pfl.registry` ModuleNotFoundError**.

Today's session work has now closed three items from this list:
- 6× memory_events allowlist violations → closed by H7 Cat B refactor (`1dbc24c`)
- Docs integrity gate self-referential coverage gap → closed by docs-integrity surgical retirement (`bfde774`)
- `gate_contract_linkage_v1.sh` missing → closed by gate_contract_linkage retirement (`4ceb28b`)

`pfl.registry` ModuleNotFoundError is the fourth item to surface visibly. Errexit's progressive advance is the mechanism: each closed gate lets the pipeline reach the next.

## Pipeline depth gained

Before this surfaced, `prove_ci.sh` advanced through a substantially-deeper sequence than ever before today — all the meta gates, all the docs-integrity / mutation guardrails, the entire creative surface gates, proof suite completeness, registry alignment, and into pytest-driven runs. The new failure surfaces near the end of the pipeline (after `Repo-root allowlist gate ... 2 passed in 0.43s`).

The depth of progress through 2026-05-02 is the substantive measure of how much dormancy four sessions today closed.

## Three coherent shapes for the resolution

By analogy to today's prior findings, three interpretations are possible without further reading:

1. **The `pfl.registry` module exists somewhere but isn't importable in this environment.** Could be a `PYTHONPATH` issue, missing `__init__.py`, or the module's parent directory not being installed. The fix would be to make the import work — either by configuring PYTHONPATH (the `scripts/py` shim handles this for some scripts; perhaps not for the heredoc invocation), by adding the missing `__init__.py`, or by installing whatever package provides `pfl`.

2. **The `pfl.registry` module never existed and the import is dormant residue.** Some prior code referenced a planned `pfl` namespace package (perhaps short for "PFL Buddies registry" or similar) that was never implemented. The fix would be to remove the import and whatever code uses it.

3. **The module was deleted in a sweep cleanup (analogous to `2dfb96e`)**. A `pfl.registry` module existed at some point, was deleted, and the importing code was missed. The fix shape parallels today's prior retirements: remove the importing code or update it to use what survived.

A doc-read session that runs `git log --all -- "*pfl/*" "*pfl.py"`, `grep -rn "from pfl" .`, and `grep -rn "import pfl" .` would settle which interpretation is correct.

## Why this session deferred

Three reasons:

1. **The session's substantive deliverable is complete.** The gate_contract_linkage retirement is shipped (`4ceb28b`) — the architectural sequence that began with `d9c93e6` (finding) and `328d9ac` (resolution) is closed end-to-end at the code level. `prove_ci.sh` advances substantially further than this morning.

2. **The same investigation shape works.** Today has run four iterations of the finding → resolution → refactor pattern: H7 Cat B (memory_events), docs-integrity, gate_contract_linkage are all fully closed; the pattern is well-rehearsed for whoever picks this up next.

3. **The error shape — Python `ModuleNotFoundError` — is mechanically different from the prior bash-level dormancy.** It's worth a fresh session that starts with `grep -rn` for `pfl` references rather than rolling immediately from one closure into the next. Different error class, different investigation entry point.

## What's next

A future session should:

1. Run `grep -rn "pfl\." scripts/ src/ Tests/ 2>/dev/null` to locate all references to the `pfl` namespace.
2. Run `git log --all --oneline -- "*pfl*"` to see the namespace's repo history.
3. Identify whether `prove_ci.sh` (or a script it invokes) has the heredoc Python import that's failing.
4. Form a position on which of the three interpretations fits.
5. Ship a resolution memo.
6. In a separate session, ship the fix.

The expected resolution is most likely Interpretation 2 or 3 — `pfl.registry` is dormant residue rather than a real module that's just unimportable. But the investigation decides.

## A pattern note on today's session pattern

Four iterations of the finding → resolution → refactor pattern shipped today:

1. **H7 Cat B sequence** — `1cd9455` (escalation) → `b8ef4d0` (resolution) → `5c207d3` (gate comment) → `1dbc24c` (refactor)
2. **Docs-integrity sequence** — `74f58c8` (finding) → `b3885d0` (resolution) → `bfde774` (refactor)
3. **gate_contract_linkage sequence** — `d9c93e6` (finding) → `328d9ac` (resolution) → `4ceb28b` (refactor)
4. **(This memo)** — pfl.registry ModuleNotFoundError, finding stage only

Three sequences fully closed, one stage shipped on the fourth. The pattern is now reproducible and well-evidenced. Future-Steve picking up the `pfl.registry` resolution can follow the same investigation pattern, the same memo shapes, and the same script-driven refactor scaffolding.

## Cross-references

- Commit `4ceb28b` (today, 2026-05-02) — gate_contract_linkage retirement, whose completion surfaced this finding.
- `_observations/OBSERVATIONS_2026_04_28_TRACK_A_FIRST_DISTRIBUTION.md` — names `pfl.registry` ModuleNotFoundError as a standing item on 2026-04-28.
- `_observations/OBSERVATIONS_2026_05_02_GATE_CONTRACT_LINKAGE_MISSING.md` (`d9c93e6`) — the structurally parallel earlier finding from this evening.
- `_observations/OBSERVATIONS_2026_05_02_GATE_CONTRACT_LINKAGE_RESOLUTION.md` (`328d9ac`) — the resolution memo that closed the prior finding; serves as the precedent shape for this finding's eventual resolution.
- `scripts/prove_ci.sh` — the script whose execution surfaces the failure (likely via a heredoc Python invocation, location to be identified in the resolution session).

## Append-only

This memo records the finding. It does not edit any prior memo or artifact. `prove_ci.sh` continues at rc=1; the failure is now an explicitly-recorded transitional condition with a known-but-deferred resolution path, paralleling today's three earlier finding-stage memos.
