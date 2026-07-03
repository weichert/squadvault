# Session Brief — Unit F1: FAAB_CLAIM Verifier Vocabulary + Binder Crossover Fix

**Date authored:** 2026-07-02 (DECIDE session; D-X/D-Y/D-Z ratified 2026-07-02)
**Session type:** EXECUTE (Claude Code), two founder gates (⛔ Gate 1: test plan + design note; ⛔ Gate 2: diff review + merge)
**Repo:** engine (`weichert/squadvault`) — confirm identity with `test -f scripts/recap_artifact_regenerate.py`
**Plan reference:** Stage B attribution (squash `7f436bd`); D-X dispositions; D-Z integrity constraint
**Scope in one line:** teach the FAAB_CLAIM verifier to correctly handle the claim shapes assembly legitimately produces, without weakening its grip on genuine invention.

---

## Paste-ready kickoff prompt

> You are an EXECUTE session for SquadVault Unit F1: the FAAB_CLAIM verifier vocabulary and binder-crossover fix. Read `_observations/session_brief_unit_f1_faab_verifier_fix.md` in full before doing anything. Follow CLAUDE.md session ritual: fresh clone, `git log -1` to verify HEAD, repo identity via `test -f scripts/recap_artifact_regenerate.py`. Two-lane discipline: you execute; the founder adjudicates at the two ⛔ gates. **Hard rules: this unit modifies ONLY the FAAB_CLAIM verification logic in `recap_verifier_v1.py` (and its tests) — no assembly, prompt, Tier-2 policy, or data-layer changes; no generation API calls; prod DB untouched (read-only fixtures only). Tests are written and founder-ratified BEFORE implementation (Gate 1). The D-Z integrity constraint governs: no change may cause a genuine-invention case to pass — under-fixing is acceptable, over-trusting is not.** Nothing is published.

---

## 1. Objective

Eliminate the two verifier-side false-positive mechanisms established by Stage B, per D-X:

- **F1a — claim vocabulary.** The FAAB_CLAIM check currently force-binds every FAAB dollar to the nearest player name. It must instead recognize three non-player-scoped claim shapes and check each against its actual canonical source:
  - **Franchise-total claims** (e.g., "Michele has spent $98 on FAAB"): check against season-to-window franchise FAAB spending (the same derivation `derive_faab_spending` reads), ±$1.
  - **Team-defense pickup claims** (e.g., "the Cleveland defense — a $5 FAAB pickup"): defenses are rosterable; check against the defense's WAIVER_BID_AWARDED record, ±$1.
  - **Team-name references** (e.g., "$2 on the Chargers"): resolve to the corresponding defense/roster entity where the league's canonical model supports it; where it does not, the claim is checked against any in-window entity carrying the amount rather than force-bound to an unrelated player.
- **F1b — binder crossover.** When a claimed amount matches an in-window player's real WBA within ±$1, bind to that player rather than the merely-nearest name (the Jennings $35.01 / Darnold $9.11 / Bigsby $4.42 mechanism). Nearest-name binding remains the fallback when no amount-match exists.

Explicitly out of scope per D-X: Tier-2 policy (untouched — post-fix it correctly short-circuits genuine fabrication), and the 2019/2020 starvation suppression (Unit F2, assembly-side).

## 2. The fixture ground truth

The Stage B memo (`OBSERVATIONS_2026_07_02_FAAB_CLAIM_ATTRIBUTION_STAGE_B.md`) contains all 9 captured failure events with verbatim prose. These are the regression fixtures — real model output, real canonical amounts, classification founder-ratified. Transcribe them into test fixtures exactly as quoted. Post-fix required outcomes:

- The 8 false-positive events (3 H2p + 5 H3p) **pass** verification.
- The 1 genuine invention (Pitts $39, no matching record anywhere in window) **still fails**.

## 3. D-Z adversarial suite (written at Gate 1, before implementation)

Beyond the 9 fixtures, the test plan must include adversarial cases designed to prove the fix does not over-trust. Minimum set:

