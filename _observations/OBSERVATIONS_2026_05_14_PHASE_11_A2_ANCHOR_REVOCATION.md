# Phase 11 A2 — Cavallini/Mahomes 2018 Anchor Revocation

**Date:** 2026-05-14
**Status:** Provisional / observational. No tier. Not registered in Documentation Map. **Filed as the A2 specification's §8.6 triggered-revision addendum** — a per-finding factual correction filed alongside `OBSERVATIONS_2026_05_13_PHASE_11_A2_SPECIFICATION.md` per that memo's §7 governance ("Specification amendment between revision-points ... a per-finding addendum filed alongside this memo. Append-only; this memo is not silently revised").
**Filing precedent:** Tier 5 Live Observation Cadence Doctrine at `1cf4142`.

**HEAD at authoring:** `38ddcd2` (A3 specification).

**Predecessors:**

- `ee671da` — A2 specification (the memo this addendum corrects example references in; §3.8 / §4.5 / §12.5 carry the misidentification)
- `2da7f21` — A2 decision-readiness Step 1 (§4.5 D2-ε is where the anchor was "confirmed"; the confirmation is the locus of the error)
- `3e9065f` — A2 selection-prep (cited the Cavallini/Mahomes record as a Step 1 verification target per its Anti-Drift §6)
- `Narrative_Angles_v2_Definitive_Scope.md` Phase 6 / Dimension 6 — the originating source of the "Cavallini spent $62 on Patrick Mahomes" claim

**Output:** The "Italian Cavallini / Mahomes 2018" anchor — cited across the A2 chain as a $62 QB pick by franchise 0002 in 2018 — is **revoked as a player-identity claim.** Player `9988` is **Antonio Brown (WR)**, not Patrick Mahomes (QB). The substrate facts the anchor was built on (a $62 pick of player 9988 by franchise 0002 in 2018; ~1804 career points for player 9988) are real and unchanged; only the *player-identity label* and the *QB-position framing* are revoked. A2's structural shape, its six elections, and its `compute_auction_most_expensive_v1` derivation are unaffected. This addendum records the finding, the root cause, the corrected facts, and the downstream consequences.

---

## 1. What this memo is, and is not

**It is:** the canonical record of a factual correction — the revocation of a player-identity claim that propagated through the A2 chain. It is the A2 spec's §8.6 triggered-revision addendum: a finding the spec did not anticipate, recorded append-only alongside the spec rather than by silently rewriting it.

**It is not:** a re-opening of any A2 framing decision, a structural revision to A2, or a rewrite of the A2 specification text. A2's three v1 sub-shapes, its six inherited dispositions (Reading 1 / D3-Alpha / D4.1-Gamma / D4.2-Alpha / D4.3 / D5-Gamma), its No-New-Foundations posture, and its operational shape are **all unaffected.** This is a single example-anchor misidentification, not a scope or design problem.

---

## 2. The finding

**Player `9988` is Antonio Brown — a wide receiver — not Patrick Mahomes.**

The A2 chain cited an "Italian Cavallini / Mahomes 2018 anchor": a $62 auction pick by franchise 0002 in the 2018 auction, attributed to Patrick Mahomes, framed as the league's marquee QB-position auction pick and as the most-cited `Narrative_Angles_v2` success example. The pick exists in the substrate. The player identity attached to it does not hold: `player_id 9988` resolves to Antonio Brown, a WR.

**Confidence: high.** The revocation is a player-directory resolution finding (2026-05-14).

---

## 3. Root cause — how the misidentification propagated

The error originates in `Narrative_Angles_v2_Definitive_Scope.md` Phase 6, which records the success example as: *"Italian Cavallini spent $62 on Patrick Mahomes in the 2018 auction — the third-highest bid in league draft history — and that investment has returned 1,847 career points."*

The A2 chain inherited this claim and "confirmed" it without independently resolving the player identity:

