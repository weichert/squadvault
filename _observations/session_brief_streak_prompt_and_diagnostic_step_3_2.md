# Session Brief — Step 3.2 streak prompt instruction + diagnostic harness

**Drafted:** 2026-05-04 UTC.

**Predecessors:**
- `30dd16f` — Step 3 audit memo committed.
- `6e7d44a` — Step 3.1 helper module + refactor shipped (43 new
  tests, behavioral parity proven against W13 2024
  narrative_angles_text byte-diff id=124 vs id=129).

**Starting commit:** `6e7d44a` on `main`. Verify before any other action:

```
git log -1 --oneline
```

Must show:
`6e7d44a core/recaps: introduce streak_strings_v1 helper, ...`.

**Working tree:** `/Users/steve/projects/squadvault-ingest-fresh`.

**Phase:** 10 — Operational Observation.

**Shape:** Multi-commit landing. The brief produces three artifacts
that should land as separate commits per the one-topic-per-commit
discipline:

1. **Doc commit** — this brief itself, plus the diagnostic harness
   tracked under `scripts/`. Rationale for tracking the harness:
   the score thread's `step_1_score_diagnostic_harness.py` lived in
   /tmp and was lost; that lesson is canonicalized in userMemories
   as "No /tmp artifacts treated as durable across sessions."
   Tracked harness = re-runnable diagnostic across sessions.
2. **Prompt commit** — `creative_layer_v1.py` insertion of the
   streak-verbatim instruction per memo §6, plus pre-fix
   observation memo capturing the BASELINE harness run (drafts
   under the OLD prompt, no streak instruction).
3. **Post-fix commit** — post-fix observation memo capturing
   POST-FIX harness run (drafts under the NEW prompt, with streak
   instruction). Includes policy decision (HARD vs SOFT, per-template
   if needed) for Step 3.3 to consume as its precondition.

**Expected session length:** 2–3 sessions. The harness runs against
DB state which Steve must drive; this brief assumes a single live
operator running the diagnostic locally between commits.

---

## What this brief does

Lands Step 3.2 of the four-step playbook for streak verbs:

- Adds the prompt instruction draft from audit memo §6 to
  `creative_layer_v1.py` immediately after the existing
  `parts.append(narrative_angles.strip())` at line 279.
- Adds a tracked diagnostic harness `scripts/step_1_streak_diagnostic_harness.py`
  that mirrors the score-thread Step 1 pattern, classifying each
  STREAK claim emitted in `narrative_angles_text` against the
  model's `narrative_draft` prose into VERBATIM / PARAPHRASE /
  INVERTED / OMITTED.
- Captures BASELINE (pre-fix, OLD prompt) and POST-FIX (NEW prompt)
  measurements in two observation memos.
- Records policy decision (HARD vs SOFT, per-template if needed) for
  Step 3.3 to consume.

What this brief does NOT do:

- No verifier change. `recap_verifier_v1.py` stays untouched —
  Step 3.3's job.
- No new angles. The angle-detection layer is unchanged.
- No threshold changes. `_detect_streaks` and
  `_detect_streak_records` continue to fire on the same
  |streak| >= 3 / |streak| >= record - 1 boundaries.
- No new prompt instructions beyond the streak block in §6.
- No coverage-gap fixes. Memo §10 Q1 (asymmetric record-approach)
  and Q2 (won-from-losing snap) remain out of scope.

---

## The change at a glance

### Code

| File | Change |
|------|--------|
| `src/squadvault/ai/creative_layer_v1.py` | Insert one `parts.append(...)` between line 279 and line 280, inside the `if narrative_angles:` block, with the §6 instruction text. |
| `scripts/step_1_streak_diagnostic_harness.py` | New tracked file. Imports canonical helpers from `streak_strings_v1`; reads `prompt_audit` rows; classifies STREAK claims. |

### Docs

| File | Type | Notes |
|------|------|-------|
| `_observations/session_brief_streak_prompt_and_diagnostic_step_3_2.md` | New | This brief, doc-only. |
| `_observations/OBSERVATIONS_2026_05_04_STREAK_PROMPT_PRE_FIX_DIAGNOSTIC.md` | New | Baseline measurement, doc-only. Lands with prompt commit (Commit 2). |
| `_observations/OBSERVATIONS_2026_05_04_STREAK_PROMPT_POST_FIX_OBSERVATION.md` | New | Post-fix measurement + policy decision, doc-only. Lands as Commit 3. |

