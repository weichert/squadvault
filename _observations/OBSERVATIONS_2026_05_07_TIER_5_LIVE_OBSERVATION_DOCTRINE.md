# OBSERVATIONS — Tier 5 live observation cadence doctrine v1.0

**Drafted:** 2026-05-07.
**HEAD at draft:** `09598b3` (post-`6740014` Tests/ ruff cleanup non-finding closure; post-`09598b3` `d['raw_mfl']` dead-stash deletion).
**Phase:** 10 — Operational Observation.
**Position in plan:** Concretizes the Tier 5 W14+ live observation cadence placeholder referenced as "active-next-focus" through `50e3141`, `16d4a1b`, and `d8ac8b1` closure memos and through two predecessor session briefs without ever being formally defined. Doc-only; v1.0 of an evolving doctrine.

---

## 1. TL;DR

**Filing decision.** This memo lands in `_observations/` rather than `docs/50_ops_and_build/` because the doctrine is v1.0 and unvalidated against any real W14+ cycle. Operational doctrine that may refine in response to its first empirical exercise belongs in the lower-friction `_observations/` track, versioned by memo date. Promotion to `docs/50_ops_and_build/Tier_5_Live_Observation_Cadence_v1_0.md` is gated on one or two real W14+ 2026 cycles validating the cadence empirically (per §9 below).

**What Tier 5 is.** Tier 5 is an operational track — not a thread, not a session brief, not a feature — that exercises three pieces of durable diagnostic infrastructure shipped during the 2026-05-06/07 arc against freshly-captured `prompt_audit` rows from new recap-generation passes. Its purpose is to surface re-activation signals for closed/deferred threads (Section 10 Q1 Bug 1, SCORE_VERBATIM legacy-drift, player-streak verb inversion, and others) as those signals appear in live W14+ play, before they accumulate as silent quality drift. The track is forward-looking by design: it operates on data captured after the doctrine's ship date, not on retrospective corpus replay.

**The placeholder problem this memo solves.** "Tier 5" was reified across three closure memos and at least two predecessor session briefs without ever being concretely scoped. The post-§10 Q1 development direction memo it pointed to did not exist as a discoverable artifact. `_observations/` and `docs/` contained no doctrine memo. The Operational Plan v1.1 documented Track A through Track D but no Tier 5. The pattern is the same shape as the "59 rows" figure surfaced in `16d4a1b` §11 — named concepts that are not verified at every reference drift the same way that quantitative figures drift. This memo ends the placeholder status. The act of writing it is the closure of a doctrine-shape gap that has been carried as named-only since at least 2026-05-04.

---

## 2. What "live observation" means concretely

Live observation is a specific operational practice, distinguished from two adjacent practices that already have shipped infrastructure:

**Corpus replay** (the SCORE_VERBATIM Step 0 probe shape at `2e05884`): runs a diagnostic against the historical artifact set. Output is era cross-tabs against ship-date boundaries. The probe's `POST_FIX_TO_PRESENT` bucket is by-construction-impossible under helper-bound discipline; non-zero hits surface helper drift. Corpus replay is *retrospective* — it inspects rows captured before the diagnostic existed.

**Retrospective reverify** (the `--baseline-tag` enhancement at `d8ac8b1`): replays current verifier rules against the past `prompt_audit` corpus and computes per-category baseline-vs-current deltas. Output is the category-NEW verdict that lets a merge gate distinguish legacy drift from real regression. Retrospective reverify is *forward-pointing-but-historical* — its corpus is the past, but its purpose is to make future verifier-rule changes safer.

**Live observation** is neither. Tier 5 cycles operate on `prompt_audit` rows captured after the doctrine's ship date (2026-05-07). The trigger is operational: a new recap-generation pass produces a new `prompt_audit` row, which becomes a candidate for inspection if its (season, week) falls in the cycle's activation surface (§3 below). The three diagnostic tools are exercised against the live row. The cycle's output goes to a memo. The cycle terminates either log-and-close (no signal) or spawn-a-thread (signal fires per §6).

The trigger condition formally: a new approved-or-attempted recap (any `prompt_audit` row regardless of `verification_passed`) with `captured_at >= 2026-05-07` AND `(season, week)` in the season currently being processed.

---

## 3. When Tier 5 activates

