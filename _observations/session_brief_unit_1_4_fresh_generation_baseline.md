# Session Brief — Unit A7 (Unit 1.4): Fresh-Generation Failure-Rate Baseline

**Version:** v1.1 (amended against HEAD c344c58; see Amendment Log)
**Date authored:** 2026-07-01 (DECIDE session, Completion Plan v1.3 Window A)
**Session type:** EXECUTE (Claude Code), with two founder gates marked GATE below
**Repo:** engine (`weichert/squadvault`) — confirm identity with `test -f scripts/recap_artifact_regenerate.py`
**Plan reference:** Completion Plan v1.3, Unit A7; D-B (n=24-36, pre-registered); closure-cert-6 evidence
**Why now:** this is the only remaining unit with a hard calendar reason — the baseline must be measured **before** live-cycle voice/prompt iteration begins (Week 1 ~09-08), or the pre-season control is contaminated. Runbook trigger fires 07-18.

---

## Amendment Log (v1.0 draft -> v1.1)

Verified against HEAD `c344c58` on 2026-07-01 (DECIDE-lane clone). Two corrections; everything else unchanged.

1. **Category enum corrected (R1).** The v1.0 draft listed 8 verifier categories. `recap_verifier_v1.py` at HEAD emits **14**: SCORE, SUPERLATIVE, STREAK, SERIES, BANNED_PHRASE, PLAYER_SCORE, PLAYER_FRANCHISE, FAAB_CLAIM, CHAMPIONSHIP_CLAIM, SEASON_RECORD_CLAIM, PLAYER_AVG_CLAIM, NUMERIC_UNANCHORED, PLAYER_STREAK_CLAIM, DRAFT_AUCTION_DOLLAR. R1's pre-registered SQL must `GROUP BY category` with **no category filter** so the readout reflects whatever the verifier actually emits.
2. **R2 outcome classes corrected for tier-aware retry.** The lifecycle at HEAD is not a flat 3-attempt loop: `_NO_RETRY_CATEGORIES = frozenset({"FAAB_CLAIM", "NUMERIC_UNANCHORED"})` short-circuits directly to facts-only (Phase C tier policy — retries cannot self-correct those categories). R2 therefore distinguishes **facts-only (Tier-2 short-circuit)** from **facts-only (3 attempts exhausted)**. Retry temperatures step down `[default, 0.5, 0.3]`.

