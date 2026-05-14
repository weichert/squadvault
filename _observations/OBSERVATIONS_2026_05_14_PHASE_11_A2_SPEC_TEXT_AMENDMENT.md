# Phase 11 A2 (Draft History Vault) — Specification Text Amendment: Anchor References

**Date:** 2026-05-14
**Status:** Provisional / observational. No tier. Not registered in Documentation Map. **A dedicated A2-specification text-amendment addendum** per A2 spec §7 governance ("Specification amendment between revision-points ... a per-finding addendum filed alongside this memo. Append-only; this memo is not silently revised") and §8.6 (triggered revision — "dated addenda filed alongside this memo"). Filed alongside `OBSERVATIONS_2026_05_13_PHASE_11_A2_SPECIFICATION.md` and its companion `OBSERVATIONS_2026_05_14_PHASE_11_A2_ANCHOR_REVOCATION.md`.
**Filing precedent:** Tier 5 Live Observation Cadence Doctrine at `1cf4142`.

**HEAD at authoring:** `72087d5` (A1 archive-script docstring fix).

**Predecessors:**

- `ee671da` — A2 specification (the memo this addendum amends — eight sites carry the revoked anchor)
- `e5fbb94` — A2 Cavallini/Mahomes 2018 anchor revocation memo (the finding; this memo discharges its §6.2 recommended follow-on)
- `97498fa` — A2 test anchor purge (the test surface was corrected in code; this memo brings the spec text into alignment with the corrected test surface)
- `2da7f21` — A2 decision-readiness Step 1 (§4.5 D2-ε — the mis-verification, superseded by `e5fbb94` §4; not amended here, see §6)

**Output:** The A2 anchor revocation memo (`e5fbb94`) superseded the false "Cavallini/Mahomes 2018 QB anchor" claims *by reference* and explicitly deferred the A2 spec-text amendment as "a distinct, larger follow-on" (revocation memo §6.2). This memo discharges that follow-on. It provides the **recommended corrected text** for each of the eight A2-spec sites that carry the revoked anchor (§§3.1, 3.8, 4.4, 4.5, 5.5, 6.8, 12.1, 14). It is **not an in-place edit** of `ee671da` — the A2 spec is append-only per its own §7. This memo is the authoritative corrected-text record; the corrections fold into the A2 spec at promotion (`_observations/` → `docs/`) or at A2's next revision-point (NFL Week 1 2026 per A2 spec §8), whichever comes first.

---

## 1. What this memo is, and is not

**It is** the spec-text amendment the revocation memo (`e5fbb94`) §6.2 recommended as a follow-on. The revocation memo *superseded* the false claims by reference — it recorded, site by site, that each claim was revoked. This memo goes the next step: it provides the **corrected text** each site should carry. The revocation memo answered "what is wrong"; this memo answers "what it should say instead."

**It is not** an in-place edit of the A2 specification (`ee671da`). The A2 spec is append-only per its own §7 governance and §8.6 triggered-revision provision. This memo is a dated addendum filed alongside the spec — the same mechanism the revocation memo used, and the same mechanism the 2026-05-14 Roadmap seasons-count revision (`c4b4436`) used for the Roadmap. The corrected text in §3 below is *recommended text*, not applied text; it folds into the A2 spec at promotion or revision-point.

**It is not** an amendment of A2 Step 1, A2 Step 2, or A2 selection-prep. Those are chain-step memos — historical records of the state of knowledge at each step. A2 Step 1 §4.5 genuinely recorded "CONFIRMED" because that was the (mistaken) finding at that step; amending it would be rewriting history. The revocation memo §4 correctly handles those by *supersession* — "the CONFIRMED verdict is revoked." This memo's scope is the **standing specification only** — the document meant to be promoted to `docs/` and to govern A2's implementation. A standing spec carrying factually-wrong text is a problem in a way a historical chain-step memo carrying its then-current understanding is not.

