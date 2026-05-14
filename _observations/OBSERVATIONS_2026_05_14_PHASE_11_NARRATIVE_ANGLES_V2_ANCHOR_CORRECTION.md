# Phase 11 — Narrative_Angles_v2 Anchor Correction Record

**Date:** 2026-05-14
**Status:** Provisional / observational. No tier. Not registered in Documentation Map. **A correction-record memo** for `Narrative_Angles_v2_Definitive_Scope.md` — the originating source of the revoked Cavallini/Mahomes 2018 anchor. The fourth and final artifact in the 2026-05-14 A2 anchor-correction lineage.
**Filing precedent:** Tier 5 Live Observation Cadence Doctrine at `1cf4142`.

**HEAD at authoring:** `65f0304` (A2 spec-text amendment).

**Predecessors:**

- `e5fbb94` — A2 Cavallini/Mahomes 2018 anchor revocation memo (the finding; §6.3 / §9.4 recorded that `Narrative_Angles_v2` Phase 6 carries the originating misidentification and recommended correction "when that document is next touched")
- `97498fa` — A2 test anchor purge (the code-side correction)
- `65f0304` — A2 specification text amendment (the A2-spec-side correction; this memo is the analogous correction record for the *originating* document)

**Output:** `Narrative_Angles_v2_Definitive_Scope.md` is the originating source of the false "Italian Cavallini spent $62 on Patrick Mahomes" claim — the misidentification that propagated, via A2 Step 1 §4.5's mis-verification, into the A2 chain. The anchor was revoked at `e5fbb94`: `player_id 9988` is Antonio Brown, a wide receiver, not Patrick Mahomes, a quarterback. This memo is the authoritative correction record for `Narrative_Angles_v2` itself. It enumerates **all four sites** in `Narrative_Angles_v2` that carry the misidentification (the revocation memo §6.3 caught one of the four), provides recommended corrected text for each, and is explicit that it **cannot apply the correction** — `Narrative_Angles_v2` is a project-knowledge scope document, not a git-repo artifact, so the correction folds in when the document is next touched. With this memo filed, the 2026-05-14 A2 anchor-correction lineage is complete.

---

## 1. What this memo is, and is not

**It is** the correction record for `Narrative_Angles_v2_Definitive_Scope.md` — the document where the false "Cavallini spent $62 on Patrick Mahomes" claim *originated*. The revocation memo (`e5fbb94`) traced the propagation path: the misidentification entered the A2 chain from `Narrative_Angles_v2` Phase 6, was "confirmed" by A2 Step 1 §4.5's structured-field match (which never resolved the player identity), and wove through the A2 spec. The revocation memo corrected the *finding*; the test purge (`97498fa`) corrected the *code*; the spec-text amendment (`65f0304`) corrected the *A2 spec text*. This memo is the analogous correction record for the *originating document*.

**It is not** an edit of `Narrative_Angles_v2_Definitive_Scope.md`. That document is **not in the git repository.** It exists only as a project-knowledge scope document. It cannot be corrected by a commit because it is not a repo artifact, and it cannot be edited from the working environment because it lives in a read-only mount. This memo is therefore a **correction record**, not an applied correction — the same relationship the A2 spec-text amendment (`65f0304`) has to the A2 spec, except that where the A2 spec folds the correction in at promotion or revision-point, `Narrative_Angles_v2`'s correction folds in only "when the document is next touched" (revocation memo §6.3), because the document is not under repo version control at all.

**It is not** an investigation of *how* the misidentification entered `Narrative_Angles_v2` Phase 6 in the first place. The revocation memo §3 / §9.2 already addressed this: the error is in `Narrative_Angles_v2`'s text; whether the v2 author misread a roster, transposed a player, or inherited the error from elsewhere is uncharacterized and is not load-bearing. This memo records *what* is wrong and *what it should say*, not *how it got wrong*.

**It is not** a resolution of the broader documentation-architecture question §8 surfaces (that `Narrative_Angles_v2` is a load-bearing scope document outside both the git repo and the Documentation Map). That is recorded as a side-finding for a future session; it is not this memo's to resolve.

**Confidence on the framing:** **High.**

---

## 2. The document's status — why this is a correction *record*, not a correction

`Narrative_Angles_v2_Definitive_Scope.md` self-identifies as: **Status: SCOPED. Date: 2026-03-29. Governing Contracts: Creative Layer Contract Card, PLAYER_WEEK_CONTEXT Contract Card, Canonical Operating Constitution.** It is a scope document, authored 2026-03-29 — predating the entire Phase 11 surface track and the per-surface constitutional-memo discipline.

