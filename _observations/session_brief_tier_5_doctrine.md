# Session Brief — Tier 5 doctrine memo (live observation cadence definition)

**Drafted:** 2026-05-07 (read-only preparatory material; this brief lands as a single doc commit when the session begins, OR is held in conversation context if Steve elects).

**Working tree:** `/Users/steve/projects/squadvault-ingest-fresh`

**Phase:** 10 — Operational Observation.

**Shape:** Doc-only session, single wave. **No production-path code changes; no diagnostic-script changes.** The session writes one or two memos defining what "Tier 5 W14+ live observation cadence" concretely *is*, since the term has been referenced as "active-next-focus" through three closure memos (`50e3141`, `16d4a1b`, `d8ac8b1`) and the post-§10 Q1 development direction without ever being formally defined.

**Expected session length:** 60–90 minutes. One commit (the doctrine memo). Optionally a second commit if Framing B (activation wrapper) is elected mid-session.

**Starting commit:** `d8ac8b1` (or successor if any micro-thread has landed between this brief and session start). Verify HEAD before any other action; record at session start.

---

## Why this session, and what it determines

Three closure memos shipped on 2026-05-06 / 2026-05-07 reference "Tier 5 W14+ live observation cadence" as the natural next-focus once their respective threads close:

- `50e3141` (§10 Q1 Bug 1 Step 0b) — "Tier 5 W14+ live observation cadence promotes from named-only to active-next-focus."
- `16d4a1b` (SCORE_VERBATIM Step 0) — "Tier 5 W14+ live observation cadence (active-next-focus per Bug 1 Step 0b closure)."
- `d8ac8b1` (Direction 2 reverify category-attribution) — implicitly, by retiring the manual category-breakdown SQL workaround that operational cadence would have required.

Two predecessor session briefs reference Tier 5 explicitly:

- `session_brief_player_streak_verb_inversion_diagnostic.md` — "If decision tier is *promote*, item 5 becomes the next active thread and Tier 5 (W14+ live observation per the post-§10 Q1 direction memo) defers further. If decision tier is *close* or *editorial-defer*, Tier 5 becomes the next active focus."
- `session_brief_section_10_q1_paired_revised.md` and successors — multiple "Tier 5" references as the post-§10 Q1 operational track.

**The problem:** "Tier 5" is treated as if it's defined elsewhere. The post-§10 Q1 development direction memo it points to does not exist as a discoverable artifact. `_observations/` contains no `TIER_5_*` or `LIVE_OBSERVATION_*` doctrine memo. `docs/` has no equivalent. The Operational Plan v1.1 mentions observation tracks (Track A through Track D) but no Tier 5. The result: "Tier 5" is a placeholder that's been reified through repeated reference without ever being concretely scoped.

**This session's deliverable:** an operational doctrine memo that ends the placeholder status. The memo defines:

1. What live observation means in concrete operational terms (what gets captured, when, under what trigger).
2. How the three pieces of durable diagnostic infrastructure shipped during the 2026-05-06/07 arc fit into the cadence.
3. Re-activation criteria for the closed/deferred threads (Bug 1, SCORE_VERBATIM) and how live observation surfaces them.
4. The boundary between "live observation" and "ad-hoc investigation" — when a Tier 5 cycle terminates vs spawns a four-step playbook session.
5. Cadence frequency, memo discipline, and the artifact trail per cycle.

The memo lands in `_observations/` matching the existing observation memo convention, OR in `docs/50_ops_and_build/` if it's authored as canonical doctrine rather than situational observation. Decision deferred to session start; see Q1 below.

---

## Predecessor work the doctrine builds on

Three pieces of durable diagnostic infrastructure were shipped during the 2026-05-06/07 arc, which together form the operational toolkit Tier 5 exercises:

1. **`scripts/step_1_streak_diagnostic_harness.py`** — the `classify-bug1-specimens` scope shipped at `6329ae9`. Six-bucket classifier across the 13 historical T9-LOSS specimens. Re-runs the bucket distribution against any future audit state. Re-activates Bug 1's Step 1 production-path code if `EVICTION_LIKELY ≥ 2` across distinct franchises post-helper.

