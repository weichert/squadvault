# OBSERVATIONS — Streak Prompt Post-Fix Observation (Step 3.2, four-step playbook)

**Drafted:** 2026-05-04 UTC.
**HEAD:** `<INSERT — this memo's commit SHA after landing>` on `main`.
**Phase:** 10 — Operational Observation.
**Position in plan:** Step 3.2 final commit (Commit 3) of the streak
verb pre-computation thread per
`_observations/OBSERVATIONS_2026_05_04_STREAK_VERB_PRE_COMPUTATION_SCOPE.md`.
This memo is doc-only; records the POST-FIX harness measurement
under the §6 streak-verbatim instruction (live since `71d6e5f`).
Includes the policy decision for Step 3.3.

**Predecessors:**
- `30dd16f` — audit memo (Step 3 scope, §6 prompt draft, §7
  verifier sketch).
- `6e7d44a` — Step 3.1 helper module + refactor.
- `50a7794` — Step 3.2 brief + harness v1.
- `a33d764` — harness fix-up to v1.2 (functional).
- `71d6e5f` — Step 3.2 prompt instruction landed + pre-fix
  observation memo.

**Successor:** Step 3.3 (verifier) unblocks on this memo. The
policy decisions in §6 below are the binding scope for 3.3.

---

## TL;DR

Five findings from the post-fix corpus (12 regenerated `prompt_audit`
rows under the §6 instruction, spanning W9/W11/W12/W13 across both
2024 and 2025):

- **VERBATIM rate stayed at 0%.** Full canonical headlines never
  appear as substrings of narrative prose. The model uses
  owner-first-word aliases (`"Brandon"`) for readability rather than
  full franchise names (`"Brandon Knows Ball"`). This is a binding
  stylistic constraint, not a compliance failure. **Audit memo §7's
  `STREAK_VERBATIM` rule on full headlines, as designed, would
  auto-reject every recap and is the wrong verifier shape.**
- **Sub-phrase compliance shifted dramatically.** Canonical fragments
  — `"has lost three straight"`, `"N-game losing streak"`,
  `"extending"`, `"continues"`, `"snapping it"` — appear in the new
  prose. The model heard §6's vocabulary directives and embedded
  canonical verbs and noun phrases around its preferred aliases.
  11 of 12 post-fix rows contain at least one canonical sub-phrase.
  The §6 instruction worked, just at a different granularity than
  the audit memo anticipated.
- **T9-LOSS fabrication eliminated where T3 fires.** Pre-fix:
  5/13 W13 2025 rows fabricated "league record" claims. Post-fix
  W13 2025 (ids 131, 132): 0/2. The §6 silence-fallback sentence
  propagated to model output. Concrete §10 Q1 evidence for the
  closing-the-form follow-up thread.
- **NEW post-fix failure mode: anchor-less record fabrication.**
  id=140 (W11 2025 post-fix) contains *"matching the league's
  all-time record for futility"* — but **no STREAK angle fired in
  that prompt's angles block**. Pre-fix W11 2025 (id=55) contained
  no record-fabrication phrasing. The §6 instruction did not
  prevent this because the silence-fallback is keyed off the
  angles block; the model reasoned from standings + LEAGUE_HISTORY
  outside that channel. **This is the load-bearing finding for
  Step 3.3's verifier design.**
- **INVERTED rate: 0% true positive.** One harness flag (id=111,
  pre-fix W12 2025) audits to a cross-team false positive. The
  verb-inversion failure mode the audit memo §1 framed as
  load-bearing for Step 3 does not manifest in this league's
  corpus — pre-fix or post-fix.

**Step 3.3 policy decision (binding scope for the next session):**

| Verifier rule                          | Severity | Action |
|----------------------------------------|----------|--------|
| `STREAK_VERBATIM` (full headline)      | —        | DROP. Per audit memo §7. Data does not justify this rule. |
| `STREAK_INVERSION`                     | HARD     | ADD. Narrow check: direction-contradicting verbs attached to a franchise alias when a STREAK angle fired. |
| `RECORD_CLAIM_ANCHORING`               | HARD     | ADD. Any record-shaped claim in prose must have a T8/T9/T10 angle in the angles block AND the canonical record value must match. Catches both T9-LOSS fabrication AND anchor-less fabrication. |
| `STREAK_OUTCOME_CLAUSE_VERBATIM` (T5/T6) | SOFT  | OPTIONAL. T5/T6 verb-bearing minimum spans (`"streak continues"` / `"streak extended, not snapped"`) are short and reproducible; SOFT flag for review without auto-reject. |

