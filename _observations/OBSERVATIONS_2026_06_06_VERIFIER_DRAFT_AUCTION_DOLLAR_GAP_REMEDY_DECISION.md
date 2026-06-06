# OBSERVATIONS 2026-06-06 - Verifier draft/auction dollar gap: REMEDY DECISION

Decision-readiness session (one phase). Engine HEAD e4e0060, clean tree. No fix
code, no fixture mutation, no generation. This memo RECORDS the remedy decision.
The FIX is the next gated session (code-adjacent -> prove_ci; this memo is doc-only).

Source of record for the gap itself: OBSERVATIONS_2026_06_05_VERIFIER_DRAFT_
AUCTION_DOLLAR_GAP.md (commit aa020dd). This session re-confirmed that gap at
current HEAD and ran the decision probes; it does not re-derive aa020dd.

## Decision (recorded)

Remedy A, single commit, skip B, defer C, FAAB-style HARD/SOFT tiering per S4.

- A (chosen): add ONE self-contained verifier category that queries DRAFT_PICK
  (+ player_directory for position) directly, re-derives the ground truth, and
  validates the voiced draft/auction dollar and positional-spend claims. Durable,
  data-anchored. Aligns with 'data-layer fixes are strong; suppress guardrails weak'.
- B (skipped): interim suppress-side SOFT flag. A is small enough to do directly,
  so B would be thrown-away work.
- C (deferred): aggregate-dollar sub-check. Distinct data source and claim shape
  (waiver sum, not draft); tracked as a separate follow-on (see P6).

Sub-decisions:
- S1 one commit / one session. No prompt-assembly edit is needed (see refinement
  below), so A is a single topic: the new verifier category. This SUPERSEDES
  aa020dd's two-commit framing (surface-to-evidence-block + category).
- S2 skip interim B; go straight to A.
- S3 defer C; anchor it against WAIVER_BID_AWARDED sum in its own commit.
- S4 tier the new category like FAAB_CLAIM:
    HARD when the voiced figure CONTRADICTS the re-derived ground truth, or is
      cited for a (season, franchise) that HAS DRAFT_PICK coverage but yields no
      matching derivation (fabrication).
    SOFT / flag-for-review when there is NO DRAFT_PICK coverage for that scope
      (a data hole - e.g. the known 2021 DRAFT_PICK gap). This keeps 'silence over
      speculation' intact: we do not assert a claim is wrong when we lack facts to
      judge it; we surface it for the commissioner instead.

## Two refinements over aa020dd (load-bearing for the fix session)

R1 - A is VERIFIER-ONLY; no prompt-assembly edit. Every verifier category queries
the ledger directly (FAAB loads WAIVER_BID_AWARDED at recap_verifier_v1.py line
4424). P3 confirmed the emitted figures are already DERIVED deterministically from
DRAFT_PICK.bid_amount by auction_draft_angles_v1 detectors 23/24 and already reach
the prompt as narrative angles. So the verifier does not need an 'evidence block';
it re-derives ground truth itself and compares. Neither half of aa020dd's two-part
A requires a prompt change. A collapses to one self-contained category.

R2 - the dollars live in DRAFT_PICK ONLY. P4 (read on the committed fixture, season
2024, league 70985): DRAFT_PICK = 170 events, bid_amount present on ALL 170.
TRANSACTION_AUCTION_WON = 10 events and carries NO dollar field at all (payload
keys: franchise_id, mfl_type, player_id, raw_mfl_json, source_url). So A must anchor
against DRAFT_PICK, NOT against both event types as aa020dd listed. The new category
should not query TRANSACTION_AUCTION_WON for dollars - there are none promoted there.

## Probe results (this session, 2026-06-06)

