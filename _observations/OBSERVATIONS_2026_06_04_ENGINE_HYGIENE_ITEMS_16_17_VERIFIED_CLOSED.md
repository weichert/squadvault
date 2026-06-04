# Engine-Hygiene Items 16 + 17 — Verified Closed; 2021 Draft Gap Characterized; Stale-Open Pattern Recurrence

**Date:** 2026-06-04
**Status:** Observational. No tier. Not registered in the Documentation Map.
**Engine HEAD at verification:** `4fb8ec9`.
**Trigger:** A bounded engine-hygiene session picked roadmap items 17 and 16 from the 2026-06-02 session brief. Re-grounding against the repo before any edit found item 17 already complete, item 16's drift-sweep already complete, and item 16's one genuine remainder (the 2021 DRAFT_PICK gap cause) resolvable by a read-only live-DB diagnostic, which this session ran. This memo records the corrected statuses with evidence, characterizes the 2021 gap, and flags the recurrence pattern.

**Predecessors / anchors:**

- `OBSERVATIONS_2026_05_14_PHASE_11_A2_ANCHOR_REVOCATION.md` (`e5fbb94`) — item 17 finding (player 9988 is Antonio Brown, WR, not Mahomes).
- `97498fa` — A2 test anchor purge (item 17 code-side correction).
- `OBSERVATIONS_2026_05_14_PHASE_11_A2_SPEC_TEXT_AMENDMENT.md` — item 17 spec-text correction record (section 8.4: "the 2026-05-14 A2 anchor-correction set is complete").
- `OBSERVATIONS_2026_05_14_PHASE_11_ROADMAP_SEASONS_COUNT_REVISION.md` — item 16 compound-drift reconciliation.
- `OBSERVATIONS_2026_05_16_PHASE_11_ROADMAP_V2.md` — item 16 figure correction ("no surface carries '17 seasons'; the legacy approximation is fully retired").
- `OBSERVATIONS_2026_05_02_PRIORITY_LIST_AMENDMENT.md` — stale-open drift doctrine and the four-instance threshold.

---

## 1. What this memo records

Items 16 and 17 were carried OPEN by both the 2026-06-02 session brief and userMemories. The repo at `4fb8ec9` shows both closed at every layer that takes an edit; item 16's only genuine open thread (the 2021 gap cause) is characterized below. Recorded so the next brief drops both.

## 2. Item 17 (A2 Cavallini/Mahomes anchor) — closed

**Test half — done, verified at HEAD.** No `test_cavallini_mahomes_2018_qb_anchor_regression` exists. The test is `test_qb_position_record_computed_independently_of_overall` in `Tests/test_draft_history_vault_aggregations_v1.py`; file-level and test docstrings carry the corrected Antonio-Brown-not-Mahomes note with a pointer to the revocation memo. Landed at `97498fa`.

**Memo-correction half — done, intentionally not an in-place edit.** Corrected text for all eight A2-spec sites lives in the spec-text-amendment memo, which is append-only per the A2 spec's section 7 and folds in at promotion or revision-point. The lines in `OBSERVATIONS_2026_05_13_PHASE_11_A2_SPECIFICATION.md` still reading "Cavallini / Mahomes 2018 anchor" are supposed to stay as written; editing them in place would violate the established supersession-then-fold-in pattern. No sanctioned edit exists for item 17.

## 3. Item 16 (seasons-count compound drift sweep) — sweep closed, gap characterized

**Sweep half — done.** The canonical surface doc was reconciled by the 05-14 seasons-count revision and the 05-16 Roadmap v2, which retired "17 seasons" and fixed per-surface counts (A1=16, A2=7, A3=16, FAAB window=4). `docs/` carries zero seasons-count claims. `src/` carries none (the "17" in `auction_draft_angles_v1.py` is roster spots; "2018-2025" is a correct era range, not a count). Residual "17 seasons" mentions are confined to append-only historical `_observations/` memos and are not to be swept.

**The 2021 DRAFT_PICK gap — characterized (2026-06-04).** The revision memo named three hypotheses for 2021's zero DRAFT_PICK events: snake-format-2021, a renamed draft event_type, or an ingest gap. A read-only `memory_events` diagnostic against the live DB (league 70985) settles it:

