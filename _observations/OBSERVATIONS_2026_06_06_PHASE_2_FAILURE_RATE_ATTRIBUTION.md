# OBSERVATIONS 2026-06-06 -- Phase 2 Failure-Rate Attribution Findings

<!--
  Rename to OBSERVATIONS_2026_06_06_PHASE_2_FAILURE_RATE_ATTRIBUTION.md,
  place in _observations/, commit doc-only, SKIP prove_ci. ASCII subject.
  Two items still open (marked OPEN below): prompt_text read for the firm
  option-2 call, and an optional captured_at confirmation of the stale-corpus
  framing.
-->

## Provenance
- Date: 2026-06-06
- Engine HEAD / verifier tag: 151d41b (also reverified as head-vs-april)
- Baseline tag: april-baseline (worktree at 10e12a8, 2026-04-20)
- DB: ./.local_squadvault.sqlite   League: 70985
- Continues the Phase 2 failure-rate attribution runbook; closes the open leg
  of OBSERVATIONS_2026_06_06_VERIFIER_CONSISTENCY_AND_FAILURE_RATE.md.
- Scope: diagnose-only. No verifier rewrite, no pipeline/model change. The only
  writes were derived prompt_audit_reverify sidecar rows (tags 151d41b,
  april-baseline, head-vs-april). Facts immutable and append-only throughout.

## Part 0 -- Settled from static evidence (re-verified this pass)
- DRIFT ruled out. creative_layer_v1 _MODEL = "claude-sonnet-4-20250514", last
  touched ddf2453 (2026-03-24), stable through HEAD.
- TIGHTENING confirmed dominant (see Part 1 baseline table).
- Category map: 19 categories; 16 HARD-capable, 3 SOFT-only (BANNED_PHRASE,
  NUMERIC_UNANCHORED, SPECULATION). DRAFT_AUCTION_DOLLAR mixed-severity.

## Corpus summary (headline rate, with n)
- Reverified attempts: 163 over 34 distinct weeks.
- Fails under current verifier: 153 -> fraction 153/163 = 0.94.
- Originally passed: 72. pass->fail universe: 64. still-pass: 8. fail->pass: 2.

CRITICAL FRAMING: 0.94 is the STALE-CORPUS rate, not the current pipeline's
quality. These are frozen captured drafts; reverify regenerates nothing.
Confirmed by capture date: 124 of 163 rows (76%) were captured before the
2026-05-03 score pre-rendering fix; only 39 are post-fix. The pre-fix drafts
carry the old fabricated score strings, which is what produces the 564
SCORE_VERBATIM hits (Part 1 table). The score pre-rendering fix is confirmed
WORKING in the live pipeline: SCORE_VERBATIM appears in 124/124 pre-fix rows but
only 3/39 post-fix. Post-fix rows that still fail (29/39) do so almost entirely
on NON-score categories (FAAB / series / streak / superlative) -- the residual
live concern is non-score fabrication. This pass measures how far the verifier
tightened against archival drafts -- NOT how often the live pipeline fabricates
today. The current-pipeline rate requires Part 3 fresh generations and is
explicitly out of scope here.

CAVEAT on the post-fix 39: they are a mix of organic recaps and deliberately-
constructed fabrication-probe rows (single-claim test inputs designed to be
caught, e.g. "$20 FAAB attributed to Trey Mcbride"). Their aggregate fail rate
is therefore NOT a clean live-pipeline signal -- which is exactly why Part 3
(fresh, controlled generations) is the right instrument for the current rate.

## Part 1 -- Attribution

### Q1 row-level pass->fail by category (first cut; superseded by the baseline table)
| category | rows_now_failing | class |
|---|---|---|
| SCORE_VERBATIM | 59 | POST-April (2fe75b2 05-03) |
| FAAB_CLAIM | 29 | PRE-April (5b119b6 04-15) |
| STREAK | 13 | PRE-April (56bb6b4 04-01) |
| DRAFT_AUCTION_DOLLAR | 9 | POST-April (84564a4 06-05) |
| SERIES | 5 | PRE-April (cc54885 04-01) |
| SEASON_RECORD_CLAIM | 4 | POST-April (0350304 05-17) |
| RECORD_CLAIM_ANCHORING | 3 | POST-April (c435864 05-04) |
| PLAYER_FRANCHISE | 2 | PRE-April (a91fc72 04-15) |
| CHAMPIONSHIP_CLAIM | 2 | POST-April (0350304 05-17) |

The harness's row-level option-3 verdict read "REGRESSION SIGNAL: FAAB_CLAIM,
STREAK, SERIES, PLAYER_FRANCHISE." This is the co-occurrence false positive the
runbook warned about: pre-April categories appear because they ride in rows that
flipped on the NEW SCORE_VERBATIM check. The category-NEW baseline table below
is the authoritative cut and overrides it.

### Category-NEW merge gate (head-vs-april vs april-baseline) -- AUTHORITATIVE
| category | baseline | current | delta | status |
|---|---|---|---|---|
| SCORE_VERBATIM | 0 | 564 | +564 | NEW |
| RECORD_CLAIM_ANCHORING | 0 | 13 | +13 | NEW |
| DRAFT_AUCTION_DOLLAR | 0 | 12 | +12 | NEW |
| CHAMPIONSHIP_CLAIM | 0 | 8 | +8 | NEW |
| SEASON_RECORD_CLAIM | 0 | 8 | +8 | NEW |
| PLAYER_AVG_CLAIM | 0 | 1 | +1 | NEW |
| FAAB_CLAIM | 3 | 82 | +79 | +drift |
| SUPERLATIVE | 15 | 13 | -2 | -drift |
| STREAK | 45 | 45 | 0 | unchanged |
| SERIES | 33 | 33 | 0 | unchanged |
| PLAYER_FRANCHISE | 8 | 8 | 0 | unchanged |
| PLAYER_SCORE | 1 | 1 | 0 | unchanged |

