# SquadVault Trophy Taxonomy — W.5 D-J Ratification Input

**Version:** v1.2 (Championship Package added: The Belt reclassified to traveling, The Ring and The League Trophy added; see Championship Package section and Ratified Decisions)
**Date:** 2026-06-21
**Status:** Ratified D-J input (consumed by the W.5 specification session; this is NOT the spec itself). One non-blocking design-track item and one attestation flag remain.
**Source of record:** PFL Buddies 35-award canonical set + SquadVault Trophy System Explanation + Championship Package ruling
**Scope:** One entry per trophy — name / qualification (completed fact) / custody rule. Constitutional pass run on all 37 artifacts.

---

## How to read this document

Each entry carries three governed fields:

1. **Qualification** — the immutable, append-only completed fact that earns the trophy. Never predictive. Never invented.
2. **Custody** — Travels? plus the condition under which the current-holder read changes. Custody is an **append-only event ledger**; "current holder" is always a **DERIVED read**, never mutable state.
3. **Current holder (derived)** — where the source set names one, it is recorded here as a derived read *as of the named season*. It is NOT part of the qualification definition (see Constitutional Note C1).

**Provenance flag:** Qualifications are taken verbatim-in-substance from your canonical 35-set (stated). Custody rules are **derived** from the category logic in your system explainer. Per ratification, category-derived custody is authoritative for all 35 with no per-trophy overrides (Ratified Decision 1).

---

## Custody models (one per category)

| Category | Travels? | Custody model |
|---|---|---|
| Annual Trophies | No transfer; re-awarded per season | Each season appends one permanent award event. Current holder of the named award = derived read = most recent certified season's recipient. Prior seasons never erased. Mutation only via correction. |
| Positional Awards | No transfer; per season | Same as Annual. |
| Draft / Auction Awards | No transfer; per season | Same as Annual. |
| In-Season Acquisition | No transfer; per season | Same as Annual. |
| Live Record Plaques | **Travels** when surpassed | Append-only ledger of record-holders. Current holder = derived read = current record-holder. A new holder appends when a *completed* fact surpasses the prior mark. Prior holders retained. The current-holder read may be **multi-valued** when a mark is tied (co-held). |
| Permanent Historical Plaques | **Never travels** | Single immutable append. The named fact is fixed; the plaque does not change hands. One variant (The Perfect Storm) **accumulates names append-only** as the same fixed-type fact recurs; names are never erased or transferred. |
| Championship Package — Belt | **Travels** each championship | Single physical artifact. Current holder = derived read = most recent champion. One custody event appends per championship; only the current champion holds it; prior holders retained in ledger. |
| Championship Package — Ring | No transfer; minted per champion (kept) | Each championship mints one ring, kept permanently by that champion. Rings accumulate across seasons; nothing transfers. Each ring's holder = that season's champion, permanently. |
| Championship Package — League Trophy | **Communal; never leaves the shared case** | Single perpetual artifact in the community trophy case. Each championship appends the new champion to it; it accumulates every champion's name append-only. Custody is communal (the league), not individual. |

No category uses points, leaderboards, live streaks, challenges, or any contest mechanic to move custody. Custody changes are derived from completed facts only.

---

## 1. Annual Trophies (12)

Custody: per-season, no transfer `[derived from category]`. Current holder = most recent certified season's recipient (derived read).

| # | Trophy | Qualification (completed fact) | Custody |
|---|---|---|---|
| 1 | The Belt | Season league champion. | **Traveling** — see Championship Package (CP). The Belt is one of three championship artifacts. |
| 2 | The Bridesmaid Bouquet | Season runner-up. | Per-season. |
| 3 | The Hammer | Started player whose score most often exceeded the winning margin across the season. | Per-season. |
| 4 | The Cannon | Highest single-week franchise score of the season. | Per-season. |
| 5 | The Sieve | Most points allowed during the regular season. | Per-season. **Tone-care.** |
| 6 | The Benchwarmer | Most points left on bench where the MFL optimal-lineup indicator said to start. | Per-season. **Tone-care.** |
| 7 | The Clairvoyant | Highest rate of correct lineup decisions vs the MFL optimal indicator. | Per-season. **Constitutional flag — cleared, see C2.** |
| 8 | The Climb | Largest improvement in win percentage from the prior season. | Per-season. See C4. |
| 9 | The Oracle | Franchise whose incorrect lineup decisions most often produced a loss they would have won with the optimal lineup. Measures consequence, not volume. | Per-season. See C2. |
| 10 | The Banner | Best regular-season record (highest regular-season win pct before playoffs). | Per-season. |
| 11 | The Engine | Highest total points scored during the regular season. | Per-season. |
| 12 | The Black Rose | Highest losing score of the regular season. | Per-season. **Tone-care.** |