- 2021 ingested normally overall: 2,500 events, in line with 2020 (2,630) and 2022 (2,681). **Not a wholesale ingest gap.**
- 2021 has zero DRAFT_PICK and zero draft-shaped events of any name (DRAFT/PICK/AUCTION/SNAKE all empty for 2021; present for 2020 and 2022). **Not a renamed/format-change event_type.**
- The 2020-to-2021 event_type breakdown shows the FAAB switch: 2021 introduces `TRANSACTION_BBID_AUTO_PROCESS_WAIVERS` (13), `WAIVER_BID_AWARDED` (41), and `TRANSACTION_LOAD_ROSTERS` (11, approximately one per franchise) — none present in 2020 — while the legacy `TRANSACTION_WAIVER` collapses from 43 to 2. Matchups, player scores, trades, and free agents are comparable year over year.

**Characterization:** 2021 has zero DRAFT_PICK events because the 2021 roster construction was ingested as a bulk `TRANSACTION_LOAD_ROSTERS` event set rather than as enumerated draft picks, coincident with the league's 2021 switch to BBID/FAAB waivers. The DRAFT_PICK absence is a representation difference in that one season, not a wholesale ingest gap and not a renamed draft event_type. The per-pick detail for 2021 (and thus whether the underlying draft was snake/auction/keeper) is not recoverable from this substrate, but the cause of the DRAFT_PICK absence — what item 16 asked for — is now characterized. A2's auction substrate remains correctly stated as 7 empirical seasons (2018-2025 minus 2021).

**Diagnostic record (read-only, league 70985):**

| season | total_events | draft_picks |
|---|---|---|
| 2019 | 2367 | 150 |
| 2020 | 2630 | 180 |
| 2021 | 2500 | 0 |
| 2022 | 2681 | 170 |
| 2023 | 2711 | 170 |

2020-vs-2021 new/absent event types: DRAFT_PICK 180 to 0; TRANSACTION_BBID_AUTO_PROCESS_WAIVERS 0 to 13; WAIVER_BID_AWARDED 0 to 41; TRANSACTION_LOAD_ROSTERS 0 to 11; TRANSACTION_WAIVER 43 to 2.

## 4. Fifth and sixth stale-open instances

The priority-list amendment memo enumerated four stale-brief-causes-false-start instances and set a threshold: a fourth is the signal to redesign the open-items mechanism rather than amend in place. Item 17 (carried open; closed at `97498fa` + the amendment memo) is the fifth. Item 16's sweep (carried as a pending sweep; executed at 05-14 + 05-16) is the sixth. Both surfaced on the first two items checked, in a session that picked them specifically because they looked bounded and ready. The failure mode is unchanged: a status assertion propagated forward without re-derivation against the repo.

## 5. Recommendation — verify-stamps on the open-items list

The amendment memo already prescribed the fix; it has not been applied to the session-brief open-items list. Recommend the next brief carry, for each open item: a commit hash or named in-repo artifact for "closed" claims, and a runnable check (grep, path, test, gate, or query) for "open" claims. Items that can supply neither are re-grounding candidates, not execution candidates. This is how the brief is authored, not a code change.

A standing observation, not a recommendation: items 16 and 17 going two-for-two already-done indicates the engine has largely caught up to the surface state. Remaining "engine hygiene" items are likely to keep resolving as done-or-recorded; the genuinely-open work is product-surface side.

## 6. Cross-references

- `e5fbb94`, `97498fa`, `OBSERVATIONS_2026_05_14_PHASE_11_A2_SPEC_TEXT_AMENDMENT.md` — item 17 closure chain.
- `OBSERVATIONS_2026_05_14_PHASE_11_ROADMAP_SEASONS_COUNT_REVISION.md`, `OBSERVATIONS_2026_05_16_PHASE_11_ROADMAP_V2.md` — item 16 sweep closure.
- `OBSERVATIONS_2026_05_13_PHASE_11_A2_SPECIFICATION.md` — append-only spec (sites intentionally uncorrected in place).
- `OBSERVATIONS_2026_05_02_PRIORITY_LIST_AMENDMENT.md` — drift doctrine and the four-instance threshold.
