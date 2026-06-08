# Matchup Anchors Phase 1 - Disposition: DISABLE (founder-ratified)

Engine HEAD at decision: 697ffd5 (SERIES tie-aware verifier)
Date: 2026-06-08
Type: disposition / doc-only memo. No fact writes; no approvals.
Decision: D1 option (b) DISABLE, founder-ratified.

## What was decided
The phase-1 per-matchup anchor block -- derived recap-time context injected by
c2eaa57 (lifecycle) over the renderer from b91e730 -- is DISABLED. The preceding
code commit reverts the c2eaa57 injection (import + injection block) in
src/squadvault/recaps/weekly_recap_lifecycle.py, returning _derive_prompt_context
to its pre-c2eaa57 shape (byte-identical). The renderer
src/squadvault/core/recaps/render/render_matchup_anchors_v1.py and
Tests/test_matchup_anchors_v1.py are left intact and inert: the derivation stays
tested and the experiment is fully reversible (re-add import + injection).

## Why (evidence re-read under the tie-correct verifier)
The phase-1 validation (7461fc6) closed NOT VALIDATED - inverted (6/6 anchors-on
vs 2/6 anchors-off on discriminating weeks) but ran on the tie-blind verifier and
removed tie false positives by hand. This disposition re-read that evidence on the
now-tie-correct verifier (697ffd5) first.

Method: re-ran verify_recap_v1 over the retained anchors-ON drafts via
reverify_prompt_audit.py tagged 697ffd5 (pure function of stored text + DB state;
no generation; no API). Isolated the drafts by the anchor signature in
prompt_text, scoped to 2025 W10/W13/W16.

Result: the direction survives and strengthens.
- Per-run on discriminating weeks: W10 3/3, W13 3/3 = 6/6, reproducing the
  hand-cleaned figure under the code's tie-awareness. W16 had zero in-scope
  failures (non-discriminating).
- Every in-scope SERIES failure is a genuine fabrication; zero tie false
  positives. Examples: claimed 13-12 vs actual 12-12 (inclusive-H2H
  double-count); claimed 9-4 vs actual 16-14; claimed 5-8 vs actual 18-8-1.
- The one tie-touching case (claimed 18-9 for a canonical 18-8-1) is a model
  tie-fold the OLD tie-blind verifier would have PASSED and the corrected
  verifier correctly FAILS. Correction added fidelity; removed no ON-arm failure.
  One non-final attempt went fail->pass and moves no run verdict.

## Harm map by signal type
- Streak (dominant, persistent, tie-irrelevant): surfacing the streak induced
  claims the model mishandled -- magnitude fabrication (Purple Haze "7/8-game
  win streak" when actual was 0 current / 3 pre-week and the anchor said losing)
  and inversion ("losing streak snapped" when it extended to 4). Tie fix has no
  bearing here.
- H2H series (secondary, persistent, not a verifier artifact): anchors were
  ignored (gross fabrications) or corrupted from a correct base (12-12 -> 13-12).
  Corrected verifier confirms model fabrication, not false flags.
- Season record (no observed harm in sample, unproven safe): no
  SEASON_RECORD_CLAIM failure among anchor drafts; n is small; not relied on.

## Constitutional compliance
Derived recap-time context, not facts. Disabling deletes no facts
(canonical_events / memory_events untouched), creates none, is fully reversible.
Underlying H2H / streak / record values still reach the model via the existing
LEAGUE HISTORY and SEASON CONTEXT blocks, so the surface returns to the
measured-better anchors-off baseline. Humans still approve. Silence over
speculation is the operative tie-breaker.

## Entanglement and FAAB phase 2
Disabling removes the production source of the inclusive-H2H double-count; it
remains a real model-behavior finding for the record but is moot for the live
surface. FAAB phase-2 contraindication stands reinforced: the
induce-then-mishandle mechanism is intrinsic to a parallel "cite these exactly"
block and applies at least as strongly to FAAB dollars.

## Provenance
Reverify run tag 697ffd5 over retained 2025 W10/W13/W16 anchors-ON drafts. Writes
confined to the append-only prompt_audit_reverify sidecar; no canonical_events /
memory_events writes; no narrative generation; no API; no approvals.