---

## Championship Package (3 artifacts, one fact, three custody models)

A single completed fact — winning the season championship — produces three artifacts with three distinct custody ledgers. This is the marquee award. The Belt at #1 above is one of these three; The Ring and The League Trophy are added here as artifacts #36 and #37.

| CP | Artifact | Qualification (completed fact) | Custody |
|---|---|---|---|
| CP1 / #1 | The Belt | Season league champion. | **Traveling individual.** One physical belt. Only the current champion holds it; it passes to the next champion each season. Current holder = derived read = most recent champion. Append-only; prior holders retained. Carries a governed text surface (blank nameplate) for the attested champion + year. |
| CP2 / #36 | The Ring | Season league champion. | **Mint-and-keep individual.** Each champion receives their own ring, kept permanently. Rings accumulate across seasons; nothing transfers. Each ring's holder = that season's champion, permanently. |
| CP3 / #37 | The League Trophy | Season league champion (cumulative). | **Communal perpetual.** One perpetual trophy in the community trophy case; never leaves. Each championship appends the new champion's name; it accumulates every champion append-only. Custody is communal (the league), not individual. The Belt at #1 is the individual counterpart to this communal trophy. |

**Custody split rationale (ratified):** the communal League Trophy displays *all* winners cumulatively (Stanley-Cup model); the Belt *travels* to whoever currently holds the title (title-belt model); the Ring is *kept* by each champion forever (Super-Bowl-ring model). All three are append-only with derived current-holder reads, no gamification, no prediction. See Constitutional Note C7 for the attestation flag on these artifacts.

---

## 2. Positional Awards (6)

Custody: per-season, no transfer `[derived]`. All measure highest started points by position, season total.

| # | Trophy | Qualification (completed fact) | Custody |
|---|---|---|---|
| 13 | The Signal Caller | Highest started QB points, season total. | Per-season. |
| 14 | The Workhorse | Highest started RB points, season total. | Per-season. |
| 15 | The Deep Threat | Highest started WR points, season total. | Per-season. |
| 16 | The Tight Window | Highest started TE points, season total. | Per-season. |
| 17 | The Boot | Highest started K points, season total. | Per-season. |
| 18 | The Wall | Highest started DEF points, season total. | Per-season. |

---

## 3. Draft / Auction Awards (4)

Custody: per-season, no transfer `[derived]`. Auction-era data only.

| # | Trophy | Qualification (completed fact) | Custody |
|---|---|---|---|
| 19 | The Steal | Best points-per-dollar among started players. | Per-season. |
| 20 | The Burning Money | Worst points-per-dollar among significant bids. | Per-season. **Tone-care.** |
| 21 | The Patience Premium | Lowest average bid per started point across the whole draft. | Per-season. **Constitutional flag — cleared, see C3.** |
| 22 | The Whale | Highest single bid of the season. | Per-season. |

---

## 4. In-Season Acquisition Award (1)

| # | Trophy | Qualification (completed fact) | Custody |
|---|---|---|---|
| 23 | The Lifeline | Best in-season acquisition, measured by highest post-acquisition started points among players acquired via waivers, FAAB, or free agency. Retrospective only. | Per-season `[derived]`. |

---

## 5. Live Record Plaques (7)

Custody: **travels** when surpassed `[derived]`. Current holder = derived read off the ledger; prior holders retained.

