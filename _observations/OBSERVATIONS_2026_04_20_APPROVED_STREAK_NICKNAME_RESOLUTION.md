# Approved-recap verifier pass after nickname layer

**Commit:** 2ce7356
**Mechanism source:** 84bfd89 (Option B: nickname override layer — migration 0010 + pass 4a in `_build_reverse_name_map`)
**Seed source:** 2ce7356 (Alt A: commissioner curation, 10 rows in `franchise_nicknames` for league 70985)
**Scan:** 2026-04-20, `scripts/verify_season.py` against 2025/70985 and 2024/70985 on `.local_squadvault.sqlite`
**Capture:** `/tmp/alt_d/verify_2025.txt`, `/tmp/alt_d/verify_2024.txt`
**Corpus:** `recap_artifacts` state=`APPROVED`, artifact_type=`WEEKLY_RECAP`, league_id=70985
**Status:** FINAL

---

## Summary

Pass 4a is live for league 70985. The attribution-class failures
enumerated in `OBSERVATIONS_2026_04_20_APPROVED_STREAK_PROSE_CLASSIFICATION.md`
(F1, F2, F3 — MISATTRIBUTION, rooted in missing Michele / Pat aliases)
are absent from the current output. Remaining failures are
LEGITIMATE_CATCH class — the verifier correctly flagging real model
errors that made it past human review.

Category counts across 35 approved recaps (17 from 2024 + 18 from 2025):

| | 2024 | 2025 | Total |
|---|---|---|---|
| Weeks scanned | 17 | 18 | 35 |
| Weeks passed | 14 | 16 | 30 |
| Weeks failed | 3 | 2 | 5 |
| Hard failures | 3 | 4 | 7 |
| Soft warnings | 0 | 1 | 1 |

Hard failures by category: STREAK=3, SERIES=4.

---

## Mechanism proof

From `_build_reverse_name_map` applied to live 2025 data at 2ce7356:

```
name_map size: 10
owner_map size: 0  (empty — as documented in 04-21 preread)
nickname_map size: 10

Nickname-contributed aliases (pass 4a):
  stu        -> 0001
  kp         -> 0002
  pat        -> 0003
  eddie      -> 0004
  steve      -> 0005
  miller     -> 0006
  robb       -> 0007
  ben        -> 0008
  michele    -> 0009
  brandon    -> 0010
```

All ten curated nicknames resolve. The four load-bearing cases from the
04-21 preread — `kp → 0002`, `pat → 0003`, `steve → 0005`,
`michele → 0009` — are the aliases that pass 4b would have produced
from `owner_name` if the column were populated; the nickname layer
delivers them via pass 4a without requiring owner_name backfill.

---

## Classification against 2026-04-20 APPROVED_STREAK memo

The 04-20 memo enumerated 6 STREAK failures at commit 07d752b:

- **F1, F2, F3** — MISATTRIBUTION (verifier-side). Root cause per the
  04-21 preread: `reverse_name_map` had no alias for Michele (F1/F2) or
  Pat (F3), so proximity search fell through to a wrong-but-mapped
  franchise.
- **F4, F5, F6** — LEGITIMATE_CATCH. Real model errors the verifier
  correctly fired on.

Current comparison:

| Class | Expected disposition | Observed in 2ce7356 output |
|---|---|---|
| F1-F3 MISATTRIBUTION | MECHANISM_RESOLVED | **3 of 3 resolved** — no attribution-class rows in current output |
| F4-F6 LEGITIMATE_CATCH | STILL_OPEN | STILL_OPEN — 3 or more legitimate-catch rows still firing (exact correspondence subject to corpus drift; see Caveats) |

The strongest single evidence: the 04-20 memo's F1 row was
2024 W4 "Miller's Genuine Draft has/had a 3-game win streak,
actual 0/0." Week 4 of the 2024 scan at 2ce7356 passes all 8 checks.
The model wrote "Michele's been quietly building a three-game win
streak" — correct prose. The verifier now resolves `michele → 0009`,
proximity attribution lands on Italian Cavallini, canonical streak
check passes.

