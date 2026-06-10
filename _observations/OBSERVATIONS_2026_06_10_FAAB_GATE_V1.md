# OBSERVATIONS 2026-06-10 -- Deterministic post-generation FAAB gate (v1)

**Session type:** Execution (Claude Code, Opus). Engine HEAD at start: `644e78c`.
Discharges the deferred "FAAB residual gate" unit registered in STATE.md.
No formal brief existed; scope verified against STATE.md + the remediation memo
(`OBSERVATIONS_2026_06_09_RESIDUAL_REMEDIATION_VERBATIM_RESULTS.md`) per charter
section 7 (verify against the canonical record before executing).

## Why this unit

The residual-remediation pass proved FAAB fabrication is instruction-resistant:
copy-only prompt discipline moved SERIES (43% -> 9.5%) and SUPERLATIVE (-40%) but
left FAAB_CLAIM flat (~43% of samples). Two prior pre-registered context-block
experiments (matchup anchors ADD; per-player suppression REMOVE) both INCREASED
fabrication. The standing conclusion: FAAB is not movable by prompt-context tweaks;
the proven lever is enforcement, not instruction -- "enforce, don't ask."

## Founder decisions (D-G)

- **D-G1 = Hybrid:** on an out-of-allowlist FAAB figure, STRIP the carrying
  sentence(s) when removal leaves substantive prose and no violation remains;
  else BLOCK to facts-only. Silence over speculation either way.
- **D-G2 = Standalone backstop (defense in depth):** runs ALONGSIDE
  `verify_faab_claims`, does NOT import the verifier, leaves the verifier's
  factual contract frozen. Mirrors the `presentation_lint_v1` standalone precedent.

## What shipped

- `src/squadvault/core/recaps/render/faab_gate_v1.py` (new): a pure, DB-free core
  `apply_faab_gate(narrative, *, allowlist)` plus a single DB-touching loader
  `load_faab_allowlist(db, league, season)`. The detection contract (dollar
  pattern, FAAB-keyword window, draft-context suppression, +/-1.0 tolerance,
  nearest-player resolution) is mirrored verbatim from verifier Category 8 so the
  two never disagree on what is an out-of-allowlist claim. Phantom detection needs
  the FULL player universe (not just FAAB-acquired players), so the allowlist
  carries both the name->pid map and the pid->amounts map.
- `weekly_recap_lifecycle.py`: a final deterministic pass after the verification
  retry loop (`SV_FAAB_GATE_V1`). Operates only on the narrative between the
  SHAREABLE markers; the L2 byte-identity-protected facts block is untouched.
  stripped -> reassemble with the survivor; blocked -> facts-only note in the
  existing style. Fails OPEN on any error (the verifier stays the primary floor;
  a backstop fault must not degrade a verifier-approved narrative).
- `Tests/test_faab_gate_v1.py` (new): 13 tests -- clean/strip/block/determinism on
  the pure core (no DB) plus a schema-backed `load_faab_allowlist` exercise.

## Concrete value over the existing verifier path

The verifier already HARD-fails caught FAAB and the lifecycle falls back to
facts-only -- but on a verifier EXCEPTION the lifecycle KEEPS the unverified draft
(recap_verifier try/except: "keep this draft, don't retry"). The deterministic
gate re-checks FAAB independent of that plumbing, closing that hole. It also adds
the strip mechanism so a verifier-missed violation costs only its sentence, not
the whole narrative. Detection is identical to Category 8 by design, so it
introduces zero new false positives (anything the verifier passes, the gate agrees).

## Validation

- `Tests/test_faab_gate_v1.py`: 13 passed.
- Regression: `test_recap_verifier_v1.py` + `test_presentation_lint_v1.py` 302
  passed; full collectable suite 2176 passed. The only failures (ingest-fingerprint
  + dotenv collection errors) are pre-existing and environmental -- confirmed
  identical on a stashed clean tree.
- ruff + mypy: clean on both changed source files and the new test.

## Disposition

FAAB residual gate DISCHARGED. The "facts-only floor on FAAB-dense weeks" stance is
unchanged for genuinely uncleanly-removable claims (those block, as before); the new
capability is sentence-level rescue when a single clause is the only offender, plus a
deterministic guarantee on the verifier-exception path. No prompt-context lever was
touched (the contraindicated path stays closed).