**It is not** an establishment of the true QB-position record. Per the revocation memo §7, the actual all-time most-expensive QB is uncharacterized and requires an A2-implementation substrate probe. The corrected text below removes the false claim; it does not substitute a true one where the truth is not yet known.

**Confidence on the framing:** **High.**

---

## 2. The amendment principle

Each correction below follows one principle: **minimal correction — remove the false claim, preserve everything sound.**

The false claims are narrow and specific: that player 9988 is Patrick Mahomes; that player 9988 is a QB; that the "$62 / franchise 0002 / 2018" pick is "the QB-position record" or "the QB anchor." Everything else at each site is sound and is preserved — the substrate facts (a $62 pick by franchise 0002 on player 9988 in 2018; ~1804 career points for player 9988), the design rationale (the per-position-records subsection's logic), and the invariants (§6.8's narrative-claim-drift principle).

Each recommended NEW text carries a brief **correction parenthetical** pointing to the revocation memo (`e5fbb94`). This is deliberate: append-only discipline values *visible* corrections. When these corrections fold into the A2 spec at promotion, a future reader of §3.8 (or any amended site) should see that a factual error was corrected and where to read about it — not silently-clean text that hides the correction history. This matches the pattern used for the test-surface correction in `97498fa`, where the corrected test docstring retained a pointer to the revocation memo.

The recommended NEW text is the **minimal** correction. A fuller rewrite of any section — restructuring §3.8, substituting a different worked example once the true QB record is characterized, etc. — is the founder's call at promotion or revision-point. This memo provides the floor: the text with the false claim removed and the sound content preserved.

**One site is a special case — §6.8.** See §3.6 and §4 below: §6.8's correction is *correction plus reinforcement*, not simple removal. The §6.8 invariant is sound and the rank-drift point it makes is still true; only the player attribution in its example was wrong, and the discovery that the same source sentence carried *two* errors strengthens the invariant's rationale.

**Confidence on the principle:** **High.**

---

## 3. Site-by-site amendments

Eight sites. For each: the current text in `ee671da`, what is wrong, and the recommended corrected text.

### 3.1 §3.1 (line 64) — Auction-Most-Expensive History sub-shape description

**Current text:**

> Per Step 1 §6.2 finding: the per-position view surfaces the Italian Cavallini / Mahomes 2018 anchor pick as the QB-position record, preserving the Voice Profile §5 anchor in a way an overall-only view does not.

**What is wrong:** the per-position view does not surface a "Cavallini / Mahomes 2018 anchor pick as the QB-position record" — that anchor does not exist. **What is sound and preserved:** Step 1 §6.2's actual finding — the cross-era top-10 most-expensive is RB-skewed, so an overall-only view misses per-position structure. The revocation memo §5 confirmed the §3.8 per-position-records design rationale is independently valid and unaffected.

**Recommended corrected text:**

> Per Step 1 §6.2 finding: the cross-era top-10 most-expensive picks are 9-of-10 RBs, so an overall-only view is position-skewed; the per-position view surfaces each position's record independently, exposing structure an overall-only view misses. (Correction: an earlier version cited a "Cavallini / Mahomes 2018" QB anchor as the worked example here; that anchor was revoked per the 2026-05-14 A2 anchor revocation memo — player 9988 is Antonio Brown, a WR, not Patrick Mahomes. The per-position-records design rationale is unaffected.)

### 3.2 §3.8 (line 165) — Per-position records exposure

**Current text:**

> The Italian Cavallini / Mahomes 2018 anchor pick ($62, franchise 0002, player 9988) lands as the QB-position record under per-position view per Step 1 §3.1 top-10 distribution analysis. This preserves the Voice Profile §5 anchor's visibility in a way the overall-only view does not.

**What is wrong:** the claim is doubly wrong per the revocation memo §4 — player 9988 is not Mahomes, *and* player 9988 is not a QB, so the pick cannot be the QB-position record under any substrate state. **What is sound and preserved:** the per-position-records derivation itself — each per-position record is the substrate's highest position-specific bid.

