# Session Brief — Player-streak verb inversion diagnostic harness pass

**Drafted:** 2026-05-05 (read-only diagnostic preparatory material;
this brief is non-code preparatory material and lands as a single
doc commit when the session begins).

**Predecessor work:**
- §10 Q1 paired thread closure (T9-LOSS form gap + HEADLINE
  budget eviction). Whatever commits result from that session.
- Tier 1 micro-threads following §10 Q1 closure: operator regen
  of W11 2025 id=140 + post-fix observation memo, parametrized
  helper-bound verifier test (standing backlog #10).
- `_observations/OBSERVATIONS_2026_05_04_STREAK_VERB_PRE_COMPUTATION_SCOPE.md`
  §3.2 — names the three player-streak emitters as out-of-scope
  for the team-streak thread, with explicit promotion criterion:
  *"If post-Step-3.3 measurement shows player-streak verb
  inversions in the wild, those become a separate four-step
  thread."*
- Streak-verb thread closure (`6e7d44a` / `71d6e5f` / `7d891aa`)
  and Cat 3c hardening (`e4c2df8`) — the proven four-step
  playbook this thread either promotes (if evidence surfaces) or
  closes as named-only-no-evidence.
- Score string pre-rendering thread closure (`ff613a9` /
  `46c2ca5` / `1db5cbd`) — the prior application of the same
  four-step playbook; relevant as precedent for pace and shape.

**Starting commit:** TBD. Verify HEAD before any other action;
record at session start. Expected starting state: post-§10 Q1
HEAD with Tier 1 micro-threads merged (regen artifact + memo +
parametrized helper-bound test).

**Working tree:** `/Users/steve/projects/squadvault-ingest-fresh`

**Phase:** 10 — Operational Observation.

**Shape:** Diagnostic-only session, single wave. **No
production-path code changes regardless of outcome.** Decision
artifact at the end: promote four-step thread (with named
follow-on session brief outline) or close standing-backlog item
#5 as no-evidence.

**Expected session length:** 60–90 minutes. One to two commits
expected (doc-only memo if existing diagnostic infrastructure
can be reused; harness-extension code commit + memo if a new
module is needed).

---

## Preamble check

At session-start HEAD (after §10 Q1 closure + Tier 1 micro-
threads), record SHA-256 hashes for the three production files
this session will read but not modify:

```bash
shasum -a 256 \
  src/squadvault/core/recaps/context/player_narrative_angles_v1.py \
  src/squadvault/core/recaps/render/streak_strings_v1.py \
  src/squadvault/core/recaps/verification/recap_verifier_v1.py
```

The hashes are recorded for audit trail only — the diagnostic
harness imports detector functions directly, so production-path
drift does not invalidate the harness output, but the recorded
hashes anchor any specimen analysis to a known production state.

Test/lint baseline: record at session start. Expected post-§10
Q1 + Tier 1: `1947 passed / 2 skipped` (full session) or
`1944 passed / 2 skipped` (Step 3 deferred), plus `+1` from the
parametrized helper-bound verifier test if shipped under Tier 1.
Ruff `src/ Tests/` clean; mypy `src/squadvault/core/` clean.

---

## Why this session, and what it determines

The team-streak thread (Step 3.1 / 3.2 / 3.3) shipped a
four-step playbook closure for status-verb inversions on team
W-L streaks. Its scope memo §3.2 explicitly named three
player-level emitters as out-of-scope on the rationale that
"player-level streak" is a different sense of the word —
consecutive scoring weeks (P1/P2) or consecutive seasons on a
roster (P3) rather than consecutive wins/losses.

Three call sites in `player_narrative_angles_v1.py`, with
canonical phrasings verified at HEAD `bddc600`:

| # | Function | Emitter line | Canonical phrasing |
|---|---|---|---|
| P1 | `detect_player_hot_streak` | 754 | `"{player} has scored {threshold:.0f}+ points in {N} consecutive weeks for {franchise}"` |
| P2 | `detect_player_cold_streak` | 806 | `"{player} has scored under {threshold:.0f} points in {N} straight starts for {franchise}"` |
| P3 | `detect_player_franchise_tenure` | 1332 | `"{player} has been on {franchise}'s roster for {N} consecutive seasons"` |

Note that P3's canonical is fuller than the scope memo's
abbreviated `"... for {N} consecutive seasons"` — the full
emitter binds the player-name and franchise-name explicitly into
a possessive construction (`{franchise}'s roster`). This matters
for franchise-mismatch classification.

The promotion criterion from §3.2 is empirical: do model
paraphrases of these forms invert direction (over/under),
distort duration semantics ("consecutive" → "across the last"),
or mis-attribute franchise? **If yes**, the four-step playbook
applies (helper module `player_streak_strings_v1`, consumer
refactor at three call sites, prompt extension paralleling §6,
verifier extension paralleling Cat 3 streak-verb checks). **If
no**, the named-only standing-backlog item closes.

This session is the empirical arbiter. Diagnostic-first; no
production code changes regardless of outcome.

The pattern this thread re-enacts: **don't pre-commit to a
four-step thread; measure first.** The team-streak thread
surfaced 5/13 fabrications on a single fixture week before
promotion was justified. Player-streak surface area is smaller
(3 emitters vs 17 team-streak call sites) and the prompt-level
pressure differs — there is no parallel §6-style instruction yet
for player-streak phrasings, and §6's enumeration explicitly
excludes player-streak shapes (per the §10 Q1 brief's revision
discussion of §6 enumeration scope).

---

## Scope

### In scope

1. **Helper-bound canonical inventory.** Inspect P1/P2/P3
   emitters at session start and reverify exact canonical
   phrasings against the table above. If the emitter strings
   have drifted post-§10 Q1, update the harness regex
   constants accordingly.

2. **Diagnostic harness extension or new module.** Two paths,
   decision deferred to Step 0:
   - **(a) Extend** an existing harness in `scripts/` if one is
     already player-streak-aware. First action of Step 0 is a
     find/grep pass to inventory.
   - **(b) New module** `scripts/diagnose_player_streak_verb_inversions.py`
     if no existing module fits.

3. **Per-claim classification across approved 2025 corpus.**
   Seven categories:
   - `DIRECTION_INVERSION` — hot/cold direction in prose
     disagrees with canonical. e.g., model writes "scored over
     10 points" when canonical is "scored under 10 points"
     (cold streak prose flipped to hot streak). **Integrity-
     tier signal.**
   - `FRANCHISE_MISMATCH` — claim attributed to wrong franchise
     vs canonical (typically a player-traded-midseason shape).
     **Integrity-tier signal.**
   - `THRESHOLD_INVERSION` — scoring threshold N differs from
     canonical (e.g., canonical "20+" → prose "15+"). **Integrity-
     tier signal.**
   - `DURATION_DRIFT` — "consecutive weeks/starts/seasons" →
     "across the last X weeks" or "in the last X games" or
     similar precision-loss paraphrase. **Editorial-tier
     signal.**
   - `TENURE_NON_CONSECUTIVE` — P3 specifically: tenure claim
     drops or distorts the "consecutive" qualifier (e.g., "has
     played 8 seasons" omitting the consecutiveness qualifier).
     Consecutive vs total tenure is not a paraphrase.
     **Integrity-tier signal.**
   - `CORRECT` — prose matches canonical or paraphrases without
     semantic loss.
   - `NO_CLAIM` — no player-streak claim for this (player,
     emitter) tuple in this row's prose.

4. **Run against approved 2025 corpus.** Query at session start:

   ```sql
   SELECT COUNT(*) FROM recap_artifacts WHERE state = 'APPROVED';
   ```

   Memory note records "35 approved recaps" from a prior session;
   actual count may differ. Cite actual count in the memo.

5. **Decision memo.** Apply the two-tier evidence gate (mirrors
   §10 Q1 brief two-tier construction):

   - *Integrity tier:* any non-zero `DIRECTION_INVERSION`,
     `FRANCHISE_MISMATCH`, `THRESHOLD_INVERSION`, or
     `TENURE_NON_CONSECUTIVE` count → promote thread
     unconditionally. Memo records specimens; appended scaffold
     names follow-on session structure.
   - *Editorial tier:* zero integrity-tier signals AND non-zero
     `DURATION_DRIFT` → editorial decision; explicit YES/NO from
     Steve recorded in memo per silence-vs-density tradeoff.
     `DURATION_DRIFT` is precision-loss, not direction-loss; per
     the silence-over-speculation principle, defaulting to defer
     is constitutionally consistent.
   - *Close tier:* both zero → close standing-backlog item #5.
     Memory edit removes the named-only item; memo documents
     "no evidence in approved corpus as of <date>; reconsider on
     observation drift."

### Out of scope

- **Any production-path code change.** Diagnostic-only session.
  The four-step playbook (helper / consumer / prompt / verifier)
  starts in a follow-on session if promoted.
- **Detector re-validation.** This thread does not re-investigate
  whether `detect_player_hot_streak` / `detect_player_cold_streak`
  / `detect_player_franchise_tenure` correctly identify their
  target shape. The team-streak thread's reframe-memo lesson
  stands: "the detector is not the problem" was that thread's
  finding; this thread does not re-litigate detection.
- **Helper module construction.** `player_streak_strings_v1` is
  a follow-on artifact, not an in-session deliverable.
- **Prompt extension.** A parallel §6-style instruction for
  player-streak phrasings is post-promotion work.
- **Verifier extension.** A parallel `verify_player_streak_claims`
  rule is post-promotion work.
- **W14+ live observation.** This session uses approved-corpus
  rows only. Live observation is Tier 5 in the post-§10 Q1
  development direction and runs on its own cadence.
- **Architecture or governance changes.** No.
- **Reverify-as-merge-gate.** Diagnostic session has no merge
  gate beyond the standard ruff/mypy/pytest gates on the
  harness-extension commit (if shipped); the memo is doc-only.

---

## Step-by-step decomposition

### Step 0 — Re-grounding and harness inventory

Verify HEAD, baseline tests/ruff/mypy, inventory existing
player-aware diagnostic infrastructure, decide harness path:

```bash
git rev-parse HEAD
pytest -q 2>&1 | tail -3
ruff check src/ Tests/
mypy src/squadvault/core/
find scripts/ -name "*player*" -o -name "*diagnose*"
grep -rn "detect_player_hot_streak\|detect_player_cold_streak\|detect_player_franchise_tenure" \
  scripts/
sqlite3 .local_squadvault.sqlite \
  "SELECT COUNT(*) FROM recap_artifacts WHERE state = 'APPROVED';"
```

If existing harness already imports any of P1/P2/P3 detectors,
extend in-place per the standing scripts/ discipline (one new
classifier function, gate-passes). If not, commit 1 is a new
harness module per Step 0a below.

### Step 0a — Harness extension or new module (code commit)

Either path is one commit, ruff/mypy/pytest gated, staging gate
+ banner paste gate + no-xtrace + repo-root allowlist.

If new module: `scripts/diagnose_player_streak_verb_inversions.py`.
Read-only diagnostic. The harness needs:

- Query approved-state rows from `recap_artifacts` joined to
  `prompt_audit` for `narrative_draft` and `narrative_angles_text`
  text.
- For each row, re-run the three detectors against the stored
  (db_path, league_id, season, week) context to reconstruct
  canonical angles. **This is required because
  `prompt_audit.angles_summary_json` strips `franchise_ids` and
  `headline` per `prompt_audit_v1.py:174`** — the audit summary
  is insufficient for counterfactual angle reconstruction. Same
  pattern as §10 Q1 Step 0a.
- Per-claim classifier: for each (row, player, emitter) tuple,
  compare prose against canonical phrasing and bucket per the
  seven-category scheme above.
- Output: row-level CSV or markdown table to stdout + summary
  counts. No file writes by default; `--write-csv` flag for
  follow-up reference.

Suggested commit message:

```
scripts/diagnose_player_streak_verb_inversions: classifier
for P1/P2/P3 verb inversions (streak-verb scope memo §3.2)

Diagnostic-only harness for player-streak verb inversions per
the streak-verb scope memo §3.2 promotion criterion. Re-runs
detect_player_hot_streak / detect_player_cold_streak /
detect_player_franchise_tenure against approved-corpus rows
and classifies prose disagreement across seven categories
(DIRECTION_INVERSION, FRANCHISE_MISMATCH, THRESHOLD_INVERSION,
DURATION_DRIFT, TENURE_NON_CONSECUTIVE, CORRECT, NO_CLAIM).

Implementation note: classification requires per-row
counterfactual angle reconstruction (re-running the three
detectors against the stored season/week context) since
prompt_audit.angles_summary_json strips fids/headlines per
prompt_audit_v1.py:174.

No production-path changes. Output of this harness against the
approved corpus is cited in the matching observation memo.
```

### Step 0b — Diagnostic memo (doc commit)

Run the harness. Cite bucket counts. Apply the two-tier evidence
gate. Memo naming:
`_observations/OBSERVATIONS_<YYYY_MM_DD>_PLAYER_STREAK_VERB_DIAGNOSTIC.md`

Memo body sections:

1. **Why this session.** Link to §3.2 scope memo; brief restate
   of the promotion criterion.
2. **Harness output.** Per-emitter counts (P1, P2, P3 in three
   tables); total approved-corpus row count; classification
   distribution.
3. **Specimen analysis.** For any non-zero integrity-tier
   signal, full prose excerpt + canonical phrasing comparison +
   row id + row context (season, week). For editorial-tier
   signals, abbreviated specimens (one or two representative).
4. **Decision.** Promote / editorial-elect / close, with explicit
   gate-tier identification. Mirror the §10 Q1 brief's gate
   labeling for memo-style consistency.
5. **Memory edits performed.** Standing-backlog item #5 update
   (closure language varies by decision tier).
6. **(If promote)** Follow-on session brief outline. Not a full
   brief — just a scaffold naming helper module signature,
   consumer-refactor scope, prompt-extension shape, verifier-
   extension shape. The follow-on session would draft a full
   brief from this scaffold.

If decision is *promote*: outline section 6 names:

- Helper module: `src/squadvault/core/recaps/render/player_streak_strings_v1.py`.
  Pure helper, no I/O. Signatures:
  - `format_player_hot_streak(player, threshold, streak, franchise) -> str`
  - `format_player_cold_streak(player, threshold, streak, franchise) -> str`
  - `format_player_tenure(player, franchise, streak) -> str`
- Consumer refactor: replace inline f-strings at lines 752-755,
  804-807, 1330-1333 with helper calls. One commit per emitter
  per one-topic-per-commit discipline. Three commits.
- Prompt instruction: extend creative_layer_v1.py with a
  parallel block to §6 enumerating player-streak phrasings and
  silence-fallback. One commit.
- Verifier extension: `verify_player_streak_claims` paralleling
  `verify_streak_verbs_verbatim`. Cat 3-class severity, HARD on
  direction inversions and franchise mismatches, SOFT (or no
  rule) on duration drift. One commit. Includes Cat 3-style
  helper-bound test feeding `format_player_*` output through
  `_player_anchor_present`.

If decision is *close*: section 6 omitted. Memory edit closes
standing-backlog item #5 with conditional reopening clause:
"closure is 'no evidence in current corpus'; if W14+ live
observation surfaces specimens, re-promote."

---

## Diagnostic harness design notes

### Per-emitter classification logic

**P1 — `detect_player_hot_streak`.**

Canonical: `{player} has scored {threshold:.0f}+ points in {N} consecutive weeks for {franchise}`.

Verb-inversion shapes (regex constructed at runtime per
canonical-angle tuple):

```python
_P1_DIRECTION_INVERSION = re.compile(
    rf"\b{re.escape(player_name)}\s+(?:has\s+)?scored\s+under\s+{threshold:.0f}",
    re.IGNORECASE,
)  # canonical is "{N}+", inversion is "under N"

_P1_DURATION_DRIFT = re.compile(
    rf"\b{re.escape(player_name)}\s+(?:scored|has\s+scored)\b.*?"
    rf"(?:in\s+the\s+last|across\s+the\s+last|over\s+the\s+last|"
    rf"in\s+\d+\s+of\s+the\s+last)\s+\d+",
    re.IGNORECASE,
)  # canonical is "consecutive", drift is "in/across/over the last"

# THRESHOLD_INVERSION: scan prose for `{player} ... scored {N}+`
# where N != canonical threshold; cross-reference at runtime.
# FRANCHISE_MISMATCH: scan prose for `{player} ... for {franchise}`
# where franchise != canonical franchise alias set.
```

**P2 — `detect_player_cold_streak`.**

Canonical: `{player} has scored under {threshold:.0f} points in {N} straight starts for {franchise}`.

Inversion shapes mirror P1 with direction reversed. The
integrity-critical inversion is "under" → "over" or "{N}+" — a
player drought becoming a hot streak in prose. Duration-drift
shape is symmetric with P1.

**P3 — `detect_player_franchise_tenure`.**

Canonical: `{player} has been on {franchise}'s roster for {N} consecutive seasons`.

Inversion shapes:

```python
_P3_TENURE_NON_CONSECUTIVE = re.compile(
    rf"\b{re.escape(player_name)}\b[^.]*?"
    rf"\b(?:has\s+played|been\s+with|on\s+the\s+roster)\b[^.]*?"
    rf"\d+\s+(?:season|year)s?",
    re.IGNORECASE,
)  # matches tenure claim shapes that may omit "consecutive"
# Then post-filter: if "consecutive" is NOT in the matched span,
# classify as TENURE_NON_CONSECUTIVE.

_P3_FRANCHISE_MISMATCH: cross-reference {franchise}'s roster vs
prose-attributed franchise.
```

P3 prose typically embeds the tenure phrase inside a longer
sentence; the classifier scope is the sentence containing the
player + franchise + season-count.

### Counterfactual reconstruction

Mirrors §10 Q1 Step 0a pattern. The three detectors are pure
functions of `(db_path, league_id, season, week)` per
established convention. Re-running them against the same context
the production pipeline saw yields the canonical angles
regardless of how the audit summary was serialized.

```python
from squadvault.core.recaps.context.player_narrative_angles_v1 import (
    detect_player_hot_streak,
    detect_player_cold_streak,
    detect_player_franchise_tenure,
)

p1_angles = detect_player_hot_streak(
    db_path=db_path, league_id=league_id, season=season, week=week,
)
# Each angle yields (player_id, threshold, streak, franchise_id) tuple
# from the headline f-string params; classifier uses these to build
# the runtime regexes.
```

### Sample size sufficiency

Approved-corpus row count × claims-per-row matters here. Memory's
"35 approved recaps" gives a rough sense; assume ~10 player-
streak claims per recap × 3 emitters yields ~1,050 candidate
classifications. Order-of-magnitude — actual count depends on
how often any single recap fires P1/P2/P3 emitters.

If the corpus shows zero integrity-tier signals AND zero
editorial-tier signals AND most candidates classify `NO_CLAIM`
(i.e., the model rarely makes player-streak claims at all), the
result is ambiguous — surface area too small to validate
falsifiably. Memo's decision in that case is *close-with-
watchpoint*: close standing-backlog item #5 but document the
ambiguous-corpus reading and add a memory note to re-investigate
on observation drift in W14+ live processing.

This is a real possibility. Player-streak emitters fire less
frequently than team-streak emitters because the threshold (P1
needs 5+ weeks for HEADLINE, P2 needs 4+ straight starts for
HEADLINE, P3 needs 3+ consecutive seasons) is shape-different
from team-streak detection (W-L count off the standings). If
the corpus reflects a typical season distribution, the candidate
pool may be small.

---

## Predicted commit count and shape

One to two commits:

| # | Type | Conditional | Notes |
|---|---|---|---|
| 1 | Code (harness) | Only if new module needed | `scripts/diagnose_player_streak_verb_inversions.py`; full ruff/mypy/pytest/staging/banner/no-xtrace/allowlist gate |
| 2 | Doc (memo) | Always | `_observations/OBSERVATIONS_<date>_PLAYER_STREAK_VERB_DIAGNOSTIC.md`; cites harness output; carries decision artifact |

Plus optional commit 3 (memory edits via `memory_user_edits`
tool calls) — outside the repo, but discipline note: standing-
backlog item #5 update should match the memo's decision tier
exactly. Memory edit timing: after the memo lands, not before.

**Test count math.** Diagnostic harness adds zero pytest cases.
Final expected count = baseline.

---

## Known gotchas

### Detector locations may have shifted post-§10 Q1

The §10 Q1 brief touches `narrative_angles_v1.py` (team-streak
detector), not `player_narrative_angles_v1.py`. Player-streak
detector locations should be stable through that thread. Re-
verify line numbers at session start regardless — production
code drift is the standing assumption.

The verified line numbers at HEAD `bddc600` are 754, 806, 1332.
The scope memo §3.2's cited "752–755, 804–807, 1330–1333" line
ranges are slightly stale (off by 0–2 lines).

### Approved-corpus count may have shifted

Memory: 35 approved recaps. Actual count at session start may
differ. Query at Step 0; cite actual count in memo. The two-tier
gate is unaffected by corpus size; only the *strength of
inference* depends on it.

### Player-name aliasing

Player-streak prose uses player names directly (no franchise-
name aliasing layer like the team-streak thread needed). However:

- Players with common first names ("Josh", "Aaron") may produce
  attribution ambiguity in the harness.
- Recent name changes or trade-midseason events may produce
  franchise-attribution ambiguity (a player canonically tagged
  to franchise X for the angle but referenced in prose for
  franchise Y because of a trade).

Treat ambiguous specimens as `MANUAL_REVIEW` rather than
auto-classifying; document them explicitly in the memo.

### §6 silence-fallback does NOT cover player-streak phrasings

Per the §10 Q1 brief's revision discussion (and verified at
`creative_layer_v1.py:281–291`), the §6 prompt instruction
enumerates only team-streak phrasings (T1/T2/T3 status, T5/T6
outcome). Player-streak emitters get no §6-style canonical-
phrasing-or-silence directive.

This means: if `DIRECTION_INVERSION` or `FRANCHISE_MISMATCH`
specimens surface, they are not failures of an existing prompt
guardrail — they are fabrications occurring in the absence of
any guardrail. The four-step thread (if promoted) would *add*
the guardrail; the diagnostic measures whether it's needed.

The asymmetric implication: a player-streak fabrication is
strong evidence the guardrail belongs in place. A team-streak
fabrication, by contrast, is evidence of guardrail leakage
because §6 already exists to prevent it.

### What the team-streak thread learned applies here

- Data-layer fixes are strong; prompt guardrails are weak. If
  promoted, the prompt instruction is a complement to the
  helper-supplied canonical phrasings, not a substitute.
- Verifier coverage is asymptotic. The follow-on four-step
  thread should ship the four canonical inversion shapes
  enumerated above, then let observation drive expansion.
- Read the prose before proposing a fix. The seven-category
  classifier is a starting point; specimen analysis in the memo
  may reveal a fifth or sixth bucket worth promoting.
- Chat-rendering hazard (per memory): the mobile/web chat client
  auto-links bare `_v1.py` substrings to fake URLs in displayed
  echo. Pasted `cp` commands LOOK like their destinations are
  mangled but actual bytes pass through unchanged. Verify with
  `git status` showing modifications at canonical paths, not
  from the rendered echo.

---

## Fixture set

Approved 2025 corpus rows from `recap_artifacts WHERE state =
'APPROVED'`. No specific weeks pre-selected; the harness scans
all approved rows. Specimen retention: any row classified with
an integrity-tier signal is preserved verbatim in the memo body
for follow-on session reference.

---

## Open questions

### Q1 — Editorial-tier threshold for `DURATION_DRIFT`

If the corpus shows zero integrity-tier signals AND non-zero
`DURATION_DRIFT`, what's the threshold for ship vs defer?
`DURATION_DRIFT` is precision-loss, not direction-loss — "scored
20+ in 3 of the last 4 weeks" instead of canonical "scored 20+
in 3 consecutive weeks" is technically a different claim but
does not fabricate from cloth.

**Default:** defer absent egregious distortion (>10% of
candidate claims drifting). Editorial decision recorded in memo.
The silence-over-speculation principle defaults to defer; the
asymmetry is that *promoting* a four-step thread for editorial-
tier evidence imposes guardrails that may suppress legitimate
prose variation, while *deferring* leaves a known precision-loss
risk unaddressed.

### Q2 — Does P3 (franchise tenure) belong in this thread?

P3 is structurally different from P1/P2 — it's a tenure claim,
not a scoring-streak claim. The team-streak thread treated W-L
streaks as a single category; this thread treats player-scoring
and player-tenure as a single category for diagnostic
convenience.

**Default:** include P3. If specimens come back showing P3 has
a different inversion-shape distribution than P1/P2, the
follow-on four-step thread can split them — `player_streak_strings_v1`
covers P1/P2 and a separate `player_tenure_strings_v1` (or a
single combined module with two function families) covers P3.

### Q3 — Live W14+ observation as a concurrent track

If this session closes standing-backlog item #5 with no
evidence, but live W14+ observation later surfaces specimens,
re-promote? **Default:** yes. Closure is "no evidence in current
corpus", not "no possible evidence". The standing-backlog memory
edit should reflect this conditional explicitly.

### Q4 — Should the harness output be retained as a reverify-tag-style baseline?

The team-streak thread used `reverify_tag` SQL queries against
`prompt_audit_reverify` as a merge gate. This diagnostic session
has no merge gate (doc-only memo), but the harness output itself
could be tagged for future re-runs to detect drift in production
behavior over time.

**Default:** not in this session. If the four-step thread
promotes, its merge gate would re-run this harness as part of
the post-fix probe. Adding a tagging mechanism now for a
diagnostic that may close-without-promotion is over-engineering.

---

## Standing backlog (carries forward post-§10 Q1)

Updated assuming §10 Q1 closed cleanly (Step 3 ship-gated by
either tier; either ship or deferred outcome) and Tier 1 micro-
threads merged:

1. **(THIS SESSION when run)** Player-streak verb inversion
   diagnostic harness pass.
2. SCORE_VERBATIM 59-row legacy drift (open horizon thread).
3. Cat 3c row-76 W14 2025 attribution edge case (open horizon,
   deferred — does not affect detection, only label).
4. Snap-outcome detection (memo §10 Q2, named-only).
5. **(Updated by this session per decision)** Player-streak
   verb inversion thread — promoted to scoped four-step thread
   (with named follow-on session brief) OR closed as no-evidence
   (with re-promotion clause if W14+ live surfaces specimens).
6. NOTABLE-pass alphabetical lockout investigation (named-only;
   promote-conditional on §10 Q1 Stage A surfacing).
7. Tests/ ruff cleanup.
8. `d['raw_mfl']` write at `extract_recap_facts_v1.py:190`
   (deferred).
9. **(If §10 Q1 Step 3 deferred)** HEADLINE budget eviction
   follow-on session.
10. Parametrized helper-bound verifier test — closed if Tier 1
    micro-thread shipped post-§10 Q1 closure.

If decision tier is *promote*, item 5 becomes the next active
thread and Tier 5 (W14+ live observation per the post-§10 Q1
direction memo) defers further. If decision tier is *close* or
*editorial-defer*, Tier 5 becomes the next active focus.

---

## Anti-drift discipline

1. Re-grounding is session step 0. Verify HEAD, record actual
   test/lint baseline, inventory existing player-aware
   diagnostic infrastructure before any other action.
2. Diagnostic-first applies. No production code changes
   regardless of harness output. The four-step playbook (helper
   / consumer / prompt / verifier) is post-promotion work in a
   separate session.
3. The two-tier evidence gate is the decision mechanism;
   integrity-tier signals promote, editorial-tier signals
   elect, both-zero close. The gate is the same shape as the
   §10 Q1 brief's two-tier gate to maintain pattern consistency.
4. One topic per commit (1 or 2 commits; harness extension
   separate from memo).
5. Memory may be stale; the artifact trail is authoritative. If
   any line number or canonical phrasing has drifted from this
   brief's table, stop and re-ground before running the harness.
6. The team-streak thread's reframe-memo lesson: detector is
   rarely the problem. This session does not re-investigate
   detection — only prose-vs-canonical disagreement.
7. Helper-bound discipline: the follow-on four-step thread (if
   promoted) routes every canonical-phrase reference through
   `player_streak_strings_v1`. The diagnostic harness in this
   session does not yet have a helper to route through;
   classifier regexes are inline. The follow-on thread tightens
   this.
8. `_observations/` is the correct location for the memo — not
   repo root. `Tests/test_repo_root_allowlist_v1.py` enforces
   exactly 5 files at root; a memo at root fails CI on push but
   passes the local pre-commit hook (the local/CI divergence
   memory note flags this as a recurring trap).

---

## Opening move

```
cd ~/projects/squadvault-ingest-fresh
git fetch origin
git rev-parse HEAD                       # record
shasum -a 256 \
  src/squadvault/core/recaps/context/player_narrative_angles_v1.py \
  src/squadvault/core/recaps/render/streak_strings_v1.py \
  src/squadvault/core/recaps/verification/recap_verifier_v1.py
pytest -q 2>&1 | tail -3                 # baseline
ruff check src/ Tests/                   # confirm zero
mypy src/squadvault/core/                # confirm clean
find scripts/ -name "*player*" -o -name "*diagnose*"
grep -n "def detect_player_hot_streak\|def detect_player_cold_streak\|def detect_player_franchise_tenure" \
  src/squadvault/core/recaps/context/player_narrative_angles_v1.py
sqlite3 .local_squadvault.sqlite \
  "SELECT COUNT(*) FROM recap_artifacts WHERE state = 'APPROVED';"
```

Then Step 0 — decide harness path (extend existing vs new
module). If new module: Step 0a (harness extension, code-only
commit, full gate). Step 0b (diagnostic memo, doc-only commit)
follows in either path. Apply two-tier evidence gate. Update
standing backlog per decision tier.

---

## The point

The streak-verb thread closure left a named-only follow-up in
§3.2: player-streak verb inversions. This session is the
empirical arbiter — diagnostic-only, decision-bearing.

Promote the four-step thread if integrity-tier signals exist
(direction inversion, franchise mismatch, threshold inversion,
non-consecutive tenure distortion). Close standing-backlog item
#5 if not. Either outcome is a useful artifact; neither is a
four-step playbook execution.

Diagnostic first. Specimens before promotion. One session
decides whether the next major thread is structural (player-
streak playbook) or operational (W14+ live observation per
Tier 5 of the post-§10 Q1 development direction).
