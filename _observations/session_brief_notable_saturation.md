# Session Brief — NOTABLE-pass alphabetical lockout investigation

**Drafted:** 2026-05-06 (read-only session; this brief is non-code
preparatory material and lands as a single doc commit).

**Thread context.** This brief scopes the work for **standing
backlog item 6** (NOTABLE-pass alphabetical lockout
investigation), promoted to actionable per
`OBSERVATIONS_2026_05_06_BUG_1_LABELING_CORRECTION.md` (`1e2c0f5`).

**This brief is NOT for original Bug 1.** Original Bug 1 (T3
strength-3 HEADLINE eviction via alphabetical tiebreak) remains
deferred per the Step 0b memo's gate verdict
(`OBSERVATIONS_2026_05_05_T9_LOSS_PRE_FIX_DIAGNOSTIC.md`,
`39b4c42`): `STATUS_CLAIM_EVICTED = 0; STATUS_CLAIM_OMITTED = 5
BKB-only`. The diversity trigger (≥2 franchises × ≥2 weeks of
STATUS_CLAIM_OMITTED) is unchanged. If/when the original Bug 1
trigger fires, that thread activates with the
already-designed categorical-reservation fix.

The two threads share a mechanism family (alphabetical-tiebreak
eviction of STREAK angles) but operate at different tiers and
would have different fixes. They can coexist; the
NOTABLE-saturation thread does not block, supersede, or
absorb original Bug 1.

**Predecessor work:**
- `1e2c0f5` —
  `_observations/OBSERVATIONS_2026_05_06_BUG_1_LABELING_CORRECTION.md`
  (this thread's promotion authority; identifies the
  mechanism precisely)
- `22770d9` —
  `_observations/OBSERVATIONS_2026_05_06_BUG_1_SPECIMEN_2_HUNT_AND_OCCURRED_AT_GAP.md`
  (cross-franchise structural-recurrence evidence: 19
  candidates × 7 franchises × 16 seasons)
- `a5c5c1b` —
  `_observations/OBSERVATIONS_2026_05_06_T9_LOSS_POST_FIX_REVERIFY.md`
  (id=142 specimen #1; observation valid, original Bug 1
  attribution superseded by `1e2c0f5`)
- `cdbca96` (revised brief) —
  named the NOTABLE saturation risk in "Known gotchas →
  NOTABLE saturation dependency" as standing backlog item 6
- `OBSERVATIONS_2026_04_16_WRITING_ROOM_SURFACING_AUDIT.md` —
  the April surfacing audit; documents related budget-eviction
  patterns at MINOR; relevant for design vocabulary
- `OBSERVATIONS_2026_05_04_C2_REVENGE_GAME_SURFACING_AUDIT.md` —
  refines the surfacing audit's framing; "volume-vs-cap, not
  pair-scope" is the corrected mechanism

**Starting commit:** `1e2c0f5` on `main`. Verify HEAD before
any other action: `git rev-parse HEAD` must print
`1e2c0f5af36ac2876f5ea8552698e84d5bd7b59b`.

**Working tree:** `/Users/steve/projects/squadvault-ingest-fresh`

**Phase:** 10 — Operational Observation.

**Shape:** Code session, single wave. Step 0 is a diagnostic
harness extension or new probe; Steps 1–4 (or 1–3 if a
direction with smaller scope is chosen) are production-path
commits; Step 5 is closure memo. Reverify-as-merge-gate
applies before code commits.

---

## The mechanism (re-derived against current HEAD)

`weekly_recap_lifecycle.py:760-786` (current HEAD `1e2c0f5`):

```python
_all_angles.sort(key=lambda a: (-a.strength, a.category, a.headline))

if _all_angles:
    budgeted = []
    h_count = n_count = 0
    minor_pool: list[NarrativeAngle] = []
    for a in _all_angles:
        if a.strength >= 3 and h_count < 3:
            budgeted.append(a)
            h_count += 1
        elif a.strength == 2 and n_count < 6:
            budgeted.append(a)
            n_count += 1
        elif a.strength <= 1:
            minor_pool.append(a)
```

The sort at line 760 orders by `(-strength, category, headline)`.
Within the strength=2 tier, this is alphabetical-by-category,
then alphabetical-by-headline. Categories starting with letters
earlier in the alphabet land NOTABLE slots first; categories
later in the alphabet are evicted when `n_count` reaches 6.

STREAK as a category name competes against:
- `FAAB_AUCTION_BUST` (sometimes strength=2; alphabetically before STREAK)
- `FAAB_ROI_NOTABLE` (often strength=2; alphabetically before STREAK)
- `FRANCHISE_DEEP` (sometimes strength=2; alphabetically before STREAK)
- `PLAYER_NARRATIVE` (often strength=2; alphabetically before STREAK)
- `PLAYER_SUPERLATIVE` (sometimes strength=2; alphabetically before STREAK)