**Recommended corrected text:**

> Each per-position record is the all-time highest bid for that position present in the substrate; the QB-position record, like every per-position record, is whatever the substrate's highest position-specific bid resolves to at A2-implementation time. (Correction: an earlier version of this paragraph identified the "$62, franchise 0002, player 9988" pick as the QB-position record; that identification was revoked per the 2026-05-14 A2 anchor revocation memo — player 9988 is Antonio Brown, a WR, so that pick is a WR-position-record candidate, not the QB record. The actual QB-position record is uncharacterized pending an A2-implementation substrate probe; the per-position-records derivation surfaces it.)

### 3.3 §4.4 (line 227) — Factual-provenance certification

**Current text:**

> The traceability is verified by Step 1 §3 (empirical probe; 1163 auction picks loaded across 7 seasons; 4690 (season, franchise, player) scoring rows; Italian Cavallini / Mahomes 2018 anchor confirmed at $62 franchise 0002 player 9988 with 1804 career points). **Satisfied through substrate inheritance.**

**What is wrong:** "Italian Cavallini / Mahomes 2018 anchor confirmed" — the anchor (as a Mahomes/QB entity) was not confirmed. **What is sound and preserved:** every substrate fact in the parenthetical — 1163 picks, 7 seasons, 4690 scoring rows, the $62 pick, franchise 0002, player 9988, 1804 career points — is correct per the revocation memo §5. Only the "Cavallini / Mahomes anchor" framing of the last item is wrong.

**Recommended corrected text:**

> The traceability is verified by Step 1 §3 (empirical probe; 1163 auction picks loaded across 7 seasons; 4690 (season, franchise, player) scoring rows; the 2018 $62 pick of player 9988 by franchise 0002 confirmed at substrate, with 1804 career points for player 9988). **Satisfied through substrate inheritance.** (Correction: an earlier version described this pick as the "Italian Cavallini / Mahomes 2018 anchor"; player 9988 is Antonio Brown, a WR, not Patrick Mahomes — per the 2026-05-14 A2 anchor revocation memo. The substrate facts — the $62 pick, franchise 0002, player 9988, 1804 career points — are correct as stated; only the Mahomes attribution was wrong.)

### 3.4 §4.5 (line 244) — §9.2 artisan-frame discussion

**Current text:**

> The Italian Cavallini / Mahomes anchor (Step 1 §4.5 / D2-ε) lands as the QB-position record under §3.8 per-position view, preserving the most-cited Narrative_Angles_v2 success-example pick's visibility through substrate-derived rendering rather than narrative-frozen labeling.

**What is wrong:** the entire sentence is built on the revoked anchor; the revocation memo §4 noted "the most-cited Narrative_Angles_v2 success example was itself factually wrong about the player; there is no Mahomes pick to preserve the visibility of." **What is sound and preserved:** the §9.2 artisan-frame fit does not depend on the anchor — it rests on substrate-derived per-position rendering serving the Voice Profile §5 "league remembers" frame.

**Recommended corrected text:**

> The per-position records under §3.8 serve the Voice Profile §5 "league remembers" frame by surfacing each position's marquee auction pick directly from the substrate — substrate-derived rendering rather than narrative-frozen labeling. (Correction: an earlier version of this sentence cited an "Italian Cavallini / Mahomes anchor" as the QB-position record and as the most-cited Narrative_Angles_v2 success example; that anchor was revoked per the 2026-05-14 A2 anchor revocation memo — the Narrative_Angles_v2 Phase 6 success example misattributed player 9988, who is Antonio Brown, a WR, to Patrick Mahomes. The §9.2 artisan-frame fit does not depend on the revoked anchor.)

### 3.5 §5.5 (line 306) — Test baseline at the specified shape

**Current text:**