Three facts about its status shape this memo:

1. **It is not in the git repository.** A `find` across the repo for the document returns only code artifacts (`narrative_angles_v1.py`, `verify_narrative_angles_v2.py`, test files) — the scope document itself is absent. It exists only in project knowledge.
2. **It is not registered in the Documentation Map** (v1.6, `ac96447`). A `grep` for "narrative" against the Map returns nothing.
3. **It declares itself governed by the Canonical Operating Constitution** — so it considers itself doctrine-bound, even though it is neither repo-resident nor Map-registered.

The consequence: `Narrative_Angles_v2` cannot be corrected by a git commit, because it is not a git artifact. The only constitutionally-available action is to **record** the correction — an authoritative, dated, discoverable record of exactly what is wrong and what it should say — to be applied when the document is next touched. That is what this memo is. (This is itself the structural reason the `Narrative_Angles_v2` correction was always framed, in the revocation memo §6.3, as "when that document is next touched" rather than as an actionable commit.)

**Confidence on the document's status:** **High** — the absence from the repo and the Map are both directly verified.

---

## 3. The four sites — completing the revocation memo's investigation

The revocation memo (`e5fbb94`) §6.3 scoped `Narrative_Angles_v2` out as "out of this memo's scope" and recorded a single recommendation: "Phase 6's success example should be corrected or annotated." That pointed at one site — the Phase 6 worked example in the "What Success Looks Like" sample recap. **The full footprint is four sites.** A precise `grep` for "Mahomes" across `Narrative_Angles_v2_Definitive_Scope.md` returns four lines:

| Site | Line | Section | What it is |
|---|---|---|---|
| 1 | 42 | "The Verification Test" | A "permitted observation" example in the permitted-vs-forbidden list |
| 2 | 43 | "The Verification Test" | A "forbidden analytics" example in the same list |
| 3 | 213 | Detector #20 — AUCTION_PRICE_VS_PRODUCTION | The detector's worked `[NOTABLE]` example |
| 4 | 571 | "What Success Looks Like" | The Phase-6-relevant sentence in the sample-recap blockquote |

Sites 1, 2, and 3 are *before* the Phase 6 section header (line 527); the revocation memo's "Phase 6's success example" recommendation pointed only at site 4. This memo enumerates all four. (This is a completion of the revocation memo's investigation, not a criticism of it — the revocation memo explicitly scoped `Narrative_Angles_v2` out and did not claim to have enumerated its footprint.)

**Confidence on the four-site enumeration:** **High** — a precise `grep` for "Mahomes" returns exactly these four lines; line 527 also matches a "Phase 6" grep but is only the section header, not a misidentification site.

---

## 4. The correction principle

The **core finding** is a player-identity error: `player_id 9988` is Antonio Brown (WR), not Patrick Mahomes (QB). That is the headline correction at all four sites.

But two of the four sites (3 and 4) layer **additional fabricated content** in the *same sentences* as the misidentification — content that travels with the error and cannot be left standing once the identity is corrected:

- **"1,847 career points"** — a specific figure. The substrate figure for `player_id 9988` is ~1804 career points across all rosters (A2 Step 1 §4.5); the "1,847" figure is not substrate-confirmed, and in any case it is Antonio Brown's production, not Patrick Mahomes's.
- **"the third-highest bid in league draft history"** (site 4) — this is the *exact claim* A2 spec §6.8 cited as its narrative-claim-drift example: A2 Step 1 §3.1 found $62 ranks *outside* the cross-era top-10 most-expensive (the 10th-place bid is $69). The claim was substrate-stale even before the identity error was found.
- **"the most productive auction investment in league history"** (site 3) / **"more than any other auction pick ever"** (site 4) — unverified superlatives. A2 Step 1 §3.1 established the all-time most-*expensive* pick is the $76 Barkley pick; "most productive" was never substrate-verified for any identity.

So the correction principle has two layers:

1. **The identity error** — Patrick Mahomes → Antonio Brown; QB → WR — is fixed at all four sites. This is the headline.
2. **The fabricated figures and superlatives that travel in the same sentences** — "1,847 career points," "third-highest bid in league draft history," "most productive ... ever" — are removed at sites 3 and 4, because they were part of the same fabricated framing and cannot be left asserting falsehoods once the identity is corrected. You cannot swap "Mahomes → Antonio Brown" and leave "the most productive auction investment in league history," because that superlative was never true of *any* identity for that pick.

