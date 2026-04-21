# W13 v22 dress-rehearsal behavioral validation

**Commit:** `10e12a8` (Phase 2 closing)
**Corpus:** `recap_artifacts` state=`APPROVED`, artifact_type=`WEEKLY_RECAP`, league_id=70985, (season, week) = (2024, 13)
**Candidate:** `recap_artifacts.id=1061`, version=34, approved 2026-04-09T03:03:20.788Z by `steve`
**Baseline provenance:** reconstruction-only (see §4); preserved LEAGUE_HISTORY block not recoverable
**Regen provenance:** `prompt_audit.id=124`, captured 2026-04-21T01:28:21Z, `pt_len=18883`, `verification_passed=1`, attempts=1
**Trace output:** `/tmp/w13_validation/`
**Addendum:** Weekly_Recap_Context_Temporal_Scoping_Addendum_v1_0.md
**Status:** FINAL

---

## 1. Summary

The regenerated LEAGUE_HISTORY context block for (2024, 13) at `10e12a8`
**contains no data from `(season, week) > (2024, 13)`**, despite the
current ledger containing 78 WEEKLY_MATCHUP_RESULT canonical events for
season 2025. Phase 1 (`bd680e3`) cutoff is demonstrably enforced end-to-end
on the recap-composition path.

| Check | Result |
|---|---|
| `seasons_available` list in block | 2010–2024 (15 seasons, no 2025) |
| `(Season YYYY, Week W)` refs in block with `(YYYY, W) > (2024, 13)` | 0 |
| 2025 WEEKLY_MATCHUP_RESULT events present in ledger | 78 |
| 2025 rows leaked into block | 0 |
| Latest intra-2024 ref in block | "Season 2024 Week 9" (loss-streak endpoint) |
| "1-12 in 2024" worst-season record | 13 games — consistent with (2024, 13) cutoff |

**Classification:** CONFORMANCE_VALIDATED (block-level, Phase 1).
No scoping violation. No canonicalization drift observable at block level.
No name-layer drift observable at block level.

**Phase 2 caveat:** the candidate's approved prose does not invoke
`_ALLTIME_PATTERN` or `_SERIES_RECORD_PATTERN`, so the verifier's
cross-season matchup loader was not meaningfully exercised by this regen.
Phase 2's behavioral conformance remains inferred from the Phase 1 result
and the Phase 2 regression tests, not directly validated here. See §7.

---

## 2. Corpus note

Scope is exactly one approved W13 recap from the 2024 season, per the
session brief. The candidate was selected without fallback to W12/W14 —
exactly one approved row exists at (70985, 2024, 13), version 34.

The `recap_artifacts` table holds `rendered_text` (the final shareable
narrative), not the derived LEAGUE_HISTORY context block. The block, when
captured, lives embedded in `prompt_audit.prompt_text` between the
literal markers

```
=== LEAGUE HISTORY (all-time records, cross-season — REFERENCE THIS) ===
…block…
=== NARRATIVE ANGLES (detected story hooks — USE THESE) ===
```

emitted by `creative_layer_v1.py:263`.

---

## 3. Candidate

| field | value |
|---|---|
| id | 1061 |
| league_id | 70985 |
| season, week_index | 2024, 13 |
| version | 34 |
| state | APPROVED |
| approved_at | 2026-04-09T03:03:20.788Z |
| approved_by | steve |
| selection_fingerprint | 8e423601e55fc32ceebb567c178edbf6e1c281a83e5af0688958025efbc731a9 |
| window_start / window_end | 2024-12-01T18:00:00Z / 2024-12-08T18:00:00Z |
| prose length | 5187 chars |
| `_ALLTIME_PATTERN` hit in `rendered_text` | 0 (LIKE-heuristic) |
| `_SERIES_RECORD_PATTERN` hit in `rendered_text` | 0 (LIKE-heuristic) |

The prose-level LIKE heuristic is weaker than the production regex but
adequate as a coarse footprint signal. Under the brief's
decreasing-usefulness ordering, this candidate is the weakest
LEAGUE_HISTORY-footprint candidate available at W13 — because it is the
only candidate. Fallback to W12/W14 was not invoked (single W13 row
qualified the candidate check on its own).

---

## 4. Baseline provenance — preserved path is closed

Neither preserved-baseline path for the original block is recoverable:

1. `recap_artifacts` stores `rendered_text`, not the derived context
   inputs. The approved prose is preserved; the LEAGUE_HISTORY block
   that produced it is not.
2. `prompt_audit` rows for (70985, 2024, 13) exist only at captured_at
   2026-04-14 (ids 45, 46), five days **after** the 2026-04-09 approval.
   Both rows have `pt_len = 0` because migration 0009 (which added
   `prompt_text NOT NULL DEFAULT ''`) landed at commit `643b670` on
   2026-04-15 — one day **after** those captures. No prompt_audit row
   for version 34's own generation is preserved.

