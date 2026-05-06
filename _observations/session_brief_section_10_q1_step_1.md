# Session brief — §10 Q1 Step 1: T9-LOSS form implementation

## Preamble: HEAD verification

Starting commit: `39b4c42`

Expected SHA-256 hashes for files this session reads or modifies:

| Path | SHA-256 |
| :--- | :--- |
| `src/squadvault/core/recaps/render/streak_strings_v1.py` | `69370ebe6596b5f440f83c7df7e861bb1671448e845b0ec36292295a3d16edb5` |
| `src/squadvault/core/recaps/context/narrative_angles_v1.py` | `8a7e4ee9190aa4177502d387bf1cdb7aa00bb1344b43e72e1841639289628409` |
| `src/squadvault/core/recaps/verification/recap_verifier_v1.py` | `31ae8fee60038263efe05f78ef302b374ee9a9b1e625faf1d916b4bbdee8d9cb` |
| `scripts/step_1_streak_diagnostic_harness.py` | `31b1e97d7fc432c79dc5a90f771813e1cfb15eeaa06b6d8d3ff15f04b0a136a8` |
| `_observations/OBSERVATIONS_2026_05_05_T9_LOSS_PRE_FIX_DIAGNOSTIC.md` | `378993df8834f8245bf8e7d4a78bd5a7fda9b36479f623a660d703ff1b6fb0d5` |

Re-grounding gate at session start: print HEAD, run shasum, verify all
five hashes match exactly. Drift on any line aborts the session pending
re-grounding (anti-drift discipline rule 1).

Baseline at session start:
* Test suite: **1939 passed, 2 skipped**
* Ruff (`src/`, `Tests/`): clean
* Mypy (`src/squadvault/core/`): clean, 60 source files

## Scope — what this session does and does not do

**This session implements the T9-LOSS angle form** to close the
RECORD_APPROACH fabrication category surfaced in the §10 Q1
pre-fix diagnostic memo (commit `39b4c42`). The session:

* Extends `format_streak_record` with a T9-LOSS branch.
* Wires `_detect_streak_records` to invoke that branch.
* Extends `_angle_anchor_present` to recognize T9-LOSS phrasing as
  a valid anchor for `RECORD_CLAIM_ANCHORING`.
* Ships under the gate sequence and reverify-as-merge-gate
  validates against the W11/W13 2025 fixture set.

**This session does not:**

* Implement a symmetric T10-LOSS-side-only "tied/broke" form.
  T10-LOSS already exists; the asymmetry being closed is solely
  the missing T9-LOSS approach form. The "asymmetric by design"
  note at `streak_strings_v1.py:30` will be updated to reflect
  that T9-LOSS now exists; the T8/T10 win-record vs loss-record
  asymmetry is **untouched** since neither evidence nor brief
  supports broadening it.