The "W14+" semantic in the term name is intentional but not exclusionary. Weeks 14 and beyond are the playoff stretch where the narrative-richness signals Tier 5 is built to detect concentrate most heavily: record-claim eligibility peaks (record-approach and record-tying detector hits cluster in late season), season-storyline weight is heaviest (T8/T9/T10 streaks have had time to accumulate), and retry pressure is highest (T9-LOSS at strength=2 competes with HEADLINE-budget pressure most acutely when many high-strength angles also fire).

The doctrine adopts a tiered activation rather than a hard gate:

- **W14 through end-of-season (including playoffs and championship week): full cycle.** Every captured `prompt_audit` row inside this window triggers a cycle. Cycle memos are mandatory.
- **W11 through W13: opportunistic.** A cycle fires if a captured row exhibits a noteworthy signal during the cycle commissioner's normal review. Scheduled cycles do not run.
- **W1 through W10: backlog-only.** Tier 5 does not initiate cycles for early-regular-season weeks. If a future cycle's diagnostic incidentally surfaces a W1-W10 specimen (for example via a cross-season scan that matches an early-week historical row to a live signal), that specimen feeds the relevant thread but does not retroactively constitute a cycle.

The pre-W14 priority is not exclusion. The brief's framing of "lower priority but not excluded" is correct; the tiered activation above codifies it.

---

## 4. The Tier 5 toolkit

Three pieces of durable diagnostic infrastructure shipped during the 2026-05-06/07 arc constitute the Tier 5 toolkit. Each is specified below by its position in a cycle, its expected output, the re-activation criterion it encodes, and its single-paste invocation.

### 4.1. Bug 1 generation/eviction classifier

