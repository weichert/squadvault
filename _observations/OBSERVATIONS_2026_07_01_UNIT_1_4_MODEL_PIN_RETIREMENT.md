# Observation - 2026-07-01 - Unit A7 (1.4) blocked by retired model pin; production pin updated

**Session type:** EXECUTE (Claude Code). Started as Unit A7 (fresh-generation failure-rate
baseline, brief `_observations/session_brief_unit_1_4_fresh_generation_baseline.md`).
Halted at the Step 1 smoke by a blocking finding; pivoted (founder-approved) to a small
production-config change. **The baseline itself was NOT run and remains open** - it must
be re-pre-registered and run against the corrected config in a fresh session.

**Repo:** engine `weichert/squadvault`. **HEAD at session start:** `c344c58` (verified;
identity file present; clean tree). All Amendment-Log config facts re-verified against
source at that HEAD (model, retry cap 3, temps [None,0.5,0.3], no-retry cats
{FAAB_CLAIM, NUMERIC_UNANCHORED}, verifier 14-category enum). Corrected one brief path:
the verifier is `src/squadvault/core/recaps/verification/recap_verifier_v1.py` (brief
cited `src/squadvault/recaps/recap_verifier_v1.py`); its enum is the 14 categories as listed.

## The blocking finding

The pinned production generation model `claude-sonnet-4-20250514` reached end-of-life
2026-06-15 and now returns **HTTP 404 not_found_error** from the API. `creative_layer_v1`
catches any API error and **silently degrades to deterministic facts-only output**. The
Step 1 smoke (throwaway cell 2024 wk8, scratch DB) reproduced this:

```
creative_layer_v1: API call failed (404 not_found_error: model: claude-sonnet-4-20250514)
  - falling back to deterministic facts-only output.
```

Consequence: a baseline run against this config would exercise ONLY the facts-only
fallback path - no LLM generation, `verification_attempts=1`, zero prompt_audit rows -
which does not answer the baseline question. This is exactly the silent-degradation
hazard the brief's smoke step exists to catch (there for a dead key; here a dead model).
Confirmed removal, not transient: same API key reaches current models; only the pinned
snapshot 404s.

## Founder decision (2026-07-01)

Stop the baseline as specified; do not run 24-36 generations against the retired model;
do not silently swap models inside the measurement. Make a small explicit production-config
update replacing the retired pin with the current approved successor; treat it as a config
change, not a measurement tweak; smoke-test it; then rerun the baseline against the updated
config in a separate session.

## Successor selection - a second incompatibility

The proposed `claude-sonnet-5` is available on the key but **rejects the `temperature`
parameter (HTTP 400: "temperature is deprecated for this model")**. `creative_layer_v1`
sends `temperature`, and the tier-aware retry loop steps it `[None, 0.5, 0.3]` - the exact
mechanism the baseline's R2 outcome distribution measures. So Sonnet 5 is a *migration*
(remove temperature control + redesign/re-verify the retry strategy), not a pin swap, and
it would change what the baseline measures. Compatibility probe on the key:

| model | `temperature=0.8` | dated snapshot |
|---|---|---|
| claude-sonnet-5 | 400 rejected | no (alias) |
| claude-opus-4-8 | 400 rejected | no |
| claude-sonnet-4-6 | OK | no (alias) |
| **claude-sonnet-4-5-20250929** | **OK** | **yes** |

**Founder ratified `claude-sonnet-4-5-20250929`**: temperature-compatible (preserves the
retry decay unchanged) and a dated snapshot (strict reproducibility, charter section 8).
The response-shape is already handled - `_extract_text_from_response` iterates all content
blocks and takes `.text` where present, so thinking-block responses are consumed correctly.

## The change

`src/squadvault/ai/creative_layer_v1.py` line 25: `_MODEL` `claude-sonnet-4-20250514` ->
`claude-sonnet-4-5-20250929`, with a comment recording the retirement, the temperature
rationale, and the dated-pin choice. One line + comment; no other code touched.

## Confirming smoke (founder step 6) - all green

Model `claude-sonnet-4-5-20250929`, cell 2024 wk8, fresh scratch copy,
`SQUADVAULT_PROMPT_AUDIT=1`:
- **LLM call occurs:** `verification_attempts=2` - generated on attempt 1, verification
  failed (16 checks), retried (temperature-decay), attempt 2 hit a Tier-2 `FAAB_CLAIM` and
  correctly short-circuited to facts-only. Real generation + verifier + retry, not fallback.
- **No model-failure fallback:** the only fallback is the legitimate Tier-2 short-circuit
  (an R2 outcome class), not an API failure.
- **prompt_audit rows written:** delta = 2 (one per attempt), each with `checks_run` +
  `hard_failures` by category - the R1 data source, populated.
- **prod DB hash unchanged:** `effb00e54fce5c38...` before and after.

Standard trio green after the change: ruff clean; mypy clean (160 files); pytest
2369 passed, 3 skipped (the retired-model DeprecationWarning is gone).

## State / provenance

- Prod DB `.local_squadvault.sqlite` untouched: sha256
  `effb00e54fce5c3860423a08338b8711bc96229172452888c97823bc8c5af36b`.
- Measurement ran only against `/tmp` scratch copies (deleted). Nothing published.
- Engine env: venv `/tmp/unit14_venv`; anthropic 0.115.1.

## Open follow-ups

1. **Unit A7 baseline still owed** - re-pre-register and run against the corrected config
   (Sonnet 4.5) in a fresh session; the calendar reason (before Week 1 ~09-08) still holds.
   The mechanism now demonstrably works (the confirming smoke shows attempts, retries,
   Tier-2 short-circuit, and per-attempt prompt_audit capture).
2. **Document of Record staleness (founder / DECIDE):**
   `docs/SquadVault_Product_Document_of_Record_v2_1.md:58` records the pin as
   `claude-sonnet-4-20250514`. That is a canonical (Tier-0) doc - not edited in this
   EXECUTE change; it needs a founder/DECIDE update to reflect the new pin.
3. **Host disk pressure:** the machine volume was at ~100% (about 1.6 GB free) during the
   session; the 60 MB scratch copy fit, but the eventual 24-36 baseline run needs headroom
   for scratch writes. Free space before that run.
4. `scripts/_archive/delivery/apply_creative_layer_calibration_v1.py:75` also names the old
   model, but it is an archived delivery script - intentionally left untouched.
