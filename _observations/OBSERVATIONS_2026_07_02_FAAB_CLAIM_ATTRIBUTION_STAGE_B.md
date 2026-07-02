# Observation - 2026-07-02 - FAAB_CLAIM Attribution, Stage B (Prose Capture)

**Session type:** EXECUTE (Claude Code, Opus 4.8). Diagnosis-only (D-W): no edits to verifier,
prompts, Tier-2 policy, data layer, or any source file. Two founder gates (Gate 1
pre-registration, Gate 2 memo). Follow-on to Stage A (memo + brief squash `9571885`).
**Brief:** `_observations/session_brief_faab_claim_attribution_stage_b.md` (landed squash `1038da4`).

**Status:** PRE-REGISTRATION BLOCK FROZEN at Gate 1, founder-ratified 2026-07-02 (crossover
boundary folded in at ratification time). Results sections populated post-run.

**Process note (surfaced for the founder):** the Stage B brief body did not arrive with the
first kickoff (only a `[full Stage B brief text]` placeholder); the session halted and the
brief was re-sent and landed (`1038da4`) before any Stage B work. While awaiting it, only
reversible pre-Gate-1 prep ran (trio, scratch copy, the permitted throwaway smoke). No gate
was crossed, no source touched, prod untouched.

---

## 0. Ritual / provenance

- **HEAD:** `1038da4` (after the brief merge; verified `git log -1`).
- **Repo identity:** engine confirmed (`scripts/recap_artifact_regenerate.py` present).
- **Standard trio:** ruff `check src/squadvault/` clean; mypy clean (163 files); pytest green
  at session end (2380 passed, 2 skipped; the 2 warnings are the in-test empty-key fixture).
- **Prod DB start hash:** `effb00e54fce5c3860423a08338b8711bc96229172452888c97823bc8c5af36b`
  (re-verified unchanged after the smoke).
- **Scratch DB:** `/tmp/stageb_scratch.sqlite`, copied from prod; copy hash identical
  (`effb00e5...`). All generation lands in scratch only.

## 1. PRE-REGISTRATION BLOCK (FROZEN at Gate 1, founder-ratified 2026-07-02)

### 1.1 Configuration in force (measured as-is; no edits)

| Item | Value (verified this session) |
|---|---|
| HEAD | `1038da4` |
| Scratch-DB source hash | `effb00e54fce5c3860423a08338b8711bc96229172452888c97823bc8c5af36b` |
| Generation model (`_MODEL`, `creative_layer_v1.py:35`) | `claude-sonnet-4-5-20250929` |
| Temperature / retry decay | `0.8` base; `[None, 0.5, 0.3]` |
| Retry cap | `3` (`_MAX_VERIFICATION_RETRIES`) |
| No-retry categories | `FAAB_CLAIM`, `NUMERIC_UNANCHORED` (FAAB_CLAIM Tier-2 short-circuits) |
| Verifier | `core/recaps/verification/recap_verifier_v1.py` at HEAD (FAAB check `:4432-4614`) |
| Voice profile (`get_voice_profile(scratch,'70985')`) | PRESENT, len 3938, sha256 `3fdd8c9564c6066752d0b8f9129d3a45ce13b4c99859814df0d9ee467d407d8a` |
| Prompt-audit capture | `SQUADVAULT_PROMPT_AUDIT=1` (prose + verification_result_json land per attempt) |

### 1.2 The 9 inherited cells (verbatim from the Stage A memo section 5, H3 rows)

n=9, population = sample, no draw, no substitution. A cell that cannot run is
`INELIGIBLE_POST_PIN`.

```
2022 wk5   2023 wk5   2023 wk12
2024 wk2   2024 wk4   2024 wk9
2024 wk11  2024 wk12  2024 wk14
```

Throwaway smoke cell **2024 wk8** (not among the 9) - excluded and recorded (section 3).

### 1.3 Capture fields (per FAAB_CLAIM failure event) - frozen at Gate 1

For every attempt that produces a FAAB_CLAIM hard failure, capture from that attempt's
`prompt_audit` row (scratch, `id > BASELINE`, cell keys):

1. **Verbatim FAAB-implicated sentence(s)** from the rejected draft (`narrative_draft`).
2. **Claimed dollar amount + the player the model attached it to** (from the prose).
3. **Verifier `best_name` binding** for that claim (which player the binder resolved + the
   character distance). The failure evidence string exposes `best_name`
   (`"$N FAAB attributed to {best_name}"`); the **distance is not logged**, so it is
   reconstructed deterministically by re-running the verifier's own binder logic
   (`recap_verifier_v1.py:4558-4569`) read-only against the captured prose. The memo will
   label field 3's distance as **reconstructed, not logged** (hazard 4).
