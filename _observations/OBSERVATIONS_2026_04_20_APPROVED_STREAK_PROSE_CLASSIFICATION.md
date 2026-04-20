# Approved-recap STREAK failure prose classification

**Commit:** 07d752b
**Corpus:** `recap_artifacts` state=`APPROVED`, artifact_type=`WEEKLY_RECAP`, league_id=70985
**Scan source:** `/tmp/sv_07d752b_validation.tgz` (2026-04-19 validation run)
**Harness:** `/tmp/classify_approved_streak_failures.py`
**Trace output:** `/tmp/sv_approved_streak_classification/`
**Status:** FINAL

---

## Summary

Category counts (of 6 underlying STREAK failures):

| Category | Count | Failures |
|---|---|---|
| MISATTRIBUTION | 3 | F1, F2, F3 |
| LEGITIMATE_CATCH | 3 | F4, F5, F6 |
| PRE_EXISTING_DIGIT | 0 | (all six are spelled-count captures) |
| AMBIGUOUS | 0 | — |
| STILL_SLIPS_MULTI | 0 | (F6 has a compounding cross-week artifact; see addendum) |

Hazard breakdown for the 3 MISATTRIBUTION entries:

| Hazard | Count | Failures |
|---|---|---|
| HAZARD_A — winning-streak attribution gap | 3 | F1, F2, F3 |
| HAZARD_B — proximity substring false-match | 1 (compound) | F3 |
| HAZARD_C — proximity pass-2 misattribution | 0 | — |
| HAZARD_D — other | 0 | — |

Cross-reference against 04-19 memo's follow-up briefs:

- **Brief #1 (`_POSSESSIVE_OBJECT_WIN_STREAK`):** would resolve 2 of 3 MISATTRIBUTION entries as currently scoped (F1, F3). **F2 exposes a scope gap:** "won N straight" is a subject-of-verb construction, not possessor-of-streak-noun. A strict parallel of the losing-streak pattern does not cover it. Brief #1 needs re-scoping before implementation.
- **Brief #2 (proximity substring hardening):** would resolve F3 as defense-in-depth. F3 is already covered by Brief #1 if implemented first — Brief #2 is not a hard dependency for approved-corpus resolution of this failure set.
- **Unaddressed by either brief as currently scoped:** 1 of 3 (F2, until Brief #1 is widened).

Widening finding: **all 6 captures are spelled counts**; none would have fired pre-12bbadb/07d752b. The spelled-count widening surfaces 3 real model errors (LEGITIMATE_CATCH) that would otherwise have shipped, at the cost of surfacing 3 verifier-side defects (MISATTRIBUTION). Net value is positive but conditional on the follow-up briefs closing the verifier-side noise.

Same-week and cross-week consistency finding: **neither of the two cross-week consistency flags in this scan represents a genuine model self-contradiction.** Both are attribution artifacts downstream of MISATTRIBUTION-class defects. Detail in addendum.

---

## Corpus note

This memo classifies failures in the **APPROVED recap corpus** —
`recap_artifacts.rendered_text` where `state='APPROVED'` and
`artifact_type='WEEKLY_RECAP'`. These are recaps reviewed and shipped; a
verifier failure here means either the verifier caught a real model error
that made it past human review (LEGITIMATE_CATCH), or the verifier fires
on prose that is not actually wrong (MISATTRIBUTION).

This is disjoint from the 2026-04-19 STREAK_SPELLED_COUNT_READOUT memo,
which classified 16 rows from the `prompt_audit` corpus (draft attempts).
No row inventory overlap. The retry-loop correctness conclusions from the
04-19 memo carry over implicitly.

The attributed-franchise name in each failure's evidence string is the
**verifier's** attribution — the output of
`_resolve_streak_count_attribution`, not ground truth. "Miller's Genuine
Draft has/had a 3-game win streak" does not mean the prose is about
Miller's Genuine Draft; it means the resolver landed there. That
distinction is the whole point of this classification pass.

---

## Pipeline state at 07d752b (reference for per-failure traces)

**`_resolve_streak_count_attribution`** (line 1313) dispatches by `is_losing`:

- `is_losing=True` → runs `_POSSESSIVE_OBJECT_STREAK` against a 40-char
  pre-match window. Regex matches AND possessor mappable → that fid.
  Regex matches but possessor unmappable → `None` (silence over
  misattribution, no proximity fallback). Regex no-match → proximity.
- `is_losing=False` → goes **straight** to proximity with window=150.
  No winning-streak possessive pattern exists at 07d752b.

**`_find_nearby_franchise`** (line 421):

- Pass 1: pre-match window, pick **rightmost** lowercase alias.
- Pass 2: post-match window, pick **leftmost** lowercase alias.

**`_POSSESSIVE_OBJECT_STREAK`** (line 1219) matches
`<Proper-Noun Possessor>'s [N-game]? losing streak` only. No winning
counterpart. This is the architectural source of HAZARD_A.

**`_build_reverse_name_map`** aliases (4 passes): full franchise name
(exact + lowercase), first-word of franchise name (≥3 chars, non-stopword,
unique), last-word of franchise name (≥5 chars, non-stopword, unique),
owner first-name (≥2 chars, unique). Uniqueness is enforced per pass;
non-unique aliases are silently dropped.

---

## Per-failure classification

### Failure 1 — 2024 W4: Miller's Genuine Draft, 3-game win, actual 0/0

**Prose (±150 / span / 80):**

> The week's closest finish came down to 0.15 points as Italian Cavallini
> edged Miller's Genuine Draft 108.00-107.85. **Michele's been quietly
> building a** *three-game win streak* while Miller dropped to 0-4. Both
> teams left significant points on the bench —

**Pipeline trace:**
- pattern match: `three-game win streak` (spelled)
- parsed_count: 3; is_losing: False
- possessive-object pattern: NOT RUN (winning streak)
- attribution path: proximity-pass1
- attributed: Miller's Genuine Draft (via "miller" rightmost in pre-window)
- historical_skip: False
- other matches in week: 0

**Classification:** MISATTRIBUTION.
**Hazard:** HAZARD_A (possessive-of-streak-noun variant).

The streak subject is Michele (owner of Italian Cavallini). A
`_POSSESSIVE_OBJECT_WIN_STREAK` pattern mirroring the existing losing
pattern would match "Michele's … three-game win streak" and attribute to
Italian Cavallini via owner alias pass 4. Under the existing
unmappable-possessor silence semantics, the check would correctly verify
Italian Cavallini's actual streak rather than silencing. If the 3-game
count matches Italian Cavallini's pre-week or current streak, this flips
from MISATTRIBUTION to silent pass under Brief #1.

**Resolves under:** Brief #1 (as scoped).

---

### Failure 2 — 2024 W5: Robb's Raiders, 4-game win, actual 0/0

**Prose (±150 / span / 80):**

> Burrow exploded for 47.70 points — the highest individual score of the
> season — carrying Italian Cavallini past Robb's Raiders 135-108.
> **Michele's now** *won four straight* and sits at 4-1. Tank Bigsby,
> picked up for just $4, dropped 25.40 on Robb's be…

**Pipeline trace:**
- pattern match: `won four straight` (spelled; `_STREAK_PATTERN` group 2 —
  the "won|lost|losing N straight/consecutive/in a row" branch)
- parsed_count: 4; is_losing: False (context "won four straight" contains
  none of "losing"/"lost"/"loss"/"skid")
- possessive-object pattern: NOT RUN
- attribution path: proximity-pass1
- attributed: Robb's Raiders (via "robb" and/or "raiders" alias,
  rightmost in pre-window)
- historical_skip: False
- other matches in week: 0

**Classification:** MISATTRIBUTION.
**Hazard:** HAZARD_A, **subject-of-verb variant** (structurally distinct
from F1).