When 6+ strength=2 angles compete and STREAK is in the mix,
STREAK loses every alphabetical tiebreak against
FAAB/FRANCHISE/PLAYER categories. This is structurally identical
to the HEADLINE-pass eviction problem that the original Bug 1
addresses at strength=3.

After NOTABLE saturates, strength=2 angles do not fall through
to MINOR — the MINOR pool gates on `a.strength <= 1` (line 784).
Strength=2 angles that don't make NOTABLE are silently dropped
into the "+ N minor angles omitted" footer count.

## Specimen #1 — id=142 (W14 2025)

**Pulled from session memory; re-verify at session start.** From
the §10 Q1 closure session:

```
Narrative angles for Week 14 (what's interesting):
  [HEADLINE] [RE: Paradis' Playmakers, Brandon Knows Ball]
            Paradis' Playmakers blew out Brandon Knows Ball by 106.60
  [HEADLINE] [RE: Robb's Raiders] Egbuka, Emeka has scored
            under 8 points in 4 straight starts ...
  [HEADLINE] [RE: Robb's Raiders] Lions, Detroit has scored
            under 8 points in 4 straight starts ...
  [NOTABLE] [RE: Brandon Knows Ball] Brandon Knows Ball spent
            $51 on Thomas Jr., Brian — averaging just 10.6 ...
  [NOTABLE] [RE: Eddie & the Cruisers] Eddie & the Cruisers
            spent $32 on McConkey, Ladd ...
  [NOTABLE] [RE: Italian Cavallini] Italian Cavallini spent
            $60 on Jefferson, Justin ...
  [NOTABLE] [RE: Purple Haze] Allen, Keenan ($21 FAAB) has
            scored 103.6 points across 9 starts ...
  [NOTABLE] [RE: Brandon Knows Ball] Boutte, Kayshon ($15 FAAB)
            has scored 85.3 points ...
  [NOTABLE] [RE: Stu's Crew] Chiefs, Kansas City ($1 FAAB) has
            scored 39.0 points ...
  [MINOR] ... 3 visible MINOR ...
  (+ 112 minor angles omitted)
```

**6 NOTABLE entries — cap saturated.** All 6 are FAAB-related
(3 FAAB-bust shapes, 3 FAAB-ROI shapes). The strength=2 T9-LOSS
STREAK angle for Brandon Knows Ball (per Probe B confirmation,
detector emitted it correctly) was evicted by alphabetical
tiebreak: FAAB_AUCTION_BUST and FAAB_ROI_NOTABLE both sort
before STREAK.

The constitutional consequence: the model never saw the
canonical T9-LOSS phrasing; the prose contained no record-shape
claim; the §6 silence-fallback held; verifier's
`_RECORD_CLAIM_PATTERN` short-circuited; verification passed
with `passed: true`. **Constitutional integrity is not violated
by this eviction**, but the recap loses density on a story
worth telling: Brandon's all-time-record-approach situation.

## Cross-franchise structural-recurrence evidence

From `22770d9`'s candidate scan: 19 (season, week, franchise)
tuples across 7 franchises and 16 seasons satisfy T9-LOSS or
T9-WIN streak-shape arithmetic. Pre-2024 candidates are blocked
from regen-based evidence-gathering by the `occurred_at`
infrastructure gap. This means specimen-N hunting in pre-2024
data is not currently possible without unrelated infrastructure
work.

The 7 distinct franchises (0002, 0003, 0005, 0006, 0007, 0008,
0009) plus Brandon (0010) covers 8 of the 10 PFL Buddies
franchises. The structural pattern is league-wide, not
Brandon-specific.

Within already-processed corpus (2024–2025), id=142 is
specimen #1. Specimen #2 within already-processed corpus is
extremely unlikely without further 2025 weeks completing — the
W11–W18 candidates already discovered are all Brandon. The
diversity trigger from the original Bug 1 thread (≥2 franchises)
is unsatisfiable within already-processed corpus.

**The brief proceeds on weight of: specimen #1 mechanism
confirmation + structural-recurrence evidence**, not on
multiple empirical specimens. The labeling-correction memo's
mechanism re-derivation provides the rigor that a single
specimen alone wouldn't.

---

## Two design philosophies (the load-bearing choice)

### Philosophy 1 — Architectural symmetry across MINOR and NOTABLE

