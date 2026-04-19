# OBSERVATIONS_2026_04_18 — STREAK id=7 already resolved by b58b1a2

## Summary

STREAK id=7 — captured 2026-04-14 against 2025 W4 prose
"Robb snapped his losing streak with a 119.05-98.60 win over Brandon" —
was classified as verifier-side pass-2 misattribution in the a8dd37b
backlog annotation. Scoping at HEAD confirms:

- The captured failure was real and verifier-side at capture time.
- The documented mechanism (len<5 first-word filter excluding "robb")
  was correct for the **capture-time** verifier (b55cc17).
- Commit **b58b1a2** (2026-04-15 21:10 PDT, ~36h after capture) relaxed
  that filter from `< 5` to `< 3` as part of unrelated PLAYER_FRANCHISE
  alias-coverage work. That change incidentally resolved id=7.
- At HEAD (a8dd37b), row 7's prose no longer reproduces the failure:
  `_find_nearby_franchise` returns `Robb's Raiders` via the `"robb"`
  first-word alias, not `Brandon Knows Ball` via pass-2 fallback.
- The a8dd37b idiomatic-target guard is orthogonal — row 7's snap span
  ends on literal "streak" and exits the guard via its literal branch.

No code action taken this session.

## Evidence

### Regex replay at HEAD against the captured prose (row 7)

At `match.start=1289` in row 7's narrative_draft:

```
_SNAP_PATTERN span:              "snapped his losing streak"
is_losing_snap:                  True
ends on "streak"/"skid":         True  → a8dd37b guard returns False
_POSSESSIVE_OBJECT_STREAK:       no match (leading-cap blocks "his")
_find_nearby_franchise(window=150):
    before_context rfind:        "robb" at offset 149 (1 char before snap)
    RESULT:                      fid=0007 via ('BEFORE', 'robb', 1)
    display_name:                "Robb's Raiders"
```

`reverse_name_map` at HEAD (from franchise_directory 70985/2025,
owner_name column empty for all 10 rows) contains `"robb" → 0007` via
Pass 2 (first-word, `len < 3` filter). At b55cc17 that alias would not
have been added — the filter was `len < 5`.

### Positive control — row 39 (2024 W9, same day, 33 min after capture)

Row 39 prose: "Eddie snapped his losing streak with a 129.20-116.45 win
over KP." Structurally identical to row 7. Row 39 passed verification at
b55cc17 because "Eddie" (5 chars) cleared the `len < 5` filter.
Confirms the len-threshold boundary as the discriminator between the
two outcomes at capture time.

### Timeline

| Time                    | Event                                       |
|-------------------------|---------------------------------------------|
| 2026-04-08 22:01 PDT    | `2e52a15` introduces first-word aliases w/ `len < 5` |
| 2026-04-14 03:02 PDT    | **row 7 captured — failed at b55cc17**      |
| 2026-04-14 03:35 PDT    | **row 39 captured — passed at b55cc17**     |
| 2026-04-15 21:10 PDT    | `b58b1a2` relaxes filter to `len < 3`       |
| 2026-04-17 (a8dd37b)    | idiomatic-target guard (id=54/id=25 class)  |
| 2026-04-18 (this pass)  | Scoping confirms supersedure                |

## Documentation drift to correct

The a8dd37b commit message / backlog annotation describes the id=7
mechanism with `len<5` as the relevant filter and cites "robb / ben / kp"
as the short-first-word aliases. At HEAD:

- Pass 2 first-word filter is `len < 3` — "robb" (4), "ben" (3), "stu"
  (3) all pass; only `len < 3` strings are excluded.
- Pass 3 last-word filter is `len < 5` — separate pass, different purpose.
- Pass 4 owner-name alias filter is `len < 2` — catches "KP" when
  `owner_name` is populated.

Any future STREAK backlog entry that references the alias-filter
thresholds should cite the correct per-pass values rather than a single
`len<5` summary.

## Latent items surfaced but NOT pursued this session

Kept separate per one-topic-per-pass discipline. Backlog for future
scoping:

1. **`franchise_directory.owner_name` is empty for all 10 franchises in
   70985/2025.** Pass 4 (owner-name alias) therefore contributes no
   aliases to `reverse_name_map` for this league. The b369ea8 commit
   that wired in owner aliases assumes `owner_name` is populated at
   ingest; for this league it is not. Consequence: when the model
   writes "KP and the Playmakers" or "Pat left massive production on
   his bench" (both appear verbatim in row 7 prose), the only way the
   verifier can resolve the reference is via the franchise-name-derived
   aliases (Pass 2 first-word, Pass 3 last-word). "Playmakers" is the
   last-word alias for "Paradis' Playmakers" — works. "KP" and "Pat"
   have no path. Possible data-layer fix: populate `owner_name` at the
   MFL-adapter / franchise_directory ingest step. Scoping required
   before any change.

2. **STREAK id=7 class has no regression test covering the corrected
   attribution at HEAD.** The `b58b1a2` alias-widening landed without a
   STREAK-class regression test — it was a PLAYER_FRANCHISE-motivated
   change. A future tightening of the filter (e.g., re-adding a
   substring-safety threshold) could silently reopen this hole. A
   positive regression test ("given row 7's prose + the 70985/2025
   name_map, `verify_streaks` returns zero HARD failures attributed to
   Brandon Knows Ball") would pin the current behavior. Not landed this
   session — the scoping gate was for classification, not for adding
   insurance tests.

3. **Session brief's documented mechanism was drafted from static
   analysis against an assumed post-a8dd37b state, not from
   prompt_audit replay.** In this case the analysis was correct for
   the capture-era code but stale for HEAD. Future session briefs that
   document mechanism from static analysis should note which commit
   the analysis was performed against.

## What would have happened if this hadn't been caught

If a fix had been landed this session under the documented mechanism —
either Option A (pronoun-possessive pass-2 suppression) or Option B
(further widening the alias map) — it would have been a no-op fix on
top of an already-resolved failure, with test coverage that didn't
reproduce the real-world condition. Net effect: code complexity
increase, false sense of coverage. The scoping-first discipline caught
this before any code landed.