> New cross-season derivation functions (`compute_auction_most_expensive`, `compute_auction_bust_hall`, `compute_auction_bargain_hall`, or whatever the implementer elects to name them). Unit-tested against fixtures including the Italian Cavallini / Mahomes 2018 anchor per Step 1 §4.5 verification.

**What is wrong:** "fixtures including the Italian Cavallini / Mahomes 2018 anchor" — the test surface was purged of the anchor in commit `97498fa`; the spec text describes a fixture that no longer exists. **What is sound and preserved:** the tests do unit-test the derivation functions; the corrected text reflects what they actually test now.

**Recommended corrected text:**

> New cross-season derivation functions (`compute_auction_most_expensive`, `compute_auction_bust_hall`, `compute_auction_bargain_hall`, or whatever the implementer elects to name them). Unit-tested against synthetic fixtures, including the per-position-record derivation property (per-position records computed independently of the overall record). (Correction: an earlier version referenced "the Italian Cavallini / Mahomes 2018 anchor" as a test fixture; the anchor was revoked and the test surface purged of it in commit 97498fa — see the 2026-05-14 A2 anchor revocation memo. The test validates the derivation property with neutral synthetic fixtures.)

### 3.6 §6.8 (line 375) — Narrative-claim drift principle — SPECIAL CASE

**Current text:**

> Any sub-shape that surfaces ordinal-rank claims ("the all-time most-expensive pick"; "the third-highest bid in league history"; "the worst auction bust in PFL history") must compute the rank at render time against the current substrate state. **A2 does not narrative-freeze rank claims into the archive at write time.** Per Step 1 §4.5 / §6.4 finding: the Narrative_Angles_v2 success-example claim that the Cavallini / Mahomes 2018 $62 pick was "the third-highest bid in league draft history" was substrate-accurate at the moment v2 was authored but is empirically not current (cross-era as of 2025, $62 ranks outside the top-10 most-expensive; the 10th-place bid is $69).

**What is wrong:** only the player attribution — "the Cavallini / Mahomes 2018 $62 pick." **What is sound and preserved — almost all of it:** the §6.8 invariant (compute rank at render time; do not narrative-freeze) is entirely sound and unaffected. The rank-drift point is *still true* — there is a real $62 pick by Cavallini in 2018, and its cross-era rank did drift outside the top-10. The revocation memo §5 noted §6.8 is in fact *reinforced* by the finding: the same Narrative_Angles_v2 Phase 6 sentence carried *two* narrative-frozen errors — a drifted rank and a wrong player identity.

This is the **special case**: the correction is *correction plus reinforcement*, not simple removal. The invariant stays whole; the rank-drift example stays whole; only the player attribution is fixed; and a sentence is added noting the two-error finding strengthens the invariant's rationale.

**Recommended corrected text:**

