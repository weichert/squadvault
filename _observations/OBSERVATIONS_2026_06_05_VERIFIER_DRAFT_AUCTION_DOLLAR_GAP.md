# OBSERVATIONS 2026-06-05 - Verifier draft/auction dollar gap (CONFIRMED)

Diagnostic-only session (one phase). Engine HEAD 4ba8992, clean tree. No fixes,
no fixture mutation, all generation stayed DRAFT. Fix is a later session.

## Question

Does verify_recap_v1 flag draft/auction dollar figures or positional draft-spend
claims, or do they pass unchecked? The product promise 'AI assists, humans
approve' only holds if the verifier actually anchors what the voice emits.

## Verdict

CONFIRMED GAP. No verifier category validates a draft/auction dollar figure or a
positional draft-spend claim against DRAFT_PICK or TRANSACTION_AUCTION_WON. Proven
two ways: a deterministic static read (the robust core) and a live corroborating run.

## PRONG 1 - static (deterministic; needs no API key)

Across the 4,808-line recap_verifier_v1.py, verify_recap_v1 runs 15 check passes
and queries EXACTLY three canonical event types:

| Event type | Used by |
|---|---|
| WEEKLY_MATCHUP_RESULT | SCORE, SCORE_VERBATIM, SUPERLATIVE, STREAK, STREAK_INVERSION, RECORD_CLAIM_ANCHORING, SERIES, CHAMPIONSHIP/SEASON_RECORD |
| WEEKLY_PLAYER_SCORE | PLAYER_SCORE, PLAYER_FRANCHISE, PLAYER_AVG_CLAIM, PLAYER_STREAK_CLAIM, season/all-time player high |
| WAIVER_BID_AWARDED | FAAB_CLAIM |

DRAFT_PICK and TRANSACTION_AUCTION_WON: zero queries anywhere in the file.

Three near-miss checks and why each lets draft/auction dollars through:

1. SUPERLATIVE (verify_superlatives, lines ~1290-1305): when the +/-80-char window
   matches auction|investment|points per dollar|bargain|draft pick|$N spent/pick|
   most productive auction/draft, the loop executes `continue`. It DISARMS to avoid
   false-positive scoring-record matches - it never validates the figure. So a
   '$70 top pick in league history' superlative is dropped, not checked.
2. FAAB_CLAIM (verify_faab_claims): loads only WAIVER_BID_AWARDED (line 4424).
   Line ~4524 suppresses outright when \bdraft\b appears within the 30-char keyword
   window; it also requires a player name within 100 chars, so manager/position
   spend (Ben spent $99 on wideouts) finds no player and is skipped. The correctly
   cited waiver figures pass because they are real WAIVER_BID_AWARDED rows - that
   path works as designed.
3. NUMERIC_UNANCHORED (verify_numeric_unanchored): _AGGREGATE_COUNT_PATTERN matches
   a count followed by move|acquisition|pickup|transaction (min 4); sub-check 2
   catches historical ordinals >= 10. Dollar figures and positional spend are
   entirely out of scope.

Static classification: VERIFIER_SIDE structural gap.

## PRONG 2 - dynamic (corroboration; live API run)

Recipe note / methodological finding: the persisted recap_artifacts.rendered_text
is the WRONG inspection point whenever any hard failure fires. The no-retry and
exhausted-retry paths overwrite the voiced text with the facts-only base plus a
'Falling back to facts-only - silence over fabrication' note (lifecycle ~1379-1432).
_extract_shareable_recap returns the full text when delimiters are absent, so a
standalone verify of a facts-only artifact reports passed with all checks run -
on facts, not on the discarded voice. To observe voice-side numerics you must
catch a run where the voiced text PASSES (no fallback), or read the pre-fallback
audit. A force=True loop that inspects per-iteration persisted artifacts and breaks
on the first passing voiced run with a non-waiver dollar figure does the job.

First run this session (positive control): the voiced attempt fabricated a FAAB
amount - '$3 FAAB ... T.J. Hockenson' vs canonical $0.50. FAAB_CLAIM caught it
(HARD), no-retry -> facts-only fallback. This confirms FAAB_CLAIM fires correctly.

Loop run, iteration 1 (the gap): embedded passed=True, standalone passed=True,
hard=0, soft=0, no fallback - the voiced shareable section survived and was scored
clean. It contained these unanchored claims, which passed the gate:

- Ben: 'putting $99 of his $200 budget into the position - exactly half his draft
  capital' (auction positional spend).
- Michele: 'spending $70 on his top pick while his cheapest player went for just
  $1' (draft concentration).

Neither is verifiable against any queried event type; both passed as verified-clean.

Precision note: a crude in-loop classifier also flagged $16 Greg Dortch and $11
Baker Mayfield as draft/auction. Those are waiver figures (the adjacent 'draft
strategy' sentence fell inside the +/-50-char context window). They are NOT gap
instances. The robust instances are the auction/draft figures above.

Secondary finding: 'five teams making paid waiver claims totaling $67' is an
AGGREGATE dollar sum that also passed unflagged. FAAB_CLAIM is per-player and
NUMERIC_UNANCHORED is counts-only, so no check covers a dollar aggregate. Distinct
from the draft/auction gap; same root shape (an unanchored dollar figure).

## Classification

- The missing check: VERIFIER_SIDE (structural - no category anchors draft/auction
  dollars; no DRAFT_PICK / TRANSACTION_AUCTION_WON query exists).
- The emission: MODEL_SIDE - the voice surfaces season/draft numerics into a weekly
  recap; these figures come from season/draft context in the prompt assembly, not
  the week-1 selection set. Whether the specific numbers are accurate is unknown -
  unverified is unverified.
- The remedy: AMBIGUOUS between data-side anchoring and a new verifier category.
  Per the constitution, any fix adds anchoring, never loosens a check.

## Scoped follow-up (LATER session - do not fix here)

Candidate fix shapes, to be decided next session:
A. Data-side: surface DRAFT_PICK / TRANSACTION_AUCTION_WON dollar facts into the
   prompt evidence block so the figures are anchored, then add a verifier category
   that validates auction/draft dollar + positional-spend claims against them.
B. Suppress-side (NOT loosening): if draft/auction context is detected and the
   figures are not in the evidence block, treat as NUMERIC_UNANCHORED (SOFT) so the
   commissioner sees the flag - interim measure pending A.
C. Aggregate-dollar sub-check: extend the unanchored sweep to dollar aggregates
   ('totaling $N') as SOFT.
Recommendation: A is the durable fix (data-layer fixes are strong; prompt/suppress
guardrails are weak). B/C are cheap interim SOFT flags. One topic per commit.