2. **`scripts/diagnose_score_verbatim_drift.py`** — shipped at `2e05884`. Four-bucket SCORE_VERBATIM era cross-tab classifier. Re-runs against any future reverify tag. Re-activates SCORE_VERBATIM thread if `POST_FIX_TO_PRESENT > 0` (verifier/helper drift) or post-Wave-1 row with `original_passed=1` (real regression).

3. **`scripts/reverify_prompt_audit.py --baseline-tag`** — shipped at `d8ac8b1`. Category-attribution merge gate. Eliminates the manual category-breakdown SQL step at every merge gate by computing per-category baseline vs current deltas and emitting a category-NEW verdict.

The doctrine memo names these explicitly as the Tier 5 toolkit and documents how each is exercised in the operational cadence.

Two closure memos provide the re-activation criteria they encode:

- `50e3141` §6 — Bug 1 re-activation when "Tier 5 W14+ live observation produces a post-helper prompt_audit row for a non-Brandon franchise where T9-LOSS was generated AND evicted."
- `16d4a1b` §8 — SCORE_VERBATIM re-activation when "POST_FIX_TO_PRESENT bucket increments above zero on a future reverify run" or "post-Wave-1 row appears in the failing set with original_passed=1."

The doctrine memo references these and adds any I've missed during scope inspection at session start.

---

## Scope

### In scope

#### 1. Doctrine memo authoring

The session writes one substantive memo. Working title: `_observations/OBSERVATIONS_2026_05_<DD>_TIER_5_LIVE_OBSERVATION_DOCTRINE.md` or `docs/50_ops_and_build/Tier_5_Live_Observation_Cadence_v1_0.md`. Decision per Q1 below.

Sections the memo covers:

- **§1 — TL;DR.** What Tier 5 is in two paragraphs. The placeholder problem this memo solves.
- **§2 — What "live observation" means concretely.** Distinguishes from corpus replay (which the SCORE_VERBATIM Step 0 probe did) and from retrospective reverify (which the d8ac8b1 enhancement supports). Live observation operates on freshly-captured `prompt_audit` rows from new W14+ recap generation passes — not historical rows. Defines the trigger condition (a new approved-or-attempted recap with `captured_at >= <doctrine ship date>`).
- **§3 — When Tier 5 activates.** The phrase "W14+" in the term name carries specific semantic content: weeks 14 and beyond are the playoff stretch where most narrative-richness signals concentrate (record-claim eligibility peaks, season-storyline weight is heaviest, retry pressure is highest). Pre-W14 weeks are *not excluded* from observation but are lower-priority. The doctrine codifies the W14+ priority while not over-narrowing the trigger surface.
- **§4 — The Tier 5 toolkit.** The three pieces of infrastructure shipped 2026-05-06/07. For each:
  - When in the cycle to run it.
  - What output to capture.
  - What re-activation criterion the output checks.
  - The single-paste invocation form.