The recommended corrected text below is the **conservative** correction: it fixes the identity and removes any claim that is not substrate-safe. The `Narrative_Angles_v2` author may prefer a fuller rework — substituting a different verified example, or restating with re-verified substrate figures. The recommended text is the floor: factually safe, identity-correct, no asserted falsehoods. (Same "minimal correction; fuller rework is the author's call" framing as the A2 spec-text amendment §2.)

**Confidence on the principle:** **High.**

---

## 5. Site-by-site recommended corrected text

### 5.1 Site 1 — line 42 (the Verification Test, permitted-observation example)

**Current text:**

> - "Italian Cavallini spent $62 on Mahomes and got 1,847 career points" → **Observation. Permitted.**

**What is wrong:** the player ("Mahomes") and the figure ("1,847 career points"). **What is sound:** the example's *purpose* — illustrating a SQL-verifiable observation, in contrast to site 2's forbidden analytics claim.

**Recommended corrected text:**

> - "Italian Cavallini spent $62 on Antonio Brown in the 2018 auction" → **Observation. Permitted.**

The $62 / Cavallini / Antonio Brown / 2018 pick is substrate-confirmed and SQL-verifiable; it illustrates a permitted observation cleanly. The "1,847 career points" figure is dropped — it is not substrate-confirmed, and the bid statement alone is a clean verifiable-observation example.

### 5.2 Site 2 — line 43 (the Verification Test, forbidden-analytics example)

**Current text:**

> - "Mahomes was a steal at $62" → requires valuation judgment → **Analytics. Forbidden.**

**What is wrong:** only the player name. **What is sound:** everything else — the "steal = valuation judgment = forbidden analytics" point is identity-independent.

**Recommended corrected text:**

> - "Antonio Brown was a steal at $62" → requires valuation judgment → **Analytics. Forbidden.**

A pure name swap. This is the cleanest of the four sites.

### 5.3 Site 3 — line 213 (Detector #20 AUCTION_PRICE_VS_PRODUCTION worked example)

**Current text:**

> **Example:** "[NOTABLE] Italian Cavallini spent $62 on Patrick Mahomes in 2018. He's scored 1,847 career points on that roster — the most productive auction investment in league history."

**What is wrong:** the player ("Patrick Mahomes"), the figure ("1,847 career points on that roster"), and the superlative ("the most productive auction investment in league history"). **What is sound:** the example's *purpose* — illustrating what a `[NOTABLE]` AUCTION_PRICE_VS_PRODUCTION angle looks like (a price paired against production).

**Recommended corrected text:**

> **Example:** "[NOTABLE] Italian Cavallini spent $62 on Antonio Brown in the 2018 auction — among the priciest single-player bids of that draft. The detector pairs that $62 price against Brown's points on the roster."

The identity is corrected; the fabricated figure and the unverified "most productive ever" superlative are removed; the example still illustrates the detector's price-vs-production shape. If the `Narrative_Angles_v2` author prefers a concrete career-point figure in the example, it should be a *re-verified* substrate figure for the Cavallini-roster production of `player_id 9988`, not the "1,847" carried over from the fabrication.

### 5.4 Site 4 — line 571 (the "What Success Looks Like" sample recap)

**Current text** (the second sentence of the blockquote line; the first sentence — about Josh Allen — is unaffected):

> Italian Cavallini spent $62 on Patrick Mahomes in the 2018 auction — the third-highest bid in league draft history — and that investment has returned 1,847 career points, more than any other auction pick ever.

**What is wrong:** the player ("Patrick Mahomes"), and *both* superlatives — "the third-highest bid in league draft history" (the exact claim A2 spec §6.8 cited as narrative-claim drift; $62 is outside the cross-era top-10 per A2 Step 1 §3.1) and "more than any other auction pick ever" (unverified; the all-time most-*expensive* pick is the $76 Barkley pick per A2 Step 1 §3.1). The "1,847 career points" figure is also not substrate-confirmed. **What is sound:** the example's *purpose* — illustrating "a recap where the commissioner learns something about their own league."

**Recommended corrected text:**

> Italian Cavallini spent $62 on Antonio Brown in the 2018 auction — one of the franchise's notable auction bids — and the points Brown scored on that roster are the kind of price-vs-production story the auction detectors surface.

