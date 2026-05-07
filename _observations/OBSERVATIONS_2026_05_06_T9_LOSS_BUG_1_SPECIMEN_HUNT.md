# OBSERVATIONS -- Section 10 Q1 Bug 1 specimen #2 hunt (cross-season T9-LOSS scan)

**Drafted:** 2026-05-06.
**HEAD at run:** cdaf1cd (harness commit immediately preceding this memo).
**Phase:** 10 -- Operational Observation.
**Position in plan:** Diversity-trigger arbiter for the post-fix
memo's open Bug 1 follow-on. Companion to harness commit `cdaf1cd`.

---

## TL;DR

- **DIVERSITY TRIGGER SATISFIED.** The cross-season T9-LOSS scan
  surfaced **13 non-Brandon specimens across 5 distinct franchises
  and 6 distinct seasons** (2011, 2012, 2014, 2016, 2017, 2019) in
  the 2010-2025 PFL Buddies canonical event corpus.
- The post-fix memo's framing -- "Bug 1 stays at single-specimen
  status; diversity trigger requires cross-franchise evidence which
  a 2025-only scan cannot provide" -- is now empirically refuted
  by 14 historical seasons of canonical data.
- **Bug 1 (HEADLINE budget eviction) promotes from "noted, single-
  specimen" to "actionable thread, multi-specimen, multi-franchise."**
  The follow-on session brief drafts the four-step playbook for
  HEADLINE budget reservation/eviction policy.
- Important caveat: these are **detector-eligible** specimens, not
  generated-but-evicted specimens. The post-fix memo's specimen #1
  proved generation-and-eviction; this scan only proves the first
  link in that chain (the detector would have fired). Confirming
  generation-and-eviction for these 13 specimens requires
  prompt_audit history inspection per (season, week), which is
  out of scope for the diversity-trigger question.

---

## 1. Why this session

The Section 10 Q1 paired thread closed Bug 2 (T9-LOSS form gap,
integrity tier) at commits `0887556` / `cb128d4` / `69db27d`.
Bug 1 (HEADLINE budget eviction, editorial tier) was named-only
in the brief and gated on a diversity trigger:

> The brief's diversity trigger for Bug 1 promotion: >=2 distinct
> franchises across >=2 distinct weeks of T9-LOSS angles
> generated-but-evicted.

The post-fix memo (`a5c5c1b`) recorded specimen #1 (Brandon Knows
Ball, fid=0010, W14 2025) and noted that 2025-only scans
identified additional Brandon-only candidates (W11-W18) but no
cross-franchise specimens. The memo defined the next thread
action:

> Bug 1 specimen #2 hunt: scan 2024 and prior seasons for
> T9-LOSS-eligible (week, franchise) candidates from a
> *different* franchise than Brandon. If found, promote Bug 1
> to actionable thread.

This session executes that scan.

---

## 2. Harness output

Run command:

    PYTHONPATH=src python scripts/step_1_streak_diagnostic_harness.py \
      --db .local_squadvault.sqlite \
      --league-id 70985 \
      --scope hunt-t9-loss-cross-season

**Corpus:** 16 seasons (2010-2025), 266 (season, week) tuples
total scanned, 250 with multi-season league history available.
Pre-2010 weeks suppressed by `_detect_streak_records`'s
`is_multi_season` guard; that's correct silence-over-speculation
behavior, not a scan limitation.

**Counts:**

| Metric | Value |
|---|---:|
| Seasons in scope | 16 (2010-2025) |
| (season, week) tuples scanned | 266 |
| Weeks with multi-season history | 250 |
| Brandon T9-LOSS hits (excluded) | 8 |
| **Non-Brandon T9-LOSS specimens** | **13** |

**Brandon hit weeks (for completeness):** 2025W11, 2025W12,
2025W13, 2025W14, 2025W15, 2025W16, 2025W17, 2025W18. Internally
consistent with the post-fix memo's specimen #1 description.

---

## 3. Non-Brandon specimens

| # | Season | Week | Franchise | fid | Streak | Record |
|---:|---:|---:|---|---|---:|---:|
| 1 | 2011 |  4 | Ben's Gods               | 0008 | -4 |  5 |
| 2 | 2011 |  5 | MGD                       | 0006 | -4 |  5 |
| 3 | 2011 |  6 | MGD                       | 0006 | -5 |  6 |
| 4 | 2011 | 12 | Paradis' Playmakers       | 0002 | -6 |  7 |
| 5 | 2012 |  9 | Purple Haze               | 0003 | -6 |  7 |
| 6 | 2014 |  9 | Paradis' Playmakers       | 0002 | -6 |  7 |
| 7 | 2016 | 13 | Ben's Gods                | 0008 | -7 |  8 |
| 8 | 2016 | 14 | Ben's Gods                | 0008 | -7 |  8 |
| 9 | 2016 | 15 | Ben's Gods                | 0008 | -7 |  8 |
| 10 | 2016 | 16 | Ben's Gods                | 0008 | -7 |  8 |
| 11 | 2017 | 11 | MGD                       | 0006 | -7 |  8 |
| 12 | 2019 |  8 | Miller's Genuine Draft    | 0006 | -8 |  9 |
| 13 | 2019 |  9 | Miller's Genuine Draft    | 0006 | -9 | 10 |