---

## Current failures (STILL_OPEN / LEGITIMATE_CATCH class)

All seven hard failures in the current output are correct-attribution
+ model-error. Every referenced franchise is resolvable via pass-2
first-word alias alone; none depend on pass 4a. Table:

| Season | Week | Category | Prose claim (evidence) | Franchise | Pass-2 alias | Note |
|---|---|---|---|---|---|---|
| 2024 | 8 | SERIES | Ben vs Miller 7-1 (actual 14-16, 30 meetings) | 0008, 0006 | `ben`, `miller` | Invented series record |
| 2024 | 9 | STREAK | Ben's Gods 4-game win (actual 0 current / 1 pre-week) | 0008 | `ben` | Invented streak |
| 2024 | 12 | SERIES | Purple Haze vs Warmongers 8-4 (actual 13-12, 25 meetings) | 0003, 0005 | `purple`, `weichert` | Invented series record |
| 2025 | 5 | STREAK | Stu's Crew 4-game losing streak (actual 0 current / 2 pre-week) | 0001 | `stu` | Overstated |
| 2025 | 16 | STREAK | Paradis 5-game win streak (actual 7 current / 6 pre-week) | 0002 | `paradis` | Understated |
| 2025 | 16 | STREAK | Warmongers 3-game win streak (actual 5 current / 4 pre-week) | 0005 | `weichert` | Understated |
| 2025 | 16 | SERIES | Paradis vs Warmongers 12-2 (actual 13-16, 29 meetings) | 0002, 0005 | `paradis`, `weichert` | Invented series record |

Soft warning (2025 W11 SPECULATION "kicking himself") is unchanged
behavior, not relevant to Alt A/D scope.

Attribution-dependency check: every failing row attributes to a
franchise whose pass-2 first-word alias was available before the
nickname layer landed. None of these failures would change disposition
if pass 4a were disabled. This is the expected shape for
LEGITIMATE_CATCH class failures.

---

## Caveats

1. The 04-20 memo's corpus was a snapshot at commit 07d752b on
   2026-04-19. The approved corpus at 2ce7356 may have drifted — new
   weeks approved, old weeks re-rendered — so exact row-by-row
   correspondence from F1-F6 to current-output rows is inexact.
   The classification above uses category + franchise + claim shape
   as the correspondence anchor.
2. Attribution correctness is inferred from (a) the verifier's
   evidence string naming the canonical franchise and (b) the
   mechanism-proof alias dump. A prose-level confirmation for each
   currently-failing row is scope for a deeper follow-up if desired;
   not required for this memo's resolution claim.
3. The 2025 W16 double-STREAK (Paradis / Warmongers) and the
   2025 W16 SERIES failure cluster in the same week, same matchup.
   The model appears to have conflated overall-season standings with
   head-to-head and understated streaks in a single recap. That's a
   distinct failure pattern from the 04-20 memo's rows, not a
   regression; scope for future observation if it repeats.

---

## Forward-look

- The nickname mechanism's first payoff — eliminating the
  MISATTRIBUTION class from F1-F3 — has landed. Mechanism shipped in
  84bfd89, content shipped in 2ce7356, resolution observed here.
- No fix is proposed for the 7 STILL_OPEN rows. These are the
  verifier correctly catching real claim-vs-canonical discrepancies
  in shipped recaps. Standard dispositions (regenerate with current
  mechanism, or accept as historical record) are commissioner-level
  decisions outside the architecture-frozen Phase 10 scope.
- Next candidate observation: if any future approved recap fires a
  STREAK-class failure whose attribution franchise is NOT pass-2-
  resolvable (e.g., the model writes "Michele had a 3-game win
  streak" as a standalone sentence with no Italian Cavallini context),
  that would exercise pass 4a directly and provide the second-order
  load-bearing proof. None observed in the 2024/2025 corpus at
  2ce7356.