| # | Trophy | Qualification (completed fact) | Current holder (derived, as of 2025) |
|---|---|---|---|
| 24 | The Cavallini Standard | All-time win-percentage leader. | (derived read — not baked in; see C1) |
| 25 | The Dynasty | Most championship titles. | Paradis' Playmakers, 4 |
| 26 | The Eternal Runner-Up | Most runner-up finishes without a championship. | Ben's Gods, 3 |
| 27 | The Executioner | Most blowout victories above the threshold margin. | (derived read) |
| 28 | The Iron Curtain | Best all-time points-allowed average across all regular seasons. | (derived read) |
| 29 | The Unbroken Chain | Longest consecutive playoff-appearance streak in digital history. | (derived read). See C5. |
| 30 | The Floor | Worst single-season record in digital history. | Brandon Knows Ball, 0-14 (2025). **Co-held on tie** (multi-valued read). See C6. **Tone-care.** |

---

## 6. Permanent Historical Plaques (5)

Custody: **never travels** `[derived]`. Single immutable append.

| # | Plaque | Qualification (fixed fact) |
|---|---|---|
| 31 | The Founder's Seal | All 10 members present since the digital era began. A statement of membership, not a competition. |
| 32 | The Inaugural Champion | Robb's Raiders, 2010. First champion of the digital era. |
| 33 | The One-Point Club | Championships decided by under 2 points. Cavallini 2013, KP 2019. |
| 34 | The Back-to-Back | Only franchise to win consecutive championships in the digital era. KP 2019-2020. |
| 35 | The Perfect Storm | Each 0-14 regular season in digital history. Names **accumulate (multi-listed)**, append-only. Brandon Knows Ball, 2025 (first listed). See C6. |

---

## Constitutional pass

**C1 — Current-holder must be a derived read, not part of the definition (applies to all live-record plaques).**
The source set bakes phrases like "Currently held by Paradis' Playmakers with 4 titles" and "Brandon Knows Ball, 0-14 in 2025" into the award *description*. Under the custody model, the current holder is a derived read off the append-only ledger and must NOT be hardcoded into the immutable qualification. The taxonomy above separates them: qualification stays pure ("most championship titles"); current holder is a labeled derived field. This keeps the definition immutable while the holder updates by derivation. **Action: hold this separation in the W.5 spec.**

**C2 — The Clairvoyant (crystal ball) and The Oracle: CLEARED. Not prediction.**
The Clairvoyant measures the *rate of lineup decisions that already matched the settled MFL optimal indicator*. The lineup was set, the games were played, MFL computed the optimal in hindsight, and we count how often the actual choice matched it. This is the "past call that turned out right (documented history)" case — entirely retrospective, evaluating completed facts. It is NOT an ongoing scored forecasting mechanic. The Oracle is the inverse (consequential wrong calls, also retrospective). Both clear the no-prediction rule.
**Implementation guardrail:** the Clairvoyant must read completed `(season, lineup, optimal)` facts only. It must never drift into a forward-looking "predicted accuracy" score, a running prediction counter, or any mechanic that asks managers to forecast and then scores the forecast. As specified, it is clean; the guardrail protects against implementation drift. The crystal-ball/sundial visuals are ceremonial irony, not a forecasting claim.

**C3 — The Patience Premium (scales): CLEARED. Not prediction.**
A pure retrospective ratio: total auction dollars divided by started points delivered, across a completed auction and completed season. Nothing forecasted, nothing scored forward. The scales visual is a balance/discipline metaphor. Clean.

**C4 — The Climb: not a live progress mechanic.**
Year-over-year win-pct improvement is a retrospective delta computed once from two completed seasons. It is a record, not a progress bar or engagement loop. Clean as specified; the spec must compute it from completed seasons only, not display it as live in-season momentum.

**C5 — The Unbroken Chain: "streak" = historical record, not gamification.**
Longest consecutive playoff-appearance streak in digital history is a documented record derived from completed seasons. This is distinct from a live "keep your streak alive" engagement mechanic, which the constitution forbids. Clean, provided it is computed from completed postseason facts and displayed as history — never as a live counter that incentivizes ongoing play.