1. **Near-miss invention:** an invented amount within $2–$5 of a real in-window player's WBA (outside ±$1) → must fail.
2. **Amount-match, wrong attribution, player-scoped:** prose that *explicitly and unambiguously* attributes player A's real amount to player B by name ("KP grabbed Jennings for $35" when the $35.01 bid was on a different player and Jennings has no WBA) → must fail. The crossover rule applies to *binding ambiguity*, not to explicit false attribution — the test plan must state how the implementation distinguishes these (e.g., crossover rebinding only when the amount-matching player is themselves named within the window).
3. **Invented franchise total:** a franchise-total claim off by >$1 from the canonical derivation → must fail.
4. **Invented defense pickup:** a team-defense claim where that defense has no WBA record → must fail.
5. **The A7 smoke pair as fixtures:** "$11 Joe Burrow" / "$5 Kirk Cousins" (recorded in the Stage B memo's smoke section; neither player has WBA records) → must fail.
6. **Compound sentence:** one sentence containing a correct franchise total and an invented player amount → the invented claim must still fail.

If implementing F1a for any claim shape cannot meet its adversarial cases, that shape is dropped from this unit and recorded — under-fix, don't over-trust.

## 4. Procedure

**Step 0 — Ritual.** Fresh clone, HEAD recorded, identity check, standard trio green, prod DB hash recorded (read-only throughout; fixtures come from the Stage B memo and canonical derivations, not fresh generation).

**Step 1 — Test plan + design note (no implementation).** Write: (a) the fixture tests from §2, failing as expected against current code (red for the 8, red-for-the-right-reason confirmed for Pitts); (b) the adversarial suite from §3 with expected outcomes; (c) a one-page design note describing the claim-shape recognition approach, the crossover-rebinding condition, and precisely how adversarial case 2 is distinguished from legitimate crossover. No verifier edits yet.

**⛔ Gate 1 — Founder ratifies the test plan + design note.** The tests are frozen at ratification; implementation may not weaken, delete, or reinterpret them. New tests may be added during implementation; expected outcomes of ratified tests may not change.

**Step 2 — Implement.** Modify the FAAB_CLAIM logic in `recap_verifier_v1.py` per the ratified design. Keep the diff surgical: no drive-by refactors, no changes to other verifier categories.

**Step 3 — Prove.** Full trio green; all ratified fixtures and adversarial cases green; **verifier category-breakdown non-regression** per the reverify-as-merge-gate discipline (category-level SQL against the standard reverify corpus — FAAB_CLAIM failures should drop; every other category's counts must be unchanged); prove_ci exit 0 on the clean tree.

**Step 4 — Memo.** `_observations/OBSERVATIONS_2026_07_XX_UNIT_F1_FAAB_VERIFIER_FIX.md`: design note as implemented, fixture/adversarial results table, category non-regression evidence, any dropped claim shapes with reasons, explicit statement that Tier-2 and assembly were untouched.

**⛔ Gate 2 — Founder reviews the diff + memo; merge.** Present the full source diff. On approval: commit series per convention (source+tests commit, memo commit, STATE line commit; founder-written messages, no Co-Authored-By), one PR, `gh pr merge --squash` via CLI, verify on fresh main.

## 5. Acceptance criteria

- All 8 Stage B false-positive fixtures pass; Pitts $39 and every adversarial invention case fail; no ratified test's expected outcome changed post-Gate 1.
- Category-breakdown non-regression: only FAAB_CLAIM moves, downward.
- Diff confined to FAAB_CLAIM logic + tests; Tier-2 policy and assembly untouched (state the file:line span of the diff in the memo).
- Trio green; prove_ci exit 0; prod DB hash unchanged.
- Fix effect is NOT claimed as measured — the memo states that re-measurement is the separate pre-registered unit per D-Y.

## 6. Known hazards

- Directory confusion — identity test first.
- **The crossover loophole is the unit's central risk (D-Z):** adversarial case 2 is the test that keeps ±$1 amount-matching from becoming "any plausible dollar passes." If the distinction can't be implemented cleanly, drop F1b's rebinding to a narrower condition and record it.
- Fixture transcription: quote the Stage B memo's prose byte-exactly; a paraphrased fixture tests nothing.
- The franchise-total canonical source must be the same derivation assembly uses (`derive_faab_spending` path), not a reimplementation — two computations of "franchise FAAB spend" is how drift is born.
- prove_ci requires a clean working tree and adequate disk — check both before invoking.

## 7. Out of scope

Tier-2 policy · assembly/prompt changes (F2 is separate) · re-measurement (own pre-registered unit per D-Y) · other verifier categories · enum/doc updates (Unit A4) · any generation API calls.
