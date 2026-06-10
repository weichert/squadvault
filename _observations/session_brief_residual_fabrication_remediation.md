# SESSION BRIEF - Residual fabrication remediation (Option 2+, post-E1.4)

**Status: SCOPED + D-R1 ADJUDICATED (Option A - one unit, both levers; founder 2026-06-09).
Executing.**
**Type:** engine / pipeline (prompt + facts-block; NOT diagnose-only).
**Authored against HEAD:** `2d404f7`.
**Motivated by:** E1.4 baseline (YELLOW; non-score residual the headline) -
`OBSERVATIONS_2026_06_09_E1_4_..._BASELINE_RESULTS.md`. Extends Option 2 from the
Phase-2 attribution memo (`OBSERVATIONS_2026_06_06_PHASE_2_FAILURE_RATE_ATTRIBUTION.md`).

## Finding that resolves the Phase-2 OPEN gate (firm prompt read, LIVE corpus)

The Phase-2 memo flagged an OPEN gate: confirm residual fabrications are absence-driven
(enrichment) vs present-but-misread (discipline), by reading prompt_text against evidence.
The E1.4 fresh corpus is that data. Reading the 29 residual hard failures' prompt blocks:

- **FAAB - ABSENCE-driven (enrichment is correct).** The prompt carries franchise FAAB
  TOTALS ("Stu's Crew: $79 spent") but NO per-player bids. The model invents per-player
  amounts ($8 Kyren Williams vs actual $21.22) and phantom awards (no waiver record).
- **SERIES - PRESENT-BUT-MISREAD (discipline, NOT a data gap).** The prompt ALREADY emits
  `[NO H2H DATA] ... do not cite a series record for this matchup` for absent pairings and
  H2H context for present ones. The model fabricates series records anyway (e.g. "5-0" for
  pairings with explicit do-not-cite). Fork-b absence signal is ALREADY implemented; the
  failure is adherence.
- **SUPERLATIVE (all-time/record) - PRESENT-BUT-MISREAD.** The prompt has a full
  `LEAGUE HISTORY (all-time records ...)` block. The model still asserts false "all-time
  record" framings on real in-week scores. Data present; misapplied.
- **STREAK - mixed**; Option 1 (trailing-count hardening) is the named lever, separate.

**Conclusion: "facts-block enrichment" alone is necessary but NOT sufficient.** It fixes
FAAB. Series/superlative are a VERBATIM/DISCIPLINE problem (the data is there; the model
infers/misapplies). The proven score-pre-rendering playbook had TWO parts: (1) pre-render
the canonical string, (2) instruct "copy verbatim, do not compute." Residual remediation
needs BOTH parts, applied per category - not just part (1).

## D-R1 - ADJUDICATED: Option A (one unit, both levers). Founder 2026-06-09.

The fix is two distinct levers; pick how to sequence:
- **A (RECOMMENDED): one unit, both levers.** (i) FAAB enrichment - pre-render a per-player
  FAAB-awards list WITH EXPLICIT ABSENCE; (ii) Series + all-time pre-rendering - convert the
  H2H / all-time facts from "context to reason over" into COPY-VERBATIM strings with a hard
  "cite only the provided string; never compute or infer a record" instruction. Streak
  (Option 1) folded in or noted.
- **B: split.** Ship FAAB enrichment first (clean absence-driven win), spec series/all-time
  verbatim-discipline as a second unit (it is prompt-instruction + pre-render work with its
  own validation).

## Scope of work (engine; prompt + facts-block)

- Locate the context builders: `weekly_recap_lifecycle._derive_prompt_context` and the
  block emitters (LEAGUE HISTORY, WRITER ROOM / FAAB spending, NOTABLE/series). Add:
  - **FAAB:** per-player awards block for the week, including an explicit "no FAAB awards
    this week" / per-relevant-player "no bid" absence line.
  - **Series / all-time:** emit the canonical H2H and all-time records as COPY-VERBATIM
    strings (the score-prerender pattern), with the do-not-compute instruction.
- Keep changes at the prompt/context layer; do NOT touch the verifier's factual contract.

## Acceptance criteria (binary)

1. Targeted before/after on the E1.4 failing weeks: residual hard failures (FAAB / series /
   superlative) drop materially on re-generation (cheap - ~14 weeks, < $0.30).
2. The facts-block changes are deterministic; golden-path / determinism suite green;
   2024-2025 selection unchanged (this is prompt-layer, not selection).
3. ruff / mypy / full suite green; prove_ci clean (3.11). Observation memo + STATE.md.
4. Optionally: a fuller E1.4-style re-measure to band the post-fix residual (founder elects;
   ~$0.60).

## OUT OF SCOPE

- The verifier (factual contract untouched).
- Score category (already clean ~0.6%).
- A full re-run of E1.4 as acceptance (the targeted before/after on failing weeks suffices
  for this unit; a full re-measure is a separate founder election).

## Note

This brief REVISES the Phase-2 "overwhelmingly absence-driven" read using live-pipeline
evidence: series/superlative are present-but-misread (discipline), not data gaps. The
remediation therefore carries a verbatim/instruction lever, not enrichment alone.