**C6 — The Floor vs The Perfect Storm: same event, two artifacts, two custody rules. (RESOLVED)**
Both reference Brandon Knows Ball's 2025 0-14. The Floor is a **live record** (worst single-season record, travels if surpassed); per ratification it is **co-held on a tie**, so its current-holder read is multi-valued. The Perfect Storm is a **permanent plaque** that **multi-lists names**, accumulating one append per 0-14 occurrence. Consequence flagged: multi-listing necessarily retires the prior "the only 0-14" framing, since "only" is a claim a future fact could falsify. The qualification is now "each 0-14 regular season," which is append-stable and immutable per occurrence. They legitimately coexist: in 2025 both name the same franchise; a future 0-14 would co-hold The Floor and append a second name to The Perfect Storm. (A hypothetical worse-than-0-14 mark, only possible under a longer season format, would transfer The Floor but not touch The Perfect Storm, which is keyed specifically to 0-14.)

**C7 — "PFL" expansion on the Belt and Ring renders is generator-guessed, NOT attested. OPEN.**
The current Belt and Ring renders engrave **"Phony Football League"** as the expansion of PFL. This is the image generator's invention, not a confirmed fact — the exact same hazard class as the founding year, where the generator produced 1985 and Claude's arithmetic produced ~1986, while the attested truth was 1984. The PFL expansion must be **human-attested (attested by / attested on / basis)** before it is engraved into any permanent champion artifact. Until attested, "Phony Football League" is a hypothesis, and minting it into the Belt/Ring/League Trophy would embed an unverified claim into the league's most durable objects. The blank brass nameplate on the Belt is correctly handled — it is a governed text surface (attested champion + year), same pattern as the clubhouse banner. **Action: attest the PFL expansion before any championship artifact is finalized.**

All 37 artifacts derive from immutable append-only facts. No artifact introduces points, leaderboards, live streaks, or contest mechanics around custody. No artifact scores forecasts. The Championship Package's three custody models (traveling / mint-and-keep / communal perpetual) are all append-only with derived current-holder reads.

---

## Ratified decisions (folded into v1.1)

1. **Per-trophy steal rules — derived custody ratified.** Category-derived custody (from the system explainer) is authoritative for all 35. No per-trophy overrides.
2. **The Floor — co-held on tie.** The current-holder read is multi-valued: all franchises sharing the worst single-season mark co-hold simultaneously. Still a derived read off completed facts; append-only.
3. **The Perfect Storm — multi-listed, accumulating.** Each 0-14 regular season earns a name on the permanent plaque. Names accumulate append-only; nothing is erased or transferred. The "only" framing is retired (it was a claim a future fact could falsify); qualification reframed to "each 0-14 regular season."
4. **Championship Package — three artifacts, three custody models.** The championship now yields The Belt (traveling individual), The Ring (mint-and-keep individual, new #36), and The League Trophy (communal perpetual in the shared case, new #37). The Belt is reclassified from per-season to traveling. Artifact count is now 37.

## Standing requirements for the W.5 spec

- **C1 separation.** Current holder stays a derived read for every live-record plaque; baked-in holders are removed from qualification text.
- **C2 guardrail.** The Clairvoyant reads completed `(season, lineup, optimal)` facts only; no forward-looking predicted-accuracy mechanic.
- **C7 attestation.** The "Phony Football League" expansion of PFL must be human-attested before it is engraved into the Belt, Ring, or League Trophy. Until then it is a generator guess, not a fact.

## Remaining open items

- **Attestation (blocking for championship artifacts):** confirm or correct the PFL expansion (currently "Phony Football League" by generator guess) with provenance fields before minting any championship artifact. See C7.
- **Render assignment (design track, non-blocking).** The two cleat renders (front / sole) map to The Workhorse and The Boot; assignment TBD. Does not gate the taxonomy.

---

## Render reconciliation (informational)

Confirmed image-to-trophy matches from prior batches, against the canonical set:

- Wax seal, ten interlocking rings → #31 The Founder's Seal
- Portcullis in stone arch → #28 The Iron Curtain
- Bronze sundial, single hand (two views) → #9 The Oracle
- Life ring on coiled rope → #23 The Lifeline
- Blackened rose under glass cloche → #12 The Black Rose

Trophies without a confirmed render yet: The Hammer, Cavallini Standard, Dynasty, Eternal Runner-Up, Executioner, Unbroken Chain, Floor, Inaugural Champion, One-Point Club, Back-to-Back, Perfect Storm. Render production is a separate track and does not gate the taxonomy.