Config facts pinned at HEAD (record verbatim in the pre-registration block, then re-verify against the fresh clone's HEAD at session start):

- Generation model: `claude-sonnet-4-20250514` (`src/squadvault/ai/creative_layer_v1.py:25`, `_MODEL`)
- Retry cap: `_MAX_VERIFICATION_RETRIES = 3` (`src/squadvault/recaps/weekly_recap_lifecycle.py`)
- Retry temperatures: `[None (default), 0.5, 0.3]`
- No-retry categories: `FAAB_CLAIM`, `NUMERIC_UNANCHORED`
- Voice profile: **DB state, not repo config** — read at generation time via `get_voice_profile(db_path, league_id)` (`squadvault.core.tone.voice_profile_v1`). The pre-registration block records its value as probed from the **scratch DB**.
- Missing-key behavior: silent facts-only fallback with RuntimeWarning (`creative_layer_v1.py`) — the smoke step exists to catch this.

If the fresh clone's HEAD differs from `c344c58`, re-verify every pinned fact above before drafting the pre-registration block; git is authoritative over this brief.

---

## Paste-ready kickoff prompt (start the fresh session with this)

> You are an EXECUTE session for SquadVault Unit A7 (Unit 1.4): the pre-registered fresh-generation failure-rate baseline. Read `_observations/session_brief_unit_1_4_fresh_generation_baseline.md` in full before doing anything. Follow CLAUDE.md session ritual: fresh clone, `git log -1` to verify HEAD, confirm repo identity via `test -f scripts/recap_artifact_regenerate.py`. Two-lane discipline applies: you execute; the founder adjudicates at the two GATE points. **Hard rule: no pinned-sample generation call is made until the pre-registration block is written, shown to the founder, and ratified (Gate 1); the single smoke generation on a throwaway cell (Step 1, constraint 6) is explicitly permitted before Gate 1 and is excluded from the eligible universe. The pinned sample may not be re-drawn after Gate 1 for any reason** — if a pinned cell proves ineligible, record it as `INELIGIBLE_POST_PIN` in the results; do not substitute. Facts are immutable; this measurement runs against a scratch copy of the DB; nothing is published; silence over speculation throughout.

---

## 1. Objective

Produce the pre-season baseline measurement of the fresh-generation failure rate: what fraction of freshly generated weekly recaps fail verification on the **first attempt**, broken down by **verifier category**, and what the **final-outcome distribution** is after the tier-aware retry loop. This is closure-certification-6 evidence and the clean control against which in-season voice iteration will later be compared.

Two readouts, both pre-registered:

- **R1 — First-attempt category breakdown.** Counts by verifier category across the n first attempts, over the **full 14-category enum at HEAD** (no filter; see Amendment Log). Use the category-breakdown SQL discipline from `reverify_prompt_audit` — **never** row-level pass/fail counts (row-level conflates legacy drift with current behavior).
- **R2 — Final-outcome distribution.** For each of the n cells, exactly one of:
  1. passed on attempt 1
  2. passed on attempt 2
  3. passed on attempt 3
  4. facts-only — Tier-2 short-circuit (first hard failure in a no-retry category)
  5. facts-only — 3 attempts exhausted
  6. `INELIGIBLE_POST_PIN`

  Record the triggering category for outcomes 4 and 5.

## 2. Non-negotiable constraints

1. **Pre-registration before generation.** The complete sample (every (season, week) cell), the draw seed, the model configuration in force, and the voice-profile state are all written down and founder-ratified **before the first API call**. No re-draws, no substitutions after ratification.
2. **Scratch DB.** Copy the production engine DB to a scratch path (e.g. `cp .local_squadvault.sqlite /tmp/unit14_scratch.sqlite`) and point the lifecycle at the copy. The 24-36 measurement drafts and their prompt_audit rows do not enter the real ledger. Record the production DB's file hash in the memo so the fact-state the measurement ran against is pinned. *(Default ratified in this brief: scratch copy. If the founder prefers the real DB — unapproved drafts are legitimate append-only lifecycle artifacts — that is a Gate 1 override, not an EXECUTE choice.)*
3. **Production configuration, measured as-is.** No prompt edits, no verifier edits, no special flags. The generation model, prompt assembly, retry loop, and voice-profile state are whatever HEAD + current config + current DB state produce. The voice profile is read from the scratch DB at generation time; its value is recorded, not altered.
4. **Census-first eligibility.** Before drawing, probe the scratch DB for the eligible cell universe: (season, week) cells where the golden-path inputs for a weekly recap exist and are complete. Read actual SQL results; do not assume week ranges per season. Show the founder the eligible-universe count in the Gate 1 block.
5. **Nothing is published.** No approval, no distribution, no artifact regeneration against prod paths.
6. **ANTHROPIC_API_KEY must be set** (`set -a; source .env.local; set +a` pattern). If generation silently falls back to facts-only for a missing key (the known RuntimeWarning degradation), the run is invalid — check for the warning on a single smoke cell **before** Gate 1, using a throwaway cell that is then excluded from the eligible universe for the draw.

## 3. Procedure

**Step 0 — Ritual.** Fresh clone, verify HEAD (`git log -1`), repo identity check, install, run the standard trio (ruff CI-scope, mypy CI invocation, pytest) to confirm a green base. Record HEAD hash — it goes in the memo. If HEAD != `c344c58`, re-verify the Amendment Log's pinned config facts against actual source.

**Step 1 — Scratch DB + smoke.** Copy the DB; record `shasum` of the source. Run one smoke generation on a throwaway cell against the scratch DB to prove: API key live (no facts-only warning), lifecycle writes land in scratch, verifier + retry loop engage, prompt_audit rows appear. Note the throwaway cell — it is excluded from the draw.

**Step 2 — Census.** SQL probe of the eligible (season, week) universe on scratch (minus the smoke cell). Save the probe SQL and its result verbatim for the memo. Probe and record the voice-profile value (`get_voice_profile`) from the scratch DB here.

**Step 3 — Pre-registration block (draft).** Write, in the observation memo skeleton:
- HEAD hash; scratch-DB source hash; generation model id (confirm `_MODEL` in `src/squadvault/ai/creative_layer_v1.py` — do not guess); voice-profile state (value or NONE, as probed in Step 2); verifier version reference (full 14-category enum); retry policy in force (cap 3, temperatures `[default, 0.5, 0.3]`, no-retry categories `FAAB_CLAIM`/`NUMERIC_UNANCHORED`).
- Draw procedure: seeded deterministic draw of **n = 36** cells (founder may reduce to 24 at Gate 1 for API budget; D-B permits 24-36) from the eligible universe, seed = `20260701`, method = `ORDER BY` over a deterministic hash of (season, week, seed) with the exact SQL included. Stratification: none — a flat seeded draw over the eligible universe is simpler to defend; the memo will report the drawn cells' season spread so any era skew is visible rather than corrected.
- The drawn cell list itself, in full.
- The two readout definitions (R1, R2 with the six outcome classes) and the category-breakdown SQL that will produce R1, written **now**, before results exist.

**GATE 1 — Founder ratifies the pre-registration block.** Show the block verbatim. Founder confirms: n, seed, cell list, scratch-DB choice, config-as-is. After ratification the block is frozen. `INELIGIBLE_POST_PIN` is the only permitted deviation, and it is recorded, not repaired.

**Step 4 — Run.** Generate the n cells sequentially against scratch. For each: record attempt count, per-attempt verifier failures by category, tier of first hard failure (if any), final outcome. No intervention mid-run; if a run errors for infrastructure reasons (network, rate limit), retry the *infrastructure* step and note it — infrastructure retries are not verification attempts.

**Step 5 — Readouts.** Execute the pre-registered R1 SQL and assemble R2. No post-hoc metric additions; anything interesting-but-unregistered goes in a clearly labeled "exploratory, not pre-registered" appendix.

**Step 6 — Memo.** `_observations/OBSERVATIONS_2026_07_XX_UNIT_1_4_FRESH_GENERATION_BASELINE.md` containing: the frozen pre-registration block, the census probe + result, R1 table, R2 table, infrastructure notes, the smoke-cell record, and a one-paragraph plain reading (counts only — no speculation about causes; attribution work is a separate unit if warranted, per the Phase-2 failure-rate-attribution precedent).

**GATE 2 — Founder approves the memo; commit.** One commit, doc-only (`_observations/` — never repo root), founder-written message per convention (`git commit -F /tmp/msg.txt`, ASCII-only subject). Scratch DB may be deleted after the memo commit or retained at founder's preference (default: delete; the memo's hashes and SQL make the run reconstructable).

