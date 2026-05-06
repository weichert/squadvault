# §10 Q1 Step 1 closure — post-fix reverify and live-path observation

**Date:** 2026-05-06
**Step:** 1.4 (observation only, no production code changes)
**Thread head:** `69db27d` (Step 1.3 verifier widening)
**Brief:** `_observations/session_brief_section_10_q1_step_1.md` (`b75da29`)

## Summary

§10 Q1 Step 1's three production-path commits are landed and
empirically validated. The reverify-as-merge-gate and live-path
probes performed in this session establish:

- Step 1.1, 1.2, 1.3 are correct in code (1945 passing unit tests).
- Step 1.2's detector fires correctly on real W14 2025 inputs
  (Probe 1.4.C.B below).
- Step 1.3's verifier widening is unit-test validated but its
  live-path validation is *gated* on the §10 Q1 Bug 1 follow-on
  thread (HEADLINE budget eviction at strength=2).
- The brief's reverify-as-merge-gate expectation ("≥8 fail→pass
  on W11/W13 RECORD_APPROACH specimens") was a brief modeling
  error: captured `narrative_angles_text` columns are immutable
  artifacts; reverify cannot retroactively validate Step 1's
  helper change on prompts captured before the helper changed.

§10 Q1 thread is **closed for Bug 2** (T9-LOSS form, integrity
tier). **Open for Bug 1** (HEADLINE budget, editorial tier);
this session produces specimen #1 of the brief's diversity
trigger (≥2 franchises × ≥2 weeks) for Bug 1 promotion.

## Production-path commits

| Commit | Surface | What it does |
| :--- | :--- | :--- |
| `0887556` | `format_streak_record` (helper) | Adds T9-LOSS branch inside the existing `if streak <= -3:` gate, mirroring T9-WIN at line 217. Returns canonical tuple `(headline, "")` where headline is `"{name} is 1 loss from the league loss streak record ({R})"`. Path A (helper-internal symmetry) per the brief. |
| `cb128d4` | `_detect_streak_records` (detector) | Replaces hardcoded `strength=3` with conditional `strength = 3 if abs(streak) >= record else 2`, mirroring win-side ordering at line 570. T10 retains strength=3; T9-LOSS emits at strength=2. |
| `69db27d` | `_angle_anchor_present` (verifier) | Folds prior win-only T9 branch into `direction_token`-parametrized symmetric branch. Recognizes T9-LOSS canonical phrasing as valid record-claim anchor. Adjacent doc updates (preamble, docstring) per Option B scope. |

Test-count delta: 1939 → 1945 (+6: two new helper tests, three
verifier tests, one detector strength-assertion pair −1 deletion).

## Probe 1.4.A — Full-corpus reverify

Tag: `69db27d_step_1_complete`

```
Reverify summary: rows=141
  still-pass:  6
  still-fail:  75
  fail→pass:   0
  pass→fail:   60

*** REGRESSION: pass→fail > 0 — do NOT merge. ***
```

The row-level summary tripped the merge-gate. Category-attribution
SQL (Probe 1.4.A.B) per the prior session's documented escape
hatch resolved the regression as fully attributable to known
causes outside Step 1's surface:

| Category | distinct_rows | Step 1 surface? |
| :--- | :---: | :--- |
| SCORE_VERBATIM | 59 | No — backlog "59-row drift" item |
| STREAK | 13 | No — verb-inversion category |
| SERIES | 5 | No |
| RECORD_CLAIM_ANCHORING | 3 | Yes (see below) |
| PLAYER_FRANCHISE | 2 | No |
| FAAB_CLAIM | 1 | No |

The 3 Cat 3c `pass→fail` rows decompose as:

- **Row 76** (W14 2025): row-76 attribution edge case from open
  backlog ("affects attribution label only, not detection"). Not
  Step-1-caused.
- **Row 123** (W13 2025) and **Row 140** (W11 2025): both
  W11/W13 RECORD_APPROACH specimens that originally captured
  `verification_passed=1` because the row predates `c435864`'s
  Cat 3c rule landing (id=140 captured 2026-05-04T10:59 UTC,
  `c435864` landed 2026-05-04 12:11 UTC, 1h12m gap per the
  Step 1 brief preamble). The "pass" was a pre-rule artifact,
  not a Step-1.3 regression.

