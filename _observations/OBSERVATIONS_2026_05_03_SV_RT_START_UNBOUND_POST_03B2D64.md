# OBSERVATIONS — 2026-05-03 — sv_rt_start unbound variable in prove_ci.sh tail post-03b2d64

**Status:** Finding. Stops for scope decision before next code work.
**Trigger:** Post-commit `prove_ci.sh` rc=1 after `03b2d64` (Option B refactor).
**Predecessor:** `b1c27cc` (Option B finding memo); `03b2d64` (Option B apply commit).
**HEAD at memo-write:** `03b2d64` on local main (not yet pushed at memo-draft time).

---

## Failure surface

Post-commit `prove_ci.sh` flows past every prior stage — including the
export-assemblies stage, which ran three times during the run and was green
each time (main golden path + 2 reruns inside `prove_creative_determinism`)
— and fails at the very tail of the script:

```
scripts/prove_ci.sh: line 332: sv_rt_start: unbound variable
```

Surrounding context (lines 330–332):

```bash
# SV_CI runtime envelope enforcement (best-effort; v1)
sv_rt_end="$(./scripts/py -c 'import time; print(int(time.time()))')"
export SV_CI_RUNTIME_SECONDS="$(( sv_rt_end - sv_rt_start ))"
```

`sv_rt_end` is assigned at line 331. `sv_rt_start` is referenced at line 332
but is not assigned anywhere in `scripts/prove_ci.sh`. Under nounset
semantics, the arithmetic substitution fails on the unbound name and the
script exits non-zero.

Verification:
```
grep -n "sv_rt_start\|sv_rt_end" scripts/prove_ci.sh
```
Returns only lines 331 and 332. There is no assignment anywhere in the file.

## Why now — B is not the cause

Pre-`d50a2a7`: prove_ci bottomed out at the export-assemblies stage with a
`SystemExit("Voice variant rendering (--voice) has been retired...")` from
`recap_week_render.py:140`. The chain never reached line 332.

Post-`d50a2a7`, pre-`03b2d64`: prove_ci bottomed out at the export-assemblies
stage with `RuntimeError: missing canonical Window or Selection fingerprint
line in neutral output` from `extract_blocks_from_neutral`. Same effect — the
chain never reached line 332.

Post-`03b2d64` (Option B applied): export-assemblies stage is green; the
`OK: Golden path proof mode passed.` and `OK: NAC assembly_plain_v1 structure
looks stable.` lines fire three times in a single prove_ci run. The chain
now flows past export-assemblies, through `prove_contract_surface_completeness_v1.sh`,
and into the runtime envelope arithmetic at line 332, where the unbound
`sv_rt_start` surfaces.

This defect has been latent since the runtime-envelope code was added
(best-effort enforcement, v1 per the inline comment). The export-assemblies
dormancy at `0638c9e` (Mar 26 2026) masked it. B's success exposed it.

## Classification

**Not a regression introduced by `03b2d64`.** Latent defect in
`scripts/prove_ci.sh`, previously unreachable. The export-assemblies
dormancy that began at `0638c9e` (~5 weeks) is now closed; the next dormant
defect in the chain is now reachable.

The shape mirrors the Option B brief's outcome 2 prediction:
"rc != 0 with `_status.sh` surfacing — second possibility from the original
Position B brief. Finding memo, push, close." The variable name differs
(`sv_rt_start` not `_status.sh`); the pattern matches.

## Fix shape (out of scope for this finding session)

The runtime envelope intent is "best-effort": measure end-to-end CI runtime
and export it for downstream consumers. The cleanest fix is to assign
`sv_rt_start` early in the script, paired with the existing `sv_rt_end`
assignment at the tail:

```bash
# near the top of scripts/prove_ci.sh (after set -e/-u and basic exports)
sv_rt_start="$(./scripts/py -c 'import time; print(int(time.time()))')"

# existing tail (lines 331-332) stays as-is
sv_rt_end="$(./scripts/py -c 'import time; print(int(time.time()))')"
export SV_CI_RUNTIME_SECONDS="$(( sv_rt_end - sv_rt_start ))"
```

Alternative: make line 332 tolerant — `${sv_rt_start:-${sv_rt_end}}` —
but that defeats the runtime measurement. The pair-assignment fix is the
right shape.

Suggested commit message subject for the future fix:
```
scripts: assign sv_rt_start at prove_ci entry to pair with sv_rt_end (best-effort runtime envelope)
```

One file, one line addition (plus precise placement after the existing
early `export` block), separate commit. Out of scope for this finding.

## Adjacent observation: pytest count delta (pre-existing, not B)

Pytest at the top level (apply script's gate 3/3): 1830 passed, 2 skipped.
Pytest inside prove_ci.sh (three runs visible in the output): 1816 passed,
2 skipped.

Delta of 14. Not investigated; outside this finding's scope. Plausible
causes: prove_ci sets different env vars (`SV_PROVE_TS_UTC`,
`SQUADVAULT_TEST_DB`, etc.) that gate certain test branches; tracked-Tests-only
invocation may differ from default collection. Pre-existing — both before
and after B, prove_ci's pytest stages produced the same count shape.

## Stop signal

No code work proposed in this session. Finding recorded.

Recommended sequence:

1. Commit this memo as a separate one-topic commit.
2. Push: `03b2d64` (Option B) and the memo land on origin together.
3. Address the `sv_rt_start` fix in a future session — one-file, paired-assignment
   placement — and re-run `prove_ci.sh` looking for outcome (a) rc=0 (full
   chain green) or (b) the next surfacing stage.

## Evidence trail (for future-session verification)

1. **HEAD** at memo-write: `03b2d64` (Option B apply commit).
2. **Export-assemblies stage**: ran 3 times in this `prove_ci.sh` run; all
   green; NAC harness reported `OK: NAC assembly_plain_v1 structure looks
   stable.` each time.
3. **prove_ci stage that fired**: tail-stage runtime envelope, line 332,
   after `prove_contract_surface_completeness_v1.sh` and after the final
   `gate_worktree_cleanliness_v1.sh end` would have run.
4. **`sv_rt_start` references**: 0 (only line 332 reads it; nothing writes it).
5. **`sv_rt_end` references**: 1 (line 331 assigns; line 332 reads).
6. **Pytest baseline preserved by Option B**: 1830 passed / 2 skipped at
   top-level gate; 1816 passed / 2 skipped in prove_ci's pytest stages
   (delta is pre-existing, not B-related).
7. **Commit subject ASCII fidelity** (xxd head, first 128 bytes, captured
   in the apply script run):
   ```
   636f 6e73 756d 6572 733a 2062 7569 6c64
   2061 7373 656d 626c 7920 626c 6f63 6b73
   2066 726f 6d20 7374 7275 6374 7572 6564
   2066 6965 6c64 732c 206e 6f74 2070 6172
   7365 6420 7465 7874 2028 4f70 7469 6f6e
   2042 290a
   ```
   Pure ASCII through the subject line; em-dashes appear only in body
   (not surveyed in this xxd window; sourced from a printf-quoted file
   so byte-perfect).

End of memo.