- **Source:** `scripts/step_1_streak_diagnostic_harness.py`, scope `classify-bug1-specimens` (shipped at `6329ae9`, six-bucket schema per `50e3141` §1).
- **Position in cycle:** runs first when a captured row's (season, week) is W14+ and the row's narrative_angles_text contains a T9-LOSS-eligible angle (or its omitted-tail signal).
- **Output:** six-bucket distribution: `GENERATED_AND_SURFACED`, `GENERATED_AND_BUDGETED_NOT_SURFACED`, `EVICTION_LIKELY`, `NOT_GENERATED_POST_HELPER`, `NOT_GENERATED_PRE_HELPER`, `NO_AUDIT_DATA`.
- **Re-activation criterion:** `EVICTION_LIKELY ≥ 1` for a non-Brandon franchise → promote Section 10 Q1 Bug 1 to Step 1 production-path immediately (the 2-and-2 threshold's "two distinct franchises" bar is met by Brandon W14 2025 plus any one new specimen). The Step 1 design surface is preserved at `50e3141` §5.
- **Current scope limitation (Q5 named-only follow-on):** the classifier is hardcoded to the 13 historical specimens `_BUG_1_SPECIMENS`. Live W14+ cycles need a current-week discovery extension (a new scope variant operating on `(season, week, fid)` tuples discovered live). This is documented as a follow-on in §10 below. Until shipped, the classifier runs as designed against the 13 historical specimens; any live W14+ specimen requires a manual scope extension at cycle time.
- **Invocation:**

      PYTHONPATH=src python scripts/step_1_streak_diagnostic_harness.py \
        --db .local_squadvault.sqlite \
        --league-id 70985 \
        --scope classify-bug1-specimens

### 4.2. SCORE_VERBATIM era cross-tab probe

- **Source:** `scripts/diagnose_score_verbatim_drift.py` (shipped at `2e05884`, four-bucket schema per `16d4a1b` §1).
- **Position in cycle:** runs second, against the most recent reverify tag if one has been minted since the prior cycle, OR at end-of-cycle if no new tag exists.
- **Output:** four-bucket distribution (`ALL_LEGACY_HYPHEN`, `MIXED_LEGACY_AND_NO_SCORE`, `ALL_NO_SCORE`, `POST_FIX_TO_PRESENT`) with era cross-tab against the Wave 1 ship date (2026-05-03).
- **Re-activation criterion:** either signal from `16d4a1b` §8 — `POST_FIX_TO_PRESENT > 0` (verifier or helper drift; investigate immediately), OR a post-Wave-1 row appears in the failing set with `original_passed=1` (real regression in approved prose; promotes back to actionable thread). Per `16d4a1b` §11, the probe's automatic verdict logic is too conservative on its own; the cycle commissioner reads the per-row `orig` column alongside the bucket count.
- **Invocation:**

      PYTHONPATH=src python scripts/diagnose_score_verbatim_drift.py \
        --db .local_squadvault.sqlite \
        --verifier-tag <current_or_baseline_tag>

### 4.3. Reverify category-attribution gate

- **Source:** `scripts/reverify_prompt_audit.py` with `--baseline-tag` (shipped at `d8ac8b1`).
- **Position in cycle:** runs third, at the cycle's gate boundary (before any thread-promotion decision is committed to the memo).
- **Output:** per-category baseline-vs-current delta + category-NEW verdict, replacing the manual category-breakdown SQL workaround.
- **Re-activation criterion:** any `category-NEW > 0` → investigate per the named category. The category dimension distinguishes "this is the legacy-drift cohort we already know about" from "this is a new failure shape that did not exist at the baseline."
- **v1.0 baseline tag:** `59846b0`. This is the most recent post-Wave-1 verifier-clean state at doctrine ship date and is the natural baseline against which Tier 5 cycles reverify-compare.
- **Baseline rotation rule:** the baseline tag rotates when a verifier-extension thread closes AND a fresh reverify run against the prior baseline confirms zero `category-NEW`. The post-rotation baseline is the new tag. Doctrine v1.X memos record each rotation explicitly with the prior tag, the new tag, the closing thread, and the zero-delta confirmation reverify run.
- **Invocation:**

      PYTHONPATH=src python scripts/reverify_prompt_audit.py \
        --db .local_squadvault.sqlite \
        --baseline-tag 59846b0

### 4.4. Toolkit composition (Framing B deferred mid-session)

The three tools above can be exercised independently or composed into a single-paste cycle via an activation wrapper at `scripts/run_tier_5_cycle.py`. The wrapper would take a baseline date and run all three diagnostics in sequence, printing the union of their outputs.

The decision on whether to ship the wrapper this session depends on whether §4.1–§4.3 read as one-tool-three-modes or three-separate-tools. As written, the three tools have distinct scopes, distinct DB shapes, and distinct re-activation criteria; they share only the live-W14+-row trigger. That reads as three-separate-tools-that-share-a-trigger, not one-tool-three-modes. The wrapper would primarily save typing rather than simplify mental model. Per the brief's §2 default ("if §4 makes the toolkit feel like three separate tools that happen to be related, the wrapper is over-engineering"), Framing B is deferred to a follow-on session, gated on whether the first real W14+ 2026 cycle reveals friction in the manual three-paste form.

---

## 5. Per-cycle cadence and memo discipline

**Trigger-based, not calendar-based.** A Tier 5 cycle fires when a captured `prompt_audit` row matches the trigger condition in §2 and the activation tier in §3 calls for a full cycle. The cycle does not run on a fixed weekly or monthly schedule.

**Mandatory end-of-W14+-window retrospective.** At the end of each season's W14+ window (post-Super-Bowl-week), a Tier 5 retrospective memo runs whether or not cycles fired during the window. The retrospective records: number of cycles run, signal-fire count per §6 thread, threads promoted to actionable, and any toolkit-coverage gaps surfaced. This catches the no-findings-equals-no-memo failure mode that would otherwise let Tier 5 fall silent without acknowledging it had run at all. Precedent: Operational Plan v1.1 §9.3 self-evaluation cadence pattern (phase-end retrospectives).

**Per-cycle artifacts.** A single observation memo per cycle, named `OBSERVATIONS_<YYYY_MM_DD>_TIER_5_<descriptive_tag>.md`. The memo records:

- HEAD at run, plus toolkit-file SHA-256 hashes (anchor to known production state).
- The captured `prompt_audit` row IDs inspected.
- Each toolkit's output, with the actual output captured to `/tmp/` and referenced by path in the memo body.
- Bucket distributions or delta tables per tool.
- Decision verdict per §7 below: log-and-close vs spawn-thread.
- If a thread is spawned, the follow-on session brief is drafted as a separate doc commit, not embedded in the cycle memo.

**Batching rule.** If two captures arrive in rapid succession within a single review window (commissioner-defined; default 24 hours), they batch into one cycle's memo with separate sections per capture. This prevents memo-per-row inflation while preserving per-capture traceability.

---

## 6. Re-activation criteria, consolidated

The following table consolidates every closed/deferred thread with a Tier 5-detectable re-activation signal as of doctrine ship date. Each row names the thread, the signal that fires re-activation, the toolkit piece (or manual inspection step) that detects it, and the action the cycle commissioner takes when the signal fires.

| Thread | Signal | Detected by | Action |
|---|---|---|---|
| Section 10 Q1 Bug 1 (HEADLINE budget eviction) | `EVICTION_LIKELY ≥ 1` for non-Brandon franchise | §4.1 classifier (with current-week extension per Q5) | Promote to Step 1 production-path; ship helper + budget reservation per `50e3141` §5 |
| SCORE_VERBATIM legacy-drift | `POST_FIX_TO_PRESENT > 0` OR post-Wave-1 row with `original_passed=1` | §4.2 probe | Investigate verifier/helper drift OR real regression per `16d4a1b` §8 |
| Player-streak verb inversion (per `OBSERVATIONS_2026_05_06_PLAYER_STREAK_VERB_DIAGNOSTIC.md` §148) | Any `DIRECTION_INVERSION` / `FRANCHISE_MISMATCH` / `THRESHOLD_INVERSION` / `TENURE_NON_CONSECUTIVE` on a current-week T9-LOSS / T8 / T10 / tenure detector hit | Manual prose inspection + harness re-run against the live row's (season, week) | Promote standing-backlog #5 to actionable four-step thread per the predecessor diagnostic brief |
| Cat 3c row-76 attribution edge case | New W14+ row exhibits paragraph-end record-claim with no possessive subject before AND wrong franchise label in the verifier's output | Manual prose inspection during cycle | Re-investigate sentence-boundary or anaphora resolution shape; deferred — affects label only, not detection |
| Snap-outcome detection (named-only) | Captured prose makes a snap-outcome claim (a play-resolution claim with no canonical-event anchor) | Manual prose inspection during cycle | Promote to scoped detection-spec session |
| NOTABLE-pass alphabetical lockout (named-only) | NOTABLE-cap-saturated row where the alphabetical lockout pattern (consistent first-alphabetical winner across multiple weeks' NOTABLE pass) is visible in prose | Manual prose inspection during cycle | Promote to scoped budget-pass session |

The table is the operational-readiness surface §6 of the doctrine specifies. New deferred threads add rows; thread closures remove them. The doctrine v1.X iteration mechanism (§9) ensures the table stays current.

---

## 7. Boundary: observation vs investigation

The diagnostic-first principle and the silence-over-speculation principle together frame the boundary between "this cycle terminates" and "this cycle spawns work."

**Cycle terminates (log-and-close)** when:

- All three toolkit outputs cleared (no signal fires per §6 table), OR
- A signal fires but raw-prose inspection per the cycle commissioner contradicts the automatic verdict (the `16d4a1b` §11 lesson — the probe's verdict logic is read alongside the per-row evidence, not in isolation), AND the contradiction is documented in the memo with the specific evidence.

**Cycle spawns a four-step playbook session** when:

- Any §6 signal fires AND the raw-prose inspection corroborates the automatic verdict, AND
- The fired signal's table-row "Action" column names a thread with an existing predecessor (`50e3141`, `16d4a1b`, the player-streak diagnostic brief, etc.), so the follow-on session has a documented design surface to start from.

**Diagnostic-first holds inside the cycle.** No production-path code change happens in a Tier 5 cycle memo. The cycle is read-only. Any production-path work is the spawned session, gated on its own brief, gates, and merge criteria.

**Silence-over-speculation holds at decision boundaries.** If a signal's interpretation is ambiguous, the memo records both readings and defers; it does not force a verdict. Ambiguity is a finding in itself and is named as such. The cycle commissioner does not invent confidence to close ambiguous signals.

---

## 8. Pre-W14+ activation conditions

The 2025 NFL fantasy season is over as of doctrine ship date. The 2026 NFL season's W14 will not arrive until late November 2026. Tier 5's first real cycle is therefore approximately six months away.

This memo ships months ahead of its first real exercise. That gap is acknowledged here rather than papered over. The doctrine's §9 explicitly contemplates v1.1 / v1.2 refinements after empirical validation; what follows is the zero-cycle baseline operational state.

**What to do now (zero-cycle baseline):**

- Pin `59846b0` as the v1.0 reverify baseline tag (per §4.3). The pin is recorded in this memo and persists until the rotation criterion fires.
- Spot-check toolkit hashes at session start of any session that touches `scripts/diagnose_score_verbatim_drift.py`, `scripts/reverify_prompt_audit.py`, or `scripts/step_1_streak_diagnostic_harness.py`. The doctrine memo's §4 hashes are the anchor.
- Smoke-test the three-tool pipeline against the current 142-row reverify corpus once during the pre-W14+ period (no later than 2026-08-01) to confirm end-to-end runnability. Smoke-test memo not required; a captured `/tmp/` output and a memory note are sufficient.
- Document any tooling gaps surfaced by the smoke test as named-only follow-ons in the standing backlog (§10 here).

**What triggers the first real cycle:**

- First captured `prompt_audit` row with `(season, week) >= (2026, 14)` AND `captured_at >= 2026-05-07`. The cycle commissioner is the row's recap-pass operator.

**Pre-trigger period (now to W14 2026):**

- Cycles do not run.
- Smoke test once (above).
- Toolkit hash spot-checks during any touching session.

---

## 9. Closure conditions for Tier 5 itself

Tier 5 is operational, not a thread. It does not "close." It can degrade, and the doctrine documents the degradation modes and recovery paths.

**Degradation modes:**

- **Commissioner unavailable for >2 weeks during W14+ window.** Cycles defer through the unavailability window. On return, a catch-up cycle runs against any captured rows during the gap; the catch-up cycle's memo explicitly notes the deferred period.
- **Infrastructure rot (toolkit hashes drift uninvestigated).** Caught at session-start hash check. The drift itself is anti-drift's job; once drift is observed, the cycle that observed it produces a corrective memo before continuing. If drift cannot be explained against the commit history of the toolkit files, the cycle defers all three tools' outputs and produces an integrity-investigation memo.
- **No narrative-rich weeks in a season.** The end-of-season retrospective records the absence; doctrine remains active. Absence-of-cycles is a finding worth recording; it documents that the season's prose did not exhibit Tier 5-detectable patterns.
- **Doctrine v1.X iteration.** Refinement via successor `_observations/` memos until empirical validation (one to two real W14+ cycles) supports promotion to `docs/50_ops_and_build/Tier_5_Live_Observation_Cadence_v1_0.md`. The promotion event is itself a doctrine-state-change memo.

**Doctrine refinement is a non-closure operational state.** Naming this explicitly prevents the calcification pattern where v1.0 stays v1.0 across multiple seasons because no individual session is willing to claim authority for v1.1. v1.X evolution is expected; the act of refining is normal operations, not a special event.

---

## 10. Standing-backlog updates and authority position

**Standing backlog after this memo (re-ordered to reflect Tier 5 monitoring relationships):**

1. (THIS MEMO) Tier 5 doctrine v1.0 — RETIRED at this commit hash.
2. Section 10 Q1 Bug 1 (HEADLINE budget eviction) — DEFER at `50e3141`. Tier 5 monitors via §6. Re-activates per §6 table action column.
3. SCORE_VERBATIM legacy-drift — CLOSED at `16d4a1b`. Tier 5 monitors via §6.
4. Player-streak verb inversion — named-only per `session_brief_player_streak_verb_inversion_diagnostic.md` standing backlog #5. Tier 5 monitors via §6.
5. Cat 3c row-76 W14 2025 attribution edge case — deferred (label only). Tier 5 monitors via §6 manual prose inspection.
6. Snap-outcome detection — named-only. Tier 5 monitors via §6 manual prose inspection.
7. NOTABLE-pass alphabetical lockout investigation — named-only. Tier 5 monitors via §6 manual prose inspection.
8. Tests/ ruff cleanup — RETIRED at `6740014` (5th instance of stale-backlog hazard).
9. `d['raw_mfl']` write at `extract_recap_facts_v1.py:190` — RETIRED at `09598b3`.
10. **(NEW)** Bug 1 classifier current-week scope extension (Q5 follow-on) — named-only. The §4.1 classifier currently runs against the 13 hardcoded historical specimens; live W14+ cycles need a current-week discovery scope. Promote-conditional on first real W14+ 2026 cycle revealing friction in the manual scope-extension form.
11. **(NEW)** Tier 5 doctrine v1.1 — triggered by first real W14+ 2026 cycle that surfaces a refinement to §3 / §4 / §5 / §6 / §7. Refinement-by-observation rather than refinement-by-design.
12. **(META, NEW)** Priority-list mechanism redesign — flagged at fifth instance of stale-backlog hazard per `6740014`'s closure memo §"The five-instance stale-backlog pattern". The 2026-05-02 amendment proposed two structural fixes: (a) generate the list from commit metadata, or (b) retire the format. Neither has shipped. Tier 5 does not directly own this meta-item; it is named here because the standing-backlog mechanism is the surface §6 relies on for "what's open and how it re-activates." If the priority-list mechanism is restructured, §6's table presentation may need a parallel adjustment.

**Authority position per Operational Plan v1.1 §12.** Tier 5 sits *under* the Operational Plan as an implementation track for the diagnostic toolkit shipped 2026-05-06/07. It does not amend or override the Operational Plan's authority for ops-and-build doctrine. Tier 5's own authority is operational doctrine for the specific surface it covers (the three toolkit pieces and their re-activation criteria), and that authority is provisional v1.0 — pending empirical validation via real W14+ cycles, after which the doctrine promotes to `docs/50_ops_and_build/` and the authority firms.

**Memory edit updates (post-commit):**

- Edit #17 (open-horizon): retire "active-next-focus" framing for Tier 5 in favor of "operational track per `OBSERVATIONS_2026_05_07_TIER_5_LIVE_OBSERVATION_DOCTRINE.md`."
- Edit #17 (or successor): update mypy file count from 59 to 60 (observed at session start).
- Edit #17 (or successor): retire the SCORE_VERBATIM "59-row drift" framing (already corrected by `16d4a1b` §11; this memo is the persistence boundary).

---

## 11. Methodology notes

- **Doctrine memos that may evolve belong in `_observations/`.** Q1's trade-off analysis (brief Step 1) reads as well-justified at v1.0; promotion to `docs/` after one or two real cycles is the right pattern. Operational doctrine that is provisional should be filed with provisional friction (memo-date versioning). Binding doctrine in `docs/` ahead of empirical validation calcifies guesses.
- **The placeholder pattern is itself a finding.** "Tier 5" calcified across at least five distinct artifacts (three closure memos, two predecessor briefs) without ever being defined. The `16d4a1b` §11 lesson generalizes: numbers and named concepts that are not verified at every reference drift the same way. This memo's existence is the corrective; the pattern is worth flagging in successor session briefs as a class of risk.
- **The toolkit's three tools are not a system.** They share a trigger condition (live W14+ row) and a memo discipline (Tier 5 cycle memo) but have distinct scopes, DB shapes, and verdict logics. Treating them as one-tool-three-modes would obscure the per-tool reasoning each requires (the `16d4a1b` §11 read-the-orig-column lesson; the `50e3141` §5 design-surface preservation; the `d8ac8b1` baseline-rotation criterion). The doctrine names them as a toolkit, not a system, deliberately.
- **First real cycle is months away.** This memo is forward-deployed doctrine. The discipline of writing it ahead of its first exercise is itself the test — if §3, §4, §5, §6 cannot be written concretely now without empirical data, then the placeholder was placeholder-of-confusion rather than placeholder-of-readiness. The fact that §1–§10 can be written concretely is the evidence the doctrine is real, not aspirational.

---

## 12. Files and commits referenced

- `09598b3` — HEAD at draft.
- `6740014` — Tests/ ruff cleanup non-finding closure (5th-instance stale-backlog).
- `d8ac8b1` — `reverify_prompt_audit.py --baseline-tag` (Tier 5 toolkit piece 4.3).
- `16d4a1b` — SCORE_VERBATIM Step 0 closure (re-activation criteria for §6).
- `2e05884` — `diagnose_score_verbatim_drift.py` (Tier 5 toolkit piece 4.2).
- `50e3141` — Bug 1 generation/eviction classifier closure (re-activation criteria for §6, design surface for spawned thread).
- `6329ae9` — `step_1_streak_diagnostic_harness.py classify-bug1-specimens` (Tier 5 toolkit piece 4.1).
- `_observations/OBSERVATIONS_2026_05_06_PLAYER_STREAK_VERB_DIAGNOSTIC.md` — re-activation citation source for §6 player-streak entry (lines 26 and 148).
- `_observations/session_brief_tier_5_doctrine.md` (`769f80a`) — predecessor session brief.
- `scripts/step_1_streak_diagnostic_harness.py` — Bug 1 classifier (SHA-256 `5adb1fbb…` at HEAD).
- `scripts/diagnose_score_verbatim_drift.py` — SCORE_VERBATIM probe (SHA-256 `3f6ad837…` at HEAD).
- `scripts/reverify_prompt_audit.py` — reverify gate (SHA-256 `ca43daf1…` at HEAD).