"Michele's now won four straight" is a contraction of "Michele has now
won four straight" — a subject-of-verb construction, not a
possessor-of-streak-noun. A regex paralleling `_POSSESSIVE_OBJECT_STREAK`
as written (matching `<Possessor>'s [N-game]? streak`) would not match
this. The fix needs to also cover verbal constructions where the subject
of "won N straight / consecutive / in a row" is the streak owner.

Suggested shape for the widened Brief #1:
- sub-pattern A: `<Possessor>'s [N-game]? (winning|win) streak`
- sub-pattern B: `<Subject>(?:'s|'ve|\s+has|\s+have)\s+(?:now\s+)?won\s+<N>\s+(?:straight|consecutive|in\s+a\s+row)`

Sub-pattern B is looser than A — the subject isn't always a possessive so
the proper-noun anchor has weaker discriminating power — but the
contraction "'s" in "Michele's now won four" is a reasonable anchor and
mirrors the pronoun-possessor filter already used in
`_POSSESSIVE_OBJECT_STREAK`. Pattern design for sub-B belongs in the
implementation pass, not here.

**Resolves under:** Brief #1 **only if widened** to include the verbal
construction. As scoped today (possessive-of-streak-noun only), Brief #1
does NOT cover this case.

---

### Failure 3 — 2024 W7: Ben's Gods, 5-game win, actual 0/6

**Prose (±150 / span / 80):**

> points on his bench, including Rachaad White's 26.10. That's the kind
> of lineup decision that turns a competitive game into a statement loss.
>
> **Pat's** *five-game win streak* survived Miller's winless season by
> the thinnest margin possible. Purple Haze s…

**Pipeline trace:**
- pattern match: `five-game win streak` (spelled)
- parsed_count: 5; is_losing: False
- possessive-object pattern: NOT RUN
- attribution path: proximity-pass1
- attributed: Ben's Gods
- historical_skip: False
- other matches in week: 2 (a second match in later prose not shown)

**Classification:** MISATTRIBUTION.
**Hazard:** HAZARD_A primary + **HAZARD_B compound**.

The streak subject is Pat (owner of some franchise — the prose names
"Purple Haze" shortly after, which is consistent with Pat being the owner
of Purple Haze, to be confirmed against `franchise_directory`).

"Pat's" sits directly before the match span at distance ~1 char. If "pat"
were a key in `reverse_name_map` (owner alias pass 4 or first-word alias
pass 2), pass-1 would find "pat" as the rightmost alias and attribute
there. The fact that pass-1 instead returned Ben's Gods means "pat" is
**not** a key in `reverse_name_map` — most likely dropped from pass-4
owner aliasing due to a uniqueness collision, OR Pat's franchise's owner
field carries a longer form that doesn't shorten to "pat". Confirming the
mechanism requires an ad-hoc dump of `reverse_name_map` for 2024; see
"New brief candidate" below.

With "pat" missing from the map, the rightmost alias hit in the pre-window
is "ben" **inside the word "bench"** at "points on his bench". Word-
boundary-ignorant `rfind("ben")` matches the substring. Attribution lands
on Ben's Gods — a clean HAZARD_B.

Both hazards contribute, but either Brief #1 (possessor path catches
"Pat's five-game win streak" and either attributes correctly to Pat's
franchise or silences via unmappable-possessor) or Brief #2 (word-
boundary matching prevents the "ben"-in-"bench" hit, at which point
proximity falls back to pass-2 or returns None) would resolve F3
independently.

**Resolves under:** Brief #1 (as scoped). Brief #2 would also resolve it
independently — useful defense-in-depth but not a near-term dependency
for closing F3.

---

### Failure 4 — 2024 W9: Ben's Gods, 4-game win, actual 0/1

**Prose (±150 / span / 80):**

> ts carried Stu with 36.20 points while Ben got 25.80 from Derrick Henry
> but couldn't overcome leaving 26.85 points on the bench. **The loss
> snaps Ben's** *four-game win streak* and drops him to 7-2, tied for
> first with Stu at 6-3.