## 4. Acceptance criteria

- Pre-registration block exists in the committed memo and demonstrably predates results (frozen at Gate 1, unchanged after).
- R1 is produced by the pre-registered category-breakdown SQL over the full category enum, not row-level counts and not a filtered subset.
- All n cells accounted for in exactly one R2 outcome class (pass-on-k, facts-only short-circuit, facts-only exhausted, or INELIGIBLE_POST_PIN).
- Production DB untouched (hash unchanged); no published artifacts; repo diff is the memo file only.
- Standard trio still green at session end.

## 5. Known hazards for this session

- H3: both clones prompt `squadvault %` — run the identity test before anything else.
- The facts-only fallback is *silent but warned* — the smoke step exists precisely to catch a dead key before the pinned run.
- Tier-2 short-circuit means some cells legitimately never reach attempt 2 — do not misread these as retry-loop failures or count their absence of attempts 2-3 as anomalous.
- `.md` auto-linking corrupts pasted bytes — write the memo via the heredoc `pathlib.Path.write_text()` pattern, not chat paste.
- Do not let any facts-only fallback be counted as a "pass" — outcomes 4 and 5 are their own R2 classes.

## 6. Out of scope

Failure attribution / root-causing (separate unit if counts warrant) · any prompt, verifier, or voice changes · re-running with alternate configs · publishing anything · Unit A8, CO.3, or any other Window A/B unit.