- **A2 selection-prep (`3e9065f`)** cited the Cavallini/Mahomes record as a Step 1 verification target per its Anti-Drift §6 — correctly flagged as not-yet-confirmed.
- **A2 Step 1 §4.5 (D2-ε, `2da7f21`)** ran the verification probe and reported **"MATCH at franchise=0002, player_id=9988, $62 in 2018"** plus a career-production corroboration: "Player 9988 total points across all `WEEKLY_PLAYER_SCORE` entries = 1804.4 points ... order-of-magnitude matches v2's 1,847 claim." It declared the Anti-Drift §6 verification target **DISCHARGED** and the anchor "substrate-anchored."
- **A2 Step 2 and A2 spec** inherited the "confirmed" anchor and wove it through §3.8 (the QB-position-record example), §4.5 (the artisan-frame anchor), §12.5 (side-findings), and §5.5 (the test-fixture reference).

**The D2-ε confirmation confirmed the wrong thing.** The probe matched on `(bid_amount=$62, season=2018, franchise=0002)` and corroborated with career-points order-of-magnitude. It never resolved `player_id 9988` against `player_directory` to verify the *name*. The career-points corroboration was a **false positive**: Antonio Brown's career fantasy-point total is also in the ~1800 range, so the number — 1804.4 vs v2's 1,847 — did not disambiguate Brown from Mahomes. It looked like corroboration; it was coincidence of two players having similar career length.

This is the inverse of the standing diagnostic principle "read the prose before proposing a fix — most apparent model fabrication is verifier false positives." Here, an apparent *confirmation* was the false positive. A verification step that matches on numeric facts and corroborates with an order-of-magnitude metric can confirm a claim's *numbers* while leaving its *identity claim* unverified.

**Confidence: high** on the propagation path (the chain commits record it); **medium-high** on "the originating error is in Narrative_Angles_v2 Phase 6" (the misidentification is certainly *in* v2's text; whether v2's author misread a roster or the error entered v2 from elsewhere is uncharacterized and out of scope for this memo).

---

## 4. The corrected facts

| Claim as cited in the A2 chain | Corrected fact |
|---|---|
| Player 9988 is Patrick Mahomes (QB) | Player 9988 is **Antonio Brown (WR)** |
| The $62 player-9988 pick is "the QB-position anchor" / lands as "the QB-position record" | The $62 player-9988 pick is a **WR pick**; it is a WR-position-record *candidate*, not the QB-position record. The actual QB-position record is whatever the highest QB bid in the substrate is — **uncharacterized this memo** (an A2-implementation substrate probe surfaces it). |
| (implied) the $62 pick is A2's marquee most-expensive anchor | A2's **overall** most-expensive record is **$76 — Saquon Barkley, player 13604, by Cavallini (franchise 0002) in 2019.** This is unchanged: A2 spec §3.5 already correctly states "the all-time most-expensive at $76 has held since 2019." The $62 pick was never the overall record; it was only ever framed as the *QB-position* record, and that framing is what is revoked. |

**What remains true and unchanged:**

- The $62 pick of player 9988 by franchise 0002 in the 2018 auction **exists in the substrate.** The pick is real.
- Player 9988's ~1804 career fantasy points across `WEEKLY_PLAYER_SCORE` entries **are real.** Antonio Brown had a long, productive career; the number is his.
- A2's **overall** most-expensive record — $76 Barkley by Cavallini, 2019, player 13604 — is correct and was correctly stated in A2 spec §3.5.
- The franchise identity is correct: franchise `0002` is Italian Cavallini. Only the *player* on the $62 pick was misidentified.

---

## 5. What is NOT affected

The revocation is narrow. The following are explicitly unaffected:

- **A2's structural shape.** The three v1 sub-shapes (Auction-Most-Expensive History; Auction-Bust Hall; Auction-Bargain Hall) are unchanged. The per-position-records subsection (§3.8) is structurally fine — A2 lifts both the overall record and the per-position records; that design is correct. What is wrong in §3.8 is the *example* (the claim that the Cavallini/Mahomes pick "lands as the QB-position record"), not the subsection's design.
- **A2's six inherited elections.** Reading 1, D3-Alpha, D4.1-Gamma, D4.2-Alpha, D4.3, D5-Gamma — none depended on the anchor's player identity.
- **The `compute_auction_most_expensive_v1` derivation.** The derivation surfaces whatever the substrate says, per position. It never depended on a hardcoded "Mahomes" label. The companion test correction (see §6) confirms the derivation behavior is validated independent of the revoked anchor.
- **A2's No-New-Foundations posture, governance, revision-point, and Mode B operational shape.**
- **A2 spec §6.8's narrative-claim-drift finding.** §6.8 / Step 1 §6.4 established that the "$62 was the third-highest bid in league history" claim from `Narrative_Angles_v2` is no longer current (cross-era as of 2025, $62 ranks outside the top-10; the 10th-place bid is $69). **That finding stands** — it is about *rank drift over time*, not player identity. Only the example sentence's player label ("the Cavallini / Mahomes 2018 $62 pick") carries the misidentification; the rank-drift point itself is valid and unaffected.

