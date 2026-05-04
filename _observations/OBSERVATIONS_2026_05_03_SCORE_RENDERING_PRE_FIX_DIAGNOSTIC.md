# OBSERVATIONS — Score-Rendering Pre-Fix Diagnostic (Step 1, four-step plan)

**Drafted:** 2026-05-03 (probe runs 2026-05-03 / 2026-05-04 UTC).
**HEAD:** `08355f8` on `main`.
**Phase:** 10 — Operational Observation.
**Position in plan:** Step 1 of the four-step plan documented in
`d76e71b`. This memo is doc-only, lands as the first commit of Wave 1
of the score-string pre-rendering brief
(`session_brief_score_string_pre_rendering_step_2_revised_v2.md`).

---

## TL;DR

- **Step 2 should proceed.** Pre-rendering the matchup score in an
  unambiguous format removes the hyphen-as-separator hazard entirely
  regardless of model compliance variability. Selected format: **"to"**
  (i.e., `"107.65 to 65.40"`).
- **Step 5's severity policy is NOT settled by Step 1 evidence alone**
  (per the brief's design — that's Step 4's job). However, the v17
  approved-prose evidence below argues against Policy A as a default
  even at high post-fix VERBATIM rates. The memo flags this for the
  Step 4 memo to weigh against post-fix observation.
- **A separate thread is opened: post-v17 regression.** Score-string
  compliance collapsed between v17 (APPROVED 2026-04-09) and
  v18–v22 (DRAFTs, 2026-04-14 to 2026-04-16): VERBATIM rate fell
  from 48.2% to 4.0%, MARGIN_ONLY rate rose from 25.9% to 80.0%.
  This is NOT in scope for Step 2 but warrants its own diagnostic
  before the next live recap generation.

---

## Methodology

Diagnostic harness `step_1_score_diagnostic_harness.py` (v3.1)
classifies each canonical (winner_score, loser_score) matchup pair
in approved/draft/superseded prose into one of:

- **VERBATIM** — bullet-form score string `"{w}.{ww}-{l}.{ll}"` or
  reverse appears verbatim in prose.
- **PARAPHRASE_ROUNDED** — integer hyphen-pair appears (e.g. `108-65`
  for `107.65/65.40`); the ambiguous form the brief targets.
- **PARAPHRASE_OTHER** — both decimal scores present in prose but
  not in either paired form (legitimate prose variation).
- **MARGIN_ONLY** — at least one franchise reference appears, neither
  decimal score appears (matchup mentioned but score elided).
- **OMITTED** — no franchise reference (matchup not covered).

Nickname-aware: harness mirrors `_load_franchise_nicknames` and pass
4a's first-word-extraction rules (10 PFL Buddies nicknames seeded;
all 10 produce usable aliases).

Two query scopes were run:

1. **v2 default scope:** APPROVED-only, last 10 recaps cross-season.
2. **v3.1 W13 2025 all-states:** all 22 versions of the W13 2025
   recap, partitioned by lifecycle state.

Provenance probe (`probe_w13_2025_provenance.sh`) read
`recap_artifacts` and `editorial_actions` to characterize what
drove each version transition.

Arc-split probe (`probe_w13_arc_split_and_v17_other.sh`) split the
W13 2025 versions into v1–v17 (initial generation arc, ending
APPROVED 2026-04-09) and v18–v22 (post-approval regens, 2026-04-14 to
2026-04-16) and recomputed per-state distributions for each arc
separately.

---

## Probe 1 — v2 cross-season APPROVED-only (selection-biased reference point)

Last 10 APPROVED weekly recaps, league 70985:

| Recap | Season/Wk | V | Pairs | VERB |
|---|---|---|---|---|
| 1160 | 2025/W7 | 27 | 5 | 5 |
| 1065 | 2024/W17 | 24 | 1 | 1 |
| 1064 | 2024/W16 | 23 | 2 | 2 |
| 1063 | 2024/W15 | 23 | 4 | 4 |
| 1062 | 2024/W14 | 25 | 5 | 5 |
| 1061 | 2024/W13 | 34 | 5 | 5 |
| 1060 | 2024/W12 | 22 | 5 | 5 |
| 1059 | 2024/W11 | 23 | 5 | 5 |
| 1058 | 2024/W10 | 23 | 5 | 5 |
| 1057 | 2024/W9 | 26 | 5 | 5 |

