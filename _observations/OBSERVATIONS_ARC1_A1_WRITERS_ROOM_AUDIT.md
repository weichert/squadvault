# A1 Audit: Writer's Room Prompt Inspection
## Arc 1: Data Integrity | SquadVault Commissioner Review Arc
**Date:** 2026-05-17
**HEAD at authoring:** 4946733
**Governing brief:** session_brief_commissioner_review_arc.md

---

## Questions the audit must answer

1. Is prior approved recap text being passed as context?
2. What cross-week figures are currently computed and passed?
3. What instruction, if any, exists about numeric claim sourcing?

---

## Finding 1: No prior approved recap text is injected

**Verdict: NOT A CAUSE.**

`weekly_recap_lifecycle.py` passes six context parameters to
`draft_narrative_v1()`:
- `season_context` -- standings, streaks, scores
- `league_history` -- cross-season longitudinal data
- `narrative_angles` -- detected story hooks
- `writer_room_context` -- scoring deltas + FAAB totals
- `player_highlights` -- per-franchise starter/bench scoring
- `verification_feedback` -- rejection notes on retry

No prior approved recap text. No previous week narratives.
The fabrication-persistence pattern (Brian Thomas Jr. appearing in W4 AND W12)
is not caused by context injection -- it is caused by the model re-generating
the same hallucination from the same cumulative context each time.

---

## Finding 2: FAAB context passes cumulative totals only -- no per-player bids

**Verdict: PRIMARY CAUSE of FAAB fabrication.**

`writer_room_context_v1.py` renders the WRITER ROOM block as:

    FAAB spending through this week:
      Brandon: $247 spent ($153 remaining of $400, 62% spent)
      Eddie: $189 spent ...
      Steve: $312 spent ...

Individual player+bid pairs are NOT present. The model sees "Brandon spent $247
total" but has no data about which players cost what. When it writes about
notable acquisitions, it invents player names and amounts consistent with the
total -- always plausible, never correct.

Confirmed fabricated claims (not in WAIVER_BID_AWARDED):
  Brian Thomas Jr. ($51) -- Brandon -- W4, W12
  Ladd McConkey ($32) -- Eddie -- W4
  Brock Bowers ($46) -- Steve -- W4
  Justin Jefferson ($60) -- Michele -- W13, W14

---

## Finding 3: Existing verifier has a logic gap that allows these through

**Verdict: VERIFIER BUG -- Category 8 FAAB_CLAIM.**

`verify_faab_claims()` finds dollar amounts near FAAB keywords, then searches
for a nearby player name that EXISTS IN `faab_bids` (i.e., has a
WAIVER_BID_AWARDED record). Players with NO canonical bid record are filtered
out of the name search:

    for display_name, pid in display_to_pid.items():
        if pid not in faab_bids:
            continue   # <-- silently skips players never acquired via FAAB

Result: a player fabricated into a FAAB claim who was never a waiver pickup
is invisible to the verifier. The verifier only catches WRONG AMOUNTS for
players who WERE acquired via FAAB -- not fabricated acquisitions of players
who were never picked up at all.

This is the direct cause of why Brian Thomas Jr. ($51), McConkey ($32),
Bowers ($46), and Jefferson ($60) pass verification.

---

## Finding 4: System prompt has no numeric-sourcing constraint

**Verdict: CONSTRAINT GAP -- Phase A2 target.**

The system prompt contains:
  - "NEVER invent facts, scores, player names, or events not in the
    provided data"
  - "NEVER fabricate counts, statistics, or per-team tallies"
  - "Do NOT claim a team made 'X acquisitions' ... this data is not
    provided and you cannot derive it accurately"

But NO instruction equivalent to: "every dollar amount must appear
verbatim in the provided context."

The model interprets "do not fabricate" but will still synthesize
plausible-looking FAAB amounts from the cumulative total. A specific
numeric-sourcing constraint is needed (Phase A2).

---

## Causal chain

    FAAB totals only in context
        + no per-player bid data in context
        + no numeric-sourcing constraint in prompt
        + verifier skips players with no canonical bid record
    = fabricated player+amount pairs reach commissioner undetected

---

## Remediation plan confirmed

**B1 (immediate):** Fix `verify_faab_claims()` -- remove the
`if pid not in faab_bids: continue` guard from the player-finding loop.
Any player named near a FAAB keyword + dollar amount must have a
matching WAIVER_BID_AWARDED record. No record = HARD failure.

**A2 (next):** Add prompt instruction: "Every specific dollar amount
in this recap must appear verbatim in the Signal Scout context.
Do not synthesize, estimate, or derive figures not present."

**A3 (after A2):** Extend Writer Room context to include individual
player+bid pairs from WAIVER_BID_AWARDED, making the prompt
self-sufficient for FAAB claims.

---

## Answers to brief's three questions

1. Prior approved recap text: NO -- not injected. Not a cause.
2. Cross-week figures passed: FAAB cumulative totals per franchise,
   week-over-week scoring deltas. No per-player bid amounts.
3. Numeric sourcing instruction: NONE explicit for dollar amounts.
   General "do not invent" exists but insufficient.