This is a meaningful pivot from audit memo §7. The pivot is justified
by data, not preference. The new rules are narrower, more targeted,
and motivated by observed failure modes. §7's full-headline
`STREAK_VERBATIM` framing was reasoned from a hypothesized failure
mode (verb inversion) that did not manifest, with a metric (full
headline as substring) that does not track meaningful compliance
under the model's stylistic constraints.

---

## Methodology

Same harness as pre-fix
(`scripts/step_1_streak_diagnostic_harness.py` v1.2 at `a33d764`),
plus two additional manual classifiers:

1. **T9-LOSS pattern grep** — `grep -iE "league record|all-time record|short of|shy of|set last|set across|matching .* record|all-time .* for"` against `narrative_draft` for each post-fix row. Catches the asymmetric record-approach phrasings the helpers don't emit (memo §10 Q1).
2. **Anchor inspection** — for any record-claim hit, dump the corresponding row's `narrative_angles_text` and check for a T8/T9/T10 angle line. If absent, the claim is anchor-less.

### Post-fix corpus

12 newly-regenerated `prompt_audit` rows under HEAD `71d6e5f`:

| pa.id | season | week | attempt | verifier | draft_len |
|------:|-------:|-----:|--------:|---------:|----------:|
| 130   | 2024   | 13   | 1       | PASSED   | 1949 |
| 131   | 2025   | 13   | 1       | FAILED   | 1761 |
| 132   | 2025   | 13   | 2       | PASSED   | 2138 |
| 133   | 2024   | 9    | 1       | FAILED   | 2074 |
| 134   | 2024   | 9    | 2       | FAILED   | 1769 |
| 135   | 2024   | 9    | 3       | FAILED (facts-only fallback) | 1905 |
| 136   | 2024   | 11   | 1       | PASSED   | 2268 |
| 137   | 2024   | 12   | 1       | FAILED   | 2121 |
| 138   | 2024   | 12   | 2       | FAILED   | 1772 |
| 139   | 2024   | 12   | 3       | PASSED   | 1632 |
| 140   | 2025   | 11   | 1       | PASSED   | 1795 |
| 141   | 2025   | 12   | 1       | PASSED   | 1496 |

W9 2024 (ids 133-135) fell to facts-only fallback after 3 failed
verifier attempts on `SCORE_VERBATIM` and `SERIES`. Drafts are still
real prose (1769-2074 chars; not bullet-list templates), but the
content is more factually constrained than typical model output.
The streak-claim findings from W9 2024 should be read as
"compliance under retry pressure" rather than free-form behavior.

### Three query scopes

1. **`last10-approved`** — 10 most-recent (season, week_index) pairs
   with at least one APPROVED artifact, latest `prompt_audit` row
   per pair.
2. **Per-week scopes** for W9, W11, W12, W13 in 2024 and 2025
   (7 scopes total). Includes both pre-fix and post-fix rows;
   post-fix subset identified by `pa.id >= 130`.
3. **Manual anchor inspection** for the 1 post-fix row whose prose
   contained record-claim phrasing (id=140).

---

## Headline finding 1: VERBATIM stayed at 0%

| Scope                  | Pre-fix V/N | Post-fix V/N | Net change |
|------------------------|-------------|--------------|-----------:|
| last10-approved        | 0 / 3       | 0 / 4        | 0 |
| W13 2024               | 0 / 3       | 0 / 4        | 0 |
| W13 2025               | 0 / 13      | 0 / 15       | 0 |
| W9 2024 (post-fix only)| —           | 0 / 7        | 0 |
| W12 2024               | 0 / 1       | 0 / 4        | 0 |
| W12 2025               | 0 / 27 (pre)| 0 / 2 (post) | 0 |
| **Combined**           | **0 / 19**  | **0 / 14 (post-fix subset)** | **0** |