> Any sub-shape that surfaces ordinal-rank claims ("the all-time most-expensive pick"; "the third-highest bid in league history"; "the worst auction bust in PFL history") must compute the rank at render time against the current substrate state. **A2 does not narrative-freeze rank claims into the archive at write time.** Per Step 1 §4.5 / §6.4 finding: the Narrative_Angles_v2 Phase 6 success-example claim that a Cavallini 2018 $62 pick was "the third-highest bid in league draft history" was substrate-accurate at the moment v2 was authored but is empirically not current (cross-era as of 2025, $62 ranks outside the top-10 most-expensive; the 10th-place bid is $69). (Correction and reinforcement: an earlier version of this sentence attributed the $62 pick to "Cavallini / Mahomes" — that attribution was revoked per the 2026-05-14 A2 anchor revocation memo; player 9988 is Antonio Brown, a WR, not Patrick Mahomes. The rank-drift point stands unchanged — the $62 pick is real and its cross-era rank did drift. The same Narrative_Angles_v2 Phase 6 sentence in fact carried two narrative-frozen errors — a drifted rank and a wrong player identity — which strengthens, not weakens, this invariant's rationale.)

### 3.7 §12.1 (line 562) — Confidence labeling, highest-confidence claims

**Current text:**

> **A2's substrate-derivability per D3-Alpha is empirically verified.** Step 1 §3 confirmed all three v1 sub-shapes consume `DRAFT_PICK` + `WEEKLY_PLAYER_SCORE` + `player_directory` and trace to existing D20-D28 detector aggregations. Cavallini / Mahomes 2018 anchor substrate-confirmed (franchise 0002, player 9988, $62, 1804 career points). (§§3.1, 4.1, 4.3, 4.5)

**What is wrong:** "Cavallini / Mahomes 2018 anchor substrate-confirmed" — same as §4.4, the substrate facts are correct but the "anchor" framing is wrong. **What is sound and preserved:** the substrate-derivability claim itself, and every substrate fact in the parenthetical.

**Recommended corrected text:**

> **A2's substrate-derivability per D3-Alpha is empirically verified.** Step 1 §3 confirmed all three v1 sub-shapes consume `DRAFT_PICK` + `WEEKLY_PLAYER_SCORE` + `player_directory` and trace to existing D20-D28 detector aggregations. The 2018 $62 pick of player 9988 by franchise 0002 is substrate-confirmed (with 1804 career points for player 9988). (§§3.1, 4.1, 4.3, 4.5) (Correction: an earlier version described this as the "Cavallini / Mahomes 2018 anchor"; player 9988 is Antonio Brown, a WR, not Patrick Mahomes — per the 2026-05-14 A2 anchor revocation memo. The substrate facts are correct as stated.)

### 3.8 §14 (line 646) — Cross-references

**Current text:**

> `Narrative_Angles_v2_Definitive_Scope.md` Phase 6 — Italian Cavallini / Mahomes anchor source (now substrate-confirmed per Step 1 §4.5)

**What is wrong:** "Italian Cavallini / Mahomes anchor source (now substrate-confirmed)" — Narrative_Angles_v2 Phase 6 is indeed the *source* of the claim, but it is the source of a *misidentification*, not a "now substrate-confirmed" anchor. **What is sound and preserved:** the cross-reference itself — Phase 6 *is* the relevant source to point at; the pointer's characterization is what is wrong.

**Recommended corrected text:**

> `Narrative_Angles_v2_Definitive_Scope.md` Phase 6 — source of the (revoked) "Cavallini / Mahomes 2018" anchor claim; the Phase 6 success example misattributed player 9988 (Antonio Brown, WR) to Patrick Mahomes. See the 2026-05-14 A2 anchor revocation memo.

---

## 4. The §6.8 special case, restated

Seven of the eight sites are *removals* — the false claim is excised and sound content preserved or substituted. §6.8 is different and worth restating clearly because a future applier of this amendment should not over-correct it.

§6.8 is the narrative-claim-drift invariant. Its logic — substrate-derived rank claims must compute at render time, never narrative-freeze — is **sound, load-bearing, and entirely unaffected** by the anchor revocation. Its illustrative example references "the Cavallini / Mahomes 2018 $62 pick," and the example's *point* is rank-drift: a claim that was substrate-accurate when Narrative_Angles_v2 was authored is empirically not current. That point is **still true** — there is a real $62 Cavallini 2018 pick, and its cross-era rank did drift outside the top-10.

Only the player attribution ("Mahomes") was wrong. And the discovery sharpens the invariant rather than weakening it: the *same* Narrative_Angles_v2 Phase 6 sentence carried **two** narrative-frozen errors — a drifted rank *and* a wrong player identity. An invariant whose motivating example turns out to contain two independent instances of exactly the failure mode the invariant guards against is an invariant with a *stronger* empirical case, not a weaker one. The recommended §6.8 corrected text (§3.6) therefore preserves the entire invariant and the entire rank-drift example, fixes only the attribution, and adds one sentence recording the two-error finding as reinforcement.

A future applier should resist the impulse to delete or soften §6.8's example on the grounds that "it referenced the revoked anchor." The example is one of A2's strongest — it should be corrected and kept, not removed.

**Confidence:** **High.**

---

## 5. What this memo does NOT do

- **It does not edit `ee671da`'s spec file.** The A2 spec is append-only per §7 / §8.6. This memo provides recommended corrected text; the corrections fold in at promotion or revision-point (§7 below).
- **It does not amend A2 Step 1, A2 Step 2, or A2 selection-prep.** Those are historical chain-step memos; the revocation memo `e5fbb94` §4 handles them by supersession. This memo's scope is the standing specification only.
- **It does not characterize the true QB-position record.** Per the revocation memo §7, that requires an A2-implementation substrate probe. The §3.2 corrected text removes the false QB-record claim and states the record is uncharacterized; it does not substitute a true one.
- **It does not modify `Narrative_Angles_v2`.** The revocation memo §9.4 recorded that `Narrative_Angles_v2` Phase 6 carries the originating misidentification; correcting `Narrative_Angles_v2` itself remains a separate follow-on, out of this memo's scope.
- **It does not apply the corrections via a script.** Unlike the code-file corrections this session (the test-surface purge and the archive-script docstrings, which were applied by patch scripts because those are freely-editable code files), the A2 spec is a provisional constitutional memo under append-only discipline. The corrected text is *specified* here, *applied* at promotion or revision-point — not script-applied now.

**Confidence:** **High.**

---

## 6. Relationship to the revocation memo and the test purge

This memo is the third and final artifact in the 2026-05-14 A2 anchor-correction set:

- **`e5fbb94` — the revocation memo.** Recorded the finding (player 9988 is Antonio Brown, not Patrick Mahomes), the root cause (A2 Step 1 §4.5's verification matched structured fields without resolving player identity), and *superseded the false claims by reference* across the A2 chain.
- **`97498fa` — the test purge.** Corrected A2's test surface in code — renamed the misframed test, neutralized the aggregations fixture, corrected the render test to the accurate identity (Antonio Brown, WR).
- **This memo — the spec-text amendment.** Provides the corrected *text* for the eight A2-spec sites the revocation memo superseded by reference. Where the revocation memo said "this claim is revoked," this memo says "here is what the section should say instead."

With this memo filed, the revocation memo's §6.2 recommended follow-on ("the A2 spec text amendment ... a distinct, larger follow-on") is **discharged.** The one remaining item from the revocation memo's downstream-consequences set is the `Narrative_Angles_v2` Phase 6 correction (revocation memo §6.3 / §9.4), which is its own document's concern.

**Confidence:** **High.**

---

## 7. Application disposition

The corrected text in §3 folds into the A2 specification **at the A2 spec's promotion or its next revision-point, whichever comes first:**

- **At promotion** (`_observations/` → `docs/`, per A2 spec §8.4): when the A2 spec is promoted after one full cycle, the promotion session applies the §3 corrected text as part of moving the file. The promotion is the natural moment — the spec is being touched anyway, and a promoted (Tier-registered) spec should not carry known factual errors.
- **At A2's next revision-point** (NFL Week 1 2026, per A2 spec §8): if the revision-point fires before promotion, the revision session applies the §3 corrected text.

Until the corrected text is folded in, **this memo is the authoritative corrected-text record.** A reader of the A2 spec who encounters any of the eight sites should read this memo (and the revocation memo `e5fbb94`) for the correction. The A2 spec's eight sites are not silently wrong — they are *visibly superseded*: the revocation memo supersedes the claims, and this memo supersedes the text.

This is the same supersession-then-fold-in pattern the 2026-05-14 Roadmap seasons-count revision (`c4b4436`) used for the Roadmap: a dated addendum is the authoritative record until the next natural touch-point folds the correction into the source document.

**Confidence:** **High** — the disposition follows directly from A2 spec §7 / §8.4 / §8 and the established supersession-then-fold-in pattern.

---

## 8. Confidence labeling

### 8.1 Highest-confidence claims

- The eight sites (§§3.1, 3.8, 4.4, 4.5, 5.5, 6.8, 12.1, 14) are the complete set of A2-spec sites carrying the revoked anchor — a precise `grep` for "Cavallini" / "Mahomes" against `ee671da` returns exactly these eight, matching the revocation memo §6.2 enumeration. (§3)
- The amendment principle is minimal correction — remove the false claim, preserve everything sound. The substrate facts, the design rationale, and the §6.8 invariant are all sound and preserved. (§2)
- §6.8 is a special case — correction plus reinforcement, not removal. The invariant and the rank-drift example are sound and stay whole; only the player attribution is fixed. (§3.6, §4)
- This memo does not edit `ee671da`; it is a dated addendum, and the corrected text folds in at promotion or revision-point. (§1, §7)
- This memo discharges the revocation memo §6.2 recommended follow-on. (§6)

### 8.2 Medium-high confidence claims

- The recommended corrected text is the *minimal* correction; a fuller rewrite of any section is the founder's call at promotion or revision-point. The recommended text is a sound floor, but the founder may legitimately choose to restructure (e.g., substitute a corrected worked example in §3.8 once the true QB record is characterized). (§2)

### 8.3 Claims this memo deliberately does not make

- No claim about the true QB-position record — uncharacterized pending an A2-implementation substrate probe. (§3.2, §5)
- No edit of `ee671da`'s file; no script application. (§5)
- No amendment of A2 Step 1 / Step 2 / selection-prep — handled by supersession in the revocation memo. (§1, §5)
- No modification of `Narrative_Angles_v2` — a separate follow-on. (§5, §6)

### 8.4 Side-findings recorded within this memo

- **The 2026-05-14 A2 anchor-correction set is complete with this memo** (§6) — revocation memo + test purge + spec-text amendment. The only remaining downstream item is the `Narrative_Angles_v2` Phase 6 correction.
- **The supersession-then-fold-in pattern is now used twice on 2026-05-14** — for the Roadmap (seasons-count revision `c4b4436`) and for the A2 spec (this memo). In both cases a dated addendum is the authoritative record until the source document's next natural touch-point. This is an established, repeatable pattern for correcting provisional constitutional memos under append-only discipline.

---

## 9. Cross-references

- `ee671da` — A2 specification (the memo this addendum amends — §§3.1 / 3.8 / 4.4 / 4.5 / 5.5 / 6.8 / 12.1 / 14)
- `e5fbb94` — A2 Cavallini/Mahomes 2018 anchor revocation memo (the finding; §6.2 recommended this follow-on; §4 superseded the claims by reference that this memo now provides corrected text for)
- `97498fa` — A2 test anchor purge (the code-side correction; this memo brings the spec text into alignment with the corrected test surface)
- `c4b4436` — Phase 11 Roadmap seasons-count revision (the same-session precedent for the supersession-then-fold-in pattern on a provisional constitutional memo)
- `2da7f21` — A2 decision-readiness Step 1 (§4.5 D2-ε — the mis-verification; handled by supersession in `e5fbb94`, not amended here)
- `1cf4142` — Tier 5 Live Observation Cadence Doctrine v1.0 (filing precedent)
- `Narrative_Angles_v2_Definitive_Scope.md` Phase 6 — the originating misidentification; correcting it remains a separate follow-on per `e5fbb94` §6.3

---

*Filing: `_observations/OBSERVATIONS_2026_05_14_PHASE_11_A2_SPEC_TEXT_AMENDMENT.md`.*
*Provisional / observational. No tier. No Map registration. A dedicated A2-specification text-amendment addendum per A2 spec §7 / §8.6 — corrected text specified here, folds into the spec at promotion or revision-point.*