**Principle.** Both tiers below HEADLINE use rotation-aware
fairness; HEADLINE remains pure-strength-priority because cap=3
forces hard prioritization. NOTABLE structurally mirrors MINOR's
rotation hash (and possibly its 1-per-category cap and
coverage-first sort, depending on Step 0 evidence).

**Concrete shape (Direction B — rotation-only minimal change).**
Apply MINOR's rotation hash domain (`category:season:week`) at
the NOTABLE pass. The sort at line 760 stays unchanged for
strength-3 (HEADLINE keeps deterministic strength-priority),
but a separate rotation-aware sort is applied within the
strength-2 tier before the budget loop.

```python
# Pseudocode — actual implementation in Steps below
strength_2_pool = [a for a in _all_angles if a.strength == 2]

def _notable_key(a):
    rotation = hashlib.md5(
        f"{a.category}:{season}:{week_index}".encode()
    ).hexdigest()
    return (rotation, a.headline)

strength_2_pool.sort(key=_notable_key)

# Then iterate strength_2_pool in NOTABLE pass instead of _all_angles
```

**Tradeoffs.**

- (+) Architectural symmetry: rotation principle applies wherever
  alphabetical tiebreaks would systematically lock out
  categories. Same hash domain, same determinism guarantee.
- (+) Direction-agnostic: T9-WIN, T9-LOSS, REVENGE_GAME,
  TRADE_OUTCOME, and any other strength=2 STREAK or other
  category benefits equally.
- (+) No category-asymmetry — STREAK gets no special
  treatment; the principle is "fair rotation," not "STREAK
  matters most."
- (−) Doesn't address the load-bearing-category argument
  (STREAK's verifier surface is Cat 3/Cat 3c HARD; structural
  weight is asymmetric whether or not we acknowledge it
  architecturally).
- (−) Rotation moves *which* category loses each week; over a
  season every category gets fair turns. But within any *single*
  week, the model still doesn't see all the angles that "matter."
  For weeks where multiple high-priority categories all need
  surfacing, rotation doesn't help density.
- (−) The 1-per-category MINOR cap exists because MINOR has 19
  detectors competing for 4 slots. NOTABLE has fewer competing
  categories (typically 3–8 strength=2 angles per week from
  what id=142 shows). The 1-per-category constraint at NOTABLE
  may not bite often; rotation alone may be sufficient.

**Rotation-domain question for Step 0.** Whether to also adopt
the 1-per-category cap from MINOR is a Step 0 evidence question:
if id=142-shape weeks consistently have 6+ FAAB-or-PLAYER
strength=2 angles (the failure mode), the cap helps; if not, it's
unnecessary complexity.

---

### Philosophy 2 — STREAK carve-out via per-tier categorical reservation

**Principle.** STREAK is the load-bearing category for
fabrication prevention (Cat 3/Cat 3c verifier surface, helper-
bound discipline tests, the largest single-category investment
in the codebase). Categorical reservation makes the
architectural priority explicit: STREAK gets reserved slots
wherever it competes, because STREAK is constitutionally
weighted differently from other categories.

**Concrete shape (Direction C — reservation parallel to
original Bug 1's design).** At NOTABLE pass, reserve 1 of 6
slots for STREAK strength=2 if any STREAK strength=2 angle
exists. Other strength=2 angles compete for the remaining 5
slots via the existing alphabetical sort. Direct parallel to
original Bug 1's HEADLINE design (1 of 3 reserved for STREAK
strength=3).

```python
# Pseudocode — actual implementation in Steps below
strength_2_angles = [a for a in _all_angles if a.strength == 2]
streak_s2 = [a for a in strength_2_angles if a.category == "STREAK"]
other_s2 = [a for a in strength_2_angles if a.category != "STREAK"]

# Reserve 1 of 6 NOTABLE slots for STREAK if any exists.
if streak_s2:
    budgeted.append(streak_s2[0])
    n_count = 1

remaining_s2 = sorted(
    streak_s2[1:] + other_s2,
    key=lambda a: (a.category, a.headline),
)
for a in remaining_s2:
    if n_count >= 6:
        break
    budgeted.append(a)
    n_count += 1
```

**Tradeoffs.**

- (+) Reuses already-designed pattern from original Bug 1's
  brief; same shape, smaller blast radius for diff review.
- (+) Constitutional priority is explicit in code: STREAK's
  load-bearing role is encoded structurally, not relegated to
  comment-level convention.
- (+) Surgically addresses the specific failure mode without
  disturbing other categories' surfacing.
- (+) Pairs cleanly with original Bug 1's HEADLINE reservation
  if/when that activates: STREAK gets 1 reserved at HEADLINE
  for strength=3 + 1 reserved at NOTABLE for strength=2.