P1 - static re-confirm (deterministic, robust core). At e4e0060 verify_recap_v1
still runs 15 check passes and queries exactly WEEKLY_MATCHUP_RESULT, WEEKLY_PLAYER_
SCORE, WAIVER_BID_AWARDED. DRAFT_PICK and TRANSACTION_AUCTION_WON: zero occurrences
anywhere in the 4808-line file. SUPERLATIVE disarms (continue) on the +/-80-char
auction/draft window (~1308); FAAB_CLAIM suppresses on \bdraft\b within 30 chars
and skips when no player name is within 100 chars; NUMERIC_UNANCHORED is counts-only.
Classification unchanged: VERIFIER_SIDE structural gap.

P3 - figure provenance: case (a), DERIVED. detect_auction_budget_allocation emits
'$MAX top pick, $MIN cheapest' (max/min of bid_amount per franchise per season);
detect_auction_positional_spending emits per-position sums. Both are deterministic
functions of canonical DRAFT_PICK.bid_amount -> anchorable, and the figures' own
accuracy is sound at the point of derivation. The gap is purely that the verifier
never re-derives to confirm the VOICE transcribed them faithfully.

P4 - anchorability: both shapes reconstruct. Max/min per franchise (e.g. $59/$1,
$60/$1) for top-pick/cheapest; per-franchise-per-position sums (e.g. fid 0004 WR
$141) for positional spend, with 170/170 DRAFT_PICK position coverage via
player_directory. Aggregation ladder for the fix: per-pick -> per-franchise (max/min)
-> per-franchise-per-position (sum).

P5 - blast radius: small and controlled. Categories are string labels (no enum, no
count constant). No test pins checks_run. No existing passing test asserts these
draft/auction figures pass clean, so A flips zero green tests. reverify_prompt_audit.py
is present; the FIX session uses the category-breakdown SQL on prompt_audit_reverify.
result_json (NOT row-level pass->fail counts) to isolate the new category from drift.

P6 - aggregate-dollar secondary finding ('five teams ... totaling $67'): waiver-
sourced (sum of WAIVER_BID_AWARDED), a distinct data source and claim shape from the
DRAFT_PICK gap. Deferred as C; one topic per commit.

P2 - dynamic reproduce on the repaired fixture: prerequisites verified-ready but the
LIVE run was deferred this session. The decision-readiness work was done in a fresh
clone with no .env.local / ANTHROPIC_API_KEY, so no keyed generation ran here. What
is confirmed: the committed fixture resolves weeks 1-4 to real events and contains
the anchor events (DRAFT_PICK 170, AUCTION_WON 10, WAIVER 65; season 2024). The gap
was already corroborated LIVE at aa020dd (loop iteration 1 caught $99/$70/$1 passing
the gate clean, hard=0, no fallback). The A/B/C decision rests on the deterministic
core (P1/P3/P4/P5) and does not depend on P2. If an end-to-end-on-repaired-CI artifact
is wanted, run the force=True per-iteration inspection loop (inspection-point recipe
in aa020dd) on a disposable fixture copy in the keyed environment; not load-bearing.

## Constitutional check

The chosen remedy ADDS a verifier category that anchors figures against canonical
DRAFT_PICK facts. It loosens no existing check. SOFT-tier no-coverage scopes preserve
silence over speculation. Facts immutable/append-only; narrative derived; AI assists,
humans approve. No analytics/optimization/engagement/prediction introduced.

## Next session (the FIX - gated, code-adjacent, prove_ci required)

Scope sketch (one commit): a new verify_draft_auction_dollars category in
recap_verifier_v1.py that (1) loads DRAFT_PICK + player_directory positions, (2) parses
the voiced claim shapes (top-pick/cheapest -> max/min; positional spend / 'half his
draft capital' -> per-position sum and ratio), (3) re-derives ground truth and compares,
(4) emits HARD/SOFT per S4. Add checks_run += 1. Tests: pass clean on faithful figures,
HARD on a drifted figure, SOFT on a no-coverage scope. Run the reverify category-
breakdown gate before merge. Deferred companions: C (waiver aggregate sub-check).
