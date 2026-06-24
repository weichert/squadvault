# Championship Week 17 - Canonicalization Adjudication (the week 17 = 18 phantom) - DRAFT

**Prepared:** 2026-06-23. **Session type:** DECIDE (adjudication). **Anchor:** engine `main` `7c588d5`.
**Purpose:** (1) record the week-17 championship ruling on the governance record, with its evidence; (2) adjudicate a canonical-layer rule that collapses the 2021+ week-18 phantom once, for all consumers, without violating append-only; (3) fix the now-divergent championship-week surfaces that PR #8 left behind.
**Conforms to:** the Canonicalization Policy Addendum v1.0 (deterministic-and-total; ephemeral; scoring-function-as-sole-authority; reconstructability - "canonicalize twice over the same `memory_events` ledger yields identical `canonical_events`").
**Status:** RATIFIED 2026-06-23 (all four decision points). Census-amended - see Section 9, which supersedes the section-5 sequencing and the section-8 harm-B claim.

## 1. The week-17 ruling (retroactive governance record)

**Fact (ratified by founder, evidence-backed):** for the 2021+ expansion era, this league's championship is **week 17**; week 18 is MFL's trailing/padding copy (a byte-identical duplicate of the week-17 title game), not a distinct event.

**Evidence (PR #8 close-out):** the playoff bracket contracts 10 -> 8 -> 4 -> 2 and ends at week 17, identical across all five expansion seasons (2021-2025). A 10-team single-elimination-style bracket terminating at week 17 is dispositive: the title is decided at week 17. Week 18 carries the same two franchises and the same scores - a duplicate, not a follow-on game.

**Scope:** 2021+ only. 2010-2020 championship = week 16 (shorter season, no phantom); untouched by everything below.

This ruling changed a core temporal primitive (`_champ_week(2021+): 18 -> 17`, shipped in PR #8) but until now lived only in a code diff. This memo puts the *why* on the append-only record so no future session has to reverse-engineer it from `_champ_week` line 60.

## 2. The problem PR #8 left: a divergent, partly-buggy multi-surface definition

The championship-week notion is encoded in MULTIPLE surfaces. PR #8 corrected one and left the others:

| Surface | Says (2021+) | State |
|---|---|---|
| `scripts/gen_season_award_winners.py` `_champ_week` (line 60) | **17** | correct (PR #8) |
| `recap_verifier_v1.py` `_CHAMPIONSHIP_WEEK_BY_ERA` (line ~3600) | **18** | STALE - two harms below |
| `hall_of_fame_render_v1.py` (`championship_week`) | (sources its week elsewhere) | CENSUS - confirm |
| LEAGUE_HISTORY / recap temporal scoping | (unknown) | CENSUS - confirm |

**Verifier harm A - latent break on collapse.** The verifier checks championship claims at week 18 and currently passes only because the week-18 phantom mirrors week 17. Collapse the phantom (section 4) while the verifier still expects week 18 and championship verification breaks (week 18 goes empty). The two are coupled; they must move together.

**Verifier harm B - active bug today.** `_season_record(..., regular_season_only=True)` excludes `m.week == champ_week`, which for the verifier is **18**. So for 2021+ it excludes the phantom (week 18) but KEEPS week 17 - the real title game - inside the "regular season" record. The championship leaks into regular-season records exactly where it should be excluded. This is shipped and wrong now (build to confirm against live data). It is the clearest reason the week-17 ruling must propagate to every surface, not just the awards.

## 3. Two coupled problems, one adjudication

- **(A) Definitional consistency:** every surface that encodes a championship week must agree - week 17 for 2021+, week 16 for 2010-2020.
- **(B) The phantom itself:** week 18 duplicates week 17 in the canonical matchup/player streams. Today each consumer works around it (sub-wave 1 deduped it in the generator; PR #8 relabeled it). That is per-consumer patching of a data-layer fact - the same anti-pattern as the 2018 contamination. Fix it once, at the fact.

## 4. The adjudicated rule

**R1 - Collapse the phantom at the canonical layer (fix-at-the-fact).** In the 2021+ era, a week-18 matchup (and its player-week rows) that is byte-identical to the week-17 record is a phantom duplicate and is suppressed from the canonical view (`v_canonical_best_events` and the matchup/player streams consumers read). Conditions, binding:
- **Append-only preserved:** the raw `memory_events` ledger retains BOTH rows unchanged; only the canonical *view* serves the deduped truth. Nothing is deleted from the ledger.
- **Byte-identical only:** the collapse fires solely when week 18 duplicates week 17 (same franchises, same scores). A genuinely distinct post-title week-18 happening (the "report league happenings after our championship" case) is KEPT - silence-over-speculation does not license dropping a real event.
- **Deterministic / reconstructable:** the rule is total and deterministic; re-canonicalizing the same ledger yields identical canonical output (Canonicalization Policy reconstructability invariant).
- **Semantic, not structural:** the existing `action_fingerprint` dedup does not catch this (week 17 vs 18 differ in the week field), so R1 is a documented canonicalization SEMANTIC rule, registered on the Canonicalization surface.

**R2 - Align every championship-week surface to the ruling.** All surfaces from the section-2 census set to week 17 (2021+) / 16 (2010-2020): the verifier era table AND its default fallthrough, hall_of_fame, LEAGUE_HISTORY/recap scoping, and any others the census finds. After R2, the award generator's local dedup (and PR #8's relabel) become redundant and can be retired in favor of the canonical-layer truth.

## 5. Sequencing (the coupling is load-bearing - do not invert)

1. **Census first** (build, read-only): enumerate EVERY surface that encodes a championship/last week OR works around the week-18 phantom. Do not assume the verifier + hall_of_fame are the only two - this session has been burned three times by assuming where a value lived. (event-type name, the filter coupling, the gate surfaces.)
2. **R2 before/with R1:** align all surfaces to week 17 FIRST (or atomically with R1). Collapsing the phantom (R1) while any surface still expects week 18 breaks that surface (verifier harm A).
3. **R1:** land the canonical-layer collapse.
4. **Retire the workarounds:** drop the award-generator local dedup and confirm the awards are byte-identical to their current (correct) values, now sourced from the canonical truth rather than a per-consumer patch.
5. **Regression-prove:** verifier championship + record claims correct for 2021+ (harm B fixed); B1 #33 and sub-wave-1 awards byte-identical; 2010-2020 entirely untouched.

## 6. Boundaries / non-goals

- 2010-2020 is untouched (week 16, no phantom).
- No architecture change: R1 extends the existing canonicalization framework with one documented semantic rule; it does not alter the layer structure or governance model.
- Append-only is preserved absolutely - the ledger keeps every row; only the canonical view dedups.
- No analytics / optimization / engagement / prediction. This is a correctness/consistency fix.
- The 2021 manual import and the remaining B2 sub-waves are unrelated and unblocked by this.

## 7. Decision points for ratification

1. **Record the week-17 ruling + scope** (section 1) on the governance log.
2. **Ratify R1** - canonical-layer collapse of the 2021+ week-18 phantom, byte-identical-only, append-only-preserving, deterministic, registered as a canonicalization semantic.
3. **Ratify R2 + the sequencing** - align every championship-week surface to the ruling, BEFORE/atomic-with R1; retire the per-consumer workarounds after.
4. **Approve a census-first build** - enumerate all affected surfaces before changing any, then implement R2 -> R1 -> retire -> regression-prove, as its own EXECUTE unit.

## 8. Provenance / status

- Inputs: the PR #8 championship-week fix and its bracket evidence; the live verifier/generator divergence read at `7c588d5`; the Canonicalization Policy Addendum v1.0.
- DRAFT. No code, no writes. On ratification, this is one census-first EXECUTE unit (the verifier harm B alone justifies it independent of the phantom collapse).

## 9. Census amendment - RATIFIED 2026-06-23

The census (`CHAMP_WK17_CENSUS_REPORT.md`, read at `7c588d5`) halted under stop-condition (a): it surfaced material beyond this memo. Findings and the rulings on them, all ratified:

**9.1 - A fifth surface: `gen_franchise_records.py:52` `_champ_week=18`.** Not in the section-2 table. It charges the week-17 title into 2021+ regular-season `points_against`, and it feeds `franchise_season_records`, which is **already seeded to prod and feeds the live Wave A plaques** (the Sieve et al.). **Ruling:** the engine fix is IN SCOPE for this unit - leaving it on week 18 reships the exact divergence we are closing. Align to 17, regenerate `franchise_season_records` engine-side, and report the full value diff plus an explicit Wave-A-plaque outcome-flip check.

**9.2 - The data-driven surfaces are R1-dependent, not R2 targets.** `hall_of_fame_aggregations`, `franchise_deep_angles`, `championship_timeline`, `season_context` derive the championship week via `min(playoff_week_counts, key=(count, -w))`; the `-w` tiebreak picks week 18 today and self-corrects to 17 once R1 removes the phantom - no code change. The section-2 "align hall_of_fame" line is withdrawn; hall_of_fame is R1-dependent, not an align target. R2 covers only the hardcoded constants: award gen (done), verifier era-table + default, and `gen_franchise_records`.

**9.3 - Harm B requires R1 AND R2 jointly. (Supersedes section 8.)** The section-8 claim that harm B is fixable "independent of the phantom collapse" is WRONG. With `champ_week=17` but the phantom still present, the week-18 copy leaks into the regular-season record instead of week 17 - still wrong. Demonstrated: 2024 franchise 0005 regular-season record is 11-6 today; R2-alone leaves it 11-6; only R1+R2 yields the correct 10-6. This strengthens the atomic case.

**9.4 - Sequencing is ATOMIC, not "R2 before R1." (Supersedes section 5 step 2.)** Because the data-driven surfaces flip only at R1 and harm B needs R1+R2 jointly, an "R2-first" interim leaves the championship surfaces mutually inconsistent. **Ruling:** R1 and R2 land atomically.

**9.5 - A2 premise holds.** All five expansion seasons: week-18 matchups and player-weeks are byte-identical to week 17. No non-identical phantom; R1's blanket suppression is safe and stays conservative. (No HALT on condition (b).)

**9.6 - Prod data + plaque-flip handling. (Founder ruling.)** Aligning `gen_franchise_records` moves shipped prod values (e.g., 2024 0005 PA 1934.75 -> 1798.95; 0002 2135.0 -> 1986.1; comparable each expansion year). The corrected fact stands - the record follows the true championship week, not the bug. The prod re-seed of `franchise_season_records` is a SEPARATE gated follow-on. **If any Wave A plaque changes holder for any expansion season, the build HALTS pre-merge and surfaces the specific flip (plaque, season, old -> new holder, underlying delta); the founder sees it first and decides case-by-case how it lands (e.g., a league-facing correction note) before merge and before prod apply.** No pre-authorization of plaque flips.