- (−) Introduces category-asymmetry; future categories asking
  for similar treatment may need their own carve-outs (slippery
  slope risk).
- (−) Doesn't address other strength=2 categories that might
  also suffer alphabetical-lockout (REVENGE_GAME, TRADE_OUTCOME).
  The April surfacing audit named these as alphabetical-lockout
  victims at MINOR; whether they suffer at NOTABLE too is an
  open empirical question that this direction doesn't measure.
- (−) If the unspoken project preference is symmetry across
  tiers, having HEADLINE+NOTABLE both reserve for STREAK while
  MINOR uses rotation creates three different mechanisms across
  three tiers. Architecturally less coherent.

---

### Recommendation: **Direction B (Philosophy 1, rotation-only at NOTABLE)**

**Justifications:**

1. **Direction-and-category-agnostic is constitutionally
   stronger.** STREAK is load-bearing for fabrication prevention,
   yes — but other categories may have their own constitutional
   weight that hasn't been audited yet. Building a fair-rotation
   mechanism instead of category-specific reservations
   future-proofs against discovering similar load-bearing-ness
   in REVENGE_GAME, TRADE_OUTCOME, or others.

2. **Architectural coherence is a long-term value.** Three
   different budget-tier mechanisms (HEADLINE strength-priority,
   NOTABLE STREAK-reservation, MINOR rotation+cap+coverage) is
   harder to reason about than two (HEADLINE strength-priority,
   NOTABLE+MINOR rotation-with-tier-specific-extras). The brief
   landing on rotation-at-NOTABLE preserves the option of
   later adding cap or coverage if Step 0 evidence demands it.

3. **The original Bug 1 brief's HEADLINE-reservation design is
   not undermined by this choice.** If/when Bug 1 activates, its
   reservation fires at strength=3 in HEADLINE. The two designs
   coexist: HEADLINE uses pure-strength-priority + STREAK
   reservation (because cap=3 makes pure-strength too tight for
   rotation to help), NOTABLE uses rotation (because cap=6 has
   enough room for rotation to produce fair coverage).

4. **The April surfacing audit's lessons reinforce rotation.**
   The audit found that 19 detector categories at MINOR had
   alphabetical-lockout problems; the rotation hash fix
   (committed at the unnamed prior commit per `weekly_recap_
   lifecycle.py:806–812`) addressed it without category-
   specific carve-outs. The same lockout shape recurring at
   NOTABLE points to the same systemic fix shape.

5. **The recommendation is rebuttable.** If Step 0 evidence
   shows a shape rotation can't help (e.g., NOTABLE saturates
   from a *single* category every week, not from a rotating
   set), Step 1's design pivots to Direction C. The brief's
   evidence gate makes this contingency explicit.

**Steve elects in-session.** This recommendation is the brief
author's read; the philosophical choice is sufficiently
load-bearing that Steve confirms before Step 1 ships.

---

## Scope

### In scope (Direction B baseline)

1. **Step 0** — Diagnostic harness extension or new probe to
   classify NOTABLE-saturation weeks across the 2024–2025
   corpus. Bucket counts: NOTABLE_SATURATED_WITH_STREAK_EVICTED
   (the failure mode), NOTABLE_SATURATED_NO_STREAK_EVICTED
   (saturation without integrity-relevant loss),
   NOTABLE_NOT_SATURATED (most weeks, expected). Read-only.
2. **Step 1** — Apply rotation hash to NOTABLE pass at
   `weekly_recap_lifecycle.py:781`. Mirror the MINOR-pass
   rotation hash domain (`category:season:week`); preserve
   determinism.
3. **Step 2** — Test additions: synthetic angle list with 8
   strength=2 angles (saturating NOTABLE), assert that across
   different weeks the surfaced 6 vary deterministically by
   week.
4. **Step 3 (CONDITIONAL on Step 0 evidence)** — 1-per-category
   cap at NOTABLE pass, mirroring MINOR's `_minor_cats` set.
   Ships if Step 0 evidence shows weeks with 3+ same-category
   strength=2 angles competing with STREAK; defers if not.
5. **Step 4** — Closure memo: post-fix harness re-run, id=142
   regen comparison, NOTABLE-saturation status update in
   carry-forward backlog. Reverify-as-merge-gate applies for
   Step 1 (per the standard pattern).

### In scope (Direction C alternate, if Steve elects)

1. **Step 0** — Same diagnostic harness extension; Step 0's
   bucket counts inform whether Direction C is sufficient
   (confirms STREAK is the dominant evicted category) or
   whether broader rotation is needed.
