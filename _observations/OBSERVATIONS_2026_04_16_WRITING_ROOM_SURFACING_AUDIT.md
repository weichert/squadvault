# Phase 10 Observation — Writing Room surfacing audit

**Date:** 2026-04-16
**Commit under test:** `f36350e` (baseline 1,777 passing, 2 skipped)
**Method:** Read-only diagnostic via `scripts/diagnose_surfacing_audit.py`
over 70 `prompt_audit` rows (league=70985, attempt=1, seasons 2024–2025).
No DB writes, no detector changes, no selection-logic changes.

---

## The question this session was set up to answer

Phase 10 Observation v3 named one central question:

> Between Signal Scout intake and `recap_artifacts.rendered_text`, where
> do TRADE_OUTCOME and SCORING_MOMENTUM_IN_STREAK angles get dropped?

The audit answers it. But the audit also reveals that the two named
detectors aren't the whole phenomenon, and that the phenomenon is not
one shape but several overlapping shapes. The observation lays them
out separately because they imply different dispositions.

## Naming note up front

The briefing's informal D-numbering ("D4 TRADE_OUTCOME, D49
SCORING_MOMENTUM_IN_STREAK") does not match the in-source
`CATEGORY_TO_DETECTOR` map at
`src/squadvault/recaps/writing_room/prompt_audit_v1.py:60`. In source:

- `TRADE_OUTCOME` → **D15** (labeled "Detector 15" in
  `player_narrative_angles_v1.py:1639`)
- `PLAYER_BOOM_BUST` → **D4**
- `SCORING_MOMENTUM_IN_STREAK` → **D49** (matches)

This doc keys on category strings. The OBSERVATIONS_2026_04_14 note
already uses this convention and it's more stable than the D-numbers.

## Stage 1 of the briefing's candidate list is a no-op in production

The scope doc named four candidate stages. Inspection at commit
`f36350e` confirms `build_selection_set_v1` and `SelectionSetV1` are
not called in `weekly_recap_lifecycle.py` (`has_selection_set=True` at
line 1040 is a provenance flag). The production path is detector →
`_all_angles` → tiered budget. **There is no Writing Room
intake-contract filter between detector emission and the budget gate.**
"NOT_DETECTED" and "intake-rejected" are indistinguishable because no
intake rejection stage exists. The remaining three stages — budget,
prompt assembly, model omission — are the real classification axes.

---

## Primary finding — the surfacing void is broader than two detectors

Across 70 audit rows, **nine categories reach the 0-budget void bar**
(detected > 5, budgeted = 0):

| Category | Detections | Budgeted | Weeks fired |
|---|---:|---:|---:|
| PLAYER_JOURNEY | 221 | 0 | 2 |
| TRADE_OUTCOME | 95 | 0 | 22 |
| LUCKY_RECORD | 39 | 0 | 16 |
| SCORING_MOMENTUM_IN_STREAK | 32 | 0 | 12 |
| SCORING_RECORD | 16 (×; see Finding 5) | 0 | 13 |
| PERFECT_LINEUP_WEEK | 25 | 0 | 9 |
| PLAYER_VS_OPPONENT | 20 | 0 | 4 |
| PLAYER_FRANCHISE_TENURE | 19 | 0 | 2 |
| AUCTION_STRATEGY_CONSISTENCY | 16 | 0 | 2 |
| SCORING_STRUCTURE_CONTEXT | 6 | 0 | 2 |

The briefing framed this as "D4 + D49: 50 firings across 35 weeks, zero
surfacings." The audit data puts the actual number at **461 detections
across 2 seasons, zero budgeted — spread across nine categories, not
two.** The briefing's D4 was informal shorthand for TRADE_OUTCOME, which
is D15 in source; the actual D4 (`PLAYER_BOOM_BUST`) is adjacent in
shape at 571 detections → 6 budgeted (1.0%), not a full void but
demonstrating the same mechanism.