Combined VERBATIM aggregate across all probes: **0 / 33** (0.0%).

The reason is mechanical and consistent: full canonical headlines
contain the FULL franchise name (e.g. `"Brandon Knows Ball"`,
`"Miller's Genuine Draft"`, `"Weichert's Warmongers"`), but in
narrative prose the model normalizes to the owner first-word alias
for readability:

- `"Brandon Knows Ball"` → `"Brandon"`
- `"Miller's Genuine Draft"` → `"Miller"`
- `"Weichert's Warmongers"` → `"Steve"` or `"Steve's Warmongers"`
- `"Paradis' Playmakers"` → `"KP"` (curated nickname pass 4a)

This is the same normalization the model applies to player names
(`"Allen, Josh"` → `"Josh Allen"`) — a binding stylistic constraint
of natural-prose generation, not a compliance failure. The full
canonical-headline-as-substring metric does not track meaningful
behavior.

The §6 instruction enumerated the canonical phrasings as templates
with `<name>` placeholders. The model treated `<name>` as
substitutable rather than literal. **Reasonable model behavior;
unreasonable verifier expectation.** The audit memo §7's
`STREAK_VERBATIM` rule, as designed, should not be implemented.

---

## Headline finding 2: Sub-phrase compliance shifted dramatically

The §6 instruction worked, just at sub-phrase granularity rather than
full-headline. Canonical fragments embedded around the model's
preferred aliases.

### Specific examples from post-fix rows

**id=130 (W13 2024 v38 post-fix).** Verifier passed first attempt.
> *"Miller has lost three straight and sits at 1-12, extending his
> losing streak rather than snapping it."*