Reading:
- 6 NEW categories are all post-04-20 additions -> intended tightening. The
  script's "REGRESSION: 6 NEW" is its CI wording; here NEW == the tightening set.
- STREAK / SERIES / PLAYER_FRANCHISE / PLAYER_SCORE: ZERO delta. No pre-April
  check changed verdict between April and HEAD. No regression.
- FAAB_CLAIM 3 -> 82 (+79): traces to deliberate post-baseline hardening
  (a7b3829 extend FAAB keyword list; b5258d9 FAAB fabrication prevention). The
  evidence column confirms the new hits are TRUE fabrications ("No
  WAIVER_BID_AWARDED record found for <player>"), i.e. the expanded check
  catching real invention. Intended tightening, not drift.
- SUPERLATIVE 15 -> 13 (-2): a small loosening (fewer flags). Benign.

### Option 3 verdict (model pinning): DROPPED
Airtight on two independent grounds: (1) reverify holds the draft text frozen,
so model behavior cannot be the variable -- every pass->fail is a verifier-side
verdict change on byte-identical input; (2) the baseline table maps every
verdict change to an intentional verifier commit. No regression exists. Model
pinning targets a cause not in evidence.

## Part 2 -- Option-2 decision (facts-block enrichment)

### Capturability gate (Q2-PRE)
- Failing rows total: 153. Empty prompt_text (pre-2026-04-15 capture,
  uncapturable): 56. Non-empty usable: 97.

### Triage (Q2, hard-failure lines)
- claim-text-in-prompt: 2
- claim-text-absent: 470
- prompt-empty-uncapturable: 316
(Line-level counts across all hard failures; the 97 non-empty figure above is
row-level. A failing row carries multiple hard-failure lines, e.g. SCORE_VERBATIM
x5, hence lines >> rows.)

### Option 2 verdict: DIRECTIONAL high-leverage, with a fork
Overwhelmingly absent-dominant (470 vs 2). The fabrications split two ways, both
data-layer addressable:
- (a) Value contradicts an EXISTING canonical value -- series "3-0" vs actual
  H2H "16-10"; streak "7-game" vs actual "0 (current), 1"; all-time-record
  claims vs actual. Fix: enrich the facts block with H2H / streak / record so
  the model cites rather than invents. High-leverage.
- (b) Transaction that DOES NOT EXIST -- FAAB "$60 to Tyreek Hill" where there
  is no waiver-bid record. No value to supply; the lever is feeding EXPLICIT
  ABSENCE (an explicit, possibly empty, FAAB-awards list) so the model sees
  "none" instead of a void it fills.
Both align with the project's data-layer lesson (give it the data -- including
explicit absence -- and it cites it; withhold it and it invents). Enrichment is
the right next step, but it must include absence signals, not just present
values. PRECEDENT (proven this pass): score pre-rendering already validated this
playbook -- SCORE_VERBATIM fabrication fell from 124/124 pre-fix to 3/39 post-fix
once the canonical score string was pre-rendered and the model instructed to copy
it verbatim. Option 2 is extending that same proven approach to the FAAB / series
/ streak / record categories, which have not yet had it.

OPEN -- firm confirmation: the triage is instr-based (crude). Pull ~12 non-empty
failing rows' prompt_text and read it against the evidence column to confirm the
correct value (or explicit absence) was genuinely missing from the block. If
present-but-misread on a meaningful share, that share is generation discipline,
not enrichment.

### SOFT-only blind spot
Q2 joins hard_failures only; BANNED_PHRASE / NUMERIC_UNANCHORED / SPECULATION
never appear here. A clean Q2 does not clear unanchored-number fabrication.

## Part 3 -- Live rate sampling (NOT run this pass)
Out of scope here and the decisive next step for the CURRENT-pipeline rate, since
this corpus is stale. Stratified candidates the harness surfaced (dense by FAAB):
2025 W13, 2024 W13, 2025 W10; sparse: 2024 W1/W2/W3. Run under the current
pipeline (post score-pre-rendering, post FAAB hardening) to measure live
fabrication, then re-run the harness with --refresh.

## Remediation disposition
- Option 1 (STREAK trailing-count hardening): ships INDEPENDENTLY; stands on the
  demonstrated gap. Note STREAK verdicts are stable April->HEAD (delta 0), so this
  is a coverage improvement, not a regression fix.
- Option 2 (facts-block enrichment): DIRECTIONAL high-leverage; spec as its own
  session, including explicit-absence signals (fork b above). Gate the firm call
  on the prompt_text read (OPEN).
- Option 3 (model pinning): DROPPED (no regression; model not the variable).

## Scope / discipline
- Diagnose-only. Sidecar reverify rows only; no verifier/pipeline/model change;
  no fact/ledger writes.
- The 0.94 fraction is the stale-corpus rate, integrity diagnostics only, NOT a
  metric to optimize and NOT the live-pipeline rate.
- W16 streak correction stays PARKED (append-corrected-version path).
- Doc-only memo; ASCII subject; SKIP prove_ci.