**Pipeline trace:**
- pattern match: `four-game win streak` (spelled)
- parsed_count: 4; is_losing: False
- possessive-object pattern: NOT RUN
- attribution path: proximity-pass1
- attributed: Ben's Gods (via word-boundary "Ben" hits in "Ben got" and
  "snaps Ben's" — correct attribution via either)
- historical_skip: False
- other matches in week: 0

**Classification:** LEGITIMATE_CATCH.

Attribution is correct. The prose is literally "The loss snaps Ben's
four-game win streak." Ben's Gods entered W9 on a 1-game win streak
(Ben lost W7, won W8, lost W9 — a W-L-W pattern yielding the pre-week
1-game streak reported by the verifier). The 4-game claim is fabricated.

A note on the W7→W9 cross-week flag that at first glance tempts a
"model is carrying stale state about the W1-W6 six-game streak"
hypothesis: the W7 "five-game win streak" failure is not about Ben's
Gods at all (see F3 — it's Pat's streak, misattributed to Ben via the
"bench" substring hazard). So the cross-week pattern isn't a stale-
state signal; it's one verifier-side misattribution plus one genuine
model error that both nominally reference Ben's Gods via the verifier's
attribution output. No cross-recap state-leak pattern is demonstrated
by this evidence.

**Resolves under:** n/a — model-side error that the verifier correctly
catches. No verifier-side fix needed.

---

### Failure 5 — 2025 W5: Stu's Crew, 4-game losing, actual 0/2

**Prose (±150 / span / 80):**

> out belonged to Stu, who demolished Brandon 138.15-76.05. Dak Prescott
> (38.65 points) carried Stu's Crew to their first win of the season,
> snapping a *four-game losing streak*. Brandon's winless season
> continues — now 0-5 and averaging just 85.7 points pe…

**Pipeline trace:**
- pattern match: `four-game losing streak` (spelled)
- parsed_count: 4; is_losing: **True**
- possessive-object pattern: ran, did not match (prose uses "snapping a
  four-game losing streak" — indefinite article, no possessor name
  directly preceding the N-game phrase)
- attribution path: proximity-pass1
- attributed: Stu's Crew (via "stu" alias and/or "stu's crew" full-name
  match, rightmost in pre-window)
- historical_skip: False
- other matches in week: 0

**Classification:** LEGITIMATE_CATCH.

Attribution is correct. The prose frames Stu's Crew as the snapper of
their own losing streak — "Dak Prescott … carried Stu's Crew to their
first win of the season, snapping a four-game losing streak." The claim
is two compounded fabrications: (a) Stu's Crew entered W5 at 2-2 with a
2-game losing streak, not 0-4; (b) W5 was not their first win of the
season. The verifier catches only the count discrepancy via the STREAK
check; the "first win of the season" fabrication is outside STREAK scope
and would require a separate win-record check.

Note on the losing-streak pipeline: `_POSSESSIVE_OBJECT_STREAK` did run
here (because is_losing=True) but correctly did not match — there is no
`<Proper Noun>'s [N-game] losing streak` construction in the 40-char pre-
window. Attribution fell through to proximity and landed correctly. This
is the intended happy path for the losing-streak check.

**Resolves under:** n/a — model-side fabrication correctly caught.

---

### Failure 6 — 2025 W16: Weichert's Warmongers, 3-game win, actual 5/4

**Prose (±150 / span / 80):**

> it comes.
>
> KP advances to his seventh championship appearance across the last 16
> seasons, extending his five-game win streak and 12-2 record. **Steve's**
> *three-game win streak* carries the 9-5 Warmongers to their first title
> game since the data began track…

**Pipeline trace:**
- pattern match: `three-game win streak` (spelled)
- parsed_count: 3; is_losing: False
- possessive-object pattern: NOT RUN
- attribution path: **proximity-pass2** (post-match window)
- attributed: Weichert's Warmongers — via "warmongers" last-word alias
  found in the post-match text "carries the 9-5 Warmongers"
- historical_skip: False
- other matches in week: 2 — the "five-game win streak" earlier in the
  same paragraph

