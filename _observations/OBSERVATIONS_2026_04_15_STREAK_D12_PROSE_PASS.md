# OBSERVATIONS 2026-04-15 — STREAK Voice, D12 Prose, and Adjacent Findings

**Phase:** 10 — Operational Observation
**Predecessor:** session brief at 7d4cbc6 (successor to b5af302)
**Working tree:** `/Users/steve/projects/squadvault-ingest-fresh`
**Production database:** `.local_squadvault.sqlite`
**Output:** observation only — no code changes proposed in this session

---

## TL;DR

A two-week prose-reading pass intended to evaluate three narrow questions
(STREAK voice post-b5af302, D12 prose post-7d4cbc6, negative-space
regressions) instead surfaced seven findings, only one of which addressed
the original questions cleanly. STREAK voice reads correct in the prose
examined. D12 cannot be evaluated in either week because the angle is not
reaching the audit-captured prompt under any 2025 condition observed.
The remaining five findings are independent of the original scope: two
new verifier false-positive families on W10, one cross-franchise
misattribution on W14, one "plausible-narrative" fabrication on W14, one
process gap (the prompt audit captures only one of the seven prompt
blocks the model receives), and one regen-lifecycle audit-write gap
(the regens this session wrote no audit rows because of an env-var
misconfiguration, meaning the prose read was from yesterday's
generations rather than today's).

---

## Method

Two weeks regenerated under the post-b5af302 / post-7d4cbc6 code, prose
read alongside `prompt_audit`-captured `narrative_angles_text`:

- **2025 W10** — chosen for STREAK density (mid-season, multiple losing
  streaks), no D12 fires expected from the threshold sweep
- **2025 W14** — chosen for STREAK + dual-side D12 (Gibbs vs Ben's Gods
  and Stafford vs Weichert's, both above threshold=25 with this-week
  ≈ prior-avg)

A third week (W18, McCaffrey D12 with the nuanced "this below prior"
shape) was scoped but not run after W14 made clear that D12 was not
visible in audit-captured prompts and that other findings warranted
documentation priority.

For each week:

1. Regenerate via `scripts/py scripts/recap_artifact_regenerate.py`.
2. Pull `prompt_audit` rows for the week, all attempts, with full
   `narrative_angles_text`, `narrative_draft`, `verification_result_json`.
3. Read prose against angles, classify observations as MODEL_SIDE,
   VERIFIER_SIDE, or AMBIGUOUS.
4. Where the prose contained a specific claim absent from the visible
   angles (Watson FAAB), trace through `memory_events` and the prompt
   assembly code to determine what the model actually received.

Mid-session it was discovered (see Finding 9 below) that this session's
regens silently wrote zero audit rows — both W10 and W14 reads operated
on `prompt_audit` rows from yesterday's generations (2026-04-14T10:06
and 2026-04-14T10:09). All findings other than Finding 7 (STREAK voice)
are properties of the prose+verifier+prompt-pipeline that hold regardless
of which generation produced the rows. Finding 7's framing has been
adjusted accordingly.

---

## Findings

Listed in order of significance to future code work, not in order of
session discovery.

### Finding 1 (significant) — D12 PLAYER_VS_OPPONENT not present in audit-captured prompts

**Original question (Q2 from the brief):** "When PLAYER_VS_OPPONENT now
fires (~7 weeks per season), does the new headline framing produce a
usable callback in the prose?"

**Result:** Cannot be answered. The angle is absent from the
audit-captured prompts in both weeks read.

**Evidence:**

- W14: D12 sweep (`scripts/diagnose_d12_threshold_sweep.py`) shows two
  D12 fires at the production config (threshold=25, min_meetings=2,
  mode=all): Gibbs (Weichert's vs Ben's Gods, this 33.50 / prior n=2
  avg=33.35) and Stafford (Ben's Gods vs Weichert's, this 32.05 /
  prior avg=32.75).
- The W14 `narrative_angles_text` (2,040 chars) contains zero
  references to `PLAYER_VS_OPPONENT`, "vs Ben", "vs Weichert", "Gibbs",
  or "Stafford" outside the prose itself.
- The full `angles_summary_json` (6,690 chars, 3.3× larger than the
  rendered audit text) also contains zero references to player_id 15789
  (Watson, used as a comparison probe) or the D12 candidates by name.
- The visible audit footer reads `(+ 109 minor angles omitted)` —
  meaning angles are generated but not surfaced.