**42/42 (100%) VERBATIM, 0 OMITTED.**

This number is **selection-biased**: APPROVED prose has by
construction survived human review. The version numbers (22–34)
show heavy iteration was required to land at compliant prose. The
denominator does not represent "what the model produces"; it
represents "what the model produces conditional on having survived
review." This number alone is not evidence that Step 2 is
unnecessary — it shows that *given enough regenerations*, the
existing system can land at verbatim compliance.

---

## Probe 2 — v3.1 W13 2025 all-states (full retry-and-iteration history)

### Aggregate (all 22 versions)

| Category | Count | % covered |
|---|---|---|
| VERBATIM | 42 | 38.2% |
| PARAPHRASE_ROUNDED | 24 | 21.8% |
| PARAPHRASE_OTHER | 2 | 1.8% |
| MARGIN_ONLY | 42 | 38.2% |
| OMITTED | 0 | — |

The aggregate is misleading on its own — it conflates two distinct
populations identified by the provenance probe and the arc-split
probe. Per-arc breakdown follows.

### Arc split (the corrected reading)

The provenance probe revealed that the 22 versions are NOT a single
retry loop. v17 was APPROVED on 2026-04-09; v18 began 5 days later
on 2026-04-14. v18–v22 are post-approval regens, almost certainly
with prompt configurations that differ from the v1–v17 arc. (Per
user memory: "first live end-to-end recap generation occurred during
the 2026-04-20 session using W13 2025 data" — the v18–v22 timing is
adjacent.)

**Arc A — v1–v17 (initial generation, 2026-03-25 to 2026-04-09):**

| State | Pairs | VERB | ROUND | OTHER | MARG |
|---|---|---|---|---|---|
| DRAFT | 50 | 48.0% | 20.0% | 0.0% | 32.0% |
| APPROVED | 5 | 80.0% | 0.0% | 20.0% | 0.0% |
| SUPERSEDED | 30 | 43.3% | 36.7% | 0.0% | 20.0% |
| **Aggregate** | **85** | **48.2%** | **24.7%** | **1.2%** | **25.9%** |

**Arc B — v18–v22 (post-approval regens, 2026-04-14 to 2026-04-16):**

| State | Pairs | VERB | ROUND | OTHER | MARG |
|---|---|---|---|---|---|
| DRAFT | 25 | **4.0%** | 12.0% | 4.0% | **80.0%** |

### Provenance characterization

- All 22 versions are `created_by = 'system'` (v1 is `batch_reprocess`).
  None are operator-named. The `created_by` column does not appear to
  be populated from the regenerate script's `--created-by` flag in
  this league's history, or those regens went through a different
  path. **Treat `created_by` as not informative for arc identification.**
- `editorial_actions` is **empty** for W13 2025 across all 22
  versions. No NOTES, REGENERATE, WITHHOLD, OPEN, or APPROVE rows
  exist. Either editorial workflow has not been exercised on this
  recap, or the generation lifecycle does not write to that table
  for this league. **Treat editorial_actions as not informative for
  this case.**
- Six versions (v4, v7, v9, v11, v12, v14, v17) carry `approved_at`
  + `approved_by = 'steve'`. Five of those six are now SUPERSEDED.
  This is consistent with an "approve-and-checkpoint, then iterate"
  pattern — not "rejected for prose quality." A prior approval
  decision does not constitute a permanent contract; later approval
  of a newer version supersedes earlier ones.

---

## Probe 3 — v17 APPROVED PARAPHRASE_OTHER prose (load-bearing for Step 5)

`recap_artifacts.id=1026`, version 17, APPROVED at
`2026-04-09T00:20:24.621Z`. One pair classified PARAPHRASE_OTHER:
Italian Cavallini (149.95) vs. Eddie & the Cruisers (105.10).

Decimal-pair gap in prose: 174 chars. The actual prose:

> "Italian Cavallini put up 149.95 points to demolish Eddie & the
> Cruisers by nearly 45 points in Week 13's most lopsided result.
> Patrick Mahomes dropped 40 points for Michele, while Eddie managed
> just 105.10 despite getting 29 points from the Seattle defense."

This is **legitimately good prose**: both canonical scores present,
margin in natural language ("nearly 45 points"), player-level
attribution. The only reason it is not VERBATIM is that the bullet-
form score string `149.95-105.10` does not appear — the model
elected to reference each franchise's score in its own sentence
rather than render the paired form. **A reviewer (Steve) approved
this prose.** The reviewer's standard is therefore not "verbatim
score string mandatory."

