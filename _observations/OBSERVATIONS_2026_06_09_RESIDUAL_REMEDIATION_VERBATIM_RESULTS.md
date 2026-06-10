# Residual fabrication remediation (verbatim/copy discipline) - RESULTS

Date: 2026-06-09
Brief: session_brief_residual_fabrication_remediation_CORRECTED.md (`0ad5751`)
Motivated by: E1.4 baseline YELLOW (non-score residual the headline).

## What shipped (three copy-only guardrails, prompt-context layer)

1. **Superlative / all-time** (`league_history_v1.py`): a value may carry an
   all-time/record/season-high framing ONLY if it matches a listed record; never attach a
   record framing to a weekly score.
2. **Series** (`weekly_recap_lifecycle.py` angles header): state a series / head-to-head
   record ONLY by copying a provided "leads the series" line; for any pairing without one -
   including [NO H2H DATA] matchups and non-matchup pairings - do not mention a series
   record; never compute/infer.
3. **FAAB** (`writer_room_context_v1.py`): copy-only allowlist - "any player NOT listed
   received NO FAAB bid"; plus an explicit "no acquisitions on record" absence line when
   FAAB spending exists but no per-player bids do.

Verifier untouched (factual contract preserved). ruff/mypy green; 3 render tests updated to
the new wording.

## Why this lever (the corrected diagnosis)

The E1.4 failing weeks' prompts ALREADY contained the per-player FAAB block (with correct
amounts + "only cite these"), the series do-not-cite signal, and the all-time records. The
residual is PRESENT-BUT-MISREAD (discipline), not a data gap - so enrichment was moot and
retry was insufficient (FAAB is Tier-2 no-retry; SERIES Tier-1 retried but persisted). The
proven lever is the verbatim/copy half of the score fix (copy the string, don't compute).

## Validation (multi-sample: 3 samples x 14 failing weeks = 42 narratives)

Verifier-detected residual hard failures, per sample:

| Category    | BEFORE (E1.4, 1/wk) | AFTER (% of 42 samples) | Effect            |
|-------------|---------------------|--------------------------|-------------------|
| SERIES      | 6 / 14 (43%)        | 4 (9.5%)                 | strongly reduced  |
| SUPERLATIVE | 8 / 14 (57%)        | 14 (33%)                 | reduced ~40%      |
| STREAK      | 4 / 14 (29%)        | 2 (4.8%)                 | reduced           |
| FAAB_CLAIM  | 5 / 14 (36%)        | 18 (43%)                 | UNMOVED (~flat)   |

**Overall residual fabrication: 2.00 -> 0.98 per sample (-51%).**

## Findings

- **Copy-only discipline works where the model can copy a provided string** - SERIES
  collapsed (43% -> 9.5%); SUPERLATIVE improved materially.
- **FAAB is instruction-resistant.** Explicit copy-only + absence did NOT move it (~flat
  within noise). This matches its Tier-2 "synthesizes regardless of feedback" classification.
  FAAB fabrication - especially phantom amounts and pre-FAAB-season phantoms - needs a
  NON-instruction lever: most likely a deterministic post-generation pass that strips/blocks
  any FAAB dollar figure not on the canonical per-player allowlist (a hard gate, not a
  prompt request). Flagged as the follow-up unit.
- Method caveat: numerator is verifier-detected (lower bound); multi-sample reduces but does
  not eliminate stochastic noise. The qualitative result - series fixed, superlative
  improved, FAAB stubborn - is robust.

## Disposition

Net -51% residual reduction; series effectively closed, superlative improved. Committed as a
real improvement. FAAB remains the open residual and is re-scoped to a deterministic
post-generation FAAB gate (instruction-resistant -> enforce, don't ask).