- **§5 — Per-cycle cadence and memo discipline.** What a "Tier 5 cycle" produces as artifacts. Single observation memo per cycle? Per week? Per month? Per noteworthy-finding? Recommend a specific cadence and justify it. The Operational Plan v1.1 §9.3 self-evaluation cadence pattern is a precedent.
- **§6 — Re-activation criteria, consolidated.** Bug 1, SCORE_VERBATIM, the player-streak verb inversion thread (item #5 from `session_brief_player_streak_verb_inversion_diagnostic.md`), and any other deferred threads with named re-activation conditions. Each criterion gets a row in a consolidated table: thread, signal, infrastructure that detects it, action when fired.
- **§7 — Boundary: observation vs investigation.** When a Tier 5 cycle's output is logged-and-closed vs when it spawns a four-step playbook session. The `silence-over-speculation` principle plus the `diagnostic-first` discipline frame this boundary; the memo concretizes it.
- **§8 — Pre-W14+ activation conditions.** Honest acknowledgment: the 2025 NFL season is over; the 2026 season won't reach W14 until late November. Tier 5's actual activation is months away. The doctrine documents what to do *now* (zero-cycle baseline) and what triggers the first real cycle.
- **§9 — Closure conditions for Tier 5 itself.** Tier 5 is operational, not a thread. It has no "close" — but it has degradations (commissioner unavailable, infrastructure rot, no narrative-rich weeks). Documents the degradation modes and the recovery path for each.
- **§10 — Standing-backlog updates and authority position.** What Tier 5's existence changes about the standing backlog (re-orders priority of named-only items by their re-activation hooks), and where Tier 5 sits in the authority hierarchy from `Operational_Plan_v1_1.md` §12.

#### 2. Optional second commit — Framing B activation wrapper

If session time permits and Steve elects, a second commit ships the activation wrapper script: `scripts/run_tier_5_cycle.py` or similar, which invokes the three diagnostic tools in sequence against any new prompt_audit rows since a baseline date. Single-paste invocation. Output is the union of the three tools' outputs.

Discipline: the wrapper does not make decisions — it only runs the diagnostics and prints their output. The memo's §7 boundary (observation vs investigation) applies to the wrapper's output as much as to manual invocation.

**Default:** ship the doctrine memo first. Decide on the wrapper script after seeing the doctrine's §4 toolkit specification — if §4 makes the toolkit feel like three separate tools that happen to be related, the wrapper is over-engineering. If §4 makes the toolkit feel like one tool with three modes, the wrapper is the natural artifact.

#### 3. Memory edit updates

After the doctrine memo lands, update memory edit #17 to reflect:

- Tier 5 doctrine concretized at <commit hash>.
- Standing backlog re-ordered per §10 of the doctrine memo.
- "Active-next-focus" framing for Tier 5 retired in favor of "operational track per doctrine memo."

### Out of scope

- **Live observation execution.** No actual cycles ship in this session. The 2026 W14 trigger is months away; this session writes the doctrine, not the practice.
- **Production-path code changes.** Doctrine-only. Anything that would change `src/squadvault/` is out of scope.
- **Architectural changes.** Phase 10 is frozen. Tier 5 fits within existing architecture; the doctrine documents that fit.
- **Retroactive corpus analysis.** The SCORE_VERBATIM Step 0 already did the historical pass. Tier 5 is forward-looking by definition.
- **Reverify-as-merge-gate operational changes.** The `--baseline-tag` flag at `d8ac8b1` is the merge-gate work; doctrine references it but doesn't extend it.
- **New diagnostic tooling beyond the optional Framing B wrapper.** Anything that needs new infrastructure beyond the existing three tools requires its own session brief.

---

## Step-by-step decomposition

### Step 0 — Re-grounding (paste at session start)

    cd ~/projects/squadvault-ingest-fresh
    git fetch origin
    git rev-parse HEAD                       # expected: d8ac8b1 or successor
    git log --oneline -8                     # confirm 2026-05-06/07 arc landed
    git status                               # confirm clean tree

    PYTHONPATH=src python -m pytest Tests/ -q 2>&1 | tail -3   # baseline 1957/3
    ruff check src/ Tests/                                       # confirm zero
    mypy src/squadvault/core/ 2>&1 | tail -3                     # confirm clean

Pin SHA-256 hashes for the three Tier 5 infrastructure files (these don't change in this session, but the hashes anchor §4 of the doctrine memo to a known production state):

    shasum -a 256 \
      scripts/diagnose_score_verbatim_drift.py \
      scripts/reverify_prompt_audit.py \
      scripts/step_1_streak_diagnostic_harness.py

**Expected at d8ac8b1:**

| File | SHA-256 |
|---|---|
| `scripts/diagnose_score_verbatim_drift.py` | `3f6ad8373109181e1cbf20ac6998382b01577fdb89023d219f4cd6875f91df86` |
| `scripts/reverify_prompt_audit.py` | `ca43daf1612c10a5a8678cd4b3b7b4f070f9b1c3dd84ded918fea63f21577a26` |
| `scripts/step_1_streak_diagnostic_harness.py` | `5adb1fbb699638e8456327427492844e4c17af468e8dd22c07ec67f9faf8f679` |

Drift on any of these means a follow-on micro-thread shipped between this brief and session start; re-read the changed file's docstring before authoring §4.

Read predecessor closure memos in full (the doctrine memo summarizes their re-activation criteria):

    cat _observations/OBSERVATIONS_2026_05_06_BUG_1_GENERATION_EVICTION_CLASSIFIER.md
    cat _observations/OBSERVATIONS_2026_05_07_SCORE_VERBATIM_STEP_0_PROBE.md
    cat _observations/OBSERVATIONS_2026_05_06_T9_LOSS_BUG_1_SPECIMEN_HUNT.md

Inventory existing doctrine surface:

    ls _observations/ | grep -iE "tier|live|cadence|observation_window|operational"
    ls docs/50_ops_and_build/ 2>/dev/null
    grep -rn "Tier 5\|live observation" _observations/ docs/ 2>/dev/null | head -20

The grep should return exactly the three closure memos referencing Tier 5 plus this brief. If anything else turns up, the doctrine surface isn't actually missing — re-scope before proceeding.

### Step 1 — Memo location decision (Q1 resolution)

Decide whether the memo lands in `_observations/` (situational observation) or `docs/50_ops_and_build/` (canonical doctrine). See Q1 below for the trade-off analysis. Decision recorded as the first paragraph of §1 of the memo body.

**Default if no strong preference at session start:** `_observations/`. Doctrine memos that may evolve (Tier 5's cadence will likely refine after first real cycle) are better placed in `_observations/` where versioning is implicit via memo date. Promotion to `docs/` happens after one or two real cycles validate the doctrine empirically.

### Step 2 — Memo authoring

Write the memo per the §1–§10 structure in "In scope" §1 above. Use the bulletproof memo-write form (memory edit #21): a `python3 <<PYEOF` heredoc with the memo body assigned to a triple-quoted raw string variable, then `pathlib.Path(...).write_text(MEMO, encoding='utf-8')`. The heredoc delimiter must be quoted (single quotes around `PYEOF`) to suppress shell expansion.

Length expectation: 200-350 lines. Substantially longer than the SCORE_VERBATIM Step 0 closure memo (162 lines), shorter than the Operational Plan v1.1.

### Step 3 — Gate, stage, commit, push

Standard pattern from this thread's prior commits:

    ls -la _observations/OBSERVATIONS_<...>.md && head -10 _observations/<...>.md
    git add _observations/<...>.md && git status --short && git diff --cached --stat
    # Separate paste turn for commit (multi-`-m` form per memory edit #21)
    git commit -m "..." -m "..."
    # Separate paste turn for push
    git push

Suggested commit message structure (multi-`-m` to avoid apostrophe-in-shell hazards):

    git commit -m "_observations: Tier 5 live observation cadence doctrine v1.0" \
      -m "" \
      -m "Concretizes the placeholder Tier 5 W14+ live observation cadence referenced as active-next-focus in 50e3141, 16d4a1b, and d8ac8b1 closure memos and in the post-Section 10 Q1 development direction. Doctrine memo defines what live observation concretely means, when it activates, how the three Tier 5 toolkit pieces (Bug 1 classifier 6329ae9, SCORE_VERBATIM probe 2e05884, reverify --baseline-tag d8ac8b1) fit into the cadence, and consolidated re-activation criteria for the closed/deferred threads." \
      -m "" \
      -m "<elaborate scope per §1-§10 of the memo>" \
      -m "" \
      -m "<note on memo location decision per Q1>" \
      -m "" \
      -m "<note on optional Framing B wrapper if elected>" \
      -m "" \
      -m "No production-path changes."

### Step 4 — Optional Framing B wrapper (gated)

Only proceed if session time remains AND the §4 toolkit specification reads as one-tool-three-modes rather than three-separate-tools. See "Optional second commit" in In scope §2.

If shipped: separate commit, separate gate paste, separate commit-message paste, separate push.

### Step 5 — Memory edit updates

Two edits expected:

1. Update edit #17 (open-horizon memory edit) to reflect doctrine concretization.
2. Optionally add a new edit if the doctrine surfaces a discipline pattern worth preserving across sessions (e.g., "doctrine-via-observation-memo iteration: place evolving operational doctrine in _observations/, promote to docs/ after empirical validation"). Default: don't add unless Steve elects.

---

## Open questions

### Q1 — Memo location: `_observations/` or `docs/50_ops_and_build/`

Doctrine that's actively evolving belongs in `_observations/` (versioned by memo date, low-friction iteration). Doctrine that's canonical and binding belongs in `docs/` (versioned by file name `_v1_0.md`, higher-friction promotion).

Tier 5 hasn't run a single real cycle yet. Its cadence-and-discipline specifics are best-guesses informed by Operational Plan §9 patterns and the diagnostic infrastructure we shipped. After two or three real W14+ cycles, the doctrine will refine. Until then, `_observations/` is the right home.

**Default:** `_observations/OBSERVATIONS_2026_05_<DD>_TIER_5_LIVE_OBSERVATION_DOCTRINE.md`. Promote to `docs/50_ops_and_build/Tier_5_Live_Observation_Cadence_v1_0.md` after first real cycle.

### Q2 — Cadence frequency

Per-week observation cycle is heavyweight. Per-month cycle may miss W14+ pressure that lasts only 4-5 weeks of the season. Per-noteworthy-finding cycle is reactive, not cadence-based.

**Default in the memo:** "trigger-based per noteworthy capture, with a mandatory end-of-W14+-window retrospective whether or not a cycle fired during the window." This matches the Operational Plan's §9.3 self-evaluation cadence pattern (phase-end retrospectives) while accommodating the trigger-driven nature of Tier 5's diagnostic toolkit.

### Q3 — Should the doctrine establish a `prompt_audit_reverify` baseline tag for Tier 5 cycles

The `--baseline-tag` flag at `d8ac8b1` is unscoped to a particular operational practice. Tier 5 needs a stable baseline against which each cycle's reverify run is compared. The natural baseline is the most recent post-Wave-1 verifier-clean state — currently `59846b0`.

**Default in the memo:** name `59846b0` as the Tier 5 v1.0 baseline tag. Document the baseline-rotation criterion (when does Tier 5 retire `59846b0` and adopt a newer tag as baseline?). Suggested rule: rotate when a verifier-extension thread closes and reverify confirms zero category-NEW against the prior baseline.

### Q4 — How the optional Framing B wrapper composes the three tools

If shipped, the wrapper would need to:

- Discover the latest prompt_audit rows since a doctrine baseline date.
- Run the Bug 1 classifier against any new T9-LOSS detector-eligible specimens.
- Run the SCORE_VERBATIM probe against the latest reverify tag.
- Run reverify with `--baseline-tag 59846b0` (or the doctrine's current baseline) for category-NEW verdict.
- Print a single combined output.

Three-tool composition surfaces a question the doctrine should also address: when the Bug 1 classifier needs *non-Brandon* T9-LOSS detector-eligibility, where do those specimens come from in a live W14+ context? The classifier's existing `_BUG_1_SPECIMENS` list is hardcoded to the 13 historical specimens. A live-observation extension would need a *current-week* discovery mechanism. That's potentially a §4 toolkit gap.

**Default:** name the gap in the doctrine memo §4 even if the Framing B wrapper isn't shipped this session. The gap is real regardless. Whether it's a session-blocking concern depends on Q5.

### Q5 — Is the Bug 1 classifier sufficient as Tier 5 toolkit, or does it need a current-week extension?

The classifier was built for the historical specimen list. Live observation needs to surface *new* T9-LOSS detector-eligible specimens as they occur. The current-week extension would be a new scope on the harness (e.g., `classify-current-week-t9-loss`) that runs the detector against the most recent prompt_audit row's (season, week) and classifies any T9-LOSS hits the same way.

**Default in the memo:** flag this as the first concrete Tier 5-driven enhancement to the toolkit. Don't ship it in this session; document it as named-only follow-on. Tier 5's first real cycle will reveal whether it's actually needed (depends on whether a non-Brandon T9-LOSS angle fires in W14+ 2026).

---

## Anti-drift discipline

1. **Re-grounding is session step 0.** Verify HEAD, record actual test/lint baseline, read the three closure memos in full before authoring. The brief is dated 2026-05-07; if the next session is days or weeks later, predecessor work may have shifted.

2. **Doctrine memo is doc-only.** Zero production-path changes. Zero diagnostic-script changes (except the optional Framing B wrapper). Zero test changes. The memo body references file paths and commit hashes; it does not modify them.

3. **The placeholder pattern is itself a finding.** The brief records that "Tier 5" was reified through repeated reference without ever being defined. The doctrine memo should briefly acknowledge this in §1 — placeholders that survive multiple memos calcify into apparent canon. Memory edit #21's lesson about the "59 rows" figure is the same shape: numbers and named concepts that aren't verified at every reference drift in the same way.

4. **One topic per commit.** Doctrine memo is one commit. Optional Framing B wrapper is a separate commit. Memory edit updates happen via the memory tool, not in a commit.

5. **Memo writes via `python3 <<PYEOF` form** per memory edit #21. No triple-backticks, no `PYEOF` literals in body. The memo body has at most plain markdown syntax.

6. **Lint+test gates and `git commit` / `git push` MUST be in separate paste turns** per memory edit #22. Doc-only commits still go through the standard gate sequence (parse-check optional for `.md`, but the staging gate `git status --short && git diff --cached --stat` is mandatory before `git commit`).

7. **Memo length budget: 200-350 lines.** Substantially longer than the SCORE_VERBATIM Step 0 closure memo (162 lines), shorter than the Operational Plan v1.1. If the draft exceeds 400 lines, look for sections that should be split into a follow-on memo or moved to a Q open-questions block for a later session.

8. **The doctrine is v1.0, not the final form.** Document the doctrine's own iteration mechanism. Tier 5 v1.1, v1.2 etc. via successor memos in `_observations/` until promotion to `docs/`. The memo's §9 (closure conditions for Tier 5 itself) should explicitly include "doctrine refinement" as a non-closure operational state.

---

## Standing backlog (carries forward post-this-session)

If the doctrine memo ships and is the session's only commit:

1. **(THIS SESSION when run)** Tier 5 doctrine memo v1.0.
2. SCORE_VERBATIM thread — CLOSED at `16d4a1b`. Tier 5 monitors via `diagnose_score_verbatim_drift.py`. Re-activates per §6 of the doctrine memo.
3. Section 10 Q1 Bug 1 — DEFER at `50e3141`. Tier 5 monitors via `step_1_streak_diagnostic_harness.py classify-bug1-specimens` (potentially extended with a current-week scope per Q5). Re-activates per §6 of the doctrine memo.
4. Cat 3c row-76 W14 2025 attribution edge case (deferred — affects label only).
5. Snap-outcome detection (named-only).
6. NOTABLE-pass alphabetical lockout investigation (named-only).
7. Tests/ ruff cleanup (deferred).
8. `d['raw_mfl']` write at `extract_recap_facts_v1.py:190` (deferred).
9. Player-streak verb inversion thread (named-only; per `session_brief_player_streak_verb_inversion_diagnostic.md` standing backlog item #5).
10. **(NEW)** Bug 1 classifier current-week scope extension — named-only follow-on per Q5.
11. **(NEW)** Tier 5 doctrine v1.1 — triggered by first real W14+ 2026 cycle.

If Framing B wrapper also ships:

12. **(NEW, if shipped)** `scripts/run_tier_5_cycle.py` — durable infrastructure per §4 of the doctrine memo.

---

## Opening move (paste into terminal at session start)

    cd ~/projects/squadvault-ingest-fresh
    git fetch origin
    git rev-parse HEAD
    git log --oneline -8
    git status
    PYTHONPATH=src python -m pytest Tests/ -q 2>&1 | tail -3
    ruff check src/ Tests/
    mypy src/squadvault/core/ 2>&1 | tail -3

    shasum -a 256 \
      scripts/diagnose_score_verbatim_drift.py \
      scripts/reverify_prompt_audit.py \
      scripts/step_1_streak_diagnostic_harness.py

    ls _observations/ | grep -iE "tier|live|cadence|operational" | head
    grep -rn "Tier 5\|live observation" _observations/ docs/ 2>/dev/null | head -20

Then read the three closure memos (`50e3141`, `16d4a1b`, plus `OBSERVATIONS_2026_05_06_T9_LOSS_BUG_1_SPECIMEN_HUNT.md`). Then resolve Q1 (memo location), then author the memo per §1–§10 structure.

---

## The point

The post-§10 Q1 development direction has been "Tier 5 W14+ live observation cadence" through three closure memos and at least two predecessor session briefs, without that term ever being formally defined. Closure memos cite re-activation criteria *that depend on Tier 5 cycles existing*. The placeholder has calcified into apparent canon.

This session ends the placeholder status. One doctrine memo, 200-350 lines, defines what Tier 5 concretely is: the operational track that exercises the three diagnostic tools shipped during the 2026-05-06/07 arc against fresh prompt_audit captures, with consolidated re-activation criteria for the closed/deferred threads, and clear cadence/memo discipline.

The memo is v1.0. It will refine after the first real W14+ 2026 cycle. The act of writing it is the closure of the doctrine-shape gap that's been carried as named-only since at least 2026-05-04.

Doctrine first. Cycles second. The first cycle is months away.