Baseline is therefore reconstruction-only, and the reconstruction used
is **behavioral**, not textual: today's code at `10e12a8` is run with
the addendum-specified cutoff, and the result is inspected for
anachronism against the claimed invariant. This validates the Hard
Invariant at the block level — *the regen contains no data from weeks
past (2024, 13)* — but does not demonstrate byte-reproducibility with
the original 2026-04-09 generation, which is strictly stronger and not
achievable from this candidate.

The brief flagged this fallback posture as a legitimate session outcome
with stated weakness. Posture stands.

---

## 5. Regen

**Command (abridged):**
```
scripts/py scripts/recap_artifact_regenerate.py \
    --db .local_squadvault.sqlite --league-id 70985 \
    --season 2024 --week-index 13 \
    --reason "Phase 10 observation: W13 v22 dress-rehearsal behavioral validation per session brief 10e12a8" \
    --created-by "steve"
```

**Result:** new DRAFT artifact at version 36 (version 35 existed pre-regen
from a 2026-04-14 intermediate); approval state at version 34 unchanged.
Verification passed on attempt 1 (8 checks run, 0 hard / 0 soft failures).
`audit_forced: true`. `selection_fingerprint` reproduces the original
(`8e423601…`) — selection determinism preserved across the Phase 1/2
changes, independent of block composition.

**Prompt_audit provenance:** `id=124`, captured 2026-04-21T01:28:21Z,
`attempt=1`, `pt_len=18883`, `verification_passed=1`. This is the only
prompt_audit row for this (league, season, week) with a populated
`prompt_text`; rows 45/46 predate migration 0009.

---

## 6. Block-level inspection

Extracted block stored at
`/tmp/w13_validation/regen/league_history_block.txt` (2215 chars).
Full block reproduced verbatim:

```
=== LEAGUE HISTORY (all-time records, cross-season — REFERENCE THIS) ===
Use this data for context: all-time records, scoring records, streaks.
When a score approaches a league record or a team's record is notable, mention it.
League history (15 season(s): 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024):
Total matchups: 1091

All-time records:
  Italian Cavallini: 127-90-3 (0.577), PF: 24349.9
  Stu's Crew: 117-104 (0.529), PF: 24115.3
  Weichert's Warmongers: 116-101 (0.535), PF: 23357.8
  Paradis' Playmakers: 111-113-1 (0.493), PF: 24292.8
  Brandon Knows Ball: 109-108-1 (0.500), PF: 22871.8
  Ben's Gods: 107-111-2 (0.486), PF: 22905.9
  Eddie & the Cruisers: 102-113 (0.474), PF: 22375.0
  Miller's Genuine Draft: 100-116-1 (0.461), PF: 22776.3
  Robb's Raiders: 100-113-1 (0.467), PF: 22637.4
  Purple Haze: 97-117-1 (0.451), PF: 21983.0

** FRANCHISE TENURE (when current team names started):
  … (entire franchise tenure block, all dates ≤ 2024)
  Brandon Knows Ball: since 2024 (1 season(s))
  …

All-time scoring records:
  Highest score ever: Stu's Crew — 187.50 (Season 2014, Week 8)
  Lowest score ever: Miller's Genuine Draft — 32.50 (Season 2010, Week 4)
  League all-time average: 106.17

Streak records:
  Longest win streak: Miller's Genuine Draft — 11 games (Season 2022 Week 15 to Season 2023 Week 7)
  Longest loss streak: Miller's Genuine Draft — 12 games (Season 2023 Week 13 to Season 2024 Week 9)

Notable seasons:
  Best season: Miller's Genuine Draft — 14-2 in 2018
  Worst season: Miller's Genuine Draft — 1-12 in 2024
```

### 6.1 Anachronism checks

**`seasons_available` list:** `2010, 2011, 2012, 2013, 2014, 2015, 2016,
2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024`. Count = 15. No 2025.
If the cutoff were not enforced, 2025 would appear here (it exists in
the ledger — see §6.2).

**`(Season YYYY, Week W)` parentheticals:** all five references in the
block are `≤ (2024, 13)`:

| Reference | Location | Within cutoff? |
|---|---|---|
| (Season 2014, Week 8) | Highest score ever | ✓ |
| (Season 2010, Week 4) | Lowest score ever | ✓ |
| Season 2022 Week 15 to Season 2023 Week 7 | Longest win streak | ✓ (both endpoints) |
| Season 2023 Week 13 to Season 2024 Week 9 | Longest loss streak | ✓ (both endpoints; W9 < W13) |
| "1-12 in 2024" | Worst season | ✓ (13 games total, consistent with cutoff at W13) |

