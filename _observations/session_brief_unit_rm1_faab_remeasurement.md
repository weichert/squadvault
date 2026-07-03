# Session Brief — Unit RM1: FAAB Fix Re-Measurement (Post-F1 Fresh-Generation Rate)

**Date authored:** 2026-07-02 (DECIDE session; D-Y ratified 2026-07-02; F1 landed `6778101`; F2 adjudicated tests-only at `5c3fc04`)
**Session type:** EXECUTE (Claude Code), two founder gates (⛔ Gate 1: pre-registration; ⛔ Gate 2: memo approval)
**Repo:** engine (`weichert/squadvault`) — confirm identity with `test -f scripts/recap_artifact_regenerate.py`
**Plan reference:** A7 baseline (memo at squash `1948de4`, frozen); D-B (n=24–36, pre-registered); D-Y (one re-measurement for the fix arc)
**Why now:** last unit of the FAAB arc; must land before live-cycle iteration begins (Week 1 ~09-08), and ideally before the 07-18 runbook trigger.

---

## Paste-ready kickoff prompt

> You are an EXECUTE session for SquadVault Unit RM1: the post-F1 fresh-generation re-measurement. Read `_observations/session_brief_unit_rm1_faab_remeasurement.md` in full before doing anything. Follow CLAUDE.md session ritual: fresh clone, `git log -1` to verify HEAD, repo identity via `test -f scripts/recap_artifact_regenerate.py`. Two-lane discipline: you execute; the founder adjudicates at the two ⛔ gates. **Hard rules: no pinned-sample generation until the pre-registration block is founder-ratified (Gate 1); the single smoke generation on a throwaway cell is permitted before Gate 1 and excluded from the eligible universe. The pinned sample may not be re-drawn after Gate 1 — an ineligible pinned cell is recorded INELIGIBLE_POST_PIN, never substituted. All generation runs against a scratch DB copy; prod hashed at start and end, unchanged. Production configuration measured as-is; no edits of any kind.** Nothing is published. The A7 baseline, Stage A/B memos, and F1/F2 memos are frozen history — read, never amend.

---

## 1. Objective

Measure the fresh-generation failure rate at current HEAD and compare it, category by category, against the frozen A7 baseline. The sole behavioral change between the baseline HEAD (`89d9321`) and current main is the Unit F1 verifier fix — F2 was adjudicated tests-only (no source change), and all other landed commits were docs. The measured delta therefore attributes to F1. The memo states this attribution basis explicitly, including the commit-range audit that proves it (Step 0).

Readouts identical to A7, pre-registered: R1 first-attempt category breakdown (category-breakdown SQL, never row-level) and R2 final-outcome distribution (pass-on-attempt-k / facts-only), plus R3 (new, pre-registered): the baseline-vs-RM1 category comparison table with FAAB_CLAIM highlighted.

## 2. Non-negotiable constraints