**Classification:** LEGITIMATE_CATCH.

Attribution to Warmongers is correct in substance — "Steve's three-game
win streak carries the 9-5 Warmongers" unambiguously identifies the
Warmongers as the streak owner. But the attribution **path** is fragile:
pass-1 found no alias in the 150-char pre-match window, meaning "steve" is
not a key in reverse_name_map for this season. This implies the owner
first-name pass-4 aliasing dropped "steve" due to a uniqueness collision.
Post-match proximity catches "warmongers" and lands correctly — but this
is luck, not design.

The 3-game claim itself is demonstrably wrong. Warmongers entered W16 on
a 4-game win streak and exited on a 5-game streak. Neither actual nor
pre-week matches 3. Model-side fabrication, correctly caught.

**Resolves under:** n/a for the LEGITIMATE_CATCH itself — model error,
no verifier fix needed. But the attribution fragility surfaced here is
worth a separate observation, captured in "New brief candidate" below.

---

## Cross-week consistency addendum

The validation scan reported two cross-week consistency flags in addition
to the 6 per-week STREAK failures. Prose inspection reveals **neither is
a genuine model self-contradiction**; both are attribution artifacts.

### 2024 Ben's Gods W7 (5-game) vs W9 (4-game)

Cross-week check says: Ben's Gods had claims of 5-game win streak in W7
and 4-game win streak in W9, which is inconsistent.

Actual:
- W7 claim "five-game win streak" is about **Pat**, not Ben.
  Misattributed to Ben's Gods via HAZARD_B (substring "ben" inside
  "bench"). See F3.
- W9 claim "four-game win streak" is correctly about Ben (per F4), and
  is a model fabrication.

So the cross-week flag is built from one MISATTRIBUTION + one
LEGITIMATE_CATCH. The two claims are not genuinely about the same
franchise in the prose. **This is not a cross-recap state-leak pattern —
it's an artifact of the underlying per-week MISATTRIBUTION in W7.** Once
Brief #1 (widened) resolves F3, this cross-week flag disappears.

### 2025 Weichert's Warmongers W16 (5-game and 3-game, same week)

Cross-week check says: two distinct win-streak count claims for Warmongers
in the same week — 5 and 3.

Actual:
- 5-game claim is "extending his five-game win streak" referring to **KP**
  (owner of a different franchise).
- 3-game claim is "Steve's three-game win streak carries the 9-5
  Warmongers" correctly attributed to Warmongers.

The 5-game claim is misattributed to Warmongers because "kp" is not in
reverse_name_map (same uniqueness-collision mechanism as "steve" — to be
confirmed by the owner-alias diagnostic). Pass-1 on "five-game" finds
nothing before the match; pass-2 after-match finds "warmongers" in the
subsequent sentence and attributes there. The 3-game claim then
attributes to Warmongers as well (also via pass-2 to "warmongers"
post-match, per the harness trace). Two nominal claims about Warmongers,
one fabricated count, one correct count, both landing on the same
franchise via the same fragile pass-2 mechanism.

**Not a model self-contradiction — it's verifier-side attribution
bleed-through from pass-2.**