**Net new failures introduced by Step 1: zero.**

Brief expectation gap: the brief specified `≥8 fail→pass` on
W11/W13 RECORD_APPROACH specimens. Actual: 0. Probe 1.4.A.C
(W11/W13 angle-block inspection) confirmed all 8 specimens
have `narrative_angles_text` columns containing no T9-LOSS
line — these prompts were captured before the helper emitted
T9-LOSS. Step 1.3's widening cannot make captured prose pass
because the captured angle block predates the helper change.
**Reverify-as-merge-gate's value here is non-regression
attestation, not retroactive validation.**

## Probe 1.4.B — Harness re-run

Skipped per the immutability finding above. The Step 0b
harness operates on captured `narrative_draft` strings,
which are also immutable; bucket counts cannot transition.
The harness's purpose post-Step-1 is regression detection on
*future* weeks, which Probe 1.4.C exercises directly.

## Probe 1.4.C — Live-path validation via fresh regen

### C.1 — Slot inspection

W14 2025 selected as target: Brandon Knows Ball (fid=0010) at
streak=-14, longest_loss_streak=15. T9-LOSS condition
`abs(-14) == 15 - 1` exactly satisfied. Self-holder edge case
(Brandon owns his own loss-streak record) — benign for
detection per the helper's contract.