The identity is corrected; both unverified superlatives are removed; the "1,847" figure is dropped. The sentence still illustrates good output — a concrete price-vs-production observation is exactly what the rest of `Narrative_Angles_v2` says good output looks like. Note: this is the sentence A2 spec §6.8 already flagged for the "third-highest bid" rank-drift; the §6.8 narrative-claim-drift invariant and its A2-spec-side correction (`65f0304` §3.6) stand independently — this memo corrects the *originating* sentence; the A2 spec amendment corrected the A2-spec sentence that referenced it.

---

## 6. What this memo does NOT do

- **It does not edit `Narrative_Angles_v2_Definitive_Scope.md`.** The document is not a git-repo artifact and lives in a read-only mount. This memo provides recommended corrected text; the correction folds in when the document is next touched (§7).
- **It does not characterize the true substrate figures** for the Cavallini-roster production of `player_id 9988`. The recommended corrected text removes the unverified "1,847" figure rather than substituting a re-verified one; substituting a verified figure (if the author wants a concrete number in the example) is a re-verification step the author owns.
- **It does not investigate how the misidentification entered `Narrative_Angles_v2` Phase 6.** Out of scope per §1; the revocation memo §3 / §9.2 already addressed it as uncharacterized and not load-bearing.
- **It does not resolve the documentation-architecture question** (§8) — that `Narrative_Angles_v2` is a load-bearing scope document outside the git repo and the Documentation Map. That is recorded as a side-finding, not resolved here.
- **It does not touch the A2 chain.** The A2-side corrections are complete (`e5fbb94`, `97498fa`, `65f0304`); this memo is solely about the originating document.

**Confidence:** **High.**

---

## 7. Application disposition

The recommended corrected text in §5 folds into `Narrative_Angles_v2_Definitive_Scope.md` **when that document is next touched** — for any reason. There is no scheduled trigger (the document is not under repo version control, has no revision-point, and is not Map-registered), so "next touched" is the only available disposition, exactly as the revocation memo §6.3 anticipated.

Until the corrected text is folded in, **this memo is the authoritative correction record** for `Narrative_Angles_v2`'s anchor misidentification. Anyone working in `Narrative_Angles_v2` — or relying on its Phase 6 / Detector #20 / Verification-Test examples — should read this memo (and the revocation memo `e5fbb94`) first.

This is the same supersession-then-fold-in pattern used three times now on 2026-05-14: the Roadmap seasons-count revision (`c4b4436`) for the Roadmap, the A2 spec-text amendment (`65f0304`) for the A2 spec, and this memo for `Narrative_Angles_v2`. In each case a dated `_observations/` memo is the authoritative record until the source document's next natural touch-point. The one structural difference here: the Roadmap and the A2 spec are repo-resident and have defined touch-points (revision-point, promotion); `Narrative_Angles_v2` is neither, so its "next touch-point" is unscheduled.

**With this memo filed, the 2026-05-14 A2 anchor-correction lineage is complete:**

- `e5fbb94` — the finding (revocation memo)
- `97498fa` — the code correction (test purge)
- `65f0304` — the A2-spec-text correction (spec-text amendment)
- this memo — the originating-document correction record (`Narrative_Angles_v2`)

There is no further downstream item in the anchor-correction lineage.

**Confidence:** **High.**

---

## 8. Side-finding — Narrative_Angles_v2 is a load-bearing scope document outside the repo and the Map

Recorded, not resolved.

`Narrative_Angles_v2_Definitive_Scope.md` is referenced as a cross-reference by at least ten committed `_observations/` memos — the A1 selection-prep, the full A2 chain (selection-prep, Step 1, Step 2, spec), the full A3 chain (selection-prep, Step 1, Step 2, spec), and the A2 spec-text amendment. It declares itself governed by the Canonical Operating Constitution. It is, by any reasonable measure, a **load-bearing scope document** for the Phase 11 surface track.

Yet it is **neither in the git repository nor registered in the Documentation Map.** It exists only as project knowledge. This has a concrete consequence, demonstrated by this very memo: a factual error in `Narrative_Angles_v2` cannot be corrected by a commit — it can only be *recorded*, the way this memo records it, and applied whenever the document is next touched. A load-bearing doctrine-governed document with no version control and no Map registration is a documentation-architecture gap.