2. **Step 1** — Apply categorical reservation at NOTABLE pass
   (1 of 6 slots for STREAK strength=2 if any exists). Mirror
   original Bug 1's HEADLINE design at
   `weekly_recap_lifecycle.py:781`.
3. **Step 2** — Test additions: synthetic angle list with
   STREAK strength=2 + 6 other strength=2 angles, assert STREAK
   surfaces; angle list with no STREAK strength=2, assert all
   6 NOTABLE slots filled normally.
4. **Step 3** — Closure memo.

### Out of scope

- **Original Bug 1** (T3 strength-3 HEADLINE eviction). Remains
  deferred per Step 0b decision. Diversity trigger unchanged.
- **NOTABLE cap raise** (Direction D from the design enumeration).
  Rejected: treats symptom, not mechanism; shifts other
  budget constraints; the original brief explicitly listed
  NOTABLE-cap-raising as out-of-scope for this kind of work.
- **MINOR pass changes.** The April surfacing audit closed
  with disposition "no code change." MINOR's rotation-hash +
  1-per-category + coverage-first design is functioning as
  designed.
- **Direction A (full MINOR-mirror at NOTABLE).** If Step 0
  evidence suggests it, the brief's Direction-B baseline +
  Step 3 conditional 1-per-category cap covers most of A's
  scope without committing to coverage-first sort (which is
  intentionally MINOR-only per the surfacing audit's "breadth
  vs depth" distinction).
- **Snap-outcome detection** (memo §10 Q2). Named-only.
- **Player-streak verb inversion thread.** Brief queued at
  `afec7b6`, separate from this work.
- **`occurred_at` infrastructure backfill.** Documented, not
  required for this thread.
- **Verifier surface changes.** No new HARD/SOFT rules; the
  existing Cat 3/Cat 3c surface is unchanged. NOTABLE-saturation
  is a density question, not an integrity question — verifier
  is unaffected.
- **Architecture changes.** No changes to the budget tier
  model (HEADLINE 3 / NOTABLE 6 / MINOR 4 / total 15), to the
  strength scale, or to the deterministic seed shape.

---

## Step 0 — Diagnostic harness or new probe

Two implementation paths to choose between in-session:

**Path 1 — Extend `step_1_streak_diagnostic_harness.py`.**
Add NOTABLE_SATURATED bucket logic alongside existing
RECORD_APPROACH/STATUS_CLAIM_OMITTED buckets. Pro: existing
infrastructure; familiar invocation. Con: harness is named
"streak diagnostic"; NOTABLE saturation affects categories
beyond STREAK.

**Path 2 — New probe `scripts/notable_saturation_probe.py`.**
Single-purpose read-only probe; no integration with the
fabrication-shape classifier. Pro: scope-clean naming; doesn't
overload the streak harness's semantics. Con: another script
in `scripts/` to maintain; no integration with the §10 Q1
fabrication-shape work.

**Default: Path 2.** The existing streak harness's purpose is
narrative-shape classification (RECORD_APPROACH /
STATUS_CLAIM_*); NOTABLE saturation is a different question
(budget-tier filling). Mixing them at the harness layer
conflates surfaces. New probe also has the advantage of being
discardable if the thread closes without follow-up.

**Probe output shape:**

```
For each (season, week_index) in 2024–2025 with non-empty
prompt_audit:

  notable_count: int       # entries in rendered NARRATIVE ANGLES
                           # block under [NOTABLE] tier
  notable_saturated: bool  # notable_count == 6
  evicted_strength_2_streak: int
                           # count of strength-2 STREAK angles
                           # detected by _detect_streak_records
                           # but absent from rendered block
  evicted_strength_2_total: int
                           # count of all strength-2 angles
                           # generated but absent from rendered
                           # block (NOTABLE saturation casualties)
  bucket: NOTABLE_SATURATED_WITH_STREAK_EVICTED
        | NOTABLE_SATURATED_NO_STREAK_EVICTED
        | NOTABLE_NOT_SATURATED
```

**Evidence gate (two-tier, paralleling §10 Q1's gate shape):**

- **Integrity tier:** N/A. NOTABLE saturation is a density
  question, not an integrity question (§6 silence-fallback
  holds; verifier passes). The integrity surface for STREAK
  fabrication remains the original Bug 1's STATUS_CLAIM_EVICTED
  bucket, which is unchanged.
- **Editorial tier:**
  `NOTABLE_SATURATED_WITH_STREAK_EVICTED ≥ 2 distinct weeks`
  → ship Step 1 (rotation hash). The diversity criterion
  (multiple weeks) ensures the fix isn't designed for a
  one-off pattern.
- **Defer tier:** All NOTABLE_SATURATED_WITH_STREAK_EVICTED in
  one week (e.g., id=142 only) → defer Step 1 to a follow-on
  thread; document the single-specimen disposition in Step 0
  memo.

The defer condition is subtle. id=142 alone is one specimen;
the cross-franchise candidate scan from `22770d9` predicts
many more cases exist in pre-2024 data but blocked by
infrastructure. So "single specimen in already-processed
corpus" is consistent with both (a) single-week aberration and
(b) tip of structural-recurrence iceberg. Step 0's probe
across 2024–2025 should produce more datapoints — whether
within-corpus diversity meets the trigger is the empirical
question.

If 2024–2025 produces only one specimen, the brief's preamble
(specimen #1 + structural recurrence from candidate scan) is
the strongest evidence available without infrastructure work.
Steve elects whether that's sufficient for Step 1.

---

## Step 1 — Direction B (recommendation): NOTABLE rotation hash

**Single file:** `src/squadvault/recaps/weekly_recap_lifecycle.py`

**Current shape (lines 773–786):**

```python
if _all_angles:
    budgeted = []
    h_count = n_count = 0
    minor_pool: list[NarrativeAngle] = []
    for a in _all_angles:
        if a.strength >= 3 and h_count < 3:
            budgeted.append(a)
            h_count += 1
        elif a.strength == 2 and n_count < 6:
            budgeted.append(a)
            n_count += 1
        elif a.strength <= 1:
            minor_pool.append(a)
```

**New shape (Direction B baseline):**

```python
if _all_angles:
    budgeted = []
    h_count = n_count = 0
    minor_pool: list[NarrativeAngle] = []

    # Phase 1: HEADLINE (unchanged) — strength-priority,
    # deterministic alphabetical tiebreak.
    for a in _all_angles:
        if a.strength >= 3 and h_count < 3:
            budgeted.append(a)
            h_count += 1

    # Phase 2: NOTABLE — rotation-hash tiebreak prevents
    # alphabetical lockout of late-alphabet categories
    # (STREAK, REVENGE_GAME, TRADE_OUTCOME) when 6+ strength-2
    # angles compete. Same domain as the MINOR rotation hash
    # at lines 806–812 (`category:season:week`).
    notable_pool = [a for a in _all_angles if a.strength == 2]
    if notable_pool:
        def _notable_key(a: NarrativeAngle) -> tuple[str, str]:
            rotation = hashlib.md5(
                f"{a.category}:{season}:{week_index}".encode()
            ).hexdigest()
            return (rotation, a.headline)
        notable_pool.sort(key=_notable_key)
        for a in notable_pool:
            if n_count >= 6:
                break
            budgeted.append(a)
            n_count += 1

    # Phase 3: MINOR pool collection (unchanged behavior; just
    # restructured loop above).
    for a in _all_angles:
        if a.strength <= 1:
            minor_pool.append(a)
```

**Determinism preservation:** rotation hash is seeded on
`category:season:week`; same week always produces the same
ordering. Reproducible against fixed inputs.

**Tests required:**
- Existing tests asserting NOTABLE saturation behavior get
  rotation-aware assertions: same-week consistency, different-
  week variation. (Verify in-session whether existing tests
  pin specific orderings — earlier survey returned zero such
  tests, but session-start re-grep confirms.)
- New test: synthetic angle list with 8 strength=2 angles
  including 1 STREAK; across different (season, week) inputs,
  STREAK appears in NOTABLE for some weeks and is rotated out
  for others; aggregate over 12 weeks shows STREAK surfaces in
  approximately `6/8 = 75%` of weeks (up from 0% pre-fix when
  alphabetically locked out).

**Constraint surfaced from session-start probes:**
- Step 3 grep for `narrative_angles_text` test assertions
  returned empty. **No test fixtures pin NOTABLE ordering.**
  The fixture-byte-equality risk that the original Bug 1
  brief flagged for HEADLINE does not appear to apply at
  NOTABLE.
- Reverify_tag references are schema-only; no test/production
  code pins reverify-tag-to-ordering. Reverify-as-merge-gate
  will surface any prompt-text byte-equality drift in the
  W11/W13 fixture set, but no asserted-equal hazard exists.

---

## Step 1 — Direction C (alternate): NOTABLE STREAK reservation

**Single file:** `src/squadvault/recaps/weekly_recap_lifecycle.py`

**New shape (Direction C):**

```python
if _all_angles:
    budgeted = []
    h_count = n_count = 0
    minor_pool: list[NarrativeAngle] = []

    # Phase 1: HEADLINE (unchanged).
    for a in _all_angles:
        if a.strength >= 3 and h_count < 3:
            budgeted.append(a)
            h_count += 1

    # Phase 2: NOTABLE with STREAK reservation. STREAK is
    # load-bearing for fabrication prevention (Cat 3/Cat 3c
    # verifier surface); reserve 1 of 6 slots for STREAK
    # strength=2 if any exists.
    strength_2_angles = [a for a in _all_angles if a.strength == 2]
    streak_s2 = [a for a in strength_2_angles
                 if a.category == "STREAK"]
    other_s2 = [a for a in strength_2_angles
                if a.category != "STREAK"]

    if streak_s2:
        budgeted.append(streak_s2[0])
        n_count = 1

    remaining_s2 = sorted(
        streak_s2[1:] + other_s2,
        key=lambda a: (a.category, a.headline),
    )
    for a in remaining_s2:
        if n_count >= 6:
            break
        budgeted.append(a)
        n_count += 1

    # Phase 3: MINOR pool collection (unchanged).
    for a in _all_angles:
        if a.strength <= 1:
            minor_pool.append(a)
```

**Edge cases requiring tests:**
- 0 STREAK strength=2 angles → reservation slot is unused;
  6 NOTABLE slots fill normally (`n_count == min(6,
  len(other_s2))`).
- 2+ STREAK strength=2 angles → first goes to reserved slot;
  subsequent compete for remaining 5 slots via existing
  alphabetical sort.
- 7+ strength=2 angles total with 1 STREAK → STREAK gets
  reserved slot; top 5 other_s2 (by alphabetical sort) fill
  remaining; 1+ strength=2 angles evicted as before.

---

## Step 2 — Test additions

Single file: `Tests/test_weekly_recap_lifecycle.py` (or
wherever budget logic is exercised — Steve confirms in-session).

Per-direction tests detailed above. Common to both:
- Synthetic `_all_angles` lists with controlled strength
  distributions.
- Determinism assertion: same inputs produce same output.
- No regression on HEADLINE pass (3-slot strength-priority
  unchanged).
- No regression on MINOR pass (rotation+cap+coverage unchanged).

---

## Step 3 (CONDITIONAL, Direction B only) — 1-per-category cap

**Pre-condition for shipping this step.** Step 0 harness must
report NOTABLE-saturated weeks where 3+ of the 6 NOTABLE slots
are filled by a single category (e.g., 3 FAAB_AUCTION_BUST
plus 3 FAAB_ROI_NOTABLE in id=142). If single-category
dominance is rare, Step 3 defers; rotation alone produces
sufficient coverage.

**New shape (additive on Direction B):**

```python
# Phase 2: NOTABLE — rotation-hash tiebreak + 1-per-category
# cap (mirrors MINOR-pass behavior at lines 821-825).
notable_pool = [a for a in _all_angles if a.strength == 2]
if notable_pool:
    notable_pool.sort(key=_notable_key)
    notable_cats: set[str] = set()
    for a in notable_pool:
        if n_count >= 6:
            break
        if a.category in notable_cats:
            continue
        budgeted.append(a)
        n_count += 1
        notable_cats.add(a.category)
```

This is a clean additive change to Step 1's Direction B; if
Step 0 evidence justifies it, ships in same session.

---

## Step 4 — Closure memo

Post-fix harness re-run + id=142 regen comparison + carry-
forward backlog update. Standard closure pattern from §10 Q1
Step 1.4. Reverify-as-merge-gate applies for Step 1 commit
(per the standard pattern; specific prompts to scan listed
in-session).

Memo placement:
`_observations/OBSERVATIONS_<YYYY_MM_DD>_NOTABLE_SATURATION_POST_FIX.md`.

---

## Open questions

### Q1 — Direction choice (B vs C)

**Default: Direction B (rotation hash) per recommendation
above.** Steve confirms in-session before Step 1 ships. If
Direction C is elected, the Step 1 plan above changes
accordingly; Step 3 (1-per-category cap) is no longer
applicable.

### Q2 — Diagnostic-harness placement (Path 1 vs Path 2)

**Default: Path 2 (new probe).** Per scope-clean naming
argument above.

### Q3 — Step 0 evidence threshold

**Default: ≥2 distinct weeks of
NOTABLE_SATURATED_WITH_STREAK_EVICTED in 2024–2025 corpus** to
ship Step 1. Single-specimen disposition is "defer with
preamble evidence" — Steve elects whether structural-recurrence
candidate scan + id=142 alone is sufficient.

### Q4 — Rotation-domain seed (`category:season:week` vs other)

**Default: same as MINOR rotation domain.** Consistency across
NOTABLE and MINOR rotation produces predictable behavior.
Alternative would be `category:franchise_id:season:week`
(franchise-aware rotation) but this introduces a different
semantics question — out of scope unless Step 0 surfaces a
need.

### Q5 — Test count baseline confirmation

The brief asserts ~1945 passed at HEAD `1e2c0f5`. Reconfirm at
session start.

---

## Standing backlog (carries forward post-this-thread)

1. **(THIS SESSION when run)** NOTABLE-pass alphabetical
   lockout investigation.
2. SCORE_VERBATIM 59-row legacy drift (open horizon thread).
3. Cat 3c row-76 W14 2025 attribution edge case (open horizon,
   deferred — does not affect detection, only label).
4. Snap-outcome detection (memo §10 Q2, named-only).
5. Player-streak verb inversion thread (`afec7b6` brief queued).
6. **(REPLACED by this session)** NOTABLE-pass alphabetical
   lockout investigation — promoted to active.
7. Tests/ ruff cleanup.
8. `d['raw_mfl']` write at `extract_recap_facts_v1.py:190`
   (deferred).
9. Original Bug 1 (T3 HEADLINE strength-3 eviction) — deferred
   per Step 0b; diversity trigger unchanged.
10. `WEEKLY_MATCHUP_RESULT.occurred_at` backfill — documented
    per `22770d9`; activates on historical-recap use case OR
    pre-2024 specimen-N requirement.
11. Parametrized helper-bound verifier test (named-only,
    no urgency).

---

## Anti-drift discipline

1. **Re-grounding is session step 0.** Verify HEAD =
   `1e2c0f5`, run mechanism re-derivation against current
   `weekly_recap_lifecycle.py:760-786`, confirm test/lint
   baseline before any code change.
2. **Diagnostic-first applies.** Step 0 probe runs before any
   production-path commit. If Step 0 evidence shows
   single-specimen-in-corpus disposition, Steve elects ship-
   or-defer before Step 1 commits.
3. **Mechanism re-derivation before naming.** The labeling
   error in `a5c5c1b` and `22770d9` came from generalizing a
   thread name without re-deriving against source. This brief's
   thread name (NOTABLE-pass alphabetical lockout) is derived
   from the actual code mechanism at line 781; future
   generalizations must re-verify against current source.
4. **One topic per commit; staging gate before each commit.**
5. **Test delta assertion preferred over absolute counts.**
6. **Helper-bound discipline.** No tests or production code
   should hard-code the rotation hash output; the rotation
   function is the source of truth, tests assert on its
   determinism not its specific value.
7. **Original Bug 1 stays out of scope.** This thread does
   NOT address original Bug 1. If Step 0 surfaces
   STATUS_CLAIM_EVICTED or STATUS_CLAIM_OMITTED activity that
   meets the Bug 1 diversity trigger, that's a *separate*
   thread to promote — not in-session scope creep.

---

## Opening move

```
cd ~/projects/squadvault-ingest-fresh
git fetch origin
git rev-parse HEAD                     # expect 1e2c0f5
shasum -a 256 \
  src/squadvault/recaps/weekly_recap_lifecycle.py \
  _observations/OBSERVATIONS_2026_05_06_BUG_1_LABELING_CORRECTION.md \
  _observations/OBSERVATIONS_2026_05_06_T9_LOSS_POST_FIX_REVERIFY.md
sed -n '760,830p' src/squadvault/recaps/weekly_recap_lifecycle.py
pytest -q 2>&1 | tail -3               # record baseline
ruff check src/ Tests/                 # confirm zero
mypy src/squadvault/core/              # confirm clean (60 files)
```

Then Step 0a (probe creation) → Step 0b (probe run + Step 0
memo) → **decision point: Steve confirms Direction B or C; if
B, Step 0 evidence determines whether Step 3 ships** → Step 1
(production-path) → Step 2 (tests) → Step 3 (conditional) →
Step 4 (closure memo).

---

## The point

This thread closes the NOTABLE-pass surfacing-budget eviction
of late-alphabet strength=2 categories, with STREAK as the
primary motivating evidence and rotation-hash-at-NOTABLE as the
recommended mechanism. Direction B preserves architectural
coherence between MINOR and NOTABLE; Direction C preserves
parallelism with the (still-deferred) original Bug 1's HEADLINE
reservation. Steve's election is the one philosophical choice;
everything else is mechanical.

The labeling correction memo (`1e2c0f5`) established that this
thread is *not* "Bug 1" — it is its own thread with its own
mechanism, scope, and disposition. Original Bug 1 remains
deferred. The two threads share a mechanism family but are
mechanically distinct and would have different fixes.

Mechanism first. Direction second. Step 0 third. Production
fourth.