- Pre-registration before generation: full cell list, draw seed, model config, voice-profile state, and the R1/R2/R3 definitions written and founder-ratified before the first pinned API call.
- Fresh draw, new seed: seed = 20260702, n = 36 (founder may reduce to 24 at Gate 1 per D-B), drawn from the same eligible-universe definition as A7 (census re-run at current HEAD; do not reuse A7's census results — re-probe). The draw method is the A7 method: deterministic hash over (season, week, seed), exact code included in the block. The A7 smoke cell and this session's smoke cell are both excluded from the universe.
- Scratch DB; prod hash recorded at start/end, unchanged. Measurement drafts and prompt_audit rows never enter the real ledger.
- Production configuration as-is: model id read from `creative_layer_v1.py` at HEAD (expected `claude-sonnet-4-5-20250929` — verify), voice profile recorded (expected sha `3fdd8c95` — verify), retry loop as shipped, Tier-2 as shipped.
- ANTHROPIC_API_KEY via `set -a; source .env.local; set +a`; smoke one throwaway cell before Gate 1 to prove no facts-only key degradation.
- Scratch retention: scratch survives until the Gate 2 squash lands on main (the standing post-A7 rule).

## 3. Procedure

**Step 0 — Ritual + attribution audit.** Fresh clone, HEAD recorded, identity check, trio green, prod hash recorded. Then the commit-range audit: list every commit on main from `89d9321` (exclusive) to HEAD (inclusive) with one-line classification (source-behavioral / tests-only / docs-only). The audit must show F1's source commit as the only behavioral change; if any other behavioral commit appears, halt and escalate — the attribution premise fails.

**Step 1 — Scratch + smoke.** Copy DB, record hash, smoke a throwaway cell, confirm real generation + verifier + prompt_audit capture.

**Step 2 — Census.** Re-probe the eligible (season, week) universe on scratch (minus both smoke cells). Probe SQL + result verbatim for the memo.

**Step 3 — Pre-registration block (draft).** HEAD; scratch source hash; commit-range audit result; model id; voice sha; retry policy; seed 20260702; n=36; draw code; the drawn 36 cells in full; R1/R2/R3 definitions with the R1 and R3 SQL written before results exist. R3's comparison uses the A7 memo's committed R1 table as the baseline side — quoted, not recomputed.

**⛔ Gate 1 — Founder ratifies.** Block frozen; INELIGIBLE_POST_PIN is the only permitted deviation.

**Step 4 — Run.** 36 cells, sequential, no intervention; per-attempt category failures and final outcomes recorded; infrastructure retries noted, not counted.

**Step 5 — Readouts.** Pre-registered R1, R2, R3. Anything unregistered goes in a labeled exploratory appendix.

**Step 6 — Memo.** `_observations/OBSERVATIONS_2026_07_XX_UNIT_RM1_FAAB_REMEASUREMENT.md`: frozen block, census, R1/R2/R3 tables, the attribution statement with the commit-range audit, infrastructure notes, smoke record, and a counts-only plain reading. The memo may state whether the FAAB_CLAIM count moved and by how much; it may not claim causal mechanism beyond the audited attribution basis, and it may not declare the arc "done" — that adjudication is the founder's, in the DECIDE lane, on these numbers.

**⛔ Gate 2 — Founder approves; commit** (memo + STATE line, two-commit series per pattern; founder-written messages via `/tmp/msg.txt`, ASCII subjects, no Co-Authored-By; one PR, `gh pr merge --squash` via CLI). Scratch deleted only after the squash lands.

## 4. Comparison discipline

- Category-level only, both sides produced by the same breakdown SQL discipline. No row-level pass/fail comparisons.
- Expected shape, stated in advance for honesty, not as a success criterion: FAAB_CLAIM first-attempt count materially lower than A7's; all other categories within ordinary run-to-run variation. If any non-FAAB category moves sharply, that is a finding to report, not to explain away — the memo records it and the founder adjudicates whether it warrants attribution work.
- n=36 vs n=36 with different draws: the memo notes that cell-mix differences bound the comparison's precision, reports the two draws' season spreads side by side, and makes no significance claims.

## 5. Acceptance criteria

- Frozen block predates all pinned generation; commit-range audit present and clean.
- All 36 cells terminal (pass-on-k / facts-only / INELIGIBLE_POST_PIN); R1/R3 from pre-registered SQL.
- Prod hash unchanged; nothing published; repo diff = memo (+ STATE line).
- Trio green at session end; scratch retained until squash lands.

## 6. Known hazards

- Directory confusion — identity test first.
- Dead-key facts-only degradation — the smoke exists for this.
- Do not reuse A7's census, seed, or cell list — RM1 is a fresh draw by design; reusing the A7 cells would measure per-cell reproduction, not the rate.
- The A7 baseline numbers come from the committed A7 memo verbatim — never recomputed from surviving artifacts.
- Facts-only is its own R2 class, never counted as a pass.

## 7. Out of scope

Declaring the FAAB arc closed (founder adjudication on the numbers) · any prompt/verifier/assembly/policy edits · attribution of unexpected movements (separate unit if warranted) · the template-header ruling · Unit A4 · any fix work of any kind.