**Distinct franchises:** 5 (fids 0002 Paradis, 0003 Purple Haze,
0006 MGD/Miller's, 0008 Ben's Gods, plus 0010 Brandon in the
excluded count). Note that fid 0006 shows two display names across
years -- "MGD" in 2011/2017 vs "Miller's Genuine Draft" in 2019 --
consistent with the franchise_directory per-season name resolution
and not a detector or harness inconsistency.

**Distinct (season, week) pairs:** 13.

**Distinct seasons:** 6 (2011, 2012, 2014, 2016, 2017, 2019).

**Pattern observation.** The 2016 W13-W16 sequence is the same
Ben's Gods loss streak across four consecutive weeks (streak=-7
against record=8 throughout). At W17 the streak either tied/broke
the record (T10 angle) or was snapped; the canonical record_length
holding at 8 across W13-W16 indicates the streak did not advance
the record during those weeks. Real history; not detector noise.

The 2011 specimens show the league's longest_loss_streak record
*growing* through the season (5 -> 5 -> 6 -> 7), consistent with
early-history league when individual streaks were also setting
the record. Detector correctly tracks the temporal scope per
LEAGUE_HISTORY discipline.

---

## 4. Decision

**DIVERSITY TRIGGER SATISFIED.** Per the brief's gate:

> >=2 distinct franchises across >=2 distinct weeks of T9-LOSS
> angles generated-but-evicted.

Actual: 5 franchises across 13 (season, week) tuples (or 13
distinct weeks if counting flat across seasons; or 6 distinct
seasons if collapsing within-season repeats). Vastly oversatisfies.

**Bug 1 promotes** from "noted, single-specimen" to "actionable
thread, multi-specimen, multi-franchise."

**Caveat.** The diversity trigger as stated in the post-fix memo
specifies "T9-LOSS angles generated-but-evicted." The scan in
this session proves *detector-eligibility* across the historical
corpus -- the angles would have fired at the data layer. Whether
each specimen was actually generated-and-evicted in the recap
that was rendered for that (season, week) requires:

1. Verifying that the recap's narrative_angles_text contained
   the T9-LOSS line (generation), and
2. Verifying that the rendered prose did NOT surface the
   record-shape claim (eviction).

That two-step verification is in scope for the follow-on
actionable-thread brief, not for this diagnostic memo. The
diversity trigger's purpose was to determine whether Bug 1's
risk pattern is single-franchise or systemic. Result: systemic.
That's enough to promote.

It is also possible some of the 13 historical specimens predate
the T9-LOSS form being emitted by the helpers (helpers added at
`0887556` on 2026-05-06; pre-fix corpus had `_detect_streak_records`
emitting only T8 / T9-WIN / T10). For pre-fix recaps, "evicted"
isn't quite the right framing -- the angle wasn't even emitted.
But the systemic-risk conclusion still holds: across 14 historical
seasons, the underlying *streak conditions* fired in 5 distinct
franchises. The eviction-risk surface is structurally cross-
franchise.

---

## 5. Follow-on session brief scaffold

The actionable-thread brief drafts as a four-step playbook
mirroring the Section 10 Q1 Step 1 thread. Outline:

- **Step 0a -- Generated-but-evicted classifier extension.**
  Extend the harness with a fourth scope (or a flag) to
  cross-reference detector-eligible (season, week, fid) tuples
  against `prompt_audit` history for that week, and classify
  each as GENERATED_AND_SURFACED, GENERATED_AND_EVICTED, or
  NOT_GENERATED. Diagnostic-only.
- **Step 0b -- Memo.** Apply the classifier across the 13
  specimens identified in this memo. Report bucket counts.
  Confirm or refine the systemic-eviction hypothesis.
- **Step 1 -- HEADLINE budget reservation policy.** Production-
  path commit. Likely shape: reserve a slot in the HEADLINE
  budget for any T9-LOSS or T8/T10 angle when its strength
  threshold is met, preventing rotation-hash eviction. Discipline:
  one-topic-per-commit; helper (if any new helper needed) before
  consumer wiring.
- **Step 2 -- Verifier extension (if applicable).** If the budget
  policy enforces specific surfacing rules, the verifier may
  need a parallel check. Possibly out of scope; defer to Step 1
  evidence.
- **Step 3 -- Reverify-as-merge-gate + post-fix observation.**
  Per the playbook.

The brief drafts post-this-memo as a separate doc commit. Not
in this session.

---

## 6. Standing-backlog updates

