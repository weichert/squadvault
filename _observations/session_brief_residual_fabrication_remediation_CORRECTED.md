# SESSION BRIEF (CORRECTED) - Residual fabrication remediation: verbatim/copy discipline

**Supersedes the premise of** `session_brief_residual_fabrication_remediation.md` (`0db1889`).
That brief scoped "facts-block enrichment (Option 2)"; deeper verification during execution
FALSIFIED its central premise. Per charter section 6 this is a new dated brief, not an edit.
**Status: SCOPED (corrected); founder approved the pivot 2026-06-09. Implementing.**
**Type:** engine / prompt-context (NOT diagnose-only). HEAD `0db1889`.

## The correction (verify-first catch during execution)

The enrichment premise was that the residual fabrications are absence-driven (data missing
from the prompt). Reading the actual prompts of the E1.4 failing weeks shows the opposite:

- **FAAB:** all 5 fabrications had the per-player "Individual FAAB acquisitions" block
  PRESENT, with the explicit instruction "ONLY these amounts may be cited - do not invent
  others." 4 of 5 had the specific player listed with the CORRECT bid (Kyren Williams:
  prompt $21.22, model wrote $8). The data + instruction were there; the model ignored them.
- **SERIES:** the prompt already emits `[NO H2H DATA] ... do not cite a series record` for
  absent pairings and the verified H2H for present ones. The model fabricates anyway.
- **SUPERLATIVE (all-time):** the prompt has a full `LEAGUE HISTORY (all-time records)`
  block. The model asserts false all-time-record framings anyway.

**Conclusion: the residual is PRESENT-BUT-MISREAD (generation discipline), not a data gap.
Enrichment is moot - the data and the "do not invent" instructions are already present.**

## Why retry alone won't fix it (evidence)

The lifecycle has a tier-aware verify-retry loop (`_MAX_VERIFICATION_RETRIES=3`):
- FAAB_CLAIM is Tier-2 NO-RETRY (the code comment: "fabricated amounts recur regardless
  of feedback"). So FAAB failures are never regenerated. (Its comment's premise - "model
  synthesizes from cumulative totals" - is now stale: per-player bids ARE supplied, and it
  still fabricates.)
- SERIES is Tier-1 RETRY-eligible - yet series fabrications PERSISTED through the E1.4 run's
  retries (the captured draft is the final attempt). Retry with feedback did not resolve it.

So neither enrichment nor naive retry is the lever.

## The lever: verbatim/copy pre-rendering (the proven score-fix mechanism)

The score fix worked (SCORE_VERBATIM 124/124 -> 3/39) NOT by supplying scores (always
present) but by pre-rendering the canonical score as a COPY-STRING and instructing
"copy verbatim, do not compute." That is a DISCIPLINE lever. Extend it to the residual:

- **Series:** pre-render the verified H2H as a copy-string ("All-time series: X leads Y-Z");
  for absent pairings keep the explicit do-not-cite; instruction: cite ONLY the provided
  string, never compute or infer a series record.
- **All-time / superlative:** pre-render the actual all-time/season-high records as
  copy-strings; instruction: an "all-time"/"record"/"season-high" claim may ONLY be made by
  copying a provided record string; otherwise omit the superlative framing.
- **FAAB:** the per-player block already exists; tighten its framing to copy-only and add an
  explicit per-relevant-player "no FAAB bid this week" absence line so phantom awards have a
  "none" to land on rather than a void. Re-examine the FAAB Tier-2 no-retry classification.

## Scope of work

Context builders: `narrative_angles_v1.py` (series), `league_history_v1.py` (all-time),
`writer_room_context_v1.py` (FAAB). Convert reason-over context to copy-verbatim strings +
hard copy-only instruction. Optionally revisit the retry tiers given verbatim strings change
the retry calculus. Prompt-layer only; verifier untouched.

## Acceptance criteria (binary)

1. Targeted before/after on the E1.4 failing weeks (~14, < $0.30 re-gen): residual hard
   failures (series / superlative / FAAB) drop materially.
2. Deterministic; golden-path / determinism suite green; selection unchanged.
3. ruff / mypy / full suite green; prove_ci clean (3.11). Observation memo + STATE.md.

## OUT OF SCOPE

Verifier contract; score category (clean); a full E1.4 re-measure (separate founder election).

## Honest note

This corrects a misdiagnosis in my own prior brief (incomplete prompt read missed the
per-player FAAB block). The execution-time verification caught it before any wrong code
shipped. Recorded plainly per the cert-5 discipline: catching drift is the process working.