* Add a new verifier rule or category. `verify_record_claim_anchoring`
  with `_angle_anchor_present` already enforces the integrity
  invariant; the diagnostic confirmed (see "Critical pre-flight
  finding" below) that the existing verifier *would* catch the W11
  id=140 fabrication if T9-LOSS prose were treated as an anchor
  AND if id=140 had been verified post-`c435864`. Step 1.3 closes
  the anchor-recognition half; the rest of the integrity surface
  is already in place.
* Modify HEADLINE budget policy. T9-LOSS lands at strength=2
  mirroring T9-WIN. Editorial-weight asymmetry (Path B) is
  rejected per the path-decision discussion at session brief
  drafting time.
* Touch the streak diagnostic harness's `_would_t9_loss_fire`
  predicate. After Step 1 lands, a follow-up commit (Step 1.5)
  retires the predicate by routing the harness through the
  production detector — but that is its own commit, not bundled
  with the production-path changes.

## Critical pre-flight finding

The Step 0b memo's Step 1 sketch (lines 138–164) framed Step 1 as
a four-step playbook including a new verifier rule. **That framing
was based on an assumption that the diagnostic later refuted.**
Live inspection of the verifier surface during Step 0b's drafting
established that:

1. `_RECORD_CLAIM_PATTERN` (recap_verifier_v1.py:2010) already
   matches all 8 W11/W13 RECORD_APPROACH specimens.
2. `verify_record_claim_anchoring` (recap_verifier_v1.py:2190)
   already enforces angle-anchor presence with severity HARD,
   wired into `verify_recap_v1` at line 3797 with
   `narrative_angles_text` supplied from the lifecycle.
3. `_angle_anchor_present` (recap_verifier_v1.py:2152)
   recognizes T8 (win-broke), T9-WIN (one win from), and T10
   (loss-broke) — but **not** T9-LOSS (line 2181 explicitly
   excludes loss direction from the "is 1 X from record" check
   per the absent T9-LOSS form).
4. The W11 id=140 row's `verification_passed=1` despite all
   other failure conditions being satisfied is explained by the
   row predating the `verify_record_claim_anchoring` rule:
   id=140 captured 2026-05-04T10:59 UTC (03:59 PT); rule landed
   in `c435864` at 2026-05-04 05:11 PT (12:11 UTC), 1 hour 12
   minutes after the row's verification.

Step 1's design follows from this finding: extend the helper, wire
the detector, teach `_angle_anchor_present` about the new form,
and let the existing `RECORD_CLAIM_ANCHORING` HARD rule do the
integrity work it was designed for.

## Step 1.1 — Extend `format_streak_record` (streak_strings_v1.py)

### Diff scope

* Loss-side branch at line 226 currently only checks
  `if abs(streak) >= record_length:` for T10 tied/broke.
* Add a T9-LOSS branch *before* T10 (mirroring win-side ordering
  at lines 217–223 where T8 tied/broke is checked before T9-WIN
  one-from).

Wait — re-read the win-side ordering: line 218 is `streak >=
record_length` (T8 tied/broke checked first), line 222 is
`streak == record_length - 1` (T9-WIN one-from checked second).
So the existing convention is **tied/broke first, then one-from**.
Mirror that on the loss side: T10 tied/broke first (existing),
then T9-LOSS one-from.

Final branch shape for the loss side:

```python
# Losing side: T10 (tied/broke) first, then T9-LOSS (one loss from record).
if streak <= -3:
    if abs(streak) >= record_length:
        headline = (
            f"{franchise_name} tied/broke the league loss streak record "
            f"({abs(streak)} games)"
        )
        detail = f"Previous record: {record_length} by {record_holder_name}."
        return (headline, detail)
    if abs(streak) == record_length - 1:
        headline = (
            f"{franchise_name} is 1 loss from the league loss streak record "
            f"({record_length})"
        )
        return (headline, "")

return None
```

### Notes / docstring updates

* Update the docstring's `Returns:` section (lines 192–200) to
  list T9-LOSS alongside T8/T9/T10:

  ```
  * ``streak >= record_length``      → T8 tied/broke (winning)
  * ``streak == record_length - 1``  → T9-WIN one-from-record (winning); detail is ``""``
  * ``abs(streak) >= record_length`` → T10 tied/broke (losing)
  * ``abs(streak) == record_length - 1 AND streak <= -3`` → T9-LOSS one-from-record (losing); detail is ``""``
  ```

* Update the `Notes:` "Asymmetry by design" bullet (lines
  205–209). Replace with a narrower note: the T9-LOSS form was
  added in §10 Q1 Step 1 (commit SHA filled in at commit time);
  the form mirrors T9-WIN's empty-detail convention because no
  supporting context is available for an approach-to-record case
  on either side.

* Update the body comment at line 226 from
  `# Losing side: T10 (tied/broke) only — no T9-loss form (memo §10 Q1).`
  to
  `# Losing side: T10 (tied/broke) and T9-LOSS (one-from) — symmetric with win side post-§10 Q1 Step 1.`

### Gate sequence after Step 1.1

```
ruff check src/ Tests/
mypy src/squadvault/core/
pytest -q 2>&1 | tail -5
```

Expected: ruff clean, mypy clean (60 files), pytest **1939 passed
or +N passed if Tests/ contains a streak_strings_v1 unit-test
file with T9-LOSS coverage**.

If the test count is unchanged, surface the gap explicitly: the
helper test file at `Tests/test_streak_strings_v1*.py` (path to
verify on session machine) should gain at least one positive
T9-LOSS case, mirroring whatever T9-WIN coverage already exists.
Test-add scope is bounded to mirror existing T9-WIN test shapes,
not introduce new test patterns.

### Commit

Single-file commit:

```
core/recaps/render/streak_strings_v1: add T9-LOSS form

Adds the loss-side approach-to-record branch (streak <= -3 AND
abs(streak) == record_length - 1) emitting the canonical
"{name} is 1 loss from the league loss streak record ({N})"
phrasing with empty detail, mirroring T9-WIN.

Closes the asymmetry surfaced as memo §10 Q1: the brief had
documented the T9-LOSS absence as deliberate; pre-fix
diagnostic 39b4c42 established 8 RECORD_APPROACH-shape
fabrication specimens across W11/W13 2025 attributed to BKB.
The four-step playbook calls for canonical-phrasing-as-anchor
to give the verifier a target.

Detector wiring (Step 1.2) and verifier anchor recognition
(Step 1.3) follow as separate commits in this thread.
```

## Step 1.2 — Wire `_detect_streak_records` (narrative_angles_v1.py)

### Diff scope

Lines 579–592 currently handle the loss side:

```python
if streak <= -3 and history.longest_loss_streak:
    record = history.longest_loss_streak.length
    holder = fname(history.longest_loss_streak.franchise_id)
    result = format_streak_record(fname(rec.franchise_id), streak, record, holder)
    if result is not None:
        headline, detail = result
        # T10 (only loss-side form): always strength 3.
        angles.append(NarrativeAngle(
            category="STREAK",
            headline=headline,
            detail=detail,
            strength=3,
            franchise_ids=(rec.franchise_id,),
        ))
```

The `format_streak_record` call already returns either T10 or
(post-Step-1.1) T9-LOSS; the detector needs to emit the right
strength per form. Mirror the win-side strength logic at line 570
(`strength = 3 if streak >= record else 2`):

```python
if streak <= -3 and history.longest_loss_streak:
    record = history.longest_loss_streak.length
    holder = fname(history.longest_loss_streak.franchise_id)
    result = format_streak_record(fname(rec.franchise_id), streak, record, holder)
    if result is not None:
        headline, detail = result
        # T10 (streak <= -record): strength 3. T9-LOSS (streak == -(record-1)): strength 2.
        # Mirrors win-side ordering at line 570.
        strength = 3 if abs(streak) >= record else 2
        angles.append(NarrativeAngle(
            category="STREAK",
            headline=headline,
            detail=detail,
            strength=strength,
            franchise_ids=(rec.franchise_id,),
        ))
```

### Self-critique on path

Path A (strength=2 for T9-LOSS, mirroring T9-WIN) was confirmed at
session brief drafting time. The strength assignment branch is
*structurally* symmetric with the win side; if post-Step-1
evidence shows T9-LOSS angles getting evicted by HEADLINE budget
pressure and re-creating fabrication condition, that's a Bug 1
follow-on thread (HEADLINE budget policy), not a strength-axis
revision. The diversity-trigger condition for Bug 1 follow-on
(memo §10 Q1: ≥2 distinct franchises across ≥2 distinct weeks)
applies symmetrically here.

### Gate sequence after Step 1.2

Same as Step 1.1: ruff, mypy, pytest. Test count change
expected: depends on whether `Tests/test_narrative_angles_v1*.py`
contains existing T9-WIN strength-assignment coverage that
naturally extends to T9-LOSS. Surface count delta in commit body.

### Commit

```
core/recaps/context/narrative_angles_v1: emit T9-LOSS angles

Extends _detect_streak_records' loss-side branch to assign
strength=2 for the T9-LOSS form (abs(streak) == record_length - 1)
and strength=3 for T10 (abs(streak) >= record_length), mirroring
the win-side ordering at line 570.

Pre-Step-1.1 the helper returned None for T9-LOSS shape, so the
loss-side branch only ever emitted T10 angles (always strength=3).
Post-Step-1.1 the helper returns a T9-LOSS tuple for the
approach-shape cases; this commit teaches the detector to
strength-assign correctly.

Verifier anchor recognition (Step 1.3) follows as a separate
commit. Until 1.3 lands, models that produce T9-LOSS-shaped
prose with the new canonical angle present in NARRATIVE ANGLES
will pass via the angle-anchor check; models that produce
record-approach prose without canonical phrasing AND without
T9-LOSS angle will still be caught (the existing T9-WIN/T10
cases). Models that produce T9-LOSS-shaped prose with the new
canonical T9-LOSS angle present BUT phrased differently in
prose will fail RECORD_CLAIM_ANCHORING — Step 1.3 widens
_angle_anchor_present to recognize the new form.
```

The intermediate-state caveat in the commit body matters: between
Step 1.2 and Step 1.3, the codebase is in a self-consistent state
where the new angle is generated but not yet recognized as a
verifier anchor. This is acceptable as a transient because the
pre-Step-1 fabrication shape (record-approach prose with no
T9-LOSS angle) is what gets caught; the new state changes the
model's input (the T9-LOSS angle is now in the angles block) and
correspondingly should change the prose (verbatim or
paraphrase of the canonical form). Mid-thread the verifier
catching legitimate post-Step-1.2 prose is a feature, not a
regression — it forces the retry loop to converge on canonical
phrasing.

If session execution finds this transient state intolerable
(ruff/mypy/pytest gates fail, or a CI job we haven't anticipated
breaks), bundle Step 1.2 and Step 1.3 into a single commit. Note
that this is a *recovery* from a discovered constraint, not the
preferred path. One-topic-per-commit discipline tilts toward
keeping them split.

## Step 1.3 — Extend `_angle_anchor_present` (recap_verifier_v1.py)

### Diff scope

Lines 2173–2186 currently iterate aliases checking T8/T10
tied/broke and (win-only) T9-WIN one-from:

```python
for alias in aliases:
    alias_re = re.escape(alias)
    # T8 / T10
    if re.search(
        rf"\b{alias_re}\s+tied/broke\s+the\s+league\s+{direction_token}\s+streak\s+record",
        narrative_angles_text,
    ):
        return True
    # T9 (winning side only — no T9-LOSS form per memo §10 Q1)
    if not is_loss and re.search(
        rf"\b{alias_re}\s+is\s+1\s+win\s+from\s+the\s+league\s+win\s+streak\s+record",
        narrative_angles_text,
    ):
        return True
return False
```

Replace with:

```python
for alias in aliases:
    alias_re = re.escape(alias)
    # T8 (win) / T10 (loss): tied/broke
    if re.search(
        rf"\b{alias_re}\s+tied/broke\s+the\s+league\s+{direction_token}\s+streak\s+record",
        narrative_angles_text,
    ):
        return True
    # T9-WIN (win) / T9-LOSS (loss): 1 from
    word = "loss" if is_loss else "win"
    if re.search(
        rf"\b{alias_re}\s+is\s+1\s+{word}\s+from\s+the\s+league\s+{word}\s+streak\s+record",
        narrative_angles_text,
    ):
        return True
return False
```

The body comment at line 2181 (currently noting T9-LOSS absence)
gets removed; the new shared form covers both directions
symmetrically post-Step-1.

### Notes

* `direction_token` (line 2172) is already `"loss" if is_loss
  else "win"` — same as the new `word` variable. Consider folding
  to one variable rather than introducing two synonyms. Pick the
  name that reads most naturally in both call sites; my marginal
  preference is keeping `direction_token` and using it twice.
  Either is fine; surface in commit body which name was used.

* The "T9 (winning side only ...)" comment that motivated this
  exclusion is no longer accurate. Replace with a comment that
  records the symmetric structure post-§10 Q1 Step 1.

### Gate sequence after Step 1.3

Same triplet. Test count: existing
`Tests/test_recap_verifier_v1*.py` files likely have T9-WIN anchor
tests that the change extends to T9-LOSS. New tests bounded to
mirror T9-WIN shapes.

### Commit

```
core/recaps/verification: recognize T9-LOSS as RECORD_CLAIM anchor

Extends _angle_anchor_present to recognize the T9-LOSS form
("{name} is 1 loss from the league loss streak record ({N})")
as a valid anchor for record-shaped streak claims, alongside
the existing T8/T9-WIN/T10 forms.

Closes the verifier-side half of the §10 Q1 thread:
- Step 1.1 added the helper form
- Step 1.2 wired the detector to emit T9-LOSS angles
- this commit teaches the verifier to recognize T9-LOSS prose
  as anchored when the angle exists in the prompt

Pre-§10 Q1 the verifier's exclusion at line 2181 was deliberate
because no T9-LOSS angle existed; with the angle now generated,
the exclusion would block legitimate model output from passing
the angle-anchor check.

Reverify-as-merge-gate (Step 1.4) confirms the W11/W13 fixture
set behaves as expected post-this-commit.
```

## Step 1.4 — Reverify-as-merge-gate (no commit; observation only)

### Goal

Empirically confirm that the three-commit production-path change
behaves correctly on the W11/W13 2025 fixture set:

1. **Pre-fix verifier behavior** — re-run `verify_recap_v1` against
   the captured `narrative_draft` and `narrative_angles_text` from
   id=140, 122, 125, 126, 127, 112, 114, 123 (the eight W11/W13
   RECORD_APPROACH specimens). Expected: all eight emit a HARD
   `RECORD_CLAIM_ANCHORING` failure with sub-claim "no angle
   anchor in prompt." This proves the existing verifier *would*
   have caught these had the rule been in place at capture time;
   it does **not** prove Step 1's helper / detector / anchor
   changes work, only that the integrity rule is in place.

2. **Post-fix harness re-run** — re-run the §10 Q1 fabrication-
   shape harness (`scripts/step_1_streak_diagnostic_harness.py`
   `--scope week --season 2025 --week-index 11/13`) after the
   three commits land. Expected:

   * RECORD_APPROACH bucket count: unchanged from pre-fix
     (1 W11, 7 W13). The harness operates on captured
     `narrative_draft` strings; it cannot observe what new
     drafts would look like post-fix. The harness's purpose
     post-Step-1 is regression detection on **future weeks**, not
     post-hoc rewrite of historical evidence.
   * STATUS_CLAIM_OMITTED bucket count: unchanged (5 W11, 0
     W13). Same reason — captured prose is captured.

3. **Post-fix new-week run** — generate a *new* recap for any
   future week where BKB (or another franchise) has a streak at
   `record - 1`. Confirm:

   * The rendered NARRATIVE ANGLES block contains a T9-LOSS
     line for the franchise (proves Steps 1.1 + 1.2 work).
   * The model's draft either uses verbatim canonical phrasing
     OR uses fabrication phrasing that the verifier catches via
     RECORD_CLAIM_ANCHORING (proves Step 1.3's anchor recognition
     plus the existing rule cover the case).

If no current-week candidate franchise exists at session time
(BKB's streak length not at exactly `record - 1` for the next
unprocessed week), Step 1.4 documents the limitation in an
observation memo and marks reverify as deferred to the next
applicable week. **Silence over speculation:** the session does
not synthesize a fixture row to fake the validation; if the data
doesn't support real reverify, the memo records the gap.

### Predicate retirement (Step 1.5; separate commit)

After 1.4 documents the new-week behavior, the harness's
`_would_t9_loss_fire` predicate (added at 0a-time as the
counterfactual gate) becomes redundant. Step 1.5 retires it:

* Replace the predicate call site with a direct invocation of
  `format_streak_record` (or `_detect_streak_records` + filter,
  whichever maps cleanly), removing the predicate function.
* Keep the harness regression-sentinel role intact: the
  RECORD_APPROACH bucket continues to fire on any future week
  where the model produces record-approach prose without a
  canonical anchor (i.e., catches both pre-§10-Q1 historical
  rows and any post-fix regression).

Step 1.5 is a small, single-file scripts/ commit. No production
gate impact.

## Anti-drift discipline reminders

* **Verify HEAD and SHA-256s before any code change.** A drift on
  any of the five preamble hashes aborts the session pending
  re-grounding. The hashes were computed at session brief
  drafting time against `39b4c42` HEAD.
* **Read prose from `prompt_audit.narrative_draft` before
  proposing fixes.** The Step 0b drill chain in this thread's
  prior session demonstrated the cost of skipping this — three
  amend-cycles on the harness alone before bucket counts
  stabilized. Don't repeat.
* **One topic per commit; staging gate with
  `git diff --cached --stat` before every commit.** The Step 1
  thread is structured as four production-path commits (1.1, 1.2,
  1.3, plus Step 1.5 predicate retirement) with one observation
  memo (Step 1.4). No more, no less.
* **Test delta assertion preferred over absolute counts.** Each
  commit's gate check should record the test count delta from
  pre-commit baseline, not just print the absolute number.
* **Diagnostic-first.** If any reverify step in 1.4 surfaces
  unexpected behavior, stop and surface rather than improvise. The
  session-brief sketch is *the plan*, not a contract; deviation
  for diagnostic reasons is correct, deviation for expediency is
  not.
* **`/tmp` artifacts are not durable across sessions** (memory
  note 2026-04-21). Any per-row prose dumps written to `/tmp`
  during 1.4 should be summarized in the observation memo before
  session close, not relied on as future input.

## Files referenced

* `_observations/OBSERVATIONS_2026_05_05_T9_LOSS_PRE_FIX_DIAGNOSTIC.md`
  — the §10 Q1 pre-fix diagnostic memo (commit `39b4c42`).
* `scripts/step_1_streak_diagnostic_harness.py` — the §10 Q1
  fabrication-shape classifier (commit `850478c`).
* `src/squadvault/core/recaps/render/streak_strings_v1.py:30, 200,
  205, 226` — current asymmetric-by-design notes; updated by
  Step 1.1.
* `src/squadvault/core/recaps/context/narrative_angles_v1.py:539,
  570, 579–592` — current T8/T9-WIN/T10 detector and strength
  assignment; extended by Step 1.2.
* `src/squadvault/core/recaps/verification/recap_verifier_v1.py:2010
  (_RECORD_CLAIM_PATTERN), 2152 (_angle_anchor_present), 2190
  (verify_record_claim_anchoring), 2319 (anchor-check call site)`
  — verifier surface; extended by Step 1.3.
* `cdbca96` — original §10 Q1 paired-thread brief (post-review
  revision).
* `39b4c42` — Step 0b pre-fix diagnostic memo (this session's
  parent).
* `c435864`, `63fe2c0`, `1b9b88f`, `e4c2df8`, `a212640` — the
  RECORD_CLAIM_ANCHORING rule and four follow-up refinements that
  established the verifier surface this session relies on.

## Opening move

```
cd ~/projects/squadvault-ingest-fresh
git fetch origin
git rev-parse HEAD
git log --oneline -5

shasum -a 256 \
  src/squadvault/core/recaps/render/streak_strings_v1.py \
  src/squadvault/core/recaps/context/narrative_angles_v1.py \
  src/squadvault/core/recaps/verification/recap_verifier_v1.py \
  scripts/step_1_streak_diagnostic_harness.py \
  _observations/OBSERVATIONS_2026_05_05_T9_LOSS_PRE_FIX_DIAGNOSTIC.md

pytest -q 2>&1 | tail -3
ruff check src/ Tests/
mypy src/squadvault/core/
```

Expected: HEAD `39b4c42`; ancestry includes `850478c`,
`afec7b6`, `cdbca96`, `bddc600`; all five SHA-256 hashes match
the preamble; pytest 1939 / 2; ruff and mypy clean. Drift on any
line aborts pending re-grounding.