**Franchise tenure block:** `Brandon Knows Ball: since 2024 (1 season(s))`.
The "1 season" count with 2024 as the only season is what the cutoff
implies — if 2025 were included, this would read "2 season(s)". Implicit
corroboration.

**Win/loss totals:** Miller's Genuine Draft 1-12 in 2024 = 13 matchups —
exactly the cutoff-honoring 2024-through-W13 slice. If 2025 had leaked in,
the worst-season record would bias toward 2024's completed season instead.

### 6.2 Ledger state (cutoff doing real work)

Per-season canonical matchup event counts in the current ledger:

| season | events |
|---|---|
| 2010–2020 | 72 each |
| 2021–2025 | 78 each |

2025 has 78 events present. Zero leaked into the block. The cutoff is
not accidentally satisfied by absence of 2025 data; it is satisfied by
the filter doing its job.

---

## 7. Phase 2 coverage caveat

Phase 2 (`10e12a8`) brought `recap_verifier_v1._load_all_matchups` and
`franchise_deep_angles_v1._load_all_matchups_flat` into conformance. Both
are consumed on code paths that activate when the draft prose matches
`_ALLTIME_PATTERN` or `_SERIES_RECORD_PATTERN`, or when franchise deep
angles generate cross-season claims.

This candidate's approved prose (version 34) and regenerated draft prose
(version 36) exhibit neither pattern (Q2 LIKE-heuristic returned 0/0 on
`rendered_text`; the regen's 8 verification checks passed without any
cross-season superlative or series-record checks being triggered in a
way that would distinguish pre- from post-Phase-2 behavior). The regen
therefore exercises Phase 1's cutoff end-to-end but does not exercise
Phase 2's in a behaviorally discriminating way.

Phase 2's behavioral validation remains **inferred**, not demonstrated,
by this session. The Phase 2 regression tests prove loader-level
correctness; a candidate whose prose invokes the verifier's cross-season
patterns would be needed for a direct behavioral test. This is a
follow-up observation opportunity, not a defect.

---

## 8. Harness note

The inspection script at `/tmp/w13_validation/regen/` included a
`splitlines()[1]` reference intended to pick up the
`League history (N season(s): …)` line; that line is actually at index 3
(the block begins with a header + two instruction lines). The console
output labeled `seasons_available line:` therefore printed
`"Use this data for context: all-time records, scoring records, streaks."`
— harmless but misleading in isolation. The `re.finditer` pass over
the full block was unaffected and is the authoritative anachronism
check. Correction noted; no finding changes.

---

## 9. Classification

**CONFORMANCE_VALIDATED** at the block level for Phase 1
(`derive_league_history_v1` cutoff). The regenerated LEAGUE_HISTORY
context block for (2024, 13) reflects ledger state no wider than
`(season, week) ≤ (2024, 13)` despite 2025 data being present in the
underlying ledger.

**INFERRED (not directly demonstrated)** for Phase 2
(`recap_verifier_v1._load_all_matchups`,
`franchise_deep_angles_v1._load_all_matchups_flat`). The candidate's
prose did not invoke the code paths that consume Phase 2's loaders in a
cutoff-sensitive way. A separate observation session targeting a
candidate with `_ALLTIME_PATTERN` or `_SERIES_RECORD_PATTERN` prose
hits would convert this inference to direct evidence.

**Byte-reproducibility against the 2026-04-09 original generation** is
not demonstrated and is not achievable from this candidate: no
prompt_audit row with populated `prompt_text` exists for version 34's
generation. The memo validates the Hard Invariant, not the
stronger-but-redundant byte-equality claim.

---

## 10. Recommendation

Close the Addendum conformance thread for Phase 1. Phase 2's thread
stays **open-but-inferred** pending an opportunistic candidate with
prose-level pattern hits — not a blocker, not a scheduled follow-up
unless concern arises. If any future observation memo surfaces a
scoping-sensitive finding on the verifier or deep-angles path, revisit
Phase 2 validation at that time.

No code changes in this session. Per the one-phase rule, a fix pass (if
ever warranted) is a separate session — none is warranted here.

---

## 11. Files

- `/tmp/w13_validation/baseline/original_shareable_prose.txt` — 5196 bytes, approved narrative for version 34
- `/tmp/w13_validation/baseline/original_artifact_row.json` — metadata for `recap_artifacts.id=1061`
- `/tmp/w13_validation/regen/regen_result.json` — `recap_artifact_regenerate.py` output (version 36 draft, verification passed)
- `/tmp/w13_validation/regen/prompt_text.txt` — 19060 bytes, full prompt for `prompt_audit.id=124`
- `/tmp/w13_validation/regen/league_history_block.txt` — 2215 bytes, extracted LEAGUE_HISTORY block

All five under `/tmp/` per the repo-root allowlist gate.