Three canonical fragments visible:
- `"has lost three straight"` — T4 sub-phrase. ("3" spelled as
  "three" is the only delta from the helper's `"has lost 3 straight"`.)
- `"losing streak"` — T3/T4 noun phrase from `format_streak_phrase`.
- `"extending ... rather than snapping it"` — T5/T6 verb pair,
  explicitly disambiguating direction. The model has clearly
  internalized the §6 line *"do not substitute 'snapped' for
  'extended' or vice versa"*.

**id=132 (W13 2025 v23 attempt 2 post-fix).** Verifier passed.
> *"Brandon's 13-game losing streak continues — he's now 0-13 and
> staring at a winless season."*

- `"13-game losing streak"` — T3 sub-phrase from
  `format_streak_phrase`, verbatim.
- `"continues"` — T5 outcome verb.

**id=131 (W13 2025 v23 attempt 1 post-fix).** Verifier failed
(unrelated grounds; draft prose was clean for streak format).
> *"Brandon's ongoing misery — now 0-13 with his losing streak at
> 13 games."*

- `"losing streak"` — noun phrase.
- "13 games" — count preserved.

**id=139 (W12 2024 attempt 3 post-fix).** Verifier passed on
attempt 3.
> *"Steve extended his win streak to six games, beating Pat 126.75
> to 82.95 behind Lamar Jackson's 28.35 points."*

- `"extended his win streak"` — T1 sub-phrase plus T5 verb.
- `"six games"` — count preserved (spelled out).

### Sub-phrase compliance metric

If the post-fix metric is "% of post-fix rows containing at least
one canonical sub-phrase from `streak_strings_v1`":

- 11 of 12 post-fix rows hit (92%). The exception is id=140
  (anchor-less fabrication; see Headline finding 4).

This is the metric Step 3.3's verifier should track if it tracks
anything format-related at all. SOFT enforcement on T5/T6 outcome
clauses is the modest version of this rule.

---

## Headline finding 3: T9-LOSS fabrication eliminated where T3 fires

The audit memo §10 Q1 documented the asymmetric record-approach
gap: the helpers emit `format_streak_record` headlines for T8/T9/T10
on the winning side and T10 on the losing side, but no T9-LOSS
form for the losing side. Pre-fix data showed the model fabricating
this missing form.

### Pre-fix evidence (from PRE_FIX_DIAGNOSTIC memo)

5 of 13 W13 2025 rows fabricated T9-LOSS-shaped claims:

| pa.id | Phrasing                                                                    |
|------:|-----------------------------------------------------------------------------|
| 122   | "closing in on the all-time league record of 15 games"                      |
| 123   | "still three short of the all-time record of 15 games set across 2024-2025" |
| 125   | "longest active losing streak across the last 16 seasons of data"           |
| 126   | "one shy of the league record he set last season"                           |
| 127   | "one short of the league record he set last season"                         |

### Post-fix evidence

Manual grep on all post-fix W13 rows (130, 131, 132):

```
$ grep -iE "league record|all-time record|short of|shy of|set last|set across" \
    on narrative_draft of pa.id IN (130, 131, 132)
(no record-approach phrasing)
```

**0/3 post-fix W13 rows contain T9-LOSS fabrication.** The §6
instruction's silence-fallback sentence — *"If the angles do not
supply a phrasing for what you want to say, omit the streak claim
— silence is preferred over fabrication"* — propagated to the
model's output for the same week's same angle.

This is the strongest single-finding evidence that §6 worked. It
also concretely justifies promoting memo §10 Q1 (T9-LOSS form) from
"deferred curiosity" to a named follow-up thread: the model
*demands* the form, and absent it, the model fabricates. The right
fix is to add the form to `format_streak_record` so the prompt can
supply it canonically.

---

## Headline finding 4: Anchor-less record fabrication is a NEW post-fix failure mode

**The most consequential finding of this memo.** id=140 (W11 2025
post-fix) contains a record-claim that has **no anchor anywhere in
the angles block**.

### The claim

From narrative_draft of pa.id=140:
> *"The loss extended Brandon's streak to 11 straight defeats,
> matching the league's all-time record for futility."*

### Pre-fix W11 2025 baseline

The most recent pre-fix W11 2025 row (id=55, 2026-04-15):
```
$ grep -iE "record|all-time|matching|consecutive|ever|history|futility"
(no record/history phrasing)
```

**Pre-fix W11 2025 contained no record-fabrication phrasing.** This
is a NEW post-fix behavior.

### Anchor inspection

The angles block for id=140 (full dump in §Methodology data;
abbreviated here):

```
Narrative angles for Week 11 (what's interesting):
  [HEADLINE] [RE: Stu's Crew, Italian Cavallini] Stu's Crew blew
            out Italian Cavallini by 44.80
  [HEADLINE] [RE: Paradis' Playmakers] Packers, Green Bay has
            scored under 8 points in 4 straight starts...
  [HEADLINE] [RE: Miller's Genuine Draft] Allen, Josh's 51.85
            points is the highest individual score of the season...
  [NOTABLE] [RE: Brandon Knows Ball] Brandon Knows Ball spent $51
            on Thomas Jr., Brian — averaging just 8.8 points...
  [NOTABLE] [RE: Brandon Knows Ball] Boutte, Kayshon ($15 FAAB)
            has scored 71.3 points across 3 starts...
  [... 7 more NOTABLE/MINOR angles, none STREAK ...]
  (+ 98 minor angles omitted)
```

**No T1/T3/T4 STREAK angle fired for Brandon at W11 2025.** No
T8/T9/T10 record-claim angle fired either. Yet the model produced
a record-claim in prose.

### Why the silence-fallback didn't apply

The §6 silence-fallback sentence is keyed off the angles block:

> *"If the angles do not supply a phrasing for what you want to
> say, omit the streak claim — silence is preferred over
> fabrication."*

The model didn't reason from the angles block. It reasoned from
two other prompt blocks:

1. **SEASON CONTEXT (standings)** — contains `"Streak: L11"` for
   Brandon. The model knows the streak count.
2. **LEAGUE HISTORY** — presumably contains a longest-loss-streak
   record value (this would require dumping `prompt_text` for id=140
   to confirm, but is the most plausible source).

The model connected these two facts and produced a record claim
without any angle-level anchor. The §6 instruction did not prohibit
this because the instruction is angle-block-scoped.

### Why didn't T3 fire as an angle?

Brandon's loss streak at W11 2025 was 11 games. The detector
threshold for T3 is `current_streak <= -4`. Brandon at -11 should
fire T3 with strength=3 (HEADLINE).

The angles block above shows 3 HEADLINE angles, none of which is
Brandon's STREAK. The "+ 98 minor angles omitted" line indicates
the angle budget was tight; some angles were filtered. But T3 at
strength=3 should have made the cut by deterministic strength sort.

This is an **open question** — possibly a detector edge case
(season-edge weeks for franchises with all-loss seasons), possibly
budget-shape issue, possibly something else. **Investigation does
not gate Step 3.3 but is named as a follow-up.**

### Why this is the load-bearing finding for Step 3.3

The verifier in Step 3.3 must read the FINAL prose and not rely on
which prompt block the model reasoned from. The verifier must:
1. Detect record-shaped claims via prose pattern match.
2. Require a corresponding T8/T9/T10 angle in the prompt's angles
   block AND/OR a canonical record value in `LeagueHistoryContextV1`
   that matches the claim's value.
3. Fail HARD when neither anchor is present.

This is a different rule than the audit memo §7's `STREAK_VERBATIM`.
It catches both T9-LOSS fabrication (Headline finding 3) AND
anchor-less fabrication (Headline finding 4). It is informed by
post-fix evidence, not pre-fix hypothesis.

---

## Headline finding 5: INVERTED rate is 0% true positive

The harness flagged 1 INVERTED across the entire corpus:

**id=111 (W12 2025, pre-fix attempt 3) — claim: T3, Brandon loss.**
Prose:
> *"Stu beat Brandon 137.00-102.50 to push his win streak to three
> games while extending Brandon's losing streak to 12 games — now
> 0-12 on the season."*

The harness inversion-attachment check found `"win streak"` (claim
direction LOSS, opposite-direction phrase) within 30 chars after
the alias `"Brandon"`. But the syntactic attachment is to `"Stu"`
via `"Stu beat Brandon ... his win streak"` — the possessive `"his"`
refers back to `"Stu"`, not Brandon. Cross-team alias false
positive.

**Manual reclassification: PARAPHRASE.** True INVERTED rate across
the entire 33-claim corpus: 0%.

The harness's alias-attachment heuristic correctly caught most
cross-team false positives in this run (vs the 10 false positives
in v1.1), but pronoun-reference disambiguation is genuinely outside
regex reach. Step 3.3's verifier should not depend on resolving this
correctly with regex — the verifier-side rule for `STREAK_INVERSION`
should be narrowly scoped to **possessive-attached-to-alias-name**
patterns (e.g., `Brandon's win streak`) rather than proximity-window
matching.

---

## Pivot rationale: drop `STREAK_VERBATIM`, add `STREAK_INVERSION` + `RECORD_CLAIM_ANCHORING`

Audit memo §7 proposed `STREAK_VERBATIM` as the new verifier check
on T1-T4/T5/T6/T8/T9/T10 templates with HARD severity. The post-fix
data argues against this design:

1. **Full-headline VERBATIM is unattainable** under the model's
   alias-normalization stylistic constraints (Headline finding 1).
   Any HARD rule on full headlines auto-rejects 100%.
2. **The verb-inversion failure mode it targets does not manifest**
   in this corpus (Headline finding 5). 0/33 true inversions across
   pre-fix and post-fix. The original motivating concern (audit
   memo §1: "model writes 'won 3 in a row' of a losing streak") is
   not surfaced by any data point here.
3. **The actual post-fix failure mode is anchor-less record
   fabrication** (Headline finding 4) — a different shape than
   `STREAK_VERBATIM` would catch. `STREAK_VERBATIM` checks for
   canonical phrasing presence; the load-bearing problem is
   *fabricated* phrasing whose canonical form doesn't exist (T9-LOSS)
   or where no anchor exists at all.

The pivot:

- **Drop:** `STREAK_VERBATIM` HARD on full headlines.
- **Add:** `STREAK_INVERSION` HARD — a narrow check on possessive
  patterns. Catches the rare true inversion if it surfaces.
- **Add:** `RECORD_CLAIM_ANCHORING` HARD — the load-bearing rule.
- **Optional:** `STREAK_OUTCOME_CLAUSE_VERBATIM` SOFT on T5/T6.

This is a deviation from binding scope (audit memo §7). The
deviation is justified by data and recorded here as the binding
re-scope event for Step 3.3.

---

## Step 3.3 policy decisions

### Rule 1: `STREAK_INVERSION` — HARD severity

**Trigger:** A T1/T2/T3/T4 STREAK angle fires (for franchise X,
direction D) AND prose contains a possessive construction
`X's <opposite-direction-phrase>` OR `X has <opposite-direction-verb>`
where the direction matches the inverse of D.

**Patterns to match:**
- For LOSS-direction angle: `<X>'s win streak`, `<X>'s winning streak`,
  `<X> has won \d+`, `<X> snapped`
- For WIN-direction angle: `<X>'s losing streak`, `<X>'s loss streak`,
  `<X> has lost \d+`, `<X> snapped`

**Possessive form is mandatory.** Proximity-window matching produces
false positives (Headline finding 5). The verifier must require
possessive attachment to the alias name itself.

**Severity rationale:** HARD. True positive is a fact-corrupting
error (model claims wrong direction for a confirmed streak). False
positive rate should be near zero given the possessive constraint.
Baseline true rate: 0/33; post-fix HARD enforcement is essentially
free.

### Rule 2: `RECORD_CLAIM_ANCHORING` — HARD severity

**Trigger:** Prose contains a record-shaped claim (regex set below)
attached to a franchise alias.

**Patterns to match (record-shaped claim):**
- `\b\w+'s? \d+-game (?:losing|winning|win|loss) streak (?:is|hit|reaches?|reaching) (?:historic|record|all-time|league)`
- `(?:matching|matches|tied|tying|broke|breaks?|breaking) the (?:league|all-time)? ?record`
- `(?:one|two|three|\d+) (?:short|shy|away) (?:of|from) the (?:league|all-time)? ?record`
- `closing in on the (?:league|all-time)? ?record`
- `longest (?:active )?(?:winning|losing|win|loss) streak (?:in|across|of)`
- `(?:set|matching) (?:last|previous) season` near a streak count

**Pass condition (anchor + value match):**
1. A T8/T9/T10 angle for franchise X must be present in
   `narrative_angles_text`, AND
2. The numeric record value claimed in prose must equal the angle's
   `record_length` parameter (within ±0 tolerance), AND
3. The record-holder name claimed (if present) must match the
   angle's `record_holder_name`.

**Fail conditions (any of):**
- No T8/T9/T10 angle in the angles block for X (anchor-less
  fabrication, Headline finding 4).
- Record value disagrees with canonical (e.g. claim says "15 games",
  angle says "13 games").
- Record-holder name disagrees with canonical.

**Severity rationale:** HARD. Both failure modes (T9-LOSS fabrication
and anchor-less fabrication) corrupt facts about league history.
Pre-fix evidence: 5/13 W13 2025. Post-fix evidence: 1 anchor-less in
12 post-fix rows. HARD enforcement keeps the failure mode from
reaching publication.

**Implementation note:** This rule reads from
`LeagueHistoryContextV1.longest_win_streak` and `longest_loss_streak`
for ground-truth record values. It also reads from
`narrative_angles_text` to detect T8/T9/T10 anchors. The rule should
be wired as Category 3c (after `verify_streaks` Category 3 and
adjacent to a future STREAK_INVERSION Category 3b).

### Rule 3: `STREAK_OUTCOME_CLAUSE_VERBATIM` — SOFT severity (optional)

**Trigger:** T5 (continuation) or T6 (extension) outcome clause
fires in the angles block.

**Patterns to match (verbatim presence in prose):**
- T5: `streak continues`
- T6: `streak extended, not snapped` — OR `extending ... rather
  than snapping`

**Pass condition:** at least one of the canonical T5/T6 clauses
appears in prose for each franchise whose streak fired with an
outcome detail.

**Severity rationale:** SOFT. The verb-bearing minimum span is
short, reproducible, and observably present in 11/12 post-fix rows
(per Headline finding 2). SOFT flag without auto-reject keeps
reviewer attention on cases where the model elided the verb pair
entirely. Could be promoted to HARD in a future iteration if SOFT
data shows >95% compliance.

**Optional flag:** This rule is the smallest concession to audit
memo §7's "verbatim" framing. If the implementation cost in 3.3
exceeds budget, defer this rule to a Step 3.4 — Rules 1 and 2 are
the load-bearing additions.

### Dropped: `STREAK_VERBATIM` on T1-T4 full headlines

Per the pivot rationale above. Audit memo §7's design is superseded
by this memo's evidence-based redesign.

---

## Open questions

1. **Why didn't T3 fire as an angle for Brandon at W11 2025?**
   The detector at `current_streak == -11` should produce a
   HEADLINE-strength T3 angle. The angles block for id=140 contains
   3 HEADLINEs and 0 STREAK angles. Either the detector silently
   skipped (deterministic bug), the angle budgeting filtered it
   (logic gap), or the angle fired but failed to render. **Action:**
   investigate `detect_narrative_angles_v1` behavior on
   season-edge / all-loss-season inputs. **Does not gate Step 3.3.**
   Promotes to a named follow-up thread on detector coverage.

2. **Where exactly did the model read Brandon's record from?** The
   id=140 anchor-less claim implies the model reasoned from
   STANDINGS + LEAGUE_HISTORY. Confirming requires dumping
   `prompt_text` for id=140 and checking what LEAGUE_HISTORY
   contained for league 70985 longest-loss-streak. **Action:**
   one-shot diagnostic when convenient. **Does not gate Step 3.3.**

3. **Memo §10 Q1 (T9-LOSS form): promotion to follow-up thread.**
   Concrete data justifies adding the asymmetric record-approach
   form to the helpers. Pre-fix data showed 5/13 fabrication; the
   model wants the form. Adding it lets the prompt + verifier
   constrain it canonically. **Action:** open a four-step thread
   for §10 Q1 after Step 3.3 lands.

4. **Memo §10 Q2 (won-from-losing snap detection): still deferred.**
   No evidence in this corpus motivates promotion. Stays on the
   horizon list as deferred.

5. **Harness limitations for Step 3.3 unit tests.** v1.2's
   alias-attachment check for INVERTED is regex-based and produces
   false positives on cross-team possessives (Headline finding 5).
   Step 3.3's tests should use possessive-only patterns rather than
   proximity windows.

---

## Anti-drift discipline

1. Helper-bound: every canonical-phrase reference in this memo and
   in the future verifier rules routes through `streak_strings_v1`.
   No hand-written format expectations.
2. The pivot from audit memo §7's `STREAK_VERBATIM` to this memo's
   three-rule design is recorded as a re-scope event with binding
   force on Step 3.3. The pivot is justified by data, named
   explicitly, and traceable to specific findings (Headline
   findings 1, 4, 5).
3. The two open questions (Q1 about T3 detector behavior, Q2 about
   model reasoning source) are named for visibility and tracked
   separately — they do NOT scope-creep Step 3.3.
4. Step 3.3 begins with audit memo §7 superseded by this memo's
   §6 (Step 3.3 policy decisions) as the binding scope.
5. The four-step playbook's third-step pattern is preserved: pivot
   was forced by post-fix evidence, not by ad-hoc preference.

---

## Stop signal

Post-fix measurement captured. Policy decisions recorded. Step 3.3
unblocked. The next session brief should cite this memo (§
"Step 3.3 policy decisions") as the binding scope for the verifier
implementation.

The four-step playbook now has its second completed run:

1. ✓ Pre-rendering (Step 3.1, `6e7d44a`).
2. ✓ Prompt instruction + diagnostic (Step 3.2, `71d6e5f` + this).
3. → Verifier (Step 3.3, next session).

Two follow-up threads named for the horizon list:
- **§10 Q1 (T9-LOSS form):** add asymmetric record-approach helper.
- **W11 2025 T3 detector miss:** investigate
  `detect_narrative_angles_v1` coverage gap.