A pre-rendered `"149.95 to 105.10"` source format would not change
this passage's structure — the narrative arc here calls for splitting
the scores across sentences with player-attribution context between
them.

---

## What this evidence supports

### Step 2 — pre-render in unambiguous format

**Proceed.** The hyphen-rounded ambiguity (`108-65` for `107.65/65.40`)
is observable in the data: 21.8% aggregate, 24.7% in Arc A, 36.7%
specifically among Arc A SUPERSEDED rows. That's not a rare hazard;
it's the dominant non-MARGIN_ONLY failure mode. Pre-rendering removes
the ambiguity at the source. Selected format: **`"{winner_score:.2f} to {loser_score:.2f}"`** —
e.g., `"107.65 to 65.40"`. Rationale:

- Robust to `_ascii_punct` normalization (no characters that pass
  through that normalizer change semantics).
- Reads naturally in the bullet form (`"X beat Y 107.65 to 65.40"`)
  and in narrative prose.
- En-dash carve-out adds maintenance surface; "vs." reads awkwardly
  alongside "beat".

The format choice is not load-bearing — any of the three brief
options would mechanically work. "to" is the lowest-friction default.

### Step 3 — verbatim-copy prompt instruction

**Proceed** with the brief's wording, adjacent to the existing
VERIFIED FACTS aggregate-count warning. The carve-out for margin
language is essential per the v17 evidence — the reviewer accepts
prose like "by nearly 45 points" alongside (or in lieu of) verbatim
score strings.

### Step 5 — verifier severity (Wave 2; deferred to Step 4 evidence)

The brief's selection rule is post-fix VERBATIM ≥95% → Policy A,
70–95% → Policy C, <70% → Policy B. **Step 1 evidence is pre-fix and
cannot drive this decision** — Step 4's post-fix observation is
the authority. However, two pieces of evidence shape the prior:

1. **Pre-fix VERBATIM rate is well below 70% in both arcs**
   (Arc A: 48.2%, Arc B: 4.0%). Expecting the post-fix rate to leap
   to ≥95% on prompt-rule strength alone is optimistic.
2. **Policy A would have rejected the v17 APPROVED prose** (the
   Cavallini/Eddie PARAPHRASE_OTHER pair). The reviewer accepted
   that prose. A verifier policy that auto-rejects prose the
   reviewer accepts is misaligned with reviewer judgment.

The Step 4 memo should weigh these against post-fix evidence. A
plausible default landing is **Policy C with HARD severity**, which
catches PARAPHRASE_ROUNDED while accepting PARAPHRASE_OTHER. Policy
A as a *first* landing is unlikely to be correct; Policy A may
become defensible after multiple weeks of post-fix evidence
demonstrate stable VERBATIM compliance. Policy B (SOFT) remains
defensible as a strict-diagnostic-posture starting position.

---

## Out of scope — flagged for follow-up

### Post-v17 regression thread

Score-string compliance collapsed sharply between Arc A and Arc B:

| Metric | Arc A (v1–v17) | Arc B (v18–v22) | Δ |
|---|---|---|---|
| VERBATIM | 48.2% | 4.0% | −44.2 pp |
| ROUNDED | 24.7% | 12.0% | −12.7 pp |
| MARGIN_ONLY | 25.9% | 80.0% | +54.1 pp |

The v18–v22 prose is overwhelmingly eliding scores entirely (80%
MARGIN_ONLY). This is not random drift across regens; the magnitude
and direction are too consistent. Most likely causes (not
investigated in this memo):

- Prompt-rule iteration between sessions changed the assembler's
  guidance to the model in a way that pushed it toward elision.
- Verifier-rule additions between sessions introduced rejection
  pressure that the model adapts to by avoiding score strings.
- A regression in the prompt-assembler code path that withholds
  the data the model needs to render scores correctly.

**Recommendation:** before generating the next live W14 2025 recap,
diagnose the v18+ regression. The diagnostic harness can be re-run
with `--season 2025 --week 14` once any draft exists; comparing v1–v5
of W14 to Arc A's v1–v17 would surface whether the regression
persists across weeks. If it does, Step 2's pre-rendering will not
fix it — the data layer can deliver the format faithfully and the
model can still elect to omit it.