---

## Steps

### Step 0 — Re-grounding

```
cd ~/projects/squadvault-ingest-fresh
git fetch origin
git rev-parse --short HEAD
git log -1 --oneline
```

HEAD must be `6e7d44a`. Re-read audit memo §3 (call sites), §4
(taxonomy), §6 (prompt instruction), §7 (verifier sketch — for 3.3),
§8 (sequencing) before starting.

### Step 1 — Land Commit 1 (brief + harness)

```
cp ~/Downloads/session_brief_streak_prompt_and_diagnostic_step_3_2.md \
   _observations/session_brief_streak_prompt_and_diagnostic_step_3_2.md
cp ~/Downloads/step_1_streak_diagnostic_harness.py \
   scripts/step_1_streak_diagnostic_harness.py

# Smoke test the harness
python3 scripts/step_1_streak_diagnostic_harness.py --help

# Stage and confirm
git add -A
git diff --cached --stat
# Expect: 2 files (1 new in _observations/, 1 new in scripts/)

git commit -F - <<'MSG'
session_brief + harness: Step 3.2 streak prompt instruction + diagnostic

Lands the session brief and the tracked diagnostic harness for
the streak verb pre-computation thread's prompt+diagnostic phase.

The harness adapts the score-thread step_1_score_diagnostic_harness.py
pattern (which lived in /tmp during the score thread and was
unrecoverable post-session). Tracked under scripts/ per the
canonicalized lesson: no /tmp artifacts treated as durable.

Classifies each STREAK claim emitted in narrative_angles_text
against the model's narrative_draft into:
  VERBATIM   — canonical phrasing as substring
  PARAPHRASE — franchise named, fact preserved, not verbatim
  INVERTED   — franchise named, direction or verb wrong
  OMITTED    — franchise not named at all (silence is fine)

Helper-bound: canonical phrases come from streak_strings_v1
helpers, never hand-written. V8 follow-up lesson applied.

Step 3.2 of the four-step playbook from
_observations/OBSERVATIONS_2026_05_04_STREAK_VERB_PRE_COMPUTATION_SCOPE.md.

Doc-only + new script. No source or test changes.
MSG
```

### Step 2 — Run baseline diagnostic (pre-fix, OLD prompt)

```
# Last 10 approved recaps cross-season:
python3 scripts/step_1_streak_diagnostic_harness.py \
    --db .local_squadvault.sqlite \
    --league-id 70985 \
    --scope last10-approved \
    > /tmp/baseline_last10.txt 2>&1

cat /tmp/baseline_last10.txt | tail -30
```

Optionally also run the W13 all-states scope to compare lifecycle
state distributions:

```
python3 scripts/step_1_streak_diagnostic_harness.py \
    --db .local_squadvault.sqlite \
    --league-id 70985 \
    --scope week --season 2024 --week-index 13 \
    --show-snippets \
    > /tmp/baseline_w13_2024.txt 2>&1

python3 scripts/step_1_streak_diagnostic_harness.py \
    --db .local_squadvault.sqlite \
    --league-id 70985 \
    --scope week --season 2025 --week-index 13 \
    --show-snippets \
    > /tmp/baseline_w13_2025.txt 2>&1
```

### Step 3 — Land Commit 2 (prompt instruction + pre-fix memo)

Apply the prompt-instruction change and the pre-fix observation memo.
Fill in the memo with actual baseline numbers from Step 2.

```
cp ~/Downloads/creative_layer_v1.py \
   src/squadvault/ai/creative_layer_v1.py
cp ~/Downloads/OBSERVATIONS_2026_05_04_STREAK_PROMPT_PRE_FIX_DIAGNOSTIC.md \
   _observations/OBSERVATIONS_2026_05_04_STREAK_PROMPT_PRE_FIX_DIAGNOSTIC.md
# Edit the memo to fill in the harness numbers from /tmp/baseline_*.txt

ruff check src/
mypy src/squadvault/core/
pytest -q
# Expect: 1914 passed / 2 skipped, ruff and mypy clean.

git add -A
git diff --cached --stat
# Expect: 2 files (1 modified in src/, 1 new in _observations/)

git commit -F - <<'MSG'
core/ai: add streak-verbatim instruction to creative_layer_v1

Adds the prompt instruction drafted in audit memo §6 to the
NARRATIVE ANGLES block of the weekly-recap prompt assembly,
immediately after the existing narrative_angles content append.

The instruction enumerates the canonical streak phrasings (T1-T6
from streak_strings_v1) and instructs the model to copy them
verbatim, calling out the specific failure modes the four-step
playbook targets: verb paraphrase, direction inversion, and
snapped/extended substitution.

Predecessor commit 6e7d44a (Step 3.1) consolidated the helpers;
this commit makes the prompt name those helpers' templates and
ask for verbatim copy. Step 3.3 (verifier STREAK_VERBATIM) reads
the same canonical strings through the same helpers.

Pre-fix baseline diagnostic captured in
_observations/OBSERVATIONS_2026_05_04_STREAK_PROMPT_PRE_FIX_DIAGNOSTIC.md
using scripts/step_1_streak_diagnostic_harness.py.

No verifier change. No new angles. Step 3.2 mid-wave commit.
MSG
```

