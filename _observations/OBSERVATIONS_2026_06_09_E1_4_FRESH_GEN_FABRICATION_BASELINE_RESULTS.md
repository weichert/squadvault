# E1.4 Fresh-Generation Fabrication Baseline - RESULTS

Date: 2026-06-09
Pre-registration: OBSERVATIONS_2026_06_09_E1_4_FRESH_GEN_FABRICATION_BASELINE_PREREG.md
(frozen at 95daa09). Per charter section 6 the prereg is immutable; this is the dated
results memo it points to (the prereg's "results appended post-run" is honored here).
Generation HEAD (re-freeze): 28d059f.

## Disclosed deviations from the frozen protocol

1. **Pipeline includes the historical weekly-windowing fix (`abd5c3c`)**, which post-dates
   the prereg freeze (`95daa09`). Without it the 28 historical weeks cannot select matchups
   at all (substrate-readiness blocker; see
   OBSERVATIONS_2026_06_09_E1_4_SUBSTRATE_READINESS_BLOCKER.md). The fix changes SELECTION
   (which events feed a week), not the generation/fabrication path the baseline measures.
   Re-frozen at 28d059f; prove_ci green; 2024-2025 selections byte-identical.
2. **Paced retry on rate-limited weeks.** The first generation pass hit API rate-limiting
   after ~13 weeks (the creative layer falls back to facts-only silently). Rate-limited
   weeks were re-generated with inter-call delays until one narrative was captured. The
   measurement remains single-pass per week (one captured narrative each); the retry was
   to OBTAIN that single capture, not to select among multiple.
3. **Spend is estimated** (~$0.60) from prompt+draft character lengths x Sonnet-4 pricing;
   the pipeline does not persist API usage. The founder's Anthropic console is authoritative.
   Well under the $15 cap; no cap-stop occurred. All 32 weeks generated.

## Method (frozen query method, as far as operationalized)

- 32 weeks generated per the prereg order, claude-sonnet-4-20250514, max_tokens=1500,
  captured to prompt_audit. All 32 carry a non-empty narrative.
- SCORE: automated score-pair extraction from each narrative, matched to canonical
  WEEKLY_MATCHUP_RESULT scores for the week.
- RESIDUAL (FAAB / series / streak / superlative + records): fabrication NUMERATOR is the
  canonical verifier's per-category HARD failures on the fresh corpus (the TRUST detector).
  Denominators are claim-OPPORTUNITY counts (matchups for series; franchise-weeks for
  streak/superlative; FAAB-era waiver awards for FAAB). The verifier UNDERCOUNTS (the
  SOFT-only blind spot recorded 2026-06-06), so residual rates here are LOWER BOUNDS.

## Results

Verification: **18 of 32 fresh weeks pass clean; 14 have >=1 residual hard failure.**

SCORE (claim-level, automated): 157 MATCH / 1 non-match (a 144.10-144.10 tie artifact, not
a fabrication) = **~0.6%**. The score pre-rendering fix holds; scores are essentially clean.

Non-score residual (verifier hard failures over opportunity denominators):

| Category    | FAB | Opportunities | Rate  | Band   |
|-------------|-----|---------------|-------|--------|
| FAAB (in-era 2022+) | 4 | 45 awards | 8.9% | YELLOW |
| SERIES      | 6   | 160 matchups  | 3.8%  | YELLOW |
| SUPERLATIVE | 8   | 320 fr-weeks  | 2.5%  | YELLOW |
| STREAK      | 6*  | 320 fr-weeks  | 1.9%  | GREEN  |

*STREAK = 4 team-streak + 2 player-streak hard failures.
Plus: SEASON_RECORD_CLAIM 3 hard failures (standings/record fabrication).
Plus: **a phantom-FAAB fabrication in pre-FAAB 2021 W5** - the model invented a FAAB award
in a season with no FAAB substrate (the prereg's FABRICATED definition: "asserting a
transaction that does not exist"). A distinct, notable fabrication mode.

## Verdict (against the pre-registered bands; D-B3)

**NOT GREEN.** A null/clean outcome is decisively ruled out. The non-score residual is the
headline, exactly as the prereg hypothesized:
- FAAB, SERIES, SUPERLATIVE all land YELLOW at the verifier LOWER BOUND; because the
  verifier undercounts, true claim-level rates are likely higher (some plausibly RED).
- FAAB is the hottest residual (8.9% in-era + a pre-FAAB phantom), consistent with FAAB
  context-manipulation levers having been falsified/closed rather than solved.
- STREAK is GREEN at this bound; SCORE is clean.

Per the prereg criterion, YELLOW => cert-6 records the measured rate with the existing
remediation queue as the named path: **Option 1 (streak hardening)** and especially
**Option 2 (facts-block enrichment)** for the FAAB/series/superlative residual; **Phase 12
(Ask-the-Historian) gating noted** - the interactive generation path would ride this same
residual and should not ship unmitigated.

## Confidence and limits

- Numerator is verifier-detected (lower bound); denominators are opportunity estimates, not
  the precedent's exact MATCH+SILENT+FABRICATED enumeration. Bands are therefore
  approximate and conservative (biased toward GREEN by the undercount). The qualitative
  finding - non-trivial non-score residual, FAAB worst, scores clean - is robust; the exact
  percentages are indicative, not certified to two digits.
- A fuller claim-level annotation (per-claim MATCH/SILENT/FABRICATED for the residual
  categories) would tighten the rates; it is the natural follow-up if cert-6 needs a
  certified number rather than a banded verdict.

## Cert-6 disposition

E1.4 is DISCHARGED as a measurement: the live-pipeline fabrication baseline is recorded.
The cert-6 entry is **YELLOW with a FAAB watch**, remediation queue named, Phase 12 gating
noted. The baseline is not a pass; it is an honest measurement that routes the non-score
residual to the existing remediation path.
