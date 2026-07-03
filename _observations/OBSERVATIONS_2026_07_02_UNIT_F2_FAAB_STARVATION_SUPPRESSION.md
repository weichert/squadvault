# Observation - 2026-07-02 - Unit F2: FAAB Starvation Suppression (Regression Lock + Premise Correction)

**Session type:** EXECUTE (Claude Code, Opus 4.8). Brief:
`_observations/session_brief_unit_f2_faab_starvation_suppression.md` (landed squash `06d8d0c`).
Adjudicated to **Option 1 - tests-only regression lock** with a formal premise correction
(founder, 2026-07-02; D-X disposition 4). Gate 1 and Gate 2 collapsed into one gate (all tests
green-now; no implementation). Nothing published.

---

## 0. Ritual / provenance

- **HEAD at start:** `06d8d0c` (past `6778101`; the landed F2 brief). Verified `git log -1`.
- **Repo identity:** engine confirmed (`scripts/recap_artifact_regenerate.py` present).
- **Canonical DB (read-only):** hash `effb00e54fce5c38...` recorded start and end, **unchanged**.
  All diagnostics were read-only assembly dry-runs; no generation.
- **Standard trio (branch, CI invocations):** `ruff check src/squadvault/` clean;
  `mypy src/squadvault/ --exclude _retired` clean (160 source files);
  `pytest Tests/ -q` = **2397 passed, 2 skipped** (2393 prior + 4 new F2 tests). `prove_ci`
  N/A for this tests-plus-docs-only diff (see section 5).

## 1. Premise correction (append-only; the brief file is NOT amended)

Brief section 1 claims that for zero-WBA seasons "the weekly prompt **still receives** FAAB
narrative angles (detectors 17/18) and/or writer-room FAAB context." **That claim is
falsified at HEAD**, and was **already contradicted by the Stage A memo**
(`OBSERVATIONS_2026_07_02_FAAB_CLAIM_ATTRIBUTION_STAGE_A.md`):

- **Line 116** - the selection table row: `2019 wk5 ... FAAB reaches prompt? **NO** (0 season WBA)`.
- **Line 134** - the H1 classification: `Season WBA = 0: no WBA bullet, no FAAB
  writer-room/angle possible ... Data absent -> invention.`

D-X disposition 4's premise (a FAAB-context leak to suppress) was **wrong in the DECIDE lane**.
H1 is **unprompted invention** - the model fabricates FAAB dollars with no FAAB context in the
prompt - and its practical mitigation is the **Unit F1 verifier fix** (landed `6778101`), which
now fails invented FAAB, with the Tier-2 short-circuit carrying the recap to facts-only. The
brief file remains frozen as landed; this memo carries the correction.

## 2. Verified assembly reading (read-only, at HEAD `06d8d0c`)

FAAB reaches the weekly prompt through exactly two assembly-side surfaces, both keyed to
canonical `WAIVER_BID_AWARDED` (WBA):

- **Writer-room FAAB context** - `weekly_recap_lifecycle.py:1030-1053`:
  `derive_faab_spending` / `derive_faab_acquisitions` / `derive_faab_roi`
  (`context/writer_room_context_v1.py`, reading WBA) rendered by
  `render_writer_room_context_for_prompt` (`:368`, whose FAAB lines are all conditional -
  `if faab:` / `if acquisitions:`).
- **FAAB narrative angles (detectors 17/18)** - `weekly_recap_lifecycle.py:910` ->
  `detect_player_narrative_angles_v1` (`context/player_narrative_angles_v1.py:1887+`,
  `FAAB_ROI_NOTABLE` / `FAAB_FRANCHISE_EFFICIENCY`), loading season WBA.

Both read WBA; a zero-WBA season yields empty derivations and zero FAAB angles, for **every
week**. Empirical dry-run (`_derive_prompt_context` -> `_build_user_prompt`, read-only against
the local corpus):

- **2019 and 2020 (zero WBA):** the **only** line containing "faab" in the full assembled
  prompt is the template section header (see section 3). No FAAB angle, no FAAB spending line,
  no acquisition/ROI line.
- **2024 (65 season WBA):** 26 FAAB lines - angles, spending block, copy-only guard, ROI -
  i.e. the surfaces work normally when data exists.

So there is **no in-scope assembly-side FAAB context to suppress**: it is already empty by data
for zero-WBA seasons. Suppression is incidental-on-empty-derivations, and this unit **locks**
that behavior rather than adding a (no-op) gate.

## 3. Residual template-header finding (flagged; OUT OF SCOPE)

The single residual FAAB token in a zero-WBA prompt is the writer-room section header label
added by `_build_user_prompt` (`src/squadvault/ai/creative_layer_v1.py:322`):

```
=== WRITER ROOM (scoring deltas, FAAB spending) ===
```

It appears whenever the WRITER ROOM block is present (i.e. whenever scoring deltas exist),
naming "FAAB spending" even with no FAAB data beneath it. This is a **prompt-template**
element, explicitly **out of scope** for this unit (brief section 7) and per section 2.3
flagged-not-fixed. It is **left for a separate DECIDE ruling** on whether a header that names
FAAB when no FAAB data is present constitutes an "invitation" worth gating. Test 1 exempts
exactly this line.

## 4. Test plan as implemented (`Tests/test_faab_starvation_regression_lock_v1.py`)

Tests-only; assembly-level; deterministic; no generation. All **green at HEAD** (the lock).
Adapted from brief section 3, with **Test 2 (byte-identical pre/post) DROPPED** - moot with no
source change (there is no pre/post to compare). Drop recorded here per adjudication.

| Test | Encodes | Result |
|------|---------|--------|
| 1 - zero-WBA invariant lock | zero WBA -> the only FAAB line in the full prompt is the exempted template header (`:322`) | green |
| 3 - free-agent preservation | `TRANSACTION_FREE_AGENT` renders "... added ... (free agent)." with no `$` | green |
| 4 - data-keyed proof | same season/fixture: 0 WBA -> only header; 1 WBA row -> writer-room FAAB context appears | green |
| 5 - boundary | exactly one WBA is treated as non-zero (FAAB context present) | green |

Test 4 is the anti-hardcoding proof: toggling a single WBA row on the **same season number**
flips FAAB context from absent to present, which a season-number gate could not produce.

## 5. Scope, non-touch, and non-measurement statements

- **Zero source changes.** Diff is one new test file only
  (`Tests/test_faab_starvation_regression_lock_v1.py`) plus this memo and a STATE line.
- **Untouched:** verifier, Tier-2 policy, prompt templates, assembly/derivation source, data
  layer. (No `src/` change at all.)
- **Category-breakdown reverify is N/A** for this unit - there is no verifier change, so the
  reverify-as-merge-gate discipline does not apply. Stated explicitly rather than omitted.
- **`prove_ci` is N/A** for this diff - a tests-plus-docs-only change touches no runtime
  source, so the golden-path/drift proof surface is unaffected. The standard trio (ruff CI
  scope, mypy CI invocation, full pytest including the four new tests) is the proof and is run
  on the branch before commit. Stated explicitly rather than omitted.
- **Effect is NOT measured.** This is a behavior lock, not a re-measurement; per D-Y,
  re-measurement of the fresh-generation failure rate is the separate pre-registered unit.
- **H1's practical mitigation is the Unit F1 verifier fix** (`6778101`); F2 adds durability
  (a future detector/derivation change cannot silently reintroduce a zero-WBA FAAB leak).