### Step 4 — Regen weeks under the NEW prompt

```
set -a; source .env.local; set +a

scripts/py scripts/recap_artifact_regenerate.py \
    --db .local_squadvault.sqlite \
    --league-id 70985 \
    --season 2024 \
    --week-index 13 \
    --reason "Step 3.2 post-fix harness capture: streak instruction in prompt" \
    --force

scripts/py scripts/recap_artifact_regenerate.py \
    --db .local_squadvault.sqlite \
    --league-id 70985 \
    --season 2025 \
    --week-index 13 \
    --reason "Step 3.2 post-fix harness capture: streak instruction in prompt" \
    --force
```

These regens append new prompt_audit rows. The harness in Step 5
will pick up the latest rows for these weeks.

### Step 5 — Run post-fix diagnostic

```
python3 scripts/step_1_streak_diagnostic_harness.py \
    --db .local_squadvault.sqlite \
    --league-id 70985 \
    --scope week --season 2024 --week-index 13 \
    --show-snippets \
    > /tmp/postfix_w13_2024.txt 2>&1

python3 scripts/step_1_streak_diagnostic_harness.py \
    --db .local_squadvault.sqlite \
    --league-id 70985 \
    --scope week --season 2025 --week-index 13 \
    --show-snippets \
    > /tmp/postfix_w13_2025.txt 2>&1

diff /tmp/baseline_w13_2024.txt /tmp/postfix_w13_2024.txt | head -40
diff /tmp/baseline_w13_2025.txt /tmp/postfix_w13_2025.txt | head -40
```

The diffs surface which classifications shifted under the new prompt.

### Step 6 — Land Commit 3 (post-fix memo + policy decision)

Write the post-fix memo with:
- Pre/post compliance numbers (VERBATIM rate per template).
- Specific INVERTED examples that survived the prompt change (if any).
- Policy decision: HARD (verifier rejects on STREAK_VERBATIM
  violation) or SOFT (verifier flags for human review). Per-template
  split allowed.
- Trigger condition for Step 3.3 to begin.

```
cp ~/Downloads/OBSERVATIONS_2026_05_04_STREAK_PROMPT_POST_FIX_OBSERVATION.md \
   _observations/OBSERVATIONS_2026_05_04_STREAK_PROMPT_POST_FIX_OBSERVATION.md

git add -A
git diff --cached --stat
# Expect: 1 file (1 new in _observations/)

git commit -F - <<'MSG'
observations: Step 3.2 post-fix streak prompt observation + policy decision

Captures post-fix harness measurements (W13 2024 + 2025 regens
under the new prompt with the streak-verbatim instruction) and
records the policy decision for Step 3.3:

[INSERT POLICY DECISION HERE: HARD / SOFT / per-template split]

Pre/post-fix VERBATIM rate by template:
[INSERT TABLE HERE]

Step 3.3 (verifier STREAK_VERBATIM) is unblocked.

Doc-only.
MSG
```

---

## In scope

- New tracked harness `scripts/step_1_streak_diagnostic_harness.py`.
- Prompt instruction insertion in `creative_layer_v1.py`.
- Three observation memos in `_observations/`: this brief, the
  pre-fix diagnostic, the post-fix observation.
- Three commits per the one-topic-per-commit discipline.
- Policy decision (HARD vs SOFT) for Step 3.3.

## Out of scope — explicitly deferred

- **`recap_verifier_v1.py`.** No verifier change. Step 3.3.
- **Coverage-gap fixes.** Memo §10 Q1 / Q2.
- **Player-level streak diagnostic.** If post-fix shows player
  streak inversions, that's a separate four-step thread per the
  audit memo.
