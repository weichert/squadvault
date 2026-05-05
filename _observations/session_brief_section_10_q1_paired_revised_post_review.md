# Session Brief — §10 Q1 paired thread (T9-LOSS form gap + HEADLINE budget eviction) — REVISED

**Drafted:** 2026-05-04 (read-only session; this brief is non-code
preparatory material and lands as a single doc commit).

**Revision rationale.** The earlier draft framed Bug 1 (HEADLINE
budget eviction) and Bug 2 (T9-LOSS form gap) as a paired
fabrication-prevention surface where both fixes were necessary
for id=140-class fabrications. That framing implicitly assumed
T9-LOSS at strength=3. Locking Q1 to strength=2 (mirroring T9-WIN
at `narrative_angles_v1.py:570`) decouples the bugs: Bug 2 alone
prevents the record-approach fabrication shape (id=140's
"matching the league's all-time record for futility"). Bug 1 is
real but its mechanism in producing the id=140-class fabrications
is no longer load-bearing post-streak-verb-thread, since the §6
prompt-instruction silence-fallback (`creative_layer_v1.py:281-291`)
gives the model a non-fabrication path when T3 is evicted —
silence rather than invention. The angles block remains the only
canonical-phrasing source in the prompt; STANDINGS continues to
expose only the compact `W{N}`/`L{N}` marker. Bug 1's residual
harm shape is therefore *silent omission* (recaps lose status-
claim density on T3-eviction weeks), not the fabrication shape
the original reframe assumed. Step 3 is therefore
evidence-gated by the Step 0 diagnostic harness — ship if
non-zero status-claim fabrications, defer to follow-on otherwise.

The brief retains the four-step playbook structure but the
"paired" framing is replaced with "Bug 2 is load-bearing; Bug 1
is real but evidence-gated." Five commits possible; four likely.

**Predecessor work:**
- `9729658` — `_observations/OBSERVATIONS_2026_05_04_W11_T3_DIAGNOSTIC_REFRAME.md`
  (the parent reframe; original "paired-bug" framing originates
  here; see Revision rationale above for divergence).
- `e4c2df8` — `RECORD_CLAIM_ANCHORING` (Cat 3c) verifier landed,
  including subject-aware resolver and direction-from-prose. The
  output-side safety net is in place; this thread closes the
  angle-supply-side gap.
- `7d891aa` / `71d6e5f` / `6e7d44a` — Step 3 (streak verb
  pre-computation) closed via the four-step playbook. Critically,
  this thread put canonical streak phrases into STANDINGS, which
  reduces the model's reliance on T3 angles for streak-status
  prose and is the basis for relegating Bug 1 to evidence-gated.
- `OBSERVATIONS_2026_05_04_STREAK_PROMPT_POST_FIX_OBSERVATION.md`
  — origin of memo §10 Q1 promotion (Headline finding 3, T9-LOSS
  fabrication evidence: 5/13 W13 2025 pre-fix → 0/3 post-fix).
- `OBSERVATIONS_2026_05_04_STREAK_VERB_PRE_COMPUTATION_SCOPE.md`
  — original audit memo where §10 Q1 was first surfaced and
  deferred.

**Starting commit:** `bddc600` on `main`. Verify HEAD before any
other action: `git rev-parse HEAD` must print `bddc600...`.

**Working tree:** `/Users/steve/projects/squadvault-ingest-fresh`

**Phase:** 10 — Operational Observation.

**Shape:** Code session, single wave. The verifier extension is
mechanical (Cat 3c is HARD at `e4c2df8`; T9-LOSS is one new
branch). Diagnostic-first discipline applies: pre-fix harness
run before any code change, post-fix harness run in two stages
(post-Step-2 angle-presence, post-Step-3 budget-restoration),
reverify-as-merge-gate before Step 3 and Step 4 verifier
commits.

**Expected session length:** 90–150 minutes. Five to six commits
expected (one diagnostic memo, two data-layer commits, optionally
one budget commit gated on evidence, one verifier-extension
commit). Step 3 may defer to a follow-on session if the Step 0
harness shows zero status-claim fabrications in the corpus.

---

## Preamble check — drift verification

At HEAD `bddc600`, the following SHA-256 hashes pin the files this
session will touch. Re-run before code changes; if any diverge,
the brief is stale and re-grounding is required.

| Path | SHA-256 (HEAD `bddc600`) |
|---|---|
| `src/squadvault/core/recaps/render/streak_strings_v1.py` | `69370ebe6596b5f440f83c7df7e861bb1671448e845b0ec36292295a3d16edb5` |
| `src/squadvault/recaps/weekly_recap_lifecycle.py` | `18e9047699a961f4781cb1d93f4f9620d72d7427a7fa6ef10979f1cd027bbf35` |
| `src/squadvault/core/recaps/context/narrative_angles_v1.py` | `8a7e4ee9190aa4177502d387bf1cdb7aa00bb1344b43e72e1841639289628409` |
| `src/squadvault/core/recaps/verification/recap_verifier_v1.py` | `31ae8fee60038263efe05f78ef302b374ee9a9b1e625faf1d916b4bbdee8d9cb` |
| `docs/addenda/Weekly_Recap_Context_Temporal_Scoping_Addendum_v1_0.md` | `f063d45737cee2796bfaac48a7803aa8361eb14218d27c55c3e0dc9e3df07bb8` |
| `_observations/OBSERVATIONS_2026_05_04_W11_T3_DIAGNOSTIC_REFRAME.md` | `02069e5be75723b3a9fc733419e31657d6ee06182f4e0187d39415fa8df82ce0` |

Reverify via `shasum -a 256 <path>` at session start. Drift on
`recap_verifier_v1.py` or `narrative_angles_v1.py` is most likely
since both are active surfaces.

**Module docstring drift check.** The Step 1 commit edits the
"Asymmetric / by design" wording in `streak_strings_v1.py` lines
30–32 and 199–209 per the brief. The score thread closure
(`ff613a9` / `46c2ca5` / `1db5cbd`) is the most recent surface
that may have shifted these line ranges. Verify at session start:

```bash
grep -in "[Aa]symmetr\|no T9-[lL]oss form\|deliberately absent" \
  src/squadvault/core/recaps/render/streak_strings_v1.py
# Expected hits at HEAD bddc600: lines 30, 86, 200, 205, 226.
# Line 86 is the marker-vs-phrase asymmetry note — preserve unchanged.
```

If the matches don't fall in the cited ranges, update the Step 1
plan accordingly before committing. The hash above will catch any
drift but the grep makes the in-text references concrete.

Test/lint baseline at HEAD `bddc600`: 1939 passed / 2 skipped;
ruff `src/` + `Tests/` clean; mypy `src/squadvault/core/` clean
(60 files). Re-record at session start.

---

## Why this session, and what it fixes

The W11 reframe memo (`9729658`) renamed the original
"T3 detector miss" framing into two distinct bugs. Under the
revised Q1 (T9-LOSS at strength=2), the bugs decouple as follows:

> **Bug 2 (load-bearing) — `_detect_streak_records` has no
> T9-LOSS form.** The helper at `streak_strings_v1.py:226–236`
> deliberately preserves an asymmetry (memo §10 Q1). When a
> franchise is `record_length - 1` games into a losing streak,
> `format_streak_record` returns `None` and no record-anchor
> angle fires. Pre-fix W13 2025 evidence: 5/13 rows fabricated
> approach-to-record phrasings ("one shy of the league record",
> etc.) the helper structurally cannot supply. id=140's "matching
> the league's all-time record for futility" is the W11
> manifestation of the same shape. Closing this gap (Steps 1, 2,
> 5) puts canonical T9-LOSS phrasing into NOTABLE, which the
> model sees in `narrative_angles_text` directly.