**Caveat from Finding 9:** the audit rows examined are from 2026-04-14
generations, not from this session's regens. It is *possible* — though
unlikely without an intervening code change between yesterday and today
— that today's code path now produces D12 angles. Resolving this
requires re-regenerating with audit enabled (now possible after the
Finding 9 operator fix).

**Two distinct hypotheses, both consistent with the evidence:**

- H1: D12 fires in the sweep but not in production. The detector runs
  additional gates (data depth, franchise tenure, lineup-status checks,
  opponent-mapping edge cases) the sweep doesn't model.
- H2: D12 fires in production but is filtered/budgeted out before
  prompt assembly. The "(+ 109 minor angles omitted)" line covers MINOR
  angles that exist in `angles_summary_json` but get dropped by the
  budget gate (per b5af302 / 0fadb16: coverage-aware,
  category-diverse MINOR fill).

The two hypotheses imply different fix surfaces. H1 → detector. H2 →
budget gate. Empirical separation is the next required step before
any code change.

**Suggested follow-up:**

- Re-regenerate W10 and W14 with audit enabled (now confirmed
  propagating after Finding 9 fix) and re-confirm D12 absence from
  fresh audit rows.
- Add `--verbose` or per-week breakdown to
  `scripts/verify_player_trend_detectors.py` so it prints which weeks
  produced D12 fires under production code paths, not just sweep
  config tuples.
- If production fires exist for W10 or W14, inspect
  `angles_summary_json` for those weeks for D12 entries, and inspect
  `budgeted_summary_json` to see whether the budget kept or dropped them.
- This is a precondition for any further D12 prose-quality work. The
  reframe from b5af302 cannot be evaluated when the angles aren't
  reaching the model.

---

### Finding 2 (significant) — `prompt_audit` captures only one of seven prompt blocks

**Discovery path:** investigating why a Watson FAAB claim in W14 prose
had no Watson reference anywhere in the audit-captured fields (Finding 4
below).

**Evidence:** `_build_user_prompt` in `src/squadvault/ai/creative_layer_v1.py`
(lines 225–322) assembles the user-turn prompt from up to eight blocks:

1. Header (league/season/week/EAL)
2. SEASON CONTEXT (standings, streaks, scoring)
3. LEAGUE HISTORY (all-time records, cross-season)
4. NARRATIVE ANGLES (detected story hooks)
5. WRITER ROOM (scoring deltas, FAAB spending)
6. PLAYER HIGHLIGHTS (individual player performances)
7. VERIFIED FACTS (canonical, authoritative)
8. VERIFICATION CORRECTIONS (only on retry)

`prompt_audit` schema captures `narrative_angles_text`,
`angles_summary_json`, `budgeted_summary_json`. These three fields all
trace to block 4 only. Blocks 2, 3, 5, 6, 7, and 8 reach the model
but are not persisted.