This is **recorded for a future documentation-architecture or Documentation-Map-revision session**, not resolved here. The questions it raises — should the project's scope documents be repo-resident? should they be Map-registered? what is the right home and version-control posture for pre-Phase-11 scope documents that remain load-bearing? — are real, but they are a separate and larger topic than the anchor correction. Resolving them is not "clearing the anchor-correction debt"; it is opening a new and distinct question. One-topic discipline keeps this memo to the anchor correction; the architectural gap is flagged for whoever takes up Map-revision or documentation-architecture work.

**Confidence on the side-finding:** **High** that the gap exists and is correctly characterized; the disposition (record, do not resolve) is the one-topic-consistent call.

---

## 9. Confidence labeling

### 9.1 Highest-confidence claims

- `player_id 9988` is Antonio Brown (WR), not Patrick Mahomes (QB) — the core finding, established at `e5fbb94`. (§4)
- The misidentification appears at four sites in `Narrative_Angles_v2` (lines 42, 43, 213, 571); a precise `grep` for "Mahomes" returns exactly these four. The revocation memo §6.3 caught one of the four. (§3)
- `Narrative_Angles_v2_Definitive_Scope.md` is not in the git repo and not in the Documentation Map — both directly verified. (§2, §8)
- This memo cannot apply the correction; it is a correction record, applied when the document is next touched. (§1, §2, §7)
- Sites 3 and 4 layer fabricated figures and superlatives ("1,847 career points," "third-highest bid," "most productive ... ever") in the same sentences as the misidentification; these are removed in the recommended corrected text because they were part of the same fabricated framing. (§4, §5.3, §5.4)
- With this memo, the 2026-05-14 A2 anchor-correction lineage is complete. (§7)

### 9.2 Medium-high confidence claims

- The recommended corrected text is the conservative floor — identity-correct, no asserted falsehoods. A fuller rework (a different verified example, or restatement with re-verified substrate figures) is the `Narrative_Angles_v2` author's call. (§4, §5)

### 9.3 Claims this memo deliberately does not make

- No edit of `Narrative_Angles_v2_Definitive_Scope.md` — recorded correction, not applied. (§1, §6)
- No re-verified substrate figure for the Cavallini-roster production of `player_id 9988` — the recommended text removes the unverified figure rather than substituting one. (§5.3, §6)
- No investigation of how the misidentification entered `Narrative_Angles_v2`. (§1, §6)
- No resolution of the documentation-architecture gap (§8) — recorded for a future session. (§6, §8)

### 9.4 Side-findings recorded within this memo

- **`Narrative_Angles_v2` is a load-bearing scope document outside the repo and the Map** (§8) — recorded for a future documentation-architecture or Map-revision session; not resolved here.
- **The supersession-then-fold-in pattern is now used three times on 2026-05-14** — Roadmap (`c4b4436`), A2 spec (`65f0304`), and `Narrative_Angles_v2` (this memo). The pattern is established for correcting source documents under append-only or out-of-repo discipline; the structural variation is that `Narrative_Angles_v2`'s "next touch-point" is unscheduled because the document is not repo-resident. (§7)

---

## 10. Cross-references

- `e5fbb94` — A2 Cavallini/Mahomes 2018 anchor revocation memo (the finding; §6.3 / §9.4 recorded the `Narrative_Angles_v2` Phase 6 misidentification and recommended this follow-on)
- `97498fa` — A2 test anchor purge (the code-side correction in the lineage)
- `65f0304` — A2 specification text amendment (the A2-spec-side correction; the direct structural precedent for this memo's correction-record form)
- `c4b4436` — Phase 11 Roadmap seasons-count revision (the first 2026-05-14 use of the supersession-then-fold-in pattern)
- `2da7f21` — A2 decision-readiness Step 1 (§4.5 — the mis-verification that propagated the `Narrative_Angles_v2` Phase 6 claim into the A2 chain)
- `1cf4142` — Tier 5 Live Observation Cadence Doctrine v1.0 (filing precedent)
- `Narrative_Angles_v2_Definitive_Scope.md` — the document this memo is the correction record for; Status SCOPED, dated 2026-03-29; not repo-resident, not Map-registered; misidentification at lines 42, 43, 213, 571

---

*Filing: `_observations/OBSERVATIONS_2026_05_14_PHASE_11_NARRATIVE_ANGLES_V2_ANCHOR_CORRECTION.md`.*
*Provisional / observational. No tier. No Map registration. A correction-record memo — corrected text specified here, folds into `Narrative_Angles_v2` when that document is next touched.*