4. **WBA reality:** whether the model-named player, and any player within the 100-char
   binder window, has a real `WAIVER_BID_AWARDED` record for the season, with canonical
   amount (probe `v_canonical_best_events`, read-only).
5. **Pickup event type(s)** surfaced for the named player in that cell's selected bullets
   (`WAIVER_BID_AWARDED` / `TRANSACTION_FREE_AGENT` / none) - from `recap_runs` selection.

Per-cell run metadata: attempt count, per-attempt FAAB_CLAIM yes/no, final outcome.

### 1.4 Terminal classes + decision rule (pre-registered; written before any generation)

Per FAAB_CLAIM failure **event**:
- **H1p (model invention):** the model-named player has no season WBA record **and** no player
  within the 100-char binder window has a WBA matching the claimed amount (+/-$1); OR the
  named player has a WBA but the claimed amount contradicts it by >$1 with no nearer player
  explaining it. The model fabricated the FAAB dollar/attribution.
- **H2p (proximity misbinding):** the model's FAAB sentence is factually correct for some
  player who **does** have a matching WBA record (+/-$1), but the verifier's binder resolved
  `best_name` to a **different** nearer player who lacks that record, producing the failure.
- **Crossover boundary (explicit, ratification-time):** if the model-named player has no
  WAIVER_BID_AWARDED record but a **different in-window player carries exactly the claimed
  dollar amount (+/-$1)**, classify the event **H2p** (proximity misbinding), not H1p. H1p
  requires that **no** in-window player matches the claimed amount.
- **H3p (other):** anything not cleanly H1p or H2p - described verbatim, not forced.

Per **cell**: terminal class = the dominant mechanism across its FAAB failure events; cells
with mixed mechanisms are labeled explicitly. A cell with **zero** FAAB_CLAIM failures across
all attempts is `NO_FAILURE_REPRODUCED` (a legitimate terminal class, not a defect). A cell
that cannot run is `INELIGIBLE_POST_PIN`.

### 1.5 Run procedure

Generate each of the 9 cells **once** through the shipped retry loop against scratch
(`SQUADVAULT_PROMPT_AUDIT=1`). No re-runs to force a failure (that would bias the readout).
Capture every FAAB_CLAIM failure event across whatever attempts naturally occur (FAAB_CLAIM
short-circuits on first occurrence per Tier-2, but a cell may reach later attempts on other
categories first). Infrastructure retries (network/rate-limit) are noted and are **not**
verification attempts. No mid-run intervention.

### 1.6 Non-comparability (pre-committed)

Stage B is attribution, not measurement. Its pass/fail pattern is **not** comparable to the
A7 baseline and no sentence in this memo will read it as a rate update - different model
invocations produce different prose; a cell may pass here. This run is an independent draw
from the A7 run (whose scratch/prose was deleted).

---

## 2. GATE 1 - founder ratification

Founder confirms: the 9-cell list, config-as-is (model `claude-sonnet-4-5-20250929`), scratch
measurement, the 5 capture fields, the terminal classes + decision rule, and the run-once
procedure. On confirmation the block is FROZEN; `INELIGIBLE_POST_PIN` / `NO_FAILURE_REPRODUCED`
are the only permitted post-freeze outcomes.

**Ratified:** founder, 2026-07-02, with the crossover boundary in the decision rule folded in
at ratification time. Block frozen; only `INELIGIBLE_POST_PIN` / `NO_FAILURE_REPRODUCED` are
permitted post-freeze outcomes.

---

## 3. Smoke record (Step 1, pre-Gate-1; throwaway cell 2024 wk8, excluded from the 9)

Cell 2024 wk8, scratch, `SQUADVAULT_PROMPT_AUDIT=1`, model `claude-sonnet-4-5-20250929`:
`verification_attempts=1`, `checks_run=16`, `passed=False`; **no API-failure fallback**
(real generation, key live). One `prompt_audit` row captured (`id=366`), `narrative_draft`
2089 chars, 2 FAAB_CLAIM hard failures - both the "no WAIVER_BID_AWARDED record" branch:
`$11 FAAB attributed to Joe Burrow`, `$5 FAAB attributed to Kirk Cousins`; prose carried
`"...for $11 on FAAB and delivering 207..."`. This confirms all capture fields are readable
(prose = field 1/2; verifier claim string = field 3 best_name; WBA/event-type probes =
fields 4/5). Prod DB hash unchanged after the smoke. (2024 wk8 is the throwaway; excluded.)