`recap_artifacts` state pre-regen: 29 versions for W14 2025;
APPROVED at v18 (2026-04-09); subsequent DRAFTs captured
2026-04-14 through 2026-04-16 (the captured-prose corpus
referenced in §10 Q1's Step 0b memo). Standard PFL Buddies
workflow: post-approval experimental DRAFTs against later
verifier commits. Adding a v30 DRAFT for post-§10 Q1
observation does not violate governance — append-only
ledger handles experimental drafts after approved versions.

### C.2 — Regen

```
scripts/recap_artifact_regenerate.py \
  --db .local_squadvault.sqlite \
  --league-id 70985 --season 2025 --week-index 14 \
  --reason "step_1_4_C_post_t9_loss_closure_observation" \
  --force
```

Result:

| Field | Value |
| :--- | :--- |
| `version` | 30 |
| `created_new` | true |
| `verification_attempts` | 1 |
| `verification_result.passed` | true |
| `hard_failures` | `[]` |
| `soft_failures` | `[]` |
| `checks_run` | 11 |
| `prev_approved_version` | 18 |
| `selection_fingerprint` | `cb6fe88...` (force-overridden) |
| `prompt_audit` row | id=142 |

Verifier passed on first attempt. But "passed" is necessary,
not sufficient — two paths produce identical JSON:

1. **Desired path:** angle block contains T9-LOSS line; prose
   contains record-shape claim about Brandon; verifier's anchor
   check accepts the angle as proof of grounding.
2. **Pass-by-silence path:** angle block contains T9-LOSS line,
   but prose contains no record-shape claim at all;
   `_RECORD_CLAIM_PATTERN` short-circuits at line 2230 with no
   matches; the anchor check never runs.

C.3 inspects which path occurred.

### C.3 — Angle block and prose inspection (id=142)

**Angle block:** Brandon Knows Ball appears in [HEADLINE]
(opponent attribution for the Paradis blowout) and two
[NOTABLE] entries (FAAB analyses). The canonical T9-LOSS
STREAK line is **absent** from the rendered block. The block
ends with `(+ 112 minor angles omitted)` — meaning many
strength=2 angles were emitted by the detector but evicted
from the surfaced output by the budget policy.

**Narrative draft:** Records Brandon's actual streak length
("his streak to 14 straight") and season record ("now 0-14
... staring at a winless season"). No record-shape phrasings:
no "all-time record", no "league record", no "X games short
of", no "longest losing streak". The model wrote
streak-shape prose without record-shape claims.

**Path 2 (pass-by-silence) is what occurred.** The model had
no T9-LOSS angle in its prompt to draw on, did not fabricate
a record claim, did not surface one at all. Verifier's
`_RECORD_CLAIM_PATTERN` short-circuited; Step 1.3's widening
never executed in the live path.

This is constitutionally fine — silence over speculation is
the project's stated principle. But it leaves Step 1.3's
live-path validation unproven on this specimen.

### C.B — Detector validation via direct invocation

Direct invocation of `_detect_streak_records` on the same W14
2025 inputs the lifecycle saw confirms the detector fires
correctly:

```
_detect_streak_records emitted 1 angle(s):

  [strength=2] [STREAK] Brandon Knows Ball is 1 loss from the league loss streak record (15)
      franchise_ids: ('0010',)
```

**Step 1.1 + Step 1.2 are validated end-to-end on real
inputs.** The angle exists at the data layer. Its absence
from id=142's rendered block is a downstream surfacing-budget
finding, not a detector failure.

## §10 Q1 Bug 1 follow-on — specimen #1

The brief's diversity trigger for Bug 1 promotion: ≥2 distinct
franchises across ≥2 distinct weeks of T9-LOSS angles
generated-but-evicted. id=142 establishes:

- **Specimen #1:** Brandon Knows Ball (fid=0010), W14 2025,
  strength=2 T9-LOSS angle generated by detector, evicted from
  rendered block by HEADLINE/NOTABLE/MINOR budget filter,
  resulting prose contained no record-shape claim, verifier
  passed via short-circuit.

One more specimen (different franchise OR different week)
satisfies the diversity trigger and promotes Bug 1 from
"noted" to "actionable thread." Probe E identified 7 more
T9-LOSS-eligible (week, franchise) candidates in 2025 alone
(W11–W18, all Brandon) — all single-franchise; the diversity
trigger requires *cross-franchise* evidence, which a 2025-only
scan cannot provide. 2024 / 2023 / earlier-season scans needed
for second-specimen evidence.

The Bug 1 thread, when promoted, is editorial-tier (HEADLINE
budget policy), distinct from §10 Q1 Bug 2's integrity-tier
closure. The brief's two-tier framing accommodates this exact
outcome.

## §10 Q1 thread status

- **Bug 2 (T9-LOSS form, integrity tier): CLOSED.** Helper +
  detector + verifier all correct. Helper-bound discipline
  test in `Tests/test_recap_verifier_v1.py:test_angle_anchor_t9_loss_helper_bound`
  guards the canonical-phrasing-to-regex coupling.
- **Bug 1 (HEADLINE budget eviction, editorial tier): OPEN
  with specimen #1.** Diversity trigger (≥2 franchises × ≥2
  weeks) requires one more cross-franchise specimen before
  thread promotion.

## Side-finding: SCORE_VERBATIM 59-row drift confirmed

Probe 1.4.A.B's category breakdown empirically confirmed the
open-backlog SCORE_VERBATIM drift at exactly 59 distinct rows
spanning 2024–2025 W1–W17. Not Step-1-related; not in §10 Q1
scope; logged here so the count is durable for the next
session that picks up the SCORE_VERBATIM thread.

## Methodological notes

Three lessons from this session worth carrying forward:

1. **Reverify-as-merge-gate cannot validate retroactively on
   captured prose.** Captured `narrative_angles_text` columns
   are immutable artifacts; verifier-side changes cannot make
   pre-change prompts pass. The gate's value is non-regression
   attestation against the *current* corpus, not validation of
   forward-looking changes. Validation of forward changes
   requires fresh regens.

2. **Schema introspection before query construction.** Two
   query failures this session attributed to guessing column
   names (`payload_json`, `recap_artifacts.week`) and pattern
   formats (`LIKE '%:0010:%'`). Discipline: any query against
   a table or string-format Claude has not directly inspected
   gets `.schema` or a sample-row inspection first.

3. **Verifier `passed=true` is necessary but not sufficient
   evidence of correctness.** Two distinct paths (canonical
   anchor recognition vs. silence short-circuit) produce
   identical JSON. Probe design needs to distinguish — id=142
   would have been a misleading "Step 1.3 validated" without
   the angle-block inspection.

## Next thread actions

- **Step 1.5** (separate commit): retire
  `scripts/step_1_streak_diagnostic_harness.py`'s
  `_would_t9_loss_fire` predicate by routing the harness
  through the production detector. Per the brief, single-file
  commit in `scripts/`.
- **Bug 1 specimen #2 hunt**: scan 2024 and prior seasons for
  T9-LOSS-eligible (week, franchise) candidates from a
  *different* franchise than Brandon. If found, promote Bug 1
  to actionable thread.
- **SCORE_VERBATIM 59-row backlog item**: independent thread,
  outside §10 Q1 scope.