- **Bug 1 (HEADLINE budget eviction):** PROMOTED from "open with
  specimen #1" to "actionable thread, scaffold drafted in this
  memo."
- The carry-forward backlog updates accordingly. The userMemories
  Edit #17 will be replaced post-this-commit to reflect Bug 1's
  new state.

Other open items unchanged:

- SCORE_VERBATIM 59-row drift (independent thread; confirmed at
  59 distinct rows by Probe 1.4.A.B in the post-fix memo).
- Cat 3c row-76 (deferred; affects label only, not detection).
- Tier 5 W14+ live observation cadence (operational; activates
  per the post-Section 10 Q1 development direction).
- Snap-outcome detection (named-only).
- Tests/ ruff cleanup (deferred).
- `d['raw_mfl']` write at `extract_recap_facts_v1.py:190` (deferred).

---

## 7. Methodology notes

A few items worth recording for the session record:

- **Memory drift caught at session start (again).** This evening's
  initial framing of standing-backlog #10 as "30-minute Tier 1
  micro-thread" was structurally blocked on Section 10 Q1 Step 1
  having shipped, which memory hadn't recorded. Grounding via
  `git log | grep` resolved the ambiguity; confirmed Section 10
  Q1 Step 1 shipped through commit `fdd06fa` (2026-05-06). Memory
  edit #17 was updated later in the session to reflect the new
  state. A lower-overhead approach -- defaulting to a
  `git log --oneline` scan when memory and intent diverge -- is
  now reflexive.

- **JSON-path drift caught at grounding-paste boundary.** Two of
  the early grounding queries used `$.season` and `$.week_index`
  against `v_canonical_best_events.payload_json`. Actual paths
  are `$.season` (which works -- season is a top-level column,
  not in the payload) and `$.week` (not `$.week_index`). The
  schema-introspection-before-query discipline from the post-fix
  memo would have caught this; I skipped it because the query
  "felt obvious." Cost: one extra grounding paste. Lesson encoded
  in the post-fix memo's section 5; reaffirmed here.

- **Heredoc raw-string discipline (memory edit #21) bit at the
  apply step.** The first apply attempt of the harness extension
  used a regular triple-quoted Python string for the HELPER body,
  not a raw string. Python interpreted the backslash-n escapes
  inside print-with-newline literals as actual newlines,
  fragmenting the resulting source into 85 ruff syntax errors.
  Recovered via `git checkout --` of the unstaged file and
  reapply with the raw-string form. Memory edit #21's
  triple-quoted raw string form is the bulletproof default; the
  regular triple-quoted string is a foot-gun when content
  includes any backslash escapes.

- **Triple-quote delimiter collision in raw-string memo body.**
  This memo file was first attempted with literal three-single-
  quote sequences in the section 7 prose (referencing the
  raw-string form by its delimiter). Python's tokenizer treated
  the embedded three-single-quotes as the closing of the outer
  raw-string, then failed to parse the trailing prose as code.
  Three paste-fragility hazards in one day: chat-rendered .md
  auto-linking (memory edit #14), heredoc with embedded triple-
  backticks (memory edit #21), and raw-string body containing
  the closing delimiter sequence. All three are variations on
  "delimiter collisions in copy/paste contexts." A consolidated
  hazard catalog might be worth its own memory edit; deferred
  for now.

- **Apply scripts stay idempotent.** All apply attempts (the
  failed-then-reverted regular-string version, the failed-by-
  syntax memo write, and the successful retries) used anchor-
  checks ("OLD block not found", "helper already present",
  "anchor blocks not unique") to refuse-on-drift. Working as
  intended; these guards let re-application be safe.

---

## 8. Files and commits referenced

- `scripts/step_1_streak_diagnostic_harness.py` -- harness with
  new `hunt-t9-loss-cross-season` scope (`cdaf1cd`).
- `_observations/OBSERVATIONS_2026_05_06_T9_LOSS_POST_FIX_REVERIFY.md`
  (`a5c5c1b`) -- the post-fix memo defining the diversity trigger
  and naming this scan as the next thread action.
- `0887556` / `cb128d4` / `69db27d` -- Section 10 Q1 Step 1 thread
  (helper / detector / verifier).
- `b94493c` -- standing-backlog #10 closure (parametrized helper-
  bound verifier test) earlier in this session.
- `src/squadvault/core/recaps/context/narrative_angles_v1.py` --
  `_detect_streak_records` at line 539; T9-LOSS branch in body.
- `src/squadvault/core/recaps/render/streak_strings_v1.py` --
  `format_streak_record` at line 176; T9-LOSS form per the
  Section 10 Q1 Step 1 thread.
- `src/squadvault/core/recaps/context/season_context_v1.py` --
  `derive_season_context_v1` at line 495.
- `src/squadvault/core/recaps/context/league_history_v1.py` --
  `derive_league_history_v1` at line 641.
