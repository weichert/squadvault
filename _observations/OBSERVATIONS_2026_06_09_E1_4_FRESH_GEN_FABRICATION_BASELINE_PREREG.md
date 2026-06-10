# E1.4 Fresh-Generation Fabrication Baseline - PRE-REGISTRATION

Engine HEAD at protocol freeze: b4bb6ce (post-E1.5b formatting gate)
Date: 2026-06-09
Type: diagnostic / measurement. Derived DRAFTs only; no fact writes; no approvals.
Status: PRE-REGISTRATION (recorded before any regen; results appended post-run).
Unit: E1.4 (Document of Record). Doubles as Closure cert-6 evidence and as
go/no-go context for the Phase 12 Ask-the-Historian generation path.

## Question

What is the CURRENT live pipeline's fabrication rate, by category, on fresh
generations -- post score-pre-rendering, post FAAB hardening, at the frozen
HEAD above? Headline: the non-score residual (FAAB / series / streak /
superlative). This is Part 3 of the Phase 2 failure-rate attribution runbook
(OBSERVATIONS_2026_06_06_PHASE_2_FAILURE_RATE_ATTRIBUTION.md): the 0.94
stale-corpus rate is NOT the live rate; this measurement produces the live rate.

## D-B adjudications (founder-adopted recommendations, this session)

- D-B1: n = 32 weeks (2 per digital season, 2010-2025).
- D-B2: spend cap = USD 15.00 hard cap, real API cost. Estimated actual spend
  is low single-digit dollars (32 single-pass generations,
  claude-sonnet-4-20250514, max_tokens=1500); the cap is the guardrail, not
  the estimate. Generation stops at the cap; stopped-at-cap is reported
  honestly with the weeks completed.
- D-B3: interpretation bands, pre-registered in section "Criterion" below.

## Week selection (deterministic; no run-time discretion)

Rule: harness-surfaced sentinels fill 2024/2025 (dense-FAAB: 2025 W13,
2024 W13, 2025 W10; sparse: 2024 W2). Every other season takes W5 and W12.
Substitution rule: a quiet week (zero played matchups in the weekly window)
substitutes week+1, then week-1; substitutions are recorded in results.

The 32 weeks, in pre-registered GENERATION ORDER (chronological; a cap-stop
truncates this list from the tail, never selectively):

  2010 W5,  2010 W12, 2011 W5,  2011 W12, 2012 W5,  2012 W12,
  2013 W5,  2013 W12, 2014 W5,  2014 W12, 2015 W5,  2015 W12,
  2016 W5,  2016 W12, 2017 W5,  2017 W12, 2018 W5,  2018 W12,
  2019 W5,  2019 W12, 2020 W5,  2020 W12, 2021 W5,  2021 W12,
  2022 W5,  2022 W12, 2023 W5,  2023 W12, 2024 W2,  2024 W13,
  2025 W10, 2025 W13

Substrate split: 24 weeks pre-2022 (no FAAB substrate; FAAB category not
scored there) / 8 weeks 2022-2025 (FAAB-era overlap window). Series, streak,
and superlative categories are scored across all 32.

## Generation procedure

- Instrument: scripts/recap_artifact_regenerate.py per week, single pass
  (variance measurement is out of scope for this unit), current pipeline at
  the frozen HEAD, captured to prompt_audit as usual.
- DRAFT state only. No approvals, no distribution, no fact/ledger writes.
- DB working copy and any reverify sidecar are local-only, never committed.

## Claim-extraction method

Inherits the claim classes of the matchup-anchors precedent
(OBSERVATIONS_2026_06_07_MATCHUP_ANCHORS_PHASE1_FRESH_GEN_VALIDATION.md):

- MATCH: asserted value equals canonical value (number AND direction/leader).
- SILENT: no claim of that type for that franchise/entity in that draft.
- FABRICATED: a claim of that type diverging from the canonical value, OR
  asserting an entity/transaction that does not exist (e.g. phantom FAAB award).
- AMBIGUOUS: temporally or referentially unresolvable claims; recorded,
  excluded from the rate.

Adaptation from precedent, flagged not slipped: ground truth for 32 weeks is
derived by FROZEN QUERY METHOD rather than inline enumeration -- canonical-DB
queries via the existing detectors and audit_queries/ library, with the
relevant context blocks confirmed present in prompt_text before classifying.
Same independence guarantee as the precedent, achieved by freezing the method
instead of the numbers.

Rate per category = FABRICATED / (MATCH + SILENT + FABRICATED).
Cross-check (not the rate): reverify_prompt_audit.py per-category
hard-failure counts on the fresh sidecar. Detector counts undercount (the
SOFT-only blind spot recorded 2026-06-06); divergence between claim-level
rate and detector counts is itself reported.

## Criterion (pre-registered, falsifiable; D-B3)

Per residual category (FAAB on the 8 FAAB-era weeks; series / streak /
superlative on all 32):

- GREEN: rate <= 2% in EVERY residual category. The generation path stands as
  cert-6 evidence as-is.
- YELLOW: rate > 2% and <= 10% in ANY category. Cert-6 records the measured
  rate with the existing remediation queue (Option 1 streak hardening,
  Option 2 facts-block enrichment) as the named path; Phase 12 gating noted.
- RED: rate > 10% in ANY category. Cert-6 blocked on remediation; Option 2
  escalates to next engine priority.

Either outcome is a real finding; a null is not a pass. Score categories are
measured and reported but are not the headline and do not move the bands.

## Freeze clause

This protocol is frozen at the commit that lands this memo. The execution
session (E1.4, Claude Code / Opus, diagnose-only) verifies the commit
predates all generation timestamps. Results are appended to this memo
post-run. Any deviation from this protocol is recorded AS a deviation in the
results section -- never silently amended here. Actual spend is recorded in
the results against the D-B2 cap.

## Scope / discipline

- Diagnose-only: zero pipeline/verifier/prompt changes in the execution
  session; the committed artifact is this memo and its appended results.
- Doc-only commit path for this memo; ASCII subject; SKIP prove_ci.
