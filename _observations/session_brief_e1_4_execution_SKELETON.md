# SESSION BRIEF (SKELETON) - Unit E1.4 execution: fresh-generation fabrication baseline

**STATUS: SKELETON - NOT YET EXECUTABLE.** Blocked on two predecessors (below). This is a
prep artifact authored by the E1.3-adjacent scoping pass (engine HEAD `2b50457`); it
captures everything knowable from the engine so the execution session starts warm. The
bracketed `[FROM PROTOCOL]` fields are filled from the Fable pre-registration memo, NOT
guessed here - pre-registration independence is the point.

**Tool/model (execution half):** Claude Code / Opus 4.8. **Boundary: DIAGNOSE-ONLY - no
pipeline changes in-session** (charter: reverify stays local-only; no token telemetry in
the creative layer).

## Hard predecessors (must exist before this brief is executable)

1. **Fable pre-registration protocol memo** (chat/DECIDE session). Defines: `n` (D-B,
   24-36, founder deferred the pick TO this protocol), the discriminating weeks across the
   pre/post-2021 substrate split, the per-category thresholds, the claim-extraction method,
   and the falsifiable success/headline criterion. Filed in `_observations/` as a
   PRE-REGISTRATION memo (precedent format:
   `OBSERVATIONS_2026_06_07_MATCHUP_ANCHORS_PHASE1_FRESH_GEN_VALIDATION.md` -
   "recorded before any regen; results appended post-run").
2. **D-B adjudicated** - `n` (deferred to the protocol) + an **explicit spend cap** (real
   API cost; the cap is the guardrail). The protocol records both.

## What is knowable now (engine substrate - verified at `2b50457`)

- **Generate path:** `scripts/recap_artifact_regenerate.py` / `scripts/regenerate_season.py`
  produce fresh recaps; generation is captured to the `prompt_audit` table.
- **Measurement path:** `scripts/reverify_prompt_audit.py` re-verifies captured drafts and
  computes **per-category hard-failure counts** (supports `--baseline-tag` for category-NEW
  deltas). Local-only per charter section 8. DB: `.local_squadvault.sqlite`.
- **Category taxonomy:** the headline is the **non-score residual** - FAAB / series /
  streak / superlative. Score categories are measured but are not the headline.
- **Claim classes (precedent):** MATCH / SILENT / FABRICATED / AMBIGUOUS(excluded from rate).
- **Doubles as Closure cert-6 evidence** - the baseline measures the generation path that
  Ask-the-Historian (Phase 12) would later ride.

## Execution shape (to finalize against the protocol)

1. Confirm the protocol memo is filed and frozen; record its hash. Re-verify D-B values.
2. Fresh-generate the `[FROM PROTOCOL: the n discriminating weeks]` under the
   `[FROM PROTOCOL: spend cap]`; stop at the cap and report if hit.
3. Extract claims per `[FROM PROTOCOL: claim-extraction method]`; classify by category.
4. Compute fabrication rate per category; report the non-score residual as the headline,
   against `[FROM PROTOCOL: category thresholds + falsifiable criterion]`.
5. Write the RESULTS memo appended to the pre-registration memo (same-file or paired,
   per the precedent). NO pipeline edits.

## Acceptance criteria (binary)

1. Pre-registration protocol memo exists and was frozen BEFORE generation (verify by
   commit order / timestamps).
2. Results memo in `_observations/` reports live-pipeline fabrication rate **by category**,
   non-score residual as headline, judged against the pre-registered criterion.
3. **Zero pipeline changes** in the session (diff touches only `_observations/`; the DB
   working copy and any reverify sidecar are local-only, not committed).
4. Spend stayed within the D-B cap (or stopped-at-cap is reported honestly).
5. STATE.md discharges E1.4 (cert-6 evidence linked); doc-only path for the committed
   artifact (the memo).

## OUT OF SCOPE

- Authoring the pre-registration protocol (Fable's session - charter section 2.1/2.4).
- ANY pipeline / verifier / prompt change (diagnose-only; fixes are downstream units).
- Score-category deep analysis (headline is the non-score residual).
- Committing the DB, reverify sidecar, or generated artifacts (local-only).

## OPEN until predecessors land

`[FROM PROTOCOL]` fields above; D-B `n` + spend cap. Recommend: founder runs the Fable
protocol session (pre-registration + D-B), then "execute E1.4" finalizes this skeleton
against the frozen protocol.