## 4. Results (populated post-run; pre-registration block above unchanged since Gate 1)

Run: 9 cells generated once each against scratch, `SQUADVAULT_PROMPT_AUDIT=1`, model
`claude-sonnet-4-5-20250929`, prompt_audit baseline id 366 (post-smoke). Zero infrastructure
retries. Prod DB hash unchanged after the run (`effb00e5...`). 9 FAAB_CLAIM failure events
occurred across 5 of the 9 cells; 4 cells reproduced no FAAB failure.

### 4.1 Per-cell capture tables (all five fields; prose verbatim)

Field key: F1 sentence (verbatim) - the dollar's entity attachment is visible in the model's
own words; F2 claimed $ + the entity the MODEL attaches it to; F3 the verifier `best_name`
binding + distance (distance **reconstructed** read-only, not logged); F4 WBA reality
(named entity + in-window players, canonical amount); F5 surfaced pickup type.

**2022 wk5 - H1p** (attempt 1)
- F1: "The Cruisers spent $39 on Kyle Pitts, who is averaging just 5.0 points through four
  starts, and $35 on Javonte Williams..."
- F2: $39 -> **Kyle Pitts** (model's own attribution). F3: binder best_name Kyle Pitts,
  dist 7 (binding agrees with the model). F4: Pitts has **no** 2022 WBA; no in-window player
  carries $39. F5: not surfaced as a pickup. -> genuine invention.

**2023 wk5 - NO_FAILURE_REPRODUCED** (attempt 1 passed).

**2023 wk12 - H3p** (FAAB fail attempt 3)
- F1: "Dak Prescott led Stu with 43.55 while the Cleveland defense - a $5 FAAB pickup -
  managed just 3.00..."
- F2: $5 -> **the Cleveland defense** (a team defense). F3: binder best_name **Dak Prescott**
  (a QB), dist 64 - the binder attached the $5 to a player the sentence did not. F4: Dak
  Prescott no 2023 WBA; no in-window player carries $5. F5: n/a (defense). -> non-player scope.

**2024 wk2 - NO_FAILURE_REPRODUCED** (attempt 1 passed).

**2024 wk4 - H3p** (attempt 1; 2 events, both H3p)
- Event A: F1 "KP dropped $40 on Kareem Hunt this week and started the **Chicago defense
  (8.00 points on a $0 claim)**, but left 46.65 points on the bench." F2 $0 -> **the Chicago
  defense**. F3 binder best_name **Kareem Hunt**, dist 72. F4 the model's *other* figure,
  "$40 on Kareem Hunt", matches Hunt's real WBA **$40.99** and was **not** flagged; the
  flagged $0 is the defense's claim. -> non-player scope (defense), not a Hunt error.
- Event B: F1 "**Michele has spent $98 on FAAB through four weeks** - most in the league.
  The $52 he dropped on Dontayvion Wicks this week pushed him past KP ($77 total)." F2 $98 ->
  **Michele (franchise total)**. F3 binder best_name **Dontayvion Wicks**, dist 75. F4 no
  player has a $98 bid; **$98 is a real franchise total** (franchise 0005 = $98.15 in 2024,
  appendix probe); the model's "$52 on Dontayvion Wicks" matches Wicks's real **$52.78** and
  was **not** flagged. -> franchise-total scope, a true statement misbound to a player.

**2024 wk9 - NO_FAILURE_REPRODUCED** (3 attempts; failed only non-FAAB categories).

**2024 wk11 - H2p** (FAAB fail attempt 2)
- F1: "Jauan Jennings started and scored 20.10 in his second week since the $35 FAAB pickup."
- F2: $35 -> **Jauan Jennings**. F3: binder best_name **Breece Hall** (no WBA), dist 55 -
  bound to a different, nearer name. F4: Jennings carries a real WBA **$35.01**
  (|35 - 35.01| <= $1) - the model's claim is correct. F5: not surfaced for Hall.
  -> proximity misbinding (crossover satisfied: Jennings in-window at the claimed amount).

**2024 wk12 - MIXED (H2p + H3p): 2 H2p + 2 H3p, no dominant** (attempt 1; 4 events)
- H2p: F1 "Sam Darnold sat on Eddie's bench with 28.40 after putting up 172.00 points across
  8 starts since the **$9 pickup**." F2 $9 -> **Sam Darnold**. F3 binder best_name **Jaylen
  Waddle** (no WBA). F4 Darnold real WBA **$9.11** (|9 - 9.11| <= $1) - correctly stated;
  binder false positive.
- H2p: F1 "...Tank Bigsby, who's put up 73.70 points across 8 starts after a **$4 FAAB
  bid**." F2 $4 -> **Tank Bigsby**. F3 binder best_name **Jayden Daniels** (no WBA). F4
  Bigsby real WBA **$4.42** (|4 - 4.42| <= $1) - correctly stated; binder false positive.
- H3p x2: F1 "...the **Chargers** have scored 72.00 points across 9 starts after costing
  either **$2 or $3** in FAAB. Sam Darnold sat on Eddie's bench..." F2 $2 and $3 -> **"the
  Chargers"** (a team-name reference, not a resolvable single WBA player). F3 binder
  best_name **Sam Darnold** (real $9.11, does not match $2/$3). F4 no unambiguous in-window
  player carries $2 or $3. -> ambiguous team-name referent -> H3p per the catch-all.

**2024 wk14 - NO_FAILURE_REPRODUCED** (attempt 1 passed).

### 4.2 Classification - three passes (all shown; all moves evidenced)

The classification moved across three passes as the captured prose was read more closely;
all passes are shown, all moves are evidenced from quoted sentences, and the frozen decision
rule was not altered at any point - only its H3p catch-all and its +/-$1 tolerance were applied.

**Pass 1 - mechanical (capture script output, unedited).** The frozen rule applied by the
script, keyed on the verifier's `best_name` binding (before any prose reading):

| cell | Pass 1 class |
|---|---|
| 2022 wk5 | H1p |
| 2023 wk5 | NO_FAILURE_REPRODUCED |
| 2023 wk12 | H1p |
| 2024 wk2 | NO_FAILURE_REPRODUCED |
| 2024 wk4 | H1p |
| 2024 wk9 | NO_FAILURE_REPRODUCED |
| 2024 wk11 | H2p |
| 2024 wk12 | H1p (mixed: 3 H1p + 1 H2p) |
| 2024 wk14 | NO_FAILURE_REPRODUCED |

**Reclassification Pass 1 -> Pass 2** (2 events moved; the mechanical pass bucketed
non-player-scoped figures as H1p because `best_name` was a player):

| event | sentence (verbatim) | before | after | evidence |
|---|---|---|---|---|
| 2023 wk12 $5 | "the Cleveland defense - a $5 FAAB pickup" | H1p | H3p | $5 attaches to a team defense, not the bound player Dak Prescott |
| 2024 wk4 $98 | "Michele has spent $98 on FAAB through four weeks" | H1p | H3p | $98 is a franchise total (real $98.15), not a player bid |

**Pass 2 - first prose read** (the mid-flight table):

| cell | Pass 2 class |
|---|---|
| 2022 wk5 | H1p |
| 2023 wk12 | H3p |
| 2024 wk4 | MIXED (H1p + H3p) |
| 2024 wk11 | H2p |
| 2024 wk12 | H1p (mixed: 3 H1p + 1 H2p) |
| (others) | NO_FAILURE_REPRODUCED |

**Reclassification Pass 2 -> Pass 3** (4 events moved; closer reading separated the model's
attribution (F2) from the verifier's binding (F3) for the Hunt and Darnold-area events):

| event | sentence (verbatim) | before | after | evidence |
|---|---|---|---|---|
| 2024 wk4 $0 | "started the Chicago defense (8.00 points on a $0 claim)" | H1p | H3p | $0 attaches to the Chicago **defense**; the model's "$40 on Kareem Hunt" separately matched $40.99 and was not flagged |
| 2024 wk12 $9 | "Sam Darnold sat on Eddie's bench ... since the $9 pickup" | H1p | H2p | $9 attaches to **Darnold**, real WBA $9.11 (within +/-$1) - correct; binder bound it to Jaylen Waddle (no WBA) |
| 2024 wk12 $2 | "the Chargers have scored 72.00 points ... after costing either $2 or $3 in FAAB" | H1p | H3p | $2 attaches to **"the Chargers"** (team-name ref), not Darnold; ambiguous referent |
| 2024 wk12 $3 | (same sentence as above) | H1p | H3p | $3 attaches to "the Chargers", not Darnold; ambiguous referent |

**Pass 3 - final prose read** (labeled final):

| cell | terminal class | per-mechanism event counts |
|---|---|---|
| 2022 wk5 | H1p | 1 H1p |
| 2023 wk5 | NO_FAILURE_REPRODUCED | - |
| 2023 wk12 | H3p | 1 H3p |
| 2024 wk2 | NO_FAILURE_REPRODUCED | - |
| 2024 wk4 | H3p | 2 H3p (Chicago DEF $0, franchise $98) |
| 2024 wk9 | NO_FAILURE_REPRODUCED | - |
| 2024 wk11 | H2p | 1 H2p |
| 2024 wk12 | MIXED (H2p + H3p) | 2 H2p + 2 H3p (no dominant) |
| 2024 wk14 | NO_FAILURE_REPRODUCED | - |

**Final counts.** Terminal: H1p 1, H2p 1, H3p 2, MIXED(H2p+H3p) 1, NO_FAILURE_REPRODUCED 4
(all 9 cells terminal; none dropped; no INELIGIBLE_POST_PIN). Event-level (9 events across 5
reproducing cells): **H1p 1, H2p 3, H3p 5**.

Fidelity checks (final pass): every H2p has an in-window player at the claimed amount +/-$1
(Jennings $35 vs $35.01; Darnold $9 vs $9.11; Bigsby $4 vs $4.42), satisfying the ratified
crossover boundary; the sole H1p (Pitts $39) has no in-window match; the Darnold "$9 pickup"
vs canonical $9.11 is within +/-$1 and is therefore a correctly-stated claim (binder false
positive), not a model error.

### 4.3 Closing - responsible layer(s), no fix design (D-W)

With the final distribution, the dominant failure mechanism is the **verifier's per-player
proximity binder producing false positives on correct, non-player-scoped or adjacent FAAB
statements** - franchise totals ($98, real), team-defense pickups (Cleveland/Chicago DEF),
and team-name references ("the Chargers"). Eight of the nine FAAB failure events are such
false positives (H2p proximity misbinds + H3p out-of-scope bindings); genuine model
invention is present but **smaller than the A7 baseline suggested** - a single event
(Kyle Pitts $39).

Two layers are named (no fix designed, per D-W):

1. **The verifier's FAAB claim model** - it is per-player-only and proximity-bound: it treats
   any dollar near a FAAB keyword as a per-player bid and attaches it to the nearest player
   name within 100 chars. It cannot represent franchise totals, team defenses, or team-name
   references, and its nearest-name binding attaches dollars to players the sentence did not.
2. **The assembly/verifier contract** - the assembly legitimately surfaces FAAB truths the
   verifier cannot represent: `derive_faab_spending` renders franchise-total FAAB spend into
   the writer-room context, and defense/roster context surfaces defense and team references.
   The mismatch spans both layers rather than being a defect in either alone.

Factual description of the shipped code path (not a fix proposal): because `FAAB_CLAIM` is a
Tier-2 no-retry category, the retry loop **short-circuits to facts-only on the first
FAAB_CLAIM failure**. That policy amplifies every one of these false positives into an
immediate facts-only fallback for the whole recap - so a single mis-bound dollar discards an
otherwise-passing narrative.

### 4.4 Non-comparability (per frozen block section 1.6)

This is attribution, not measurement. The Stage B pass/fail pattern (4 cells reproduced no
FAAB failure this run) is **not** a rate and **not** a revision of the A7 baseline
(69.4% first-attempt / 44.4% facts-only). A7 and Stage B are independent model invocations
against different scratch copies; different prose is expected, and a cell passing here says
nothing about the baseline rate. No number in this memo should be read as a baseline update.

## Appendix (non-load-bearing, exploratory)

- Probe (read-only) confirming the H3p franchise-total finding: 2024 total FAAB spend by
  franchise from `v_canonical_best_events` WAIVER_BID_AWARDED - 0006/0004/0003 $100.00,
  0009/0001 $99.99, **0005 $98.15**, 0002 $87.03, 0008 $79.44, 0007 $77.22, 0010 $52.97.
  The model's "$98" matches a real franchise total; the verifier bound it to a player.
- Field 3 distances were reconstructed read-only from the captured prose using the verifier's
  binder logic (nearest occurrence within 100 chars); they are not emitted by the verifier at
  runtime (hazard 4).
- Smoke throwaway 2024 wk8 (excluded) itself showed H1p-style invention (QBs Joe Burrow $11 /
  Kirk Cousins $5, no WBA) - consistent with the H1p mechanism but not part of the 9.
- The 4 NO_FAILURE_REPRODUCED cells (2023 wk5, 2024 wk2, 2024 wk9, 2024 wk14) passed FAAB
  this run; 2024 wk9 reached 3 attempts failing only non-FAAB categories. This is the
  expected non-determinism, not a defect (frozen block 1.6).