**Why this matters:** the diagnostic-first principle ("read the prose,
determine model-side vs verifier-side before writing code") is
systematically incomplete for any finding whose evidence trail does
not run through NARRATIVE ANGLES. Watson is the proving case — the
"$20 FAAB pickup" detail is real and almost certainly delivered via
WRITER ROOM, but the entire diagnostic path through `prompt_audit`
read as a clean fabrication for two query rounds before the prompt
assembly code was inspected. The diagnostic time cost was substantial.

**Suggested follow-up:** add a `prompt_text` column to `prompt_audit`
that stores the full assembled `user_prompt` returned by
`_build_user_prompt`. This is an append-only addition consistent with
the constitution's facts-immutable principle. Cost: one schema
migration, one capture-site write, no retroactive backfill required.
Benefit: every future Watson-shaped finding becomes inspectable without
code archaeology or re-running with print statements.

This is a process-layer fix, not a model-layer or verifier-layer fix.
It does not alter what reaches the model, only what is observable about
what reached the model.

---

### Finding 3 (significant) — New verifier false-positive families on W10

**Original question (Q3 from the brief):** "Are there visible quality
regressions? New fabrication patterns?"

**Result:** Three of the four hard_failures across W10 attempts 1 and 2
read as verifier false positives, not model fabrications. The retry
loop ran three attempts (rows 17, 18, 19) and the third passed without
any model improvement on the rejected substance — the third draft
stochastically dodged the buggy parse rather than addressing it. The
fourth hard_failure is ambiguous from the evidence string alone and
needs a canonical-data lookup.

**Evidence:**

| Row | Attempt | Category | Verifier claim | Prose context | Classification |
|-----|---------|----------|----------------|---------------|---------------|
| 17 | 1 | SUPERLATIVE | "Season high of 103.10" | "...in their 137.50-103.10 win over Italian Cavallini" | VERIFIER_SIDE — matchup-line losing-team score conflated with season-superlative |
| 17 | 1 | SUPERLATIVE | "Season low of 90.10" | "Brandon managed just 90.10 total — his second-lowest score of the season" | AMBIGUOUS — claim is franchise-scoped, evidence cites league-low (76.05) without scope-matching |
| 17 | 1 | SERIES | "Series record 8-2 (Paradis vs Italian Cavallini)" | "KP's team moved to 8-2 and maintains the league's best record" | VERIFIER_SIDE — overall season W-L conflated with H2H series |
| 18 | 2 | SERIES | "Series record 7-3 (Eddie vs Miller)" | "Josh Allen's 26.40 points led Miller to his second straight win and a 7-3 record" | VERIFIER_SIDE — same pattern as row 17 |

**Two new patterns surface, structurally similar to the V1–V6 family
documented in `OBSERVATIONS_2026_04_14_SUPERLATIVE_WIDER_PASS.md`:**

- **FP-SUPERLATIVE-MATCHUP-LINE:** the verifier matches a number that
  appears in a matchup-line score format (`A.AA-B.BB`) against a
  season-superlative when "season" appears elsewhere in the same
  paragraph. The number was not the model's superlative claim; it was
  the losing team's score in a matchup line. Distinct from V1–V6 in
  that the parse trigger is matchup proximity, not previous-vs-current
  or all-time framing.
- **FP-SERIES-OVERALL-RECORD:** the verifier matches W-L records like
  "8-2" and "7-3" against H2H series records when the W-L appears in
  proximity to a franchise pair the matchup describes. The W-L was
  the overall-season standing, not a series claim. The V1–V6 work was
  scoped to SUPERLATIVE; SERIES parse patterns are out of scope for
  that work and unaddressed.

**Cross-reference to prior work:** row 17 is the same physical row as
the row 17 in `OBSERVATIONS_2026_04_14_SUPERLATIVE_WIDER_PASS.md` —
confirmed via `captured_at` timestamp lookup. The
"ambiguous-pending-retest" classification for row 17 a1 / 103.10 in
that doc resolves here as VERIFIER_SIDE under the new
FP-SUPERLATIVE-MATCHUP-LINE pattern.

**Operational consequence:** retry loop costs are non-zero (three
attempts on W10) and one source of those costs is verifier
calibration, not model behavior. Same observation as the wider-pass
doc, generalized to a different category (SERIES) and a different
pattern within SUPERLATIVE.

**Suggested follow-up:** add the two new FP patterns to the V1–V6
backlog. Both are reproducible from prose alone. Whether to fix in
this session or defer is a separate decision; the evidence here is
just classification.

---

### Finding 4 (significant) — Cross-franchise misattribution on W14

**Discovery path:** the W14 prose contains *"Christian Watson added 23
in his first week since a $20 FAAB pickup"* in the paragraph about
Paradis' Playmakers blowing out Brandon Knows Ball.

**Tracing the data:**

- Christian Watson is `player_id=15789` (WR, GBP).
- `memory_events` shows a real $20.45 FAAB pickup of Watson by franchise
  0002 (Steve's Warmongers) on 2025-11-20, three weeks before W14.
- W14 weekly score: Watson scored 22.90 starting for franchise 0002.
- W14 prose attributes Watson's points to franchise 0008 (Paradis'
  Playmakers / KP), in the same paragraph as the Brandon blowout.

**Classification:** MODEL_SIDE attribution error. The dollar amount
($20) is real. The score (23 ≈ 22.90 rounded) is real. The franchise
attribution is wrong by one team. The model knew the FAAB pickup
detail (presumably from the WRITER ROOM block; see Finding 2) and
inserted it into the wrong matchup paragraph.

**Why this matters:** this is the same shape as the historical
Eddie/Eddie-&-the-Cruisers short-form misattribution pattern, but
inverted in direction. There the verifier caught an attribution error
because it traced through franchise short-forms. Here the verifier did
not catch the error because FAAB attribution is not in the verifier's
check set. The error reaches review-required state.

**Trust impact:** higher than verifier FPs. A reader who knows their
own roster will see "Watson scored 23 for KP" and immediately know
this is wrong. Verifier FPs delay generation but produce correct prose
on retry; misattributions produce confidently wrong prose that passes
verification cleanly.

**Suggested follow-up:**

- Add a verifier check category for player-franchise-week consistency:
  every named player score in prose should match the canonical
  `WEEKLY_PLAYER_SCORE` row for that player + week + franchise.
- This is a substantive new check, not a parse-pattern adjustment.
  Scoping belongs to a separate session.

---

### Finding 5 (significant) — "First week since" fabricated on W14

**Same prose, same trace path as Finding 4.** The model wrote *"his
first week since a $20 FAAB pickup."* Watson's actual W14 was the
**third** week with franchise 0002 — he scored 7.40 in W12 (nonstarter),
16.30 in W13 (nonstarter), and 22.90 in W14 (starter, first start).

**Classification:** MODEL_SIDE plausible-narrative fabrication. Two
charitable readings:

- The WRITER ROOM block lists the FAAB pickup but not the per-week
  appearance history, and the model invented "first week since" as
  plausible-sounding narrative filler.
- The WRITER ROOM block lists "first start since pickup" and the model
  paraphrased to "first week" — losing the start/non-start distinction
  but making a structurally similar claim.

We cannot distinguish these readings without seeing the actual WRITER
ROOM text the model received (see Finding 2). Either reading classifies
as MODEL_SIDE; the difference is whether the framing was supplied or
invented.

**Why this matters:** "first week since" is a class of claim the
model produces frequently in narrative prose (any time-since-event
pattern). If the WRITER ROOM block does not pre-render these claims,
the model will fill them in plausibly, and they will sometimes be
wrong. Same coverage gap as Finding 4 from a different angle.

**Suggested follow-up:** intentionally orthogonal to Finding 4 even
though they share a prose target. Finding 4 is a player-franchise
attribution check. Finding 5 is a temporal-claim check ("first
since X", "Nth straight Y") and requires either a verifier category
that handles ordinal/temporal claims against canonical event history,
or upstream pre-rendering in the WRITER ROOM block to remove the
opportunity for fabrication. The latter is more aligned with the
documented principle "withhold data the model cannot use correctly,
provide pre-derived conclusions where possible."

---

### Finding 6 (significant) — FAAB_TRANSACTION verifier coverage gap

**Restated from earlier in the session.** The verifier's six check
categories (SCORE, SUPERLATIVE, STREAK, SERIES, BANNED_PHRASE,
PLAYER_SCORE) do not include any check on FAAB transaction claims.
A model claim like "$20 FAAB pickup" is not validated against the
canonical `WAIVER_BID_AWARDED` / `TRANSACTION_BBID_WAIVER` event
history.

**Independent of Findings 4 and 5.** Even if attribution and temporal
claims were correct, FAAB dollar amounts could still be fabricated and
pass verification. In W14 the dollar amount happened to be real, but
the absence of a check means a future regeneration could invent
"$45 FAAB pickup" with equal confidence and cleanliness.

**Suggested follow-up:** scope a FAAB_TRANSACTION verifier category.
Lower priority than Findings 4 and 5 because the model has been
observed using real FAAB amounts in this single sample — but the
absence of any guard means trust depends on data delivery integrity,
which Finding 2 has shown to be incompletely auditable.

---

### Finding 7 (provisional positive) — STREAK voice reads correct in the prose examined

**Original question (Q1 from the brief):** "When the model encounters
a losing-streak team this week, does it now naturally write 'extended'
or describe the streak continuing — or does it still reach for
'snapped' framing?"

**Result:** all observed STREAK callouts across both weeks use the
correct framing. No instance of inappropriate "snapped" reach.

**Important framing caveat:** the W10 and W14 audit rows examined are
from 2026-04-14 generations, not from this session's regens (see
Finding 9). The b5af302 commit landed prior to those generations, so
the prose is post-fix code, but the framing should be "STREAK voice
was clean in the W10 and W14 prose examined" rather than "STREAK voice
is clean post-b5af302 because of this session's regen evidence."

**Evidence (W10):**

- *"extending Brandon's losing streak to 10 games and keeping him
  winless through Week 10"* — losing streak, "extending" used
- *"Steve's Warmongers stayed hot with their third straight win"* —
  winning streak, "third straight" framing
- *"snapped his win streak"* (referring to Pat losing) — correctly used
  on a winning streak that was actually broken

**Evidence (W14):**

- *"KP extended his win streak to five games"* — "extended" on win
- *"Steve's Warmongers rolled to their third straight win"*
- *"Miller extended his own win streak to two games"*
- *"ending Eddie's hopes with his third straight loss"* — losing streak,
  "third straight" framing, no inappropriate "snapped"
- *"extended their streaks of sub-8-point performances to four straight
  starts each"* — player-level streak callouts also clean

**Caveat:** W14 attempt 2 contains *"extended his losing streak to
one"* about Ben after his only-recent loss. Grammatically fine,
semantically odd — a "streak of one" is a stretch of the word. Probably
an artifact of the explicit annotation language being applied to a
1-game situation. Worth watching, not actionable from a single
instance.

**Sample size:** two weeks is small for declaring a pattern; the
provisional positive should be revisited once Finding 9 is fixed and
fresh post-7d4cbc6 audit rows accumulate.

---

### Finding 8 (process observation) — silent fallback on missing API key

**Discovery path:** initial W14 regen ran in a fresh shell where
`ANTHROPIC_API_KEY` had not been propagated. The lifecycle did not
error; it produced a deterministic facts-only fallback and committed
v20 with `verification_attempts: 1`, `verification_result: null`. The
v20 was a quality regression compared to v18 (which was a real
model-generated draft) but the regen JSON output gave no obvious
indication this had happened.

Recovery required a re-regen after propagating the API key. v21
became the actual evaluation target.

**Suggested follow-up:**

- Fail loudly when API key is missing on regen invocation (rather
  than fall back). Regen is an explicit human-initiated action where
  silent degradation surprises.
- Consider refusing to commit a facts-only fallback as a *new*
  approved version when the prior version was a model-generated
  narrative — avoids accidental quality regression.
- At minimum, surface in the regen JSON output that fallback was used.

This pairs with Finding 9 below as a class concern about silent
side-effect skipping in the regen lifecycle. The principle "silence is
preferred over speculation" is about model output, not operational
state changes; silent quality regression and silent audit-write
skipping conflate the two.

---

### Finding 9 (significant) — Regen lifecycle silently skips `prompt_audit` write when env var unset

**Discovery path:** late-session sanity check on `prompt_audit` row
timestamps revealed that this session's W10 and W14 regens wrote zero
audit rows. Both reads operated on rows from 2026-04-14T10:06 (W10)
and 2026-04-14T10:09 (W14) — yesterday's generations.

**Root cause traced:**

- `prompt_audit_v1.py` line 195: gate is strict
  `os.environ.get(AUDIT_ENV_VAR) != "1"`. Anything other than the exact
  string `"1"` is a no-op.
- `AUDIT_ENV_VAR = "SQUADVAULT_PROMPT_AUDIT"` (line 40).
- `.env.local` did not contain `SQUADVAULT_PROMPT_AUDIT` (verified via
  `grep -i "audit" .env.local` → no match).
- The session brief stated `"SQUADVAULT_PROMPT_AUDIT=1 on regens by
  default"` — this turns out to be incorrect. There is no default in
  `.env.local`, and the lifecycle does not set it.

**Operator-side fix applied this session:**

```
echo "SQUADVAULT_PROMPT_AUDIT=1" >> .env.local
```

After `set -a; source .env.local; set +a`, `${SQUADVAULT_PROMPT_AUDIT}`
propagates as `1` and the gate passes. Verified.

**Operational consequence (retrospective):** any regen invoked from a
fresh shell that sources only `.env.local` since whenever
`SQUADVAULT_PROMPT_AUDIT` was last present in the environment
(unknown — possibly never in `.env.local`) has produced no audit row.
The artifact and verification-result side of the lifecycle worked
normally; only the audit row was skipped. This means `prompt_audit`
is not a complete record of all regens, and any analysis based on
`prompt_audit` row counts (e.g., "how many drafts have been generated
this season") undercounts by an unknown factor.

**Code-side question for backlog:** the strict `== "1"` gate is
defensible (avoids ambiguous truthy values), but the silent no-op
on regen specifically is a design choice worth revisiting. Regen is
an explicit human-initiated diagnostic action; the failure mode of
"diagnostic that produces no diagnostic record" is the worst possible
combination. Two options worth scoping:

- **Override on regen:** `scripts/recap_artifact_regenerate.py` sets
  `SQUADVAULT_PROMPT_AUDIT=1` in its own process environment before
  invoking the lifecycle. Audit write becomes unconditional on regen.
- **Surface the skip:** regen JSON output includes an
  `audit_captured: bool` field reflecting whether the gate passed.
  Operator notices immediately when the value is False.

Either reduces the chance of a future session quietly reading
yesterday's data while believing it is today's.

**Pairs with Finding 8:** both are silent side-effect skips in the
regen lifecycle. Finding 8 is silent fallback to facts-only on missing
API key. Finding 9 is silent audit-write skip on missing env var.
Together they suggest the regen lifecycle has a class issue with
silent operational skips that are easily mistaken for normal
operation.

---

## Implications for backlog and future sessions

**Originating question status:**

- Q1 (STREAK voice): partially answered. Voice is clean in the prose
  examined, with the framing caveat from Finding 9. Re-confirm once
  fresh post-fix audit rows accumulate.
- Q2 (D12 prose): unanswerable until D12 reaches the audit-captured
  prompt. Finding 1 takes priority over the original prose-quality
  question.
- Q3 (negative space): answered with five new findings, none of which
  were in the original scope.

**Backlog deltas:**

- New: D12 production firing rate verification (Finding 1)
- New: `prompt_audit` schema extension to capture full assembled prompt
  (Finding 2)
- New: FP-SUPERLATIVE-MATCHUP-LINE and FP-SERIES-OVERALL-RECORD verifier
  patterns (Finding 3)
- New: player-franchise-week consistency verifier check (Finding 4)
- New: temporal-claim verifier check or upstream pre-rendering for
  "first since" framings (Finding 5)
- New: FAAB_TRANSACTION verifier check (Finding 6)
- New: lifecycle behavior on missing API key (Finding 8)
- New: regen lifecycle audit-write override and/or skip surfacing
  (Finding 9)
- Carry-forward: rows 7/20/25/54 historical STREAK fabrications —
  unaffected
- Carry-forward: D12 PLAYER_VS_OPPONENT firing rate verification —
  now subsumed under Finding 1

**Priority observation:** Findings 9 and 2 together are the
highest-leverage items. Finding 9 is now operator-fixed for this
machine but the code-side options remain backlog and should be scoped
before another session relies on `prompt_audit`. Finding 2 reduces the
time cost of every future diagnostic session. Finding 4 closes a
coverage gap that produces confidently-wrong prose passing
verification — the worst combination from a trust-impact perspective.
Findings 3 and 6 are calibration / coverage extensions, lower priority
but cleaner to scope.

---

## What is not done in this session

- No code changes. All findings are observations and scoped backlog
  items. The Finding 9 fix was an operator-side `.env.local` edit, not
  a code change.
- No re-regen of W10 or W14 with audit now enabled. Worth doing as a
  short follow-up to confirm Finding 1 holds against fresh audit rows.
- No third-week (W18) regen or read. Subsumed by Finding 1.
- No FAAB_TRANSACTION verifier check scoping. Backlog only.
- No prompt_audit schema migration. Backlog only.
- No regression fixture drafting for FP-SUPERLATIVE-MATCHUP-LINE or
  FP-SERIES-OVERALL-RECORD. That belongs to the verifier-fix session
  that addresses them.
- No code-side fix for Finding 9's gate behavior. Operator-side fix
  applied; code-side scoping deferred.

---

## Closing

The session as scoped (read prose, evaluate three narrow questions)
produced one positive answer (STREAK voice) and one structural
unknown (D12 reaching prompt). The session as it actually unfolded
produced five additional findings of higher significance than the
original scope, plus one process-side discovery (Finding 9) that
revealed the entire prose-reading exercise was operating on
yesterday's data. The diagnostic-first discipline made the
layer-classification possible — reading the prose carefully and
tracing each suspect claim to its underlying source data
distinguished verifier FPs from model fabrications, surfaced the
prompt-audit gap as a process problem rather than a model problem,
and ultimately surfaced Finding 9's silent audit-write skip when row
timestamps were checked.

The most operationally useful next move is not addressing any single
finding, but addressing Finding 2 first so subsequent findings can
be diagnosed against the actual prompt the model received. With
Finding 9's operator fix already applied, fresh regens will now write
audit rows; a Finding 2 schema extension would make those rows
diagnostically complete.