> **Bug 1 (real, evidence-gated) — Budget evicts strength-3
> STREAK headlines.** The HEADLINE sort key in
> `weekly_recap_lifecycle.py:760` is `(-strength, category,
> headline)`. STREAK loses every alphabetical tiebreak against
> `FRANCHISE_DEEP`, `PLAYER_NARRATIVE`, `PLAYER_SUPERLATIVE`. T3
> strength-3 STREAK angles can be evicted from the prompt's
> angles block.
>
> The reframe memo claimed this was load-bearing for the id=140
> fabrication. **The reframe memo did not explicitly evaluate
> the §6 silence-fallback's effect on Bug 1's residual harm
> shape**, despite postdating the streak-verb thread closure
> (`9729658` at 14:08 — `e4c2df8` closed at 13:30 the same day,
> `71d6e5f` shipped at 03:39). What the streak-verb thread
> shipped (audited at `creative_layer_v1.py:281-291`) is a §6
> prompt instruction that routes the model through the angles
> block for the **enumerated** streak phrasings — T1/T2 status,
> T3 short-streak, T5/T6 outcome — *and* a silence-fallback
> ("If the angles do not supply a phrasing for what you want
> to say, omit the streak claim"). The silence-fallback's
> grammatical scope is global ("any streak claim") but its
> contextual scope sits inside a directive about status verbs.
> Bug 1's status-claim shape is enumerated; Bug 2's record-
> approach shape is not (and the LEAGUE_HISTORY block at line
> 265 actively encourages mentioning record proximity). The
> brief's confidence in §6 for Bug 1 is therefore *higher* than
> its confidence in §6 for record-approach claims — §6 directly
> addresses Bug 1, only indirectly addresses Bug 2.
>
> So when T3 is evicted from HEADLINE, the canonical phrase
> disappears from `narrative_angles_text` entirely and the §6
> silence-fallback fires: the model omits the status claim
> rather than fabricating one. T3 eviction's residual harm shape
> is therefore *silent omission* (informational-density loss on
> T3-eviction weeks), not the fabrication shape the original
> reframe assumed.
>
> Whether silent omission is sufficiently load-bearing to
> motivate Step 3 is an editorial question, not an integrity
> question — silence over speculation is a constitutional
> principle. Step 0 measures both shapes (`STATUS_CLAIM_EVICTED`
> for residual fabrication, `STATUS_CLAIM_OMITTED` for silent
> loss) and explicitly distinguishes the gating rule for each.

The pattern from prior threads: **give the model verified data
and it cites verified data; withhold data and it invents.**
Bug 2 is the data-layer-supply gap for record-approach claims
and is unambiguously load-bearing. Bug 1 is the data-layer-
emphasis gap for status claims and may have been partially
absorbed by the streak-verb-thread fix.

---

## Scope

### In scope

1. Extend `streak_strings_v1.format_streak_record` to emit a
   T9-LOSS form (`"{name} is 1 loss from the league loss streak
   record ({R})"`) when `abs(streak) == record_length - 1`.
2. Update `_detect_streak_records`
   (`narrative_angles_v1.py:579–592`) to surface the new branch
   as a `STREAK`-category `NarrativeAngle` **with strength=2**
   (Q1 decided; mirrors T9-WIN at line 570).
3. Update tests at `Tests/test_streak_strings_v1.py:213`
   (`test_record_losing_one_from_record_returns_none`) to assert
   the new T9-LOSS phrasing instead of the gap.
4. **(Conditional, gated by Step 0 evidence)** Fix the HEADLINE
   budget eviction at `weekly_recap_lifecycle.py:773–786`. Ship
   if Step 0 shows non-zero `STATUS_CLAIM_EVICTED` (integrity
   gate, ships unconditionally) OR if Steve elects to ship on
   non-zero `STATUS_CLAIM_OMITTED` (editorial gate, density
   restoration). Defer if both are zero. Categorical reservation
   is the proposed mechanism
   (see Step 3 below). If status-claim fabrications are zero,
   defer to follow-on session and document in the Step 0 memo.
5. Extend `_angle_anchor_present`
   (`recap_verifier_v1.py:2155–2187`) to recognize the new
   T9-LOSS canonical phrasing as a valid record-claim anchor,
   so the new angles satisfy `RECORD_CLAIM_ANCHORING` Cat 3c.
6. Pre-fix and post-fix diagnostic harness runs against the
   established fixture set. Post-fix runs in two stages:
   post-Step-2 (angle-presence) and post-Step-3 (budget
   restoration, if Step 3 ships). Reuse
   `scripts/step_1_streak_diagnostic_harness.py` extended for
   T9-LOSS phrasing and fabrication-shape classification.

### Out of scope

- **Snap-outcome detection** (memo §10 Q2). Won-from-losing and
  lost-from-winning quadrants of the outcome matrix are still
  uncovered. Out of scope; no evidence in this corpus motivates
  promotion.
- **Player-streak verb inversions.** Player streak emitters
  (`PLAYER_HOT_STREAK` / `PLAYER_COLD_STREAK`) are a separate
  four-step thread per audit memo §3.2.
- **Other budget-eviction patterns.** This session fixes the
  HEADLINE alphabetical tiebreak only if Step 0 evidence
  warrants. The MINOR pool already uses a rotation hash
  (`weekly_recap_lifecycle.py:806–812`); the NOTABLE pass uses
  the same alphabetical sort but at cap=6 the observable failure
  rate is much lower. Extending rotation to NOTABLE is a
  follow-up if post-fix observation surfaces NOTABLE evictions
  of importance.
- **Architecture changes.** No changes to the budget tier model
  (HEADLINE 3 / NOTABLE 6 / MINOR 4 / total 12), to the strength
  scale, or to the deterministic rotation seed shape.
- **Verifier severity revision.** `RECORD_CLAIM_ANCHORING` stays
  HARD per the existing Cat 3c policy. The verifier extension is
  mechanical (one new pattern in `_angle_anchor_present`).
- **Approved-recap regeneration.** See Operator regen decision
  below — explicitly *out of session* but planned between
  commits 5 and 6 by the operator.

---

## Operator regen decision

**Decision: Yes, regen W11 2025 id=140 between Step 4 (verifier)
and any post-fix observation memo.** The harness measures
angle-block structure and anchor-presence; it does not measure
prose quality. The score thread (`46c2ca5`) and streak-verb
thread (`71d6e5f`) both regenerated approved-recap fixtures
between data-layer commits and the post-fix memo. This thread
follows that precedent.

Operator step (between Step 4 and the optional post-fix memo):

```bash
scripts/py scripts/recap_artifact_regenerate.py \
  --season 2025 --week 11 --row-id 140
```

The optional post-fix observation memo (commit 7 in the
predicted-shape table) cites the regenerated draft as ground
truth alongside the harness output.

---

## Step-by-step decomposition

### Step 0 — Pre-fix diagnostic (TWO commits: 0a harness extension + 0b memo)

Step 0 is two commits, not one. Per the post-`1d800a9` `scripts/`
discipline, the harness extension is a code commit that runs
through the full ruff/mypy/pytest gate. The memo citing its
output lands separately.

#### Step 0a — Harness extension (code commit)

Before any code change to production paths, extend
`scripts/step_1_streak_diagnostic_harness.py` to classify
fabrications by shape:

```python
_T9_LOSS_RECORD_APPROACH = re.compile(
    r"(?:closing in on|short of|shy of|matching|matches)\s+"
    r"(?:the\s+)?(?:league|all-time)?\s*record"
    r"|longest\s+(?:active\s+)?(?:losing|loss)\s+streak",
    re.IGNORECASE,
)

_T3_STATUS_CLAIM = re.compile(
    r"\b(?:on|riding)\s+(?:a|an)?\s*\d+[- ](?:game\s+)?"
    r"(?:losing|loss|win|winning)\s+streak",
    re.IGNORECASE,
)
```

Commit 0a contains the regex constants, the four-bucket
classifier function, and harness wiring — but no fixture-run
output and no memo. Standard gate: ruff `src/ Tests/`, mypy
`src/squadvault/core/`, pytest, staging gate (`git diff --cached
--stat`), banner paste gate, no-xtrace, repo-root allowlist.
The harness is a read-only diagnostic script; it adds zero
pytest cases but must still pass the existing suite.

Suggested commit message:

```
scripts/step_1_streak_diagnostic_harness: add fabrication-shape
classifier for §10 Q1 thread

Extends the streak-domain diagnostic harness with regex
constants and a four-bucket classifier (RECORD_APPROACH,
STATUS_CLAIM_EVICTED, STATUS_CLAIM_OMITTED,
STATUS_CLAIM_NOT_EVICTED, MISS) per the §10 Q1 paired-thread
brief.

No production-path changes; no fixture-run output is bundled
here. Step 0b (separate doc commit) cites this harness's
output against the established W11/W13 2025 fixture set.

Implementation note: STATUS_CLAIM_EVICTED and
STATUS_CLAIM_OMITTED classification requires per-row
counterfactual angle reconstruction (re-running _detect_streaks
against the stored season/week context) because
prompt_audit.angles_summary_json strips franchise_ids and
headline fields per prompt_audit_v1.py:174. The harness
invokes _detect_streaks directly against derived context, not
against the audit summary.
```

#### Step 0b — Pre-fix memo (doc commit)

Run against the fixture set (§ Fixture set below). Classify each
fabrication row as one of:

- **RECORD_APPROACH** — Bug 2 shape (fabrication); pattern matches
  `_T9_LOSS_RECORD_APPROACH` AND no canonical T9-LOSS angle
  exists in `narrative_angles_text` AND the row would have a
  T9-LOSS angle post-fix (counterfactual: re-run
  `_detect_streak_records` against the canonical context with
  the new helper). **Non-zero ⇒ Bug 2 ships unconditionally.**
- **STATUS_CLAIM_EVICTED** — Bug 1 *fabrication* shape; pattern
  matches `_T3_STATUS_CLAIM` AND a strength-3 T3 STREAK angle
  was produced for the franchise but is absent from
  `narrative_angles_text` AND the *count* in the prose disagrees
  with the canonical streak length from STANDINGS. (The
  disagreement clause is what distinguishes fabrication from
  paraphrase.) **Non-zero ⇒ integrity issue; Step 3 ships
  unconditionally.**
- **STATUS_CLAIM_OMITTED** — Bug 1 *silent omission* shape
  (introduced under the corrected mechanism, see Revision
  rationale). For each franchise where STANDINGS shows
  `|streak| ≥ 4` AND a strength-3 T3 STREAK angle was produced
  AND the angle is absent from `narrative_angles_text`: count
  the row as `STATUS_CLAIM_OMITTED` if the prose contains no
  streak status claim for that franchise. **Non-zero ⇒
  editorial decision; Steve elects whether Step 3 ships.**
- **STATUS_CLAIM_NOT_EVICTED** — pattern matches `_T3_STATUS_CLAIM`
  AND the T3 angle is present in `narrative_angles_text`.
  (Distribution context only; not a Bug 1 signal.)
- **MISS** — none of the above applies.

**Bug 1 evidence gate (two-tier).**

- *Integrity tier:* `STATUS_CLAIM_EVICTED > 0` → Step 3 ships
  unconditionally; document specimens in the Step 0 memo.
- *Editorial tier:* `STATUS_CLAIM_EVICTED == 0` AND
  `STATUS_CLAIM_OMITTED > 0` → Step 0 memo records the omission
  count, names affected weeks, and ends with an explicit YES/NO
  decision from Steve on whether to ship Step 3. The decision
  criterion is editorial density, not integrity, and per the
  silence-over-speculation principle defaulting to defer is
  constitutionally consistent.
- *Defer tier:* both zero → Step 3 defers to follow-on; in-scope
  list updated to drop Step 3 and Step 4 narrows to the T9-LOSS
  verifier branch only.

The two-tier gate makes the constitutional split explicit:
integrity violations are non-negotiable; density losses are
editorial.

The Step 0b memo cites the 0a harness output as run against the
fixture set. Naming convention:
`_observations/OBSERVATIONS_<YYYY_MM_DD>_T9_LOSS_PRE_FIX_DIAGNOSTIC.md`
(parallel to
`OBSERVATIONS_2026_05_04_STREAK_PROMPT_PRE_FIX_DIAGNOSTIC.md`).

**Diagnostic-first acknowledgment.** When 0a runs against the
fixture set during 0b drafting, the developer sees the bucket
counts before the memo is written. If counts surprise — say,
`STATUS_CLAIM_EVICTED > 0` against the prior expectation that
§6 had suppressed all fabrication — the memo writes itself
differently than if both Bug 1 buckets are zero. That's the
diagnostic-first principle working correctly: empirical output
shapes the memo, the memo shapes which downstream commits ship.
The memo is the audit-trail artifact for the gate decision; it
is not a prediction.

The post-fix observation memo (optional Step 7, see Predicted
commit count and shape) reserves the suffix
`_POST_FIX_OBSERVATION.md`.

### Step 1 — Helper extension (`format_streak_record`)

Single file: `src/squadvault/core/recaps/render/streak_strings_v1.py`.

Current shape (lines 226–236):

```python
# Losing side: T10 (tied/broke) only — no T9-loss form (memo §10 Q1).
if streak <= -3:
    if abs(streak) >= record_length:
        headline = (
            f"{franchise_name} tied/broke the league loss streak record "
            f"({abs(streak)} games)"
        )
        detail = f"Previous record: {record_length} by {record_holder_name}."
        return (headline, detail)
```

New shape (add the T9-LOSS branch immediately after T10):

```python
    if abs(streak) == record_length - 1:
        headline = (
            f"{franchise_name} is 1 loss from the league loss streak "
            f"record ({record_length})"
        )
        return (headline, "")
```

Symmetry note: T9-WIN at lines 222–224 returns `(headline, "")`
with no detail, deliberately. T9-LOSS mirrors that convention.
The empty detail is the canonical "no supporting context"
signal — `NarrativeAngle.detail` is required and `""` is the
agreed convention.

Module docstring updates (lines 30–32 and 199–209 — verify
ranges via Preamble check grep): replace the "Asymmetric / by
design" and "Asymmetry by design" wording with a note that
asymmetry was closed in this commit, citing the §10 Q1 thread
closure. **Lines 210-214 (the T9 empty-detail convention notes)
are unrelated to §10 Q1 closure and must be preserved
unchanged.** Test file note at line 213 also flips. **Important:
line 86's "asymmetric with the marker form L{N}" reference is
unrelated** — it describes the marker-vs-phrase asymmetry
("losing streak" vs `L{N}`), not the §10 Q1 detector asymmetry.
Step 1 must preserve line 86's wording unchanged. The grep in
Preamble check is what catches mistaken rewrites; do not
blanket-replace.

Unit tests in `Tests/test_streak_strings_v1.py`:
- Replace `test_record_losing_one_from_record_returns_none`
  (line 213) with `test_record_t9_one_loss_from_record` asserting
  the new headline form and empty detail.
- Add edge case: `streak == -2`, `record_length == 3` →
  `format_streak_phrase` floor at 2 means T9-LOSS at -2 is below
  the consumer-side gate of `streak <= -3` in
  `_detect_streak_records`; the helper should still return the
  T9-LOSS string for `abs(streak) == record_length - 1` because
  the helper contract is consumer-agnostic. Document this in the
  test docstring.

One commit. Suggested message:

```
core/recaps: add T9-LOSS approach-to-record form (memo §10 Q1)

format_streak_record now emits "{name} is 1 loss from the
league loss streak record ({R})" when abs(streak) == record - 1,
mirroring the existing T9-WIN form. Closes the asymmetric design
documented at memo §10 Q1.

Pre-fix W13 2025 evidence (OBSERVATIONS_2026_05_04_STREAK_PROMPT_
POST_FIX_OBSERVATION.md Headline finding 3) showed 5/13 rows
fabricating this missing form. The §6 silence-fallback partially
mitigated post-fix; this commit closes the structural gap so the
helper supplies the canonical phrasing the model demands.

Tests: test_record_losing_one_from_record_returns_none replaced
with test_record_t9_one_loss_from_record. Detector wiring lands
in the next commit.
```

### Step 2 — Detector wiring (`_detect_streak_records`)

Single file:
`src/squadvault/core/recaps/context/narrative_angles_v1.py`.

Current shape at lines 579–592 emits T10 only on the losing
side at strength=3. Update to:

```python
if streak <= -3 and history.longest_loss_streak:
    record = history.longest_loss_streak.length
    holder = fname(history.longest_loss_streak.franchise_id)
    result = format_streak_record(fname(rec.franchise_id), streak, record, holder)
    if result is not None:
        headline, detail = result
        # T10 (broke/tied): strength 3. T9-LOSS (record-1): strength 2,
        # mirroring T9-WIN at line 570 (Q1 decision; memo §10 Q1 closure).
        strength = 3 if abs(streak) >= record else 2
        angles.append(NarrativeAngle(
            category="STREAK",
            headline=headline,
            detail=detail,
            strength=strength,
            franchise_ids=(rec.franchise_id,),
        ))
```

Tests: extend `Tests/test_narrative_angles_v1.py` (or wherever
`_detect_streak_records` is exercised) with a fixture matching
the W11 2025 shape — `current_streak = -11`, `longest_loss_streak
= 12` — and assert the resulting angle has strength=2,
category="STREAK", and the canonical T9-LOSS headline.

One commit. Suggested message:

```
core/recaps: wire T9-LOSS angle in _detect_streak_records

_detect_streak_records now emits a STREAK NarrativeAngle for the
losing-side approach-to-record case (strength=2 to mirror T9-WIN).
This pairs with the helper extension in <prior commit>.

W11 2025 fixture: Brandon Knows Ball at -11 with longest_loss_
streak = 12 now produces a strength=2 STREAK angle in addition
to the existing strength=3 T3 status angle. The strength=2 lands
the angle in NOTABLE pass (cap=6), where it consistently reaches
the prompt's angles block independent of HEADLINE budgeting.

Tests: extends streak-record detector coverage to the new branch.
```

### Step 3 — Budget HEADLINE rotation (CONDITIONAL on Step 0 evidence)

Single file: `src/squadvault/recaps/weekly_recap_lifecycle.py`,
lines 760 and 773–786.

**Pre-condition for shipping this step.** Step 0 harness must
report non-zero `STATUS_CLAIM_EVICTED` count across the fixture
set. If zero, this step defers and the brief's commit count
drops to four.

**Pre-commit prompt-text fingerprint check.** Before staging the
budget commit, scan for fixtures and tests that may assert
byte-equal `narrative_angles_text` or `prompt_text`:

```bash
grep -rn "narrative_angles_text\|prompt_text" Tests/ \
  | grep -iE "assert|expect|==.*\".*\"|\.equals?\("
```

Then run a `prompt_audit.prompt_text` diff under reverify tag
`section_10_q1_paired_step3` against a tag from before Step 3,
scoped to weeks where the new reservation actually triggers
(weeks with at least one strength-3 STREAK angle and at least
three other strength-3 angles):

```sql
SELECT season, week, prompt_text
FROM prompt_audit
WHERE reverify_tag = 'section_10_q1_paired_step3_pre'
  AND season = 2025
  AND week IN (<weeks where reservation triggers>);
```

Compare against the post-Step-3 tag. Expected outcome: zero
non-trivial diffs in unrelated weeks; ordering shifts only in
weeks where the new reservation triggers. Any diff in a week
where the reservation does NOT trigger is a bug — the
reservation was meant to be a no-op for those weeks.

The reframe memo names two options:

| Option | Mechanism | Risk |
|---|---|---|
| (a) Categorical reservation | Within strength-3 sort, reserve 1 of 3 HEADLINE slots for STREAK if any STREAK strength-3 angle exists; other categories compete for the remaining 2 | Inverts current "pure deterministic strength sort" framing; reserved slot is unused if no STREAK strength-3 fires; deterministic but biased |
| (b) Sort key change / rotation hash | Apply the MINOR-pass rotation hash (lines 806–812) to HEADLINE pass too; same hash domain (`category:season:week`) | Disturbs deterministic ordering of existing approved-recap fixture hashes; weeks with stable strength-3 sets get reordered |

**Recommendation: option (a).** Justifications:

1. STREAK is a load-bearing category for fabrication prevention
   — the verifier surface (Cat 3, Cat 3c) is the largest
   single-category investment in the codebase. Categorical
   reservation makes the architectural priority explicit.
2. The MINOR rotation hash exists because MINOR is volume-
   diverse (19 detectors, 4 slots). HEADLINE has cap=3 and
   typically 3–5 contestants per week — different problem shape;
   hashing buys little.
3. The fix is one branch in the HEADLINE collection loop
   (around line 778), not a sort key change. Smaller blast
   radius for diff-review.

Proposed implementation sketch (NOT prescriptive — Steve confirms
in-session):

```python
if _all_angles:
    budgeted = []
    h_count = n_count = 0
    minor_pool: list[NarrativeAngle] = []

    # Strength-3 partition with STREAK reservation.
    strength_3_angles = [a for a in _all_angles if a.strength >= 3]
    streak_s3 = [a for a in strength_3_angles if a.category == "STREAK"]
    other_s3 = [a for a in strength_3_angles if a.category != "STREAK"]

    # Reserve 1 of 3 HEADLINE slots for STREAK if any exists.
    if streak_s3:
        budgeted.append(streak_s3[0])  # already sorted by headline alpha
        h_count = 1

    # Remaining strength-3 angles compete for the remaining HEADLINE
    # slots via the existing alphabetical sort. This includes
    # streak_s3[1:] when 2+ STREAK strength-3 angles exist in a week
    # (rare; e.g., simultaneous win-record and loss-record breaks).
    remaining_s3 = sorted(
        streak_s3[1:] + other_s3,
        key=lambda a: (a.category, a.headline),
    )
    for a in remaining_s3:
        if h_count >= 3:
            break
        budgeted.append(a)
        h_count += 1

    # NOTABLE / MINOR passes unchanged.
    for a in _all_angles:
        if a.strength >= 3:
            continue  # already handled above
        if a.strength == 2 and n_count < 6:
            budgeted.append(a)
            n_count += 1
        elif a.strength <= 1:
            minor_pool.append(a)
```

Determinism preserved: `streak_s3[0]` and `other_s3` orderings
both come from the existing sort at line 760. The reservation is
deterministic under fixed inputs.

Edge cases requiring tests:

- 0 STREAK strength-3 angles → reservation slot is unused;
  `h_count == min(3, len(other_s3))` (no slot wasted, same as
  pre-fix when STREAK loses tiebreak).
- 2+ STREAK strength-3 angles → first goes to reserved slot;
  subsequent compete for remaining 2 slots against `other_s3`
  via existing alpha sort. (Two STREAK strength-3 angles in one
  week is rare but possible — e.g., one team breaks the win
  record AND another team breaks the loss record simultaneously.)
- 4+ strength-3 angles total with 1 STREAK → STREAK gets
  reserved slot, top 2 other_s3 fill remaining; equivalent to
  reframe memo's stated goal.

One commit. Suggested message — two variants depending on which
gate fired:

*Integrity-tier variant (`STATUS_CLAIM_EVICTED > 0`):*

```
recaps/lifecycle: reserve 1 HEADLINE slot for STREAK strength-3

Step 0 harness (<commit>) showed N STATUS_CLAIM_EVICTED specimens
— model fabricating wrong streak counts when T3 is evicted from
HEADLINE. Integrity gate fires; this commit closes the
angle-supply gap.

Strength-3 STREAK angles previously lost the alphabetical
tiebreak to FRANCHISE_DEEP / PLAYER_NARRATIVE / PLAYER_
SUPERLATIVE in the HEADLINE budget. This commit adds a
categorical reservation: 1 of 3 HEADLINE slots reserved for
STREAK strength-3 if any exists. Other strength-3 angles
compete for the remaining 2 slots via the existing alphabetical
sort. Determinism preserved.

The MINOR rotation hash (lines 806-812) is left unchanged —
different problem shape (19 detectors, 4 slots).
```

*Editorial-tier variant (`STATUS_CLAIM_EVICTED == 0`,
`STATUS_CLAIM_OMITTED > 0`, ship elected):*

```
recaps/lifecycle: reserve 1 HEADLINE slot for STREAK strength-3

Step 0 harness (<commit>) showed N STATUS_CLAIM_OMITTED specimens
(zero STATUS_CLAIM_EVICTED — §6 silence-fallback is doing its
integrity job). Editorial gate fires under explicit ship-decision
recorded in the Step 0 memo; this commit restores T3 status-claim
density on eviction-affected weeks. The integrity-vs-editorial
distinction is named in the commit because it shapes the
residual-risk surface: density restoration could marginally
raise fabrication risk if §6 phrasing supply doesn't match what
the model wants to say.

Strength-3 STREAK angles previously lost the alphabetical
tiebreak to FRANCHISE_DEEP / PLAYER_NARRATIVE / PLAYER_
SUPERLATIVE in the HEADLINE budget. This commit adds a
categorical reservation: 1 of 3 HEADLINE slots reserved for
STREAK strength-3 if any exists. Other strength-3 angles
compete for the remaining 2 slots via the existing alphabetical
sort. Determinism preserved.

The MINOR rotation hash (lines 806-812) is left unchanged —
different problem shape (19 detectors, 4 slots).
```

### Step 4 — Verifier extension (`_angle_anchor_present`)

Single file:
`src/squadvault/core/recaps/verification/recap_verifier_v1.py`,
lines 2155–2187.

Current shape (line 2181) explicitly skips T9-LOSS:

```python
# T9 (winning side only — no T9-LOSS form per memo §10 Q1)
if not is_loss and re.search(
    rf"\b{alias_re}\s+is\s+1\s+win\s+from\s+the\s+league\s+win\s+streak\s+record",
    narrative_angles_text,
):
    return True
```

New shape: add a parallel T9-LOSS branch immediately after:

```python
# T9-LOSS (added in <commit>): mirrors T9-WIN.
if is_loss and re.search(
    rf"\b{alias_re}\s+is\s+1\s+loss\s+from\s+the\s+league\s+loss\s+streak\s+record",
    narrative_angles_text,
):
    return True
```

Comment update on line 2181: drop the "no T9-LOSS form" gloss.
Module-level comment on lines 1805 and 1833 (helper docstring
references) stays unchanged — they reference Cat 3c at the
category-design level, not the rule body.

Tests: extend `Tests/test_recap_verifier_v1.py` for the new
anchor case. Three test cases:

1. **Positive anchor** — `narrative_angles_text` containing the
   T9-LOSS phrasing rendered by `format_streak_record`, prose
   containing a record-approach claim attributed to the same
   franchise; assert `verify_record_claim_anchoring` returns no
   failures.
2. **Negative anchor** — prose containing a record-approach
   claim with no T9-LOSS angle in `narrative_angles_text`;
   assert Cat 3c HARD failure on the "no angle anchor" branch.
3. **Helper-bound** — feed `format_streak_record(name, -11, 12,
   holder)`'s headline output directly into a fixture's
   `narrative_angles_text`, prose paraphrasing it; assert
   `_angle_anchor_present` returns `True`. This closes the
   helper-bound discipline gate ("every canonical-phrase
   reference in tests and verifier code routes through
   `streak_strings_v1`"). If the helper's output drifts in
   future, this test breaks; new patterns get added under
   pressure rather than forgotten.

One commit. Suggested message:

```
core/recaps/verification: T9-LOSS anchor recognition in Cat 3c

_angle_anchor_present now recognizes the T9-LOSS phrasing
("is 1 loss from the league loss streak record") as a valid
record-claim anchor. Pairs with the helper / detector commits
that started emitting T9-LOSS angles.

Without this commit, post-fix prose containing a model-paraphrased
T9-LOSS claim attached to a (now-present) T9-LOSS angle would
fail RECORD_CLAIM_ANCHORING — false positive on the "no angle
anchor in prompt" branch (line 2322). This commit closes the
verifier-side parity gap.

Tests: positive anchor, negative anchor, and helper-bound test
that feeds streak_strings_v1.format_streak_record output
directly into _angle_anchor_present.
```

---

## Diagnostic harness design

### Pre-fix probe (Step 0)

Extend `scripts/step_1_streak_diagnostic_harness.py` with the
fabrication-shape classifier described in Step 0 above. Run
against the fixture set's `narrative_draft` columns. Output
should distinguish:

- `RECORD_APPROACH` count (Bug 2 evidence)
- `STATUS_CLAIM_EVICTED` count (Bug 1 evidence — gates Step 3)
- `STATUS_CLAIM_NOT_EVICTED` count (paraphrase distribution
  context)
- `MISS` count

Pre-fix expected distribution against the fixture set:
~5 `RECORD_APPROACH` (the W13 2025 pre-fix evidence, plus W11
2025 id=140's "matching the league's all-time record for
futility"). `STATUS_CLAIM_EVICTED` count is expected near zero
post-§6 (the silence-fallback should suppress fabrication).
`STATUS_CLAIM_OMITTED` is the open empirical question — its
non-zero count would be the first time the harness has measured
silent-omission as a Bug 1 signal. The harness output anchors
the two-tier evidence gate (Step 0 above).

### Post-fix probe — staged

Two stages, separate evidence streams.

**Stage A — Post-Step-2 (angle-presence).** After Steps 1 + 2
land. Same harness, same fixtures. Expected:

- `RECORD_APPROACH` count → 0 (or near-zero), because either:
  - The model now sees the canonical T9-LOSS phrasing in the
    angles block (NOTABLE pass at strength=2) and copies it, OR
  - The model continues to paraphrase but the verifier's new
    T9-LOSS anchor branch (Step 4, not yet shipped at this
    stage) resolves the prose to the now-present T9-LOSS angle.
- `STATUS_CLAIM_EVICTED` unchanged from pre-fix (Step 3 not yet
  shipped).

If `RECORD_APPROACH` count is non-zero post-Stage-A, the data-
layer fix is incomplete — investigate before continuing.

Three readings to distinguish before declaring the data-layer
fix incomplete:

1. **NOTABLE saturation** — T9-LOSS angle was produced but
   evicted from NOTABLE pass. Diagnostic: check
   `narrative_angles_text` for the canonical T9-LOSS phrasing's
   absence despite a counterfactual presence. (Maps to Standing
   backlog item 6.)
2. **Paraphrase forced into convergence** — T9-LOSS angle
   reaches `narrative_angles_text` but the model paraphrases
   the canonical form into a non-canonical record-approach
   claim. *Pre-Step-4* (the state at Stage A),
   `_angle_anchor_present` does not yet recognize the T9-LOSS
   pattern, so paraphrase trips Cat 3c HARD on the "no angle
   anchor" branch and the auto-reject loop forces re-rolls
   until the model either copies the canonical phrasing
   verbatim (regex MISS) or falls to facts-only (no record
   claim, regex MISS). Either way `RECORD_APPROACH` → 0 at
   Stage A. *Post-Step-4*, paraphrase anchors cleanly to the
   now-recognized T9-LOSS pattern; same observable count,
   different mechanism. Diagnostic: T9-LOSS angle present in
   `narrative_angles_text` AND prose matches
   `_T9_LOSS_RECORD_APPROACH` regex but does NOT contain the
   canonical helper output. This is a verifier-side outcome,
   not a data-layer incompleteness.
3. **Genuine data-layer incompleteness** — neither saturation
   nor paraphrase explains the residual count. Stop and
   re-scope.

Reading 2 is the most likely under the §6 instruction's existing
pressure on canonical phrasing; declaring incompleteness without
distinguishing it would mis-route the next session.

**Stage B — Post-Step-3 (budget restoration).** After Step 3
ships (if it does). Same harness, same fixtures. Expected:

- `RECORD_APPROACH` count unchanged from Stage A (already at
  zero or near-zero).
- `STATUS_CLAIM_EVICTED` count → 0 (or near-zero), because T3
  strength-3 STREAK angles now reach the prompt's angles block
  via the categorical reservation. (If integrity-tier gated.)
- `STATUS_CLAIM_OMITTED` count → 0 (or near-zero), because the
  canonical phrasing reaches `narrative_angles_text` and the
  model cites it rather than triggering the §6 silence-fallback.
  (If editorial-tier gated.)

This staging is important: it tests the two bugs as independent
fabrication-prevention surfaces rather than conflating their
effects. Under the strength=2 decision, Bug 2 alone closes
record-approach fabrications. Bug 1 closes status-claim
fabrications, separately.

### Reverify-as-merge-gate

Per memory note: row-level pass→fail in
`reverify_prompt_audit.py` conflates pre-existing legacy drift
with current rule changes. Use the category-breakdown SQL
technique:

```sql
SELECT
  json_extract(failure.value, '$.category') AS category,
  COUNT(*) AS cnt
FROM prompt_audit_reverify, json_each(result_json, '$.hard_failures') AS failure
WHERE reverify_tag = 'section_10_q1_paired_<step>'
GROUP BY 1 ORDER BY 2 DESC;
```

Run the reverify tool with tag `section_10_q1_paired_step1`
before the helper commit, `section_10_q1_paired_step3` before the
budget commit (if shipping), and `section_10_q1_paired_step4`
before the verifier commit. **Zero new hits in
`RECORD_CLAIM_ANCHORING` at each merge gate proves
non-regression** even when the row-level summary shows
pre-existing pass→fail drift in unrelated categories.

The Step 4 verifier commit will *intentionally* shift
`RECORD_CLAIM_ANCHORING` distribution: rows previously failing
the "no angle anchor" branch on a T9-LOSS prose claim should now
pass. Predict the count of converted-to-pass rows from the
post-fix probe (Stage A) and assert at the merge gate.

---

## Predicted commit count and shape

Five to six commits in this session, depending on Step 3
evidence gate:

| # | Type | File(s) | Tests added | Risk | Conditional? |
|---|---|---|---|---|---|
| 1 | Code (harness) | `scripts/step_1_streak_diagnostic_harness.py` | 0 (read-only diagnostic; no production-test impact) | Low | No |
| 2 | Doc | `_observations/OBSERVATIONS_<date>_T9_LOSS_PRE_FIX_DIAGNOSTIC.md` | none | Low | No |
| 3 | Code (helper) | `streak_strings_v1.py` + `test_streak_strings_v1.py` | 2 (new T9-LOSS, edge case) | Low | No |
| 4 | Code (detector) | `narrative_angles_v1.py` + tests | 1 | Low | No |
| 5 | Code (budget) | `weekly_recap_lifecycle.py` + lifecycle tests | 3 (reservation cases) | Medium-High | **Yes — gated on Step 0** |
| 6 | Code (verifier) | `recap_verifier_v1.py` + `test_recap_verifier_v1.py` | 3 (positive, negative, helper-bound) | Low | No |

Commit 1 (harness extension) is a code commit under the post-
`1d800a9` `scripts/` discipline — not a doc commit. It runs
through the full ruff/mypy/pytest gate, staging gate, banner
paste gate, no-xtrace, and repo-root allowlist. Commit 2 is the
doc-only memo citing commit 1's harness output against the
fixture set. **Memo lands before any code that fixes anything**
— that's the diagnostic-first principle.

Plus optional commit 7 (post-fix observation memo) if the
diagnostic harness re-run produces material findings worth
recording. Likely doc-only at the end of the session or rolled
into the next session.

**Test count math.** Baseline 1939; new tests = 0 harness + +1
net helper (replace 1 + add 1 edge case) + 1 detector + (3 if
Step 3 ships, else 0) + 3 verifier = 8 (if all five code commits
ship) or 5 (if Step 3 defers). Final expected: 1947 passed
(full session) or 1944 passed (Step 3 deferred). The harness
extension is a read-only diagnostic script and adds zero
pytest cases.

If the budget-eviction commit (Step 3) reveals interactions with
the rotation hash or unexpected fixture sensitivities, that
commit may become a sub-thread spanning a separate session. The
brief should NOT bundle it with the verifier commit on those
grounds.

---

## Known gotchas

### LEAGUE_HISTORY temporal scoping

Per `docs/addenda/Weekly_Recap_Context_Temporal_Scoping_Addendum_v1_0.md`,
any code that reads `derive_league_history_v1` must pass
`as_of_season` and `as_of_week`. Verified at HEAD `bddc600`:

- `weekly_recap_lifecycle.py:674–698` calls
  `derive_league_history_v1(as_of_season=season, as_of_week=week_index)`.
- `recap_verifier_v1.py:2241–2245`
  (`verify_record_claim_anchoring`) calls
  `derive_league_history_v1(as_of_season=season, as_of_week=week)`.
- `_detect_streak_records` does NOT call
  `derive_league_history_v1` directly; it consumes a passed-in
  `LeagueHistoryContextV1` already temporally scoped by the caller.

The Step 1–4 commits do not introduce any new
`derive_league_history_v1` call sites. The addendum is binding
but not gating for this thread.

### Strength=2 decision rationale (Q1 closure)

Q1 is decided in this brief: T9-LOSS at strength=2. Rationale:

1. **Symmetry with T9-WIN.** Line 570 of `narrative_angles_v1.py`
   sets T9-WIN at strength=2. T9-LOSS mirrors that explicitly.
2. **Bug decoupling at the data layer.** At strength=2, T9-LOSS
   lands in NOTABLE pass (cap=6) and consistently reaches
   `narrative_angles_text` independent of HEADLINE budgeting.
   The record-approach fabrication shape (Bug 2) is closed by
   the data-layer angle supply alone.
3. **Bug 1's load-bearing-ness depends on which mechanism you
   read.** The streak-verb thread did *not* put canonical
   streak phrases into STANDINGS — verified at
   `streak_strings_v1.py:259` (`format_streak_marker` returns
   `W{N}`/`L{N}` only) and at `creative_layer_v1.py:281-291`
   (the §6 instruction routes the model through the angles
   block, not STANDINGS). What the streak-verb thread installed
   is a §6 silence-fallback — but only for the explicitly
   enumerated phrasings (T1/T2/T3 status, T5/T6 outcome). The
   silence-fallback's effectiveness is therefore asymmetric:
   high confidence for Bug 1's status-claim eviction shape (which
   §6 enumerates), lower-but-still-plausible confidence for any
   record-approach reasoning (which §6 does not enumerate, and
   which the LEAGUE_HISTORY block at line 265 actively encourages
   via "when ... a team's record is notable, mention it"). So
   under the corrected mechanism:
   - Bug 1's *fabrication* surface (`STATUS_CLAIM_EVICTED`) is
     structurally suppressed by §6 — expected near-zero.
   - Bug 1's *silent-omission* surface (`STATUS_CLAIM_OMITTED`)
     is the new, untested signal — open empirical question.

   The reframe memo's "doubles down on the budget pressure"
   framing was correct in identifying two bugs but did not
   explicitly evaluate the §6 silence-fallback against the
   T3-eviction shape. This brief revises it: assuming §6
   silence-fallback is effective for status claims (firm — §6
   enumerates them), Bug 1's residual harm becomes silent
   omission, gated by `STATUS_CLAIM_OMITTED` as an editorial-
   density question. The brief's two-tier gate makes the
   assumption falsifiable: non-zero `STATUS_CLAIM_EVICTED` would
   invalidate the §6-effectiveness premise and re-couple the
   bugs as the reframe memo originally argued, ship Step 3
   unconditionally.

If Step 0 evidence shows zero `STATUS_CLAIM_EVICTED`
fabrications, the strength=2 decision plus Step 3 deferral
becomes the load-bearing change. If non-zero, both bugs ship
this session under the decoupled framing.

### NOTABLE saturation dependency

The strength=2 decision (Q1 above) makes Bug 2 self-sufficient
under the assumption that T9-LOSS angles reach
`narrative_angles_text` via the NOTABLE pass (cap=6) without
being evicted. If NOTABLE saturates in the post-fix corpus, the
eviction surface shifts from HEADLINE to NOTABLE rather than
disappearing — Bug 2 is not actually closed by strength=2.

Standing backlog item 6 (NOTABLE-pass alphabetical lockout
investigation) is the named-only placeholder for this risk; no
evidence motivates promoting it yet. The Stage A probe is the
in-thread safety net: a non-zero `RECORD_APPROACH` count
post-Steps-1+2 should be read as NOTABLE-saturation evidence
first (triggering re-scoping before Step 3) rather than as
data-layer-fix incompleteness.

The assumption is monitored, not eliminated. Naming it here
ensures the Stage A reading rule is in the brief, not just
inferable from the standing backlog.

### Budget HEADLINE rotation interactions with approved-recap hashes

The `weekly_recap_lifecycle.py:760` sort is part of the
deterministic angle-budgeting pipeline. Some downstream
fingerprints / hashes may be sensitive to exact angle ordering
inside the prompt's angles block. The Step 3 pre-commit
prompt-text fingerprint check (Step 3 above) is the concrete
mechanism for catching this risk.

If any reverify-tagged hash or fixture test asserts byte-equal
`narrative_angles_text` against pre-fix expected values for
weeks where the new reservation triggers, those fixtures need
updating in the same commit. The grep + reverify diff in Step 3
scopes this risk.

### Verifier subject-aware resolver (post-`e4c2df8`)

The Cat 3c verifier uses subject-aware franchise resolution and
direction-from-prose disambiguation. The T9-LOSS extension in
Step 4 just adds a new pattern in the anchor-presence check
(`_angle_anchor_present`); it does not touch the resolver path.
The row-76 W14 2025 known edge case may still produce
attribution noise on the new T9-LOSS pattern in the same way it
does on existing patterns. Defer; the edge case is already named
on the open-issues list.

### One-topic-per-commit and stage gates

Each of five to six commits gated by:

```
git diff --cached --stat
ruff check src/ Tests/   # zero errors
mypy src/squadvault/core/   # no new errors
pytest                    # baseline + new tests
```

Plus the terminal banner paste gate, no-xtrace, repo-root
allowlist gate. Standard discipline.

---

## Fixture set

Two layers of fixtures.

### Diagnostic-harness fixtures (read-only)

- **W11 2025 id=140** (post-fix Step 3 row, `2026-05-04`).
  Anchor-less T9-LOSS fabrication: *"matching the league's
  all-time record for futility"*. Brandon Knows Ball at -11
  streak; canonical `longest_loss_streak.length = 12`. The W11
  reframe memo's primary specimen. Classified as
  `RECORD_APPROACH`.
- **W13 2025 ids 122–127** (pre-fix Step 3 rows). Five fabricated
  T9-LOSS approach-to-record phrasings:
  - id=122: *"closing in on the all-time league record of 15 games"*
  - id=123: *"still three short of the all-time record of 15 games set across 2024-2025"*
  - id=125: *"longest active losing streak across the last 16 seasons of data"*
  - id=126: *"one shy of the league record he set last season"*
  - id=127: *"one short of the league record he set last season"*
  All classified as `RECORD_APPROACH`. Origin documented in
  `OBSERVATIONS_2026_05_04_STREAK_PROMPT_POST_FIX_OBSERVATION.md`
  Headline finding 3.
- **W13 2025 ids 130–132** (post-§6 rows, pre-this-thread).
  Headline finding 3 showed 0/3 T9-LOSS fabrications post-§6.
  Used as the negative-baseline check — the diagnostic harness
  should report `MISS` on these rows to confirm the §6 silence-
  fallback's continuing effect is preserved by the data-layer
  fix.

### Unit-test fixtures (in `Tests/`)

- `test_streak_strings_v1.py` extension: T9-LOSS at
  `streak == -11`, `record_length == 12` →
  `("Brandon Knows Ball is 1 loss from the league loss streak
  record (12)", "")`.
- `test_narrative_angles_v1.py` extension: synthetic
  `SeasonContextV1` with a single -11 standings record and a
  `LeagueHistoryContextV1.longest_loss_streak.length = 12` →
  `_detect_streak_records` returns one strength=2 STREAK angle
  with the new headline.
- `test_weekly_recap_lifecycle.py` (or wherever budget logic is
  exercised — Steve confirms): synthetic angle list with 4
  strength-3 angles including 1 STREAK; assert all 3 HEADLINE
  slots include the STREAK angle and 2 of 3 of `other_s3`.
  (Only if Step 3 ships.)
- `test_recap_verifier_v1.py` extension: positive anchor,
  negative anchor, and helper-bound test (third feeds
  `format_streak_record` output directly into
  `_angle_anchor_present`).

---

## Pre-commit gates (per commit)

1. `ruff check src/ Tests/` — zero errors.
2. `mypy src/squadvault/core/` — no new errors. Record baseline
   at session start; assert against baseline.
3. `pytest` — full suite passing. Final count = baseline +
   new tests.
4. Terminal banner paste gate (pre-commit hook).
5. No `xtrace` left enabled.
6. Repo-root allowlist gate (pre-commit hook).
7. Reverify-as-merge-gate before commits 5 and 6 (per the
   harness section above).
8. **Step 3 only:** prompt-text fingerprint check (grep +
   reverify diff per Step 3 above).

Staging gate before each commit: `git diff --cached --stat`.
One file or one tightly-coupled cluster per commit.

---

## What this session does NOT do

- Does not introduce snap-outcome detection (memo §10 Q2).
- Does not fix NOTABLE-pass alphabetical lockout (deferred until
  observation evidence).
- Does not regenerate any approved artifacts *as part of session
  commits*. Operator regen of W11 2025 id=140 between Step 4 and
  the optional post-fix memo is the explicit decision (see
  Operator regen decision above) and runs outside the commit
  boundary.
- Does not modify `RECORD_CLAIM_ANCHORING` severity policy
  (stays HARD per `e4c2df8`).
- Does not touch the rotation hash in the MINOR pass.
- Does not address player-streak verb inversions.
- Does not extend the LEAGUE_HISTORY block format. The Weekly
  Recap Context Temporal Scoping Addendum is binding but not
  edited.
- Does not address the row-76 W14 2025 attribution edge case.
- Does not validate against W14+ weeks. Post-fix observation
  spans only the established fixture corpus.
- Does not ship Step 3 (budget reservation) if Step 0 evidence
  shows zero status-claim fabrications.

---

## Rollback

Each commit is independent. If commit 5 (budget) surfaces a
problem post-ship, reset commit 5 only and ship 1–4 + 6 as a
narrower thread. Helper extension + verifier extension + detector
wiring stand on their own — they close the form gap; the budget
fix closes the eviction gap. Either alone is partial progress on
id=140-class fabrications.

If commit 6 (verifier) surfaces a Cat 3c regression, reset commit
6 only. The data-layer fixes are still useful — the verifier
just falls back to its current behavior, which (without the
T9-LOSS anchor branch) would false-positive on T9-LOSS prose.
The reverify-as-merge-gate before commit 6 should catch this
class of issue.

---

## Open questions

### Q1 — T9-LOSS strength: 2 or 3?

**DECIDED: strength=2.** Mirrors T9-WIN at line 570 of
`narrative_angles_v1.py`. Decouples Bug 1 and Bug 2; Step 3
becomes evidence-gated by Step 0 harness output. Reframe memo's
"doubles down on the budget pressure" framing implicitly
assumed strength=3 and is superseded for this thread; see Known
gotchas → Strength=2 decision rationale.

### Q2 — Does T9-LOSS justify a §6 prompt rule update?

The streak-verb thread's §6 instruction
(`creative_layer_v1.py:269–280`) tells the model what to do if a
streak phrasing is missing from the angles block. That
instruction stays unchanged.

Open question: does the model need an *additional* prompt
instruction along the lines of *"approach-to-record claims must
match a T8/T9/T10 angle in the angles block; do not infer record
proximity from STANDINGS + LEAGUE_HISTORY blocks"*? Pre-fix
evidence (5/13 W13 2025) suggests the data-layer fix may be
sufficient. **Default: no new prompt rule.** Revisit only if
post-fix observation shows lingering anchor-less fabrication
specifically on record-approach claims (distinct from the
already-resolved tied/broke claims).

### Q3 — Diagnostic harness extension placement

`scripts/step_1_streak_diagnostic_harness.py` currently lives
at the top level of `scripts/`. Decision: extend that harness
in-place (one file, one diagnostic module) vs. create
`scripts/step_3_t9_loss_diagnostic_harness.py` (separate file).

**Default:** extend in-place. The streak harness is
streak-domain — adding T9-LOSS classifier is in-scope.

### Q4 — Test count baseline confirmation

The brief asserts 1939 passed / 2 skipped at HEAD `bddc600` per
memory note. Reconfirm at session start:

```
pytest -q 2>&1 | tail -3
```

If the actual baseline differs, the brief's expected-final-count
math (1947 / 1944 depending on Step 3) shifts but the structure
is unaffected.

---

## Standing backlog (carries forward)

1. **(THIS SESSION when run)** §10 Q1 paired thread (T9-LOSS
   form gap; HEADLINE budget eviction gated by evidence).
2. SCORE_VERBATIM 59-row legacy drift (open horizon thread).
3. Cat 3c row-76 W14 2025 attribution edge case (open horizon
   thread, deferred — does not affect detection, only label).
4. Snap-outcome detection (memo §10 Q2, named-only).
5. Player-streak verb inversion thread (audit memo §3.2,
   named-only).
6. NOTABLE-pass alphabetical lockout investigation (named-only,
   no evidence yet).
7. Tests/ ruff cleanup (legacy 238 errors — partly cleared in
   recent commits; remaining count to be re-tallied).
8. `d['raw_mfl']` write at `extract_recap_facts_v1.py:190`
   (deferred).
9. **(Possible new entry post-Step-0)** HEADLINE budget
   eviction follow-on session, if Step 3 defers.
10. Parametrized helper-bound verifier test (named-only,
    no urgency). The Step 4 helper-bound test as drafted asserts
    T9-LOSS specifically because that's the new branch this
    thread adds. A pytest-parametrized loop over all four
    canonical `format_streak_record` outputs (T8, T9-WIN,
    T9-LOSS, T10) would catch helper-side drift on any of them,
    not just T9-LOSS. Expanding now would broaden the verifier-
    test diff in commit 5 beyond §10 Q1 closure; the value is
    cheap if helper drift ever bites and this entry preserves
    the prior reasoning.

---

## Anti-drift discipline

1. Re-grounding is session step 0. Verify HEAD = `bddc600`,
   reverify SHA-256 hashes per § Preamble check, run docstring
   drift grep, record actual test/lint baseline before any code
   change.
2. Diagnostic-first applies. Step 0a (harness extension) and
   Step 0b (pre-fix memo citing 0a output) land as the first
   two commits. Step 1 only after Step 0b — memo lands before
   any code that fixes anything. Step 3 only after Step 0b
   evidence shows `STATUS_CLAIM_EVICTED > 0` (integrity-tier,
   unconditional ship) OR `STATUS_CLAIM_OMITTED > 0` with
   explicit ship-decision (editorial-tier).
3. The reverify-as-merge-gate technique replaces row-level
   pass→fail counts as the merge criterion. Step 3 adds a
   prompt-text fingerprint check on top.
4. One topic per commit. Five to six commits.
5. Memory may be stale; the artifact trail is authoritative. If
   any SHA-256 in § Preamble check has drifted, stop and
   re-ground.
6. Q1 is decided in this brief (strength=2). Re-decide only if
   Step 0 evidence forces it.
7. The reframe memo (`9729658`) is the parent. This brief
   diverges from its "paired" framing under the strength=2
   decision; the divergence is recorded in the Revision
   rationale and Known gotchas → Strength=2 decision rationale
   sections, and should be cited in the Step 0 memo.
8. Helper-bound: every canonical-phrase reference in tests and
   verifier code routes through `streak_strings_v1`. The Step 4
   helper-bound test enforces this for the verifier surface.

---

## Opening move

```
cd ~/projects/squadvault-ingest-fresh
git fetch origin
git rev-parse HEAD                       # expect bddc600
shasum -a 256 \
  src/squadvault/core/recaps/render/streak_strings_v1.py \
  src/squadvault/recaps/weekly_recap_lifecycle.py \
  src/squadvault/core/recaps/context/narrative_angles_v1.py \
  src/squadvault/core/recaps/verification/recap_verifier_v1.py \
  docs/addenda/Weekly_Recap_Context_Temporal_Scoping_Addendum_v1_0.md \
  _observations/OBSERVATIONS_2026_05_04_W11_T3_DIAGNOSTIC_REFRAME.md
grep -in "[Aa]symmetr\|no T9-[lL]oss form\|deliberately absent" \
  src/squadvault/core/recaps/render/streak_strings_v1.py
pytest -q 2>&1 | tail -3                 # record baseline
ruff check src/ Tests/                   # confirm zero
mypy src/squadvault/core/                # confirm clean (60 files)
```

Then Step 0a — extend the diagnostic harness with the
fabrication-shape classifier, gate (ruff/mypy/pytest/staging),
commit code-only. Then Step 0b — run the harness against the
fixture set, write the pre-fix memo citing the bucket counts,
commit doc-only. **Read 0b output before proceeding to Step 3
scope:** apply the two-tier gate (`STATUS_CLAIM_EVICTED > 0`
ships unconditionally; `STATUS_CLAIM_OMITTED > 0` requires
explicit ship-decision; both zero defers Step 3). Then Step 1
(helper) → Step 2 (detector) → harness Stage A → optional
Step 3 (budget, gated) → Step 4 (verifier — pause for reverify
gate). Operator regen of W11 2025 id=140 between Step 4 and any
post-fix memo. Optional post-fix observation memo (commit 7 if
all five code commits ship, commit 6 if Step 3 defers) if
evidence warrants.

---

## The point

Under Q1 = strength=2, the four-step playbook closes one
load-bearing structural bug (Bug 2: T9-LOSS form gap) plus a
two-tier-gated paired bug (Bug 1: HEADLINE budget eviction).
Step 1 is the helper extension. Step 2 is the detector wiring
at strength=2. Step 3 is the budget reservation, shipped under
integrity-tier evidence (`STATUS_CLAIM_EVICTED > 0`,
unconditional ship) or under editorial-tier evidence
(`STATUS_CLAIM_OMITTED > 0`, ship-by-election). Step 4 is the
verifier extension.

The reframe was load-bearing in identifying two bugs. The
revision is load-bearing in correctly characterizing each bug's
residual harm shape under the post-streak-verb-thread state.
Bug 2's residual harm is fabrication and is unambiguously the
id=140 preventer. Bug 1's residual harm under §6 is silent
omission, not fabrication — a constitutional difference. The
Step 0 harness measures both shapes and the gating rule is
two-tier: integrity ships, editorial elects, defer if neither.

Diagnostic first. Helper second. Detector third. Budget fourth
(if evidence). Verifier fifth. Reverify-as-merge-gate before
commits 5 and 6; prompt-text fingerprint check additionally
before commit 5. One topic per commit.