**Joint finding for both flags:** of the two cross-week consistency
artifacts surfaced in this scan, neither is a genuine model self-
contradiction warranting model-side intervention. Both evaporate once the
relevant per-week attribution defects are resolved (HAZARD_A/B for F3;
owner-alias uniqueness diagnostic for F6's pass-2 bleed-through).

This weakens the case that `verify_cross_week_consistency` catches
meaningful defects on this corpus. On a larger corpus it may catch real
model contradictions, but on the 2024–2025 PFL Buddies approved corpus,
the two flags it produces are both downstream of MISATTRIBUTION. Worth
tracking as an observation about the cross-week check's signal-to-noise
ratio; not a call to retire it.

---

## Blast-radius update for follow-up briefs

### Brief #1 — `_POSSESSIVE_OBJECT_WIN_STREAK` (re-scoping required)

**Pre-memo scope:** parallel of `_POSSESSIVE_OBJECT_STREAK`, matching
`<Proper Noun Possessor>'s [N-game]? (winning|win) streak`.

**Required scope widening:** add a verbal-construction sub-pattern for
"subject + (has/have/contraction) + (now)? + won + N +
straight/consecutive/in a row". Structurally distinct from the
possessive-of-noun form — the subject of the verb, not the possessor of
a noun, is the streak owner. The existing `_STREAK_PATTERN` group 2
captures the "won N straight" form; the attribution path for it needs
a symmetric possessor/subject resolver.

**Reproduction counts:**
- 04-19 `prompt_audit`: 1 (row 41 match[0])
- Approved corpus (this pass): 3 of 3 MISATTRIBUTION entries (F1, F2, F3)
- **Combined:** 4 reproductions across both corpora

**Coverage by sub-pattern:**
- Sub-pattern A (possessive-of-noun): F1, F3, + 04-19 row 41 = 3 of 4
- Sub-pattern B (subject-of-verb): F2 = 1 of 4

**Expected resolution once implemented:**
- F1 → silent pass or correct attribution (Michele → Italian Cavallini)
- F2 → silent pass or correct attribution (Michele → Italian Cavallini)
- F3 → silent pass via unmappable-possessor silence if "pat" is not in
  reverse_name_map, OR correct attribution to Pat's franchise if "pat" is
  mapped. Either outcome eliminates the MISATTRIBUTION against Ben's Gods.

### Brief #2 — proximity substring hardening (defense-in-depth)

**Scope:** replace `rfind(name)` / `find(name)` in `_find_nearby_franchise`
with word-boundary regex matching, so `ben` doesn't hit inside `bench`.

**Reproduction counts:**
- 04-19 `prompt_audit`: 1 (row 9)
- Approved corpus: 1 (F3, as compound hazard)
- **Combined:** 2 reproductions

**Dependency note:** if Brief #1 (widened) ships first, F3 is resolved
via the possessor path and Brief #2 is not strictly required to close any
known approved-corpus failure. Brief #2 remains valuable against future
unknown prose where the possessor path is absent and proximity is the
only attribution route, but its near-term urgency is reduced.

### New brief candidate — owner-alias uniqueness diagnostic

**Surfaced by:** F6 (pass-2 attribution on "warmongers" because "steve"
isn't a reverse_name_map key) and F3 (pass-1 attribution on "ben"
substring because "pat" appears to be missing from the map).

**Scope:** one-pass diagnostic dump of reverse_name_map for the PFL
Buddies 2024 and 2025 seasons to confirm whether `steve`, `kp`, and `pat`
are dropped due to uniqueness collisions in pass-2/pass-4 aliasing. If
yes, the aliasing algorithm is over-strict on this league's owner-name
distribution, and passes 2/4 could safely use franchise_id disambiguation
at match time (via context signals) rather than dropping the alias
outright at build time.

**Blast radius:** unknown; this is a diagnostic, not a fix. Could produce
a follow-up code change or a config note.

**Discipline:** separate pass. Do NOT bundle with Brief #1 or Brief #2.

---

## Out of scope

This session did NOT:

- propose or implement any verifier code changes
- dump `reverse_name_map` for 2024/2025 to confirm the
  "steve"/"kp"/"pat" uniqueness hypothesis (flagged as a new brief
  candidate above)
- confirm that "Pat's" in F3 belongs to Purple Haze vs another franchise
- trace whether the model's W7 "Pat's five-game" is itself a correct
  claim about Pat's actual streak (F3 classifies as misattribution from
  Ben's Gods's perspective; whether Pat's team actually had a 5-game
  streak entering W7 is a separate check)
- modify `franchise_directory.owner_name`
- run a ruff pass on `Tests/`
- write the widened Brief #1, Brief #2, or the new owner-alias diagnostic
  brief
- touch the four untracked diagnostic scripts under `scripts/`

All such work is captured as separate backlog items.