The phenomenon is not "two detectors broken." It is **a class of angle
that the tiered budget gate systematically drops.**

---

## Finding A — budget gate, working as designed, for six of the nine

For **TRADE_OUTCOME, SCORING_MOMENTUM_IN_STREAK, PLAYER_VS_OPPONENT,
PERFECT_LINEUP_WEEK, LUCKY_RECORD, SCORING_RECORD**, every week of
every detection had the 4-slot MINOR cap fully consumed by other
categories. These six are MINOR-tier angles (strength=1, except
TRADE_OUTCOME which reaches strength=2 only when gap ≥ 40 pts — which
didn't happen in any of its 22 detected weeks) competing for 4 slots
against categories that emit at similar or greater volume.

The DISPLACER AGGREGATE table quantifies what they lost to. Across all
void-drop events:

| Category | Times in budget |
|---|---:|
| AUCTION_BUST | 241 |
| BENCH_COST_GAME | 114 |
| BLOWOUT | 81 |
| FAAB_ROI_NOTABLE | 57 |
| STREAK | 43 |
| CHRONIC_BENCH_MISMANAGEMENT | 41 |

AUCTION_BUST alone is in the budget of 241 void-drop events. It emits
at 191 detected → 189 budgeted (99% surfacing rate), the highest of any
category — because it fires once per auction-bust player per week and
most weeks have multiple. Combined with BLOWOUT (68 detected → 67
budgeted, 99%) and NAIL_BITER (28 detected → 11 budgeted, 39%) and
BENCH_COST_GAME (104 → 87, 84%), the coverage-breadth MINOR fill
consistently prioritizes these over the audited voids.

This is **the exact pattern D12 Finding 1 resolved in April 2026.** The
budget gate is behaving as the coverage-aware MINOR fill was designed
to: breadth over depth, one-per-category, franchises not yet covered by
HEADLINE/NOTABLE sort first. The logic at
`weekly_recap_lifecycle.py:754-807` is working.

**Disposition: no code change.** The design correctly prefers breadth
over depth in MINOR fill. Whether that design still serves PFL Buddies
given the current angle mix is a governance question for the
commissioner, not a defect. The question is framed below.

---

## Finding B — season-opener detonation (the W1-only detectors)

For **PLAYER_JOURNEY, PLAYER_FRANCHISE_TENURE,
AUCTION_STRATEGY_CONSISTENCY, SCORING_STRUCTURE_CONTEXT**, the pattern
is different. These detectors fire *only at W1* of each season, and
they fire at extreme volume when they do:

- PLAYER_JOURNEY: 108 detections in 2024 W1, 113 in 2025 W1 — one per
  player with a multi-franchise journey, across all 10 rosters on
  opening day
- PLAYER_FRANCHISE_TENURE: 9 in 2024 W1, 10 in 2025 W1
- AUCTION_STRATEGY_CONSISTENCY: 8 + 8
- SCORING_STRUCTURE_CONTEXT: 3 + 3

And — load-bearing — the **W1 budgets are under the 12-cap**: 10
budgeted in 2024 W1, 11 in 2025 W1. HEADLINE and NOTABLE aren't hitting
their tier caps (3 and 6). This is not a cap-exhaustion drop. The
MINOR slots (4 of them) are being consumed by other W1-only angles
(AUCTION_BUDGET_ALLOCATION, AUCTION_DRAFT_TO_FAAB_PIPELINE,
AUCTION_LEAGUE_INFLATION, AUCTION_MOST_EXPENSIVE_HISTORY,
AUCTION_POSITIONAL_SPENDING), which emit once per W1 and are
category-diverse, so they each get their single slot.

The 1-per-category rule collapses these four "deluge" detectors to one
slot each *before* the coverage-aware sort, and then the coverage sort
loses them to whatever the week-seeded rotation hash happens to pick
first. 221 PLAYER_JOURNEY detections compress to 1 candidate slot
before the sort, then lose the rotation.

**Disposition: no code change this session.** The budget gate is still
behaving as designed — 1-per-category is the explicit rule. But this is
a distinct shape from Finding A, and it opens a different governance
question: is one PLAYER_JOURNEY line in W1 (or one every two W1s, given
rotation) the amount of surfacing the commissioner wants for a 221-fire
detector, or is it a re-tier candidate?

The W1-deluge detectors are structurally different enough from
coverage-competing MINOR categories that the observation is worth
naming separately even though both findings route to the same code
site.

---

## Governance question surfaced — is this the intended outcome?

The budget gate is functioning correctly. The question the observation
forces into the open is whether the **current angle mix and league
reality** produce the outcome the design was optimized for.

Specifically, given 2 seasons of production data:

- **6 of 9 void categories lose to AUCTION_BUST and BENCH_COST_GAME**
  in 4-slot MINOR competition. AUCTION_BUST alone occupies ~60% of
  all MINOR slots measured across void-drop weeks.
- The **1-per-category cap is the binding constraint**, not the 4-slot
  cap. The coverage-breadth sort is the tiebreaker, not the filter.
- Angles about repeat subjects (TRADE_OUTCOME describing the same trade
  every week for 22 weeks; LUCKY_RECORD describing the same lucky team
  all season) are structurally penalized by a system that prefers
  breadth.

Three framings the commissioner might consider — framed as questions,
not recommendations:

1. **Accept and name it.** The current MINOR fill is breadth-over-depth
   by design. 22 weeks of TRADE_OUTCOME never surfacing is the cost
   of giving every franchise narrative presence every week. If the
   commissioner holds this view, the observation closes with a
   documented rationale.

2. **Re-tier specific angle classes.** TRADE_OUTCOME (especially at
   gap ≥ 40 which already triggers strength=2) and SCORING_MOMENTUM
   might belong at NOTABLE, not MINOR, on their own merits. This
   isn't a budget-gate change — it's a detector-side strength
   reclassification, the same move made on
   AUCTION_BUDGET_ALLOCATION / AUCTION_PRICE_VS_PRODUCTION /
   SCORING_CONCENTRATION / STAR_EXPLOSION_COUNT in the NAv2 window
   (normal → rare tier).

3. **Question AUCTION_BUST volume.** 99% surfacing rate and 241
   appearances across void-drop weeks means AUCTION_BUST is, by
   revealed preference, the dominant MINOR category. If it's narratively
   less interesting than TRADE_OUTCOME over 22 weeks but wins on
   mechanical grounds, that's worth seeing.

None of these is this session's call. The audit surfaces the numbers.
The judgment is the commissioner's.

---

## Finding C — also visible, partially actioned

Three things the audit surfaced that are not the surfacing question.
C1 was actioned in the same session; C2 and C3 deserve their own
observations if pursued.

**C1 — raw franchise ID in SCORING_VOLATILITY headlines (resolved,
commit `fc922be`).** 2025 W10's budgeted MINOR line contained:

```
[MINOR] [RE: Miller's Genuine Draft] 0006 has the narrowest scoring
range this season — Range: 33.6 pts between best and worst weeks.
```

Initial framing attributed this to a `_name_map` lookup miss. Inspection
showed the real cause was different and localized:
`detect_scoring_volatility` in
`src/squadvault/core/recaps/context/franchise_deep_angles_v1.py`
accepted an `fname` parameter but the two emitted headlines
("narrowest/widest scoring range") interpolated the raw
`most_consistent[0]` / `most_volatile[0]` fid rather than calling
`fname(...)` on it. The `_name_map` itself was healthy — the
`[RE: Miller's Genuine Draft]` tag in the same prompt line was resolved
correctly via the lifecycle's `_name_map.get(fid, fid)` at
`weekly_recap_lifecycle.py:817`, because that code path routed through
the resolver. The headline never did. Grep over
`franchise_deep_angles_v1.py` confirmed the other five f-string
headlines in the file correctly wrap `fname(fid)`; this was the only
detector with the bug.

The existing `test_detects_volatile_and_consistent` used fixture fids
`"F1"` / `"F2"` with default `fname=_identity`, so raw fid and resolved
name were the same string — the test could not distinguish whether
`fname` was being called. Fix wrapped both headlines with `fname(...)`
and added `test_fname_resolves_franchise_id_in_headline` which passes a
non-identity `fname` and asserts resolved names appear while raw fids do
not. Regression test fails against the pre-fix detector; passes against
the fix. Tests: 1,777 → 1,779 (+1 explicit regression, +1 Hypothesis
example expansion).

**C2 — REVENGE_GAME near-void.** 658 detections → 3 budgeted (0.5%).
Highest detection volume of any MINOR category not in the void list.
Doesn't appear in the `d > 5 and b == 0` void cutoff because b=3, but
functionally a void. Pair-scoped, matchup-specific — not obviously the
same coverage-breadth mechanism. Worth its own audit pass.

**C3 — `UNMAPPED` category drift.** 1,157 angle instances across 68/70
weeks are tagged detector="UNMAPPED" in `CATEGORY_TO_DETECTOR`. The
categories involved: BLOWOUT, BYE_WEEK_CONFLICT, BYE_WEEK_IMPACT,
FRANCHISE_BYE_WEEK_RECORD, NAIL_BITER, SCORING_ANOMALY,
SCORING_RECORD, SCORING_STRUCTURE_CONTEXT, STREAK, UPSET. The
`test_category_to_detector_drift_detector` test in the suite should
fail when new categories appear and the map isn't updated. One of two
things is true: either the test is failing and hasn't been seen, or
these categories are structurally excluded from the drift check (tier
separation, ingest-layer categorization). Worth confirming which.

(C3 also affects the per-detector table in the audit output — the
UNMAPPED row at 1,157 detected / 220 budgeted / 19% rate understates
the true per-detector picture wherever those 10 categories belong.)

---

## Constraints honored

- Read-only diagnostic. No DB writes, no LLM calls, no detector
  changes, no selection-logic changes, no prompt changes.
- Diagnostic output went to `/tmp/surfacing_audit.csv` and
  `/tmp/surfacing_audit_with_drilldown.txt`.
- Baseline preserved: ruff clean, mypy clean, 1,777 passing, 2 skipped.
- Script modification was a targeted patch (146-line unified diff) to
  the existing untracked `scripts/diagnose_surfacing_audit.py`, not a
  full-file replacement.
- Architecture remains frozen. Governance model unchanged. No
  analytics, optimization, engagement loops, or predictive features
  introduced.

## Disposition

**Findings A and B: no code change.** The budget gate is working as
designed. The coverage-breadth MINOR fill prioritizes franchise
coverage over angle depth, and the 1-per-category rule caps deluge
detectors at 1 slot. Both are explicit design decisions. Whether this
serves PFL Buddies in 2026 is a governance question for the
commissioner, framed above with three candidate framings.

**Finding C1 (SCORING_VOLATILITY headlines emitting raw fid):** resolved
in commit `fc922be`. Two-line detector fix plus regression test.
Pre-existing in-production prompts (up to 12 affected weeks per the
audit's SCORING_VOLATILITY row: 6 budgeted in 2024, 6 in 2025) are not
retroactively edited — approved recaps are immutable per constitution.
Fix prevents future occurrences only.

**Finding C2 (REVENGE_GAME near-void) and C3 (UNMAPPED drift):** logged
here, not actioned in this session. Candidates for separate
observation passes if pursued.

## Next action

Commissioner decision on which of the three governance framings (if
any) to pursue for Findings A and B. If "accept and name it" is the
call, this observation closes with no further work. If re-tier or
angle-mix rebalance is the call, that becomes a scoped change with its
own observation and defect ticket.