- **D49 surfacing audit.** Separate diagnostic thread per
  userMemories Writing Room surfacing void.

## Risks / friction

- **Harness classifier false positives on INVERTED.** Hard heuristics
  (substring match on direction phrases within a 200-char window)
  can flag a paraphrase as INVERTED if the prose mentions a
  different team's opposite-direction streak nearby. Mitigation:
  the post-fix memo classifies a sample of INVERTED hits manually
  before locking in policy. `--show-snippets` exists for this audit.
- **DB query gets stale rows.** `last10-approved` joins
  `recap_artifacts` (state filter) with `prompt_audit` (matched on
  league/season/week + temporal proximity). The match isn't FK-tight
  — if an APPROVED artifact's lifecycle generated multiple
  prompt_audit rows, the harness picks the most recent before the
  artifact's `created_at`. Memo should cite the row IDs the
  classification was based on for reproducibility.
- **Regen verifier-retry-loop.** Each `recap_artifact_regenerate.py`
  run can append 1-3 prompt_audit rows depending on internal
  verifier rejects. The harness operates per-row, so retry loops
  show as multiple classification rows. Aggregate per-row gives
  the meaningful signal; per-attempt gives the retry diagnostics.
- **Prompt-text auto-link hazard.** From userMemories: "this chat
  client auto-links bare '_v1.py' substrings to fake URLs." Apply
  via downloaded files, not copy-pasted cp commands, to avoid
  visual confusion.

## Pre-commit gates (per commit)

1. `ruff check src/` — clean.
2. `mypy src/squadvault/core/` — clean (60 source files).
3. `pytest -q` — 1914 passed / 2 skipped (no test changes in any
   of the three commits).
4. Terminal banner paste gate (pre-commit hook).
5. No `xtrace` left enabled.
6. Repo-root allowlist gate (pre-commit hook). Memos go in
   `_observations/`, not repo root.

## Staging gate per commit

```
git diff --cached --stat
```

| Commit | Files staged | Rough size |
|--------|--------------|------------|
| 1 (brief + harness) | 2 (`_observations/session_brief_*.md`, `scripts/step_1_streak_diagnostic_harness.py`) | ~500 + ~330 lines |
| 2 (prompt + pre-fix memo) | 2 (`src/squadvault/ai/creative_layer_v1.py`, `_observations/...PRE_FIX_DIAGNOSTIC.md`) | ~17 line insert + memo |
| 3 (post-fix memo) | 1 (`_observations/...POST_FIX_OBSERVATION.md`) | memo only |

Any other file staged is an accidental scope expansion — abort.

---

## Anti-drift discipline

1. Re-grounding is session step 0. HEAD must be `6e7d44a`.
2. **The audit memo §6 is the prompt-instruction authority.** Any
   change to the instruction text from §6's draft requires a
   re-scope event (a follow-up audit memo, not an inline call).
3. **The harness classifier is observational, not authoritative.**
   Any disputed classification gets resolved by manual prose audit,
   not by tweaking the classifier mid-session.
4. **No verifier change.** `recap_verifier_v1.py` MUST NOT appear
   in any of this session's staged diffs.
5. One topic per commit. Three commits, in order.
6. Policy decision (HARD vs SOFT) is informed by post-fix evidence,
   not assumed. Memo §7 proposes "HARD with SOFT fallback" as a
   starting position, contingent on diagnostic evidence.

## Opening move

```
cd ~/projects/squadvault-ingest-fresh
git fetch origin
git rev-parse --short HEAD   # expect 6e7d44a
git log -1 --oneline
```

Then drop the brief + harness from `~/Downloads/`, smoke-test the
harness, and commit. Run baseline. Then proceed to the prompt
commit.

---

## The point

Step 3.1 consolidated 17 ad-hoc f-strings into 5 helpers. Step 3.2
makes the prompt name those helpers' canonical phrasings and
instructs the model to copy them verbatim — and measures the
compliance shift before/after the instruction lands. The diagnostic
informs Step 3.3's severity policy: if the model already complies
above ~95% under the new prompt, HARD makes sense as the verifier
default; if compliance is patchier, SOFT is the safer floor or a
per-template split applies.

The diagnostic harness is the load-bearing instrument. Every claim
about compliance rate routes through it. Helper-bound canonical
phrases ensure the harness, the prompt, and the (future) verifier
all read from the same source.
