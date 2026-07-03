# Session Brief — Unit P1: Non-FAAB Attribution Probe (SUPERLATIVE / SCORE_VERBATIM / STREAK)

**Date authored:** 2026-07-02 (DECIDE session; ratified 2026-07-02 with the deferral amendment; FAAB arc closed same date)
**Session type:** EXECUTE (Claude Code), one founder gate (⛔ Gate 1: memo approval)
**Repo:** engine (`weichert/squadvault`) — confirm identity with `test -f scripts/recap_artifact_regenerate.py`
**Plan reference:** RM1 memo (squash `8007dff`); Stage A precedent (`9571885`); founder deferral ruling: probe outcomes (a) and (b) are automatically deferred past Week 1 (~09-08) unless the founder explicitly reopens them
**Why:** RM1 showed the post-F1 facts-only rate (52.8%) is driven by retry exhaustion on SUPERLATIVE (15), SCORE_VERBATIM (14), and STREAK (12). Stage B proved the dominant FAAB fault was the verifier rejecting true statements; this probe asks the same question of the remaining categories before the season starts — purely informational, no calendar deadline.

---

## Paste-ready kickoff prompt

> You are an EXECUTE session for SquadVault Unit P1: the non-FAAB attribution probe. Read `_observations/session_brief_unit_p1_nonfaab_attribution_probe.md` in full before doing anything. Follow CLAUDE.md session ritual: fresh clone, `git log -1` to verify HEAD, repo identity via `test -f scripts/recap_artifact_regenerate.py`. Two-lane discipline: you execute; the founder adjudicates at Gate 1. **Hard rules: diagnosis-only — no edits to verifier, prompts, policy, data layer, or any source file; prod DB read-only, hashed at start and end, unchanged; zero generation API calls.** All committed memos (A7, Stage A/B, F1, F2, RM1) are frozen history — read, never amend. The RM1 scratch was deleted after its squash: rejected prose does not exist; work only from committed memos, code at HEAD, and prod data, and say "indeterminate without prose" where that is the truth. Silence over speculation throughout.

---

## 1. Objective

For each of SUPERLATIVE, SCORE_VERBATIM, and STREAK, establish from code and committed data what can be established deterministically:

- **Mechanism reading:** what the check compares, against what canonical source, with what tolerance/normalization — and whether there exist true-statement shapes the check structurally cannot represent or over-strictly rejects (the FAAB-binder sibling question). Cite `file:line` at HEAD.
- **Source-alignment check:** whether the canonical strings/values the check compares against are the same ones assembly surfaces to the prompt (the Stage A structural test that ruled FAAB H2-by-value out). Misalignment is the strongest deterministic signal of verifier-side fault.
- **Variance sub-readout (pre-registered):** from the RM1 memo's per-cell records — per-cell failure concentration for each category (spread vs. piled), and the A7-vs-RM1 cell-mix comparison for the categories that moved (SUPERLATIVE +5, STREAK −3, DRAFT_AUCTION_DOLLAR −3), reported as counts with no significance claims. This answers "draw artifact or real" to the extent counts can.
- **Per-category verdict**, one of: verifier-side fault identified (structural, cited) · model-side plausible with verifier structurally sound · indeterminate without prose.

## 2. Non-negotiable constraints

- **Read-only everywhere:** prod hashed at start/end, opened `mode=ro`; zero API calls; no source edits; repo diff at end = memo (+ STATE line per the established two-commit pattern).
- **Evidence provenance:** every data claim cites its SQL + verbatim result; every code claim cites `file:line` at recorded HEAD; RM1/A7 numbers quoted from committed memos, never recomputed.
- **Prior-work reuse:** the historical superlative and streak diagnosis memos in `_observations/` (the 2026-04/05 prose-classification work) may be cited as background but not treated as current-HEAD evidence — the verifier has changed since; re-read the code.
- **No fix design:** verdicts name mechanisms and layers only. The stopping rule (§4) governs what happens next.
- **Census-first:** no assumed week ranges, season scopes passed explicitly.

## 3. Procedure

**Step 0 — Ritual.** Fresh clone, HEAD recorded, identity check, trio green, prod hash recorded.

**Step 1 — Code reading.** The three checks in `recap_verifier_v1.py`: comparison logic, canonical sources, tolerances, known structural gaps. Then the assembly side for each: what the prompt actually receives for superlative/score/streak content, and whether it is pre-rendered canonical text (per the four-step playbook history) or free material the model rephrases.

**Step 2 — Data probes.** The variance sub-readout from the RM1 memo's per-cell records; the source-alignment probes on prod (read-only) for any comparison the code reading flags as suspect.

**Step 3 — Verdicts.** Per category, one of the three §1 verdicts, evidence-cited. Where "indeterminate without prose," state exactly what a Stage-B-style capture would need.

**Step 4 — Memo.** `_observations/OBSERVATIONS_2026_07_XX_UNIT_P1_NONFAAB_ATTRIBUTION_PROBE.md`: hashes, code findings with line refs, probe SQL + results, variance tables, per-category verdicts, and a closing that is strictly one of the §4 stopping-rule outcomes. Exploratory material in a labeled appendix.

**⛔ Gate 1 — Founder approves; commit** (memo + STATE line, two-commit series, founder-written messages via `/tmp/msg.txt`, ASCII subjects, no Co-Authored-By, one PR, `gh pr merge --squash` via CLI).

## 4. Stopping rule (pre-committed, founder-ratified)

The memo's closing is exactly one of:

- **(a) Fix unit scopeable** — a verifier-side structural fault as clean as the FAAB binder finding, cited. Auto-deferred past Week 1 unless the founder explicitly reopens.
- **(b) Prose capture needed** — indeterminacy that only a Stage-B-style run resolves, with the capture list. Auto-deferred past Week 1 unless the founder explicitly reopens.
- **(c) Accept the rate** — the checks are structurally sound and the facts-only rate is the model's honest ceiling under current config; the season starts there, constitutionally safe.

The deferral in (a)/(b) is part of this ratification: the probe is the last pre-season information-gathering act, not the first step of a new fix arc.

## 5. Acceptance criteria

- Prod hash unchanged; zero API calls; repo diff = memo (+ STATE line); trio green at session end.
- All three categories carry a verdict with cited evidence; the variance sub-readout is present with both concentration and cell-mix tables.
- The closing is exactly one stopping-rule outcome; no fix design anywhere.

## 6. Known hazards

- Directory confusion — identity test first.
- The RM1 memo is the sole source for per-cell records — quote its rows explicitly; the grep-style misread that produced the false DoR carry-forward is the standing cautionary example.
- SUPERLATIVE has deep prior history (the 2026-04/05 memos) — background only; the code at HEAD governs.
- Do not conflate "category count moved between draws" with "mechanism changed" — the cell-mix table exists precisely to keep those apart.

## 7. Out of scope

Executing outcome (a) or (b) · re-running any measurement · amending any frozen memo · the template-header ruling · Unit A4 · Tier-2 policy · any fix work of any kind.