This thread is its own diagnostic. Do not bundle with the Step 2
implementation.

### Editorial-actions population gap

`editorial_actions` is empty for all 22 W13 2025 versions despite
seven `approved_at` timestamps on `recap_artifacts`. Either:

- The lifecycle's approve-version path does not write to
  `editorial_actions` (only the editorial-workflow surface does).
- Approvals on this recap went through a path that bypasses
  editorial_actions.

This is a separate provenance gap. Out of scope here; flagged for
the audit-queries thread.

---

## Limitations of this memo's evidence

1. **No `prompt_audit` evidence.** Per the brief's diagnostic-first
   discipline, Step 1 is supposed to read "actual prose from
   `prompt_audit`" — i.e., the prompts that produced the prose, not
   just the rendered_text. This memo reads `recap_artifacts.rendered_text`
   only. The prompts that produced each version are not characterized.
   **Implication:** I cannot say whether v18+ failures reflect
   prompt-input changes or model-output changes. The post-v17
   regression follow-up should pull `prompt_audit` for several v18+
   versions before drawing conclusions.

2. **Apostrophe normalization not mirrored.** The harness skips
   production's `_normalize_apostrophes` step. If `franchise_directory.name`
   contains a curly apostrophe and prose contains a straight one
   (or vice versa), name-matching could miss. Spot-check of v17 and
   v22 samples did not surface obvious mismatches, but a small
   bias toward MARGIN_ONLY is possible.

3. **Single-recap evidence base for the regression thread.** Arc B
   is 5 versions of one recap. The "post-v17 regression" framing
   would be stronger with W12 or W14 evidence as a comparator.

4. **`created_by` is not informative for arc identification** in this
   league's history, contrary to the brief's expectation. Most or
   all regens recorded `'system'` rather than the operator name.
   Future memos should not rely on this column for distinguishing
   operator vs lifecycle actions.

---

## Sample row-IDs cited in this memo

| Recap ID | Season/Week | Version | State | created_at | Used as evidence for |
|---|---|---|---|---|---|
| 1026 | 2025/W13 | 17 | APPROVED | 2026-04-09T00:17:37.713Z | v17 PARAPHRASE_OTHER prose; reviewer-accepted standard |
| 1252 | 2025/W13 | 22 | DRAFT | 2026-04-16T23:43:24.493Z | v22 representative of Arc B regression (0/5 VERB, 2/5 ROUND, 3/5 MARG) |
| 780 | 2025/W13 | 9 | SUPERSEDED | 2026-04-04T16:12:44.425Z | Arc A SUPERSEDED with 5/5 VERBATIM, demonstrates that approval-then-supersession is a checkpoint pattern, not a quality rejection |
| 955 | 2025/W13 | 14 | SUPERSEDED | 2026-04-08T21:58:58Z | Arc A SUPERSEDED with 4/5 PARAPHRASE_ROUNDED, the dominant Arc A SUPERSEDED hazard pattern |

---

## Next actions in the brief's flow

1. This memo lands as commit 1 of Wave 1.
2. Step 2 — `format_matchup_score_str` helper + three render-site
   updates (per the brief, including `narrative_angles_v1.py:119,128`).
   Format: `"to"`.
3. Step 3 — verbatim-copy prompt instruction in `creative_layer_v1.py`
   between line 306 and line 307, with margin-language carve-out.
4. **Pause point** — operator-driven regen + Step 4 observation memo.
5. Wave 2 — Step 5 verifier addition with severity from Step 4 evidence,
   informed by this memo's prior on Policy A vs C.

Separately tracked, not in this brief:

- Post-v17 regression diagnostic.
- Editorial-actions population gap.

---

## Anti-drift discipline notes

- The harness was iterated three times this session (v2 →
  v3 → v3.1) in response to evidence: nickname-awareness,
  state-filter, classification-anchored snippets. v1 of the harness
  produced misleading results (selection-biased denominator); v3's
  snippets showed boilerplate not narrative. Each iteration's rationale
  is documented in the harness docstring.
- Diagnostic-first: every memo claim above traces to a probe output
  with a row ID and `created_at`. No claims rest on memory or on
  the brief's assumed model.
- The four-step plan's structure remains intact. This memo does not
  reopen Step 2's data-layer fix design or Step 5's policy
  alternatives — it provides the prior evidence for the decisions
  those steps make on their own timing.