---

## 6. Downstream consequences and dispositions

### 6.1 The A2 test surface — corrected by the companion commit

The A2 test surface carried the misidentification in two files. **Both are corrected in the companion commit** to this memo (one topic: purge the revoked anchor from A2's test surface):

- `Tests/test_draft_history_vault_aggregations_v1.py` — the test method `test_cavallini_mahomes_2018_qb_anchor_regression` is renamed to `test_qb_position_record_computed_independently_of_overall`; its synthetic anchor pick is made generic (`player_id="qb_anchor"`, not `"9988"`); the method docstring and the file-level docstring are rewritten to describe the actual derivation behavior under test and to point to this memo. The test *logic* was always correct — it validates that the QB-position record is computed independently of a higher overall record — and that logic is unchanged; only the revoked-anchor labeling is removed.
- `Tests/test_draft_history_vault_render_v1.py` — two `MostExpensivePick` fixtures using `player_id="9988"` with `position="QB"` are corrected to `position="WR"`, and the name map `{"9988": "Patrick Mahomes"}` is corrected to `{"9988": "Antonio Brown"}` (with the corresponding assertions updated). This uses the *correct* player identity rather than going generic, keeping the render test concrete while making it factually accurate.

### 6.2 The A2 specification text — recommended amendment, not done here

A2 spec (`ee671da`) carries the misidentification at these locations:

- **§3.1** (line 64) — "the per-position view surfaces the Italian Cavallini / Mahomes 2018 anchor pick as the QB-position record"
- **§3.8** (line 165) — "The Italian Cavallini / Mahomes 2018 anchor pick ($62, franchise 0002, player 9988) lands as the QB-position record"
- **§4.4** (line 227) — "Italian Cavallini / Mahomes 2018 anchor confirmed at $62 franchise 0002 player 9988 with 1804 career points" (factual-provenance certification)
- **§4.5** (line 244) — "The Italian Cavallini / Mahomes anchor ... lands as the QB-position record under §3.8 per-position view"
- **§5.5** (line 306) — "Unit-tested against fixtures including the Italian Cavallini / Mahomes 2018 anchor"
- **§6.8** (line 375) — the narrative-claim-drift example sentence (the rank-drift point stands; only the player label is wrong — see §5 above)
- **§12.1** (line 562) — "Cavallini / Mahomes 2018 anchor substrate-confirmed"
- **§14** (line 646) — cross-reference to Narrative_Angles_v2 Phase 6

**Disposition:** per A2 spec §7 governance and §8.6 triggered-revision, the A2 spec text is **not silently rewritten.** This addendum *is* the §8.6 triggered-revision record. The A2 spec text amendment — correcting the §3.1 / §3.8 / §4.5 / §5.5 / §12.1 example references to describe the per-position-records derivation without the revoked anchor, and annotating §4.4 / §6.8 / §14 — is recommended as a follow-on, to be done either at A2's next revision-point (NFL Week 1 2026 per A2 spec §8) or by a dedicated A2-spec-amendment addendum. **It is not in this memo's scope** (this memo is the named "anchor revocation memo" follow-on; the A2-spec-text amendment is a distinct, larger follow-on). A2's spec being provisional (`_observations/`, no tier, not Map-registered) and carrying an explicit triggered-revision mechanism is precisely the condition that makes "record the finding in an addendum now, amend the spec text at the revision-point" the constitutionally-correct sequence.

### 6.3 Narrative_Angles_v2 Phase 6 — carries the originating misidentification

`Narrative_Angles_v2_Definitive_Scope.md` Phase 6 is where "Cavallini spent $62 on Patrick Mahomes" enters the chain. Narrative_Angles_v2 is a scope document, not a Phase 11 surface artifact; correcting or annotating it is out of this memo's scope. **Recommended:** when Narrative_Angles_v2 is next touched, Phase 6's success example should be corrected or annotated to reflect that player 9988 is Antonio Brown. Recorded here for whoever next works in that document.

### 6.4 The verification-methodology lesson — recorded for the diagnostic toolkit

The D2-ε confirmation failure has a reusable lesson: **a verification target that names a player must resolve the player ID against `player_directory`.** Matching on `(bid_amount, season, franchise)` confirms the *transaction*; it does not confirm the *player*. Corroborating with an order-of-magnitude metric (career points) can false-positive across any two players of similar career length — it feels like corroboration, but it does not disambiguate identity. Future verification targets that assert "player X is [name]" must resolve the ID, not corroborate the surrounding numbers. Recorded for the diagnostic methodology and for any future verification-target-discharge step.

---

## 7. Confidence labeling

**Highest-confidence claims:**

- Player 9988 is Antonio Brown (WR), not Patrick Mahomes (QB) — player-directory resolution finding.
- The $62 player-9988 pick exists in the substrate and is real; player 9988's ~1804 career points are real.
- A2's overall most-expensive record ($76 Barkley, player 13604, Cavallini, 2019) is unchanged and was correctly stated in A2 spec §3.5.
- A2's structural shape, six elections, and `compute_auction_most_expensive_v1` derivation are unaffected.
- The A2 test surface is corrected by the companion commit; the test *logic* was always correct.

**Medium-high-confidence claims:**

- The originating misidentification is in Narrative_Angles_v2 Phase 6's text. (Certainly in v2's text; whether v2's author introduced it or inherited it is uncharacterized.)
- The D2-ε career-points corroboration was a false positive because Antonio Brown's career fantasy points are also ~1800. (The mechanism is sound; the exact career-points figure for the Mahomes comparison is not independently recomputed here.)

**Claims this memo deliberately does not make:**

- **No characterization of the actual QB-position record.** The highest QB bid in A2's substrate is uncharacterized this memo; an A2-implementation substrate probe surfaces it.
- **No amendment of the A2 specification text.** Recommended as a follow-on per §6.2; not done here.
- **No correction of Narrative_Angles_v2.** Recommended per §6.3; out of scope.
- **No re-opening of any A2 framing decision.** The revocation is a factual correction, not a design finding.

---

## 8. Disposition

The "Italian Cavallini / Mahomes 2018" anchor is **revoked as a player-identity claim.** Player 9988 is Antonio Brown (WR). The substrate facts are unchanged; A2's structural shape is unaffected; the A2 test surface is corrected by the companion commit; the A2 specification text amendment and the Narrative_Angles_v2 correction are recorded as recommended follow-ons.

This memo discharges the "anchor revocation memo" item from the standing A2 follow-on set. The remaining A2 follow-ons — the test rename (companion commit to this memo) and the `generate_draft_history_vault_archive.py` script-docstring `./scripts/py` correction — are separate commits in the same session.

**Filing:** `_observations/OBSERVATIONS_2026_05_14_PHASE_11_A2_ANCHOR_REVOCATION.md`. Provisional / observational. No tier. No Map registration. Filed as the A2 specification's §8.6 triggered-revision addendum per A2 spec §7 governance.

---

## 9. Cross-references

- `ee671da` — A2 specification (the memo this addendum corrects example references in)
- `2da7f21` — A2 decision-readiness Step 1 (§4.5 D2-ε — the confirmation that confirmed the wrong thing)
- `3e9065f` — A2 selection-prep (Anti-Drift §6 verification target)
- `d30a6a9` — A2 decision-readiness Step 2 (inherited the "confirmed" anchor)
- `1cf4142` — Tier 5 Live Observation Cadence Doctrine v1.0 (filing precedent)
- `Narrative_Angles_v2_Definitive_Scope.md` Phase 6 / Dimension 6 — originating source of the misidentification
- `Tests/test_draft_history_vault_aggregations_v1.py` — corrected by the companion commit
- `Tests/test_draft_history_vault_render_v1.py` — corrected by the companion commit
- `src/squadvault/core/recaps/context/auction_draft_angles_v1.py` — `compute_auction_most_expensive_v1` (the derivation, unaffected)
